from typing import NamedTuple
import bpy


class WrapNode(NamedTuple):
    links: bpy.types.NodeLinks
    node: bpy.types.ShaderNode

    def connect(self, dst_input, src_node: 'WrapNode', src_output=0):
        '''
        dst から src に link する

        self.node.inputs[dst_input] <= src_node.outputs[src_output]
        '''
        self.links.new(src_node.node.outputs[src_output],
                       self.node.inputs[dst_input])  # type: ignore

    def set_default_value(self, input, value):
        self.node.inputs[input].default_value = value  # type: ignore

    def set_image(self, image: bpy.types.Image):
        self.node.image = image  # type: ignore


class WrapNodeFactory:
    def __init__(self, node_tree: bpy.types.NodeTree):
        self.node_tree = node_tree

    def create(self, name: str, x=0, y=0) -> WrapNode:
        if not name.startswith("ShaderNode"):
            name = "ShaderNode" + name
        node = self.node_tree.nodes.new(type=name)
        node.location = (x, y)
        node.select = False

        # return node
        return WrapNode(self.node_tree.links, node)
