# test.py contains unit tests. Normally you'd put the unit tests for your app in this file,
# but since this demo app doesn't do much, this file instead contains the unit tests for
# the xbf library itself.

import sys
import unittest

# Your app would typically use the path 'xbf.cpython.core' to import these from the deps dir,
# but since we're already inside the 'xbf' project, we can import relative to this project's
# top-level dir (not deps), so we omit the 'xbf' below.
from xbf.cpython.core import Error, Success, NewError, errorf

class TestError(unittest.TestCase):
    """ TestError tests all functions related to error handling. """

    def test_error(self):
        x = NewError("hello")
        y = errorf("blah blah %d: %s", (7, x))
        self.assertEqual("blah blah 7: hello", y)


if __name__ == "__main__":
    exit_status = unittest.main(verbosity=2)
    sys.exit(exit_status)
