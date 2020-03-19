# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct
from tests.utils import TestCase

from io_mesh_w3d.import_utils import *
from tests.common.helpers.hierarchy import *
from tests.common.helpers.hlod import *
from tests.common.helpers.mesh import *
from io_mesh_w3d.common.utils.hierarchy_import import *
from io_mesh_w3d.common.utils.hierarchy_export import *


class TestHierarchyUtils(TestCase):
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

        (actual_hiera, rig) = retrieve_hierarchy(self, 'troll_skn')
        compare_hierarchies(self, hierarchy, actual_hiera)

    def test_retrieve_hierarchy_case_insensitive(self):
        hierarchy = get_hierarchy('TROLL_SKL')

        create_data(self, [], None, hierarchy)

        hierarchy.header.name = 'troll_skl'
        rig = get_or_create_skeleton(None, hierarchy, None)

        self.assertIsNotNone(rig)