# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3d.io_binary import *
from io_mesh_w3d.w3x.io_xml import *


class VertexInfluence(Struct):
    bone_idx = 0
    xtra_idx = 0
    bone_inf = 0.0
    xtra_inf = 0.0

    @staticmethod
    def read(io_stream):
        return VertexInfluence(
            bone_idx=read_ushort(io_stream),
            xtra_idx=read_ushort(io_stream),
            bone_inf=read_ushort(io_stream) / 100,
            xtra_inf=read_ushort(io_stream) / 100)

    @staticmethod
    def size():
        return 8

    def write(self, io_stream):
        write_ushort(self.bone_idx, io_stream)
        write_ushort(self.xtra_idx, io_stream)
        write_ushort(int(self.bone_inf * 100), io_stream)
        write_ushort(int(self.xtra_inf * 100), io_stream)

    @staticmethod
    def parse(xml_vertex_influence, xml_vertex_influence2=None):
        result = VertexInfluence(
            bone_idx=int(xml_vertex_influence.get('Bone')),
            xtra_idx=0,
            bone_inf=float(xml_vertex_influence.get('Weight')),
            xtra_inf=0.0)

        if xml_vertex_influence2 :
            result.xtra_idx = int(xml_vertex_influence2.get('Bone'))
            result.xtra_inf = float(xml_vertex_influence2.get('Weight'))
        return result

    def create(self, parent, parent2=None):
        influence = create_node(parent, 'I')
        influence.set('Bone', str(self.bone_idx))
        influence.set('Weight', format(self.bone_inf))

        if parent2 :
            influence2 = create_node(parent2, 'I')
            influence2.set('Bone', str(self.xtra_idx))
            influence2.set('Weight', format(self.xtra_inf))
