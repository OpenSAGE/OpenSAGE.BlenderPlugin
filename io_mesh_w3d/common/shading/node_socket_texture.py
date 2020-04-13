# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.types import NodeSocketColor


class NodeSocketTexture(NodeSocketColor):
    bl_idname = 'NodeSocketTexture'
    bl_label = 'Texture Node Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)
