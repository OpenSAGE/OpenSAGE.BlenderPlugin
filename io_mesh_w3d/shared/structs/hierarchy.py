# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector, Quaternion, Matrix

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3d.structs.version import Version
from io_mesh_w3d.w3d.utils import *
from io_mesh_w3d.w3d.io_binary import *
from io_mesh_w3d.w3x.io_xml import *


W3D_CHUNK_HIERARCHY_HEADER = 0x00000101


class HierarchyHeader(Struct):
    version = Version()
    name = ""
    num_pivots = 0
    center_pos = Vector((0.0, 0.0, 0.0))

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
        write_chunk_head(W3D_CHUNK_HIERARCHY_HEADER, io_stream,
                         self.size(False))
        self.version.write(io_stream)
        write_fixed_string(self.name, io_stream)
        write_ulong(self.num_pivots, io_stream)
        write_vector(self.center_pos, io_stream)


class HierarchyPivot(Struct):
    name = ""
    name_id = None
    parent_id = -1
    translation = Vector()
    euler_angles = Vector()
    rotation = Quaternion()
    fixup_matrix = Matrix()

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
    def parse(xml_pivot):
        pivot = HierarchyPivot(
            name=xml_pivot.attributes['Name'].value,
            parent_id=int(xml_pivot.attributes['Parent'].value))

        #if 'Name' in xml_pivot.attributes:
        #    pivot.name = xml_pivot.attributes['Name'].value
        if 'NameID' in xml_pivot.attributes:
            pivot.name_id = int(xml_pivot.attributes['NameID'].value)

        xml_translation = xml_pivot.getElementsByTagName('Translation')[0]
        pivot.translation = parse_vector(xml_translation)
        xml_rotation = xml_pivot.getElementsByTagName('Rotation')[0]
        pivot.rotation = parse_quaternion(xml_rotation)
        xml_fixup_matrix = xml_pivot.getElementsByTagName('FixupMatrix')[0]
        pivot.fixup_matrix = parse_matrix(xml_fixup_matrix)
        return pivot

    def create(self, doc):
        pivot = doc.createElement('Pivot')
        if self.name is not None:
            pivot.setAttribute('Name', self.name)
        if self.name_id is not None:
            pivot.setAttribute('NameID', str(self.name_id))
        pivot.setAttribute('Parent', str(self.parent_id))
        pivot.appendChild(create_vector(self.translation, doc, 'Translation'))
        pivot.appendChild(create_quaternion(self.rotation, doc))
        pivot.appendChild(create_matrix(self.fixup_matrix, doc))
        return pivot


W3D_CHUNK_HIERARCHY = 0x00000100
W3D_CHUNK_PIVOTS = 0x00000102
W3D_CHUNK_PIVOT_FIXUPS = 0x00000103


class Hierarchy(Struct):
    header = None
    id = None
    pivots = []
    pivot_fixups = []

    def set_name(self, name):
        self.header.name = name
        self.id = name

    def name(self):
        if self.header is not None:
            return self.header.name
        return self.id

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = Hierarchy(
            pivots=[],
            pivot_fixups=[])

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_HIERARCHY_HEADER:
                result.header = HierarchyHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_PIVOTS:
                result.pivots = read_list(
                    io_stream, subchunk_end, HierarchyPivot.read)
            elif chunk_type == W3D_CHUNK_PIVOT_FIXUPS:
                result.pivot_fixups = read_list(
                    io_stream, subchunk_end, read_vector)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self):
        size = self.header.size()
        size += list_size(self.pivots)
        size += vec_list_size(self.pivot_fixups)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_HIERARCHY, io_stream, self.size())
        self.header.write(io_stream)

        write_chunk_head(W3D_CHUNK_PIVOTS, io_stream,
                         list_size(self.pivots, False))
        write_list(self.pivots, io_stream, HierarchyPivot.write)

        if self.pivot_fixups:
            write_chunk_head(W3D_CHUNK_PIVOT_FIXUPS, io_stream,
                             vec_list_size(self.pivot_fixups, False))
            write_list(self.pivot_fixups, io_stream, write_vector)

    @staticmethod
    def parse(xml_hierarchy):
        result = Hierarchy(
            id=xml_hierarchy.attributes['id'].value,
            pivots=[])
        xml_pivots = xml_hierarchy.getElementsByTagName('Pivot')
        for xml_pivot in xml_pivots:
            result.pivots.append(HierarchyPivot.parse(xml_pivot))
        return result

    def create(self, doc):
        hierarchy = doc.createElement('W3DHierarchy')
        hierarchy.setAttribute('id', self.id)

        for pivot in self.pivots:
            hierarchy.appendChild(pivot.create(doc))
        return hierarchy
