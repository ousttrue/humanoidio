from logging import getLogger

logger = getLogger(__name__)

import pathlib
from typing import Tuple, List, Union
import json
from .mesh import (Submesh, VertexBuffer, Mesh)
from .glb import get_glb_chunks
from .accessor_util import GltfAccessor
from .coordinate import (Coordinate, Conversion)
from .node import (Node, Skin)
from .humanoid import HumanoidBones


class Vrm0:
    def __init__(self, src):
        self.data = src


class Vrm1:
    def __init__(self, src):
        self.data = src


class Loader:
    def __init__(self):
        self.meshes: List[Mesh] = []
        self.nodes: List[Node] = []
        self.roots: List[Node] = []
        self.vrm: Union[Vrm0, Vrm1, None] = None

    def _load_mesh(self, data: GltfAccessor, i: int, m):
        mesh = Mesh(m.get('name', f'mesh{i}'))

        index_offset = 0
        vertex_offset = 0
        for prim in m['primitives']:
            count = data.gltf['accessors'][prim['indices']]['count']
            sm = Submesh(index_offset, count)
            sm.vertices = VertexBuffer()
            sm.vertex_offset = vertex_offset
            vertex_offset += data.gltf['accessors'][prim['attributes']
                                                    ['POSITION']]['count']
            index_offset += count

            mesh.submeshes.append(sm)
            for k, v in prim['attributes'].items():
                sm.vertices.set_attribute(k, data.accessor_generator(v))
            sm.indices = data.accessor_generator(prim['indices'])

        return mesh

    def _load_node(self, i: int, n):
        name = n.get('name', f'node_{i}')
        node = Node(name)

        node.translation = n.get('translation', (0, 0, 0))
        node.rotation = n.get('rotation', (0, 0, 0, 1))
        node.scale = n.get('scale', (1, 1, 1))
        if 'matrix' in n:
            raise NotImplementedError('node.matrix')

        if 'mesh' in n:
            node.mesh = self.meshes[n['mesh']]

        return node

    def load(self, data: GltfAccessor):
        #
        # extensions
        #
        if 'extensions' in data.gltf:
            if 'VRM' in data.gltf['extensions']:
                self.vrm = Vrm0(data.gltf['extensions']['VRM'])
            elif 'VRMC_vrm' in data.gltf['extensions']:
                self.vrm = Vrm1(data.gltf['extensions']['VRMC_vrm'])

        #
        # mesh
        #
        for i, m in enumerate(data.gltf['meshes']):
            mesh = self._load_mesh(data, i, m)
            self.meshes.append(mesh)

        #
        # node
        #
        for i, n in enumerate(data.gltf['nodes']):
            node = self._load_node(i, n)
            self.nodes.append(node)

        for i, n in enumerate(data.gltf['nodes']):
            node = self.nodes[i]
            for child_index in n.get('children', []):
                node.add_child(self.nodes[child_index])

            if 'skin' in n:
                s = data.gltf['skins'][n['skin']]
                node.skin = Skin()
                for j in s['joints']:
                    node.skin.joints.append(self.nodes[j])

        for node in self.nodes:
            if not node.parent:
                self.roots.append(node)

        #
        # vrm
        #
        if isinstance(self.vrm, Vrm0):
            for b in self.vrm.data['humanoid']['humanBones']:
                node = self.nodes[b['node']]
                node.humanoid_bone = HumanoidBones.from_name(b['bone'])
        elif isinstance(self.vrm, Vrm1):
            for k, b in self.vrm.data['humanoid']['humanBones'].items():
                node = self.nodes[b['node']]
                node.humanoid_bone = HumanoidBones.from_name(k)


def load_glb(path: pathlib.Path, dst: Coordinate) -> Tuple[Loader, Conversion]:
    json_chunk, bin_chunk = get_glb_chunks(path.read_bytes())
    gltf = json.loads(json_chunk)

    data = GltfAccessor(gltf, bin_chunk)
    loader = Loader()
    loader.load(data)
    src = Coordinate.GLTF
    if isinstance(loader.vrm, Vrm0):
        src = Coordinate.VRM0
    return loader, Conversion(src, dst)


def load_gltf(src: pathlib.Path,
              conv: Coordinate) -> Tuple[Loader, Conversion]:
    raise NotImplementedError()


def load(src: pathlib.Path, conv: Coordinate) -> Tuple[Loader, Conversion]:
    if src.suffix == '.gltf':
        return load_gltf(src, conv)
    else:
        return load_glb(src, conv)
