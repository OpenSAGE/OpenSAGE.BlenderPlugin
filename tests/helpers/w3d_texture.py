# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import unittest
from io_mesh_w3d.structs.w3d_texture import Texture, TextureInfo


def get_texture_info():
    return TextureInfo(
        attributes=0,
        animation_type=0,
        frame_count=0,
        frame_rate=0.0)


def get_texture(name="texture.dds"):
    return Texture(
        name=name,
        texture_info=get_texture_info())


def get_texture_minimal():
    return Texture(
        name="a",
        texture_info=get_texture_info())


def get_texture_empty():
    return Texture(
        name="a",
        texture_info=None)


def compare_textures(self, expected, actual):
    self.assertEqual(expected.name, actual.name)
    if expected.texture_info is not None:
        compare_texture_infos(self, expected.texture_info, actual.texture_info)


def compare_texture_infos(self, expected, actual):
    self.assertEqual(expected.attributes, actual.attributes)
    self.assertEqual(expected.animation_type, actual.animation_type)
    self.assertEqual(expected.frame_count, actual.frame_count)
    self.assertEqual(expected.frame_rate, actual.frame_rate)
