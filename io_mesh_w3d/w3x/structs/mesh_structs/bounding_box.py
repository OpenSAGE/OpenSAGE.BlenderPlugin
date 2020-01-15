# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3x.io_xml import *


class BoundingBox(Struct):
    min = Vector((0, 0, 0))
    max = Vector((0, 0, 0))

    @staticmethod
    def parse(xml_bounding_box):
        result = BoundingBox()

        xml_min = xml_bounding_box.getElementsByTagName('Min')[0]
        result.min = parse_vector(xml_min)

        xml_max = xml_bounding_box.getElementsByTagName('Max')[0]
        result.max = parse_vector(xml_max)
        return result

    def create(self, doc):
        result = doc.createElement('BoundingBox')
        result.appendChild(create_vector(self.min, doc, 'Min'))
        result.appendChild(create_vector(self.max, doc, 'Max'))
        return result
