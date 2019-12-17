# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.io_xml import *


class Texture(Struct):
    id=""
    File=""

    @staticmethod
    def parse(xml_texture):
        return Texture(
            id=xml_texture.attributes['id'].value,
            File=xml_texture.attributes['File'].value)


    def create(self, doc):
        texture = doc.createElement('Texture')
        texture.setAttribute('id', self.id)
        texture.setAttribute('File', self.File)
        return texture
