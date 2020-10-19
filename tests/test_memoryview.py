import unittest
import array
from lib.formats.buffertypes import Vector3


class MemoryViewTests(unittest.TestCase):
    def test_memoryview_array(self):
        a = memoryview(array.array('I', [1, 2, 3]))
        self.assertEqual(a.nbytes, 12)
        self.assertEqual(a.itemsize, 4)
        self.assertEqual(len(a), 3)
        
        self.assertEqual(a.ndim, 1)
        self.assertSequenceEqual(a.strides, [4])  # type: ignore
        self.assertSequenceEqual(a.shape, [3])  # type: ignore

    def test_memoryview_ctypes_array(self):
        a = memoryview((Vector3 * 3)())  # type: ignore
        self.assertEqual(a.nbytes, 36)
        self.assertEqual(a.itemsize, 12)
        self.assertEqual(len(a), 3)

        self.assertEqual(a.ndim, 1)
        self.assertSequenceEqual(a.strides, [12])  # type: ignore
        self.assertSequenceEqual(a.shape, [3])  # type: ignore
