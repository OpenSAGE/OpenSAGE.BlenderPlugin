# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3x.io_xml import *


class BoundingSphere(Struct):
    radius = 0.0
    center = Vector((0, 0, 0))

    @staticmethod
    def parse(xml_bounding_sphere):
        result = BoundingSphere(
            radius=float(xml_bounding_sphere.get('Radius')))

        result.center = parse_vector(xml_bounding_sphere.find('Center'))
        return result

    def create(self, parent):
        result = create_node(parent, 'BoundingSphere')
        result.set('Radius', str(self.radius))
        create_vector(self.center, result, 'Center')
