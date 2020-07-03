# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector
from io_mesh_w3d.w3d.utils.helpers import *
from io_mesh_w3d.common.io_xml import *

W3D_CHUNK_AABBTREE_HEADER = 0x00000091


class AABBTreeHeader:
    def __init__(self, node_count=0, poly_count=0):
        self.node_count = node_count
        self.poly_count = poly_count  # num tris of mesh

    @staticmethod
    def read(io_stream):
        result = AABBTreeHeader(
            node_count=read_ulong(io_stream),
            poly_count=read_ulong(io_stream))

        io_stream.read(24)  # padding
        return result

    @staticmethod
    def size(include_head=True):
        return const_size(32, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_AABBTREE_HEADER, io_stream, self.size(False))
        write_ulong(self.node_count, io_stream)
        write_ulong(self.poly_count, io_stream)

        for _ in range(24):
            write_ubyte(0, io_stream)  # padding


class Children:
    def __init__(self, front=0, back=0):
        self.front = front
        self.back = back

    @staticmethod
    def parse(xml_children):
        return Children(
            front=int(xml_children.get('Front')),
            back=int(xml_children.get('Back')))

    def create(self, parent):
        xml_children = create_node(parent, 'Children')
        xml_children.set('Front', str(self.front))
        xml_children.set('Back', str(self.back))


class Polys:
    def __init__(self, begin=0, count=0):
        self.begin = begin
        self.count = count

    @staticmethod
    def parse(xml_polys):
        return Polys(
            begin=int(xml_polys.get('Begin')),
            count=int(xml_polys.get('Count')))

    def create(self, parent):
        xml_polys = create_node(parent, 'Polys')
        xml_polys.set('Begin', str(self.begin))
        xml_polys.set('Count', str(self.count))


class AABBTreeNode:
    def __init__(self, min=Vector((0.0, 0.0, 0.0)), max=Vector((0.0, 0.0, 0.0)), children=None, polys=None):
        self.min = min
        self.max = max
        self.children = children
        self.polys = polys

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
            min=parse_vector(xml_node.find('Min')),
            max=parse_vector(xml_node.find('Max')))

        xml_polys = xml_node.find('Polys')
        if xml_polys is not None:
            node.polys = Polys.parse(xml_polys)

        xml_children = xml_node.find('Children')
        if xml_children is not None:
            node.children = Children.parse(xml_children)
        return node

    def create(self, parent):
        xml_node = create_node(parent, 'Node')

        create_vector(self.min, xml_node, 'Min')
        create_vector(self.max, xml_node, 'Max')

        if self.polys:
            self.polys.create(xml_node)

        if self.children:
            self.children.create(xml_node)


W3D_CHUNK_AABBTREE = 0x00000090
W3D_CHUNK_AABBTREE_POLYINDICES = 0x00000092
W3D_CHUNK_AABBTREE_NODES = 0x00000093


class AABBTree:
    def __init__(self, header=None, poly_indices=None, nodes=None):
        self.header = header
        self.poly_indices = poly_indices if poly_indices is not None else []
        self.nodes = nodes if nodes is not None else []

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = AABBTree()

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_AABBTREE_HEADER:
                result.header = AABBTreeHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_AABBTREE_POLYINDICES:
                result.poly_indices = read_list(io_stream, subchunk_end, read_long)
            elif chunk_type == W3D_CHUNK_AABBTREE_NODES:
                result.nodes = read_list(io_stream, subchunk_end, AABBTreeNode.read)
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
        write_chunk_head(W3D_CHUNK_AABBTREE, io_stream, self.size(False), has_sub_chunks=True)
        self.header.write(io_stream)

        if self.poly_indices:
            write_chunk_head(W3D_CHUNK_AABBTREE_POLYINDICES, io_stream, long_list_size(self.poly_indices, False))
            write_list(self.poly_indices, io_stream, write_long)

        if self.nodes:
            write_chunk_head(
                W3D_CHUNK_AABBTREE_NODES,
                io_stream,
                list_size(self.nodes, False))
            write_list(self.nodes, io_stream, AABBTreeNode.write)

    @staticmethod
    def parse(xml_aabbtree):
        result = AABBTree(header=AABBTreeHeader())

        xml_polyindices = xml_aabbtree.find('PolyIndices')
        for xml_poly_index in xml_polyindices.findall('P'):
            result.poly_indices.append(int(xml_poly_index.text))

        for xml_node in xml_aabbtree.findall('Node'):
            result.nodes.append(AABBTreeNode.parse(xml_node))

        result.header.poly_count = len(result.poly_indices)
        result.header.node_count = len(result.nodes)
        return result

    def create(self, parent):
        aabbtree = create_node(parent, 'AABTree')

        poly_indices = create_node(aabbtree, 'PolyIndices')
        for index in self.poly_indices:
            xml_index = create_node(poly_indices, 'P')
            xml_index.text = str(index)

        for node in self.nodes:
            node.create(aabbtree)
