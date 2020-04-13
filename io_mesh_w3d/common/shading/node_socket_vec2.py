# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.types import NodeSocket


class NodeSocketVector2(NodeSocket):
    bl_idname = 'NodeSocketVector2'
    bl_label = 'Vector2 Node Socket'

    vec2_prop: bpy.props.FloatVectorProperty(
        name='Vector2',
        subtype='TRANSLATION',
        size=2,
        default=(0.0, 0.0),
        min=0.0, max=1.0,
        description='Vector 2')

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "vec2_prop", text=text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)
