# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import unittest
import io

from mathutils import Vector

from io_mesh_w3d.structs.w3d_version import Version
from io_mesh_w3d.structs.w3d_rgba import RGBA
from io_mesh_w3d.io_binary import read_chunk_head
from tests.helpers.w3d_vertex_material import *


class TestVertexMaterial(unittest.TestCase):
    def test_write_read(self):
        expected = get_vertex_material()

        self.assertEqual(40, expected.vm_info.size())
        self.assertEqual(98, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_VERTEX_MATERIAL, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = VertexMaterial.read(self, io_stream, chunkEnd)
        compare_vertex_materials(self, expected, actual)

    def test_write_read_minimal(self):
        expected = get_vertex_material_empty()

        self.assertEqual(18, expected.size())

        io_stream = io.BytesIO()
        expected.write(io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        (chunkType, chunkSize, chunkEnd) = read_chunk_head(io_stream)
        self.assertEqual(W3D_CHUNK_VERTEX_MATERIAL, chunkType)
        self.assertEqual(expected.size(False), chunkSize)

        actual = VertexMaterial.read(self, io_stream, chunkEnd)
        compare_vertex_materials(self, expected, actual)

    def test_chunk_sizes(self):
        vm = get_vertex_material_minimal()

        self.assertEqual(2, vm.name_size(vm.vm_name, False))
        self.assertEqual(10, vm.name_size(vm.vm_name))

        self.assertEqual(32, vm.vm_info.size(False))
        self.assertEqual(40, vm.vm_info.size())

        self.assertEqual(2, vm.name_size(vm.vm_args_0, False))
        self.assertEqual(10, vm.name_size(vm.vm_args_0))

        self.assertEqual(2, vm.name_size(vm.vm_args_1, False))
        self.assertEqual(10, vm.name_size(vm.vm_args_1))

        self.assertEqual(70, vm.size(False))
        self.assertEqual(78, vm.size())
