# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import bmesh

from io_mesh_w3d.common.utils.mesh_export import *
from io_mesh_w3d.common.utils.box_export import *
from tests.common.helpers.collision_box import *
from tests.common.helpers.hlod import *
from tests.common.helpers.hierarchy import *
from tests.utils import *


class TestBoxExportUtils(TestCase):
    def test_box_export(self):
        box = bpy.data.meshes.new('box')

        b_mesh = bmesh.new()
        bmesh.ops.create_cube(b_mesh, size=1)
        b_mesh.to_mesh(box)

        prepare_bmesh(self, box)

        box_object = bpy.data.objects.new(box.name, box)
        box_object.data.object_type = 'BOX'

        link_object_to_active_scene(box_object, bpy.context.scene.collection)

        boxes = retrieve_boxes('anything')

        self.assertEqual(1, len(boxes))
        actual = boxes[0]

        compare_vectors(self, Vector((0, 0, 0)), actual.center)
        compare_vectors(self, Vector((1, 1, 1)), actual.extend)
