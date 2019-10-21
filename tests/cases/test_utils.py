# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import io
from tests import utils
from shutil import copyfile

from io_mesh_w3d.import_utils_w3d import create_material_from_vertex_material, \
    create_material_from_shader_material, set_shader_properties
from io_mesh_w3d.export_utils_w3d import create_vertex_material, create_shader_material, \
    get_principled_bsdf, create_shader
from tests.helpers.w3d_mesh import get_mesh
from tests.helpers.w3d_material import compare_vertex_materials
from tests.helpers.w3d_shader_material import compare_shader_materials
from tests.helpers.w3d_shader import get_shader, compare_shaders

class TestUtils(utils.W3dTestCase):
    def test_vertex_material_roundtrip(self):
        mesh = get_mesh()
        context = utils.ImportWrapper(self.outpath())

        copyfile(self.relpath() + "/testfiles/texture.dds", self.outpath() + "texture.dds")

        for source in mesh.vert_materials:
            material = create_material_from_vertex_material(context, mesh, source)
            actual = create_vertex_material(material)
            compare_vertex_materials(self, source, actual)


    def test_shader_material_roundtrip(self):
        mesh = get_mesh()
        context = utils.ImportWrapper(self.outpath())

        copyfile(self.relpath() + "/testfiles/texture.dds", self.outpath() + "texture.dds")

        for source in mesh.shader_materials:
            material = create_material_from_shader_material(context, mesh, source)
            principled = get_principled_bsdf(material)
            actual = create_shader_material(material, principled)
            compare_shader_materials(self, source, actual)


    def test_shader_roundtrip(self):
        mesh = get_mesh()
        context = utils.ImportWrapper(self.outpath())

        material = create_material_from_vertex_material(context, mesh, mesh.vert_materials[0])
        expected = mesh.shaders[0]
        set_shader_properties(material, expected)
        actual = create_shader(material)
        compare_shaders(self, expected, actual)


