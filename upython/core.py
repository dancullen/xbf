import io
import sys


Error = str
Success = None

MAX_SEQUENCE_NUMBER = 2**16 - 1  # 16-bit sequence number.


def exception_details(ex):
    """
    exception_details takes a thrown exception object and returns
    a string containing the exception details and the stack trace.

    Rationale: In standard CPython, one would use traceback.format_exc(),
    but Digi XBee MicroPython doesn't come with the traceback module.
    """
    traceback_stream = io.StringIO()
    sys.print_exception(ex, traceback_stream)
    return traceback_stream.getvalue()


def detect_platform() -> str:
    """ detect_platform demonstrates how to determine the current running architecture. """
    import sys

    if sys.platform == "xbee3-zigbee":
        return "xbee3-zigbee"

    if sys.platform == "xbee-cellular":
        import xbee
        hv = (xbee.atcmd("HV") >> 8) & 0xFF  # https://xbplib.readthedocs.io/en/latest/api/digi.xbee.models.hw.html
        if hv == 0x49:
            return "xbee-cellular-CAT-1-AT&T"
        elif hv == 0x4A:
            return "xbee-cellular-LTE-M-Verizon"
        elif hv == 0x4B:
            return "xbee-cellular-LTE-M-AT&T"
        elif hv == 0x4D:
            return "xbee-cellular-CAT-1-Verizon"
        else:
            return "xbee-cellular-unknown"

    if sys.platform in ("linux", "win32") and sys.version_info[0] == 3:
        return "cpython3"

    return "unknown"


def sequence_more_recent(s1: int, s2: int, max_sequence_number: int = MAX_SEQUENCE_NUMBER):
    """
    sequence_more_recent compares two sequence numbers, handling wraparound, returning True
    if-and-only-if s1 is strictly more recent than s2. It accepts two sequence numbers s1 and s2,
    which are assumed to be unsigned integers, stored as Python ints. This function uses
    the constant MAX_SEQUENCE_NUMBER for the maximum sequence number.
    """
    return ((s1 > s2) and (s1-s2 <= max_sequence_number//2)) or ((s2 > s1) and (s2-s1 > max_sequence_number//2))


def sequence_equal_or_more_recent(s1: int, s2: int, max_sequence_number: int = MAX_SEQUENCE_NUMBER):
    """
    sequence_equal_or_more_recent is similar to sequence_more_recent but it doesn't check for strict equality;
    this function returns True if the two numbers are equal.
    """
    return (s1 == s2) or sequence_more_recent(s1, s2, max_sequence_number)


def invert(value: int):
    # invert takes an integer and changes the value 1 to a 0 and 0 to a 1.
    # Behavior is undefined for all other values.
    # One use of this is to invert the active level of an active-low push button input.
    return 1 if value == 0 else 0


class ButtonBuffer:
    """
    ButtonBuffer stores a sequence of Boolean GPIO input values.
    This allows the push button inputs to be sent redundantly across the network, for reliability.
    """

    def __init__(self, data: int = 0):
        self._data = data

    def __repr__(self):
        return "ButtonBuffer(uint32=0x%08x)" % self._data

    def put(self, input_value: int) -> None:
        self._data = ((self._data << 1) & 0xFFFFFFFF) | (input_value & 0x01)

    def get(self, delay: int = 0):
        """
        get returns the value at the given (positive) delay position, or zero if the delay is out of range.
        get(0) returns the value for the current frame.
        get(1) gives the value from the previous frame.
        And so on.
        """
        if delay < 0 or delay > 31:
            return 0
        return (self._data >> delay) & 0x01

    def get_uint32(self) -> int:
        """
        get_int returns the data as an integer.
        """
        return self._data

    def serialize(self) -> bytearray:
        """ serialize returns a binary representation of the data. """
        d = bytearray(4)
        d[0] = (self._data >> 24) & 0xFF  # Transmit in Big Endian format.
        d[1] = (self._data >> 16) & 0xFF
        d[2] = (self._data >> 8) & 0xFF
        d[3] = self._data & 0xFF
        return d

    def deserialize(self, d: bytearray) -> Error:
        """ deserialize unpacks and validates the binary data. Updates the data members upon success."""
        if len(d) != 4:
            return Error("Expected data to be 4 bytes long but got %d bytes" % len(d))
        self._data = (d[0] << 24) | (d[1] << 16) | (d[2] << 8) | d[3]
        return Success
