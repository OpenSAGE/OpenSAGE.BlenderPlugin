# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3d.structs.version import Version
from io_mesh_w3d.w3d.utils.helpers import *
from io_mesh_w3d.w3x.io_xml import *

W3D_CHUNK_ANIMATION_HEADER = 0x00000201

CHANNEL_X = 0
CHANNEL_Y = 1
CHANNEL_Z = 2
CHANNEL_Q = 6
CHANNEL_VIS = 15


class AnimationHeader:
    def __init__(self, version=Version(major=4, minor=1), name='', hierarchy_name='', num_frames=0, frame_rate=0):
        self.version = version
        self.name = name
        self.hierarchy_name = hierarchy_name
        self.num_frames = num_frames
        self.frame_rate = frame_rate

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
        write_chunk_head(W3D_CHUNK_ANIMATION_HEADER, io_stream, self.size(False))
        self.version.write(io_stream)
        write_fixed_string(self.name, io_stream)
        write_fixed_string(self.hierarchy_name, io_stream)
        write_ulong(self.num_frames, io_stream)
        write_ulong(self.frame_rate, io_stream)


W3D_CHUNK_ANIMATION_CHANNEL = 0x00000202


class AnimationChannel:
    def __init__(self, first_frame=0, last_frame=0, vector_len=1, type=0, pivot=0, unknown=0, data=None):
        self.first_frame = first_frame
        self.last_frame = last_frame
        self.vector_len = vector_len
        self.type = type
        self.pivot = pivot
        self.unknown = unknown
        self.data = data if data is not None else []
        self.pad_bytes = []

    @staticmethod
    def read(io_stream, chunk_end):
        result = AnimationChannel(
            first_frame=read_ushort(io_stream),
            last_frame=read_ushort(io_stream),
            vector_len=read_ushort(io_stream),
            type=read_ushort(io_stream),
            pivot=read_ushort(io_stream),
            unknown=read_ushort(io_stream))

        num_elements = result.last_frame - result.first_frame + 1

        if result.vector_len == 1:
            result.data = read_fixed_list(io_stream, num_elements, read_float)
        else:
            result.data = read_fixed_list(io_stream, num_elements, read_quaternion)

        while io_stream.tell() < chunk_end:
            result.pad_bytes.append(read_ubyte(io_stream))
        return result

    def size(self, include_head=True):
        size = const_size(12, include_head)
        size += (len(self.data) * self.vector_len) * 4
        size += len(self.pad_bytes)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_ANIMATION_CHANNEL, io_stream, self.size(False))

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
            pivot=int(xml_channel.get('Pivot')),
            first_frame=int(xml_channel.get('FirstFrame')))

        type_name = xml_channel.get('Type')

        if type_name == 'XTranslation':
            result.type = CHANNEL_X
        elif type_name == 'YTranslation':
            result.type = CHANNEL_Y
        elif type_name == 'ZTranslation':
            result.type = CHANNEL_Z
        else:
            result.vector_len = 4
            result.type = CHANNEL_Q

        if xml_channel.tag == 'ChannelScalar':
            for value in xml_channel:
                result.data.append(parse_float_value(value))
        else:
            for value in xml_channel:
                result.data.append(parse_quaternion(value))

        result.last_frame = result.first_frame + len(result.data) - 1
        return result

    def create(self, parent):
        if self.type < CHANNEL_Q:
            channel = create_node(parent, 'ChannelScalar')
            if self.type == CHANNEL_X:
                channel.set('Type', 'XTranslation')
            elif self.type == CHANNEL_Y:
                channel.set('Type', 'YTranslation')
            else:
                channel.set('Type', 'ZTranslation')
        else:
            channel = create_node(parent, 'ChannelQuaternion')
            channel.set('Type', 'Orientation')

        channel.set('Pivot', str(self.pivot))
        channel.set('FirstFrame', str(self.first_frame))

        if self.type < CHANNEL_Q:
            for value in self.data:
                create_value(value, channel, 'Frame')
        else:
            for value in self.data:
                create_quaternion(value, channel, 'Frame')


W3D_CHUNK_ANIMATION_BIT_CHANNEL = 0x00000203


class AnimationBitChannel:
    def __init__(self, first_frame=0, last_frame=0, type=0, pivot=0, default=1.0, data=None):
        self.first_frame = first_frame
        self.last_frame = last_frame
        self.type = type
        self.pivot = pivot
        self.default = default
        self.data = data if data is not None else []

    @staticmethod
    def read(io_stream):
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
        size += int(len(self.data) / 8)
        if len(self.data) % 8 > 0:
            size += 1
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_ANIMATION_BIT_CHANNEL, io_stream, self.size(False))
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
            pivot=int(xml_bit_channel.get('Pivot')),
            first_frame=int(xml_bit_channel.get('FirstFrame')),
            type=0,
            default=True)

        for value in xml_bit_channel:
            result.data.append(parse_float_value(value))

        result.last_frame = result.first_frame + len(result.data) - 1
        return result

    def create(self, parent):
        channel = create_node(parent, 'ChannelScalar')
        channel.set('Type', 'Visibility')

        channel.set('Pivot', str(self.pivot))
        channel.set('FirstFrame', str(self.first_frame))

        for value in self.data:
            create_value(value, channel, 'Frame')


W3D_CHUNK_ANIMATION = 0x00000200


class Animation:
    def __init__(self, header=None, channels=None):
        self.header = header
        self.channels = channels if channels is not None else []

    def validate(self, context):
        if not self.channels:
            context.error('Scene does not contain any animation data!')
            return False

        if context.file_format == 'W3X':
            return True

        if len(self.header.name) >= STRING_LENGTH:
            context.error(f'animation name \'{self.header.name}\' exceeds max length of {STRING_LENGTH}')
            return False
        if len(self.header.hierarchy_name) >= STRING_LENGTH:
            context.error(f'armature name \'{self.header.hierarchy_name}\' exceeds max length of {STRING_LENGTH}')
            return False
        return True

    # pure name. e.g. SUANTIAIRSHIP_IDLA
    def name(self):
        return self.header.name
    
    @staticmethod
    def read(context, io_stream, chunk_end):
        result = Animation()

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)
            if chunk_type == W3D_CHUNK_ANIMATION_HEADER:
                result.header = AnimationHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_ANIMATION_CHANNEL:
                result.channels.append(AnimationChannel.read(io_stream, subchunk_end))
            elif chunk_type == W3D_CHUNK_ANIMATION_BIT_CHANNEL:
                result.channels.append(AnimationBitChannel.read(io_stream))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = const_size(0, include_head)
        size += self.header.size()
        size += list_size(self.channels, False)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_ANIMATION, io_stream, self.size(False), has_sub_chunks=True)
        self.header.write(io_stream)

        for channel in self.channels:
            channel.write(io_stream)

    @staticmethod
    def parse(context, xml_animation):
        result = Animation(header=AnimationHeader())

        result.header.name = xml_animation.get('id')
        result.header.hierarchy_name = xml_animation.get('Hierarchy')
        result.header.num_frames = int(xml_animation.get('NumFrames'))
        result.header.frame_rate = int(xml_animation.get('FrameRate'))

        for child in xml_animation:
            if child.tag == 'Channels':
                for channel_child in child:
                    if channel_child.tag in ['ChannelScalar', 'ChannelQuaternion']:
                        if channel_child.get('Type') == 'Visibility':
                            result.channels.append(AnimationBitChannel.parse(channel_child))
                        else:
                            result.channels.append(AnimationChannel.parse(channel_child))
                    else:
                        context.warning(f'unhandled node \'{channel_child.tag}\' in W3DAnimation Channels!')
            else:
                context.warning(f'unhandled node \'{child.tag}\' in W3DAnimation!')
        return result

    def create(self, parent):
        animation = create_node(parent, 'W3DAnimation')
        animation.set('id', self.header.name)
        animation.set('Hierarchy', self.header.hierarchy_name)
        animation.set('NumFrames', str(self.header.num_frames))
        animation.set('FrameRate', str(self.header.frame_rate))

        channels = create_node(animation, 'Channels')
        for channel in self.channels:
            channel.create(channels)
