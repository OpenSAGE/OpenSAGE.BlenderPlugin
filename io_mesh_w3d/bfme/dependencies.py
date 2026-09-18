# <pep8 compliant>
"""Work out which other assets a .w3d refers to.

The W3D importer resolves a model's skeleton and its textures by *name, relative
to the file it is importing*:

    <directory>/<hierarchy name>.w3d      the skeleton
    <directory>/<texture name>.<ext>      each texture

When assets come out of a .big archive there is no such directory, so whatever a
model needs has to be placed next to it before the importer goes looking. This
module reads the names out of a model without unpacking it into Blender.

Only the chunk headers are walked, the payloads are skipped, so scanning is
cheap even for large models.
"""

import struct

# a chunk is an 8 byte header (type, size) followed by its payload; the top bit of
# the size marks a chunk whose payload is itself a list of chunks
CHUNK_HEADER = struct.Struct('<II')
SUB_CHUNK_FLAG = 0x80000000
SIZE_MASK = 0x7FFFFFFF

STRING_LENGTH = 16

W3D_CHUNK_TEXTURE_NAME = 0x00000032
W3D_CHUNK_SHADER_MATERIAL_PROPERTY = 0x00000053
W3D_CHUNK_HLOD_HEADER = 0x00000701
W3D_CHUNK_ANIMATION_HEADER = 0x00000201
W3D_CHUNK_COMPRESSED_ANIMATION_HEADER = 0x00000281

STRING_PROPERTY = 1

# version(4) + lod_count(4) + model_name(16), then the hierarchy name
HLOD_HIERARCHY_OFFSET = 24
# version(4) + name(16), then the hierarchy name
ANIMATION_HIERARCHY_OFFSET = 20

# a model nesting deeper than this is corrupt rather than unusual
MAX_DEPTH = 16


def _fixed_string(data, offset):
    chunk = data[offset:offset + STRING_LENGTH]
    if len(chunk) < STRING_LENGTH:
        return ''
    return chunk.split(b'\x00', 1)[0].decode('latin-1', 'replace').strip()


def _terminated_string(data, start, end):
    return data[start:end].split(b'\x00', 1)[0].decode('latin-1', 'replace').strip()


def _shader_material_property(data, start, end):
    """The value of a string-valued shader material property, if it is one.

    Shader material models, which is most of what BfMe II and later ship, name
    their textures here rather than in a texture chunk:

        long type, long name length, name\\0, long value length, value\\0
    """
    if start + 8 > end:
        return None

    prop_type = struct.unpack_from('<i', data, start)[0]
    if prop_type != STRING_PROPERTY:
        return None

    name_end = data.find(b'\x00', start + 8, end)
    if name_end < 0:
        return None

    # skip the terminator and the value's own length field
    value_start = name_end + 1 + 4
    if value_start > end:
        return None

    return _terminated_string(data, value_start, end)


def _walk(data, start, end, texture_names, hierarchy_names, depth):
    if depth > MAX_DEPTH:
        return

    offset = start
    while offset + CHUNK_HEADER.size <= end:
        chunk_type, raw_size = CHUNK_HEADER.unpack_from(data, offset)
        size = raw_size & SIZE_MASK
        body = offset + CHUNK_HEADER.size
        body_end = body + size

        # a size that runs past the end means the file is truncated or not a w3d
        if size == 0 or body_end > end:
            return

        if chunk_type == W3D_CHUNK_TEXTURE_NAME:
            texture_names.add(_terminated_string(data, body, body_end))
        elif chunk_type == W3D_CHUNK_SHADER_MATERIAL_PROPERTY:
            value = _shader_material_property(data, body, body_end)
            if value:
                texture_names.add(value)
        elif chunk_type == W3D_CHUNK_HLOD_HEADER:
            hierarchy_names.add(_fixed_string(data, body + HLOD_HIERARCHY_OFFSET))
        elif chunk_type in (W3D_CHUNK_ANIMATION_HEADER, W3D_CHUNK_COMPRESSED_ANIMATION_HEADER):
            hierarchy_names.add(_fixed_string(data, body + ANIMATION_HIERARCHY_OFFSET))
        elif raw_size & SUB_CHUNK_FLAG:
            _walk(data, body, body_end, texture_names, hierarchy_names, depth + 1)

        offset = body_end


def _normalise(names):
    # texture names carry an extension, hierarchy names do not
    return {name.rsplit('.', 1)[0].lower() for name in names if name}


def referenced_names_by_kind(data):
    """(texture names, hierarchy names) a .w3d refers to, without extensions.

    Kept separate because a texture and an unrelated .w3d file can share a base
    name in the real asset libraries (a 'pfence01' texture next to an unrelated
    'pfence01.w3d' prop model, for instance); the asset index looks each kind up
    in its own bucket so one cannot shadow the other.
    """
    texture_names = set()
    hierarchy_names = set()
    try:
        _walk(data, 0, len(data), texture_names, hierarchy_names, 0)
    except (struct.error, IndexError):
        pass

    return _normalise(texture_names), _normalise(hierarchy_names)


def referenced_names(data):
    """Names of the skeleton and textures a .w3d refers to, without extensions.

    Returned in the same shape the asset index is keyed by, so they can be looked
    up directly.
    """
    texture_names, hierarchy_names = referenced_names_by_kind(data)
    return texture_names | hierarchy_names
