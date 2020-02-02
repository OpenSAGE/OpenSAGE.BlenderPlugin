# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3d.io_binary import *
from io_mesh_w3d.w3x.io_xml import *


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

        for i, xml_vert in enumerate(xml_triangle.findall('V')):
            result.vert_ids.append(int(xml_vert.text))

        result.normal = parse_vector(xml_triangle.find('Nrm'))
        result.distance = float(xml_triangle.find('Dist').text)
        return result

    def create(self, parent):
        triangle = create_node(parent, 'T')
        for vert_id in self.vert_ids:
            xml_vert = create_node(triangle, 'V')
            xml_vert.text = str(vert_id)

        create_vector(self.normal, triangle, 'Nrm')
        xml_distance = create_node(triangle, 'Dist')
        xml_distance.text = str(self.distance)
