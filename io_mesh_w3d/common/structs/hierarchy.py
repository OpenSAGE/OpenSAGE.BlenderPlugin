# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector, Quaternion, Matrix
from io_mesh_w3d.w3d.structs.version import Version
from io_mesh_w3d.w3d.utils.helpers import *
from io_mesh_w3d.w3x.io_xml import *

W3D_CHUNK_HIERARCHY_HEADER = 0x00000101


class HierarchyHeader:
    def __init__(self, version=Version(major=4, minor=1), name='', num_pivots=0, center_pos=Vector((0.0, 0.0, 0.0))):
        self.version = version
        self.name = name
        self.num_pivots = num_pivots
        self.center_pos = center_pos

    @staticmethod
    def read(io_stream):
        return HierarchyHeader(
            version=Version.read(io_stream),
            name=read_fixed_string(io_stream),
            num_pivots=read_ulong(io_stream),
            center_pos=read_vector(io_stream))

    @staticmethod
    def size(include_head=True):
        return const_size(36, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_HIERARCHY_HEADER, io_stream, self.size(False))
        self.version.write(io_stream)
        write_fixed_string(self.name, io_stream)
        write_ulong(self.num_pivots, io_stream)
        write_vector(self.center_pos, io_stream)


class HierarchyPivot:
    def __init__(self, name='', name_id=None, parent_id=-1, translation=Vector(), euler_angles=Vector(),
                 rotation=Quaternion(), fixup_matrix=Matrix()):
        self.name = name
        self.name_id = name_id
        self.parent_id = parent_id
        self.translation = translation
        self.euler_angles = euler_angles
        self.rotation = rotation
        self.fixup_matrix = fixup_matrix

    @staticmethod
    def read(io_stream):
        return HierarchyPivot(
            name=read_fixed_string(io_stream),
            parent_id=read_long(io_stream),
            translation=read_vector(io_stream),
            euler_angles=read_vector(io_stream),
            rotation=read_quaternion(io_stream))

    @staticmethod
    def size():
        return 60

    def write(self, io_stream):
        write_fixed_string(self.name, io_stream)
        write_long(self.parent_id, io_stream)
        write_vector(self.translation, io_stream)
        write_vector(self.euler_angles, io_stream)
        write_quaternion(self.rotation, io_stream)

    @staticmethod
    def parse(context, xml_pivot):
        pivot = HierarchyPivot(
            name=xml_pivot.get('Name'),
            parent_id=int(xml_pivot.get('Parent')),
            name_id=int(xml_pivot.get('NameID', 0)))

        for child in xml_pivot:
            if child.tag == 'Translation':
                pivot.translation = parse_vector(child)
            elif child.tag == 'Rotation':
                pivot.rotation = parse_quaternion(child)
            elif child.tag == 'FixupMatrix':
                pivot.fixup_matrix = parse_matrix(child)
            else:
                context.warning('unhandled node \'' + child.tag + '\' in Pivot!')
        return pivot

    def create(self, parent):
        pivot = create_node(parent, 'Pivot')
        if self.name is not None:
            pivot.set('Name', self.name)
        if self.name_id is not None:
            pivot.set('NameID', str(self.name_id))
        pivot.set('Parent', str(self.parent_id))
        create_vector(self.translation, pivot, 'Translation')
        create_quaternion(self.rotation, pivot)
        create_matrix(self.fixup_matrix, pivot)


W3D_CHUNK_HIERARCHY = 0x00000100
W3D_CHUNK_PIVOTS = 0x00000102
W3D_CHUNK_PIVOT_FIXUPS = 0x00000103


class Hierarchy:
    def __init__(self, header=None, pivots=None, pivot_fixups=None):
        self.header = header
        self.pivots = pivots if pivots is not None else []
        self.pivot_fixups = pivot_fixups if pivot_fixups is not None else []

    def name(self):
        return self.header.name

    def validate(self, context):
        if context.file_format == 'W3X':
            return True
        if len(self.header.name) >= STRING_LENGTH:
            context.error('armature name \'' + self.header.name + '\' exceeds max length of ' + str(STRING_LENGTH))
            return False
        for pivot in self.pivots:
            if len(pivot.name) >= STRING_LENGTH:
                context.error('name of object \'' + pivot.name + '\' exceeds max length of ' + str(STRING_LENGTH))
                return False
        return True

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = Hierarchy()

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_HIERARCHY_HEADER:
                result.header = HierarchyHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_PIVOTS:
                result.pivots = read_list(io_stream, subchunk_end, HierarchyPivot.read)
            elif chunk_type == W3D_CHUNK_PIVOT_FIXUPS:
                result.pivot_fixups = read_list(io_stream, subchunk_end, read_vector)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = const_size(0, include_head)
        size += self.header.size()
        size += list_size(self.pivots)
        size += vec_list_size(self.pivot_fixups)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_HIERARCHY, io_stream, self.size(False))
        self.header.write(io_stream)

        if self.pivots:
            write_chunk_head(W3D_CHUNK_PIVOTS, io_stream, list_size(self.pivots, False))
            write_list(self.pivots, io_stream, HierarchyPivot.write)

        if self.pivot_fixups:
            write_chunk_head(W3D_CHUNK_PIVOT_FIXUPS, io_stream, vec_list_size(self.pivot_fixups, False))
            write_list(self.pivot_fixups, io_stream, write_vector)

    @staticmethod
    def parse(context, xml_hierarchy):
        result = Hierarchy(
            header=HierarchyHeader(
                name=xml_hierarchy.get('id')))

        for child in xml_hierarchy:
            if child.tag == 'Pivot':
                result.pivots.append(HierarchyPivot.parse(context, child))
            else:
                context.warning('unhandled node \'' + child.tag + '\' in W3DHierarchy!')
        return result

    def create(self, parent):
        hierarchy = create_node(parent, 'W3DHierarchy')
        hierarchy.set('id', self.header.name)

        for pivot in self.pivots:
            pivot.create(hierarchy)
