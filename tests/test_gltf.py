import unittest
import os
from typing import List
import pathlib
HERE = pathlib.Path(__file__).absolute().parent
GLTF_SAMPLE_DIR = pathlib.Path(os.getenv('GLTF_SAMPLE_MODELS'))  # type: ignore
VRM_SAMPLE_DIR = pathlib.Path(os.getenv('VRM_SAMPLES'))  # type: ignore
from lib.struct_types import Float4
from lib import formats
from lib import pyscene
from tests import helper


class GltfTests(unittest.TestCase):
    '''
    gltf(glb, vrm) -> pyscene -> gltf
    '''
    def test_box_gltf(self):
        # import
        path = GLTF_SAMPLE_DIR / '2.0/Box/glTF/Box.gltf'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)
        roots = pyscene.nodes_from_gltf(data)
        self.assertEqual(len(roots), 1)
        root = roots[0]

        mesh_node = root.children[0]
        mesh = mesh_node.mesh
        if not isinstance(mesh, pyscene.SubmeshMesh):
            raise Exception()
        vertices = mesh.attributes
        self.assertEqual(len(vertices.position), 24)
        self.assertEqual(len(vertices.normal), 24)
        self.assertEqual(len(mesh.indices), 36)
        self.assertEqual(len(mesh.submeshes), 1)

        # export
        nodes = [node for root in roots for node in root.traverse()]
        exported = pyscene.to_gltf(nodes)
        self.assertTrue(helper.check_gltf(data, exported))

    def test_box_glb(self):
        path = GLTF_SAMPLE_DIR / '2.0/Box/glTF-Binary/Box.glb'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)
        roots = pyscene.nodes_from_gltf(data)
        self.assertEqual(len(roots), 1)
        root = roots[0]

        mesh_node = root.children[0]
        mesh = mesh_node.mesh
        if not isinstance(mesh, pyscene.SubmeshMesh):
            raise Exception()
        vertices = mesh.attributes
        self.assertEqual(len(vertices.position), 24)
        self.assertEqual(len(vertices.normal), 24)
        self.assertEqual(len(mesh.indices), 36)
        self.assertEqual(len(mesh.submeshes), 1)

    def test_box_textured_gltf(self):
        path = GLTF_SAMPLE_DIR / '2.0/BoxTextured/glTF/BoxTextured.gltf'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)
        roots = pyscene.nodes_from_gltf(data)
        self.assertEqual(len(roots), 1)
        root = roots[0]

        mesh_node = root.children[0]
        mesh = mesh_node.mesh
        if not isinstance(mesh, pyscene.SubmeshMesh):
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
            helper.check_seq(texcord, [(6, 0), (5, 0), (6, 1), (5, 1), (4, 0),
                                       (5, 0), (4, 1), (5, 1), (2, 0), (1, 0),
                                       (2, 1), (1, 1), (3, 0), (4, 0), (3, 1),
                                       (4, 1), (3, 0), (2, 0), (3, 1), (2, 1),
                                       (0, 0), (0, 1), (1, 0), (1, 1)]))
        self.assertEqual(len(mesh.indices), 36)
        self.assertSequenceEqual(mesh.indices, [
            0, 1, 2, 3, 2, 1, 4, 5, 6, 7, 6, 5, 8, 9, 10, 11, 10, 9, 12, 13,
            14, 15, 14, 13, 16, 17, 18, 19, 18, 17, 20, 21, 22, 23, 22, 21
        ])
        self.assertEqual(len(mesh.submeshes), 1)

        submesh = mesh.submeshes[0]
        material = submesh.material
        texture = material.color_texture

        # material
        self.assertEqual(material.name, 'Texture')
        self.assertTrue(isinstance(material, pyscene.PBRMaterial))
        self.assertEqual(material.color, Float4(1, 1, 1, 1))
        self.assertEqual(texture.url_or_bytes,
                         path.parent / 'CesiumLogoFlat.png')

        # export
        nodes = [node for root in roots for node in root.traverse()]
        exported = pyscene.to_gltf(nodes)
        self.assertTrue(helper.check_gltf(data, exported))

    def test_box_textured_glb(self):
        path = GLTF_SAMPLE_DIR / '2.0/BoxTextured/glTF-Binary/BoxTextured.glb'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)
        roots = pyscene.nodes_from_gltf(data)

        # export
        nodes = [node for root in roots for node in root.traverse()]
        exported = pyscene.to_gltf(nodes)
        self.assertTrue(helper.check_gltf(data, exported))

    def test_unlit_gltf(self):
        path = GLTF_SAMPLE_DIR / '2.0/UnlitTest/glTF/UnlitTest.gltf'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)
        roots = pyscene.nodes_from_gltf(data)
        self.assertEqual(len(roots), 2)

        # Orange
        mesh0 = roots[0].mesh
        if not isinstance(mesh0, pyscene.SubmeshMesh):
            raise Exception()
        material0 = mesh0.submeshes[0].material
        self.assertEqual(material0.name, 'Orange')
        self.assertIsInstance(material0, pyscene.UnlitMaterial)
        self.assertTrue(
            helper.check_vec(material0.color, (1, 0.21763764, 0, 1)))

        # Blue
        mesh1 = roots[1].mesh
        if not isinstance(mesh1, pyscene.SubmeshMesh):
            raise Exception()
        material1 = mesh1.submeshes[0].material
        self.assertEqual(material1.name, 'Blue')
        self.assertIsInstance(material1, pyscene.UnlitMaterial)
        self.assertTrue(
            helper.check_vec(material1.color, (0, 0.21763764, 1, 1)))

    def test_rig_gltf(self):
        path = GLTF_SAMPLE_DIR / '2.0/RiggedSimple/glTF/RiggedSimple.gltf'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)
        roots = pyscene.nodes_from_gltf(data)
        self.assertEqual(len(roots), 1)

        mesh_node = roots[0][0][1]
        mesh = mesh_node.mesh
        if not isinstance(mesh, pyscene.SubmeshMesh):
            raise Exception()
        vertices = mesh.attributes

        joints = [(j.x, j.y, j.z, j.w) for j in vertices.joints]
        self.assertSequenceEqual(joints[64], (0, 1, 0, 0))
        weights = [(w.x, w.y, w.z, w.w) for w in vertices.weights]
        self.assertAlmostEqual(weights[64][0], 0.73860, delta=3e-3)
        self.assertAlmostEqual(weights[64][1], 0.264140, delta=3e-3)

        # skin
        skin_node = mesh_node
        skin = skin_node.skin
        self.assertEqual(skin.name, 'Armature')
        self.assertEqual(len(skin.joints), 2)
        self.assertEqual(skin.joints[0].name, 'Bone')
        self.assertEqual(skin.joints[1].name, 'Bone.001')

    def test_animated_morph_cube_gltf(self):
        path = GLTF_SAMPLE_DIR / '2.0/AnimatedMorphCube/glTF/AnimatedMorphCube.gltf'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)

        self.assertIsNone(data.gltf.bufferViews[0].byteOffset)

        roots = pyscene.nodes_from_gltf(data)
        mesh_node = roots[0]
        mesh = mesh_node.mesh
        if not isinstance(mesh, pyscene.SubmeshMesh):
            raise Exception()

        self.assertEqual(len(mesh.morphtargets), 2)
        thin = mesh.morphtargets[0]
        position = [(p.x, p.y, p.z) for p in thin.attributes.position]
        self.assertTrue(
            helper.check_seq(position[0:3], [(0, 0, 0), (0, 0, 0),
                                             (0, 0.0189325, 0)]))

    def test_vivi(self):
        path = VRM_SAMPLE_DIR / 'vroid/Vivi.vrm'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)
        roots = pyscene.nodes_from_gltf(data)
        self.assertEqual(len(roots), 5)
        root = roots[0]


if __name__ == '__main__':
    unittest.main()
