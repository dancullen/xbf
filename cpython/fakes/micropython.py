""" micropython.py is a CPython3 implementation of MicroPython's "micropython" module. """


def mem_info():
    print("stack: 576 out of 5632")
    print("GC: total: 64000, used: 3296, free: 60704")
    print("No. of 1-blocks: 41, 2-blocks: 47, max blk sz: 8, max free sz: 3750")


def stack_use():
    return 0
