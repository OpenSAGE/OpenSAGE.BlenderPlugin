# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3d.io_binary import *
from io_mesh_w3d.w3d.utils import *


W3D_CHUNK_AABBTREE_HEADER = 0x00000091


class AABBTreeHeader(Struct):
    node_count = 0
    poly_count = 0  # num tris of mesh

    @staticmethod
    def read(io_stream):
        result = AABBTreeHeader(
            node_count=read_ulong(io_stream),
            poly_count=read_ulong(io_stream))

        io_stream.read(24)  # padding
        return result

    @staticmethod
    def size(include_head=True):
        return const_size(8, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_AABBTREE_HEADER, io_stream,
                         self.size(False))
        write_ulong(self.node_count, io_stream)
        write_ulong(self.poly_count, io_stream)

        for pad in range(24):
            write_ubyte(0, io_stream)  # padding


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


class AABBTreeNode(Struct):
    min = Vector((0.0, 0.0, 0.0))
    max = Vector((0.0, 0.0, 0.0))
    children = None
    polys = None

    @staticmethod
    def read(io_stream):
        node = AABBTreeNode(
            min=read_vector(io_stream),
            max=read_vector(io_stream))
        node.children = Children(
            front=read_long(io_stream),
            back=read_long(io_stream))
        return node

    @staticmethod
    def size():
        return 32

    def write(self, io_stream):
        write_vector(self.min, io_stream)
        write_vector(self.max, io_stream)
        write_long(self.children.front, io_stream)
        write_long(self.children.back, io_stream)

    @staticmethod
    def parse(xml_node):
        node = AABBTreeNode(
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


W3D_CHUNK_AABBTREE = 0x00000090
W3D_CHUNK_AABBTREE_POLYINDICES = 0x00000092
W3D_CHUNK_AABBTREE_NODES = 0x00000093


class AABBTree(Struct):
    header = AABBTreeHeader()
    poly_indices = []
    nodes = []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = AABBTree()

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_AABBTREE_HEADER:
                result.header = AABBTreeHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_AABBTREE_POLYINDICES:
                result.poly_indices = read_list(
                    io_stream, subchunk_end, read_long)
            elif chunk_type == W3D_CHUNK_AABBTREE_NODES:
                result.nodes = read_list(
                    io_stream, subchunk_end, AABBTreeNode.read)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = const_size(0, include_head)
        size += self.header.size()
        size += long_list_size(self.poly_indices)
        size += list_size(self.nodes)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_AABBTREE, io_stream,
                         self.size(False), has_sub_chunks=True)
        self.header.write(io_stream)

        if self.poly_indices:
            write_chunk_head(W3D_CHUNK_AABBTREE_POLYINDICES, io_stream,
                             long_list_size(self.poly_indices, False))
            write_list(self.poly_indices, io_stream, write_long)
        if self.nodes:
            write_chunk_head(
                W3D_CHUNK_AABBTREE_NODES,
                io_stream,
                list_size(
                    self.nodes,
                    False))
            write_list(self.nodes, io_stream, AABBTreeNode.write)

    @staticmethod
    def parse(xml_aabbtree):
        result = AABBTree(
            header=AABBTreeHeader(),
            poly_indices=[],
            nodes=[])

        xml_polyindices = xml_aabbtree.getElementsByTagName('PolyIndices')[0]
        for xml_poly_index in xml_polyindices.getElementsByTagName('P'):
            result.poly_indices.append(
                int(xml_poly_index.childNodes[0].nodeValue))

        xml_nodes = xml_aabbtree.getElementsByTagName('Node')
        for xml_node in xml_nodes:
            result.nodes.append(Node.parse(xml_node))

        result.header.poly_count = len(result.poly_indices)
        result.header.node_count = len(result.nodes)
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