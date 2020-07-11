# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.w3d.io_binary import *


class Version:
    def __init__(self, major=5, minor=0):
        self.major = major
        self.minor = minor

    @staticmethod
    def read(io_stream):
        data = read_ulong(io_stream)
        return Version(major=data >> 16,
                       minor=data & 0xFFFF)

    def write(self, io_stream):
        write_ulong((self.major << 16) | self.minor, io_stream)

    def __eq__(self, other):
        if isinstance(other, Version):
            return self.major == other.major and self.minor == other.minor
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
