# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019

import bpy
import bmesh
from mathutils import Vector, Quaternion
from io_mesh_w3d.w3d_structs import *


def triangulate(mesh):
	bm = bmesh.new()
	bm.from_mesh(mesh)
	bmesh.ops.triangulate(bm, faces = bm.faces)
	bm.to_mesh(mesh)
	bm.free()


def export_meshes(sknFile):
    containerName = (os.path.splitext(os.path.basename(sknFile.name))[0]).upper()
    mesh_objects = [object for object in bpy.context.scene.objects if object.type == 'MESH']

    for mesh_object in mesh_objects:
        if mesh_object.name == "BOUNDINGBOX":
            box = Box(
                name=containerName + "." + mesh_object.name,
                center=mesh_object.location)
            box_mesh = mesh_object.to_mesh(bpy.context.scene, False, 'PREVIEW', calc_tessface=True)
            box.extend = Vector((box_mesh.vertices[0].co.x * 2, box_mesh.vertices[0].co.y * 2, box_mesh.vertices[0].co.z))
            box.write(sknFile)
        else:
            mesh_struct = Mesh()
            header = mesh_struct.header
            header.meshName = mesh_object.name
            header.containerName = containerName

            mesh = mesh_object.to_mesh(bpy.context.scene, False, 'PREVIEW', calc_tessface=True)
            triangulate(mesh)

            header.vertCount = len(mesh.vertices)

            for v in mesh.vertices:
                mesh_struct.verts.append(v.co.xyz)
                mesh_struct.normals.append(v.normal)

            header.minCorner = Vector((mesh_object.bound_box[0][0], mesh_object.bound_box[0][1], mesh_object.bound_box[0][2]))
            header.maxCorner = Vector((mesh_object.bound_box[6][0], mesh_object.bound_box[6][1], mesh_object.bound_box[6][2]))

            for face in mesh.polygons:
                triangle = MeshTriangle()
                triangle.vertIds = [face.vertices[0], face.vertices[1], face.vertices[2]]
                triangle.normal = face.normal
                tri_pos = Vector((mesh.vertices[face.vertices[0]] + mesh.vertices[face.vertices[1]] + mesh.vertices[face.vertices[2]])) / 3.0
                triangle.distance = (mesh_object.location - tri_pos).length
                mesh.faces.append(triangle)

            header.faceCount = len(mesh.faces)

        mesh.write(sknFile)



