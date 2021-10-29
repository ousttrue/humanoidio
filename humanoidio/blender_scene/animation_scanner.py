from typing import List
import bpy


class AnimationCurve:
    def __init__(self):
        self.keys = []


class BlenderAnimationScanner:
    def __init__(self):
        self.animations: List[AnimationCurve] = []

    def _export_animation(self, bl_obj: bpy.types.Object):
        if not bl_obj.animation_data:
            return
        if not bl_obj.animation_data.action:
            return

        bl_action = bl_obj.animation_data.action
        print(bl_action)
        for fcurve in bl_action.fcurves:
            print(fcurve, fcurve.data_path, fcurve.array_index)
            for p in fcurve.keyframe_points:
                print(p, p.co)

    def scan(self, bl_obj_list: List[bpy.types.Object]):
        for bl_obj in bl_obj_list:
            self._export_animation(bl_obj)

        return self.animations
