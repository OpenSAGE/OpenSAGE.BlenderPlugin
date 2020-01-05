# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.utils import *
from shutil import copyfile
import os

from tests.shared.helpers.hierarchy import *
from tests.shared.helpers.collision_box import *

from io_mesh_w3d.import_utils import *
from io_mesh_w3d.export_utils import *
from tests.w3d.helpers.mesh import *
from tests.w3d.helpers.mesh_structs.material_pass import *
from tests.w3d.helpers.mesh_structs.material_info import *
from tests.w3d.helpers.mesh_structs.vertex_material import *
from tests.w3d.helpers.mesh_structs.shader_material import *
from tests.w3d.helpers.mesh_structs.shader import *
from tests.w3d.helpers.hlod import *
from tests.w3d.helpers.animation import *
from tests.w3d.helpers.compressed_animation import *


class TestUtils(TestCase):
    def test_vertex_material_roundtrip(self):
        mesh = get_mesh()

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        for source in mesh.vert_materials:
            (material, _) = create_material_from_vertex_material(
                self, mesh, source)
            actual = retrieve_vertex_material(material)
            compare_vertex_materials(self, source, actual)

    def test_vertex_material_no_attributes_roundtrip(self):
        mesh = get_mesh()

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        for source in mesh.vert_materials:
            source.vm_info.attributes = 0
            (material, _) = create_material_from_vertex_material(
                self, mesh, source)
            actual = retrieve_vertex_material(material)
            compare_vertex_materials(self, source, actual)

    def test_shader_material_roundtrip(self):
        mesh = get_mesh()

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        for source in mesh.shader_materials:
            (material, _) = create_material_from_shader_material(
                self, mesh, source)
            principled = retrieve_principled_bsdf(material)
            actual = retrieve_shader_material(material, principled)
            compare_shader_materials(self, source, actual)

    def test_shader_material_minimal_roundtrip(self):
        mesh = get_mesh()

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        for source in mesh.shader_materials:
            source.properties = []

            (material, _) = create_material_from_shader_material(
                self, mesh, source)
            principled = retrieve_principled_bsdf(material)
            actual = retrieve_shader_material(material, principled)
            source.properties = get_shader_material_properties_minimal()
            compare_shader_materials(self, source, actual)

    def test_shader_roundtrip(self):
        mesh = get_mesh()

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        (material, _) = create_material_from_vertex_material(
            self, mesh, mesh.vert_materials[0])
        expected = mesh.shaders[0]
        set_shader_properties(material, expected)
        actual = retrieve_shader(material)
        compare_shaders(self, expected, actual)

    def test_boxes_roundtrip(self):
        hlod = get_hlod()
        hlod.lod_arrays[0].sub_objects.append(
            get_hlod_sub_object(bone=1, name="containerName.WORLDBOX"))
        hierarchy = get_hierarchy()
        meshes = []
        boxes = [get_collision_box(), get_collision_box("containerName.WORLDBOX")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        create_data(self, meshes, hlod, hierarchy, boxes)

        self.compare_data([], None, None, boxes)

    def test_hierarchy_roundtrip(self):
        hierarchy = get_hierarchy()
        hlod = get_hlod()
        boxes = [get_collision_box()]
        meshes = [
            get_mesh(name="sword", skin=True),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="TRUNK"),
            get_mesh(name="PICK")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        create_data(self, meshes, hlod, hierarchy, boxes)

        self.compare_data([], None, hierarchy)

    def test_too_many_hierarchies_roundtrip(self):
        hierarchy = get_hierarchy()
        hierarchy2 = get_hierarchy(name="TestHierarchy2")
        hlod = get_hlod()
        boxes = [get_collision_box()]
        meshes = [
            get_mesh(name="sword", skin=True),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="TRUNK"),
            get_mesh(name="PICK")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")


        create_data(self, meshes, hlod, hierarchy, boxes)
        coll = get_collection(hlod)
        rig2 = get_or_create_skeleton(hlod, hierarchy2, coll)

        self.assertEqual(2, len(get_objects('ARMATURE')))

        (actual_hiera, rig) = retrieve_hierarchy(self, "containerName")
        self.assertIsNone(actual_hiera)
        self.assertIsNone(rig)

    def test_hlod_roundtrip(self):
        hlod = get_hlod()
        boxes = [get_collision_box()]
        hierarchy = get_hierarchy()

        meshes = [
            get_mesh(name="sword", skin=True),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="TRUNK"),
            get_mesh(name="PICK")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        create_data(self, meshes, hlod, hierarchy, boxes)

        self.compare_data([], hlod, hierarchy)

    def test_hlod_4_levels_roundtrip(self):
        hlod = get_hlod_4_levels()
        hlod.header.hierarchy_name = "containerName"
        hierarchy = get_hierarchy()
        hierarchy.header.name = "containerName"
        hierarchy.pivots = [
            get_roottransform(),
            get_hierarchy_pivot(name="parent", parent=0),
            get_hierarchy_pivot(name="child", parent=1)]
        hierarchy.header.num_pivots = len(hierarchy.pivots)

        meshes = [
            get_mesh(name="mesh1"),
            get_mesh(name="mesh2"),
            get_mesh(name="mesh3"),

            get_mesh(name="mesh1_1"),
            get_mesh(name="mesh2_1"),
            get_mesh(name="mesh3_1"),

            get_mesh(name="mesh1_2"),
            get_mesh(name="mesh2_2"),
            get_mesh(name="mesh3_2"),

            get_mesh(name="mesh1_3"),
            get_mesh(name="mesh2_3"),
            get_mesh(name="mesh3_3")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        create_data(self, meshes, hlod, hierarchy)

        self.compare_data(meshes, hlod, hierarchy)

    def test_PICK_mesh_roundtrip(self):
        hlod = get_hlod()
        boxes = [get_collision_box()]
        hierarchy = get_hierarchy()
        meshes = [
            get_mesh(name="sword", skin=True),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="TRUNK"),
            get_mesh(name="PICK")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")


        create_data(self, meshes, hlod, hierarchy, boxes)

        self.compare_data(meshes, hlod, hierarchy, boxes)

    def test_mesh_is_child_of_mesh_roundtrip(self):
        hlod = get_hlod()
        hlod.header.hierarchy_name = "containerName"
        hlod.lod_arrays[0].sub_objects = [
            get_hlod_sub_object(bone=1, name="containerName.parent"),
            get_hlod_sub_object(bone=2, name="containerName.child")]
        hlod.lod_arrays[0].header.model_count = len(hlod.lod_arrays[0].sub_objects)

        hierarchy = get_hierarchy()
        hierarchy.header.name = "containerName"
        hierarchy.pivots = [
            get_roottransform(),
            get_hierarchy_pivot(name="parent", parent=0),
            get_hierarchy_pivot(name="child", parent=1)]
        hierarchy.header.num_pivots = len(hierarchy.pivots)

        meshes = [
            get_mesh(name="parent"),
            get_mesh(name="child")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        create_data(self, meshes, hlod, hierarchy)

        self.compare_data(meshes, hlod, hierarchy)

    def test_meshes_roundtrip(self):
        hlod = get_hlod()
        boxes = [get_collision_box()]
        hierarchy = get_hierarchy()
        meshes = [
            get_mesh(name="sword", skin=True),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="TRUNK", shader_mats=True),
            get_mesh(name="PICK")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.tga")

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture_nrm.tga")

        create_data(self, meshes, hlod, hierarchy, boxes)

        self.compare_data(meshes)

    def test_mesh_too_many_vertex_groups_roundtrip(self):
        hlod = get_hlod()
        boxes = [get_collision_box()]
        hierarchy = get_hierarchy()
        meshes = [
            get_mesh(name="sword", skin=True)]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.tga")

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture_nrm.tga")

        create_data(self, meshes, hlod, hierarchy, boxes)

        sword = bpy.context.scene.objects["sword"]
        sword.vertex_groups.new(name="number3")
        sword.vertex_groups["number3"].add([3], 0.4, 'REPLACE')

        self.compare_data(meshes)

    def test_meshes_only_roundtrip(self):
        meshes = [
            get_mesh(name="wall"),
            get_mesh(name="tower"),
            get_mesh(name="tower2", shader_mats=True),
            get_mesh(name="stone")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture_nrm.dds")

        create_data(self, meshes)

        self.compare_data(meshes)

    def test_meshes_no_textures_found_roundtrip(self):
        meshes = [
            get_mesh(name="wall"),
            get_mesh(name="tower2", shader_mats=True)]

        create_data(self, meshes)

        self.compare_data(meshes)

    def test_hidden_meshes_roundtrip(self):
        meshes = [
            get_mesh(name="wall", hidden=True),
            get_mesh(name="tower", hidden=True),
            get_mesh(name="tower2", shader_mats=True),
            get_mesh(name="stone")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture_nrm.dds")

        create_data(self, meshes)

        self.compare_data(meshes)

    def test_prelit_meshes_roundtrip(self):
        hlod = get_hlod()
        hierarchy = get_hierarchy()
        meshes = [get_mesh(name="sword", skin=True, prelit=True)]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        create_data(self, meshes, hlod, hierarchy)

        #export not supported yet
        #self.compare_data(meshes, hlod, hierarchy)

    def test_animation_roundtrip(self):
        animation = get_animation()
        hlod = get_hlod()
        boxes = [get_collision_box()]
        hierarchy = get_hierarchy()
        hierarchy.pivot_fixups = []

        meshes = [
            get_mesh(name="sword", skin=True),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="TRUNK"),
            get_mesh(name="PICK")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        create_data(self, meshes, hlod, hierarchy, boxes, animation)

        self.compare_data([], None, None, [], animation)

    def test_compressed_animation_roundtrip(self):
        compressed_animation = get_compressed_animation(
            flavor=0,
            bit_channels=False,
            motion_tc=False,
            motion_ad4=False,
            motion_ad8=False,
            random_interpolation=False)
        boxes = [get_collision_box()]
        hlod = get_hlod()
        hierarchy = get_hierarchy()
        hierarchy.pivot_fixups = []
        meshes = [
            get_mesh(name="sword", skin=True),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="TRUNK"),
            get_mesh(name="PICK")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        create_data(self, meshes, hlod, hierarchy, boxes, None, compressed_animation)

        self.compare_data([], None, None, [], None, compressed_animation)

    def test_bone_is_created_if_referenced_by_subObject_but_also_child_bones_roundtrip(
            self):
        hlod = get_hlod()
        hierarchy = get_hierarchy()
        hierarchy.pivot_fixups = []
        hierarchy.pivots = [get_roottransform()]

        hierarchy.pivots.append(get_hierarchy_pivot(name="bone_pivot", parent=0))
        hierarchy.pivots.append(get_hierarchy_pivot(name="bone_pivot2", parent=1))
        hierarchy.pivots.append(get_hierarchy_pivot(name="bone_pivot4", parent=2))
        hierarchy.pivots.append(get_hierarchy_pivot(name="bone_pivot3", parent=1))

        hierarchy.header.num_pivots = len(hierarchy.pivots)

        array = HLodArray(
            header=get_hlod_array_header(),
            sub_objects=[])

        array.sub_objects.append(get_hlod_sub_object(
            bone=0, name="containerName.BOUNDINGBOX"))
        array.sub_objects.append(get_hlod_sub_object(
            bone=0, name="containerName.mesh"))
        array.sub_objects.append(get_hlod_sub_object(
            bone=1, name="containerName.bone_pivot2"))

        array.header.model_count = len(array.sub_objects)
        hlod.lod_arrays = [array]
        meshes = [
            get_mesh(name="mesh", skin=True),
            get_mesh(name="bone_pivot2")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        create_data(self, meshes, hlod, hierarchy)

        (_, rig) = retrieve_hierarchy(self, "containerName")

        self.assertTrue("bone_pivot2" in rig.pose.bones)


    def compare_data(self, meshes=[], hlod=None, hierarchy=None, boxes=[], animation=None, compressed_animation=None):
        container_name = "containerName"
        rig = None
        actual_hiera = None
        actual_hlod = None

        (actual_hiera, rig) = retrieve_hierarchy(self, container_name)
        if hierarchy is not None:
            hierarchy.pivot_fixups = [] # roundtrip not supported
            compare_hierarchies(self, hierarchy, actual_hiera)

        actual_hlod = create_hlod(actual_hiera, container_name)
        if hlod is not None:
            compare_hlods(self, hlod, actual_hlod)

        if meshes:
            actual_meshes = retrieve_meshes(self, actual_hiera, rig, container_name)
            self.assertEqual(len(meshes), len(actual_meshes))
            for i, mesh in enumerate(meshes):
                compare_meshes(self, mesh, actual_meshes[i])

        if boxes:
            actual_boxes = retrieve_boxes(actual_hiera, container_name)

            self.assertEqual(len(boxes), len(actual_boxes))
            for i, box in enumerate(boxes):
                compare_collision_boxes(self, box, actual_boxes[i])

        if animation is not None:
            actual_animation = retrieve_animation(animation.header.name, actual_hiera, rig, timecoded=False)
            compare_animations(self, animation, actual_animation)

        if compressed_animation is not None:
            actual_compressed_animation = retrieve_animation(compressed_animation.header.name, actual_hiera, rig, timecoded=True)
            compare_compressed_animations(self, compressed_animation, actual_compressed_animation)


