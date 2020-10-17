from typing import Any, List, Optional, Tuple

import bpy
import mathutils  # pylint: disable=E0401

from scene_translator.formats import gltf
from .import_manager import ImportManager
from .node import Node


class Skin:
    def __init__(self, manager: ImportManager, skin: gltf.Skin) -> None:
        self.manager = manager
        self.skin = skin
        self.inverse_matrices: Any = None

    def get_matrix(self, joint: int) -> Any:
        if not self.inverse_matrices:
            self.inverse_matrices = self.manager.get_array(
                self.skin.inverseBindMatrices)
        m = self.inverse_matrices[joint]
        mat = mathutils.Matrix(
            ((m.f00, m.f10, m.f20, m.f30), (m.f01, m.f11, m.f21, m.f31),
             (m.f02, m.f12, m.f22, m.f32), (m.f03, m.f13, m.f23, m.f33)))
        # d = mat.decompose()
        return mat


def load_objects(context: bpy.types.Context,
                 manager: ImportManager) -> Tuple[List[Node], Node]:
    # collection
    view_layer = context.view_layer
    if hasattr(view_layer, 'collections') and view_layer.collections.active:
        collection = view_layer.collections.active.collection
    else:
        collection = context.scene.collection
        # view_layer.collections.link(collection)

    # setup
    nodes = [
        Node(i, gltf_node) for i, gltf_node in enumerate(manager.gltf.nodes)
    ]

    # set parents
    for gltf_node, node in zip(manager.gltf.nodes, nodes):
        for child_index in gltf_node.children:
            child = nodes[child_index]
            node.children.append(child)
            child.parent = node

    # check root
    roots = [node for node in enumerate(nodes) if not node[1].parent]
    if len(roots) != 1:
        root = Node(len(nodes), gltf.Node({'name': '__root__'}))
        for _, node in roots:
            root.children.append(node)
            node.parent = root
    else:
        root = nodes[0]
    root.create_object(collection, manager)

    def get_root(skin: gltf.Skin) -> Optional[Node]:

        root = None

        for joint in skin.joints:
            node = nodes[joint]
            if not root:
                root = node
            else:
                if node in root.get_ancestors():
                    root = node

        return root

    # create armatures
    root_skin = gltf.Skin.from_dict({'name': 'skin'})

    for skin in manager.gltf.skins:
        for joint in skin.joints:
            if joint not in root_skin.joints:
                root_skin.joints.append(joint)
    skeleton = get_root(root_skin)

    if skeleton:
        skeleton.create_armature(context, collection, view_layer, root_skin)

    # bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    return (nodes, root)
