# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.types import NodeSocketInterfaceFloat, NodeSocketFloat


class NodeSocketInterfaceTextureAlpha(NodeSocketInterfaceFloat):
    bl_socket_idname = 'NodeSocketTextureAlpha'

    default_value = 0.0

    def draw(self, context, layout):
        pass

    def draw_color(self, context):
        return (1.0, 0.4, 0.216, 0.5)

    @staticmethod
    def register_classes():
        bpy.utils.register_class(NodeSocketInterfaceTextureAlpha)
        bpy.utils.register_class(NodeSocketTextureAlpha)

    @staticmethod
    def unregister_classes():
        bpy.utils.unregister_class(NodeSocketTextureAlpha)
        bpy.utils.unregister_class(NodeSocketInterfaceTextureAlpha)


class NodeSocketTextureAlpha(NodeSocketFloat):
    bl_idname = 'NodeSocketTextureAlpha'
    bl_label = 'Texture Alpha Node Socket'

    default_value: bpy.props.FloatProperty(
        name='Texture Alpha',
        description='the alpha value of a texture',
        default=1.0)

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, 'default_value', text=text)

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5) 