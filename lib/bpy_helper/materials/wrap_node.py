from typing import NamedTuple
import bpy


class WrapNode(NamedTuple):
    links: bpy.types.NodeLinks
    node: bpy.types.ShaderNode

    def link(self, input, src_node: 'WrapNode', output=0):
        self.links.new(src_node.node.outputs[output],
                       self.node.inputs[input])  # type: ignore

    def set_default_value(self, input, value):
        self.node.inputs[input].default_value = value  # type: ignore
