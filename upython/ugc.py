"""
ugc.py wraps the 'gc' module in order to hide the MicroPython-vs-CPython differences.
See comments in cpython/ugc.py for more explanation.
"""

import gc


def mem_alloc():
    return gc.mem_alloc()


def mem_free():
    return gc.mem_free()


def collect():
    return gc.collect()
