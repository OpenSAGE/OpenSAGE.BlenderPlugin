# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from ....w3d.io_binary import *
from ....w3x.io_xml import *


class VertexInfluence:
    def __init__(self, bone_idx=0, xtra_idx=0, bone_inf=0.0, xtra_inf=0.0):
        self.bone_idx = bone_idx
        self.xtra_idx = xtra_idx
        self.bone_inf = bone_inf
        self.xtra_inf = xtra_inf

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

        # truncating (int()) instead of rounding used to silently drop up to a
        # whole percentage point: Blender stores vertex group weights as float32,
        # so e.g. an intended 42% comes back as 0.41999998, and int(41.999998)
        # is 41. When there genuinely is a second bone, xtra_inf is written as
        # the complement of the rounded bone_inf rather than rounding each side
        # independently, which guarantees the two always sum to exactly 100
        # regardless of that float32 noise - the game blends verts/verts_2 by
        # these weights directly (see W3dVertexInfluence in OpenSAGE), and each
        # is stored in its own bone's local space, so a missing percentage
        # point silently scaled the result and, once a bone was posed away from
        # its bind rotation, threw multi-bone vertices off by a visible amount
        # even though single-bone ones stayed perfect. A vertex with no second
        # bone at all (xtra_inf exactly 0, e.g. an unset placeholder influence)
        # is written as-is: bone_inf is not guaranteed to be 1.0 there
        bone_pct = round(self.bone_inf * 100)
        write_ushort(bone_pct, io_stream)
        if self.xtra_inf > 0:
            write_ushort(100 - bone_pct, io_stream)
        else:
            write_ushort(round(self.xtra_inf * 100), io_stream)

    @staticmethod
    def parse(xml_vertex_influence, xml_vertex_influence2=None):
        result = VertexInfluence(
            bone_idx=int(xml_vertex_influence.get('Bone')),
            bone_inf=parse_float(xml_vertex_influence, 'Weight'))

        if xml_vertex_influence2 is not None:
            result.xtra_idx = int(xml_vertex_influence2.get('Bone'))
            result.xtra_inf = parse_float(xml_vertex_influence2, 'Weight')
        return result

    def create(self, parent, parent2=None):
        influence = create_node(parent, 'I')
        influence.set('Bone', str(self.bone_idx))
        influence.set('Weight', format(self.bone_inf))

        if parent2 is not None:
            influence2 = create_node(parent2, 'I')
            influence2.set('Bone', str(self.xtra_idx))
            influence2.set('Weight', format(self.xtra_inf))
