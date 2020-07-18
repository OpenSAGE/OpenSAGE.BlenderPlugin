# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector
from io_mesh_w3d.common.io_xml import *


class BoundingBox:
    def __init__(self, min=Vector((0, 0, 0)), max=Vector((0, 0, 0))):
        self.min = min
        self.max = max

    @staticmethod
    def parse(xml_bounding_box):
        return BoundingBox(
            min=parse_vector(xml_bounding_box.find('Min')),
            max=parse_vector(xml_bounding_box.find('Max')))

    def create(self, parent):
        result = create_node(parent, 'BoundingBox')
        create_vector(self.min, result, 'Min')
        create_vector(self.max, result, 'Max')
