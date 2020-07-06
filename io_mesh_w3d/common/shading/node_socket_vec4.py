# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.types import NodeSocketInterfaceVector, NodeSocketVector


class NodeSocketInterfaceVector4(NodeSocketInterfaceVector):
    bl_socket_idname = 'NodeSocketVector4'

    default_value = (0.0, 0.0, 0.0, 0.0)

    def draw(self, context, layout):
        pass

    def draw_color(self, context):
        return (1.0, 0.4, 0.216, 0.5)

    @staticmethod
    def register_classes():
        bpy.utils.register_class(NodeSocketInterfaceVector4)
        bpy.utils.register_class(NodeSocketVector4)

    @staticmethod
    def unregister_classes():
        bpy.utils.unregister_class(NodeSocketVector4)
        bpy.utils.unregister_class(NodeSocketInterfaceVector4)


class NodeSocketVector4(NodeSocketVector):
    bl_idname = 'NodeSocketVector4'
    bl_label = 'Vector4 Node Socket'

    default_value: bpy.props.FloatVectorProperty(
        name='Vector4',
        subtype='TRANSLATION',
        size=4,
        default=(0.0, 0.0, 0.0, 0.0),
        min=0.0, max=1.0,
        description='Vector 4')

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, 'default_value', text=text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)