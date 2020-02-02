# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3x.io_xml import *


class Include(Struct):
    type = ''
    source = ''

    @staticmethod
    def parse(xml_include):
        return Include(
            type=xml_include.get('type'),
            source=xml_include.get('source'))

    def create(self, parent):
        include = create_node(parent, 'Include')
        include.set('type', self.type)
        include.set('source', self.source)
