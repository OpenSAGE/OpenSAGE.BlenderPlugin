# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from tests.utils import TestCase
from shutil import copyfile
from os.path import dirname as up

from io_mesh_w3d.common.utils.material_import import *
from io_mesh_w3d.common.utils.material_export import *

from tests.w3d.helpers.mesh_structs.vertex_material import *
from tests.w3d.helpers.mesh_structs.shader import *
from tests.common.helpers.mesh_structs.shader_material import *


class TestMaterialUtils(TestCase):
    def test_vertex_material_roundtrip(self):
        expected = get_vertex_material()

        copyfile(up(up(up(self.relpath()))) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        (material, _) = create_material_from_vertex_material(
            self, 'meshName', expected)
        actual = retrieve_vertex_material(material)
        compare_vertex_materials(self, expected, actual)

    def test_vertex_material_no_attributes_roundtrip(self):
        expected = get_vertex_material()

        copyfile(up(up(up(self.relpath()))) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        expected.vm_info.attributes = 0
        (material, _) = create_material_from_vertex_material(
            self, 'meshName', expected)
        actual = retrieve_vertex_material(material)
        compare_vertex_materials(self, expected, actual)

    def test_shader_material_roundtrip(self):
        expected = get_shader_material()

        copyfile(up(up(up(self.relpath()))) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        (material, _) = create_material_from_shader_material(
            self, 'meshName', expected)
        principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
        actual = retrieve_shader_material(material, principled)
        compare_shader_materials(self, expected, actual)

    def test_duplicate_shader_material_roundtrip(self):
        expecteds = [get_shader_material(), get_shader_material()]

        materials = []
        for mat in expecteds:
            (material, _) = create_material_from_shader_material(self, 'meshName', mat)
            materials.append(material)

        self.assertEqual(1, len(bpy.data.materials))
        self.assertTrue('meshName.ShaderMaterial.fx' in bpy.data.materials)

        for expected in expecteds:
            principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
            actual = retrieve_shader_material(material, principled)
            compare_shader_materials(self, expected, actual)

    def test_shader_material_w3x_roundtrip(self):
        expected = get_shader_material(w3x=True)
        copyfile(up(up(up(self.relpath()))) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        (material, _) = create_material_from_shader_material(
            self, 'meshName', expected)
        principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
        actual = retrieve_shader_material(material, principled, w3x=True)
        compare_shader_materials(self, expected, actual)

    def test_shader_material_w3x_rgb_colors_roundtrip(self):
        expected = get_shader_material(w3x=True, rgb_colors=True)
        copyfile(up(up(up(self.relpath()))) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        (material, _) = create_material_from_shader_material(
            self, 'meshName', expected)
        principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
        actual = retrieve_shader_material(material, principled, w3x=True)

        for prop in expected.properties:
            if prop.name in ['ColorAmbient', 'ColorEmissive']:
                prop.type = 5
                prop.value = RGBA(vec=prop.value, a=255)
            elif prop.name in ['ColorDiffuse', 'ColorSpecular']:
                prop.type = 5
                prop.value = RGBA(vec=prop.value, a=0)

        compare_shader_materials(self, expected, actual)

    def test_shader_material_w3x_two_tex_roundtrip(self):
        expected = get_shader_material(w3x=True, two_tex=True)
        copyfile(up(up(up(self.relpath()))) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        (material, _) = create_material_from_shader_material(
            self, 'meshName', expected)
        principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
        actual = retrieve_shader_material(material, principled, w3x=True)
        compare_shader_materials(self, expected, actual)

    def test_default_shader_material_properties_are_not_exported(self):
        expected = get_shader_material()
        expected.properties = []

        (material, principled) = create_material_from_shader_material(self, 'meshName', expected)

        actual = retrieve_shader_material(material, principled, w3x=False)
        self.assertEqual(0, len(actual.properties))

        actual = retrieve_shader_material(material, principled, w3x=True)
        self.assertEqual(0, len(actual.properties))

    def test_shader_material_minimal_roundtrip(self):
        expected = get_shader_material()
        expected.properties = []

        copyfile(up(up(up(self.relpath()))) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        (material, principled) = create_material_from_shader_material(
            self, 'meshName', expected)
        actual = retrieve_shader_material(material, principled)
        compare_shader_materials(self, expected, actual)

    def test_shader_roundtrip(self):
        mat = get_vertex_material()

        copyfile(up(up(up(self.relpath()))) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        (material, _) = create_material_from_vertex_material(
            self, 'meshName', mat)
        expected = get_shader()
        set_shader_properties(material, expected)
        actual = retrieve_shader(material)
        compare_shaders(self, expected, actual)