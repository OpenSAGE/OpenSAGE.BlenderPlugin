# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector
from io_mesh_w3d.common.structs.rgba import RGBA
from io_mesh_w3d.w3d.utils.helpers import *
from io_mesh_w3d.w3d.structs.version import Version
from io_mesh_w3d.w3x.io_xml import *

W3D_CHUNK_BOX = 0x00000740
ATTRIBUTE_MASK = 0xF
COLLISION_TYPE_MASK = 0xFF0

COLLISION_TYPE_PHYSICAL = 0x10
COLLISION_TYPE_PROJECTILE = 0x20
COLLISION_TYPE_VIS = 0x40
COLLISION_TYPE_CAMERA = 0x80
COLLISION_TYPE_VEHICLE = 0x100


class CollisionBox:
    def __init__(self, version=Version(), box_type=0, collision_types=0, name_='', color=RGBA(),
                 center=Vector((0.0, 0.0, 0.0)), extend=Vector((0.0, 0.0, 0.0)), joypad_picking_only=False):
        self.version = version
        self.box_type = box_type
        self.collision_types = collision_types
        self.name_ = name_
        self.color = color
        self.center = center
        self.extend = extend
        self.joypad_picking_only = joypad_picking_only

    def validate(self, context):
        if context.file_format == 'W3X':
            return True
        if len(self.name_) >= LARGE_STRING_LENGTH:
            context.error(f'box name \'{self.name_}\' exceeds max length of: {LARGE_STRING_LENGTH}')
            return False
        return True

    def container_name(self):
        return self.name_.split('.', 1)[0]

    def name(self):
        return self.name_.split('.', 1)[-1]
    
    # unique name. e.g. SUANTIAIRSHIP_SKN.OBBOX01
    def identifier(self):
        return self.name_

    @staticmethod
    def read(io_stream):
        ver = Version.read(io_stream)
        flags = read_ulong(io_stream)
        return CollisionBox(
            version=ver,
            box_type=(flags & ATTRIBUTE_MASK),
            collision_types=(flags & COLLISION_TYPE_MASK),
            name_=read_long_fixed_string(io_stream),
            color=RGBA.read(io_stream),
            center=read_vector(io_stream),
            extend=read_vector(io_stream))

    @staticmethod
    def size(include_head=True):
        return const_size(68, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_BOX, io_stream, self.size(False))

        self.version.write(io_stream)
        write_ulong((self.box_type & ATTRIBUTE_MASK) | (self.collision_types & COLLISION_TYPE_MASK), io_stream)
        write_long_fixed_string(self.name_, io_stream)
        self.color.write(io_stream)
        write_vector(self.center, io_stream)
        write_vector(self.extend, io_stream)

    @staticmethod
    def parse(context, xml_collision_box):
        result = CollisionBox(
            name_=xml_collision_box.get('id'),
            joypad_picking_only=bool(xml_collision_box.get('JoypadPickingOnly', False)))

        for child in xml_collision_box:
            if child.tag == 'Center':
                result.center = parse_vector(child)
            elif child.tag == 'Extent':
                result.extend = parse_vector(child)
            else:
                context.warning(f'unhandled node \'{child.tag}\' in W3DCollisionBox!')
        return result

    def create(self, parent):
        result = create_node(parent, 'W3DCollisionBox')
        result.set('id', self.name_)
        create_vector(self.center, result, 'Center')
        create_vector(self.extend, result, 'Extent')
