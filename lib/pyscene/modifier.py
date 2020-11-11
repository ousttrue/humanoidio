from logging import getLogger
logger = getLogger(__name__)
import re
from typing import List, Callable, Dict
from .node import Node, Skin
from .submesh_mesh import SubmeshMesh


def _split_submesh(node: Node, mesh: SubmeshMesh):
    logger.debug('split_submesh')
    for i, submesh in enumerate(mesh.submeshes):
        submesh_node = Node(f'{node.name}:submesh:{i}')
        node.add_child(submesh_node)
        submesh_node.mesh = mesh.create_from_submesh(i)
        submesh_node.skin = node.skin
    node.mesh = None
    node.skin = None


def traverse(node: Node, enter, leave):
    if enter: enter(node)
    for child in node.children:
        traverse(child, enter, leave)
    if leave: leave(node)


def before_import(roots: List[Node], is_vrm: bool):
    '''
    import 前にシーンを修正する
    '''

    # humanoid bone rename
    BONE_NAME = re.compile(r'(left|right)?(\w+)')

    def rename(node: Node):
        if node.humanoid_bone:
            m = BONE_NAME.match(node.humanoid_bone.name)
            if m:
                if m[1] == 'left':
                    new_name = f'{m[2]}.L'
                elif m[1] == 'right':
                    new_name = f'{m[2]}.R'
                else:
                    new_name = node.humanoid_bone.name
                new_name = new_name[0].upper() + new_name[1:]
                logger.debug(f'rename: {new_name} <= {node.name}')
                node.name = new_name

    for root in roots:
        traverse(root, rename, None)

    # Submeshを分割
    #
    # 条件
    #
    # * VRM
    # * morph が無い
    # * 名前に hair を含まない
    # * submesh が複数
    def split_mesh(node):
        if isinstance(node.mesh, SubmeshMesh):
            if is_vrm:
                if not node.mesh.morphtargets:
                    if 'hair' not in node.mesh.name.lower():
                        if len(node.mesh.submeshes) > 1:
                            _split_submesh(node, node.mesh)

    for root in roots:
        traverse(root, split_mesh, None)

    # leaf node の削除
    # * empty
    # * スキニングで使われていない
    # ノードがスキニングで使われている数をカウント
    weight_count: Dict[Node, int] = {}

    def count(node: Node):
        if not isinstance(node.mesh, SubmeshMesh):
            return
        if not node.skin:
            return

        def increment(weight: float, index: int):
            if weight > 0:
                joint = node.skin.joints[index]
                try:
                    weight_count[joint] += 1
                except KeyError:
                    weight_count[joint] = 1

        for i in node.mesh.indices:
            w = node.mesh.attributes.weights[i]
            j = node.mesh.attributes.joints[i]
            increment(w.x, j.x)
            increment(w.y, j.y)
            increment(w.z, j.z)
            increment(w.w, j.w)

    for root in roots:
        traverse(root, count, None)

    def remove_leaf(node: Node):
        if node.mesh:
            return
        if node.children:
            return
        if weight_count.get(node):
            return
        if not node.parent:
            return

        logger.debug(f'remove empty: {node}')
        node.parent.remove_child(node)

    for root in roots:
        traverse(root, None, remove_leaf)
