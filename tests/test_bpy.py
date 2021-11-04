from logging import getLogger

logger = getLogger(__name__)

import math
from typing import Tuple
import os
import pathlib
import unittest
from logging import basicConfig, DEBUG

HERE = pathlib.Path(__file__).absolute().parent
GLTF_SAMPLE_KEY = 'GLTF_SAMPLE_MODELS'
GLTF_SAMPLE_DIR = pathlib.Path(os.environ[GLTF_SAMPLE_KEY]) / '2.0'
GLTF_PATH = GLTF_SAMPLE_DIR / 'BoxTextured/glTF-Binary/BoxTextured.glb'
VRM_SAMPLE_KEY = 'VRM_SAMPLES'
VRM_SAMPLE_DIR = pathlib.Path(os.environ[VRM_SAMPLE_KEY])
VRM_PATH = VRM_SAMPLE_DIR / 'vroid/Darkness_Shibu.vrm'
VRM1_PATH = VRM_SAMPLE_DIR / 'Alicia_solid_A.vrm'

basicConfig(
    level=DEBUG,
    datefmt='%H:%M:%S',
    format='%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s')

import bpy
import humanoidio

humanoidio.register()


def clear():
    # clear scene
    bpy.ops.object.select_all(action='SELECT')  # type: ignore
    bpy.ops.object.delete()

    # only worry about data in the startup scene
    for bpy_data_iter in (
            bpy.data.objects,
            bpy.data.meshes,
            bpy.data.lights,
            bpy.data.cameras,
            bpy.data.materials,
    ):
        for id_data in bpy_data_iter:
            # id_data.user_clear();
            bpy_data_iter.remove(id_data)


def set_key(bl_obj: bpy.types.Object, frame: int, euler: Tuple[float, float,
                                                               float]):
    print('set_key', bl_obj, frame, euler)
    bl_obj.rotation_euler = euler
    bl_obj.keyframe_insert(data_path="rotation_euler", frame=frame)


def set_copy_rotation(src, dst):
    print(src, dst)
    bpy.context.view_layer.objects.active = dst
    bpy.ops.object.constraint_add(type='COPY_ROTATION')
    c = dst.constraints[-1]
    c.target = src
    print(c)
    # Target space
    # Owner space
    # Influence


class TestBpy(unittest.TestCase):
    def test_importer(self):
        self.assertTrue(GLTF_PATH.exists())

        # clear scene
        clear()

        bpy.ops.humanoidio.importer(filepath=str(VRM1_PATH))  # type: ignore

        # humanoidio.scene.load(path)
        # data = formats.parse_gltf(path)
        # index_map = pyscene.load(data)
        # roots = index_map.get_roots()
        # self.assertEqual(roots[0].children[0].mesh.attributes.position[0],
        #                  Float3(-0.5, -0.5, 0.5))

        # bpy_helper.importer.load(bpy.context.scene.collection, index_map)
        # exported = bpy_helper.exporter.scan()
        # self.assertEqual(exported.nodes[1].mesh.positions[0],
        #                  Float3(-0.5, -0.5, -0.5))

        # exported = [node for node in exported.nodes if not node.parent]
        # self.assertEqual(len(roots), len(exported))
        # for l, r in zip(roots, exported):
        #     self._check_node(l, r)

        bpy.ops.wm.save_as_mainfile(filepath=str(HERE.parent / 'tmp.blend'))
        humanoidio.unregister()

    def test_exporter(self):
        # cube
        bpy.ops.mesh.primitive_cube_add(size=2,
                                        enter_editmode=False,
                                        align='WORLD',
                                        location=(3, 0, 0),
                                        scale=(1, 1, 1))
        bpy.context.active_object.name = 'dst'

        # setup key frame
        bpy.context.scene.frame_end = 60
        bl_cube = bpy.context.collection.objects['Cube']
        set_key(bl_cube, 1, (0, 0, 0))
        set_key(bl_cube, 20, (0, 0, math.pi / 180 * 120))
        set_key(bl_cube, 40, (0, 0, math.pi / 180 * 240))
        set_key(bl_cube, 60, (0, 0, math.pi / 180 * 360))
        bl_cube.animation_data.action.fcurves[-1].extrapolation = 'LINEAR'

        set_copy_rotation(bpy.context.collection.objects['Cube'],
                          bpy.context.collection.objects['dst'])

        # deselect
        bpy.ops.object.select_all(action='DESELECT')

        # save
        bpy.ops.wm.save_as_mainfile(filepath=str(HERE.parent / 'export.blend'))

        # export
        path = HERE.parent / 'export.glb'
        bpy.ops.humanoidio.exporter(filepath=str(path))  # type: ignore


if __name__ == "__main__":
    unittest.main()
