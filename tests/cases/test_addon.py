import unittest
import io_mesh_w3d

class TestAddon(unittest.TestCase):
    def test_addon_enabled(self):
        self.assertIsNotNone(io_mesh_w3d.bl_info)
