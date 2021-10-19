import unittest
import struct


class TestMemoryView(unittest.TestCase):
    def test_shape(self):
        b = struct.pack("ffffff", 1, 2, 3, 4, 5, 6)
        c = memoryview(b).cast('f', [3, 2])
        # for i in range(3):
        #     for j in range(2):
        #         print(c[i][j])


if __name__ == '__main__':
    unittest.main()