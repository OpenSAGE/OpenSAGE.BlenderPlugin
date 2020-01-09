# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from xml.dom import minidom
from tests.utils import TestCase
from tests.shared.helpers.mesh_structs.vertex_influence import *


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

        doc = minidom.Document()
        mesh = doc.createElement('W3DMesh')
        doc.appendChild(mesh)

        bone_infs = doc.createElement('BoneInfluences')
        mesh.appendChild(bone_infs)
        bone_infs2 = doc.createElement('BoneInfluences')
        mesh.appendChild(bone_infs2)

        (bone_inf, bone_inf2) = expected.create(doc, multibone=True)
        bone_infs.appendChild(bone_inf)
        bone_infs2.appendChild(bone_inf2)

        io_stream = io.BytesIO()
        io_stream.write(bytes(doc.toprettyxml(indent='   '), 'UTF-8'))
        io_stream = io.BytesIO(io_stream.getvalue())

        dom = minidom.parse(io_stream)
        xml_meshes = dom.getElementsByTagName('W3DMesh')
        self.assertEqual(1, len(xml_meshes))
        xml_bone_influences_lists = xml_meshes[0].getElementsByTagName('BoneInfluences')
        self.assertEqual(2, len(xml_bone_influences_lists))

        xml_bone_influences = xml_bone_influences_lists[0].getElementsByTagName('I')
        self.assertEqual(1, len(xml_bone_influences))

        xml_bone2_influences = xml_bone_influences_lists[1].getElementsByTagName('I')
        self.assertEqual(1, len(xml_bone2_influences))

        actual = VertexInfluence.parse(xml_bone_influences[0], xml_bone2_influences[0])
        compare_vertex_influences(self, expected, actual)
