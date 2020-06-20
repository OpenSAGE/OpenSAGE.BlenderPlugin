# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from unittest.mock import patch
from mathutils import Vector
from io_mesh_w3d.common.utils.mesh_import import *
from io_mesh_w3d.common.utils.hierarchy_import import *
from io_mesh_w3d.common.utils.animation_import import *
from tests.common.helpers.mesh import *
from tests.common.helpers.hierarchy import *
from tests.common.helpers.animation import *
from tests.utils import *


class TestAnimationImportUtils(TestCase):
    def test_roottransform_visibility_channel_import(self):
        hierarchy = get_hierarchy()
        animation = get_animation()

        animation.channels.append(get_animation_channel(type=CHANNEL_VIS, pivot=0))

        rig = get_or_create_skeleton(hierarchy, get_collection())

        create_animation(rig, animation, hierarchy)