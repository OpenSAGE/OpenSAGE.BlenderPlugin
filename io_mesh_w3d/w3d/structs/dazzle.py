# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3d.io_binary import *
from io_mesh_w3d.w3d.utils import *

W3D_CHUNK_DAZZLE = 0x00000900
W3D_CHUNK_DAZZLE_NAME = 0x00000901
W3D_CHUNK_DAZZLE_TYPENAME = 0x00000902

# The dazzle is always assumed to be at the pivot point
# of the bone it is attached to (you should enable Export_Transform) for 
# dazzles. If the dazzle-type (from dazzle.ini) is directional, then the 
# coordinate-system of the bone will define the direction.


class DazzleType(Struct):
    name = 'DEFAULT'
    #HaloIntensity=1.0
    #HaloIntensityPow=0.95
    HaloSizePow=0.95
    HaloArea=1.0
    HaloScaleX=0.2
    HaloScaleY=0.2
    DazzleArea=0.05
    DazzleDirectionArea=0
    DazzleDirection=0,1,1
    DazzleSizePow=0.9
    DazzleIntensityPow=0.9
    #DazzleIntensity=50
    DazzleScaleX=1.0
    DazzleScaleY=1.0
    #FadeoutStart=30.0
    #FadeoutEnd=40.0
    #SizeOptimizationLimit=0.05
    #HistoryWeight=0.975
    #UseCameraTranslation=1
    HaloTextureName='SunHalo.tga'
    DazzleTextureName='SunDazzle.tga'
    DazzleColor=1,1,1
    HaloColor=1,1,1
    DazzleTestColor=1,1,1



class Dazzle(Struct):
    name = ''
    type_name = ''

    def name(self):
        return self.name_.split('.')[-1]

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = Dazzle(name='', type_name='')

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)
            if chunk_type == W3D_CHUNK_DAZZLE_NAME:
                result.name = read_string(io_stream)
            elif chunk_type == W3D_CHUNK_DAZZLE_TYPENAME:
                result.type_name = read_string(io_stream)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = const_size(0, include_head)
        size += text_size(self.name)
        size += text_size(self.type_name)
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_DAZZLE, io_stream, self.size(False))

        write_chunk_head(W3D_CHUNK_DAZZLE_NAME, io_stream, text_size(self.name, False))
        write_string(self.name, io_stream)

        write_chunk_head(W3D_CHUNK_DAZZLE_TYPENAME, io_stream, text_size(self.type_name, False))
        write_string(self.type_name, io_stream)
