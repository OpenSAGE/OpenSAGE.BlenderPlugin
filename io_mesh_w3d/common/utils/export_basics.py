# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy


def switch_to_pose(rig, pose):
    if rig is not None:
        rig.data.pose_position = pose
        bpy.context.view_layer.update()
