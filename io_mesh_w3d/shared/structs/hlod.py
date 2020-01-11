# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3d.io_binary import *
from io_mesh_w3d.w3x.io_xml import *
from io_mesh_w3d.w3d.utils import *
from io_mesh_w3d.w3d.structs.version import Version


W3D_CHUNK_HLOD_HEADER = 0x00000701


class HLodHeader(Struct):
    version = Version()
    lod_count = 1
    model_name = ""
    hierarchy_name = ""

    @staticmethod
    def read(io_stream):
        return HLodHeader(
            version=Version.read(io_stream),
            lod_count=read_ulong(io_stream),
            model_name=read_fixed_string(io_stream),
            hierarchy_name=read_fixed_string(io_stream))

    @staticmethod
    def size(include_head=True):
        return const_size(40, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_HLOD_HEADER, io_stream,
                         self.size(False))
        self.version.write(io_stream)
        write_ulong(self.lod_count, io_stream)
        write_fixed_string(self.model_name, io_stream)
        write_fixed_string(self.hierarchy_name, io_stream)


W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER = 0x00000703

MAX_SCREEN_SIZE = 340282346638528859811704183484516925440.000000


class HLodArrayHeader(Struct):
    model_count = 0
    max_screen_size = MAX_SCREEN_SIZE

    @staticmethod
    def read(io_stream):
        return HLodArrayHeader(
            model_count=read_ulong(io_stream),
            max_screen_size=read_float(io_stream))

    @staticmethod
    def size(include_head=True):
        return const_size(8, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER, io_stream,
                         self.size(False))
        write_ulong(self.model_count, io_stream)
        write_float(self.max_screen_size, io_stream)


W3D_CHUNK_HLOD_SUB_OBJECT = 0x00000704


class HLodSubObject(Struct):
    bone_index = 0
    identifier = ""
    name = ""

    is_box = False

    @staticmethod
    def read(io_stream):
        sub_obj = HLodSubObject(
            bone_index=read_ulong(io_stream),
            identifier=read_long_fixed_string(io_stream))

        sub_obj.name = sub_obj.identifier.split('.')[-1]
        return sub_obj

    @staticmethod
    def size(include_head=True):
        return const_size(36, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_HLOD_SUB_OBJECT, io_stream,
                         self.size(False))
        write_ulong(self.bone_index, io_stream)
        write_long_fixed_string(self.identifier, io_stream)

    @staticmethod
    def parse(xml_sub_object):
        sub_object = HLodSubObject(
            name=xml_sub_object.attributes['SubObjectID'].value,
            bone_index=int(xml_sub_object.attributes['BoneIndex'].value))

        xml_render_object = xml_sub_object.getElementsByTagName(
            'RenderObject')[0]

        xml_meshes = xml_render_object.getElementsByTagName('Mesh')
        if xml_meshes:
            sub_object.identifier = xml_meshes[0].childNodes[0].nodeValue

        xml_collision_boxes = xml_render_object.getElementsByTagName('CollisionBox')
        if xml_collision_boxes:
            sub_object.identifier = xml_collision_boxes[0].childNodes[0].nodeValue
        return sub_object

    def create(self, doc):
        sub_object = doc.createElement('SubObject')
        sub_object.setAttribute('SubObjectID', self.name)
        sub_object.setAttribute('BoneIndex', str(self.bone_index))

        render_object = doc.createElement('RenderObject')
        sub_object.appendChild(render_object)
        if self.is_box:
            box = doc.createElement('CollisionBox')
            box.appendChild(doc.createTextNode(self.identifier))
            render_object.appendChild(box)
        else:
            mesh = doc.createElement('Mesh')
            mesh.appendChild(doc.createTextNode(self.identifier))
            render_object.appendChild(mesh)
        return sub_object


W3D_CHUNK_HLOD_LOD_ARRAY = 0x00000702


class HLodArray(Struct):
    header = HLodArrayHeader()
    sub_objects = []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = HLodArray(
            header=None,
            sub_objects=[])

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, _) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER:
                result.header = HLodArrayHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_HLOD_SUB_OBJECT:
                result.sub_objects.append(HLodSubObject.read(io_stream))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = const_size(0, include_head)
        size += self.header.size()
        size += list_size(self.sub_objects, False)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_HLOD_LOD_ARRAY, io_stream,
                         self.size(False), has_sub_chunks=True)
        self.header.write(io_stream)
        write_list(self.sub_objects, io_stream, HLodSubObject.write)



W3D_CHUNK_HLOD = 0x00000700


class HLod(Struct):
    header = HLodHeader()
    lod_arrays = []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = HLod(
            header=None,
            lod_arrays=[])

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_HLOD_HEADER:
                result.header = HLodHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_HLOD_LOD_ARRAY:
                result.lod_arrays.append(HLodArray.read(
                    context, io_stream, subchunk_end))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self):
        size = 0
        size += self.header.size()
        for lod_array in self.lod_arrays:
            size += lod_array.size()
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_HLOD, io_stream,
                         self.size(), has_sub_chunks=True)
        self.header.write(io_stream)
        for lod_array in self.lod_arrays:
            lod_array.write(io_stream)

    @staticmethod
    def parse(xml_container):
        result = HLod(
            header=HLodHeader(
                model_name=xml_container.attributes['id'].value,
                hierarchy_name=xml_container.attributes['Hierarchy'].value),
            lod_arrays=[HLodArray(sub_objects=[])])

        xml_sub_objects = xml_container.getElementsByTagName('SubObject')
        for xml_sub_object in xml_sub_objects:
            result.lod_arrays[0].sub_objects.append(HLodSubObject.parse(xml_sub_object))
        result.lod_arrays[0].header.model_count = len(result.lod_arrays[0].sub_objects)
        return result

    def create(self, doc):
        container = doc.createElement('Container')
        container.setAttribute('id', self.header.model_name)
        container.setAttribute('Hierarchy', self.header.hierarchy_name)

        for sub_object in self.lod_arrays[0].sub_objects:
            container.appendChild(sub_object.create(doc))
        return container
