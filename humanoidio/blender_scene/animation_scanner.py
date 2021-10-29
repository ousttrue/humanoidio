from typing import List, Iterable, Tuple, NamedTuple
import bpy, mathutils
from .. import gltf


class Curve(NamedTuple):
    times: List[float]
    values: List[float]


def get_curve(data_path: str, curves):
    x_curve = None
    y_curve = None
    z_curve = None
    for curve in curves:
        c = Curve([], [])
        if curve.array_index == 0:
            x_curve = c
        elif curve.array_index == 1:
            y_curve = c
        elif curve.array_index == 2:
            z_curve = c
        else:
            raise NotImplementedError()
        for p in curve.keyframe_points:
            t, v = p.co
            c.times.append(t)
            c.values.append(v)

    if data_path == "rotation_euler":
        if x_curve.times == y_curve.times and y_curve.times == z_curve.times:
            values = []
            for x, y, z in zip(x_curve.values, y_curve.values, z_curve.values):
                values.append(mathutils.Euler((x, y, z)).to_quaternion())
            return x_curve.times, values
        else:
            raise NotImplementedError()
    else:
        raise NotImplementedError()


def get_curves(
    bl_action: bpy.types.Action
) -> Iterable[Tuple[str, List[bpy.types.FCurve]]]:
    curves = []
    for fcurve in bl_action.fcurves:
        if curves and curves[0].data_path != fcurve.data_path:
            yield (curves[0].data_path, curves)
            curves = []
        curves.append(fcurve)
    if curves:
        yield (curves[0].data_path, curves)


DATA_PATH_MAP = {
    "rotation_euler": gltf.AnimationChannelTargetPath.rotation,
}


class BlenderAnimationScanner:
    def __init__(self):
        self.animations = []

    def _export_animation(self, i: int, bl_obj: bpy.types.Object):
        if not bl_obj.animation_data:
            return
        if not bl_obj.animation_data.action:
            return

        bl_action = bl_obj.animation_data.action
        for data_path, curves in get_curves(bl_action):
            times, values = get_curve(data_path, curves)
            animation = gltf.Animation(i, DATA_PATH_MAP[data_path], times,
                                       values)
            self.animations.append((bl_action.name, animation))

    def scan(
        self, obj_node: List[Tuple[bpy.types.Object, gltf.Node]]
    ) -> List[Tuple[str, gltf.Animation]]:
        for i, on in enumerate(obj_node):
            self._export_animation(i, on[0])
        return self.animations
