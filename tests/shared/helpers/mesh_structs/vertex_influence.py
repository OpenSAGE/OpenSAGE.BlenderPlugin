# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.shared.structs.mesh_structs.vertex_influence import VertexInfluence


def get_vertex_influence(bone=3, xtra=4, bone_inf=0.25, xtra_inf=0.75):
    return VertexInfluence(
        bone_idx=bone,
        xtra_idx=xtra,
        bone_inf=bone_inf,
        xtra_inf=xtra_inf)


def compare_vertex_influences(self, expected, actual):
    self.assertEqual(expected.bone_idx, actual.bone_idx)
    self.assertEqual(expected.xtra_idx, actual.xtra_idx)
    if expected.bone_inf < 0.01:
        if actual.bone_inf < 0.01:
            self.assertAlmostEqual(expected.bone_inf, actual.bone_inf, 2)
        else:
            self.assertAlmostEqual(1.0, actual.bone_inf, 2)
    else:
        self.assertAlmostEqual(expected.bone_inf, actual.bone_inf, 2)
    self.assertAlmostEqual(expected.xtra_inf, actual.xtra_inf, 2)
