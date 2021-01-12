# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector
from io_mesh_w3d.common.io_xml import *


class BoundingSphere:
    def __init__(self, radius=0.0, center=Vector((0, 0, 0))):
        self.radius = radius
        self.center = center

    @staticmethod
    def parse(xml_bounding_sphere):
        return BoundingSphere(
            radius=parse_float(xml_bounding_sphere, 'Radius'),
            center=parse_vector(xml_bounding_sphere.find('Center')))

    def create(self, parent):
        result = create_node(parent, 'BoundingSphere')
        result.set('Radius', truncate(self.radius))
        create_vector(self.center, result, 'Center')
