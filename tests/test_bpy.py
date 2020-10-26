from lib.pyscene.to_submesh import facemesh_to_submesh
from lib.pyscene import to_submesh
from lib.pyscene.facemesh import FaceMesh
from lib.pyscene.submesh_mesh import SubmeshMesh
from lib.bpy_helper import scan
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


class BpyTests(unittest.TestCase):
    '''
    gltf(glb, vrm) -> pyscene -> bpy -> pyscene
    '''
    def test_box_textured_glb(self):
        bpy_helper.clear()
        path = GLTF_SAMPLE_DIR / '2.0/BoxTextured/glTF-Binary/BoxTextured.glb'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)
        roots = pyscene.nodes_from_gltf(data)
        self.assertEqual(roots[0].children[0].mesh.attributes.position[0],
                         Float3(-0.5, -0.5, 0.5))

        bpy_helper.load(bpy.context, roots)
        scanner = bpy_helper.scan()
        self.assertEqual(scanner.nodes[1].mesh.positions[0],
                         Float3(-0.5, -0.5, -0.5))

        exported = [node for node in scanner.nodes if not node.parent]
        self.assertEqual(len(roots), len(exported))
        for l, r in zip(roots, exported):
            self._check_node(l, r)

    def test_box_textured_gltf(self):
        bpy_helper.clear()
        path = GLTF_SAMPLE_DIR / '2.0/BoxTextured/glTF/BoxTextured.gltf'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)
        roots = pyscene.nodes_from_gltf(data)
        self.assertEqual(roots[0].children[0].mesh.attributes.position[0],
                         Float3(-0.5, -0.5, 0.5))

        bpy_helper.load(bpy.context, roots)
        scanner = bpy_helper.scan()
        self.assertEqual(scanner.nodes[1].mesh.positions[0],
                         Float3(-0.5, -0.5, -0.5))

        exported = [node for node in scanner.nodes if not node.parent]
        self.assertEqual(len(roots), len(exported))
        for l, r in zip(roots, exported):
            self._check_node(l, r)

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
