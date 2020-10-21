'''
* serialize: pyscene => GLTF
* deserialize: GLTF => pyscene
'''
from logging import getLogger
logger = getLogger(__name__)
from typing import List, Tuple, Any
import bpy, mathutils
from ..formats.gltf_context import GltfContext
from .bytesreader import BytesReader
from ..exporter import scene_scanner
from .. import pyscene
from ..pyscene import material
from ..pyscene.submesh_mesh import SubmeshMesh
from ..pyscene.facemesh import FaceMesh
from ..pyscene.to_submesh import facemesh_to_submesh
from ..formats import gltf, buffermanager
from ..struct_types import Float3



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


GLTF_VERSION = '2.0'
GENERATOR_NAME = 'scene_translator'


def get_min_max3(buffer: memoryview) -> Tuple[List[float], List[float]]:
    Vector3Array = (Float3 * len(buffer))
    values = Vector3Array.from_buffer(buffer)
    min: List[float] = [float('inf')] * 3
    max: List[float] = [float('-inf')] * 3
    for v in values:
        if v.x < min[0]:
            min[0] = v.x
        if v.x > max[0]:
            max[0] = v.x
        if v.y < min[1]:
            min[1] = v.y
        if v.y > max[1]:
            max[1] = v.y
        if v.z < min[2]:
            min[2] = v.z
        if v.z > max[2]:
            max[2] = v.z
    return min, max


class GltfExporter:
    def __init__(self):
        self.buffer = buffermanager.BufferManager()
        self.buffers = [self.buffer]
        self.material_store = material.MaterialStore()
        self.meshes: List[gltf.Mesh] = []
        self.skins: List[gltf.Skin] = []
        self.nodes: List[gltf.Node] = []

    def to_gltf_mesh(self, mesh: SubmeshMesh) -> gltf.Mesh:
        '''
        UniVRM compatible shared attributes and targets
        '''
        # attributes
        attributes = {
            'POSITION':
            self.buffer.push_bytes(f'{mesh.name}.POSITION',
                                   memoryview(mesh.attributes.position),
                                   get_min_max3),
            'NORMAL':
            self.buffer.push_bytes(f'{mesh.name}.NORMAL',
                                   memoryview(mesh.attributes.normal)),
        }
        if mesh.attributes.texcoord:
            attributes['TEXCOORD_0'] = self.buffer.push_bytes(
                f'{mesh.name}.TEXCOORD_0',
                memoryview(mesh.attributes.texcoord))
        if mesh.attributes.joints and mesh.attributes.weights:
            attributes['JOINTS_0'] = self.buffer.push_bytes(
                f'{mesh.name}.JOINTS_0', memoryview(mesh.attributes.joints))
            attributes['WEIGHTS_0'] = self.buffer.push_bytes(
                f'{mesh.name}.WEIGHTS_0', memoryview(mesh.attributes.weights))

        # morph targets
        targets = []
        target_names = []
        for k, v in mesh.morph_map.items():
            zero = (Float3 * (len(v)))()
            target = {
                'POSITION':
                self.buffer.push_bytes(f'{mesh.name}.targets[{k}].POSITION',
                                       v,
                                       get_min_max3,
                                       use_sparse=True),
                'NORMAL':
                self.buffer.push_bytes(f'{mesh.name}.targets[{k}].NORMAL',
                                       memoryview(zero),
                                       use_sparse=True)
            }
            targets.append(target)
            target_names.append(k)

        primitives = []
        offset = 0
        for i, submesh in enumerate(mesh.submeshes):
            # submesh indices
            indices = mesh.indices[offset:offset + submesh.vertex_count]
            offset += submesh.vertex_count
            indices_accessor_index = self.buffer.push_bytes(
                f'{mesh.name}[{i}].INDICES', memoryview(indices))

            primitive = gltf.MeshPrimitive(
                attributes=attributes,
                indices=indices_accessor_index,
                material=self.material_store.get_material_index(
                    submesh.material, self.buffer),
                mode=gltf.MeshPrimitiveMode.TRIANGLES,
                targets=targets,
                extensions={},
                extras={}
                # gltf.MeshPrimitiveExtra(target_names)
            )
            primitives.append(primitive)

        return gltf.Mesh(name=mesh.name,
                         primitives=primitives,
                         extensions={},
                         extras={})

    def to_gltf_node(self, node: scene_scanner.Node,
                     nodes: List[scene_scanner.Node],
                     skins: List[scene_scanner.Node],
                     meshes: List[FaceMesh]) -> gltf.Node:
        p = node.get_local_position()
        name = node.name
        if node.mesh:
            name = 'mesh.' + name
        return gltf.Node(
            name=name,
            children=[nodes.index(child) for child in node.children],
            translation=(p.x, p.y, p.z),
            mesh=meshes.index(node.mesh) if node.mesh else None,
            skin=skins.index(node.skin) if node.skin else None)

    def to_gltf_skin(self, skin: scene_scanner.Node,
                     nodes: List[scene_scanner.Node]):
        joints = [joint for joint in skin.traverse()][1:]

        matrices = (Matrix4 * len(joints))()
        for i, _ in enumerate(joints):
            p = joints[i].position
            matrices[i] = Matrix4.translation(-p.x, -p.y, -p.z)
        matrix_index = self.buffer.push_bytes(
            f'{skin.name}.inverseBindMatrices',
            memoryview(matrices))  # type: ignore

        return gltf.Skin(name=skin.name,
                         inverseBindMatrices=matrix_index,
                         skeleton=nodes.index(skin),
                         joints=[nodes.index(joint) for joint in joints])

    def export_vrm(self, nodes: List[scene_scanner.Node], version: str,
                   title: str, author: str):
        humanoid_bones = [node for node in nodes if node.humanoid_bone]
        if humanoid_bones:
            meta = {
                'version': version,
                'title': title,
                'author': author,
                'contactInformation': '',
                'reference': '',
                'texture': -1,
                'allowedUserName': 'OnlyAuthor',
                'violentUssageName': 'Disallow',
                'sexualUssageName': 'Disallow',
                'commercialUssageName': 'Disallow',
                'otherPermissionUrl': '',
                'licenseName': 'Redistribution_Prohibited',
                'otherLicenseUrl': '',
            }
            VRM = {
                'exporterVersion':
                'bl_vrm-0.1',
                'specVersion':
                '0.0',
                'meta':
                meta,
                'humanoid': {
                    'humanBones': [{
                        'bone': node.humanoid_bone.name,
                        'node': nodes.index(node)
                    } for node in humanoid_bones]
                },
                'firstPerson': {},
                'blendShapeMaster': {},
                'secondaryAnimation': {
                    'boneGroups': [],
                    'colliderGroups': []
                },
                'materialProperties': [{
                    'shader': 'VRM_USE_GLTFSHADER',
                    'floatProperties': {},
                    'vectorProperties': {},
                    'textureProperties': {},
                    'keywordMap': {},
                    'tagMap': {}
                } for material in self.material_store.materials]
            }
            return VRM

    def export(self, scanner: scene_scanner.Scanner,
               separate_images: bool) -> Tuple[gltf.glTF, List[Any]]:
        for mesh in scanner.meshes:
            logger.debug(mesh)
            skin = scanner.get_skin_for_store(mesh)
            bone_names: List[str] = []
            if skin:
                bone_names = [joint.name for joint in skin.traverse()][1:]
            submesh_mesh = facemesh_to_submesh(mesh, bone_names)
            logger.debug(submesh_mesh)
            self.meshes.append(self.to_gltf_mesh(submesh_mesh))

        # node
        skins = [skin for skin in scanner.skin_map.values()]
        for node in scanner._nodes:
            gltf_node = self.to_gltf_node(node, scanner._nodes, skins,
                                          scanner.meshes)
            self.nodes.append(gltf_node)

        roots = [
            scanner._nodes.index(root) for root in scanner.get_root_nodes()
        ]

        for skin in scanner.skin_map.values():
            gltf_skin = self.to_gltf_skin(skin, scanner._nodes)
            self.skins.append(gltf_skin)

        extensionsUsed = ['KHR_materials_unlit']
        vrm = self.export_vrm(scanner._nodes, scanner.vrm.version,
                              scanner.vrm.title, scanner.vrm.author)
        # if vrm:
        #     extensionsUsed.append('VRM')

        data = gltf.glTF(
            asset=gltf.Asset(generator=GENERATOR_NAME, version=GLTF_VERSION),
            buffers=[gltf.Buffer(byteLength=len(self.buffer.buffer.data))],
            bufferViews=self.buffer.views,
            accessors=self.buffer.accessors,
            images=self.material_store.images,
            samplers=self.material_store.samplers,
            textures=self.material_store.textures,
            materials=self.material_store.materials,
            nodes=self.nodes,
            meshes=self.meshes,
            skins=self.skins,
            scenes=[gltf.Scene(name='main', nodes=roots)],
            extensionsUsed=extensionsUsed,
            # extensions={'VRM': vrm}
        )

        return data, self.buffers


def export(scanner: scene_scanner.Scanner,
           separate_images: bool = False) -> Tuple[gltf.glTF, List[Any]]:
    exporter = GltfExporter()
    return exporter.export(scanner, separate_images)
