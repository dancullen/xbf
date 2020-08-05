# deploy.py Creates a release zip file.
#
# The only dependency of this script is CPython3.

import os
import pathlib
import subprocess
import zipfile


# Use this Git branch to determine which files to include.
GIT_BRANCH = "feature/NETOS-269-SNMP-SHA-AES"


# get_commit_hash returns the abbreviated hash of the most recent commit.
# More specifically, the first 8 characters of the Git commit SHA-1 hash.
def get_commit_hash():
    cmd = ["git", "describe", "--match=DoNotMatchAnyTags", "--always", "--abbrev=8", "--dirty"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    commit_hash = p.communicate()[0].strip()
    return commit_hash.decode("utf-8")


# get_paths_to_files_in_git_tree recursively returns a list of files in given location.
#
# Note that we use the git-ls-tree command so that we can avoid accidentally zipping up
# any build artifacts that might be sitting around in the tree; we only deploy the files
# that are checked into Git.
def get_paths_to_files_in_git_tree(branch, path):
    cmd = ["git", "ls-tree", "-r", "--full-name", branch, path]
    data = subprocess.check_output(cmd)
    lines = data.splitlines()
    output = []
    for line in lines:
        fields = line.split()
        if len(fields) != 4:
            continue  # Invalid line. Each line must contain 3 fields. Skip to next line.
        unicode_from_bytes = fields[3].decode("utf-8")
        output.append(unicode_from_bytes)
    return output


# get_libraries Returns a list of paths to build artifacts that need to be included in the zip file.
#
# We need to deploy the new versions of the SNMPv3 libraries.
#
# However, OpenSSL's "libcrypto", "libssl", and "libtls" do NOT need to be included because we haven't
# modified those. To be crystal clear, Treck's "cryptlib" is NOT the same thing as OpenSSL's "libcrypto".
def get_libraries():
    arch_paths = ["netos/netos/lib/arm9/32b/gnu/",
                  "netos/netos/lib/arm7/32b/gnu/"]
    filenames = ["libsnmp.a",
                 "libsnmpdbg.a",
                 "libsnmp_no_ipsec.a",
                 "libsnmp_no_ipsecdbg.a",
                 "libsnmpv3.a",
                 "libsnmpv3dbg.a",
                 "libsnmpv3_no_ipsec.a",
                 "libsnmpv3_no_ipsecdbg.a"]
    full_paths = [p + f for p in arch_paths for f in filenames]
    return full_paths


def main():

    # If you're not in the correct directory, complain loudly.
    # This script is intended to be invoked from the same directory as this file,
    # which is assumed to be in a subdirectory just below the top-level NETOS directory
    # (so that the Git commands work properly).
    current_working_dir = os.getcwd()
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    if current_working_dir != this_file_dir:
        return "This script must be invoked from the same directory as %s." % this_file_dir
    os.chdir("..")

    # Assemble the list of files to zip.
    headers = get_paths_to_files_in_git_tree(branch=GIT_BRANCH, path="netos/netos/h/snmp/")
    libs = get_libraries()
    examples = get_paths_to_files_in_git_tree(branch=GIT_BRANCH, path="netos/netos/src/examples/nasnmpv3/")

    all_files = headers + libs + examples

    # Exclude certain files from the list. For example, the .gpj project files are only used
    # by Digi to build Net+OS; those files aren't included in standard releases of Net+OS.
    all_files = [f for f in all_files if not f.endswith(".gpj")]

    # Determine the name and directory of the output zip file. The file name
    # includes the git commit hash so that we can more easily track releases.
    git_hash = get_commit_hash()
    zipfilepath = "%s/deploy/SNMPv3-SHA-AES-%s.zip" % (this_file_dir, git_hash)
    zipfiledir = os.path.dirname(zipfilepath)

    # Ensure deployment dir exists. This behaves like 'mkdir -p'-- in other words, it does not complain
    # if the directory already exists, and it generates any missing parent directories along the path.
    pathlib.Path(zipfiledir).mkdir(parents=True, exist_ok=True)

    # Now zip the files.
    with zipfile.ZipFile(zipfilepath, 'w', zipfile.ZIP_DEFLATED) as zf:
        print("Creating zip file %s..." % zipfilepath)
        for f in all_files:
            try:
                print("  %s" % f)
                zf.write(f)
            except Exception as ex:
                return str(ex)

    return None


if __name__ == "__main__":
    err = main()
    if err is None:
        print("Completed successfully.")
    else:
        print("Completed with errors. Details: %s" % err)
