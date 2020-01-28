# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from tests.utils import *
from io_mesh_w3d.custom_properties import *

#material = bpy.data.materials.new(mesh.name() + '.ShaderMaterial' + index)

class TestCustomProperties(TestCase):
    def test_object_properties(self):
        mesh = bpy.data.meshes.new('mesh')
        obj = bpy.data.objects.new('object', mesh)

        self.assertEqual('', obj.userText)
        obj.userText = 'lorem ipsum'
        self.assertEqual('lorem ipsum', obj.userText)

        object_types = ['NORMAL', 'BOX', 'DAZZLE']

        self.assertEqual('NORMAL', obj.object_type)
        for object_type in object_types:
            obj.object_type = object_type
            self.assertEqual(object_type, obj.object_type)

        with self.assertRaises(TypeError):
            obj.object_type = 'UNSUPPORTED'

        dazzle_types = ['DEFAULT', 'SUN', 'REN_L5_STREETLIGHT', 'REN_BRAKELIGHT', \
                'REN_HEADLIGHT', 'REN_L5_REDLIGHT', 'REN_NUKE', 'REN_BLINKLIGHT_RED', \
                'REN_BLINKLIGHT_WHITE', 'REN_VEHICLELIGHT_RED', 'REN_VEHICLELIGHT_WHITE']

        self.assertEqual('DEFAULT', obj.dazzle_type)
        for dazzle_type in dazzle_types:
            obj.dazzle_type = dazzle_type
            self.assertEqual(dazzle_type, obj.dazzle_type)

        with self.assertRaises(TypeError):
            obj.dazzle_type = 'UNSUPPORTED'

    def test_object_panel_draw(self):
        bpy.utils.register_class(OBJECT_PANEL_PT_w3d)
        #OBJECT_PANEL_PT_w3d(None).draw(context)
        #panel.draw(context)
     