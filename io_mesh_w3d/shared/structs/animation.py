# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3x.io_xml import *
from io_mesh_w3d.w3d.io_binary import *
from io_mesh_w3d.w3d.utils import *
from io_mesh_w3d.w3d.structs.version import Version


W3D_CHUNK_ANIMATION_HEADER = 0x00000201


class AnimationHeader(Struct):
    version = Version()
    name = ""
    hierarchy_name = ""
    num_frames = 0
    frame_rate = 0

    @staticmethod
    def read(io_stream):
        return AnimationHeader(
            version=Version.read(io_stream),
            name=read_fixed_string(io_stream),
            hierarchy_name=read_fixed_string(io_stream),
            num_frames=read_ulong(io_stream),
            frame_rate=read_ulong(io_stream))

    @staticmethod
    def size(include_head=True):
        return const_size(44, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_ANIMATION_HEADER, io_stream,
                         self.size(False))
        self.version.write(io_stream)
        write_fixed_string(self.name, io_stream)
        write_fixed_string(self.hierarchy_name, io_stream)
        write_ulong(self.num_frames, io_stream)
        write_ulong(self.frame_rate, io_stream)


W3D_CHUNK_ANIMATION_CHANNEL = 0x00000202


class AnimationChannel(Struct):
    first_frame = 0
    last_frame = 0
    vector_len = 0
    type = 0
    pivot = 0
    unknown = 0
    data = []
    pad_bytes = []

    @staticmethod
    def read(io_stream, chunk_end):
        result = AnimationChannel(
            first_frame=read_ushort(io_stream),
            last_frame=read_ushort(io_stream),
            vector_len=read_ushort(io_stream),
            type=read_ushort(io_stream),
            pivot=read_ushort(io_stream),
            unknown=read_ushort(io_stream),
            data=[],
            pad_bytes=[])

        num_elements = result.last_frame - result.first_frame + 1

        if result.vector_len == 1:
            result.data = read_fixed_list(io_stream, num_elements, read_float)
        else:
            result.data = read_fixed_list(
                io_stream, num_elements, read_quaternion)

        while io_stream.tell() < chunk_end:
            result.pad_bytes.append(read_ubyte(io_stream))
        return result

    def size(self, include_head=True):
        size = const_size(12, include_head)
        size += (len(self.data) * self.vector_len) * 4
        size += len(self.pad_bytes)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_ANIMATION_CHANNEL, io_stream,
                         self.size(False))

        write_ushort(self.first_frame, io_stream)
        write_ushort(self.last_frame, io_stream)
        write_ushort(self.vector_len, io_stream)
        write_ushort(self.type, io_stream)
        write_ushort(self.pivot, io_stream)
        write_ushort(self.unknown, io_stream)

        if self.vector_len == 1:
            write_list(self.data, io_stream, write_float)
        else:
            write_list(self.data, io_stream, write_quaternion)
        write_list(self.pad_bytes, io_stream, write_ubyte)

    @staticmethod
    def parse(xml_channel):
        result = AnimationChannel(
            pivot=int(xml_channel.attributes['Pivot'].value),
            first_frame=int(xml_channel.attributes['FirstFrame'].value),
            vector_len=1,
            type=0,
            data=[])

        type_name = xml_channel.attributes['Type'].value

        if type_name == 'XTranslation':
            result.type = 0
        elif type_name == 'YTranslation':
            result.type = 1
        elif type_name == 'ZTranslation':
            result.type = 2
        elif type_name == 'Orientation':
            result.vector_len = 4
            result.type = 6

        if xml_channel.tagName == 'ChannelScalar':
            for value in xml_channel.childs():
                result.data.append(parse_value(value, float))
        elif xml_channel.tagName == 'ChannelQuaternion':
            for value in xml_channel.childs():
                result.data.append(parse_quaternion(value))
   
        result.last_frame = result.first_frame + len(result.data) - 1
        return result

    def create(self, doc):
        if self.type < 6:
            channel = doc.createElement('ChannelScalar')
            if self.type == 0:
                channel.setAttribute('Type', 'XTranslation')
            elif self.type == 1:
                channel.setAttribute('Type', 'YTranslation')
            elif self.type == 2:
                channel.setAttribute('Type', 'ZTranslation')
        else:
            channel = doc.createElement('Orientation')
            channel.setAttribute('Type', 'Orientation')

        channel.setAttribute('Pivot', str(self.pivot))
        channel.setAttribute('FirstFrame', str(self.first_frame))

        if self.type < 6:
            for value in self.data:
                channel.appendChild(create_value(value, doc, 'Frame'))
        else:
            for value in self.data:
                channel.appendChild(create_quaternion(value, doc, 'Frame'))
        return channel


W3D_CHUNK_ANIMATION_BIT_CHANNEL = 0x00000203


class AnimationBitChannel(Struct):
    first_frame = 0
    last_frame = 0
    type = 0
    pivot = 0
    default = 1.0
    data = []

    @staticmethod
    def read(io_stream, chunk_end):
        result = AnimationBitChannel(
            first_frame=read_ushort(io_stream),
            last_frame=read_ushort(io_stream),
            type=read_ushort(io_stream),
            pivot=read_ushort(io_stream),
            default=float(read_ubyte(io_stream) / 255))

        num_frames = result.last_frame - result.first_frame + 1
        result.data = [float] * num_frames
        temp = 0
        for i in range(num_frames):
            if i % 8 == 0:
                temp = read_ubyte(io_stream)
            val = (temp & (1 << (i % 8))) != 0
            result.data[i] = val
        return result

    def size(self, include_head=True):
        size = const_size(9, include_head)
        size += (int)(len(self.data) / 8)
        if len(self.data) % 8 > 0:
            size += 1
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_ANIMATION_BIT_CHANNEL, io_stream,
                         self.size(False))
        write_ushort(self.first_frame, io_stream)
        write_ushort(self.last_frame, io_stream)
        write_ushort(self.type, io_stream)
        write_ushort(self.pivot, io_stream)
        write_ubyte(int(self.default * 255), io_stream)

        value = 0x00
        for i, datum in enumerate(self.data):
            if i > 0 and i % 8 == 0:
                write_ubyte(value, io_stream)
                value = 0x00
            value |= (int(datum) << (i % 8))
        write_ubyte(value, io_stream)

    @staticmethod
    def parse(xml_bit_channel):
        result = AnimationBitChannel(
            pivot=int(xml_bit_channel.attributes['Pivot'].value),
            first_frame=int(xml_bit_channel.attributes['FirstFrame'].value),
            type=0,
            default=True,
            data=[])

        if xml_bit_channel.tagName == 'ChannelScalar':
            for value in xml_bit_channel.childs():
                result.data.append(parse_value(value, float))
   
        result.last_frame = result.first_frame + len(result.data) - 1
        return result

    def create(self, doc):
        channel = doc.createElement('ChannelScalar')
        channel.setAttribute('Type', 'Visibility')

        channel.setAttribute('Pivot', str(self.pivot))
        channel.setAttribute('FirstFrame', str(self.first_frame))

        for value in self.data:
            channel.appendChild(create_value(value, doc, 'Frame'))
        return channel


W3D_CHUNK_ANIMATION = 0x00000200


class Animation(Struct):
    header = AnimationHeader()
    channels = []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = Animation(channels=[])

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)
            if chunk_type == W3D_CHUNK_ANIMATION_HEADER:
                result.header = AnimationHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_ANIMATION_CHANNEL:
                result.channels.append(
                    AnimationChannel.read(io_stream, subchunk_end))
            elif chunk_type == W3D_CHUNK_ANIMATION_BIT_CHANNEL:
                result.channels.append(
                    AnimationBitChannel.read(io_stream, subchunk_end))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self):
        size = self.header.size()
        size += list_size(self.channels, False)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_ANIMATION, io_stream,
                         self.size(), has_sub_chunks=True)
        self.header.write(io_stream)

        for channel in self.channels:
            channel.write(io_stream)

    @staticmethod
    def parse(xml_animation):
        result = Animation(
            header=AnimationHeader(),
            channels=[])

        result.header.name = xml_animation.attributes['id'].value
        result.header.hierarchy_name = xml_animation.attributes['Hierarchy'].value
        result.header.num_frames = int(xml_animation.attributes['NumFrames'].value)
        result.header.frame_rate = int(xml_animation.attributes['FrameRate'].value)

        xml_channels_list = xml_animation.getElementsByTagName('Channels')[0]
        for xml_channel in xml_channels_list.childs():
            if xml_channel.attributes['Type'].value == 'Visibility':
                result.channels.append(AnimationBitChannel.parse(xml_channel))
            else:
                result.channels.append(AnimationChannel.parse(xml_channel))
        return result

    def create(self, doc):
        animation = doc.createElement('W3DAnimation')
        animation.setAttribute('id', self.header.name)
        animation.setAttribute('Hierarchy', self.header.hierarchy_name)
        animation.setAttribute('NumFrames', str(self.header.num_frames))
        animation.setAttribute('FrameRate', str(self.header.frame_rate))

        channels = doc.createElement('Channels')
        animation.appendChild(channels)
        for channel in self.channels:
            channels.appendChild(channel.create(doc))

        return animation
