# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.shared.helpers.mesh_structs.vertex_influence import *
from tests.utils import TestCase
from io_mesh_w3d.w3x.io_xml import *


class TestVertexInfluence(TestCase):
    def test_write_read(self):
        expected = get_vertex_influence()

        self.assertEqual(8, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        actual = VertexInfluence.read(io_stream)
        compare_vertex_influences(self, expected, actual)

    def test_write_read_xml(self):
        expected = get_vertex_influence()
        root = create_root()
        bone_infs = create_node(root, 'BoneInfluences')
        bone_infs2 = create_node(root, 'BoneInfluences')
        expected.create(bone_infs, bone_infs2)

        # TODO: is this sufficient or should we write to an io.BytesIO ?

        xml_objects = root.findall('BoneInfluences')
        self.assertEqual(2, len(xml_objects))

        actual = VertexInfluence.parse(xml_objects[0].find('I'), xml_objects[1].find('I'))
        compare_vertex_influences(self, expected, actual)