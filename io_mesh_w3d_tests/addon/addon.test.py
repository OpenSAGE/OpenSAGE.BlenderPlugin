import unittest
import io_mesh_w3d
from io_mesh_w3d_tests.test_utils import *

class TestAddon(unittest.TestCase):
    def test_addon_enabled(self):
        self.assertIsNotNone(io_mesh_w3d.bl_info)

runTestCases([TestAddon])


