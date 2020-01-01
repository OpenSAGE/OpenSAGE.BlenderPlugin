# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from shutil import copyfile
import os

from tests.utils import TestCase
from io_mesh_w3d.import_utils_w3d import *
from io_mesh_w3d.export_utils_w3d import *
from tests.helpers.w3d_mesh import *
from tests.helpers.w3d_material_pass import *
from tests.helpers.w3d_material_info import *
from tests.helpers.w3d_vertex_material import *
from tests.helpers.w3d_shader_material import *
from tests.helpers.w3d_shader import *
from tests.helpers.w3d_box import *
from tests.helpers.w3d_hierarchy import *
from tests.helpers.w3d_hlod import *
from tests.helpers.w3d_animation import *
from tests.helpers.w3d_compressed_animation import *


class TestUtils(TestCase):
    def test_vertex_material_roundtrip(self):
        mesh = get_mesh()

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        for source in mesh.vert_materials:
            (material, _) = create_material_from_vertex_material(
                self, mesh, source)
            actual = retrieve_vertex_material(material)
            compare_vertex_materials(self, source, actual)

    def test_shader_material_roundtrip(self):
        mesh = get_mesh()

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        for source in mesh.shader_materials:
            (material, _) = create_material_from_shader_material(
                self, mesh, source)
            principled = retrieve_principled_bsdf(material)
            actual = retrieve_shader_material(material, principled)
            compare_shader_materials(self, source, actual)

    def test_shader_roundtrip(self):
        mesh = get_mesh()

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        (material, _) = create_material_from_vertex_material(
            self, mesh, mesh.vert_materials[0])
        expected = mesh.shaders[0]
        set_shader_properties(material, expected)
        actual = retrieve_shader(material)
        compare_shaders(self, expected, actual)

    def test_box_roundtrip(self):
        expected = get_box()
        hlod = get_hlod()
        hierarchy = get_hierarchy()
        create_box(expected, hlod, None, None, get_collection(None))

        boxes = retrieve_boxes(hlod, hierarchy)
        compare_boxes(self, expected, boxes[0])

    def test_hierarchy_roundtrip(self):
        print("#####################  hierarchy test")
        expected = get_hierarchy()
        hlod = get_hlod()
        mesh_structs = [
            get_mesh(name="sword"),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="BAT_SHIELD"),
            get_mesh(name="PICK")]

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        coll = get_collection(hlod)

        meshes = []
        for mesh_struct in mesh_structs:
            meshes.append(create_mesh(self, mesh_struct, expected, coll))

        rig = get_or_create_skeleton(hlod, expected, coll)

        for i, mesh_struct in enumerate(mesh_structs):
            rig_mesh(mesh_struct, meshes[i], expected, hlod, rig)

        expected.pivot_fixups = []  # not supported
        (actual, rig) = retrieve_hierarchy("containerName")

        for pivot in actual.pivots:
            print(pivot.name)
        compare_hierarchies(self, expected, actual)

    def test_hlod_roundtrip(self):
        hlod = get_hlod()
        box = get_box()
        hierarchy = get_hierarchy()

        mesh_structs = [
            get_mesh(name="sword"),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="BAT_SHIELD"),
            get_mesh(name="PICK")]

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        coll = get_collection(hlod)

        meshes = []
        for mesh_struct in mesh_structs:
            meshes.append(create_mesh(self, mesh_struct, hierarchy, coll))

        rig = get_or_create_skeleton(hlod, hierarchy, coll)
        create_box(box, hlod, hierarchy, rig, coll)

        for i, mesh_struct in enumerate(mesh_structs):
            rig_mesh(mesh_struct, meshes[i], hierarchy, hlod, rig)

        actual = create_hlod("containerName", hierarchy.header.name)
        retrieve_boxes(actual, hierarchy)
        retrieve_meshes(self, hierarchy, rig, actual, "containerName")
        compare_hlods(self, hlod, actual)

    def test_bone_is_created_if_referenced_by_subObject_but_also_child_bones_roundtrip(self):
        # TODO: simplify this test
        hlod = get_hlod()
        box = get_box()
        hierarchy = get_hierarchy()
        hierarchy.pivot_fixups = []
        hierarchy.pivots = [get_roottransform()]

        hierarchy.pivots.append(get_hierarchy_pivot("waist", 0))
        hierarchy.pivots.append(get_hierarchy_pivot("hip", 1))
        hierarchy.pivots.append(get_hierarchy_pivot("shoulderl", 2))
        hierarchy.pivots.append(get_hierarchy_pivot("arml", 3))
        hierarchy.pivots.append(get_hierarchy_pivot("BAT_SHIELD", 4))
        hierarchy.pivots.append(get_hierarchy_pivot("armr", 3))
        hierarchy.pivots.append(get_hierarchy_pivot("sword", 0))

        hierarchy.header.num_pivots = len(hierarchy.pivots)

        array = HLodArray(
            header=get_hlod_array_header(),
            sub_objects=[])

        array.sub_objects.append(get_hlod_sub_object(
            bone=3, name="containerName.BOUNDINGBOX"))
        array.sub_objects.append(get_hlod_sub_object(
            bone=7, name="containerName.sword"))
        array.sub_objects.append(get_hlod_sub_object(
            bone=0, name="containerName.soldier"))
        array.sub_objects.append(get_hlod_sub_object(
            bone=5, name="containerName.BAT_SHIELD"))
        array.sub_objects.append(get_hlod_sub_object(
            bone=0, name="containerName.PICK"))

        array.header.model_count = len(array.sub_objects)

        hlod.lod_array = array

        mesh_structs = [
            get_mesh(name="sword"),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="BAT_SHIELD"),
            get_mesh(name="PICK")]

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        coll = get_collection(hlod)

        meshes = []
        for mesh_struct in mesh_structs:
            meshes.append(create_mesh(self, mesh_struct, hierarchy, coll))

        rig = get_or_create_skeleton(hlod, hierarchy, coll)
        create_box(box, hlod, hierarchy, rig, coll)

        self.assertEqual(5, len(rig.data.bones))

        for i, mesh_struct in enumerate(mesh_structs):
            rig_mesh(mesh_struct, meshes[i], hierarchy, hlod, rig)

        actual = create_hlod("containerName", hierarchy.header.name)

        retrieve_boxes(actual, hierarchy)
        retrieve_meshes(self, hierarchy, rig, actual, "containerName")
        compare_hlods(self, hlod, actual)
        (actual_hiera, rig) = retrieve_hierarchy("containerName")
        compare_hierarchies(self, hierarchy, actual_hiera)

    def test_no_bone_is_created_if_referenced_by_subObject_and_only_child_pivots_roundtrip(self):
        # TODO: simplify this test
        hlod = get_hlod(hierarchy_name="containerName")
        box = get_box()
        hierarchy = get_hierarchy("containerName")
        hierarchy.pivot_fixups = []
        hierarchy.pivots = [get_roottransform()]

        hierarchy.pivots.append(get_hierarchy_pivot("main", 0))
        hierarchy.pivots.append(get_hierarchy_pivot("left", 1))
        hierarchy.pivots.append(get_hierarchy_pivot("left2", 2))
        hierarchy.pivots.append(get_hierarchy_pivot("right", 1))
        hierarchy.pivots.append(get_hierarchy_pivot("right2", 4))

        hierarchy.header.num_pivots = len(hierarchy.pivots)

        array = HLodArray(
            header=get_hlod_array_header(),
            sub_objects=[])

        array.sub_objects.append(get_hlod_sub_object(
            bone=0, name="containerName.BOUNDINGBOX"))
        array.sub_objects.append(get_hlod_sub_object(
            bone=1, name="containerName.main"))
        array.sub_objects.append(get_hlod_sub_object(
            bone=2, name="containerName.left"))
        array.sub_objects.append(get_hlod_sub_object(
            bone=4, name="containerName.right"))
        array.sub_objects.append(get_hlod_sub_object(
            bone=3, name="containerName.left2"))
        array.sub_objects.append(get_hlod_sub_object(
            bone=5, name="containerName.right2"))

        array.header.model_count = len(array.sub_objects)

        hlod.lod_array = array

        mesh_structs = [
            get_mesh(name="main"),
            get_mesh(name="left"),
            get_mesh(name="right"),
            get_mesh(name="left2"),
            get_mesh(name="right2")]

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        coll = get_collection(hlod)

        meshes = []
        for mesh_struct in mesh_structs:
            meshes.append(create_mesh(self, mesh_struct, hierarchy, coll))

        rig = get_or_create_skeleton(hlod, hierarchy, coll)
        create_box(box, hlod, hierarchy, rig, coll)

        self.assertIsNone(rig)

        for i, mesh_struct in enumerate(mesh_structs):
            rig_mesh(mesh_struct, meshes[i], hierarchy, hlod, rig)

        (actual_hiera, rig) = retrieve_hierarchy("containerName")
        compare_hierarchies(self, hierarchy, actual_hiera)

        actual_hlod = create_hlod("containerName", actual_hiera.header.name)
        retrieve_boxes(actual_hlod, actual_hiera)
        retrieve_meshes(self, actual_hiera, rig, actual_hlod, "containerName")
        compare_hlods(self, hlod, actual_hlod)

    def test_bone_is_created_if_referenced_by_subObject_but_starts_with_B__roundtrip(self):
        hlod = get_hlod()
        hierarchy = get_hierarchy()
        hierarchy.pivot_fixups = []
        hierarchy.pivots = [get_roottransform()]

        hierarchy.pivots.append(get_hierarchy_pivot("B_MAIN", 0))
        hierarchy.header.num_pivots = len(hierarchy.pivots)

        array = HLodArray(
            header=get_hlod_array_header(),
            sub_objects=[])

        array.sub_objects.append(get_hlod_sub_object(
            bone=1, name="containerName.V_MAIN"))
        array.header.model_count = len(array.sub_objects)

        hlod.lod_array = array

        mesh_structs = [
            get_mesh(name="V_MAIN")]

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        coll = get_collection(hlod)

        meshes = []
        for mesh_struct in mesh_structs:
            meshes.append(create_mesh(self, mesh_struct, hierarchy, coll))

        rig = get_or_create_skeleton(hlod, hierarchy, coll)

        self.assertEqual(1, len(rig.data.bones))

        for i, mesh_struct in enumerate(mesh_structs):
            rig_mesh(mesh_struct, meshes[i], hierarchy, hlod, rig)

        (actual_hiera, rig) = retrieve_hierarchy("containerName")
        compare_hierarchies(self, hierarchy, actual_hiera)

        actual_hlod = create_hlod("containerName", actual_hiera.header.name)
        retrieve_meshes(self, hierarchy, rig, actual_hlod, "containerName")
        compare_hlods(self, hlod, actual_hlod)

    def test_PICK_mesh_roundtrip(self):
        hlod = get_hlod(hierarchy_name="containerName")
        hlod.lod_array.sub_objects = [
            get_hlod_sub_object(bone=1, name="containerName.building"),
            get_hlod_sub_object(bone=0, name="containerName.PICK")]
        hlod.lod_array.header.model_count = len(hlod.lod_array.sub_objects)

        mesh_structs = [
            get_mesh(name="building"),
            get_mesh(name="PICK")]

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        hierarchy = get_hierarchy("containerName")
        hierarchy.pivot_fixups = []
        hierarchy.pivots = [
            get_roottransform(),
            get_hierarchy_pivot("building", 0)]
        hierarchy.header.num_pivots = len(hierarchy.pivots)

        coll = get_collection(hlod)

        meshes = []
        for mesh_struct in mesh_structs:
            meshes.append(create_mesh(self, mesh_struct, hierarchy, coll))

        rig = get_or_create_skeleton(hlod, hierarchy, coll)

        for i, mesh_struct in enumerate(mesh_structs):
            rig_mesh(mesh_struct, meshes[i], hierarchy, hlod, rig)

        (actual_hiera, rig) = retrieve_hierarchy("containerName")

        compare_hierarchies(self, hierarchy, actual_hiera)

        actual_hlod = create_hlod("containerName", hierarchy.header.name)
        retrieve_boxes(actual_hlod, actual_hiera)
        actual_mesh_structs = retrieve_meshes(
            self, actual_hiera, rig, actual_hlod, "containerName")
        compare_hlods(self, hlod, actual_hlod)

        self.assertEqual(len(mesh_structs), len(actual_mesh_structs))

    def test_meshes_roundtrip(self):
        hlod = get_hlod()
        box = get_box()
        hierarchy = get_hierarchy()
        expecteds = [
            get_mesh(name="sword"),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="BAT_SHIELD", shader_mats=True),
            get_mesh(name="pike")]

        coll = get_collection(hlod)
        rig = get_or_create_skeleton(hlod, hierarchy, coll)
        create_box(box, hlod, hierarchy, rig, coll)

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture_nrm.dds")

        meshes = []
        for mesh_struct in expecteds:
            meshes.append(create_mesh(self, mesh_struct, hierarchy, coll))

        rig = get_or_create_skeleton(hlod, hierarchy, coll)

        for i, mesh_struct in enumerate(expecteds):
            rig_mesh(mesh_struct, meshes[i], hierarchy, hlod, rig)

        hlod = create_hlod("containerName", hierarchy.header.name)
        retrieve_boxes(hlod, hierarchy)
        actuals = retrieve_meshes(
            self, hierarchy, rig, hlod, "containerName")

        self.assertEqual(len(expecteds), len(actuals))
        for i, expected in enumerate(expecteds):
            compare_meshes(self, expected, actuals[i])


    def test_prelit_meshes_roundtrip(self):
        hlod = get_hlod()
        box = get_box()
        hierarchy = get_hierarchy()
        expecteds = [get_mesh(name="sword", prelit=True)]

        coll = get_collection(hlod)
        rig = get_or_create_skeleton(hlod, hierarchy, coll)
        create_box(box, hlod, hierarchy, rig, coll)

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        meshes = []
        for mesh_struct in expecteds:
            meshes.append(create_mesh(self, mesh_struct, hierarchy, coll))

        rig = get_or_create_skeleton(hlod, hierarchy, coll)

        for i, mesh_struct in enumerate(expecteds):
            rig_mesh(mesh_struct, meshes[i], hierarchy, hlod, rig)

        hlod = create_hlod("containerName", hierarchy.header.name)
        retrieve_boxes(hlod, hierarchy)
        actuals = retrieve_meshes(
            self, hierarchy, rig, hlod, "containerName")

        self.assertEqual(len(expecteds), len(actuals))
        #for i, expected in enumerate(expecteds):
        #    compare_meshes(self, expected, actuals[i])
        # prelit roundtrip not supported yet
        # need a way to reference a material to its prelit chunk


    def test_animation_roundtrip(self):
        expected = get_animation()
        hlod = get_hlod()
        box = get_box()
        hierarchy = get_hierarchy()
        hierarchy.pivot_fixups = []

        mesh_structs = [
            get_mesh(name="sword"),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="BAT_SHIELD"),
            get_mesh(name="PICK")]

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        coll = get_collection(hlod)

        meshes = []
        for mesh_struct in mesh_structs:
            meshes.append(create_mesh(self, mesh_struct, hierarchy, coll))

        rig = get_or_create_skeleton(hlod, hierarchy, coll)
        create_box(box, hlod, hierarchy, rig, coll)

        for i, mesh_struct in enumerate(mesh_structs):
            rig_mesh(mesh_struct, meshes[i], hierarchy, hlod, rig)

        create_animation(rig, expected, hierarchy)

        (actual_hiera, rig) = retrieve_hierarchy("containerName")
        compare_hierarchies(self, hierarchy, actual_hiera)

        actual_hlod = create_hlod("containerName", actual_hiera.header.name)
        retrieve_boxes(actual_hlod, actual_hiera)
        actual_mesh_structs = retrieve_meshes(
            self, actual_hiera, rig, actual_hlod, "containerName")

        compare_hlods(self, hlod, actual_hlod)

        self.assertEqual(len(mesh_structs), len(actual_mesh_structs))
        for i, mesh in enumerate(mesh_structs):
            compare_meshes(self, mesh, actual_mesh_structs[i])

        actual = retrieve_animation(
            expected.header.name, hierarchy, rig, timecoded=False)
        compare_animations(self, expected, actual)

    def test_compressed_animation_roundtrip(self):
        expected = get_compressed_animation(
            flavor=0,
            bit_channels=False,
            motion_tc=False,
            motion_ad4=False,
            motion_ad8=False,
            random_interpolation=False)
        hlod = get_hlod()
        box = get_box()
        hierarchy = get_hierarchy()
        hierarchy.pivot_fixups = []
        mesh_structs = [
            get_mesh(name="sword"),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="BAT_SHIELD"),
            get_mesh(name="PICK")]

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        coll = get_collection(hlod)

        meshes = []
        for mesh_struct in mesh_structs:
            meshes.append(create_mesh(self, mesh_struct, hierarchy, coll))

        rig = get_or_create_skeleton(hlod, hierarchy, coll)
        create_box(box, hlod, hierarchy, rig, coll)

        for i, mesh_struct in enumerate(mesh_structs):
            rig_mesh(mesh_struct, meshes[i], hierarchy, hlod, rig)

        create_animation(rig, expected, hierarchy, compressed=True)

        (actual_hiera, rig) = retrieve_hierarchy("containerName")
        compare_hierarchies(self, hierarchy, actual_hiera)

        actual_hlod = create_hlod("containerName", actual_hiera.header.name)
        retrieve_boxes(actual_hlod, actual_hiera)
        actual_mesh_structs = retrieve_meshes(
            self, actual_hiera, rig, actual_hlod, "containerName")

        compare_hlods(self, hlod, actual_hlod)

        self.assertEqual(len(mesh_structs), len(actual_mesh_structs))
        for i, mesh in enumerate(mesh_structs):
            compare_meshes(self, mesh, actual_mesh_structs[i])

        actual = retrieve_animation(
            "containerName", hierarchy, rig, timecoded=True)
        compare_compressed_animations(self, expected, actual)
