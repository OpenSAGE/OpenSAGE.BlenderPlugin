# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.shared.structs.rgba import RGBA
from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3d.io_binary import *
from io_mesh_w3d.w3d.structs.version import Version
from io_mesh_w3d.w3x.io_xml import *

W3D_CHUNK_BOX = 0x00000740


class CollisionBox(Struct):
    version = Version()
    box_type = 0
    collision_types = 0
    name_ = "containerName.BOUNDINGBOX"
    color = RGBA()
    center = Vector((0.0, 0.0, 0.0))
    extend = Vector((0.0, 0.0, 0.0))

    def validate(self, context):
        if len(self.name_) >= LARGE_STRING_LENGTH:
            context.error('box name ' + self.name_ + ' exceeds max length of: ' + str(LARGE_STRING_LENGTH))
            return False
        return True

    def name(self):
        return self.name_.split('.', 1)[-1]

    @staticmethod
    def read(io_stream):
        ver = Version.read(io_stream)
        flags = read_ulong(io_stream)
        return CollisionBox(
            version=ver,
            box_type=(flags & 0b11),
            collision_types=(flags & 0xFF0),
            name_=read_long_fixed_string(io_stream),
            color=RGBA.read(io_stream),
            center=read_vector(io_stream),
            extend=read_vector(io_stream))

    @staticmethod
    def size():
        return 68

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_BOX, io_stream, self.size())

        self.version.write(io_stream)
        write_ulong((self.collision_types & 0xFF)
                    | (self.box_type & 0b11), io_stream)
        write_long_fixed_string(self.name_, io_stream)
        self.color.write(io_stream)
        write_vector(self.center, io_stream)
        write_vector(self.extend, io_stream)

    @staticmethod
    def parse(xml_collision_box):
        result = CollisionBox()

        xml_center = xml_collision_box.getElementsByTagName('Center')[0]
        result.center = parse_vector(xml_center)

        xml_extend = xml_collision_box.getElementsByTagName('Extent')[0]
        result.extend = parse_vector(xml_extend)
        return result

    def create(self, doc):
        result = doc.createElement('W3DCollisionBox')
        result.appendChild(create_vector(self.center, doc, 'Center'))
        result.appendChild(create_vector(self.extend, doc, 'Extent'))
        return result
