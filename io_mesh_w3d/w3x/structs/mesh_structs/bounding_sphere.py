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
            radius=float(xml_bounding_sphere.attributes['Radius'].value))

        xml_center = xml_bounding_sphere.getElementsByTagName('Center')[0]
        result.center = parse_vector(xml_center)
        return result

    def create(self, doc):
        result = doc.createElement('BoundingSphere')
        result.setAttribute('Radius', str(self.radius))
        result.appendChild(create_vector(self.center, doc, 'Center'))
        return result
