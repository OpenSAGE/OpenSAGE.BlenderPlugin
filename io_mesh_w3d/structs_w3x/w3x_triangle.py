# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector

from io_mesh_w3d.structs_w3x.w3x_struct import Struct
from io_mesh_w3d.io_xml import *

class Triangle(Struct):
    vert_ids = []
    normal = Vector((0, 0, 0))
    distance = 0.0

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