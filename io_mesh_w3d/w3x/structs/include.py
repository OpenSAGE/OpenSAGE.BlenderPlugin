# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3x.io_xml import *


class Include(Struct):
    type = ""
    source = ""

    @staticmethod
    def parse(xml_include):
        return Include(
            type=xml_include.attributes['type'].value,
            source=xml_include.attributes['source'].value)

    def create(self, doc):
        include = doc.createElement('Include')
        include.setAttribute('type', self.type)
        include.setAttribute('source', self.source)
        return include
