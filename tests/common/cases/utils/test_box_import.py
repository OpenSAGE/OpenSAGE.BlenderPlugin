# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy

from io_mesh_w3d.common.utils.box_import import *
from tests.common.helpers.collision_box import *
from tests.common.helpers.hlod import *
from tests.common.helpers.hierarchy import *
from tests.utils import *


class TestBoxImportUtils(TestCase):
    def test_import_box(self):
        box = get_collision_box()
        hlod = get_hlod()
        sub_object = get_hlod_sub_object(bone=1, name='containerName.box')
        hlod.lod_arrays[0].sub_objects = [sub_object]

        hierarchy = get_hierarchy()

        fake_rig = bpy.data.objects.new('rig', bpy.data.armatures.new('rig'))

        create_box(box, bpy.context.scene.collection)
        rig_box(box, hierarchy, fake_rig, sub_object)

        self.assertTrue('BOUNDINGBOX' in bpy.data.objects)
