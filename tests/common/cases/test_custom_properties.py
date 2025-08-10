# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from tests.utils import *


def to_vec4(color):
    return color[0], color[1], color[2], color[3]


def to_vec3(vec):
    return vec[0], vec[1], vec[2]


def to_vec2(vec):
    return vec[0], vec[1]


class TestCustomProperties(TestCase):
    def test_object_properties(self):
        mesh = bpy.data.meshes.new('mesh')
        obj = bpy.data.objects.new('object', mesh)

        self.assertEqual('', obj.data.userText)
        obj.data.userText = 'lorem ipsum'
        self.assertEqual('lorem ipsum', obj.data.userText)

        object_types = ['MESH', 'BOX', 'DAZZLE']

        self.assertEqual('MESH', obj.data.object_type)
        for object_type in object_types:
            obj.data.object_type = object_type
            self.assertEqual(object_type, obj.data.object_type)

        with self.assertRaises(TypeError):
            obj.data.object_type = 'INVALID'

        dazzle_types = ['DEFAULT', 'SUN', 'REN_L5_STREETLIGHT', 'REN_BRAKELIGHT',
                        'REN_HEADLIGHT', 'REN_L5_REDLIGHT', 'REN_NUKE', 'REN_BLINKLIGHT_RED',
                        'REN_BLINKLIGHT_WHITE', 'REN_VEHICLELIGHT_RED', 'REN_VEHICLELIGHT_WHITE']

        self.assertEqual('DEFAULT', obj.data.dazzle_type)
        for dazzle_type in dazzle_types:
            obj.data.dazzle_type = dazzle_type
            self.assertEqual(dazzle_type, obj.data.dazzle_type)

        with self.assertRaises(TypeError):
            obj.data.dazzle_type = 'INVALID'

    def test_material_properties(self):
        mat = bpy.data.materials.new('material')

        attributes = ['USE_DEPTH_CUE', 'ARGB_EMISSIVE_ONLY',
                      'COPY_SPECULAR_TO_DIFFUSE', 'DEPTH_CUE_TO_ALPHA']

        # attributes
        self.assertEqual(0, len(mat.attributes))

        # TODO: get to work
        # for attr in attributes:
        #atts = { 'DEFAULT' }
        #    mat.attributes.add(attr)
        #    self.assertEqual({ attr }, mat.attributes)

        # for attr in attributes:
        #    mat.attributes |= attr

        #self.assertEqual(16, mat.attributes)

        # with self.assertRaises(TypeError):
        #    mat.attributes = 'INVALID'

        # surface types
        self.assertEqual('13', mat.surface_type)

        for i in range(32):
            mat.surface_type = str(i)
            self.assertEqual(str(i), mat.surface_type)

        with self.assertRaises(TypeError):
            mat.surface_type = '32'

        self.assertEqual(0, mat.technique)
        mat.technique = -1
        self.assertEqual(0, mat.technique)
        # mat.technique = 2
        # self.assertEqual(1, mat.technique) # technique can be any index, no need to clamp to 0-1

        # other props

        ##### DO WE REALLY NEED TO ASSERT THESE CUSTOM PREPERTIES? 

        # self.assertEqual(0.0, mat.translucency)
        # mat.translucency = -1.0
        # self.assertEqual(0.0, mat.translucency)
        # mat.translucency = 2.0
        # self.assertEqual(1.0, mat.translucency)

        # self.assertEqual('', mat.vm_args_0)
        # mat.vm_args_0 = 'lorem ipsum'
        # self.assertEqual('lorem ipsum', mat.vm_args_0)

        # self.assertEqual('', mat.vm_args_1)
        # mat.vm_args_1 = 'lorem ipsum'
        # self.assertEqual('lorem ipsum', mat.vm_args_1)



        # self.assertEqual((1.0, 1.0, 1.0, 0.0), to_vec4(mat.ambient_color4))
        # mat.ambient = (-1.0, -1.0, -1.0, -1.0)
        # self.assertEqual((0.0, 0.0, 0.0, 0.0), to_vec4(mat.ambient_color4))
        # mat.ambient = (2.0, 2.0, 2.0, 2.0)
        # self.assertEqual((1.0, 1.0, 1.0, 1.0), to_vec4(mat.ambient_color4))

        # self.assertEqual(True, mat.alpha_test)

        # self.assertEqual(0, mat.blend_mode)

        # self.assertEqual((0.0, 0.0), to_vec2(mat.bump_uv_scale))

        # self.assertEqual(0, mat.edge_fade_out)

        # self.assertEqual(False, mat.depth_write)

        # self.assertEqual((0.0, 0.0, 0.0), to_vec3(mat.sampler_clamp_uv_no_mip_0))

        # self.assertEqual((0.0, 0.0, 0.0), to_vec3(mat.sampler_clamp_uv_no_mip_1))

        # self.assertEqual(0, mat.num_textures)

        # self.assertEqual('', mat.texture_1)

        # self.assertEqual(0, mat.secondary_texture_blend_mode)

        # self.assertEqual(0, mat.tex_coord_mapper_0)

        # self.assertEqual(0, mat.tex_coord_mapper_1)

        # self.assertEqual((0.0, 0.0, 0.0, 0.0), to_vec4(mat.tex_coord_transform_0))

        # self.assertEqual((0.0, 0.0, 0.0, 0.0), to_vec4(mat.tex_coord_transform_1))

        # self.assertEqual('', mat.environment_texture)

        # self.assertEqual(0.0, mat.environment_mult)

        # self.assertEqual('', mat.recolor_texture)

        # self.assertEqual(0.0, mat.recolor_mult)

        # self.assertEqual(False, mat.use_recolor)

        # self.assertEqual(False, mat.house_color_pulse)

        # self.assertEqual('', mat.scrolling_mask_texture)

        # self.assertEqual(0.0, mat.tex_coord_transform_angle)

        # self.assertEqual(0.0, mat.tex_coord_transform_u_0)

        # self.assertEqual(0.0, mat.tex_coord_transform_v_0)

        # self.assertEqual(0.0, mat.tex_coord_transform_u_1)

        # self.assertEqual(0.0, mat.tex_coord_transform_v_1)

        # self.assertEqual(0.0, mat.tex_coord_transform_u_2)

        # self.assertEqual(0.0, mat.tex_coord_transform_v_2)

        # self.assertEqual((0.0, 0.0, 0.0, 0.0), to_vec4(mat.tex_ani_fps_NPR_lastFrame_frameOffset_0))

        # # shader properties
        # shader = mat.shader

        # self.assertEqual('3', shader.depth_compare)
        # self.assertEqual('1', shader.depth_mask)
        # self.assertEqual(0, shader.color_mask)
        # self.assertEqual('0', shader.dest_blend)
        # self.assertEqual(0, shader.fog_func)
        # self.assertEqual('1', shader.pri_gradient)
        # self.assertEqual('0', shader.sec_gradient)
        # self.assertEqual('1', shader.src_blend)
        # self.assertEqual('0', shader.detail_color_func)
        # self.assertEqual('0', shader.detail_alpha_func)
        # self.assertEqual(0, shader.shader_preset)
        # self.assertEqual('0', shader.alpha_test)
        # self.assertEqual('0', shader.post_detail_color_func)
        # self.assertEqual('0', shader.post_detail_alpha_func)
