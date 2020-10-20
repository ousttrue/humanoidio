from os import supports_bytes_environ
import unittest
import os
import pathlib
HERE = pathlib.Path(__file__).absolute().parent
GLTF_SAMPLE_DIR = pathlib.Path(os.getenv('GLTF_SAMPLE_MODELS'))  # type: ignore

from lib.importer.import_manager import import_submesh
from lib.formats.gltf_context import parse_gltf
from lib.pyscene.submesh_mesh import SubmeshMesh
from lib.pyscene.material import Material, PBRMaterial


class GltfTests(unittest.TestCase):
    def test_box_gltf(self):
        path = GLTF_SAMPLE_DIR / '2.0/Box/glTF/Box.gltf'
        self.assertTrue(path.exists())

        data = parse_gltf(path)
        roots = import_submesh(data)
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
        roots = import_submesh(data)
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
        roots = import_submesh(data)
        self.assertEqual(len(roots), 1)
        root = roots[0]

        mesh_node = root.children[0]
        mesh = mesh_node.mesh
        if not isinstance(mesh, SubmeshMesh):
            raise Exception()
        vertices = mesh.attributes
        self.assertEqual(len(vertices.position), 24)
        self.assertEqual(len(vertices.normal), 24)
        self.assertEqual(len(vertices.texcoord), 24)
        self.assertEqual(len(mesh.indices), 36)
        self.assertEqual(len(mesh.submeshes), 1)

        submesh = mesh.submeshes[0]
        material = submesh.material

        # material
        self.assertEqual(material.name, 'material0')
        self.assertIs(material, PBRMaterial)

    def test_unlit_gltf(self):
        path = GLTF_SAMPLE_DIR / '2.0/UnlitTest/glTF/UnlitTest.gltf'
        self.assertTrue(path.exists())

        data = parse_gltf(path)
        roots = import_submesh(data)
        self.assertEqual(len(roots), 1)
        root = roots[0]

        mesh_node = root.children[0]
        mesh = mesh_node.mesh
        if not isinstance(mesh, SubmeshMesh):
            raise Exception()
        submesh = mesh.submeshes[0]
        material = submesh.material

        # material
        self.assertEqual(material.name, 'material0')
        self.assertIs(material, Material)


if __name__ == '__main__':
    unittest.main()
