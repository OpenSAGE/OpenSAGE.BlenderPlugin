# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3x.io_xml import *


class Children(Struct):
    front = 0
    back = 0

    @staticmethod
    def parse(xml_children):
        return Children(
            front=int(xml_children.attributes['Front'].value),
            back=int(xml_children.attributes['Back'].value))

    def create(self, doc):
        xml_children = doc.createElement('Children')
        xml_children.setAttribute('Front', str(self.front))
        xml_children.setAttribute('Back', str(self.back))
        return xml_children


class Polys(Struct):
    begin = 0
    count = 0

    @staticmethod
    def parse(xml_polys):
        return Polys(
            begin=int(xml_polys.attributes['Begin'].value),
            count=int(xml_polys.attributes['Count'].value))

    def create(self, doc):
        xml_polys = doc.createElement('Polys')
        xml_polys.setAttribute('Begin', str(self.begin))
        xml_polys.setAttribute('Count', str(self.count))
        return xml_polys


class Node(Struct):
    min = Vector((0, 0, 0))
    max = Vector((0, 0, 0))
    polys = None
    children = None

    @staticmethod
    def parse(xml_node):
        node = Node(
            children=None,
            polys=None)

        xml_min = xml_node.getElementsByTagName('Min')[0]
        node.min = parse_vector(xml_min)

        xml_max = xml_node.getElementsByTagName('Max')[0]
        node.max = parse_vector(xml_max)

        xml_polys = xml_node.getElementsByTagName('Polys')
        if xml_polys:
            node.polys = Polys.parse(xml_polys[0])

        xml_children = xml_node.getElementsByTagName('Children')
        if xml_children:
            node.children = Children.parse(xml_children[0])
        return node

    def create(self, doc):
        xml_node = doc.createElement('Node')

        xml_node.appendChild(create_vector(self.min, doc, 'Min'))
        xml_node.appendChild(create_vector(self.max, doc, 'Max'))

        if self.polys is not None:
            xml_node.appendChild(self.polys.create(doc))

        if self.children is not None:
            xml_node.appendChild(self.children.create(doc))

        return xml_node


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
            result.poly_indices.append(
                int(xml_poly_index.childNodes[0].nodeValue))

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
            aabbtree.appendChild(node.create(doc))
        return aabbtree
