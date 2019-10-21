# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest
from io_mesh_w3d.structs.w3d_texture import Texture, TextureInfo

def get_texture_info():
    return TextureInfo(
        attributes=555,
        animation_type=33,
        frame_count=63,
        frame_rate=16.0)

def get_texture(tex_info=get_texture_info()):
    return Texture(
        name="texture",
        texture_info=tex_info)

def compare_textures(self, expected, actual):
    self.assertEqual(expected.name, actual.name)
    if expected.texture_info is not None:
        compare_texture_infos(self, expected.texture_info, actual.texture_info)

def compare_texture_infos(self, expected, actual):
    self.assertEqual(expected.attributes, actual.attributes)
    self.assertEqual(expected.animation_type, actual.animation_type)
    self.assertEqual(expected.frame_count, actual.frame_count)
    self.assertEqual(expected.frame_rate, actual.frame_rate)

