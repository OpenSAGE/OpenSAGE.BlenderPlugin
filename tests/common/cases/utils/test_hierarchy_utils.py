# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from tests.utils import TestCase
from mathutils import Vector
from os.path import dirname as up
from io_mesh_w3d.import_utils import *
from tests.common.helpers.hierarchy import *
from tests.common.helpers.hlod import *
from tests.common.helpers.mesh import *
from io_mesh_w3d.common.utils.hierarchy_import import *
from io_mesh_w3d.common.utils.hierarchy_export import *


def add_bone(armature, name):
        bone = armature.edit_bones.new(name)
        bone.head = Vector((0.0, 0.0, 0.0))
        bone.tail = Vector((0.0, 1.0, 0.0))


class TestHierarchyUtils(TestCase):
    def test_hierarchy_roundtrip(self):
        hierarchy = get_hierarchy()
        hlod = get_hlod()
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK'),
            get_mesh(name='PICK')]

        create_data(self, meshes, hlod, hierarchy)

        actual_hiera, rig = retrieve_hierarchy(self, 'containerName')
        hierarchy.pivot_fixups = []  # roundtrip not supported
        compare_hierarchies(self, hierarchy, actual_hiera)

    def test_hierarchy_only_roundtrip(self):
        hierarchy = get_hierarchy()

        create_data(self, [], None, hierarchy)

        actual_hiera, rig = retrieve_hierarchy(self, 'containerName')
        hierarchy.pivot_fixups = []  # roundtrip not supported
        compare_hierarchies(self, hierarchy, actual_hiera)

    def test_hierarchy_roundtrip_pivot_order_is_correct(self):
        hierarchy = get_hierarchy()
        hierarchy.pivots = [
            get_roottransform(),
            get_hierarchy_pivot(name='bone_chassis01', parent=0),
            get_hierarchy_pivot(name='bone_treadlf', parent=1),
            get_hierarchy_pivot(name='bone_treadlr', parent=1),
            get_hierarchy_pivot(name='bone_treadrf', parent=1),
            get_hierarchy_pivot(name='bone_treadrr', parent=1),
            get_hierarchy_pivot(name='bone_turret', parent=1),
            get_hierarchy_pivot(name='bone_rocketpod', parent=6),
            get_hierarchy_pivot(name='turret01', parent=7),
            get_hierarchy_pivot(name='rocketlaunch01', parent=8),
            get_hierarchy_pivot(name='turret02', parent=7),
            get_hierarchy_pivot(name='rocketlaunch02', parent=10),
            get_hierarchy_pivot(name='bone_rails', parent=6),
            get_hierarchy_pivot(name='bone_barrel_01', parent=12),
            get_hierarchy_pivot(name='muzzlefx01', parent=13),
            get_hierarchy_pivot(name='muzzleflash_01', parent=13),
            get_hierarchy_pivot(name='muzzleflash_02', parent=13),
            get_hierarchy_pivot(name='ugrail_01', parent=13),
            get_hierarchy_pivot(name='bone_barrel_02', parent=12),
            get_hierarchy_pivot(name='muzzlefx02', parent=18),
            get_hierarchy_pivot(name='ugrail_02', parent=18),
            get_hierarchy_pivot(name='fxtrackslf', parent=1),
            get_hierarchy_pivot(name='fxtrackslr', parent=1),
            get_hierarchy_pivot(name='fxtracksrf', parent=1),
            get_hierarchy_pivot(name='fxtracksrr', parent=1)]
        hierarchy.header.num_pivots = len(hierarchy.pivots)

        create_data(self, [], None, hierarchy, [])

        actual_hiera, rig = retrieve_hierarchy(self, 'containerName')
        hierarchy.pivot_fixups = []  # roundtrip not supported
        compare_hierarchies(self, hierarchy, actual_hiera)

    def test_troll_roundtrip(self):
        hlod = get_hlod()
        hlod.header.hierarchy_name = 'troll_skl'
        hlod.lod_arrays[0].sub_objects = [
            get_hlod_sub_object(bone=32, name='troll_skn.rock'),
            get_hlod_sub_object(bone=0, name='troll_skn.troll_mesh'),
            get_hlod_sub_object(bone=24, name='troll_skn.trunk01')]
        hlod.lod_arrays[0].header.model_count = len(hlod.lod_arrays[0].sub_objects)

        hierarchy = get_hierarchy()
        hierarchy.pivot_fixups = []  # roundtrip not supported
        hierarchy.header.name = 'troll_skl'
        hierarchy.pivots = [
            get_roottransform(),
            get_hierarchy_pivot(name='b_spine', parent=0),
            get_hierarchy_pivot(name='bat_spine1', parent=1),
            get_hierarchy_pivot(name='bat_head', parent=2),
            get_hierarchy_pivot(name='b_jaw', parent=3),
            get_hierarchy_pivot(name='bat_uarml', parent=2),
            get_hierarchy_pivot(name='bat_farml', parent=5),
            get_hierarchy_pivot(name='bat_handl', parent=6),
            get_hierarchy_pivot(name='b_thumbl1', parent=7),
            get_hierarchy_pivot(name='b_thumbl2', parent=8),
            get_hierarchy_pivot(name='b_pointerl1', parent=7),
            get_hierarchy_pivot(name='b_pointerl2', parent=10),
            get_hierarchy_pivot(name='b_pinkyl1', parent=7),
            get_hierarchy_pivot(name='b_pinkyl2', parent=12),
            get_hierarchy_pivot(name='bat_uarmr', parent=2),
            get_hierarchy_pivot(name='bat_farmr', parent=14),
            get_hierarchy_pivot(name='bat_handr', parent=15),
            get_hierarchy_pivot(name='b_pinkyr1', parent=16),
            get_hierarchy_pivot(name='b_pinkyr2', parent=17),
            get_hierarchy_pivot(name='b_pointerr1', parent=16),
            get_hierarchy_pivot(name='b_pointerr2', parent=19),
            get_hierarchy_pivot(name='b_thumbr1', parent=16),
            get_hierarchy_pivot(name='b_thumbr2', parent=21),
            get_hierarchy_pivot(name='firepoint01', parent=16),
            get_hierarchy_pivot(name='trunk01', parent=16),
            get_hierarchy_pivot(name='b_pelvis', parent=0),
            get_hierarchy_pivot(name='bat_thighl', parent=25),
            get_hierarchy_pivot(name='bat_calfl', parent=26),
            get_hierarchy_pivot(name='b_footl', parent=27),
            get_hierarchy_pivot(name='bat_thighr', parent=25),
            get_hierarchy_pivot(name='bat_calfr', parent=29),
            get_hierarchy_pivot(name='b_footr', parent=30),
            get_hierarchy_pivot(name='rock', parent=0)]
        hierarchy.header.num_pivots = len(hierarchy.pivots)

        meshes = [get_mesh(name='rock'),
                  get_mesh(name='troll_mesh', skin=True),
                  get_mesh(name='trunk01')]

        create_data(self, meshes, hlod, hierarchy)

        actual_hiera, rig = retrieve_hierarchy(self, 'troll_skn')
        compare_hierarchies(self, hierarchy, actual_hiera)

    def test_get_or_create_skeleton_is_case_insensitive(self):
        hierarchy = get_hierarchy('TROLL_SKL')

        create_data(self, [], None, hierarchy)

        hierarchy.header.name = 'troll_skl'
        rig = get_or_create_skeleton(hierarchy, bpy.context.scene.collection)

        self.assertIsNotNone(rig)
        self.assertTrue('TROLL_SKL' in bpy.data.armatures)
        self.assertEqual(1, len(bpy.data.armatures))

    def test_retrieve_hierarchy_creates_pivots_for_meshes_without_parent_bone(self):
        collection = get_collection()

        create_mesh(self, get_mesh('mesh1'), collection)
        create_mesh(self, get_mesh('mesh2'), collection)
        create_mesh(self, get_mesh('mesh3'), collection)
        create_mesh(self, get_mesh('mesh4'), collection)

        hierarchy, _ = retrieve_hierarchy(self, 'lorem ipsum')

        self.assertEqual(5, len(hierarchy.pivots))

        self.assertEqual('mesh1', hierarchy.pivots[1].name)
        self.assertEqual('mesh2', hierarchy.pivots[2].name)
        self.assertEqual('mesh3', hierarchy.pivots[3].name)
        self.assertEqual('mesh4', hierarchy.pivots[4].name)

    def test_retrieve_hierarchy_creates_pivots_with_correct_parent_id_for_parented_meshes(self):
        collection = get_collection()

        create_mesh(self, get_mesh('mesh1'), collection)
        create_mesh(self, get_mesh('mesh2'), collection)
        create_mesh(self, get_mesh('mesh3'), collection)
        create_mesh(self, get_mesh('mesh4'), collection)

        bpy.data.objects['mesh2'].parent = bpy.data.objects['mesh1']
        bpy.data.objects['mesh3'].parent = bpy.data.objects['mesh2']
        bpy.data.objects['mesh4'].parent = bpy.data.objects['mesh1']

        hierarchy, _ = retrieve_hierarchy(self, 'lorem ipsum')

        self.assertEqual(5, len(hierarchy.pivots))

        self.assertEqual('mesh1', hierarchy.pivots[1].name)
        self.assertEqual(0, hierarchy.pivots[1].parent_id)
        self.assertEqual('mesh2', hierarchy.pivots[2].name)
        self.assertEqual(1, hierarchy.pivots[2].parent_id)
        self.assertEqual('mesh3', hierarchy.pivots[3].name)
        self.assertEqual(2, hierarchy.pivots[3].parent_id)
        self.assertEqual('mesh4', hierarchy.pivots[4].name)
        self.assertEqual(1, hierarchy.pivots[4].parent_id)

    def test_retrieve_hierarchy_creates_pivots_with_correct_parent_id_for_parented_meshes_inversed_order(self):
        collection = get_collection()

        create_mesh(self, get_mesh('mesh1'), collection)
        create_mesh(self, get_mesh('mesh2'), collection)
        create_mesh(self, get_mesh('mesh3'), collection)
        create_mesh(self, get_mesh('mesh4'), collection)

        bpy.data.objects['mesh1'].parent = bpy.data.objects['mesh4']
        bpy.data.objects['mesh2'].parent = bpy.data.objects['mesh3']
        bpy.data.objects['mesh3'].parent = bpy.data.objects['mesh4']

        hierarchy, _ = retrieve_hierarchy(self, 'lorem ipsum')

        self.assertEqual(5, len(hierarchy.pivots))

        self.assertEqual('mesh4', hierarchy.pivots[1].name)
        self.assertEqual(0, hierarchy.pivots[1].parent_id)
        self.assertEqual('mesh1', hierarchy.pivots[2].name)
        self.assertEqual(1, hierarchy.pivots[2].parent_id)
        self.assertEqual('mesh3', hierarchy.pivots[3].name)
        self.assertEqual(1, hierarchy.pivots[3].parent_id)
        self.assertEqual('mesh2', hierarchy.pivots[4].name)
        self.assertEqual(3, hierarchy.pivots[4].parent_id)

    def test_retrieve_hierarchy_creates_pivots_with_correct_parent_id_for_parented_meshes_where_root_mesh_has_parent_bone(
            self):
        collection = get_collection()

        armature = bpy.data.armatures.new('armature')
        rig = bpy.data.objects.new('skele', armature)
        collection.objects.link(rig)
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode='EDIT')

        bone = armature.edit_bones.new('bone1')
        bone.head = Vector((0.0, 0.0, 0.0))
        bone.tail = Vector((0.0, 1.0, 0.0))
        bone2 = armature.edit_bones.new('mesh1')
        bone2.head = Vector((0.0, 0.0, 0.0))
        bone2.tail = Vector((0.0, 1.0, 0.0))
        bone2.parent = bone

        if rig.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        create_mesh(self, get_mesh('mesh1'), collection)
        create_mesh(self, get_mesh('mesh2'), collection)
        create_mesh(self, get_mesh('mesh3'), collection)
        create_mesh(self, get_mesh('mesh4'), collection)

        bpy.data.objects['mesh1'].parent_bone = 'mesh1'
        bpy.data.objects['mesh2'].parent = bpy.data.objects['mesh1']
        bpy.data.objects['mesh3'].parent = bpy.data.objects['mesh2']
        bpy.data.objects['mesh4'].parent = bpy.data.objects['mesh1']

        hierarchy, _ = retrieve_hierarchy(self, 'lorem ipsum')

        self.assertEqual(6, len(hierarchy.pivots))

        self.assertEqual('ROOTTRANSFORM', hierarchy.pivots[0].name)
        self.assertEqual(-1, hierarchy.pivots[0].parent_id)
        self.assertEqual('bone1', hierarchy.pivots[1].name)
        self.assertEqual(0, hierarchy.pivots[1].parent_id)
        self.assertEqual('mesh1', hierarchy.pivots[2].name)
        self.assertEqual(1, hierarchy.pivots[2].parent_id)
        self.assertEqual('mesh2', hierarchy.pivots[3].name)
        self.assertEqual(2, hierarchy.pivots[3].parent_id)
        self.assertEqual('mesh3', hierarchy.pivots[4].name)
        self.assertEqual(3, hierarchy.pivots[4].parent_id)
        self.assertEqual('mesh4', hierarchy.pivots[5].name)
        self.assertEqual(2, hierarchy.pivots[5].parent_id)


    def test_retrieve_hierarchy_creates_tree_of_bones(self):
        collection = get_collection()

        self.loadBlend(up(up(up(self.relpath()))) + '/testfiles/unordered_bones.blend')

        print('#############################################################')

        hierarchy, _ = retrieve_hierarchy(self, 'lorem ipsum')

        for piv in hierarchy.pivots:
            print(piv.name)

        self.assertEqual(11, len(hierarchy.pivots))

        self.assertEqual('ROOTTRANSFORM', hierarchy.pivots[0].name)
        self.assertEqual(-1, hierarchy.pivots[0].parent_id)

        self.assertEqual('Location', hierarchy.pivots[1].name)
        self.assertEqual(0, hierarchy.pivots[1].parent_id)
        self.assertEqual('fx_damage_3', hierarchy.pivots[2].name)
        self.assertEqual(1, hierarchy.pivots[2].parent_id)
        self.assertEqual('tp_2', hierarchy.pivots[3].name)
        self.assertEqual(0, hierarchy.pivots[3].parent_id)
        self.assertEqual('turret_2', hierarchy.pivots[4].name)
        self.assertEqual(3, hierarchy.pivots[4].parent_id)
        self.assertEqual('barrel_2', hierarchy.pivots[5].name)
        self.assertEqual(4, hierarchy.pivots[5].parent_id)
        self.assertEqual('fx_damage_2', hierarchy.pivots[6].name)
        self.assertEqual(4, hierarchy.pivots[6].parent_id)
        self.assertEqual('tp_1', hierarchy.pivots[7].name)
        self.assertEqual(0, hierarchy.pivots[7].parent_id)
        self.assertEqual('turret_1', hierarchy.pivots[8].name)
        self.assertEqual(7, hierarchy.pivots[8].parent_id)
        self.assertEqual('barrel_1', hierarchy.pivots[9].name)
        self.assertEqual(8, hierarchy.pivots[9].parent_id)
        self.assertEqual('fx_damage_1', hierarchy.pivots[10].name)
        self.assertEqual(8, hierarchy.pivots[10].parent_id)
