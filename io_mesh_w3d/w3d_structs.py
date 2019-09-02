# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019

from mathutils import Vector, Quaternion
from io_mesh_w3d.io_binary import *
from io_mesh_w3d.import_utils_w3d import *
from io_mesh_w3d.w3d_adaptive_delta import *


class Struct():
    def __init__(self, *argv, **argd):
        if argd:
            # Update by dictionary
            self.__dict__.update(argd)
        else:
            # Update by position
            attrs = filter(lambda x: x[0:2] != "__", dir(self))
            for i, argv_ in enumerate(argv):
                setattr(self, attrs[i], argv_)


HEAD = 8  # 4(long = chunk_type) + 4 (long = chunk_size)

#######################################################################################
# Basic Structs
#######################################################################################


class RGBA(Struct):
    r = 0
    g = 0
    b = 0
    a = 0

    @staticmethod
    def read(io_stream):
        return RGBA(r=ord(io_stream.read(1)),
                    g=ord(io_stream.read(1)),
                    b=ord(io_stream.read(1)),
                    a=ord(io_stream.read(1)))

    @staticmethod
    def read_f(io_stream):
        return RGBA(r=read_float(io_stream),
                    g=read_float(io_stream),
                    b=read_float(io_stream),
                    a=read_float(io_stream))

    def write(self, io_stream):
        io_stream.write(struct.pack("B", self.r))
        io_stream.write(struct.pack("B", self.g))
        io_stream.write(struct.pack("B", self.b))
        io_stream.write(struct.pack("B", self.a))

    def write_f(self, io_stream):
        write_float(io_stream, self.r)
        write_float(io_stream, self.g)
        write_float(io_stream, self.b)
        write_float(io_stream, self.a)


class Version(Struct):
    major = 5
    minor = 0

    @staticmethod
    def read(io_stream):
        data = read_ulong(io_stream)
        return Version(major=data >> 16,
                       minor=data & 0xFFFF)

    def write(self, io_stream):
        write_ulong(io_stream, (self.major << 16) | self.minor)


#######################################################################################
# Hierarchy
#######################################################################################


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
    def size_in_bytes():
        return 36

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_HIERARCHY_HEADER, self.size_in_bytes())
        self.version.write(io_stream)
        write_fixed_string(io_stream, self.name)
        write_ulong(io_stream, self.num_pivots)
        write_vector(io_stream, self.center_pos)


W3D_CHUNK_PIVOTS = 0x00000102


class HierarchyPivot(Struct):
    name = ""
    parent_id = -1
    translation = Vector((0.0, 0.0, 0.0))
    euler_angles = Vector((0.0, 0.0, 0.0))
    rotation = Quaternion((1.0, 0.0, 0.0, 0.0))

    @staticmethod
    def read(io_stream):
        return HierarchyPivot(
            name=read_fixed_string(io_stream),
            parent_id=read_long(io_stream),
            translation=read_vector(io_stream),
            euler_angles=read_vector(io_stream),
            rotation=read_quaternion(io_stream))

    @staticmethod
    def size_in_bytes():
        return 60

    def write(self, io_stream):
        write_fixed_string(io_stream, self.name)
        write_long(io_stream, self.parent_id)
        write_vector(io_stream, self.translation)
        write_vector(io_stream, self.euler_angles)
        write_quaternion(io_stream, self.rotation)


W3D_CHUNK_HIERARCHY = 0x00000100
W3D_CHUNK_PIVOT_FIXUPS = 0x00000103


class Hierarchy(Struct):
    header = HierarchyHeader()
    pivots = []
    pivot_fixups = []

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
                result.pivots = read_array(
                    io_stream, subchunk_end, HierarchyPivot.read)
            elif chunk_type == W3D_CHUNK_PIVOT_FIXUPS:
                result.pivot_fixups = read_array(
                    io_stream, subchunk_end, read_vector)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def pivots_size(self):
        size = 0
        for pivot in self.pivots:
            size += pivot.size_in_bytes()
        return size

    def pivot_fixups_size(self):
        size = 0
        for _ in self.pivot_fixups:
            size += 12  # size in bytes
        return size

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        size += HEAD + self.pivots_size()
        if self.pivot_fixups:
            size += HEAD + self.pivot_fixups_size()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_HIERARCHY, self.size_in_bytes())
        self.header.write(io_stream)
        write_chunk_head(io_stream, W3D_CHUNK_PIVOTS, self.pivots_size())
        for pivot in self.pivots:
            pivot.write(io_stream)

        if self.pivot_fixups:
            write_chunk_head(io_stream, W3D_CHUNK_PIVOT_FIXUPS,
                             self.pivot_fixups_size())
            for fixup in self.pivot_fixups:
                write_vector(io_stream, fixup)


#######################################################################################
# Animation
#######################################################################################


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
    def size_in_bytes():
        return 44

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_ANIMATION_HEADER, self.size_in_bytes())
        self.version.write(io_stream)
        write_fixed_string(io_stream, self.name)
        write_fixed_string(io_stream, self.hierarchy_name)
        write_ulong(io_stream, self.num_frames)
        write_ulong(io_stream, self.frame_rate)


W3D_CHUNK_ANIMATION_CHANNEL = 0x00000202


class AnimationChannel(Struct):
    first_frame = 0
    last_frame = 0
    vector_len = 0
    type = 0
    pivot = 0
    unknown = 0
    data = []

    @staticmethod
    def read(io_stream, chunk_end):
        result = AnimationChannel(
            first_frame=read_ushort(io_stream),
            last_frame=read_ushort(io_stream),
            vector_len=read_ushort(io_stream),
            type=read_ushort(io_stream),
            pivot=read_ushort(io_stream),
            unknown=read_ushort(io_stream),
            data=[])

        if result.vector_len == 1:
            result.data = read_array(io_stream, chunk_end, read_float)
        elif result.vector_len == 4:
            result.data = read_array(io_stream, chunk_end, read_quaternion)
        return result

    def size_in_bytes(self):
        return 12 + (len(self.data) * self.vector_len) * 4

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_ANIMATION_CHANNEL, self.size_in_bytes())

        write_ushort(io_stream, self.first_frame)
        write_ushort(io_stream, self.last_frame)
        write_ushort(io_stream, self.vector_len)
        write_ushort(io_stream, self.type)
        write_ushort(io_stream, self.pivot)
        write_ushort(io_stream, self.unknown)

        for dat in self.data:
            if self.vector_len == 1:
                write_float(io_stream, dat)
            else:
                write_quaternion(io_stream, dat)


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
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        for channel in self.channels:
            size += HEAD + channel.size_in_bytes()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_ANIMATION,
                         self.size_in_bytes(), has_sub_chunks=True)
        self.header.write(io_stream)

        for channel in self.channels:
            channel.write(io_stream)


#######################################################################################
# Compressed Animation
#######################################################################################


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

#######################################################################################
# HLod
#######################################################################################


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
    def size_in_bytes():
        return 40

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_HLOD_HEADER, self.size_in_bytes())
        self.version.write(io_stream)
        write_ulong(io_stream, self.lod_count)
        write_fixed_string(io_stream, self.model_name)
        write_fixed_string(io_stream, self.hierarchy_name)


W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER = 0x00000703


class HLodArrayHeader(Struct):
    model_count = 0
    max_screen_size = 0.0

    @staticmethod
    def read(io_stream):
        return HLodArrayHeader(
            model_count=read_ulong(io_stream),
            max_screen_size=read_float(io_stream))

    @staticmethod
    def size_in_bytes():
        return HEAD

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_HLOD_SUB_OBJECT_ARRAY_HEADER,
                         self.size_in_bytes())
        write_ulong(io_stream, self.model_count)
        write_float(io_stream, self.max_screen_size)


W3D_CHUNK_HLOD_SUB_OBJECT = 0x00000704


class HLodSubObject(Struct):
    bone_index = 0
    name = ""

    @staticmethod
    def read(io_stream):
        return HLodSubObject(
            bone_index=read_ulong(io_stream),
            name=read_long_fixed_string(io_stream))

    @staticmethod
    def size_in_bytes():
        return 36

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_HLOD_SUB_OBJECT, self.size_in_bytes())
        write_ulong(io_stream, self.bone_index)
        write_long_fixed_string(io_stream, self.name)


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

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        for obj in self.sub_objects:
            size += HEAD + obj.size_in_bytes()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_HLOD_LOD_ARRAY,
                         self.size_in_bytes(), has_sub_chunks=True)
        self.header.write(io_stream)
        for obj in self.sub_objects:
            obj.write(io_stream)


W3D_CHUNK_HLOD = 0x00000700


class HLod(Struct):
    header = HLodHeader()
    lod_array = HLodArray()

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = HLod(
            header=None,
            lod_array=None
        )

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_HLOD_HEADER:
                result.header = HLodHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_HLOD_LOD_ARRAY:
                result.lod_array = HLodArray.read(context, io_stream, subchunk_end)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        size += HEAD + self.lod_array.size_in_bytes()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_HLOD,
                         self.size_in_bytes(), has_sub_chunks=True)
        self.header.write(io_stream)
        self.lod_array.write(io_stream)


#######################################################################################
# Box
#######################################################################################


W3D_CHUNK_BOX = 0x00000740


class Box(Struct):
    version = Version()
    box_type = 0
    collision_types = 0
    name = ""
    color = RGBA()
    center = Vector((0.0, 0.0, 0.0))
    extend = Vector((0.0, 0.0, 0.0))

    @staticmethod
    def read(io_stream):
        ver = Version.read(io_stream)
        flags = read_ulong(io_stream)
        return Box(
            version=ver,
            box_type=(flags & 0b11),
            collision_types=(flags & 0xFF0),
            name=read_long_fixed_string(io_stream),
            color=RGBA.read(io_stream),
            center=read_vector(io_stream),
            extend=read_vector(io_stream))

    @staticmethod
    def size_in_bytes():
        return 68

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_BOX, self.size_in_bytes())

        # TODO: fix version writing
        # self.version.write(io_stream)
        write_long(io_stream, 9)

        write_ulong(io_stream, (self.collision_types & 0xFF) | (self.box_type & 0b11))
        write_long_fixed_string(io_stream, self.name)
        self.color.write(io_stream)
        write_vector(io_stream, self.center)
        write_vector(io_stream, self.extend)


#######################################################################################
# Texture
#######################################################################################


W3D_CHUNK_TEXTURE_INFO = 0x00000033


class TextureInfo(Struct):
    attributes = 0
    animation_type = 0
    frame_count = 0
    frame_rate = 0.0

    @staticmethod
    def read(io_stream):
        return TextureInfo(
            attributes=read_ushort(io_stream),
            animation_type=read_ushort(io_stream),
            frame_count=read_ulong(io_stream),
            frame_rate=read_float(io_stream))

    @staticmethod
    def size_in_bytes():
        return 12

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_TEXTURE_INFO, self.size_in_bytes())
        write_ushort(io_stream, self.attributes)
        write_ushort(io_stream, self.animation_type)
        write_ulong(io_stream, self.frame_count)
        write_float(io_stream, self.frame_rate)


W3D_CHUNK_TEXTURE = 0x00000031
W3D_CHUNK_TEXTURE_NAME = 0x00000032


class Texture(Struct):
    name = ""
    texture_info = None

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = Texture(textureInfo=None)

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, _) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_TEXTURE_NAME:
                result.name = read_string(io_stream)
            elif chunk_type == W3D_CHUNK_TEXTURE_INFO:
                result.texture_info = TextureInfo.read(io_stream)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size_in_bytes(self):
        size = HEAD + string_size(self.name)
        if self.texture_info is not None:
            size += HEAD + self.texture_info.size_in_bytes()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_TEXTURE,
                         self.size_in_bytes(), has_sub_chunks=True)
        write_chunk_head(io_stream, W3D_CHUNK_TEXTURE_NAME, string_size(self.name))
        write_string(io_stream, self.name)

        if self.texture_info is not None:
            write_chunk_head(io_stream, W3D_CHUNK_TEXTURE_INFO,
                             self.texture_info.size_in_bytes())
            self.texture_info.write(io_stream)


#######################################################################################
# Material
#######################################################################################


W3D_CHUNK_TEXTURE_STAGE = 0x00000048
W3D_CHUNK_TEXTURE_IDS = 0x00000049
W3D_CHUNK_STAGE_TEXCOORDS = 0x0000004A
W3D_CHUNK_PER_FACE_TEXCOORD_IDS = 0x0000004B


class TextureStage(Struct):
    tx_ids = []
    per_face_tx_coords = []
    tx_coords = []

    @staticmethod
    def read(io_stream, chunk_end):
        result = TextureStage(
            txIds=[],
            per_face_tx_coords=[],
            tx_coords=[])

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_TEXTURE_IDS:
                result.tx_ids = read_array(io_stream, subchunk_end, read_long)
            elif chunk_type == W3D_CHUNK_STAGE_TEXCOORDS:
                result.tx_coords = read_array(io_stream, subchunk_end, read_vector2)
            elif chunk_type == W3D_CHUNK_PER_FACE_TEXCOORD_IDS:
                result.per_face_tx_coords = read_array(
                    io_stream, subchunk_end, read_vector)
            else:
                skip_unknown_chunk(None, io_stream, chunk_type, chunk_size)
        return result

    def tx_ids_size(self):
        return len(self.tx_ids) * 4

    def per_face_tx_coords_size(self):
        return len(self.per_face_tx_coords) * 12

    def tx_coords_size(self):
        return len(self.tx_coords) * 8

    def size_in_bytes(self):
        size = 0
        if self.tx_ids:
            size += HEAD + self.tx_ids_size()
        if self.tx_coords:
            size += HEAD + self.tx_coords_size()
        if self.per_face_tx_coords:
            size += HEAD + self.per_face_tx_coords_size()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_TEXTURE_STAGE,
                         self.size_in_bytes(), has_sub_chunks=True)

        if self.tx_ids:
            write_chunk_head(io_stream, W3D_CHUNK_TEXTURE_IDS, self.tx_ids_size())
            write_array(io_stream, self.tx_ids, write_long)

        if self.tx_coords:
            write_chunk_head(io_stream, W3D_CHUNK_STAGE_TEXCOORDS,
                             self.tx_coords_size())
            write_array(io_stream, self.tx_coords, write_vector2)

        if self.per_face_tx_coords:
            write_chunk_head(io_stream, W3D_CHUNK_PER_FACE_TEXCOORD_IDS,
                             self.per_face_tx_coords_size())
            write_array(io_stream, self.per_face_tx_coords, write_vector)


W3D_CHUNK_MATERIAL_PASS = 0x00000038
W3D_CHUNK_VERTEX_MATERIAL_IDS = 0x00000039
W3D_CHUNK_SHADER_IDS = 0x0000003A
W3D_CHUNK_DCG = 0x0000003B
W3D_CHUNK_DIG = 0x0000003C
W3D_CHUNK_SCG = 0x0000003E
W3D_CHUNK_SHADER_MATERIAL_ID = 0x3F


class MaterialPass(Struct):
    vertex_material_ids = []
    shader_ids = []
    dcg = []
    dig = []
    scg = []
    shader_material_ids = []
    tx_stages = []
    tx_coords = []

    @staticmethod
    def read(io_stream, chunk_end):
        result = MaterialPass(
            vertex_material_ids=[],
            shader_ids=[],
            dcg=[],
            dig=[],
            scg=[],
            shader_material_ids=[],
            tx_stages=[],
            tx_coords=[])

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_VERTEX_MATERIAL_IDS:
                result.vertex_material_ids = read_array(
                    io_stream, subchunk_end, read_ulong)
            elif chunk_type == W3D_CHUNK_SHADER_IDS:
                result.shader_ids = read_array(io_stream, subchunk_end, read_ulong)
            elif chunk_type == W3D_CHUNK_DCG:
                result.dcg = read_array(io_stream, subchunk_end, RGBA.read)
            elif chunk_type == W3D_CHUNK_DIG:
                result.dig = read_array(io_stream, subchunk_end, RGBA.read)
            elif chunk_type == W3D_CHUNK_SCG:
                result.scg = read_array(io_stream, subchunk_end, RGBA.read)
            elif chunk_type == W3D_CHUNK_SHADER_MATERIAL_ID:
                result.shader_material_ids = read_array(
                    io_stream, subchunk_end, read_ulong)
            elif chunk_type == W3D_CHUNK_TEXTURE_STAGE:
                result.tx_stages.append(
                    TextureStage.read(io_stream, subchunk_end))
            elif chunk_type == W3D_CHUNK_STAGE_TEXCOORDS:
                result.tx_coords = read_array(io_stream, subchunk_end, read_vector2)
            else:
                skip_unknown_chunk(None, io_stream, chunk_type, chunk_size)
        return result

    def vertex_material_ids_size(self):
        return len(self.vertex_material_ids) * 4

    def shader_ids_size(self):
        return len(self.shader_ids) * 4

    def dcg_size(self):
        return len(self.dcg) * 4

    def dig_size(self):
        return len(self.dig) * 4

    def scg_size(self):
        return len(self.scg) * 4

    def shader_material_ids_size(self):
        return len(self.shader_material_ids) * 4

    def tx_stages_size(self):
        size = 0
        for stage in self.tx_stages:
            size += HEAD + stage.size_in_bytes()
        return size

    def tx_coords_size(self):
        return len(self.tx_coords) * 8

    def size_in_bytes(self):
        size = 0
        if self.vertex_material_ids:
            size = HEAD + self.vertex_material_ids_size()
        if self.shader_ids:
            size += HEAD + self.shader_ids_size()
        if self.dcg:
            size += HEAD + self.dcg_size()
        if self.dig:
            size += HEAD + self.dig_size()
        if self.scg:
            size += HEAD + self.scg_size()
        if self.shader_material_ids:
            size += HEAD + self.shader_material_ids_size()
        if self.tx_stages:
            size += self.tx_stages_size()
        if self.tx_coords:
            size += HEAD + self.tx_coords_size()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_MATERIAL_PASS,
                         self.size_in_bytes(), has_sub_chunks=True)

        if self.vertex_material_ids:
            write_chunk_head(io_stream, W3D_CHUNK_VERTEX_MATERIAL_IDS,
                             self.vertex_material_ids_size())
            write_array(io_stream, self.vertex_material_ids, write_ulong)
        if self.shader_ids:
            write_chunk_head(io_stream, W3D_CHUNK_SHADER_IDS, self.shader_ids_size())
            write_array(io_stream, self.shader_ids, write_ulong)
        if self.dcg:
            write_chunk_head(io_stream, W3D_CHUNK_DCG, self.dcg_size())
            for dat in self.dcg:
                dat.write(io_stream)
        if self.dig:
            write_chunk_head(io_stream, W3D_CHUNK_DIG, self.dig_size())
            for dat in self.dig:
                dat.write(io_stream)
        if self.scg:
            write_chunk_head(io_stream, W3D_CHUNK_SCG, self.scg_size())
            for dat in self.scg:
                dat.write(io_stream)
        if self.shader_material_ids:
            write_chunk_head(io_stream, W3D_CHUNK_SHADER_MATERIAL_ID,
                             self.shader_material_ids_size())
            write_array(io_stream, self.shader_material_ids, write_ulong)
        if self.tx_stages:
            for tx_stage in self.tx_stages:
                tx_stage.write(io_stream)
        if self.tx_coords:
            write_chunk_head(io_stream, W3D_CHUNK_STAGE_TEXCOORDS,
                             self.tx_coords_size())
            write_array(io_stream, self.tx_coords, write_vector2)


W3D_CHUNK_MATERIAL_INFO = 0x00000028


class MaterialInfo(Struct):
    pass_count = 1
    vert_matl_count = 0
    shader_count = 0
    texture_count = 0

    @staticmethod
    def read(io_stream):
        return MaterialInfo(
            pass_count=read_ulong(io_stream),
            vert_matl_count=read_ulong(io_stream),
            shader_count=read_ulong(io_stream),
            texture_count=read_ulong(io_stream))

    @staticmethod
    def size_in_bytes():
        return 16

    def write(self, io_stream):
        write_ulong(io_stream, self.pass_count)
        write_ulong(io_stream, self.vert_matl_count)
        write_ulong(io_stream, self.shader_count)
        write_ulong(io_stream, self.texture_count)


W3D_CHUNK_VERTEX_MATERIAL_INFO = 0x0000002D


class VertexMaterialInfo(Struct):
    attributes = 0
    ambient = RGBA()  # alpha is only padding in this and below
    diffuse = RGBA()
    specular = RGBA()
    emissive = RGBA()
    shininess = 0.0
    opacity = 0.0
    translucency = 0.0

    @staticmethod
    def read(io_stream):
        return VertexMaterialInfo(
            attributes=read_long(io_stream),
            ambient=RGBA.read(io_stream),
            diffuse=RGBA.read(io_stream),
            specular=RGBA.read(io_stream),
            emissive=RGBA.read(io_stream),
            shininess=read_float(io_stream),
            opacity=read_float(io_stream),
            translucency=read_float(io_stream))

    @staticmethod
    def size_in_bytes():
        return 32

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_VERTEX_MATERIAL_INFO,
                         self.size_in_bytes())
        write_long(io_stream, self.attributes)
        self.ambient.write(io_stream)
        self.diffuse.write(io_stream)
        self.specular.write(io_stream)
        self.emissive.write(io_stream)
        write_float(io_stream, self.shininess)
        write_float(io_stream, self.opacity)
        write_float(io_stream, self.translucency)


W3D_CHUNK_VERTEX_MATERIAL = 0x0000002B
W3D_CHUNK_VERTEX_MATERIAL_NAME = 0x0000002C
W3D_CHUNK_VERTEX_MAPPER_ARGS0 = 0x0000002E
W3D_CHUNK_VERTEX_MAPPER_ARGS1 = 0x0000002F


class VertexMaterial(Struct):
    vm_name = ""
    vm_info = VertexMaterialInfo()
    vm_args_0 = ""
    vm_args_1 = ""

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = VertexMaterial()

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, _) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_VERTEX_MATERIAL_NAME:
                result.vm_name = read_string(io_stream)
            elif chunk_type == W3D_CHUNK_VERTEX_MATERIAL_INFO:
                result.vm_info = VertexMaterialInfo.read(io_stream)
            elif chunk_type == W3D_CHUNK_VERTEX_MAPPER_ARGS0:
                result.vm_args_0 = read_string(io_stream)
            elif chunk_type == W3D_CHUNK_VERTEX_MAPPER_ARGS1:
                result.vm_args_1 = read_string(io_stream)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size_in_bytes(self):
        size = HEAD + string_size(self.vm_name)
        size += HEAD + self.vm_info.size_in_bytes()
        size += HEAD + string_size(self.vm_args_0)
        size += HEAD + string_size(self.vm_args_1)
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_VERTEX_MATERIAL,
                         self.size_in_bytes(), has_sub_chunks=True)
        write_chunk_head(io_stream, W3D_CHUNK_VERTEX_MATERIAL_NAME,
                         string_size(self.vm_name))
        write_string(io_stream, self.vm_name)
        self.vm_info.write(io_stream)
        write_chunk_head(io_stream, W3D_CHUNK_VERTEX_MAPPER_ARGS0,
                         string_size(self.vm_args_0))
        write_string(io_stream, self.vm_args_0)
        write_chunk_head(io_stream, W3D_CHUNK_VERTEX_MAPPER_ARGS1,
                         string_size(self.vm_args_1))
        write_string(io_stream, self.vm_args_1)


#######################################################################################
# Vertices
#######################################################################################


class MeshVertexInfluence(Struct):
    bone_idx = 0
    xtra_idx = 0
    bone_inf = 0.0
    xtra_inf = 0.0

    @staticmethod
    def read(io_stream):
        return MeshVertexInfluence(
            bone_idx=read_ushort(io_stream),
            xtra_idx=read_ushort(io_stream),
            bone_inf=read_ushort(io_stream)/100,
            xtra_inf=read_ushort(io_stream)/100)

    @staticmethod
    def size_in_bytes():
        return 8

    def write(self, io_stream):
        write_ushort(io_stream, self.bone_idx)
        write_ushort(io_stream, self.xtra_idx)
        write_ushort(io_stream, int(self.bone_inf * 100))
        write_ushort(io_stream, int(self.xtra_inf * 100))


#######################################################################################
# Triangle
#######################################################################################


class MeshTriangle(Struct):
    vert_ids = []
    surface_type = 13
    normal = Vector((0.0, 0.0, 0.0))
    distance = 0.0

    @staticmethod
    def read(io_stream):
        return MeshTriangle(
            vert_ids=(read_ulong(io_stream), read_ulong(io_stream), read_ulong(io_stream)),
            surface_type=read_ulong(io_stream),
            normal=read_vector(io_stream),
            distance=read_float(io_stream))

    @staticmethod
    def size_in_bytes():
        return 32

    def write(self, io_stream):
        write_ulong(io_stream, self.vert_ids[0])
        write_ulong(io_stream, self.vert_ids[1])
        write_ulong(io_stream, self.vert_ids[2])
        write_ulong(io_stream, self.surface_type)
        write_vector(io_stream, self.normal)
        write_float(io_stream, self.distance)


#######################################################################################
# Shader
#######################################################################################


class MeshShader(Struct):
    depth_compare = 3
    depth_mask = 1
    color_mask = 0
    dest_blend = 0
    fog_func = 2
    pri_gradient = 1
    sec_gradient = 0
    src_blend = 1
    texturing = 1
    detail_color_func = 0
    detail_alpha_func = 0
    shader_preset = 2
    alpha_test = 0
    post_detail_color_func = 0
    post_detail_alpha_func = 0
    pad = 2

    @staticmethod
    def read(io_stream):
        return MeshShader(
            depth_compare=read_ubyte(io_stream),
            depth_mask=read_ubyte(io_stream),
            color_mask=read_ubyte(io_stream),
            dest_blend=read_ubyte(io_stream),
            fog_func=read_ubyte(io_stream),
            pri_gradient=read_ubyte(io_stream),
            sec_gradient=read_ubyte(io_stream),
            src_blend=read_ubyte(io_stream),
            texturing=read_ubyte(io_stream),
            detail_color_func=read_ubyte(io_stream),
            detail_alpha_func=read_ubyte(io_stream),
            shader_preset=read_ubyte(io_stream),
            alpha_test=read_ubyte(io_stream),
            post_detail_color_func=read_ubyte(io_stream),
            post_detail_alpha_func=read_ubyte(io_stream),
            pad=read_ubyte(io_stream))

    @staticmethod
    def size_in_bytes():
        return 16

    def write(self, io_stream):
        write_ubyte(io_stream, self.depth_compare)
        write_ubyte(io_stream, self.depth_mask)
        write_ubyte(io_stream, self.color_mask)
        write_ubyte(io_stream, self.dest_blend)
        write_ubyte(io_stream, self.fog_func)
        write_ubyte(io_stream, self.pri_gradient)
        write_ubyte(io_stream, self.sec_gradient)
        write_ubyte(io_stream, self.src_blend)
        write_ubyte(io_stream, self.texturing)
        write_ubyte(io_stream, self.detail_color_func)
        write_ubyte(io_stream, self.detail_alpha_func)
        write_ubyte(io_stream, self.shader_preset)
        write_ubyte(io_stream, self.alpha_test)
        write_ubyte(io_stream, self.post_detail_color_func)
        write_ubyte(io_stream, self.post_detail_alpha_func)
        write_ubyte(io_stream, self.pad)


#######################################################################################
# Shader Material
#######################################################################################


W3D_CHUNK_SHADER_MATERIAL_HEADER = 0x52


class ShaderMaterialHeader(Struct):
    number = 0
    type_name = ""
    reserved = 0

    @staticmethod
    def read(io_stream):
        return ShaderMaterialHeader(
            number=read_ubyte(io_stream),
            type_name=read_long_fixed_string(io_stream),
            reserved=read_long(io_stream))

    @staticmethod
    def size_in_bytes():
        return 37

    def write(self, io_stream):
        write_chunk_head(
            io_stream, W3D_CHUNK_SHADER_MATERIAL_HEADER, self.size_in_bytes())
        write_ubyte(io_stream, self.number)
        write_long_fixed_string(io_stream, self.type_name)
        write_long(io_stream, self.reserved)


W3D_CHUNK_SHADER_MATERIAL_PROPERTY = 0x53


class ShaderMaterialProperty(Struct):
    type = 0
    name = ""
    num_chars = 0
    value = None

    @staticmethod
    def read(io_stream):
        result = ShaderMaterialProperty(
            type=read_long(io_stream),
            num_chars=read_long(io_stream),
            name=read_string(io_stream))

        if result.type == 1:
            read_long(io_stream)  # num available chars
            result.value = read_string(io_stream)
        elif result.type == 2:
            result.value = read_float(io_stream)
        elif result.type == 4:
            result.value = read_vector(io_stream)
        elif result.type == 5:
            result.value = RGBA.read_f(io_stream)
        elif result.type == 6:
            result.value = read_long(io_stream)
        elif result.type == 7:
            result.value = read_ubyte(io_stream)
        return result

    def size_in_bytes(self):
        size = 8 + string_size(self.name)
        if self.type == 1:
            size += 4 + string_size(self.value)
        elif self.type == 2:
            size += 4
        elif self.type == 4:
            size += 12
        elif self.type == 5:
            size += 16
        elif self.type == 6:
            size += 4
        elif self.type == 7:
            size += 1
        return size

    def write(self, io_stream):
        write_chunk_head(
            io_stream, W3D_CHUNK_SHADER_MATERIAL_PROPERTY, self.size_in_bytes())
        write_long(io_stream, self.type)
        write_long(io_stream, self.num_chars)
        write_string(io_stream, self.name)

        if self.type == 1:
            write_long(io_stream, string_size(self.value))
            write_string(io_stream, self.value)
        elif self.type == 2:
            write_float(io_stream, self.value)
        elif self.type == 4:
            write_vector(io_stream, self.value)
        elif self.type == 5:
            self.value.write_f(io_stream)
        elif self.type == 6:
            write_long(io_stream, self.value)
        elif self.type == 7:
            write_ubyte(io_stream, self.value)


W3D_CHUNK_SHADER_MATERIAL = 0x51


class ShaderMaterial(Struct):
    header = ShaderMaterialHeader()
    properties = []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = ShaderMaterial(
            properties=[])

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, _) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_SHADER_MATERIAL_HEADER:
                result.header = ShaderMaterialHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_SHADER_MATERIAL_PROPERTY:
                result.properties.append(ShaderMaterialProperty.read(io_stream))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        for prop in self.properties:
            size += HEAD + prop.size_in_bytes()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_SHADER_MATERIAL,
                         self.size_in_bytes(), has_sub_chunks=True)
        self.header.write(io_stream)
        for prop in self.properties:
            prop.write(io_stream)


#######################################################################################
# AABBTree (Axis-aligned-bounding-box-tree)
#######################################################################################


W3D_CHUNK_AABBTREE_HEADER = 0x00000091


class AABBTreeHeader(Struct):
    node_count = 0
    poly_count = 0

    @staticmethod
    def read(io_stream):
        result = AABBTreeHeader(
            node_count=read_ulong(io_stream),
            poyCount=read_ulong(io_stream))

        io_stream.read(24)  # padding
        return result

    @staticmethod
    def size_in_bytes():
        return 8

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_AABBTREE_HEADER, self.size_in_bytes())
        write_ulong(io_stream, self.node_count)
        write_ulong(io_stream, self.poly_count)


class AABBTreeNode(Struct):
    min = Vector((0.0, 0.0, 0.0))
    max = Vector((0.0, 0.0, 0.0))
    front_or_poly_0 = 0
    back_or_poly_count = 0

    @staticmethod
    def read(io_stream):
        return AABBTreeNode(
            min=read_vector(io_stream),
            max=read_vector(io_stream),
            front_or_poly_0=read_long(io_stream),
            back_or_poly_count=read_long(io_stream))

    @staticmethod
    def size_in_bytes():
        return 32

    def write(self, io_stream):
        write_vector(io_stream, self.min)
        write_vector(io_stream, self.max)
        write_long(io_stream, self.front_or_poly_0)
        write_long(io_stream, self.back_or_poly_count)


W3D_CHUNK_AABBTREE = 0x00000090
W3D_CHUNK_AABBTREE_POLYINDICES = 0x00000092
W3D_CHUNK_AABBTREE_NODES = 0x00000093


class MeshAABBTree(Struct):
    header = AABBTreeHeader()
    poly_indices = []
    nodes = []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = MeshAABBTree()

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_AABBTREE_HEADER:
                result.header = AABBTreeHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_AABBTREE_POLYINDICES:
                result.poly_indices = read_array(io_stream, subchunk_end, read_long)
            elif chunk_type == W3D_CHUNK_AABBTREE_NODES:
                result.nodes = read_array(io_stream, subchunk_end, AABBTreeNode.read)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def poly_indices_size(self):
        return len(self.poly_indices) * 4

    def nodes_size(self):
        size = 0
        for node in self.nodes:
            size += node.size_in_bytes()
        return size

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        if self.poly_indices:
            size += HEAD + self.poly_indices_size()
        if self.nodes:
            size += HEAD + self.nodes_size()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_AABBTREE,
                         self.size_in_bytes(), has_sub_chunks=True)
        self.header.write(io_stream)

        if self.poly_indices:
            write_chunk_head(io_stream, W3D_CHUNK_AABBTREE_POLYINDICES,
                             self.poly_indices_size())
            write_array(io_stream, self.poly_indices, write_long)
        if self.nodes:
            write_chunk_head(io_stream, W3D_CHUNK_AABBTREE_NODES, self.nodes_size())
            for node in self.nodes:
                node.write(io_stream)


#######################################################################################
# Mesh
#######################################################################################


W3D_CHUNK_MESH_HEADER = 0x0000001F


class MeshHeader(Struct):
    version = Version()
    attrs = 0
    mesh_name = ""
    container_name = ""
    face_count = 0
    vert_count = 0
    matl_count = 0
    damage_stage_count = 0
    sort_level = 0
    prelit_version = 0
    future_count = 0
    vert_channel_flags = 3
    face_channel_falgs = 1
    min_corner = Vector((0.0, 0.0, 0.0))
    max_corner = Vector((0.0, 0.0, 0.0))
    sph_center = Vector((0.0, 0.0, 0.0))
    sph_radius = 0.0

    @staticmethod
    def read(io_stream):
        return MeshHeader(
            version=Version.read(io_stream),
            attrs=read_ulong(io_stream),
            mesh_name=read_fixed_string(io_stream),
            container_name=read_fixed_string(io_stream),
            face_count=read_ulong(io_stream),
            vert_count=read_ulong(io_stream),
            matl_count=read_ulong(io_stream),
            damage_stage_count=read_ulong(io_stream),
            sort_level=read_ulong(io_stream),
            prelit_version=read_ulong(io_stream),
            future_count=read_ulong(io_stream),
            vert_channel_flags=read_ulong(io_stream),
            face_channel_falgs=read_ulong(io_stream),
            # bounding volumes
            min_corner=read_vector(io_stream),
            max_corner=read_vector(io_stream),
            sph_center=read_vector(io_stream),
            sph_radius=read_float(io_stream))

    @staticmethod
    def size_in_bytes():
        return 116

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_MESH_HEADER, self.size_in_bytes())
        self.version.write(io_stream)
        write_ulong(io_stream, self.attrs)
        write_fixed_string(io_stream, self.mesh_name)
        write_fixed_string(io_stream, self.container_name)
        write_ulong(io_stream, self.face_count)
        write_ulong(io_stream, self.vert_count)
        write_ulong(io_stream, self.matl_count)
        write_ulong(io_stream, self.damage_stage_count)
        write_ulong(io_stream, self.sort_level)
        write_ulong(io_stream, self.prelit_version)
        write_ulong(io_stream, self.future_count)
        write_ulong(io_stream, self.vert_channel_flags)
        write_ulong(io_stream, self.face_channel_falgs)
        write_vector(io_stream, self.min_corner)
        write_vector(io_stream, self.max_corner)
        write_vector(io_stream, self.sph_center)
        write_float(io_stream, self.sph_radius)


W3D_CHUNK_MESH = 0x00000000
W3D_CHUNK_VERTICES = 0x00000002
W3D_CHUNK_VERTICES_2 = 0xC00
W3D_CHUNK_VERTEX_NORMALS = 0x00000003
W3D_CHUNK_NORMALS_2 = 0xC01
W3D_CHUNK_MESH_USER_TEXT = 0x0000000C
W3D_CHUNK_VERTEX_INFLUENCES = 0x0000000E
W3D_CHUNK_TRIANGLES = 0x00000020
W3D_CHUNK_VERTEX_SHADE_INDICES = 0x00000022
W3D_CHUNK_SHADERS = 0x00000029
W3D_CHUNK_VERTEX_MATERIALS = 0x0000002A
W3D_CHUNK_TEXTURES = 0x00000030
W3D_CHUNK_SHADER_MATERIALS = 0x50
W3D_CHUNK_TANGENTS = 0x60
W3D_CHUNK_BITANGENTS = 0x61


class Mesh(Struct):
    header = MeshHeader()
    user_text = ""
    verts = []
    normals = []
    vert_infs = []
    triangles = []
    shade_ids = []
    mat_info = None
    shaders = []
    vert_materials = []
    textures = []
    shader_materials = []
    material_pass = None
    aabbtree = None

    def read(self, io_stream, chunk_end):
        result = Mesh(
            verts=[],
            normals=[],
            vert_infs=[],
            triangles=[],
            shade_ids=[],
            shaders=[],
            vert_materials=[],
            textures=[],
            shader_materials=[])

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_VERTICES:
                result.verts = read_array(io_stream, subchunk_end, read_vector)
            elif chunk_type == W3D_CHUNK_VERTICES_2:
                #print("-> vertices 2 chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_VERTEX_NORMALS:
                result.normals = read_array(io_stream, subchunk_end, read_vector)
            elif chunk_type == W3D_CHUNK_NORMALS_2:
                #print("-> normals 2 chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_MESH_USER_TEXT:
                result.user_text = read_string(io_stream)
            elif chunk_type == W3D_CHUNK_VERTEX_INFLUENCES:
                result.vert_infs = read_array(
                    io_stream, subchunk_end, MeshVertexInfluence.read)
            elif chunk_type == W3D_CHUNK_MESH_HEADER:
                result.header = MeshHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_TRIANGLES:
                result.triangles = read_array(
                    io_stream, subchunk_end, MeshTriangle.read)
            elif chunk_type == W3D_CHUNK_VERTEX_SHADE_INDICES:
                result.shade_ids = read_array(io_stream, subchunk_end, read_long)
            elif chunk_type == W3D_CHUNK_MATERIAL_INFO:
                result.mat_info = MaterialInfo.read(io_stream)
            elif chunk_type == W3D_CHUNK_SHADERS:
                result.shaders = read_array(io_stream, subchunk_end, MeshShader.read)
            elif chunk_type == W3D_CHUNK_VERTEX_MATERIALS:
                result.vert_materials = read_chunk_array(
                    self, io_stream, subchunk_end, W3D_CHUNK_VERTEX_MATERIAL, VertexMaterial.read)
            elif chunk_type == W3D_CHUNK_TEXTURES:
                result.textures = read_chunk_array(
                    self, io_stream, subchunk_end, W3D_CHUNK_TEXTURE, Texture.read)
            elif chunk_type == W3D_CHUNK_MATERIAL_PASS:
                result.material_pass = MaterialPass.read(
                    io_stream, subchunk_end)
            elif chunk_type == W3D_CHUNK_SHADER_MATERIALS:
                result.shader_materials = read_chunk_array(
                    self, io_stream, subchunk_end, W3D_CHUNK_SHADER_MATERIAL, ShaderMaterial.read)
            elif chunk_type == W3D_CHUNK_TANGENTS:
                #print("-> tangents chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_BITANGENTS:
                #print("-> bitangents chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_AABBTREE:
                result.aabbtree = MeshAABBTree.read(self, io_stream, subchunk_end)
            elif chunk_type == W3D_CHUNK_PRELIT_UNLIT:
                print("-> prelit unlit chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_PRELIT_VERTEX:
                print("-> prelit vertex chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_PASS:
                print("-> prelit lightmap multi pass chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_TEXTURE:
                print("-> prelit lightmap multi texture chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_DEFORM:
                print("-> deform chunk is not supported")
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_PS2_SHADERS:
                print("-> ps2 shaders chunk is not supported")
                io_stream.seek(chunk_size, 1)
            else:
                skip_unknown_chunk(self, io_stream, chunk_type, chunk_size)
        return result

    def verts_size(self):
        return len(self.verts) * 12

    def normals_size(self):
        return len(self.normals) * 12

    def tris_size(self):
        size = 0
        for triangle in self.triangles:
            size += triangle.size_in_bytes()
        return size

    def vert_infs_size(self):
        size = 0
        for inf in self.vert_infs:
            size += inf.size_in_bytes()
        return size

    def shaders_size(self):
        size = 0
        for shader in self.shaders:
            size += shader.size_in_bytes()
        return size

    def textures_size(self):
        size = 0
        for texture in self.textures:
            size += HEAD + texture.size_in_bytes()
        return size

    def shade_ids_size(self):
        return len(self.shade_ids) * 4

    def shader_materials_size(self):
        size = 0
        for shaderMat in self.shader_materials:
            size += HEAD + shaderMat.size_in_bytes()
        return size

    def vert_materials_size(self):
        size = 0
        for vertMat in self.vert_materials:
            size += HEAD + vertMat.size_in_bytes()
        return size

    def size_in_bytes(self):
        size = HEAD + self.header.size_in_bytes()
        size += HEAD + self.verts_size()
        size += HEAD + self.normals_size()
        size += HEAD + self.tris_size()
        if self.vert_infs:
            size += HEAD + self.vert_infs_size()
        if self.shaders:
            size += HEAD + self.shaders_size()
        if self.textures:
            size += HEAD + self.textures_size()
        if self.shade_ids:
            size += HEAD + self.shade_ids_size()
        if self.shader_materials:
            size += HEAD + self.shader_materials_size()
        if self.mat_info is not None:
            size += HEAD + self.mat_info.size_in_bytes()
        if self.vert_materials:
            size += HEAD + self.vert_materials_size()
        if self.material_pass is not None:
            size += HEAD + self.material_pass.size_in_bytes()
        if self.aabbtree is not None:
            size += HEAD + self.aabbtree.size_in_bytes()
        return size

    def write(self, io_stream):
        write_chunk_head(io_stream, W3D_CHUNK_MESH,
                         self.size_in_bytes(), has_sub_chunks=True)
        self.header.write(io_stream)

        write_chunk_head(io_stream, W3D_CHUNK_VERTICES, self.verts_size())
        for vec in self.verts:
            write_vector(io_stream, vec)
        #write_array(io_stream, self.verts, write_vector)

        write_chunk_head(io_stream, W3D_CHUNK_VERTEX_NORMALS, self.normals_size())
        for nor in self.normals:
            write_vector(io_stream, nor)
        #write_array(io_stream, self.normals, write_vector)

        write_chunk_head(io_stream, W3D_CHUNK_TRIANGLES, self.tris_size())
        for tri in self.triangles:
            tri.write(io_stream)

        if self.vert_infs:
            write_chunk_head(io_stream, W3D_CHUNK_VERTEX_INFLUENCES,
                             self.vert_infs_size())
            for inf in self.vert_infs:
                inf.write(io_stream)

        if self.shaders:
            write_chunk_head(io_stream, W3D_CHUNK_SHADERS, self.shaders_size())
            for shader in self.shaders:
                shader.write(io_stream)

        if self.textures:
            write_chunk_head(io_stream, W3D_CHUNK_TEXTURES,
                             self.textures_size(), has_sub_chunks=True)
            for texture in self.textures:
                texture.write(io_stream)

        if self.shade_ids:
            write_chunk_head(
                io_stream, W3D_CHUNK_VERTEX_SHADE_INDICES, self.shade_ids_size())
            write_array(io_stream, self.shade_ids, write_long)

        if self.shader_materials:
            write_chunk_head(io_stream, W3D_CHUNK_SHADER_MATERIALS,
                             self.shader_materials_size(), has_sub_chunks=True)
            for shaderMat in self.shader_materials:
                shaderMat.write(io_stream)

        if self.mat_info is not None:
            write_chunk_head(io_stream, W3D_CHUNK_MATERIAL_INFO,
                             self.mat_info.size_in_bytes())
            self.mat_info.write(io_stream)

        if self.vert_materials:
            write_chunk_head(io_stream, W3D_CHUNK_VERTEX_MATERIALS,
                             self.vert_materials_size(), has_sub_chunks=True)
            for vertMat in self.vert_materials:
                vertMat.write(io_stream)

        if self.material_pass is not None:
            self.material_pass.write(io_stream)

        if self.aabbtree is not None:
            self.aabbtree.write(io_stream)


#######################################################################################
# Unsupported
#######################################################################################

# inside mesh
W3D_CHUNK_PRELIT_UNLIT = 0x00000023
W3D_CHUNK_PRELIT_VERTEX = 0x00000024
W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_PASS = 0x00000025
W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_TEXTURE = 0x00000026

W3D_CHUNK_DEFORM = 0x00000058
W3D_CHUNK_PS2_SHADERS = 0x00000080

# inside w3d io_stream
W3D_CHUNK_MORPH_ANIMATION = 0x000002C0
W3D_CHUNK_HMODEL = 0x00000300
W3D_CHUNK_LODMODEL = 0x00000400
W3D_CHUNK_COLLECTION = 0x00000420
W3D_CHUNK_POINTS = 0x00000440
W3D_CHUNK_LIGHT = 0x00000460
W3D_CHUNK_EMITTER = 0x00000500
W3D_CHUNK_AGGREGATE = 0x00000600
W3D_CHUNK_NULL_OBJECT = 0x00000750
W3D_CHUNK_LIGHTSCAPE = 0x00000800
W3D_CHUNK_DAZZLE = 0x00000900
W3D_CHUNK_SOUNDROBJ = 0x00000A00
