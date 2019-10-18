# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import io
from tests import utils

from io_mesh_w3d.import_utils_w3d import create_material
from io_mesh_w3d.export_utils_w3d import create_vertex_material
from tests.helpers.w3d_mesh import get_mesh
from tests.helpers.w3d_material import compare_vertex_materials

class TestUtils(utils.W3dTestCase):
    def test_vertex_material_roundtrip(self):
        mesh = get_mesh()

        for source in mesh.vert_materials:
            material = create_material(mesh, source)
            actual = create_vertex_material(material)
            compare_vertex_materials(self, source, actual)

