# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.types import Node


class DecisionNode(Node):
    bl_idname = 'DecisionNode'
    bl_label = 'Decision Node'

    def init(self, context):
        self.inputs.new('NodeSocketBool', 'decide')
        self.inputs.new('NodeSocketFloat', 'value1')
        self.inputs.new('NodeSocketFloat', 'value2')

        self.outputs.new('NodeSocketFloat', 'value')

    def copy(self, node):
        print('Copying from node ', node)

    def free(self):
        print('Removing node ', self, ', Goodbye!')

    def draw_label(self):
        return 'Decision'