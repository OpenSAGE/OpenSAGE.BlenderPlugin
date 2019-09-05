# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import io
from io_mesh_w3d.export_utils_w3d import create_hierarchy, export_meshes
from tests import utils


class TestExportUtils(utils.W3dTestCase):
    def test_create_hierarchy(self):
        self.loadBlend(self.relpath() + "/elladan/elladan.blend")

        (hierarchy, rig) = create_hierarchy("lorem_ipsum")

        self.assertEqual("AUELLADAN_SKL", rig.name)

        expected_pivots = ["ROOTTRANSFORM", "ROOT DUMMY", "BAT_RIBS", "BAT_HEAD", "BAT_UARMR", "BAT_FARMR",
                           "B_HANDR", "ARROW", "BAT_UARML", "BAT_FARML", "B_HANDL", "BAT_THIGHR",
                           "BAT_CALFR", "B_TOER", "BAT_THIGHL", "BAT_CALFL", "B_TOEL", "SHEATHBONE",
                           "B_SWORDBONE", "B_BOWBONE", "B_CAPE01", "B_CAPE06", "B_CAPE07", "B_CAPE08",
                           "B_CAPE09", "B_CAPE10", "B_CAPE11", "B_CAPE12", "B_CAPE13"]

        self.assertEqual(len(expected_pivots), len(hierarchy.pivots))

        for pivot in hierarchy.pivots:
            self.assertIn(pivot.name, expected_pivots)

    def test_export_meshes(self):
        self.loadBlend(self.relpath() + "/elladan/elladan.blend")

        container_name = "lorem_ipsum"
        io_stream = io.BytesIO()
        (hierarchy, rig) = create_hierarchy(container_name)

        (hlod, mesh_structs) = export_meshes(io_stream, hierarchy, rig, container_name)

        self.assertIsNotNone(hlod)
        self.assertEqual(8, len(mesh_structs))
