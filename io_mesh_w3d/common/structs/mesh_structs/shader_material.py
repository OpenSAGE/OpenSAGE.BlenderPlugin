# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector
from io_mesh_w3d.w3d.utils.helpers import *
from io_mesh_w3d.w3x.io_xml import *

W3D_CHUNK_SHADER_MATERIAL_HEADER = 0x52

W3D_NORMTYPE_TEXTURE = 1
W3D_NORMTYPE_BUMP = 2
W3D_NORMTYPE_COLORS = 5
W3D_NORMTYPE_ALPHA = 7


class ShaderMaterialHeader:
    def __init__(self, version=1, type_name='', technique=0):
        self.version = version
        self.type_name = type_name
        self.technique = technique

    @staticmethod
    def read(io_stream):
        return ShaderMaterialHeader(
            version=read_ubyte(io_stream),
            type_name=read_long_fixed_string(io_stream),
            technique=read_long(io_stream))

    @staticmethod
    def size(include_head=True):
        return const_size(37, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_SHADER_MATERIAL_HEADER, io_stream, self.size(False))
        write_ubyte(self.version, io_stream)
        write_long_fixed_string(self.type_name, io_stream)
        write_long(self.technique, io_stream)


W3D_CHUNK_SHADER_MATERIAL_PROPERTY = 0x53

STRING_PROPERTY = 1
FLOAT_PROPERTY = 2
VEC2_PROPERTY = 3
VEC3_PROPERTY = 4
VEC4_PROPERTY = 5
LONG_PROPERTY = 6
BOOL_PROPERTY = 7


class ShaderMaterialProperty:
    def __init__(self, type=0, name='', value=Vector((1.0, 1.0, 1.0, 1.0))):
        self.type = type
        self.name = name
        self.value = value

    def to_rgb(self):
        return self.value.x, self.value.y, self.value.z

    def to_rgba(self):
        if len(self.value) > 3:
            return self.value.x, self.value.y, self.value.z, self.value.w 
        elif len(self.value) == 3:
            return self.value.x, self.value.y, self.value.z, 1 
        else:
            return 1,1,1,1

    @staticmethod
    def read(context, io_stream):
        prop_type = read_long(io_stream)
        read_long(io_stream)  # num chars
        name = read_string(io_stream)
        result = ShaderMaterialProperty(
            type=prop_type,
            name=name,
            value=Vector((1.0, 1.0, 1.0, 1.0)))

        if result.type == STRING_PROPERTY:
            read_long(io_stream)  # num chars
            result.value = read_string(io_stream)
        elif result.type == FLOAT_PROPERTY:
            result.value = read_float(io_stream)
        elif result.type == VEC2_PROPERTY:
            result.value = read_vector2(io_stream)
        elif result.type == VEC4_PROPERTY:
            result.value = read_vector4(io_stream)
        elif result.type == LONG_PROPERTY:
            result.value = read_long(io_stream)
        elif result.type == BOOL_PROPERTY:
            result.value = bool(read_ubyte(io_stream))
        else:
            context.warning(f'unknown property type \'{result.type}\' in shader material')
        return result

    def size(self, include_head=True):
        size = const_size(8, include_head)
        size += len(self.name) + 1
        if self.type == STRING_PROPERTY:
            size += 4 + len(self.value) + 1
        elif self.type == FLOAT_PROPERTY:
            size += 4
        elif self.type == VEC2_PROPERTY:
            size += 8
        elif self.type == VEC3_PROPERTY:
            size += 12
        elif self.type == VEC4_PROPERTY:
            size += 16
        elif self.type == LONG_PROPERTY:
            size += 4
        else:
            size += 1
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_SHADER_MATERIAL_PROPERTY, io_stream, self.size(False))
        write_long(self.type, io_stream)
        write_long(len(self.name) + 1, io_stream)
        write_string(self.name, io_stream)

        if self.type == STRING_PROPERTY:
            write_long(len(self.value) + 1, io_stream)
            write_string(self.value, io_stream)
        elif self.type == FLOAT_PROPERTY:
            write_float(self.value, io_stream)
        elif self.type == VEC2_PROPERTY:
            write_vector2(self.value, io_stream)
        elif self.type == VEC3_PROPERTY:
            write_vector4(Vector((self.value.x, self.value.y, self.value.z ,1)), io_stream)
        elif self.type == VEC4_PROPERTY:
            write_vector4(self.value, io_stream)
        elif self.type == LONG_PROPERTY:
            write_long(self.value, io_stream)
        else:
            write_ubyte(self.value, io_stream)

    @staticmethod
    def parse(xml_constant):
        type_name = xml_constant.tag
        constant = ShaderMaterialProperty(
            name=xml_constant.get('Name'),
            value=Vector((1.0, 1.0, 1.0, 1.0)))

        values = []
        for xml_value in xml_constant.findall('Value'):
            values.append(xml_value.text)

        if type_name == 'Float':
            if len(values) == 1:
                constant.type = FLOAT_PROPERTY
                constant.value = get_float(values[0])
            if len(values) > 1:
                constant.type = VEC2_PROPERTY
                constant.value.x = get_float(values[0])
                constant.value.y = get_float(values[1])
            if len(values) > 2:
                constant.type = VEC3_PROPERTY
                constant.value.z = get_float(values[2])
            if len(values) == 4:
                constant.type = VEC4_PROPERTY
                constant.value.w = get_float(values[3])

        elif type_name == 'Int':
            constant.type = LONG_PROPERTY
            constant.value = int(values[0])
        elif type_name == 'Bool':
            constant.type = BOOL_PROPERTY
            constant.value = values[0] in ['True', 'true']
        else:
            constant.type = STRING_PROPERTY
            constant.value = values[0]

        return constant

    def create(self, parent):
        if self.type == 1:
            xml_constant = create_node(parent, 'Texture')
            xml_value = create_node(xml_constant, 'Value')
            xml_value.text = self.value

        elif self.type in [FLOAT_PROPERTY, VEC2_PROPERTY, VEC3_PROPERTY, VEC4_PROPERTY]:
            xml_constant = create_node(parent, 'Float')
            xml_value = create_node(xml_constant, 'Value')
            if self.type == FLOAT_PROPERTY:
                xml_value.text = format(self.value)
            else:
                xml_value.text = format(self.value.x)

            if self.type in [VEC2_PROPERTY, VEC3_PROPERTY, VEC4_PROPERTY]:
                xml_value = create_node(xml_constant, 'Value')
                xml_value.text = format(self.value.y)

            if self.type in [VEC3_PROPERTY, VEC4_PROPERTY]:
                xml_value = create_node(xml_constant, 'Value')
                xml_value.text = format(self.value.z)

            if self.type == VEC4_PROPERTY:
                xml_value = create_node(xml_constant, 'Value')
                xml_value.text = format(self.value.w)

        elif self.type == LONG_PROPERTY:
            xml_constant = create_node(parent, 'Int')
            xml_value = create_node(xml_constant, 'Value')
            xml_value.text = str(self.value)

        else:
            xml_constant = create_node(parent, 'Bool')
            xml_value = create_node(xml_constant, 'Value')
            xml_value.text = str(self.value).lower()

        xml_constant.set('Name', self.name)

W3D_CHUNK_SHADER_MATERIAL = 0x51


class ShaderMaterial:
    def __init__(self, header=None, properties=None):
        self.header = header
        self.properties = properties if properties is not None else []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = ShaderMaterial()

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, _) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_SHADER_MATERIAL_HEADER:
                result.header = ShaderMaterialHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_SHADER_MATERIAL_PROPERTY:
                result.properties.append(
                    ShaderMaterialProperty.read(context, io_stream))
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = const_size(0, include_head)
        size += self.header.size()
        for prop in self.properties:
            size += prop.size()
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_SHADER_MATERIAL, io_stream, self.size(False), has_sub_chunks=True)
        self.header.write(io_stream)
        write_list(self.properties, io_stream, ShaderMaterialProperty.write)

    @staticmethod
    def parse(xml_fx_shader):
        result = ShaderMaterial(
            header=ShaderMaterialHeader(
                type_name=xml_fx_shader.get('ShaderName'),
                technique=int(xml_fx_shader.get('TechniqueIndex', 0))))

        for constants in xml_fx_shader.findall('Constants'):
            for prop in constants:
                result.properties.append(ShaderMaterialProperty.parse(prop))
        return result

    def create(self, parent):
        fx_shader = create_node(parent, 'FXShader')
        fx_shader.set('ShaderName', self.header.type_name)
        fx_shader.set('TechniqueIndex', str(self.header.technique))

        constants = create_node(fx_shader, 'Constants')
        for prop in self.properties:
            prop.create(constants)
