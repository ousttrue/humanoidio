from typing import NamedTuple, Any, List
import bpy


class GroupInput(NamedTuple):
    name: str
    socket_type: str
    default_value: Any = None


def nodegroup_from_inputs(
        group_name: str, inputs: List['GroupInput']) -> bpy.types.NodeTree:

    g = bpy.data.node_groups.new(group_name, type='ShaderNodeTree')

    # inputs
    for i in inputs:
        socket = g.inputs.new(f'NodeSocket{i.socket_type}', i.name)
        if i.default_value != None:
            socket.default_value = i.default_value

    return g
