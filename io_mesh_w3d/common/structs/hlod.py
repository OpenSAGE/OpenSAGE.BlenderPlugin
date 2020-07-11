# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3d.structs.version import Version
from io_mesh_w3d.w3d.utils.helpers import *
from io_mesh_w3d.w3x.io_xml import *

W3D_CHUNK_HLOD_HEADER = 0x00000701


class HLodHeader:
    def __init__(self, version=Version(major=1, minor=0), lod_count=1, model_name='', hierarchy_name=''):
        self.version = version
        self.lod_count = lod_count
        self.model_name = model_name
        self.hierarchy_name = hierarchy_name

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
        write_chunk_head(W3D_CHUNK_HLOD_HEADER, io_stream, self.size(False))
        self.version.write(io_stream)
        write_ulong(self.lod_count, io_stream)
        write_fixed_string(self.model_name, io_stream)
        write_fixed_string(self.hierarchy_name, io_stream)


W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER = 0x00000703

MAX_SCREEN_SIZE = 340282346638528859811704183484516925440.000000


class HLodArrayHeader:
    def __init__(self, model_count=0, max_screen_size=MAX_SCREEN_SIZE):
        self.model_count = model_count
        self.max_screen_size = max_screen_size

    @staticmethod
    def read(io_stream):
        return HLodArrayHeader(
            model_count=read_ulong(io_stream),
            max_screen_size=read_float(io_stream))

    @staticmethod
    def size(include_head=True):
        return const_size(8, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER, io_stream, self.size(False))
        write_ulong(self.model_count, io_stream)
        write_float(self.max_screen_size, io_stream)


W3D_CHUNK_HLOD_SUB_OBJECT = 0x00000704


class HLodSubObject:
    def __init__(self, bone_index=0, identifier='', name='', is_box=False):
        self.bone_index = bone_index
        self.identifier = identifier
        self.name = name

        # non struct properties
        self.is_box = is_box

    @staticmethod
    def read(io_stream):
        sub_obj = HLodSubObject(
            bone_index=read_ulong(io_stream),
            identifier=read_long_fixed_string(io_stream))

        sub_obj.name = sub_obj.identifier.split('.', 1)[-1]
        return sub_obj

    @staticmethod
    def size(include_head=True):
        return const_size(36, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_HLOD_SUB_OBJECT, io_stream, self.size(False))
        write_ulong(self.bone_index, io_stream)
        write_long_fixed_string(self.identifier, io_stream)

    @staticmethod
    def parse(context, xml_sub_object):
        sub_object = HLodSubObject(
            name=xml_sub_object.get('SubObjectID'),
            bone_index=int(xml_sub_object.get('BoneIndex')))

        for child in xml_sub_object:
            if child.tag == 'RenderObject':
                for o_child in child:
                    if o_child.tag in ['Mesh', 'CollisionBox']:
                        sub_object.identifier = o_child.text
                    else:
                        context.warning('unhandled node \'' + o_child.tag + '\' in W3DContainer RenderObject!')
            else:
                context.warning('unhandled node \'' + child.tag + '\' in W3DContainer SubObject!')
        return sub_object

    def create(self, parent):
        sub_object = create_node(parent, 'SubObject')
        sub_object.set('SubObjectID', self.name)
        sub_object.set('BoneIndex', str(self.bone_index))

        render_object = create_node(sub_object, 'RenderObject')
        if self.is_box:
            box = create_node(render_object, 'CollisionBox')
            box.text = self.identifier
        else:
            mesh = create_node(render_object, 'Mesh')
            mesh.text = self.identifier


class HLodBaseArray:
    def __init__(self, header=None, sub_objects=None):
        self.header = header
        self.sub_objects = sub_objects if sub_objects is not None else []

    @staticmethod
    def read_base(context, io_stream, chunk_end, array):
        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, _) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER:
                array.header = HLodArrayHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_HLOD_SUB_OBJECT:
                array.sub_objects.append(HLodSubObject.read(io_stream))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return array

    def size(self, include_head=True):
        size = const_size(0, include_head)
        size += self.header.size()
        size += list_size(self.sub_objects, False)
        return size

    def write_base(self, io_stream, chunk_id):
        write_chunk_head(chunk_id, io_stream, self.size(False), has_sub_chunks=True)
        self.header.write(io_stream)
        write_list(self.sub_objects, io_stream, HLodSubObject.write)


W3D_CHUNK_HLOD_LOD_ARRAY = 0x00000702


class HLodLodArray(HLodBaseArray):
    @staticmethod
    def read(context, io_stream, chunk_end):
        return HLodBaseArray.read_base(context, io_stream, chunk_end, HLodLodArray())

    def write(self, io_stream):
        super().write_base(io_stream, W3D_CHUNK_HLOD_LOD_ARRAY)


W3D_CHUNK_HLOD_AGGREGATE_ARRAY = 0x00000705


class HLodAggregateArray(HLodBaseArray):
    @staticmethod
    def read(context, io_stream, chunk_end):
        return HLodBaseArray.read_base(context, io_stream, chunk_end, HLodAggregateArray())

    def write(self, io_stream):
        super().write_base(io_stream, W3D_CHUNK_HLOD_AGGREGATE_ARRAY)


W3D_CHUNK_HLOD_PROXY_ARRAY = 0x00000706


class HLodProxyArray(HLodBaseArray):
    @staticmethod
    def read(context, io_stream, chunk_end):
        return HLodBaseArray.read_base(context, io_stream, chunk_end, HLodProxyArray())

    def write(self, io_stream):
        super().write_base(io_stream, W3D_CHUNK_HLOD_PROXY_ARRAY)


W3D_CHUNK_HLOD = 0x00000700


class HLod:
    def __init__(self, header=None, lod_arrays=None, aggregate_array=None, proxy_array=None):
        self.header = header
        self.lod_arrays = lod_arrays if lod_arrays is not None else []
        self.aggregate_array = aggregate_array
        self.proxy_array = proxy_array

    def model_name(self):
        return self.header.model_name

    def hierarchy_name(self):
        return self.header.hierarchy_name

    def validate(self, context):
        if context.file_format == 'W3X':
            return True
        for lod_array in self.lod_arrays:
            for sub_obj in lod_array.sub_objects:
                if len(sub_obj.identifier) >= LARGE_STRING_LENGTH:
                    context.error(
                        'identifier \'' +
                        sub_obj.identifier +
                        '\' exceeds max length of ' +
                        str(LARGE_STRING_LENGTH))
                    return False
        return True

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = HLod()

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_HLOD_HEADER:
                result.header = HLodHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_HLOD_LOD_ARRAY:
                result.lod_arrays.append(HLodLodArray.read(context, io_stream, subchunk_end))
            elif chunk_type == W3D_CHUNK_HLOD_AGGREGATE_ARRAY:
                result.aggregate_array = HLodAggregateArray.read(context, io_stream, subchunk_end)
            elif chunk_type == W3D_CHUNK_HLOD_PROXY_ARRAY:
                result.proxy_array = HLodProxyArray.read(context, io_stream, subchunk_end)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = const_size(0, include_head)
        size += self.header.size()
        for lod_array in self.lod_arrays:
            size += lod_array.size()
        if self.aggregate_array is not None:
            size += self.aggregate_array.size()
        if self.proxy_array is not None:
            size += self.proxy_array.size()
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_HLOD, io_stream,
                         self.size(False), has_sub_chunks=True)
        self.header.write(io_stream)
        for lod_array in self.lod_arrays:
            lod_array.write(io_stream)

        if self.aggregate_array is not None:
            self.aggregate_array.write(io_stream)
        if self.proxy_array is not None:
            self.proxy_array.write(io_stream)

    @staticmethod
    def parse(context, xml_container):
        lod_array = HLodLodArray(header=HLodArrayHeader())
        result = HLod(
            header=HLodHeader(
                model_name=xml_container.get('id'),
                hierarchy_name=xml_container.get('Hierarchy')),
            lod_arrays=[lod_array])

        for child in xml_container:
            if child.tag == 'SubObject':
                lod_array.sub_objects.append(HLodSubObject.parse(context, child))
            else:
                context.warning('unhandled node \'' + child.tag + '\' in W3DContainer!')

        lod_array.header.model_count = len(lod_array.sub_objects)
        return result

    def create(self, parent):
        container = create_node(parent, 'W3DContainer')
        container.set('id', self.header.model_name)
        container.set('Hierarchy', self.header.hierarchy_name)

        for sub_object in self.lod_arrays[0].sub_objects:
            sub_object.create(container)
