from logging import getLogger

logger = getLogger(__name__)

import pathlib
from typing import Tuple, List, Optional, Union
import json
from .mesh import (Submesh, Mesh)
from .util import (get_glb_chunks, Coodinate, Conversion)


class Skin:
    def __init__(self):
        self.joints: List[Node] = []


class Node:
    def __init__(self, name: str):
        self.name = name
        self.children: List[Node] = []
        self.parent: Optional[Node] = None
        self.translation: Tuple[float, float, float] = (0, 0, 0)
        self.rotation: Tuple[float, float, float, float] = (0, 0, 0, 1)
        self.scale: Tuple[float, float, float] = (1, 1, 1)
        self.mesh: Optional[Mesh] = None
        self.skin: Optional[Skin] = None
        self.humanoid_bone = None

    def add_child(self, child: 'Node'):
        child.parent = self
        self.children.append(child)

    def traverse(self):
        yield self
        for child in self.children:
            for x in child.traverse():
                yield x


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

    def _load_mesh(self, data: util.GltfAccessor, i: int, m):
        mesh = Mesh(m.get('name', f'mesh{i}'))

        index_offset = 0
        vertex_offset = 0
        for prim in m['primitives']:
            count = data.gltf['accessors'][prim['indices']]['count']
            sm = Submesh(index_offset, count)
            sm.vertex_offset = vertex_offset
            vertex_offset += data.gltf['accessors'][prim['attributes']
                                                    ['POSITION']]['count']
            index_offset += count

            mesh.submeshes.append(sm)
            for k, v in prim['attributes'].items():
                sm.set_attribute(k, data.accessor_generator(v))
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

    def load(self, data: util.GltfAccessor):
        #
        # extensions
        #
        if 'extensions' in data.gltf:
            if 'VRM' in data.gltf['extensions']:
                self.vrm = Vrm0(data.gltf['extensions']['VRM'])
                data.conversion = Conversion(Coodinate.VRM0,
                                             data.conversion.dst)
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


def load_glb(src: pathlib.Path, conv: Coodinate) -> Tuple[Loader, Conversion]:
    json_chunk, bin_chunk = get_glb_chunks(src.read_bytes())
    gltf = json.loads(json_chunk)

    data = util.GltfAccessor(gltf, bin_chunk, conv)
    loader = Loader()
    loader.load(data)
    return loader, data.conversion


def load_gltf(src: pathlib.Path, conv: Coodinate) -> Tuple[Loader, Conversion]:
    raise NotImplementedError()


def load(src: pathlib.Path, conv: Coodinate) -> Tuple[Loader, Conversion]:
    if src.suffix == '.gltf':
        return load_gltf(src, conv)
    else:
        return load_glb(src, conv)
