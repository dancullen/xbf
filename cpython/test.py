# test.py contains unit tests.

import sys
import unittest

from xbf.upython.core import ButtonBuffer
from xbf.upython.core import sequence_equal_or_more_recent, sequence_more_recent, MAX_SEQUENCE_NUMBER

# Your app would typically use the path 'xbf.cpython.core' to import these from the deps dir,
# but since we're already inside the 'xbf' project, we can import relative to this project's
# top-level dir (not deps), so we omit the 'xbf' below.
from xbf.cpython.core import Error, Success, new_error, errorf


class TestErrors(unittest.TestCase):

    def test_errors(self):
        my_error = new_error("hello")
        self.assertEqual(Error, type(my_error))
        self.assertTrue(my_error != Success)

        y = errorf("blah blah %d: %s", 7, my_error)
        self.assertEqual("test_errors: blah blah 7: test_errors: hello", y)


class TestSequenceNumbers(unittest.TestCase):

    def test_basic(self):
        self.assertEqual(65535, MAX_SEQUENCE_NUMBER)  # These tests assume a 16-bit sequence number.

        self.assertFalse(sequence_more_recent(5, 5, MAX_SEQUENCE_NUMBER))
        self.assertFalse(sequence_more_recent(1, 2, MAX_SEQUENCE_NUMBER))
        self.assertTrue(sequence_more_recent(2, 1, MAX_SEQUENCE_NUMBER))
        self.assertTrue(sequence_more_recent(2, 0, MAX_SEQUENCE_NUMBER))

        self.assertTrue(sequence_equal_or_more_recent(5, 5, MAX_SEQUENCE_NUMBER))
        self.assertFalse(sequence_equal_or_more_recent(1, 2, MAX_SEQUENCE_NUMBER))
        self.assertTrue(sequence_equal_or_more_recent(2, 1, MAX_SEQUENCE_NUMBER))
        self.assertTrue(sequence_equal_or_more_recent(2, 0, MAX_SEQUENCE_NUMBER))

        self.assertFalse(sequence_more_recent(20, 20, max_sequence_number=20))
        self.assertTrue(sequence_more_recent(1, 19, max_sequence_number=20))
        self.assertTrue(sequence_more_recent(1, 12, max_sequence_number=20))
        self.assertFalse(sequence_more_recent(1, 11, max_sequence_number=20))
        self.assertFalse(sequence_more_recent(1, 10, max_sequence_number=20))
        self.assertFalse(sequence_more_recent(1, 9, max_sequence_number=20))

        self.assertTrue(sequence_equal_or_more_recent(20, 20, max_sequence_number=20))
        self.assertTrue(sequence_equal_or_more_recent(1, 19, max_sequence_number=20))
        self.assertTrue(sequence_equal_or_more_recent(1, 12, max_sequence_number=20))
        self.assertFalse(sequence_equal_or_more_recent(1, 11, max_sequence_number=20))
        self.assertFalse(sequence_equal_or_more_recent(1, 10, max_sequence_number=20))
        self.assertFalse(sequence_equal_or_more_recent(1, 9, max_sequence_number=20))


class TestButtonBuffer(unittest.TestCase):

    def test_basic(self):
        bb = ButtonBuffer()
        bb.put(1)
        bb.put(0)
        bb.put(1)
        assert 5 == bb.get_uint32()

        for _ in range(31):
            bb.put(0)
        assert 0x80000000 == bb.get_uint32()
        bb.put(0)
        assert 0x00000000 == bb.get_uint32()

        err = bb.deserialize(b"too-many-bytes")
        assert err is not None
        bb.deserialize(b"\xDE\xAD\xBE\xEF")
        assert 0xDEADBEEF == bb.get_uint32()
        assert b"\xDE\xAD\xBE\xEF" == bb.serialize()


if __name__ == "__main__":
    exit_status = unittest.main(verbosity=2)
    sys.exit(exit_status)
