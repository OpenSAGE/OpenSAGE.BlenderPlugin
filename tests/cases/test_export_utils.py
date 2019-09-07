# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import io
from mathutils import Vector, Quaternion
from io_mesh_w3d.export_utils_w3d import create_hierarchy, export_meshes, export_animation
from tests import utils


class TestExportUtils(utils.W3dTestCase):
    # def test_create_hierarchy(self):
    #     self.loadBlend(self.relpath() + "/elladan/elladan.blend")

    #     (hierarchy, rig) = create_hierarchy("lorem_ipsum")

    #     self.assertEqual("AUELLADAN_SKL", rig.name)

    #     expected_pivots = ["ROOTTRANSFORM", "ROOT DUMMY", "BAT_RIBS", "BAT_HEAD", "BAT_UARMR", "BAT_FARMR",
    #                        "B_HANDR", "ARROW", "BAT_UARML", "BAT_FARML", "B_HANDL", "BAT_THIGHR",
    #                        "BAT_CALFR", "B_TOER", "BAT_THIGHL", "BAT_CALFL", "B_TOEL", "SHEATHBONE",
    #                        "B_SWORDBONE", "B_BOWBONE", "B_CAPE01", "B_CAPE06", "B_CAPE07", "B_CAPE08",
    #                        "B_CAPE09", "B_CAPE10", "B_CAPE11", "B_CAPE12", "B_CAPE13"]

    #     expected_parents = [-1, 0, 1, 2, 2, 4, 5, 6, 2, 8, 9, 1, 11, 12, 1,
    #                          14, 15, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    #     expected_translations = [Vector((0.0000, 0.0000, 0.0000)),
    #                              Vector((-0.5848, 0.0915, 11.6391)),
    #                              Vector((-0.1196, 3.3882, 0.0722)),
    #                              Vector((3.6061, 0.0068, 0.2495)),
    #                              Vector((2.1429, 2.9235, 0.5041)),
    #                              Vector((3.6200, 0.0000, 0.0000)),
    #                              Vector((3.9619, 0.0001, 0.0000)),
    #                              Vector((0.9835, 0.3441, 0.1470)),
    #                              Vector((2.1882, -3.0435, 0.3085)),
    #                              Vector((3.6416, 0.0001, -0.0000)),
    #                              Vector((3.9628, -0.0001, 0.0000)),
    #                              Vector((0.0378, 0.0081, 1.1049)),
    #                              Vector((5.3092, 0.0000, 0.0000)),
    #                              Vector((5.7697, 0.0764, 0.1586)),
    #                              Vector((0.0378, 0.0081, -1.1380)),
    #                              Vector((5.3110, 0.0000, 0.0000)),
    #                              Vector((5.7186, -0.0288, 0.1480)),
    #                              Vector((1.3814, -0.4300, -2.4437)),
    #                              Vector((0.0330, -8.7253, 10.6684)),
    #                              Vector((0.0330, 8.7904, 10.6684)),
    #                              Vector((-4.4784, 3.5835, 11.5726)),
    #                              Vector((-5.6119, 0.0121, 11.2844)),
    #                              Vector((-4.4048, -3.5962, 11.4941)),
    #                              Vector((-6.7427, -4.6087, 7.5128)),
    #                              Vector((-8.4611, 0.0305, 7.6577)),
    #                              Vector((-6.7472, 4.5960, 7.6857)),
    #                              Vector((-10.1934, -5.6580, 2.9371)),
    #                              Vector((-12.3709, -0.0000, 3.3854)),
    #                              Vector((-10.1767, 5.6270, 3.0979))]

    #     expected_rotations = [Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
    #                           Quaternion((0.7071, 0.7071, 0.0000, 0.0000)),
    #                           Quaternion((0.5018, 0.4982, 0.5018, 0.4982)),
    #                           Quaternion((0.7068, -0.7067, -0.0247, -0.0195)),
    #                           Quaternion((0.3660, -0.0625, -0.0690, 0.9259)),
    #                           Quaternion((0.9911, 0.1113, -0.0722, 0.0126)),
    #                           Quaternion((1.0000, 0.0000, -0.0000, 0.0002)),
    #                           Quaternion((0.9958, 0.0485, -0.0539, 0.0561)),
    #                           Quaternion((0.3686, 0.0396, -0.0589, -0.9269)),
    #                           Quaternion((0.9917, -0.1057, -0.0724, -0.0084)),
    #                           Quaternion((0.9995, 0.0000, -0.0000, 0.0305)),
    #                           Quaternion((0.5444, -0.5018, 0.4097, -0.5328)),
    #                           Quaternion((0.9898, 0.0008, 0.1422, -0.0054)),
    #                           Quaternion((0.4797, 0.5328, -0.4824, 0.5033)),
    #                           Quaternion((0.5090, -0.5303, 0.5217, -0.4330)),
    #                           Quaternion((0.9920, 0.0006, 0.1261, -0.0048)),
    #                           Quaternion((0.5359, 0.4816, -0.4834, 0.4971)),
    #                           Quaternion((0.5067, 0.0482, 0.0284, -0.8603)),
    #                           Quaternion((0.6618, -0.2491, 0.6694, -0.2278)),
    #                           Quaternion((0.6290, 0.2972, 0.6495, 0.3069)),
    #                           Quaternion((0.5000, 0.5000, -0.5000, -0.5000)),
    #                           Quaternion((0.5000, 0.5000, -0.5000, -0.5000)),
    #                           Quaternion((0.5000, 0.5000, -0.5000, -0.5000)),
    #                           Quaternion((0.5000, 0.5000, -0.5000, -0.5000)),
    #                           Quaternion((0.5000, 0.5000, -0.5000, -0.5000)),
    #                           Quaternion((0.5000, 0.5000, -0.5000, -0.5000)),
    #                           Quaternion((0.5000, 0.5000, -0.5000, -0.5000)),
    #                           Quaternion((0.5000, 0.5000, -0.5000, -0.5000)),
    #                           Quaternion((0.5000, 0.5000, -0.5000, -0.5000))]

    #     self.assertEqual(len(expected_pivots), len(hierarchy.pivots))

    #     for i, pivot in enumerate(hierarchy.pivots):
    #         self.assertEqual(expected_pivots[i], pivot.name)
    #         self.assertEqual(expected_parents[i], pivot.parent_id)
    #         self.assertAlmostEqual(
    #             expected_translations[i].x, pivot.translation.x, 4)
    #         self.assertAlmostEqual(
    #             expected_translations[i].y, pivot.translation.y, 4)
    #         self.assertAlmostEqual(
    #             expected_translations[i].z, pivot.translation.z, 4)

    #         self.assertAlmostEqual(
    #             expected_rotations[i].x, pivot.rotation.x, 4)
    #         self.assertAlmostEqual(
    #             expected_rotations[i].y, pivot.rotation.y, 4)
    #         self.assertAlmostEqual(
    #             expected_rotations[i].z, pivot.rotation.z, 4)
    #         self.assertAlmostEqual(
    #             expected_rotations[i].w, pivot.rotation.w, 4)

    # def test_export_meshes(self):
    #     self.loadBlend(self.relpath() + "/elladan/elladan.blend")

    #     container_name = "lorem_ipsum"
    #     io_stream = io.BytesIO()
    #     (hierarchy, rig) = create_hierarchy(container_name)

    #     (hlod, mesh_structs) = export_meshes(
    #         io_stream, hierarchy, rig, container_name)

    #     meshes = ["BODY", "BROOCH", "CLOAK", "ELLADANHAIR",
    #               "HEAD", "LEGS", "SHEATH", "SWORDELLA"]

    #     vert_counts = [50, 205, 104, 182, 56, 244, 53, 414]
    #     triangle_counts = [60, 392, 139, 272, 54, 320, 66, 554]

    #     self.assertIsNotNone(hlod)
    #     self.assertEqual(len(meshes), len(mesh_structs))

    #     for i, mesh in enumerate(mesh_structs):
    #         self.assertIn(mesh.header.mesh_name, meshes)
    #         self.assertEqual(vert_counts[i], len(mesh.verts))
    #         self.assertEqual(vert_counts[i], len(mesh.normals))
    #         self.assertEqual(vert_counts[i], len(mesh.vert_infs))
    #         self.assertEqual(triangle_counts[i], len(mesh.triangles))

    # def test_export_animation(self):
    #     self.loadBlend(self.relpath() + "/elladan/elladan_animated.blend")

    #     container_name = "lorem_ipsum"
    #     io_stream = io.BytesIO()
    #     (hierarchy, _) = create_hierarchy(container_name)

    #     animation = export_animation(io_stream, container_name, hierarchy)

    #     self.assertEqual(146, animation.header.num_frames)
    #     self.assertAlmostEqual(30.0, animation.header.frame_rate, 4)
    #     self.assertEqual(71, len(animation.time_coded_channels))

