""" uos.py is a mock/fake implementation of the Digi XBee 3 MicroPython uos module for use by cpython unit tests. """

_bundle_contents = []


def bundle(*args, **kwargs):
    global _bundle_contents

    if len(args) == 0:
        # bundle() (without args) returns the list of current bundled files.
        return _bundle_contents

    if args[0] is None:
        # bundle(None) (with None as the arg) clears the bundle and returns the empty list
        _bundle_contents.clear()
        return _bundle_contents

    # bundle('file1.mpy', 'file2.mpy', ...) replaces the contents of the bundle with the given files.
    # Note that the .mpy extensions are stripped.
    _bundle_contents = [x.replace(".mpy", "") for x in args]

    return _bundle_contents


def urandom(num_bytes):
    """ urandom returns a bytes object with n random bytes generated by the hardware random number generator. """
    import os
    return os.urandom(num_bytes)
