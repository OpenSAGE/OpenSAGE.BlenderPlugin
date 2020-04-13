# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.types import NodeSocket


class NodeSocketVector4(NodeSocket):
    bl_idname = 'NodeSocketVector4'
    bl_label = 'Vector4 Node Socket'

    vec2_prop: bpy.props.FloatVectorProperty(
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
            layout.prop(self, "vec2_prop", text=text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)
