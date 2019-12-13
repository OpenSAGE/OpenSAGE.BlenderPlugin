# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.structs_w3x.w3x_struct import Struct
from io_mesh_w3d.io_xml import *


#<Node>
#	<Min X="-14.729331" Y="5.105928" Z="-1.288723"/>
#	<Max X="-2.990558" Y="9.814140" Z="2.538390"/>
#	<Polys Begin="47" Count="4"/>
#</Node>
#<Node>
#	<Min X="-15.416054" Y="-6.912834" Z="-1.306865"/>
#	<Max X="-9.852810" Y="6.912835" Z="1.577101"/>
#	<Children Front="37" Back="38"/>
#</Node>


class Children(Struct):
    front = 0
    back = 0

class Polys(Struct):
    begin = 0
    count = 0


class Node(Struct):
    min = Vector((0, 0, 0))
    max = Vector((0, 0, 0))
    children = None

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


class AABBTree(Struct):
    poly_indices = []
    nodes = []

    @staticmethod
    def parse(xml_aabbtree):
        result = AABBTree(
            poly_indices=[],
            nodes=[])

        xml_polyindices = xml_aabbtree.getElementsByTagName('PolyIndices')[0]
        for xml_poly_index in xml_polyindices.getElementsByTagName('P'):
            result.poly_indices.append(int(xml_poly_index.childNodes[0].nodeValue))

        xml_nodes = xml_aabbtree.getElementsByTagName('Node')
        for xml_node in xml_nodes:
            result.nodes.append(Node.parse(xml_node))
        return result


    def create(self, doc):
        aabbtree = doc.createElement('AABTree')

        poly_indices = doc.createElement('PolyIndices')
        aabbtree.appendChild(poly_indices)
        for index in self.poly_indices:
            xml_index = doc.createElement('P')
            xml_index.appendChild(doc.createTextNode(str(index)))
            poly_indices.appendChild(xml_index)

        for node in self.nodes:
            xml_node = doc.createElement('Node')
            xml_node_min = doc.createElement('Node')

            aabbtree.appendChild(xml_node)
        return aabbtree
