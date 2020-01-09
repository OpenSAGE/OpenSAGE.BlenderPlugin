# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3d.io_binary import *
from io_mesh_w3d.w3d.structs.version import Version


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
            bone_idx=int(xml_vertex_influence.attributes['Bone'].value),
            xtra_idx=0,
            bone_inf=float(xml_vertex_influence.attributes['Weight'].value),
            xtra_inf=0.0)

        if xml_vertex_influence2 is not None:
            result.xtra_idx = int(xml_vertex_influence2.attributes['Bone'].value)
            result.xtra_inf = float(xml_vertex_influence2.attributes['Weight'].value)
        return result

    def create(self, doc, multibone=False):
        influence = doc.createElement('I')
        influence.setAttribute('Bone', str(self.bone_idx))
        influence.setAttribute('Weight', str(self.bone_inf))

        influence2 = None
        if multibone:
            influence2 = doc.createElement('I')
            influence2.setAttribute('Bone', str(self.xtra_idx))
            influence2.setAttribute('Weight', str(self.xtra_inf))
        return (influence, influence2)
