# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3d.structs.version import Version
from io_mesh_w3d.w3d.utils.helpers import *

W3D_CHUNK_COMPRESSED_ANIMATION_HEADER = 0x00000281

TIME_CODED_FLAVOR = 0
ADAPTIVE_DELTA_FLAVOR = 1


class CompressedAnimationHeader:
    def __init__(
            self,
            version=Version(
                major=0,
                minor=1),
            name='',
            hierarchy_name='',
            num_frames=0,
            frame_rate=0,
            flavor=0):
        self.version = version
        self.name = name
        self.hierarchy_name = hierarchy_name
        self.num_frames = num_frames
        self.frame_rate = frame_rate
        self.flavor = flavor

    @staticmethod
    def read(io_stream):
        return CompressedAnimationHeader(
            version=Version.read(io_stream),
            name=read_fixed_string(io_stream),
            hierarchy_name=read_fixed_string(io_stream),
            num_frames=read_ulong(io_stream),
            frame_rate=read_ushort(io_stream),
            flavor=read_ushort(io_stream))

    @staticmethod
    def size(include_head=True):
        return const_size(44, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_COMPRESSED_ANIMATION_HEADER, io_stream, self.size(False))
        self.version.write(io_stream)
        write_fixed_string(self.name, io_stream)
        write_fixed_string(self.hierarchy_name, io_stream)
        write_ulong(self.num_frames, io_stream)
        write_ushort(self.frame_rate, io_stream)
        write_ushort(self.flavor, io_stream)


class TimeCodedDatum:
    def __init__(self, time_code=0, interpolated=False, value=None):
        self.time_code = time_code
        self.interpolated = interpolated
        self.value = value

    @staticmethod
    def read(io_stream, datum_type):
        result = TimeCodedDatum(
            time_code=read_ulong(io_stream),
            interpolated=False,
            value=read_channel_value(io_stream, datum_type))

        if (result.time_code >> 31) == 1:
            result.time_code &= ~(1 << 31)
            result.interpolated = True
        return result

    @staticmethod
    def size(datum_type):
        if datum_type == 6:
            return 20
        return 8

    def write(self, io_stream, datum_type):
        time_code = self.time_code
        if self.interpolated:
            time_code |= (1 << 31)

        write_ulong(time_code, io_stream)
        write_channel_value(self.value, io_stream, datum_type)


class TimeCodedAnimationChannel:
    def __init__(self, num_time_codes=0, pivot=-1, vector_len=0, channel_type=0, time_codes=None):
        self.num_time_codes = num_time_codes
        self.pivot = pivot
        self.vector_len = vector_len
        self.channel_type = channel_type
        self.time_codes = time_codes if time_codes is not None else []

    @staticmethod
    def read(io_stream):
        result = TimeCodedAnimationChannel(
            num_time_codes=read_ulong(io_stream),
            pivot=read_ushort(io_stream),
            vector_len=read_ubyte(io_stream),
            channel_type=read_ubyte(io_stream),
            time_codes=[])

        result.time_codes = read_fixed_list(io_stream, result.num_time_codes, TimeCodedDatum.read, result.channel_type)
        return result

    def size(self, include_head=True):
        size = const_size(8, include_head)
        for time_code in self.time_codes:
            size += time_code.size(self.channel_type)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_COMPRESSED_ANIMATION_CHANNEL, io_stream, self.size(False))
        write_ulong(self.num_time_codes, io_stream)
        write_ushort(self.pivot, io_stream)
        write_ubyte(self.vector_len, io_stream)
        write_ubyte(self.channel_type, io_stream)
        write_list(self.time_codes, io_stream, TimeCodedDatum.write, self.channel_type)


class AdaptiveDeltaBlock:
    def __init__(self, vector_index=0, block_index=0, delta_bytes=None):
        self.vector_index = vector_index
        self.block_index = block_index
        self.delta_bytes = delta_bytes if delta_bytes is not None else []

    @staticmethod
    def read(io_stream, vec_index, bits):
        result = AdaptiveDeltaBlock(
            vector_index=vec_index,
            block_index=read_ubyte(io_stream),
            delta_bytes=[])

        result.delta_bytes = read_fixed_list(io_stream, bits * 2, read_byte)
        return result

    def size(self):
        return 1 + len(self.delta_bytes)

    def write(self, io_stream):
        write_ubyte(self.block_index, io_stream)
        write_list(self.delta_bytes, io_stream, write_byte)


class AdaptiveDeltaData:
    def __init__(self, initial_value=None, delta_blocks=None, bit_count=0):
        self.initial_value = initial_value
        self.delta_blocks = delta_blocks if delta_blocks is not None else []
        self.bit_count = bit_count

    @staticmethod
    def read(io_stream, channel, bits):
        result = AdaptiveDeltaData(
            initial_value=read_channel_value(io_stream, channel.channel_type),
            bit_count=bits)

        count = (channel.num_time_codes + 15) >> 4

        for _ in range(count):
            for j in range(channel.vector_len):
                result.delta_blocks.append(AdaptiveDeltaBlock.read(io_stream, j, bits))
        return result

    def size(self, data_type):
        size = 4
        if data_type == 6:
            size = 16
        size += list_size(self.delta_blocks, False)
        return size

    def write(self, io_stream, data_type):
        write_channel_value(self.initial_value, io_stream, data_type)
        write_list(self.delta_blocks, io_stream, AdaptiveDeltaBlock.write)


class AdaptiveDeltaAnimationChannel:
    def __init__(self, num_time_codes=0, pivot=-1, vector_len=0, channel_type=0, scale=0, data=None):
        self.num_time_codes = num_time_codes
        self.pivot = pivot
        self.vector_len = vector_len
        self.channel_type = channel_type
        self.scale = scale
        self.data = data

    @staticmethod
    def read(io_stream):
        result = AdaptiveDeltaAnimationChannel(
            num_time_codes=read_ulong(io_stream),
            pivot=read_ushort(io_stream),
            vector_len=read_ubyte(io_stream),
            channel_type=read_ubyte(io_stream),
            scale=read_short(io_stream))

        result.data = AdaptiveDeltaData.read(io_stream, result, 4)
        io_stream.read(3)  # read unknown bytes at the end
        return result

    def size(self, include_head=True):
        size = const_size(13, include_head)
        size += self.data.size(self.channel_type)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_COMPRESSED_ANIMATION_CHANNEL, io_stream, self.size(False))
        write_ulong(self.num_time_codes, io_stream)
        write_ushort(self.pivot, io_stream)
        write_ubyte(self.vector_len, io_stream)
        write_ubyte(self.channel_type, io_stream)
        write_short(self.scale, io_stream)
        self.data.write(io_stream, self.channel_type)

        write_list(bytes([0, 0, 0]), io_stream, write_ubyte)  # write unknown bytes at the end


class AdaptiveDeltaMotionAnimationChannel:
    def __init__(self, scale=0.0, data=None):
        self.scale = scale
        self.data = data

    @staticmethod
    def read(io_stream, channel, bits):
        result = AdaptiveDeltaMotionAnimationChannel(
            scale=read_float(io_stream),
            data=None)

        result.data = AdaptiveDeltaData.read(io_stream, channel, bits)
        return result

    def size(self, channel_type):
        return 4 + self.data.size(channel_type)

    def write(self, io_stream, channel_type):
        write_float(self.scale, io_stream)
        self.data.write(io_stream, channel_type)


class TimeCodedBitDatum:
    def __init__(self, time_code=0, value=False):
        self.time_code = time_code
        self.value = value

    @staticmethod
    def read(io_stream):
        result = TimeCodedBitDatum(
            time_code=read_ulong(io_stream))

        if (result.time_code >> 31) == 1:
            result.value = True
            result.time_code &= ~(1 << 31)
        return result

    def size(self):
        return 4

    def write(self, io_stream):
        time_code = self.time_code
        if self.value:
            time_code |= (1 << 31)
        write_ulong(time_code, io_stream)


class TimeCodedBitChannel:
    def __init__(self, num_time_codes=0, pivot=0, channel_type=0, default_value=False, time_codes=None):
        self.num_time_codes = num_time_codes
        self.pivot = pivot
        self.channel_type = channel_type
        self.default_value = default_value
        self.time_codes = time_codes if time_codes is not None else []

    @staticmethod
    def read(io_stream):
        result = TimeCodedBitChannel(
            num_time_codes=read_ulong(io_stream),
            pivot=read_short(io_stream),
            channel_type=read_ubyte(io_stream),
            default_value=read_ubyte(io_stream))

        result.time_codes = read_fixed_list(io_stream, result.num_time_codes, TimeCodedBitDatum.read)
        return result

    def size(self, include_head=True):
        size = const_size(8, include_head)
        size += list_size(self.time_codes, False)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_COMPRESSED_BIT_CHANNEL, io_stream, self.size(False))
        write_ulong(self.num_time_codes, io_stream)
        write_ushort(self.pivot, io_stream)
        write_ubyte(self.channel_type, io_stream)
        write_ubyte(self.default_value, io_stream)
        write_list(self.time_codes, io_stream, TimeCodedBitDatum.write)


class MotionChannel:
    def __init__(self, delta_type=0, vector_len=0, channel_type=0, num_time_codes=0, pivot=0, data=None):
        self.delta_type = delta_type
        self.vector_len = vector_len
        self.channel_type = channel_type
        self.num_time_codes = num_time_codes
        self.pivot = pivot
        self.data = data

    def read_time_coded_data(self, io_stream):
        result = []

        for _ in range(self.num_time_codes):
            datum = TimeCodedDatum(
                time_code=read_short(io_stream),
                interpolated=True)  # non interpolation is not supported here
            result.append(datum)

        if self.num_time_codes % 2 != 0:
            read_short(io_stream)  # alignment

        for x in range(self.num_time_codes):
            result[x].value = read_channel_value(io_stream, self.channel_type)
        return result

    def write_time_coded_data(self, io_stream):
        for datum in self.data:
            write_short(datum.time_code, io_stream)

        if self.num_time_codes % 2 != 0:
            write_short(0, io_stream)  # alignment

        for datum in self.data:
            write_channel_value(datum.value, io_stream, self.channel_type)

    @staticmethod
    def read(io_stream):
        read_ubyte(io_stream)  # zero

        result = MotionChannel(
            delta_type=read_ubyte(io_stream),
            vector_len=read_ubyte(io_stream),
            channel_type=read_ubyte(io_stream),
            num_time_codes=read_short(io_stream),
            pivot=read_short(io_stream))

        if result.delta_type == 0:
            result.data = result.read_time_coded_data(io_stream)
        else:
            result.data = AdaptiveDeltaMotionAnimationChannel.read(io_stream, result, result.delta_type * 4)
        return result

    def size(self, include_head=True):
        size = const_size(8, include_head)
        if self.delta_type == 0:
            for datum in self.data:
                size += datum.size(self.channel_type) - 2  # time_code is a short here, not long!
            if self.num_time_codes % 2 != 0:
                size += 2  # alignment
        else:
            size += self.data.size(self.channel_type)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_COMPRESSED_ANIMATION_MOTION_CHANNEL,
                         io_stream, self.size(False), has_sub_chunks=True)
        write_ubyte(0, io_stream)
        write_ubyte(self.delta_type, io_stream)
        write_ubyte(self.vector_len, io_stream)
        write_ubyte(self.channel_type, io_stream)
        write_short(self.num_time_codes, io_stream)
        write_short(self.pivot, io_stream)

        if self.delta_type == 0:
            self.write_time_coded_data(io_stream)
        else:
            self.data.write(io_stream, self.channel_type)


W3D_CHUNK_COMPRESSED_ANIMATION = 0x00000280
W3D_CHUNK_COMPRESSED_ANIMATION_CHANNEL = 0x00000282
W3D_CHUNK_COMPRESSED_BIT_CHANNEL = 0x00000283
W3D_CHUNK_COMPRESSED_ANIMATION_MOTION_CHANNEL = 0x00000284


class CompressedAnimation:
    def __init__(self, header=None, time_coded_channels=None, adaptive_delta_channels=None,
                 time_coded_bit_channels=None, motion_channels=None):
        self.header = header
        self.time_coded_channels = time_coded_channels if time_coded_channels is not None else []
        self.adaptive_delta_channels = adaptive_delta_channels if adaptive_delta_channels is not None else []
        self.time_coded_bit_channels = time_coded_bit_channels if time_coded_bit_channels is not None else []
        self.motion_channels = motion_channels if motion_channels is not None else []

    def validate(self, context, w3x=False):
        if not self.time_coded_channels:
            context.error('Scene does not contain any animation data')
            return False

        if w3x:
            return True

        if len(self.header.name) > STRING_LENGTH:
            context.error('animation name exceeds max length of: ' + str(STRING_LENGTH))
            return False
        if len(self.header.hierarchy_name) > STRING_LENGTH:
            context.error('animation hierarchy name exceeds max length of: ' + str(STRING_LENGTH))
            return False
        return True

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = CompressedAnimation(header=None)

        while io_stream.tell() < chunk_end:
            chunk_type, chunk_size, _ = read_chunk_head(io_stream)
            if chunk_type == W3D_CHUNK_COMPRESSED_ANIMATION_HEADER:
                result.header = CompressedAnimationHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_COMPRESSED_ANIMATION_CHANNEL:
                if result.header.flavor == TIME_CODED_FLAVOR:
                    result.time_coded_channels.append(TimeCodedAnimationChannel.read(io_stream))
                elif result.header.flavor == ADAPTIVE_DELTA_FLAVOR:
                    result.adaptive_delta_channels.append(AdaptiveDeltaAnimationChannel.read(io_stream))
                else:
                    skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
            elif chunk_type == W3D_CHUNK_COMPRESSED_BIT_CHANNEL:
                result.time_coded_bit_channels.append(TimeCodedBitChannel.read(io_stream))
            elif chunk_type == W3D_CHUNK_COMPRESSED_ANIMATION_MOTION_CHANNEL:
                result.motion_channels.append(MotionChannel.read(io_stream))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self):
        size = self.header.size()
        size += list_size(self.time_coded_channels, False)
        size += list_size(self.adaptive_delta_channels, False)
        size += list_size(self.time_coded_bit_channels, False)
        size += list_size(self.motion_channels, False)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_COMPRESSED_ANIMATION, io_stream, self.size(), has_sub_chunks=True)
        self.header.write(io_stream)
        write_list(self.time_coded_channels, io_stream, TimeCodedAnimationChannel.write)
        write_list(self.adaptive_delta_channels, io_stream, AdaptiveDeltaAnimationChannel.write)
        write_list(self.time_coded_bit_channels, io_stream, TimeCodedBitChannel.write)
        write_list(self.motion_channels, io_stream, MotionChannel.write)
