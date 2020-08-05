"""
test.py contains unit tests.
"""

import sys
import unittest

from xbf.upython.core import ButtonBuffer
from xbf.upython.core import sequence_equal_or_more_recent, sequence_more_recent, MAX_SEQUENCE_NUMBER


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
