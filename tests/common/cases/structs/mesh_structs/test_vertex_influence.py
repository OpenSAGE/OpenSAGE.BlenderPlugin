# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
import struct
from tests.common.helpers.mesh_structs.vertex_influence import *
from tests.utils import TestCase
from io_mesh_w3d.w3x.io_xml import *


def _as_float32(value):
    """The nearest float32 value, matching how Blender stores vertex group
    weights - this is what actually reaches VertexInfluence.write() in practice.
    """
    return struct.unpack('<f', struct.pack('<f', value))[0]


class TestVertexInfluence(TestCase):
    def test_write_read(self):
        expected = get_vertex_influence()

        self.assertEqual(8, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        actual = VertexInfluence.read(io_stream)
        compare_vertex_influences(self, expected, actual)

    def test_write_always_sums_the_two_weights_to_exactly_100_percent(self):
        """Regression test for a roundtrip bug: Blender stores vertex group
        weights as float32, so an intended 42% is actually stored as
        0.41999998. Truncating that (the old int() behaviour) drops a whole
        percentage point, and doing that independently on both sides could
        leave the pair not summing to 100% at all - which the game's skinning
        shader (weight0*pos0 + weight1*pos1) then reads as an under-scaled,
        visibly offset vertex for exactly the vertices bound to two bones.
        """
        # exact percentages whose nearest float32 representation sits just
        # under the intended value - int() truncates these down by one
        for bone_pct, xtra_pct in ((42, 58), (16, 84), (22, 78), (1, 99), (99, 1)):
            with self.subTest(bone_pct=bone_pct, xtra_pct=xtra_pct):
                influence = get_vertex_influence(
                    bone_inf=_as_float32(bone_pct / 100), xtra_inf=_as_float32(xtra_pct / 100))

                io_stream = io.BytesIO()
                influence.write(io_stream)
                io_stream = io.BytesIO(io_stream.getvalue())
                actual = VertexInfluence.read(io_stream)

                self.assertAlmostEqual(1.0, actual.bone_inf + actual.xtra_inf, places=5)
                self.assertAlmostEqual(bone_pct / 100, actual.bone_inf, places=2)

    def test_write_does_not_drop_a_small_secondary_weight_to_zero(self):
        """The concrete case that surfaced this bug: a vertex weighted 99%/1%
        to two bones lost its entire 1% secondary influence after a roundtrip,
        silently turning a two-bone vertex into a rigidly single-bone one.
        """
        influence = get_vertex_influence(bone_inf=_as_float32(0.99), xtra_inf=_as_float32(0.01))

        io_stream = io.BytesIO()
        influence.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())
        actual = VertexInfluence.read(io_stream)

        self.assertGreater(actual.xtra_inf, 0.0)

    def test_write_of_an_unset_influence_does_not_invent_a_second_bone(self):
        """Both weights genuinely zero (an unset placeholder influence, as used
        for unweighted vertices) is not the same as 'no second bone but 100% on
        the first' - bone_inf is not guaranteed to be 1.0 here, so xtra_inf must
        not be derived as its complement.
        """
        influence = get_vertex_influence(bone_inf=0.0, xtra_inf=0.0)

        io_stream = io.BytesIO()
        influence.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())
        actual = VertexInfluence.read(io_stream)

        self.assertEqual(0.0, actual.bone_inf)
        self.assertEqual(0.0, actual.xtra_inf)

    def test_write_read_xml(self):
        expected = get_vertex_influence()
        root = create_root()
        bone_infs = create_node(root, 'BoneInfluences')
        bone_infs2 = create_node(root, 'BoneInfluences')
        expected.create(bone_infs, bone_infs2)

        xml_objects = root.findall('BoneInfluences')
        self.assertEqual(2, len(xml_objects))

        actual = VertexInfluence.parse(xml_objects[0].find('I'), xml_objects[1].find('I'))
        compare_vertex_influences(self, expected, actual)

    def test_write_read_xml_only_one_bone(self):
        expected = get_vertex_influence(bone=3, xtra=0, bone_inf=1.0, xtra_inf=0.0)
        root = create_root()
        bone_infs = create_node(root, 'BoneInfluences')
        expected.create(bone_infs)

        xml_objects = root.findall('BoneInfluences')
        self.assertEqual(1, len(xml_objects))

        actual = VertexInfluence.parse(xml_objects[0].find('I'))
        compare_vertex_influences(self, expected, actual)
