# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019

from io_mesh_w3d.structs.struct import Struct
from io_mesh_w3d.io_binary import *

class Version(Struct):
    major = 5
    minor = 0

    @staticmethod
    def read(io_stream):
        data = read_ulong(io_stream)
        return Version(major=data >> 16,
                       minor=data & 0xFFFF)

    def write(self, io_stream):
        write_ulong(io_stream, (self.major << 16) | self.minor)

    def __eq__(self, other):
        if isinstance(other, Version):
            return self.major == other.major and self.minor == other.minor
        return False