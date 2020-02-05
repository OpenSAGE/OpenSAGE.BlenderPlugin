# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.shared.utils.basics import *
from io_mesh_w3d.shared.utils.export_basics import *
from io_mesh_w3d.shared.structs.hierarchy import *


pick_plane_names = ['PICK']

def process_pivot(pivot, pivots, hierarchy):
    hierarchy.pivots.append(pivot)
    children = [child for child in pivots if child.parent_id == pivot.name]
    parent_index = len(hierarchy.pivots) - 1

    for child in children:
        child.parent_id = parent_index
        process_pivot(child, pivots, hierarchy)
    pivot.processed = True


def retrieve_hierarchy(context, container_name):
    hierarchy = Hierarchy(
        header=HierarchyHeader(),
        pivots=[],
        pivot_fixups=[])

    root = HierarchyPivot(
        name='ROOTTRANSFORM',
        parentID=-1,
        translation=Vector())
    hierarchy.pivots.append(root)

    rig = None
    rigs = get_objects('ARMATURE')
    pivots = []

    if len(rigs) == 0:
        hierarchy.header.name = container_name
        hierarchy.header.center_pos = Vector()
    elif len(rigs) == 1:
        rig = rigs[0]

        switch_to_pose(rig, 'REST')

        root.translation = rig.location

        hierarchy.header.name = rig.name
        hierarchy.header.center_pos = rig.location

        for bone in rig.pose.bones:
            pivot = HierarchyPivot(
                name=bone.name,
                parent_id=0)

            matrix = bone.matrix

            if bone.parent is not None:
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
        return (None, None)

    meshes = []
    if rig is not None:
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

        if mesh.delta_location.length < 0.01 \
                and mesh.delta_rotation_quaternion == Quaternion():
            continue

        eulers = mesh.rotation_quaternion.to_euler()
        pivot = HierarchyPivot(
            name=mesh.name,
            parent_id=0,
            translation=mesh.delta_location,
            rotation=mesh.delta_rotation_quaternion,
            euler_angles=Vector((eulers.x, eulers.y, eulers.z)))

        if mesh.parent_bone != '':
            pivot.parent_id = mesh.parent_bone
        elif mesh.parent is not None:
            pivot.parent_id = mesh.parent.name

        pivots.append(pivot)

    for pivot in pivots:
        pivot.processed = False

    for pivot in pivots:
        if pivot.processed or pivot.parent_id != 0:
            continue
        process_pivot(pivot, pivots, hierarchy)

    hierarchy.header.num_pivots = len(hierarchy.pivots)
    return (hierarchy, rig)

