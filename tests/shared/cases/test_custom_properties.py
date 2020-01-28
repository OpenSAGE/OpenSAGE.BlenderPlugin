# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from io_mesh_w3d.struct import Struct
from io_mesh_w3d.custom_properties import *
from tests.utils import *


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
            obj.object_type = 'INVALID'

        dazzle_types = ['DEFAULT', 'SUN', 'REN_L5_STREETLIGHT', 'REN_BRAKELIGHT', \
                'REN_HEADLIGHT', 'REN_L5_REDLIGHT', 'REN_NUKE', 'REN_BLINKLIGHT_RED', \
                'REN_BLINKLIGHT_WHITE', 'REN_VEHICLELIGHT_RED', 'REN_VEHICLELIGHT_WHITE']

        self.assertEqual('DEFAULT', obj.dazzle_type)
        for dazzle_type in dazzle_types:
            obj.dazzle_type = dazzle_type
            self.assertEqual(dazzle_type, obj.dazzle_type)

        with self.assertRaises(TypeError):
            obj.dazzle_type = 'INVALID'

    def test_material_properties(self):
        mat = bpy.data.materials.new('material')

        attributes = ['USE_DEPTH_CUE', 'ARGB_EMISSIVE_ONLY', \
                'COPY_SPECULAR_TO_DIFFUSE', 'DEPTH_CUE_TO_ALPHA']

        # attributes
        self.assertEqual(0, len(mat.attributes))

        # TODO: get to work
        #for attr in attributes:
            #atts = { 'DEFAULT' }
        #    mat.attributes.add(attr)
        #    self.assertEqual({ attr }, mat.attributes)

        #for attr in attributes:
        #    mat.attributes |= attr

        #self.assertEqual(16, mat.attributes)

        #with self.assertRaises(TypeError):
        #    mat.attributes = 'INVALID'

        # surface types
        self.assertEqual('13', mat.surface_type)

        for i in range(32):
            mat.surface_type = str(i)
            self.assertEqual(str(i), mat.surface_type)

        with self.assertRaises(TypeError):
            mat.surface_type = '32'

        # other props

        self.assertEqual(0.0, mat.translucency)
        mat.translucency = -1.0
        self.assertEqual(0.0, mat.translucency)
        mat.translucency = 2.0
        self.assertEqual(1.0, mat.translucency)

        self.assertEqual('', mat.vm_args_0)
        mat.vm_args_0 = 'lorem ipsum'
        self.assertEqual('lorem ipsum', mat.vm_args_0)

        self.assertEqual('', mat.vm_args_1)
        mat.vm_args_1 = 'lorem ipsum'
        self.assertEqual('lorem ipsum', mat.vm_args_1)

        self.assertEqual(0, mat.technique)
        mat.technique = -1
        self.assertEqual(0, mat.technique)
        mat.technique = 2
        self.assertEqual(1, mat.technique)

        # TODO other props
