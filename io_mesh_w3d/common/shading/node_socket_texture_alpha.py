# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.types import NodeSocketFloat, NodeSocketInterfaceFloat


class NodeSocketTextureAlpha(NodeSocketInterfaceFloat, NodeSocketFloat):
    bl_idname = 'NodeSocketTextureAlpha'
    bl_label = 'Texture Alpha Node Socket'

    float_prop: bpy.props.FloatProperty(
        name='Texture Alpha',
        default=1.0,
        min=0.0, max=1.0,
        description='Texture alpha property')

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "float_prop", text=text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)
