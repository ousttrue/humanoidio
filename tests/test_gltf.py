import unittest
import os
import pathlib
from typing import List
HERE = pathlib.Path(__file__).absolute().parent
GLTF_SAMPLE_DIR = pathlib.Path(os.getenv('GLTF_SAMPLE_MODELS'))  # type: ignore
VRM_SAMPLE_DIR = pathlib.Path(os.getenv('VRM_SAMPLES'))  # type: ignore
from lib.struct_types import Float4
from lib import formats
from lib import pyscene

EPSILON = 5e-3


def check_vec(_l, _r):
    for ll, rr in zip(_l, _r):
        d = abs(ll - rr)
        if d > EPSILON:
            return False
    return True


def check_seq(_l, _r):
    for l, r in zip(_l, _r):
        if not check_vec(l, r):
            return False
    return True


def check_mesh(l: formats.GltfContext, lm: formats.gltf.Mesh,
               r: formats.GltfContext, rm: formats.gltf.Mesh):
    if len(lm.primitives) != len(rm.primitives):
        return False

    lb = formats.BytesReader(l)
    rb = formats.BytesReader(r)

    for lp, rp in zip(lm.primitives, rm.primitives):
        # pos
        l_pos = [p for p in lb.get_bytes(lp.attributes['POSITION'])]
        r_pos = [p for p in rb.get_bytes(rp.attributes['POSITION'])]
        if len(l_pos) != len(r_pos):
            return False

        # normal

        # texcoord_0

        # weights_0

        # joints_0

        # indices
        if not isinstance(lp.indices, int):
            return False
        if not isinstance(rp.indices, int):
            return False
        li = [i for i in lb.get_bytes(lp.indices)]
        ri = [i for i in rb.get_bytes(rp.indices)]
        if len(li) != len(ri):
            return False
        # if not check_vec(li, ri):
        #     return False
        # a = 0

    return True


def is_unlit(material: formats.gltf.Material) -> bool:
    if not material.extensions:
        return False
    if not material.extensions.KHR_materials_unlit:
        return False
    return True


def check_material(l: formats.GltfContext, lm: formats.gltf.Material,
                   r: formats.GltfContext, rm: formats.gltf.Material):
    if not check_vec(lm.pbrMetallicRoughness.baseColorFactor,
                     rm.pbrMetallicRoughness.baseColorFactor):
        raise Exception('pbrMetallicRoughness.baseColorFactor')

    if lm.pbrMetallicRoughness.baseColorTexture and not rm.pbrMetallicRoughness.baseColorTexture:
        raise Exception('r has not colorTexture')
    if not lm.pbrMetallicRoughness.baseColorTexture and rm.pbrMetallicRoughness.baseColorTexture:
        raise Exception('l has not colorTexture')

    if is_unlit(lm) and not is_unlit(rm):
        raise Exception('r is not Unlit')
    elif not is_unlit(lm) and is_unlit(rm):
        raise Exception('l is not unlit')
    elif is_unlit(lm) and is_unlit(rm):
        # unlit
        pass
    else:
        # pbr
        pass
    return True


def check_gltf(l: formats.GltfContext, r: formats.GltfContext):
    '''
    import して再 export した結果が一致するか、緩く比較する
    '''

    if l.gltf.materials and not r.gltf.materials:
        raise Exception('r.gltf.materials is None')
    elif not l.gltf.materials and r.gltf.materials:
        raise Exception('l.gltf.materials is None')
    elif l.gltf.materials and r.gltf.materials:
        if len(l.gltf.materials) != len(r.gltf.materials):
            return Exception('len(l.gltf.materials) != len(r.gltf.materials)')
        for ll, rr in zip(l.gltf.materials, r.gltf.materials):
            if not check_material(l, ll, r, rr):
                return False

    if l.gltf.meshes and not r.gltf.meshes:
        raise Exception('r.gltf.meshes is None')
    elif not l.gltf.meshes and r.gltf.meshes:
        raise Exception('l.gltf.meshes is None')
    elif l.gltf.meshes and r.gltf.meshes:
        if len(l.gltf.meshes) != len(r.gltf.meshes):
            raise Exception('len(l.gltf.meshes) != len(r.gltf.meshes)')
        for ll, rr in zip(l.gltf.meshes, r.gltf.meshes):
            if not check_mesh(l, ll, r, rr):
                return False

    return True


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
        self.assertTrue(check_gltf(exported, data))

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
        self.assertEqual(material.name, 'Texture')
        self.assertTrue(isinstance(material, pyscene.PBRMaterial))
        self.assertEqual(material.color, Float4(1, 1, 1, 1))
        self.assertEqual(texture.url_or_bytes,
                         path.parent / 'CesiumLogoFlat.png')

        # export
        nodes = [node for root in roots for node in root.traverse()]
        exported = pyscene.to_gltf(nodes)
        self.assertTrue(check_gltf(exported, data))

    def test_box_textured_glb(self):
        path = GLTF_SAMPLE_DIR / '2.0/BoxTextured/glTF-Binary/BoxTextured.glb'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)
        roots = pyscene.nodes_from_gltf(data)

        # export
        nodes = [node for root in roots for node in root.traverse()]
        exported = pyscene.to_gltf(nodes)
        self.assertTrue(check_gltf(exported, data))

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
        self.assertIsInstance(material0, pyscene.Material)
        self.assertTrue(check_vec(material0.color, (1, 0.21763764, 0, 1)))

        # Blue
        mesh1 = roots[1].mesh
        if not isinstance(mesh1, pyscene.SubmeshMesh):
            raise Exception()
        material1 = mesh1.submeshes[0].material
        self.assertEqual(material1.name, 'Blue')
        self.assertIsInstance(material1, pyscene.Material)
        self.assertTrue(check_vec(material1.color, (0, 0.21763764, 1, 1)))

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
            check_seq(position[0:3], [(0, 0, 0), (0, 0, 0),
                                      (0, 0.0189325, 0)]))

    def test_vivi(self):
        path = VRM_SAMPLE_DIR / 'vroid/Vivi.vrm'
        self.assertTrue(path.exists())

        data = formats.parse_gltf(path)
        roots = pyscene.nodes_from_gltf(data)
        self.assertEqual(len(roots), 5)
        root = roots[0]

        # mesh_node = roots[0][0][1]
        # mesh = mesh_node.mesh
        # if not isinstance(mesh, pyscene.SubmeshMesh):
        #     raise Exception()
        # vertices = mesh.attributes

        # joints = [(j.x, j.y, j.z, j.w) for j in vertices.joints]
        # self.assertSequenceEqual(joints[64], (0, 1, 0, 0))
        # weights = [(w.x, w.y, w.z, w.w) for w in vertices.weights]
        # self.assertAlmostEqual(weights[64][0], 0.73860, delta=3e-3)
        # self.assertAlmostEqual(weights[64][1], 0.264140, delta=3e-3)


if __name__ == '__main__':
    unittest.main()
