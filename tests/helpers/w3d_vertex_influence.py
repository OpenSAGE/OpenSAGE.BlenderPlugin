# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest

from io_mesh_w3d.structs.w3d_vertex_influence import VertexInfluence

def get_vertex_influence():
    return VertexInfluence(
        bone_idx=33,
        xtra_idx=66,
        bone_inf=25.0,
        xtra_inf=75.0)

def compare_vertex_influences(self, expected, actual):
    self.assertEqual(expected.bone_idx, actual.bone_idx)
    self.assertEqual(expected.xtra_idx, actual.xtra_idx)
    self.assertEqual(expected.bone_inf, actual.bone_inf)
    self.assertEqual(expected.xtra_inf, actual.xtra_inf)
