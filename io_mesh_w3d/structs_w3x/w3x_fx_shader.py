# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.structs_w3x.w3x_struct import Struct
from io_mesh_w3d.io_xml import *

class Constant(Struct):
    type = ''
    name = ""
    values = []

    @staticmethod
    def parse(xml_constant):
        constant = Constant(
            type=xml_constant.tagName,
            name=xml_constant.attributes['Name'].value,
            values=[])

        xml_values = xml_constant.getElementsByTagName('Value')
        for xml_value in xml_values:
            constant.values.append(xml_value.childNodes[0].nodeValue)
        return constant

    def create(self, doc):
        xml_constant = doc.createElement(self.type)
        xml_constant.setAttribute('Name', self.name)
        
        for value in self.values:
            xml_value = doc.createElement('Value')
            xml_value.appendChild(doc.createTextNode(str(value)))
            xml_constant.appendChild(xml_value)
       
        return xml_constant


class FXShader(Struct):
    shader_name = ""
    technique_index = 0
    constants = []

    @staticmethod
    def parse(xml_fx_shader):
        result = FXShader(
            shader_name=xml_fx_shader.attributes['ShaderName'].value,
            technique_index=int(xml_fx_shader.attributes['TechniqueIndex'].value),
            constants=[])

        xml_constants = xml_fx_shader.getElementsByTagName('Constants')[0]
        for xml_constant in xml_constants.getElementsByTagName('Float'):
            result.constants.append(Constant.parse(xml_constant))
        for xml_constant in xml_constants.getElementsByTagName('Int'):
            result.constants.append(Constant.parse(xml_constant))
        for xml_constant in xml_constants.getElementsByTagName('Bool'):
            result.constants.append(Constant.parse(xml_constant))
        for xml_constant in xml_constants.getElementsByTagName('Texture'):
            result.constants.append(Constant.parse(xml_constant))
        return result


    def create(self, doc):
        fx_shader = doc.createElement('FXShader')
        fx_shader.setAttribute('ShaderName', self.shader_name)
        fx_shader.setAttribute('TechniqueIndex', str(self.technique_index))

        constants = doc.createElement('Constants')
        fx_shader.appendChild(constants)
        for constant in self.constants:
            constants.appendChild(constant.create(doc))
        return fx_shader
