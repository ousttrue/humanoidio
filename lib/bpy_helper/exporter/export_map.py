from typing import List, Dict, Any, Iterator, Optional
import bpy
from ... import pyscene


class ExportMap:
    def __init__(self, nodes: List[pyscene.Node] = None):
        self.nodes: List[pyscene.Node] = []
        if nodes:
            self.nodes = nodes
        self.meshes: List[pyscene.FaceMesh] = []
        self._node_map: Dict[bpy.types.Object, pyscene.Node] = {}
        self._skin_map: Dict[bpy.types.Object, pyscene.Skin] = {}
        self.materials: List[pyscene.UnlitMaterial] = []
        self._material_map: Dict[bpy.types.Material, int] = {}
        self.vrm = pyscene.Vrm()

    def add_node(self, obj: Any, node: pyscene.Node):
        self.nodes.append(node)
        self._node_map[obj] = node

    def get_root_nodes(self) -> Iterator[pyscene.Node]:
        for node in self.nodes:
            if not node.parent:
                yield node

    def remove_node(self, node: pyscene.Node):
        # _node_map
        keys = []
        for k, v in self._node_map.items():
            if v == node:
                keys.append(k)
        for k in keys:
            del self._node_map[k]

        # _nodes
        self.nodes.remove(node)

        # children
        if node.parent:
            node.parent.remove_child(node)

    def get_node_for_skin(self, skin: pyscene.Skin) -> Optional[pyscene.Node]:
        for node in self.nodes:
            if node.skin == skin:
                return node

    def remove_empty_leaf_nodes(self) -> bool:
        bones: List[pyscene.Node] = []
        for skin in self._skin_map.values():
            skin_node = self.get_node_for_skin(skin)
            if not skin_node:
                raise Exception()
            for bone in skin_node.traverse():
                if bone not in bones:
                    bones.append(bone)

        def is_empty_leaf(node: pyscene.Node) -> bool:
            if node.humanoid_bone:
                return False
            if node.children:
                return False
            if node.mesh:
                return False
            if node in bones:
                return False
            return True

        remove_list = []
        for root in self.get_root_nodes():
            for node in root.traverse():
                if is_empty_leaf(node):
                    remove_list.append(node)

        if not remove_list:
            return False

        for remove in remove_list:
            self.remove_node(remove)

        return True
