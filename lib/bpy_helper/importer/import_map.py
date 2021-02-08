from typing import Dict, Any
import bpy
from ... import pyscene


class ImportMap:
    '''
    pyscene と bl.types の対応を保持する
    '''
    def __init__(self):
        self.obj: Dict[pyscene.Node, bpy.types.Object] = {}
        self.mesh: Dict[pyscene.SubmeshMesh, bpy.types.Mesh] = {}
        self.skin: Dict[pyscene.Skin, bpy.types.Object] = {}
        self.material: Dict[pyscene.UnlitMaterial, bpy.types.Material] = {}
        self.image: Dict[pyscene.Texture, bpy.types.Image] = {}
        self.matrix_map: Dict[pyscene.Node, Any] = {}  # matrix
