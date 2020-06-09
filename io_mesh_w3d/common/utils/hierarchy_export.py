# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector
from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.common.structs.hierarchy import *


pick_plane_names = ['PICK']


def retrieve_hierarchy(context, container_name):
    root = HierarchyPivot(name='ROOTTRANSFORM')

    hierarchy = Hierarchy(
        header=HierarchyHeader(),
        pivots=[root])

    rig = None
    rigs = get_objects('ARMATURE')

    pivot_id_dict = dict()

    if len(rigs) == 0:
        hierarchy.header.name = container_name
        hierarchy.header.center_pos = Vector()
        context.warning('scene does not contain an armature object!')

    if len(rigs) > 0:
        rig = rigs[0]

        switch_to_pose(rig, 'REST')

        root.translation = rig.delta_location
        root.rotation = rig.delta_rotation_quaternion

        hierarchy.header.name = rig.data.name
        hierarchy.header.center_pos = rig.location

        for bone in rig.pose.bones:
            pivot = HierarchyPivot(name=bone.name, parent_id=0)

            matrix = bone.matrix

            if bone.parent is not None:
                pivot.parent_id = pivot_id_dict[bone.parent.name]
                matrix = bone.parent.matrix.inverted() @ matrix

            (translation, rotation, _) = matrix.decompose()
            pivot.translation = translation
            pivot.rotation = rotation
            eulers = rotation.to_euler()
            pivot.euler_angles = Vector((eulers.x, eulers.y, eulers.z))

            pivot_id_dict[pivot.name] = len(hierarchy.pivots)
            hierarchy.pivots.append(pivot)

        switch_to_pose(rig, 'POSE')

    if len(rigs) > 1:
        context.error('only one armature per scene allowed! Exporting only the first one: ' + rigs[0].name)

    meshes = get_objects('MESH')

    for mesh in meshes:
        process_mesh(context, mesh, hierarchy, pivot_id_dict)

    hierarchy.header.num_pivots = len(hierarchy.pivots)
    return hierarchy, rig


def process_mesh(context, mesh, hierarchy, pivot_id_dict):
    if mesh.vertex_groups \
            or mesh.object_type == 'BOX' \
            or mesh.name in pick_plane_names \
            or mesh.name in pivot_id_dict.keys():
        return

    if not mesh.parent_type == 'BONE':
        pivot = HierarchyPivot(name=mesh.name, parent_id=0)
        matrix = mesh.matrix_local

        if mesh.parent is not None and mesh.parent.type == 'MESH':
            context.warning('mesh \'' + mesh.name + '\' did have a object instead of a bone as parent!')
            if mesh.parent.name not in pivot_id_dict.keys():
                process_mesh(context, mesh.parent, hierarchy, pivot_id_dict)
                return

            pivot.parent_id = pivot_id_dict[mesh.parent.name]
            matrix = mesh.parent.matrix_local.inverted() @ matrix

        location, rotation, _ = matrix.decompose()
        eulers = rotation.to_euler()

        pivot.translation = location
        pivot.rotation = rotation
        pivot.euler_angles = Vector((eulers.x, eulers.y, eulers.z))

        pivot_id_dict[pivot.name] = len(hierarchy.pivots)
        hierarchy.pivots.append(pivot)

    for child in mesh.children:
        process_mesh(context, child, hierarchy, pivot_id_dict)
