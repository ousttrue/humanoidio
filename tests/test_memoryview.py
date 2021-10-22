import unittest
import struct
import ctypes
from humanoidio.gltf import accessor_util


class TestMemoryView(unittest.TestCase):
    def test_shape(self):
        b = struct.pack("ffffff", 1, 2, 3, 4, 5, 6)
        c = memoryview(b).cast('f', [3, 2])
        # for i in range(3):
        #     for j in range(2):
        #         print(c[i][j])

    def test_ctypes_shape(self):
        class Float3(ctypes.Structure):
            _fields_ = [
                ('x', ctypes.c_float),
                ('x', ctypes.c_float),
                ('x', ctypes.c_float),
            ]

        v = Float3(1, 2, 3)
        # print(v.__class__.__base__)
        self.assertIsInstance(v, ctypes.Structure)
        array_type = (Float3 * 256)
        self.assertEqual(Float3, array_type._type_)

        positions = array_type()
        t, c = accessor_util.get_type_count(positions)
        self.assertEqual(accessor_util.ComponentType.Float, t)
        self.assertEqual(c, 3)


if __name__ == '__main__':
    unittest.main()