# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.types import NodeSocketInt


class NodeSocketEnum(NodeSocketInt):
    bl_idname = 'NodeSocketEnum'
    bl_label = 'Enum Node Socket'

    default_value: bpy.props.EnumProperty(
        name="Direction",
        description="Just an example",
        items=[
            ('DOWN', "Down", "Where your feet are"),
            ('UP', "Up", "Where your head should be"),
            ('LEFT', "Left", "Not right"),
            ('RIGHT', "Right", "Not left")],
        default='UP')

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, 'default_value', text=text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)

class NodeSocketMaterialAttributes(NodeSocketEnum):
    bl_idname = 'NodeSocketMaterialAttributes'
    bl_label = 'Material Attributes Enum Flag Node Socket'

    default_value: bpy.props.EnumProperty(
        name='Attributes',
        description='Attributes that define the behaviour of this material',
        items=[
            ('DEFAULT', 'Default', 'desc: todo', 0),
            ('USE_DEPTH_CUE', 'UseDepthCue', 'desc: todo', 1),
            ('ARGB_EMISSIVE_ONLY', 'ArgbEmissiveOnly', 'desc: todo', 2),
            ('COPY_SPECULAR_TO_DIFFUSE', 'CopySpecularToDiffuse', 'desc: todo', 4),
            ('DEPTH_CUE_TO_ALPHA', 'DepthCueToAlpha', 'desc: todo', 8)],
        default=set(),
        options={'ENUM_FLAG'})