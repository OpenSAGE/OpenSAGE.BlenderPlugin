# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy

from io_mesh_w3d.common.utils.mesh_import import *
from io_mesh_w3d.common.utils.hierarchy_import import *
from tests.common.helpers.mesh import *
from tests.common.helpers.hierarchy import *
from tests.common.helpers.hlod import *
from tests.utils import *


class TestMeshImportUtils(TestCase):
    def test_custom_normals_import(self):
        mesh_name = 'testmesh'
        mesh_struct = get_mesh(mesh_name)

        mesh_struct.normals = [get_vec(0.0, 0.0, -1.0),
                    get_vec(0.0, 0.0, -1.0),
                    get_vec(0.0, 0.0, -1.0),
                    get_vec(0.0, 0.0, -1.0),
                    get_vec(0.0, 0.0, -1.0),
                    get_vec(0.0, 0.0, -1.0),
                    get_vec(0.0, 0.0, -1.0),
                    get_vec(0.0, 0.0, -1.0)]
        
        create_mesh(self, mesh_struct, bpy.context.scene.collection)

        mesh = bpy.data.meshes[mesh_name]

        mesh.calc_tangents()

        for i, vertex in enumerate(mesh.vertices):
            loop = [loop for loop in mesh.loops if loop.vertex_index == i][0]
            compare_vectors(self, mesh_struct.normals[i], loop.normal)


    def test_custom_normals_import_skinned_mesh(self):
        mesh_name = 'soldier'
        mesh_struct = get_mesh(mesh_name, skin=True)
        hierarchy = get_hierarchy()
        hlod = get_hlod()

        mesh_struct.normals = [get_vec(0.0, 0.0, -1.0),
                    get_vec(0.0, 0.0, -1.0),
                    get_vec(0.0, 0.0, -1.0),
                    get_vec(0.0, 0.0, -1.0),
                    get_vec(0.0, 0.0, -1.0),
                    get_vec(0.0, 0.0, -1.0),
                    get_vec(0.0, 0.0, -1.0),
                    get_vec(0.0, 0.0, -1.0)]

        expected_normals = [get_vec(0.25, 0.61, -0.74),
                    get_vec(0.25, 0.61, -0.75),
                    get_vec(-0.10, 0.96, -0.25),
                    get_vec(-0.10, 0.96, -0.25),
                    get_vec(-0.71, 0.69, -0.019),
                    get_vec(-0.71, 0.69, -0.019),
                    get_vec(-0.71, 0.69, -0.019),
                    get_vec(-0.71, 0.69, -0.019)]
        
        create_mesh(self, mesh_struct, bpy.context.scene.collection)

        get_or_create_skeleton(hlod, hierarchy, bpy.context.scene.collection)

        mesh = bpy.data.meshes[mesh_name]

        rig = bpy.data.objects[hierarchy.name()]
        rig_mesh(mesh_struct, hierarchy, rig, sub_object=hlod.lod_arrays[0].sub_objects[1])

        mesh.calc_tangents()

        for i, vertex in enumerate(mesh.vertices):
            loop = [loop for loop in mesh.loops if loop.vertex_index == i][0]
            compare_vectors(self, expected_normals[i], loop.normal)