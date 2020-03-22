# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.common.utils.helpers import *
from io_mesh_w3d.common.structs.hierarchy import *


pick_plane_names = ['PICK']


def create_pivot_subtree(pivot, pivots, hierarchy):
    hierarchy.pivots.append(pivot)
    children = [child for child in pivots if child.parent_id == pivot.name]
    parent_index = len(hierarchy.pivots) - 1

    for child in children:
        child.parent_id = parent_index
        create_pivot_subtree(child, pivots, hierarchy)
    pivot.processed = True


def retrieve_hierarchy(context, container_name):
    root = HierarchyPivot(
        name='ROOTTRANSFORM',
        parentID=-1,
        translation=Vector())

    hierarchy = Hierarchy(
        header=HierarchyHeader(),
        pivots=[root],
        pivot_fixups=[])

    rig = None
    rigs = get_objects('ARMATURE')
    pivots = []

    if len(rigs) == 0:
        hierarchy.header.name = container_name
        hierarchy.header.center_pos = Vector()
    elif len(rigs) == 1:
        rig = rigs[0]

        switch_to_pose(rig, 'REST')

        root.translation = rig.delta_location
        root.rotation = rig.delta_rotation_quaternion

        hierarchy.header.name = rig.name
        hierarchy.header.center_pos = rig.location

        for bone in rig.pose.bones:
            pivot = HierarchyPivot(
                name=bone.name,
                parent_id=0)

            matrix = bone.matrix

            if bone.parent :
                pivot.parent_id = bone.parent.name
                matrix = bone.parent.matrix.inverted() @ matrix

            (translation, rotation, _) = matrix.decompose()
            pivot.translation = translation
            pivot.rotation = rotation
            eulers = rotation.to_euler()
            pivot.euler_angles = Vector((eulers.x, eulers.y, eulers.z))

            pivots.append(pivot)

        switch_to_pose(rig, 'POSE')
    else:
        context.error('only one armature per scene allowed!')
        return None, None

    meshes = []
    if rig :
        for coll in bpy.data.collections:
            if rig.name in coll.objects:
                meshes = get_objects('MESH', coll.objects)
    else:
        meshes = get_objects('MESH')

    for mesh in list(reversed(meshes)):
        if mesh.vertex_groups \
                or mesh.object_type == 'BOX' \
                or mesh.name in pick_plane_names:
            continue

        (location, rotation, _) = mesh.matrix_local.decompose()
        eulers = rotation.to_euler()

        if location.length < 0.01 and abs(eulers.x) < 0.01 and abs(eulers.y) < 0.01 and abs(eulers.z) < 0.01:
            continue

        pivot = HierarchyPivot(
            name=mesh.name,
            parent_id=0,
            translation=location,
            rotation=rotation,
            euler_angles=Vector((eulers.x, eulers.y, eulers.z)))

        if mesh.parent_bone != '':
            pivot.parent_id = mesh.parent_bone
        elif mesh.parent :
            if mesh.parent.name == rig.name:
                pivot.parent_id = 0
            else:
                pivot.parent_id = mesh.parent.name

        pivots.append(pivot)

    for pivot in pivots:
        pivot.processed = False

    for pivot in pivots:
        if pivot.processed or pivot.parent_id != 0:
            continue
        create_pivot_subtree(pivot, pivots, hierarchy)

    hierarchy.header.num_pivots = len(hierarchy.pivots)
    return hierarchy, rig
