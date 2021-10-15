import unittest
import sys


class TestHello(unittest.TestCase):
    def test_hello(self):
        self.assertEqual(1, 1)


if __name__ == "__main__":
    unittest.main()
