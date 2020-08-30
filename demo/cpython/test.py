# test.py contains unit tests for this demo application.

import sys
import unittest

class TestSomething(unittest.TestCase):

    def test_something(self):
        self.assertTrue(True)

if __name__ == "__main__":
    exit_status = unittest.main(verbosity=2)
    sys.exit(exit_status)
