# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.io_binary import *
from io_mesh_w3d.io_xml import *


class Triangle(Struct):
    vert_ids = []
    surface_type = 13
    normal = Vector((0.0, 0.0, 0.0))
    distance = 0.0

    @staticmethod
    def read(io_stream):
        return Triangle(
            vert_ids=[read_ulong(io_stream), read_ulong(
                io_stream), read_ulong(io_stream)],
            surface_type=read_ulong(io_stream),
            normal=read_vector(io_stream),
            distance=read_float(io_stream))


    @staticmethod
    def size():
        return 32


    def write(self, io_stream):
        write_ulong(self.vert_ids[0], io_stream)
        write_ulong(self.vert_ids[1], io_stream)
        write_ulong(self.vert_ids[2], io_stream)
        write_ulong(self.surface_type, io_stream)
        write_vector(self.normal, io_stream)
        write_float(self.distance, io_stream)


    @staticmethod
    def parse(xml_triangle):
        result = Triangle(vert_ids=[])

        xml_verts = xml_triangle.getElementsByTagName('V')
        for i, xml_vert in enumerate(xml_verts):
            result.vert_ids.append(int(xml_vert.childNodes[0].nodeValue))

        result.normal = parse_vector(xml_triangle.getElementsByTagName('Nrm')[0])
        result.distance = float(xml_triangle.getElementsByTagName('Dist')[0].childNodes[0].nodeValue)
        return result


    def create(self, doc):
        result = doc.createElement('T')
        for vert_id in self.vert_ids:
            xml_vert = doc.createElement('V')
            xml_vert.appendChild(doc.createTextNode(str(vert_id)))
            result.appendChild(xml_vert)

        result.appendChild(create_vector(self.normal, doc, 'Nrm'))
        xml_distance = doc.createElement('Dist')
        xml_distance.appendChild(doc.createTextNode(str(self.distance)))
        result.appendChild(xml_distance)
        return result
