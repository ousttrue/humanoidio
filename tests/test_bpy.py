from lib.pyscene.to_submesh import facemesh_to_submesh
from lib.pyscene import to_submesh
from lib.pyscene.facemesh import FaceMesh
from lib.pyscene.submesh_mesh import SubmeshMesh
from lib.struct_types import Float3
import unittest
import os
import pathlib
HERE = pathlib.Path(__file__).absolute().parent
GLTF_SAMPLE_DIR = pathlib.Path(os.getenv('GLTF_SAMPLE_MODELS'))  # type: ignore
VRM_SAMPLE_DIR = pathlib.Path(os.getenv('VRM_SAMPLES'))  # type: ignore
import bpy
from lib import formats, pyscene, bpy_helper
from tests import helper

import pyimpex
pyimpex.register()


class BpyTests(unittest.TestCase):
    '''
    gltf(glb, vrm) -> pyscene -> bpy -> pyscene
    '''
    def _check_mesh(self, _l: pyscene.Node, _r: pyscene.Node):
        l = _l.mesh
        r = _r.mesh
        if not l and not r:
            return
        elif l and not r:
            raise Exception('r.mesh is None')
        elif not l and r:
            raise Exception('l.mesh is None')

        if isinstance(l, FaceMesh):
            raise Exception()

        if isinstance(r, FaceMesh):
            r = pyscene.facemesh_to_submesh(_r)

        self.assertTrue(l.compare(r))

    def _check_node(self, l: pyscene.Node, r: pyscene.Node):
        self.assertEqual(l.name, r.name)

        self._check_mesh(l, r)

        self.assertEqual(len(l.children), len(r.children))
        for l, r in zip(l.children, r.children):
            self._check_node(l, r)

    def setUp(self):
        bpy_helper.utils.clear()

    def test_box_textured_glb(self):
        path = GLTF_SAMPLE_DIR / '2.0/BoxTextured/glTF-Binary/BoxTextured.glb'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)
        index_map = pyscene.load(data)
        roots = index_map.get_roots()
        self.assertEqual(roots[0].children[0].mesh.attributes.position[0],
                         Float3(-0.5, -0.5, 0.5))

        bpy_helper.importer.load(bpy.context.scene.collection, index_map)
        exported = bpy_helper.exporter.scan()
        self.assertEqual(exported.nodes[1].mesh.positions[0],
                         Float3(-0.5, -0.5, -0.5))

        exported = [node for node in exported.nodes if not node.parent]
        self.assertEqual(len(roots), len(exported))
        for l, r in zip(roots, exported):
            self._check_node(l, r)

    def test_box_textured_gltf(self):
        path = GLTF_SAMPLE_DIR / '2.0/BoxTextured/glTF/BoxTextured.gltf'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)
        index_map = pyscene.load(data)
        roots = index_map.get_roots()
        self.assertEqual(roots[0].children[0].mesh.attributes.position[0],
                         Float3(-0.5, -0.5, 0.5))

        bpy_helper.importer.load(bpy.context.scene.collection, index_map)
        scanner = bpy_helper.exporter.scan()
        self.assertEqual(scanner.nodes[1].mesh.positions[0],
                         Float3(-0.5, -0.5, -0.5))

        exported = [node for node in scanner.nodes if not node.parent]
        self.assertEqual(len(roots), len(exported))
        for l, r in zip(roots, exported):
            self._check_node(l, r)

    def test_animated_morph_cube_gltf(self):
        path = GLTF_SAMPLE_DIR / '2.0/AnimatedMorphCube/glTF/AnimatedMorphCube.gltf'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)
        index_map = pyscene.load(data)
        roots = index_map.get_roots()
        self.assertEqual(
            roots[0].mesh.attributes.position[0],
            Float3(-0.009999999776482582, 0.009999998845160007,
                   0.009999999776482582))
        bpy_helper.importer.load(bpy.context.scene.collection, index_map)
        scanner = bpy_helper.exporter.scan()
        self.assertEqual(
            scanner.nodes[0].mesh.positions[0],
            Float3(-0.009999999776482582, -0.009999999776482582,
                   0.009999998845160007))

        exported = [node for node in scanner.nodes if not node.parent]
        self.assertEqual(len(roots), len(exported))
        for l, r in zip(roots, exported):
            self._check_node(l, r)

    def test_rig_gltf(self):
        path = GLTF_SAMPLE_DIR / '2.0/RiggedSimple/glTF/RiggedSimple.gltf'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)
        index_map = pyscene.load(data)
        roots = index_map.get_roots()
        bpy_helper.importer.load(bpy.context.scene.collection, index_map)
        scanner = bpy_helper.exporter.scan()

        exported = [node for node in scanner.nodes if not node.parent]
        self.assertEqual(len(roots), len(exported))
        # for l, r in zip(roots, exported):
        #     self._check_node(l, r)

    def test_scene(self):
        '''
        scene - view_layers
        '''
        scene = bpy.context.scene
        view_layer = bpy.context.view_layer
        collection = bpy.context.collection

        self.assertEqual(scene.view_layers[0], view_layer)

        self.assertNotEqual(scene.collection, collection)
        self.assertEqual(scene.collection.children[0], collection)
