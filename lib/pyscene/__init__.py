from .facemesh import FaceMesh
from .submesh_mesh import SubmeshMesh, Submesh
from .node import Node, Skin
from .material import UnlitMaterial, PBRMaterial, MToonMaterial, Texture, BlendMode, TextureUsage
from .from_gltf import nodes_from_gltf, load
from .to_gltf import to_gltf
from .to_submesh import facemesh_to_submesh
from .modifier import before_import
from .vrm_loader import Vrm, VrmExpression, VrmExpressionPreset


def reload():
    print(f'reload {__file__}')
    from . import facemesh, submesh_mesh, node, material, from_gltf, to_submesh, modifier, vrm_loader
    import importlib
    for m in [
            facemesh, submesh_mesh, node, material, from_gltf, to_submesh,
            modifier, vrm_loader
    ]:
        importlib.reload(m)