# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.common.structs.rgba import RGBA
from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3d.utils.helpers import *
from io_mesh_w3d.w3x.io_xml import *

W3D_CHUNK_SHADER_MATERIAL_HEADER = 0x52


class ShaderMaterialHeader(Struct):
    technique_index = 0
    type_name = ''
    reserved = 0  # what is this?

    @staticmethod
    def read(io_stream):
        return ShaderMaterialHeader(
            technique_index=read_ubyte(io_stream),
            type_name=read_long_fixed_string(io_stream),
            reserved=read_long(io_stream))

    @staticmethod
    def size(include_head=True):
        return const_size(37, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_SHADER_MATERIAL_HEADER,
                         io_stream, self.size(False))
        write_ubyte(self.technique_index, io_stream)
        write_long_fixed_string(self.type_name, io_stream)
        write_long(self.reserved, io_stream)


W3D_CHUNK_SHADER_MATERIAL_PROPERTY = 0x53


class ShaderMaterialProperty(Struct):
    type = 0
    name = ''
    value = Vector((1.0, 1.0, 1.0, 1.0))

    def to_rgb(self):
        return (self.value.x * 255, self.value.y * 255, self.value.z * 255)

    def to_rgba(self):
        return (self.value.x * 255, self.value.y * 255, self.value.z * 255, self.value.w * 255)

    @staticmethod
    def read(context, io_stream):
        type = read_long(io_stream)
        read_long(io_stream)  # num available chars
        name = read_string(io_stream)
        result = ShaderMaterialProperty(
            type=type,
            name=name,
            value=Vector((1.0, 1.0, 1.0, 1.0)))

        if result.type == 1:
            read_long(io_stream)  # num available chars
            result.value = read_string(io_stream)
        elif result.type == 2:
            result.value = read_float(io_stream)
        elif result.type > 2 and result.type < 6:
            result.value.x = read_float(io_stream)
            result.value.y = read_float(io_stream)
            if result.type == 4:
                result.value.z = read_float(io_stream)
            if result.type == 5:
                result.value.w = read_float(io_stream)
        elif result.type == 6:
            result.value = read_long(io_stream)
        elif result.type == 7:
            result.value = read_ubyte(io_stream)
        else:
            context.warning('unknown property type in shader material: ' + str(result.type))
        return result

    def size(self, include_head=True):
        size = const_size(8, include_head)
        size += len(self.name) + 1
        if self.type == 1:
            size += 4 + len(self.value) + 1
        elif self.type == 2:
            size += 4
        elif self.type == 3:
            size += 8
        elif self.type == 4:
            size += 12
        elif self.type == 5:
            size += 16
        elif self.type == 6:
            size += 4
        else:
            size += 1
        return size

    def write(self, io_stream):
        write_chunk_head(
            W3D_CHUNK_SHADER_MATERIAL_PROPERTY, io_stream,
            self.size(False))
        write_long(self.type, io_stream)
        write_long(len(self.name) + 1, io_stream)
        write_string(self.name, io_stream)

        if self.type == 1:
            write_long(len(self.value) + 1, io_stream)
            write_string(self.value, io_stream)
        elif self.type == 2:
            write_float(self.value, io_stream)
        elif self.type == 3:
            write_vector2(self.value, io_stream)
        elif self.type == 4:
            write_vector(self.value, io_stream)
        elif self.type == 5:
            write_vector4(self.value, io_stream)
        elif self.type == 6:
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
                constant.type = 2
                constant.value = float(values[0])
            if len(values) > 1:
                constant.type = 3
                constant.value.x = float(values[0])
                constant.value.y = float(values[1])
                constant.value.z = 1.0
                constant.value.w = 1.0
            if len(values) > 2:
                constant.type = 4
                constant.value.z = float(values[2])
            if len(values) == 4:
                constant.type = 5
                constant.value.w = float(values[3])

        elif type_name == 'Int':
            constant.type = 6
            constant.value = int(values[0])
        elif type_name == 'Bool':
            constant.type = 7
            constant.value = bool(values[0])
        else:
            constant.type = 1
            constant.value = values[0]

        return constant

    def create(self, parent):
        if self.type == 1:
            xml_constant = create_node(parent, 'Texture')
            xml_value = create_node(xml_constant, 'Value')
            xml_value.text = self.value

        if self.type > 1 and self.type < 6:
            xml_constant = create_node(parent, 'Float')
            xml_value = create_node(xml_constant, 'Value')
            if self.type == 2:
                xml_value.text = str(self.value)
            else:
                xml_value.text = str(self.value.x)

            if self.type > 2:
                xml_value = create_node(xml_constant, 'Value')
                xml_value.text = str(self.value.y)

            if self.type > 4:
                xml_value = create_node(xml_constant, 'Value')
                xml_value.text = str(self.value.z)

            if self.type == 5:
                xml_value = create_node(xml_constant, 'Value')
                xml_value.text = str(self.value.w)

        elif self.type == 6:
            xml_constant = create_node(parent, 'Int')
            xml_value = create_node(xml_constant, 'Value')
            xml_value.text = str(self.value)

        else:
            xml_constant = create_node(parent, 'Bool')
            xml_value = create_node(xml_constant, 'Value')
            xml_value.text = str(self.value).lower()

        xml_constant.set('Name', self.name)


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
        write_chunk_head(W3D_CHUNK_SHADER_MATERIAL, io_stream,
                         self.size(False), has_sub_chunks=True)
        self.header.write(io_stream)
        write_list(self.properties, io_stream,
                   ShaderMaterialProperty.write)

    @staticmethod
    def parse(xml_fx_shader):
        result = ShaderMaterial(
            header=ShaderMaterialHeader(
                type_name=xml_fx_shader.get('ShaderName'),
                technique_index=int(xml_fx_shader.get('TechniqueIndex', 0))),
            properties=[])

        for constants in xml_fx_shader.findall('Constants'):
            for property in constants:
                result.properties.append(ShaderMaterialProperty.parse(property))
        return result

    def create(self, parent):
        fx_shader = create_node(parent, 'FXShader')
        fx_shader.set('ShaderName', self.header.type_name)

        if self.header.technique_index > 0:
            fx_shader.set('TechniqueIndex', str(self.header.technique_index))

        constants = create_node(fx_shader, 'Constants')
        for property in self.properties:
            property.create(constants)
