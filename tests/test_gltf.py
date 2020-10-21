from os import supports_bytes_environ
import unittest
import os
import pathlib
HERE = pathlib.Path(__file__).absolute().parent
GLTF_SAMPLE_DIR = pathlib.Path(os.getenv('GLTF_SAMPLE_MODELS'))  # type: ignore

from lib import serialization
from lib.struct_types import Float4
from lib.formats.gltf_context import parse_gltf
from lib.pyscene.submesh_mesh import SubmeshMesh
from lib.pyscene.material import Material, PBRMaterial

EPSILON = 1e-5


def check_seq(_l, _r):
    for l, r in zip(_l, _r):
        for ll, rr in zip(l, r):
            d = abs(ll - rr)
            if d > EPSILON:
                return False
    return True


class GltfTests(unittest.TestCase):
    def test_box_gltf(self):
        path = GLTF_SAMPLE_DIR / '2.0/Box/glTF/Box.gltf'
        self.assertTrue(path.exists())

        data = parse_gltf(path)
        roots = serialization.import_submesh(data)
        self.assertEqual(len(roots), 1)
        root = roots[0]

        mesh_node = root.children[0]
        mesh = mesh_node.mesh
        if not isinstance(mesh, SubmeshMesh):
            raise Exception()
        vertices = mesh.attributes
        self.assertEqual(len(vertices.position), 24)
        self.assertEqual(len(vertices.normal), 24)
        self.assertEqual(len(mesh.indices), 36)
        self.assertEqual(len(mesh.submeshes), 1)

    def test_box_glb(self):
        path = GLTF_SAMPLE_DIR / '2.0/Box/glTF-Binary/Box.glb'
        self.assertTrue(path.exists())

        data = parse_gltf(path)
        roots = serialization.import_submesh(data)
        self.assertEqual(len(roots), 1)
        root = roots[0]

        mesh_node = root.children[0]
        mesh = mesh_node.mesh
        if not isinstance(mesh, SubmeshMesh):
            raise Exception()
        vertices = mesh.attributes
        self.assertEqual(len(vertices.position), 24)
        self.assertEqual(len(vertices.normal), 24)
        self.assertEqual(len(mesh.indices), 36)
        self.assertEqual(len(mesh.submeshes), 1)

    def test_box_textured_gltf(self):
        path = GLTF_SAMPLE_DIR / '2.0/BoxTextured/glTF/BoxTextured.gltf'
        self.assertTrue(path.exists())

        data = parse_gltf(path)
        roots = serialization.import_submesh(data)
        self.assertEqual(len(roots), 1)
        root = roots[0]

        mesh_node = root.children[0]
        mesh = mesh_node.mesh
        if not isinstance(mesh, SubmeshMesh):
            raise Exception()
        vertices = mesh.attributes
        self.assertEqual(len(vertices.position), 24)
        position = [(p.x, p.y, p.z) for p in vertices.position]
        self.assertEqual(position[0], (-0.5, -0.5, 0.5))
        self.assertEqual(len(vertices.normal), 24)
        normal = [(n.x, n.y, n.z) for n in vertices.normal]
        self.assertEqual(normal[0], (0, 0, 1))
        self.assertEqual(len(vertices.texcoord), 24)
        texcord = [(uv.x, uv.y) for uv in vertices.texcoord]
        self.assertTrue(
            check_seq(texcord, [(6, 0), (5, 0), (6, 1), (5, 1), (4, 0), (5, 0),
                                (4, 1), (5, 1), (2, 0), (1, 0), (2, 1), (1, 1),
                                (3, 0), (4, 0), (3, 1), (4, 1), (3, 0), (2, 0),
                                (3, 1), (2, 1), (0, 0), (0, 1), (1, 0),
                                (1, 1)]))
        self.assertEqual(len(mesh.indices), 36)
        self.assertSequenceEqual(mesh.indices, [
            0, 1, 2, 3, 2, 1, 4, 5, 6, 7, 6, 5, 8, 9, 10, 11, 10, 9, 12, 13,
            14, 15, 14, 13, 16, 17, 18, 19, 18, 17, 20, 21, 22, 23, 22, 21
        ])
        self.assertEqual(len(mesh.submeshes), 1)

        submesh = mesh.submeshes[0]
        material = submesh.material
        texture = material.texture

        # material
        self.assertEqual(material.name, 'material0')
        self.assertTrue(isinstance(material, PBRMaterial))
        self.assertEqual(material.color, Float4(1, 1, 1, 1))
        self.assertEqual(texture.image.width, 256)
        self.assertEqual(texture.image.width, 256)

    def test_unlit_gltf(self):
        path = GLTF_SAMPLE_DIR / '2.0/UnlitTest/glTF/UnlitTest.gltf'
        self.assertTrue(path.exists())

        data = parse_gltf(path)
        roots = serialization.import_submesh(data)
        self.assertEqual(len(roots), 2)

        mesh_node = roots[0]
        mesh = mesh_node.mesh
        if not isinstance(mesh, SubmeshMesh):
            raise Exception()
        submesh = mesh.submeshes[0]
        material = submesh.material

        # material
        self.assertEqual(material.name, 'material0')
        self.assertTrue(isinstance(material, Material))

    def test_rig_gltf(self):
        path = GLTF_SAMPLE_DIR / '2.0/RiggedSimple/glTF/RiggedSimple.gltf'
        self.assertTrue(path.exists())

        data = parse_gltf(path)
        roots = serialization.import_submesh(data)
        self.assertEqual(len(roots), 1)
        root = roots[0]

        mesh_node = roots[0][0][1]
        mesh = mesh_node.mesh
        if not isinstance(mesh, SubmeshMesh):
            raise Exception()
        vertices = mesh.attributes

        joints = [(j.x, j.y, j.z, j.w) for j in vertices.joints]
        self.assertSequenceEqual(joints[64], (0, 1, 0, 0))
        weights = [(w.x, w.y, w.z, w.w) for w in vertices.weights]
        self.assertEqual(weights[64][0], 0.73860)
        self.assertEqual(weights[64][1], 0.264140)


if __name__ == '__main__':
    unittest.main()
