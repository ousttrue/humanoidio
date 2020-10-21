'''
* serialize: pyscene => GLTF
* deserialize: GLTF => pyscene
'''
from typing import List
import bpy, mathutils
from ..formats.gltf_context import GltfContext
from .bytesreader import BytesReader
from .. import pyscene

def import_submesh(data: GltfContext) -> List[pyscene.Node]:
    '''
    glTFを中間形式のSubmesh形式に変換する
    '''
    reader = BytesReader(data)

    meshes: List[pyscene.SubmeshMesh] = []
    if data.gltf.meshes:
        for i, m in enumerate(data.gltf.meshes):
            mesh = reader.load_submesh(data, i)
            meshes.append(mesh)

    nodes: List[pyscene.Node] = []
    if data.gltf.nodes:
        for i, n in enumerate(data.gltf.nodes):
            name = n.name if n.name else f'node {i}'
            node = pyscene.Node(name)

            if n.translation:
                node.position.x = n.translation[0]
                node.position.y = n.translation[1]
                node.position.z = n.translation[2]

            if n.rotation:
                node.rotation.x = n.rotation[0]
                node.rotation.y = n.rotation[1]
                node.rotation.z = n.rotation[2]
                node.rotation.w = n.rotation[3]

            if n.scale:
                node.scale.x = n.scale[0]
                node.scale.y = n.scale[1]
                node.scale.z = n.scale[2]

            if n.matrix:
                m = n.matrix
                matrix = mathutils.Matrix(
                    ((m[0], m[4], m[8], m[12]), (m[1], m[5], m[9], m[13]),
                     (m[2], m[6], m[10], m[14]), (m[3], m[7], m[11], m[15])))
                t, q, s = matrix.decompose()
                node.position.x = t.x
                node.position.y = t.y
                node.position.z = t.z
                node.rotation.x = q.x
                node.rotation.y = q.y
                node.rotation.z = q.z
                node.rotation.w = q.w
                node.scale.x = s.x
                node.scale.y = s.y
                node.scale.z = s.z

            if isinstance(n.mesh, int):
                node.mesh = meshes[n.mesh]

            nodes.append(node)

        for i, n in enumerate(data.gltf.nodes):
            if n.children:
                for c in n.children:
                    nodes[i].add_child(nodes[c])

    scene = data.gltf.scenes[data.gltf.scene if data.gltf.scene else 0]
    if not scene.nodes:
        return []

    return [nodes[root] for root in scene.nodes]
