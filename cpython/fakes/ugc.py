"""
ugc.py is an implementation of the MicroPython 'gc' module using CPython3.

Note that the MicroPython 'gc' module differs from the CPython 'gc' module
(e.g., the former has methods gc.mem_alloc(), gc.mem_free(), and gc.collect()
but the latter does not have these.)

It is unfortunate that the only way to import 'gc' in Digi XBee 3 MicroPython is with "import gc",
not "import ugc". Oh well. So what I've done is defined upython/ugc.py that wraps the MicroPython
version of gc. And the file that you're currently reading is the CPython3 analogue.
"""


def mem_alloc():
    return 0


def mem_free():
    return 0


def collect():
    return None
