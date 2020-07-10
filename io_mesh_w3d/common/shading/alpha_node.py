# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.types import Node


class AlphaNode(Node):
    bl_idname = 'CustomNodeType'
    # Label for nice name display
    bl_label = "Custom Node"
    # Icon identifier
    bl_icon = 'SOUND'

    my_string_prop: bpy.props.StringProperty()
    my_float_prop: bpy.props.FloatProperty(default=3.1415926)


    def init(self, context):
        self.inputs.new('NodeSocketFloat', "World")
        self.inputs.new('NodeSocketVector', "!")

        self.outputs.new('NodeSocketColor', "How")
        self.outputs.new('NodeSocketColor', "are")
        self.outputs.new('NodeSocketFloat', "you")

    def update(self):
        print('UPDATE!!!!')