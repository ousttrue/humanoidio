from logging import getLogger
from tests.helper import is_unlit
logger = getLogger(__name__)
from typing import List, Callable
from .node import Node
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


def traverse(node: Node, callback: Callable[[Node], None]):
    callback(node)

    for child in node.children:
        traverse(child, callback)


def before_import(roots: List[Node], is_vrm: bool):
    '''
    import 前にシーンを修正する
    '''
    def split_mesh(node):
        if isinstance(node.mesh, SubmeshMesh):
            if is_vrm:
                if not node.mesh.morphtargets:
                    if 'hair' not in node.mesh.name.lower():
                        if len(node.mesh.submeshes) > 1:
                            '''
                            Submeshを分割

                            条件

                            * VRM
                            * morph が無い
                            * 名前に hair を含まない
                            * submesh が複数
                            '''
                            _split_submesh(node, node.mesh)

    for root in roots:
        traverse(root, split_mesh)
