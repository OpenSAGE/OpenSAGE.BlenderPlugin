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
        result.min = parse_vector(xml_bounding_box.find('Min'))
        result.max = parse_vector(xml_bounding_box.find('Max'))
        return result

    def create(self, parent):
        result = create_node(parent, 'BoundingBox')
        create_vector(self.min, result, 'Min')
        create_vector(self.max, result, 'Max')
