# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.types import NodeSocketColor, NodeSocketInterfaceColor


# this does not work yet, since the type of these sockets seems to be 'RGBA', but if connected
# only the red channel seems to be used....
# How to set the type properly??

class NodeSocketInterfaceTexture(NodeSocketInterfaceColor):
    bl_socket_idname = 'NodeSocketTexture'
    type = 'STRING'

    def draw(self, context, layout):
        pass

    def draw_color(self, context):
        return (1.0, 0.4, 0.216, 0.5)

    @staticmethod
    def register_classes():
        bpy.utils.register_class(NodeSocketInterfaceTexture)
        bpy.utils.register_class(NodeSocketTexture)

    @staticmethod
    def unregister_classes():
        bpy.utils.unregister_class(NodeSocketTexture)
        bpy.utils.unregister_class(NodeSocketInterfaceTexture)


class NodeSocketTexture(NodeSocketColor):
    bl_idname: 'NodeSocketTexture'

    default_value: bpy.props.FloatVectorProperty(
        name='texture',
        subtype='COLOR',
        size=4,
        default=(0.0, 0.0, 0.0, 0.0),
        description='Texture')

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)
