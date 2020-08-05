
""" main.py contains the main application to run on the XBee device. """

import uos
import umachine
from xbee import atcmd, relay


class UserDataRelayLogger:

    # Caution: Ensure that CSXB_MSG_LOG matches the redundant definition in constants.py.
    # The reason for redundancy is that we cannot import any user modules until after rebundling.
    CSXB_MSG_LOG = 0x00

    def print(self, msg):
        """
        print sends the given message as a User Data Relay API Frame out the relay.SERIAL
        interface so that the Connect Sensor can print it out its Serial Console.
        """
        dest = relay.SERIAL
        data = bytes([self.CSXB_MSG_LOG]) + msg
        try:
            relay.send(dest, data)
        except:
            pass  # Do nothing because relay must be broken so we have nowhere to send the error!


class DualSinkLogger:
    """
    DualSinkLogger sends the message to both the given logger (e.g., a UserDataRelayLogger)
    and to REPL/stdout. This ensures that the developer can receive the message regardless of
    whether the developer is connected to the XBee via API Frames or the via the REPL terminal.
    """

    def __init__(self, logger):
        self.logger = logger

    def print(self, msg):
        self.logger.print(msg)
        print(msg)  # This is the standard library print function.


def delete_any_dot_py_files(logger):
    """
    delete_any_dot_py_files removes any .py files from the XBee filesystem.

    This function should be invoked at the top of main.py/main.mpy before importing any custom modules.

    Rationale: .py files have priority over .mpy files in MicroPython "import" statements.
    Since we've deployed our application as .mpy files, we don't want any .py files with
    the same name to be imported instead. For example, "import common" should load
    common.mpy instead of common.py. This prevents surprises during development if
    you have old .py versions of the code on the device. More importantly, this is
    a security thing-- we want to stop someone from loading malicious .py files
    with the same names as our .mpy files.

    Note that the Connect Sensor C code must handle removal of main.py. The reason is that
    we deploy main.mpy to the device but if the device already contained a main.py, the latter
    version of main would be invoked and thus this function would never have a chance to run!
    """
    try:
        for filename in uos.listdir("/flash"):
            if filename.endswith(".py"):
                fullpath = "/flash/" + filename
                uos.remove(fullpath)
    except Exception as ex:
        logger.print("delete_any_dot_py_files: Exception occurred. Details: %s" % ex)


def djb2(data, seed=5381):
    """
     djb2 hash algorithm. Input: a 'bytes' object. Output: 32-bit integer. http://www.cse.yorku.ca/~oz/hash.html
     Use the hash value from the previous invocation as the seed input for the next invocation if you want to
     perform the hash in chunks-- see unit tests for example.
     """
    # https://stackoverflow.com/questions/16745387/python-32-bit-and-64-bit-integer-math-with-intentional-overflow
    hash = seed & 0XFFFFFFFF
    for d in data:
        hash = 0xFFFFFFFF & (0XFFFFFFFF & (hash * 33) + d)
    return hash


def rebundle_if_necessary(logger, desired_bundle):
    """
    rebundle_if_necessary checks whether the code in the bundle flash (uos.bundle()) matches the code
    stored in the filesystem flash. If there is a discrepancy, this updates the contents of the bundle.

    desired_bundle contains the list of module names (without the .mpy extensions) that need to be
    included in the bundle. All these files must be located in the top-level directory (/flash).

    Note that if the bundle is updated, the MicroPython interpreter automatically restarts.

    Caution: Do not import any user modules prior to invoking rebundle_if_necessary().
    Modules provided by the system are ok, but if you import any user modules, chances
    are that those modules will import other modules that may or may not be in the bundle.
    The old bundled versions could conflict with latest files in the filesystem,
    so we do not want to import any user modules until the code is rebundled!

    What is bundling? The Digi XBee 3 MicroPython function uos.bundle() stores byte-compiled modules
    (.mpy files) in a dedicated area of XBee 3 device flash in order to conserve heap RAM.
    Those files will be executed  instead of loading them into the heap to run them, thereby saving
    saving limited heap space for application data.

    The biggest hurdle to getting this working properly is determining at startup whether the code
    in the bundle needs to be updated. We can't just perform the bundling every time it starts
    because 1) the MicroPython restarts after bundling and we'd get caught in an endless loop,
    and 2) writing to flash memory is expensive for many reasons (e.g., takes time, wastes battery,
    risks wearing out the flash from too many writes, etc.).

    Fortunately, the XBee 3 provides a way to get a 32-bit hash of the bundled file-- the ATPYB command.
    The Digi XBee 3 Cellular User Guide are vague about the type of 32-bit hash, but investigation
    into the XBee 3 MicroPython codebase reveals that it is a djb2 hash. http://www.cse.yorku.ca/~oz/hash.html

    Unfortunately, this hash is useless to us because this hash contains some other unknown metadata as well,
    not just the bytes from the .mpy files themselves. So when we try to hash the files in the filesystem,
    it doesn't match the output of the ATPYB command.

    For example:
        import xbee, os
        uos.bundle()
        ['common']
        xbee.atcmd('PY', 'B')
        'bytecode: 2558 bytes (hash=0x9AAC4DD8)\rbundled: 2019-11-07T08:07:47'
        [f for f in uos.ilistdir('/flash')]
        [('cert', 16384, 0, 0), ('lib', 16384, 0, 0), ('empty.txt', 32768, 0, 0), ('small.txt', 32768, 0, 14),
        ('large.txt', 32768, 0, 1200), ('common.mpy', 32768, 0, 1976)]

    Notice that the file on the disk is 1976 bytes, but the bundled bytcode is 2558 bytes. And indeed,
    if we calculate a the djb2 hash on the file itself, it doesn't match the hash shown by ATPYB.

    The workaround for this is for us to calculate and store our own hash of the files at time of bundling.
    From a software security standpoint, this is not nearly as robust as if we had gotten the bundling information
    directly from the MicroPython interpreter, but keep in mind that the MicroPython system is inherently insecure--
    e.g., there is no secure boot feature for MicroPython code. So storing the hash ourselves is the best way can do.

    Where should this hash be stored? We could store it in a dedicated file in the filesystem,
    but it would be simpler if we repurpose one of the AT registers for this data. We therefore
    have decide to store the hash in the ATKP (Device Description) register-- this field can store
    up to 20 ASCII characters to be displayed in Digi Remote Manager (DRM). This is not a problem because
    we've disabled Remote Manager XBee itself-- only the overall CSXB device will be visible in DRM.

    What type of hash should we use? We might as well use djb2 just like MicroPython interpreter
    because this algorithm is fast, simple, and performs well.

    At startup, we can calculate the hash of all the .mpy files that we desire to be included in the bundle.
    Then we check that hash value  against the value stored in the ATKP register. If it doesn't match,
    we re-bundle the code and store the new hash in the ATKP register.

    For more information, see CSXB-82 for more details.

    More important note: This function must NOT have any dependencies on any of the user's Python modules;
    it must depend only on built-in modules (e.g., xbee, os). In addition, this function MUST be defined
    in main.py/main.mpy. The reason is that bundled code takes precedence over any .py/.mpy file EXCEPT
    for main.py/.mpy (main is never bundled, as explained in the source code comments within the function
    xbpy_bundle_run() in https://stash.digi.com/projects/XBEE/repos/micropython/browse/ports/xbee/xbpy_bundle.c).
    If our rebundling function depended upon code that could be included in the bundle, then we run the risk
    of the rebundling not working correctly because the old code in the bundle would get run instead of the
    newer .mpy files on the device. This could even be a security concern if, for example, this rebundling
    function depended upon a script 'x.mpy', but a malicious version of 'x.mpy' was loaded into the bundle
    by manually running uos.bundle('x.mpy') via XCTU. Therefore, to safeguard against any surprises, this
    rebundling function MUST be defined in main.py/.mpy and depend ONLY upon main.py/main.mpy.

    UPDATE 2019-12-06: There appears to be an XBee bug in which sometimes uos.bundle() returns
    an empty string for the name of one of the modules. For example, stored_bundle reports
    ['common', '', 'mqtt_handler', 'umqtt'] but we expected ` ['common', 'hardware', 'mqtt_handler', 'umqtt']`.
    And we get into an endless cycle of failed bundling, rebooting, failed bundling, rebooting, etc.
    Our workaround is to explicitly delete the contents of the bundle (i.e., uos.bundle(None)) before
    attempting to rebundle the files-- see the bottom of this function. Also be sure to check for
    zero-length bundles and if we get one, print a warning.

    UPDATE 2019-12-18: I think that another reason bundling might fail is if there is a syntax bug
    with the MicroPython script that you're trying to add to the bundle. And if that's the case,
    we'll get into a never-ending loop of rebundling, rebooting, rebundling, rebooting, etc.
    And then we get corrupted files and lots of other unsavory things. So what we should do
    right here is wait in an endless loop because this is an unrecoverable error.

    UPDATE 2019-12-20: I believe that the way in which we determine whether bundling failed for a module
    is to check whether the module name is an empty string string. The Digi MicroPython Programming Guide
    does not discuss this-- it's something that I've learned empirically. However, it is unfortunate
    that the MicroPython interpreter restarts whether bundling has succeeded or not because we lose
    our state. Maybe the thing to do is write some other state value to ATKP to indicate how many times
    we attempted to rebundle before timing out? But that is future work.
    """

    ENABLE_BUNDLE_FEATURE = True

    if not ENABLE_BUNDLE_FEATURE:
        logger.print("Bypassing bundling feature. Ensuring that bundled code has been deleted.")
        if len(uos.bundle()) > 0:  # If there are any bundled modules...
            uos.bundle(None)  # Delete contents of the bundle.
            umachine.soft_reset()  # Restart MicroPython interpreter.
        return

    logger.print("Checking whether bundling is necessary...")

    # Look up the existing bundle contents and hash.
    stored_bundle = uos.bundle()
    stored_hash = atcmd('KP')
    logger.print("stored_bundle: %s\nstored_hash: %s" % (stored_bundle, stored_hash))

    # Calculate the hash of all .mpy files on the device.
    mpy_filenames = ['%s.mpy' % m for m in desired_bundle]
    running_hash = djb2(b"")
    for fname in mpy_filenames:
        with open(fname, "rb") as f:
            while True:
                chunk = f.read(1024)
                if not chunk:  # read() returns a zero-length buffer when the end of the file is reached.
                    break
                running_hash = djb2(chunk, running_hash)
    desired_hash = "Bundle: 0x%08X" % running_hash  # ATKP field must contain no more than 20 ASCII characters.
    logger.print("desired_bundle: %s\ndesired_hash: %s" % (desired_bundle, desired_hash))

    # Check for any problems with the bundled modules. I've noticed that sometimes a zero-length module name string
    # in the list of stored modules indicates a problem with a bundled module. See comments above for more details.
    bad_bundled_module = False
    for module_name in stored_bundle:
        if len(module_name) == 0:
            bad_bundled_module = True
            logger.print("Detected zero-length module name in stored_bundle.")
            break


    # Commented out this loop because if you have a bad bundled module,
    # you'll never be able to rebundle with new code to recover from it
    # because you'd be stuck forever in a loop.
    #
    # TODO Add more state info to ATKP so that we can retry bundling if it failed but limit retries to N times.
    #      You still need to store the hash of the code you are attempting to bundle because if the host device
    #      deploys new files, you want to restart the rebundle count back at 0 times. Otherwise you'll never
    #      be able to refresh the bundle with good code!
    #
    #while bad_bundled_module:  # Wait here forever because there is an unrecoverable bundling error.
    #    logger.print("FATAL ERROR: Problem with bundle. Sleep in loop forever.")
    #    utime.sleep_ms(1000)


    # Determine if bundling is necessary.
    reason_to_bundle = ""
    if bad_bundled_module:
        reason_to_bundle = "Stored bundle contains a zero-length module name, indicating a bad bundled module."
    elif stored_bundle != desired_bundle:
        # Checking the list of module names here is not strictly necessary because the hash check below would
        # catch any discrepancy, but we still perform this check to get a more descriptive error message.
        reason_to_bundle = "Stored bundle does not contain all expected modules."
    elif stored_hash != desired_hash:
        reason_to_bundle = "Stored hash of bundle does not match hash of .mpy files."

    # Perform bundling if required.
    if not reason_to_bundle:
        logger.print("No bundling required; bundle is already up-to-date.")
        return
    logger.print("Updating bundle. Reason: %s" % reason_to_bundle)
    atcmd('KP', desired_hash)

    uos.bundle(None)  # Bundling seems to succeed more often if we first explicitly empty it like this.
    uos.bundle(*mpy_filenames)  # MUST be the last line in function because this restarts the MicroPython interpreter.
    # In other words, if the above us.bundle(...) call is successful, this function never returns.


def bootstrap(logger):
    """
    Deletes any .py files and performs rebundling if necessary.
    """
    delete_any_dot_py_files(logger)
    rebundle_if_necessary(logger, ['components', 'constants', 'ugc', 'umqtt'])


if __name__ == "__main__":
    udr_logger = UserDataRelayLogger()
    dual_logger = DualSinkLogger(udr_logger)

    # Must delete any .py files and perform bundling before importing any user modules!
    bootstrap(dual_logger)

    from components import main
    main(dual_logger)
