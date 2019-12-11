# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest

from io_mesh_w3d.structs_w3d.w3d_shader import Shader


def get_shader():
    return Shader(
        depth_compare=4,
        depth_mask=100,
        color_mask=44,
        dest_blend=6,
        fog_func=123,
        pri_gradient=90,
        sec_gradient=45,
        src_blend=42,
        texturing=11,
        detail_color_func=3,
        detail_alpha_func=7,
        shader_preset=8,
        alpha_test=83,
        post_detail_color_func=245,
        post_detail_alpha_func=32,
        pad=0)


def compare_shaders(self, expected, actual):
    self.assertEqual(expected.depth_compare, actual.depth_compare)
    self.assertEqual(expected.depth_mask, actual.depth_mask)
    self.assertEqual(expected.color_mask, actual.color_mask)
    self.assertEqual(expected.dest_blend, actual.dest_blend)
    self.assertEqual(expected.fog_func, actual.fog_func)
    self.assertEqual(expected.pri_gradient, actual.pri_gradient)
    self.assertEqual(expected.sec_gradient, actual.sec_gradient)
    self.assertEqual(expected.src_blend, actual.src_blend)
    self.assertEqual(expected.texturing, actual.texturing)
    self.assertEqual(expected.detail_color_func, actual.detail_color_func)
    self.assertEqual(expected.detail_alpha_func, actual.detail_alpha_func)

    self.assertEqual(expected.shader_preset, actual.shader_preset)
    self.assertEqual(expected.alpha_test, actual.alpha_test)
    self.assertEqual(expected.post_detail_color_func,
                     actual.post_detail_color_func)
    self.assertEqual(expected.post_detail_alpha_func,
                     actual.post_detail_alpha_func)
    self.assertEqual(expected.pad, actual.pad)
