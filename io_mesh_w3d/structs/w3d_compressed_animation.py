# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019

from io_mesh_w3d.structs.struct import Struct
from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.import_utils_w3d import read_fixed_array
from io_mesh_w3d.w3d_adaptive_delta import decode
from io_mesh_w3d.io_binary import *


W3D_CHUNK_COMPRESSED_ANIMATION_HEADER = 0x00000281


class CompressedAnimationHeader(Struct):
    version = Version()
    name = ""
    hierarchy_name = ""
    num_frames = 0
    frame_rate = 0
    flavor = 0

    @staticmethod
    def read(io_stream):
        return CompressedAnimationHeader(
            version=Version.read(io_stream),
            name=read_fixed_string(io_stream),
            hierarchy_name=read_fixed_string(io_stream),
            num_frames=read_ulong(io_stream),
            frame_rate=read_ushort(io_stream),
            flavor=read_ushort(io_stream))


class TimeCodedDatum(Struct):
    time_code = 0
    non_interpolated = False
    value = None

    @staticmethod
    def read(io_stream, type_):
        result = TimeCodedDatum(
            time_code=read_long(io_stream),
            value=read_channel_value(io_stream, type_))

        if (result.time_code >> 31) == 1:
            result.time_code &= ~(1 << 31)
            result.non_interpolated = True
        return result


class TimeCodedBitDatum(Struct):
    time_code = 0
    value = None

    @staticmethod
    def read(io_stream):
        result = TimeCodedBitDatum(
            time_code=read_long(io_stream),
            value=False)

        if (result.time_code >> 31) == 1:
            result.value = True
            result.time_code &= ~(1 << 31)
        return result


class TimeCodedAnimationChannel(Struct):
    num_time_codes = 0
    pivot = -1
    vector_len = 0
    type = 0
    time_codes = []

    @staticmethod
    def read(io_stream):
        result = TimeCodedAnimationChannel(
            num_time_codes=read_ulong(io_stream),
            pivot=read_ushort(io_stream),
            vector_len=read_ubyte(io_stream),
            type=read_ubyte(io_stream),
            time_codes=[])

        for _ in range(result.num_time_codes):
            result.time_codes.append(TimeCodedDatum.read(io_stream, result.type))
        return result


class AdaptiveDeltaAnimationChannel(Struct):
    num_time_codes = 0
    pivot = -1
    vector_len = 0
    type = 0
    scale = 0
    data = []

    @staticmethod
    def read(io_stream):
        result = AdaptiveDeltaAnimationChannel(
            num_time_codes=read_ulong(io_stream),
            pivot=read_ushort(io_stream),
            vector_len=read_ubyte(io_stream),
            type=read_ubyte(io_stream),
            scale=read_short(io_stream),
            data=[])

        result.data = AdaptiveDeltaData.read(io_stream, result, 4)

        io_stream.read(3)  # read unknown bytes at the end
        return result


class AdaptiveDeltaMotionAnimationChannel(Struct):
    scale = 0.0
    initial_value = None
    data = []

    @staticmethod
    def read(io_stream, channel, bits):
        result = AdaptiveDeltaMotionAnimationChannel(
            scale=read_float(io_stream),
            data=[])

        data = AdaptiveDeltaData.read(io_stream, channel, bits)
        result.data = decode(data, channel, result.scale)
        return result


class AdaptiveDeltaBlock(Struct):
    vector_index = 0
    block_index = 0
    delta_bytes = []

    @staticmethod
    def read(io_stream, vec_index, bits):
        result = AdaptiveDeltaBlock(
            vector_index=vec_index,
            block_index=read_ubyte(io_stream),
            delta_bytes=[])

        result.delta_bytes = read_fixed_array(io_stream, bits * 2, read_byte)
        return result


class AdaptiveDeltaData(Struct):
    initial_value = None
    delta_blocks = []
    bit_count = 0

    @staticmethod
    def read(io_stream, channel, bits):
        result = AdaptiveDeltaData(
            initial_value=read_channel_value(io_stream, channel.type),
            delta_blocks=[],
            bit_count=bits)

        count = (channel.num_time_codes + 15) >> 4

        for _ in range(count):
            for j in range(channel.vector_len):
                result.delta_blocks.append(
                    AdaptiveDeltaBlock.read(io_stream, j, bits))
        return result


class TimeCodedBitChannel(Struct):
    num_time_codes = 0
    pivot = 0
    type = 0
    default_value = False
    data = []

    @staticmethod
    def read(io_stream):
        result = TimeCodedBitChannel(
            num_time_codes=read_long(io_stream),
            pivot=read_short(io_stream),
            type=read_ubyte(io_stream),
            default_value=read_ubyte(io_stream),
            data=[])

        for _ in range(result.num_time_codes):
            result.data.append(TimeCodedBitDatum.read(io_stream))
        return result


class MotionChannel(Struct):
    delta_type = 0
    vector_len = 0
    type = 0
    num_time_codes = 0
    pivot = 0
    data = []

    # TODO: find a nice way for this
    @staticmethod
    def read_time_coded_data(io_stream, channel):
        result = []

        for x in range(channel.num_time_codes):
            datum = TimeCodedDatum(
                time_code=read_short(io_stream))
            result.append(datum)

        if channel.num_time_codes % 2 != 0:
            read_short(io_stream)  # alignment

        for x in range(channel.num_time_codes):
            result[x].value = read_channel_value(io_stream, channel.type)
        return result

    @staticmethod
    def read(io_stream):
        read_ubyte(io_stream)  # zero

        result = MotionChannel(
            delta_type=read_ubyte(io_stream),
            vector_len=read_ubyte(io_stream),
            type=read_ubyte(io_stream),
            num_time_codes=read_short(io_stream),
            pivot=read_short(io_stream),
            data=[])

        if result.delta_type == 0:
            result.data = MotionChannel.read_time_coded_data(io_stream, result)
        elif result.delta_type == 1:
            result.data = AdaptiveDeltaMotionAnimationChannel.read(
                io_stream, result, 4)
        elif result.delta_type == 2:
            result.data = AdaptiveDeltaMotionAnimationChannel.read(
                io_stream, result, 8)
        else:
            print("unknown motion deltatype!!")
        return result


W3D_CHUNK_COMPRESSED_ANIMATION = 0x00000280
W3D_CHUNK_COMPRESSED_ANIMATION_CHANNEL = 0x00000282
W3D_CHUNK_COMPRESSED_BIT_CHANNEL = 0x00000283
W3D_CHUNK_COMPRESSED_ANIMATION_MOTION_CHANNEL = 0x00000284


class CompressedAnimation(Struct):
    header = CompressedAnimationHeader()
    time_coded_channels = []
    adaptive_delta_channels = []
    time_coded_bit_channels = []
    motion_channels = []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = CompressedAnimation(
            time_coded_channels=[],
            adaptive_delta_channels=[],
            time_coded_bit_channels=[],
            motion_channels=[])

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, _) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_COMPRESSED_ANIMATION_HEADER:
                result.header = CompressedAnimationHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_COMPRESSED_ANIMATION_CHANNEL:
                if result.header.flavor == 0:
                    result.time_coded_channels.append(
                        TimeCodedAnimationChannel.read(io_stream))
                elif result.header.flavor == 1:
                    result.adaptive_delta_channels.append(
                        AdaptiveDeltaAnimationChannel.read(io_stream))
                else:
                    skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
            elif chunk_type == W3D_CHUNK_COMPRESSED_BIT_CHANNEL:
                result.time_coded_bit_channels.append(
                    TimeCodedBitChannel.read(io_stream))
            elif chunk_type == W3D_CHUNK_COMPRESSED_ANIMATION_MOTION_CHANNEL:
                result.motion_channels.append(
                    MotionChannel.read(io_stream))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result