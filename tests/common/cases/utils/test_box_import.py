# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy

from io_mesh_w3d.common.utils.box_import import *
from tests.common.helpers.collision_box import *
from tests.common.helpers.hlod import *
from tests.common.helpers.hierarchy import *
from tests.utils import *


class TestBoxImportUtils(TestCase):
    def test_create_box(self):
        box = get_collision_box()
        hlod = get_hlod()
        hlod.lod_arrays[0].sub_objects = []

        hierarchy = get_hierarchy()

        fake_rig = bpy.data.objects.new('rig', bpy.data.armatures.new('rig'))

        create_box(box, hlod, hierarchy, fake_rig, bpy.context.scene.collection)
