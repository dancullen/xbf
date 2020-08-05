import time as cpython3_time

_start = cpython3_time.time()


def ticks_ms():
    return int((cpython3_time.time() - _start) * 1000)


def ticks_diff(after, before):
    # Note that this doesn't handle wraparound. But we shouldn't have any for the purposes of the testing.
    return after - before


def sleep_ms(ms):
    cpython3_time.sleep(ms / 1000.0)


def ctime(secs):
    return cpython3_time.ctime(secs)


def time():
    return cpython3_time.time()
