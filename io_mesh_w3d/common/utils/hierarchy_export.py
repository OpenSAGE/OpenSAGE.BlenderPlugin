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
            pivot = HierarchyPivot(name=bone.name, parent_id=0)

            matrix = bone.matrix

            if bone.parent is not None:
                pivot.parent_id = rig.pose.bones.find(bone.parent.name) + 1
                matrix = bone.parent.matrix.inverted() @ matrix

            (translation, rotation, _) = matrix.decompose()
            pivot.translation = translation
            pivot.rotation = rotation
            eulers = rotation.to_euler()
            pivot.euler_angles = Vector((eulers.x, eulers.y, eulers.z))

            print(pivot.name)
            hierarchy.pivots.append(pivot)

        switch_to_pose(rig, 'POSE')
    else:
        context.error('only one armature per scene allowed!')
        return None, None

    print(len(hierarchy.pivots))



    hierarchy.header.num_pivots = len(hierarchy.pivots)
    return hierarchy, rig
