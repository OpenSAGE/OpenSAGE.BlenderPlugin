# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from tests.utils import TestCase
from unittest.mock import patch

from tests.common.helpers.mesh_structs.shader_material import *
from io_mesh_w3d.common.utils.material_import import *


class TestMaterialUtils(TestCase):
    def test_shader_material_creation_unimplemented_property(self):
        shader_mat = get_shader_material()
        shader_mat.properties.append(get_shader_material_property(2, 'UnimplementedProp'))

        with (patch.object(self, 'error')) as report_func:
            create_material_from_shader_material(self, 'lorem ipsum', shader_mat)
            report_func.assert_called_with('shader property not implemented: UnimplementedProp')
