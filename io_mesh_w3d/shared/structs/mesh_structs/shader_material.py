# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.shared.structs.rgba import RGBA

from io_mesh_w3d.w3d.io_binary import *
from io_mesh_w3d.w3d.utils import *
from io_mesh_w3d.w3d.structs.version import Version


W3D_CHUNK_SHADER_MATERIAL_HEADER = 0x52


class ShaderMaterialHeader(Struct):
    technique_index = 0
    type_name = ""
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
    name = ""
    value = None

    @staticmethod
    def read(context, io_stream):
        type = read_long(io_stream)
        read_long(io_stream)  # num available chars
        name = read_string(io_stream)
        result = ShaderMaterialProperty(
            type=type,
            name=name)

        if result.type == 1:
            read_long(io_stream)  # num available chars
            result.value = read_string(io_stream)
        elif result.type == 2:
            result.value = read_float(io_stream)
        elif result.type == 3:
            result.value = read_vector2(io_stream)
        elif result.type == 4:
            result.value = read_vector(io_stream)
        elif result.type == 5:
            result.value = RGBA.read_f(io_stream)
        elif result.type == 6:
            result.value = read_long(io_stream)
        elif result.type == 7:
            result.value = read_ubyte(io_stream)
        else:
            message = "WARNING: unknown property type in shader material: %s" % result.type
            print(message)
            context.report({'ERROR'}, message)
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
        elif self.type == 7:
            size += 1
        else:
            message = "WARNING: invalid property type in shader material: %s" % self.type
            print(message)
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
            self.value.write_f(io_stream)
        elif self.type == 6:
            write_long(self.value, io_stream)
        elif self.type == 7:
            write_ubyte(self.value, io_stream)
        else:
            message = "WARNING: invalid property type in shader material: %s" % self.type
            print(message)

    @staticmethod
    def parse(xml_constant):
        type_name = xml_constant.tagName
        constant = ShaderProperty(
            name=xml_constant.attributes['Name'].value,
            value=None)

        values = []
        xml_values = xml_constant.getElementsByTagName('Value')
        for xml_value in xml_values:
            values.append(xml_value.childNodes[0].nodeValue)

        if type_name == 'Float':
            # looks like we also have vec4, but use rgba for now
            if len(values) == 3:
                constant.value = Vector((
                        float(values[0]),
                        float(values[1]),
                        float(values[2])))
            elif len(values) == 4:
                constant.value = RGBA((
                        float(values[0]),
                        float(values[1]),
                        float(values[2]),
                        float(values[3])))
            else:
                constant.value = float(values[0])
        elif type_name == 'Int':
            contant.value = int(values[0])
        elif type_name == 'Bool':
            contant.value = bool(values[0])
        else:
            constant.value = values[0]

        return constant

    def create(self, doc):
        xml_constant = doc.createElement(self.type)
        xml_constant.setAttribute('Name', self.name)

        if self.type == 1:
            xml_value = doc.createElement('Value')
            xml_value.appendChild(doc.createTextNode(str(self.value)))
            xml_constant.appendChild(xml_value)

        elif self.type == 2:
            xml_value = doc.createElement('Value')
            xml_value.appendChild(doc.createTextNode(str(self.value)))
            xml_constant.appendChild(xml_value)

        elif self.type == 3:
            xml_value = doc.createElement('Value')
            xml_value.appendChild(doc.createTextNode(str(self.value.x)))
            xml_constant.appendChild(xml_value)
            xml_value = doc.createElement('Value')
            xml_value.appendChild(doc.createTextNode(str(self.value.y)))
            xml_constant.appendChild(xml_value)

        elif self.type == 4:
            xml_value = doc.createElement('Value')
            xml_value.appendChild(doc.createTextNode(str(self.value.x)))
            xml_constant.appendChild(xml_value)
            xml_value = doc.createElement('Value')
            xml_value.appendChild(doc.createTextNode(str(self.value.y)))
            xml_constant.appendChild(xml_value)
            xml_value = doc.createElement('Value')
            xml_value.appendChild(doc.createTextNode(str(self.value.z)))
            xml_constant.appendChild(xml_value)

        elif self.type == 5:
            xml_value = doc.createElement('Value')
            xml_value.appendChild(doc.createTextNode(str(self.value.r)))
            xml_constant.appendChild(xml_value)
            xml_value = doc.createElement('Value')
            xml_value.appendChild(doc.createTextNode(str(self.value.g)))
            xml_constant.appendChild(xml_value)
            xml_value = doc.createElement('Value')
            xml_value.appendChild(doc.createTextNode(str(self.value.b)))
            xml_constant.appendChild(xml_value)
            xml_value = doc.createElement('Value')
            xml_value.appendChild(doc.createTextNode(str(self.value.a)))
            xml_constant.appendChild(xml_value)

        elif self.type == 6 or self.type == 7:
            xml_value = doc.createElement('Value')
            xml_value.appendChild(doc.createTextNode(str(self.value)))
            xml_constant.appendChild(xml_value)

        return xml_constant


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
                    type_name=xml_fx_shader.attributes['ShaderName'].value,
                    technique_index=int(xml_fx_shader.attributes['TechniqueIndex'].value)),
                properties=[])

        xml_constants = xml_fx_shader.getElementsByTagName('Constants')[0]
        for xml_constant in xml_constants:
            result.properties.append(ShaderMaterialProperty.parse(xml_constant))
        return result

    def create(self, doc):
        fx_shader = doc.createElement('FXShader')
        fx_shader.setAttribute('ShaderName', self.header.type_name)
        fx_shader.setAttribute('TechniqueIndex', str(self.header.technique_index))

        constants = doc.createElement('Constants')
        fx_shader.appendChild(constants)
        for property in self.properties:
            constants.appendChild(property.create(doc))
        return fx_shader
