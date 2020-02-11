# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh


def create_sphere():
    mesh = bpy.data.meshes.new('Basic_Sphere')
    basic_sphere = bpy.data.objects.new("Basic_Sphere", mesh)

    b_mesh = bmesh.new()
    bmesh.ops.create_uvsphere(b_mesh, u_segments=12, v_segments=6, diameter=35)
    b_mesh.to_mesh(mesh)
    b_mesh.free()

    return basic_sphere


def create_cone(name):
    mesh = bpy.data.meshes.new(name)
    cone = bpy.data.objects.new(name, mesh)

    b_mesh = bmesh.new()
    bmesh.ops.create_cone(b_mesh, cap_ends=True, cap_tris=True,
                          segments=10, diameter1=0, diameter2=1.0, depth=2.0, calc_uvs=True)
    b_mesh.to_mesh(mesh)
    b_mesh.free()

    return mesh, cone
