# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import io
from tests import utils

from io_mesh_w3d.import_utils_w3d import create_material_from_vertex_material, \
    create_material_from_shader_material
from io_mesh_w3d.export_utils_w3d import create_vertex_material, create_shader_material
from tests.helpers.w3d_mesh import get_mesh
from tests.helpers.w3d_material import compare_vertex_materials
from tests.helpers.w3d_shader_material import compare_shader_materials

class TestUtils(utils.W3dTestCase):
    def test_vertex_material_roundtrip(self):
        mesh = get_mesh()

        for source in mesh.vert_materials:
            material = create_material_from_vertex_material(self, mesh, source)
            actual = create_vertex_material(material)
            compare_vertex_materials(self, source, actual)

    def test_shader_material_roundtrip(self):
        mesh = get_mesh()

        for source in mesh.shader_materials:
            material = create_material_from_shader_material(self, mesh, source)
            actual = create_shader_material(material)
            #compare_shader_materials(self, source, actual)

