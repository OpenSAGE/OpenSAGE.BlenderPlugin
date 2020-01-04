# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests.utils import *
from shutil import copyfile
import os

from io_mesh_w3d.import_utils import *
from io_mesh_w3d.export_utils import *
from tests.w3d.helpers.mesh import *
from tests.w3d.helpers.mesh_structs.material_pass import *
from tests.w3d.helpers.mesh_structs.material_info import *
from tests.w3d.helpers.mesh_structs.vertex_material import *
from tests.w3d.helpers.mesh_structs.shader_material import *
from tests.w3d.helpers.mesh_structs.shader import *
from tests.w3d.helpers.box import *
from tests.w3d.helpers.hierarchy import *
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
        hierarchy = get_hierarchy()
        meshes = [get_mesh()]
        boxes = [get_box(), get_box("WORLDBOX")]

        create_data(self, meshes, hlod, hierarchy, boxes)

        actual_boxes = retrieve_boxes(hlod, hierarchy)
        
        self.compare_data(meshes, hlod, hierarchy, boxes)

    def test_hierarchy_roundtrip(self):
        hierarchy = get_hierarchy()
        hlod = get_hlod()
        meshes = [
            get_mesh(name="sword", skin=True),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="TRUNK"),
            get_mesh(name="PICK")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        create_data(self, meshes, hlod, hierarchy)

        self.compare_data(meshes, hlod, hierarchy)

    def test_hlod_roundtrip(self):
        hlod = get_hlod()
        boxes = [get_box()]
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

    def test_hlod_4_levels_roundtrip(self):
        hlod = get_hlod_4_levels()
        boxes = [get_box()]
        hierarchy = get_hierarchy()

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

        create_data(self, meshes, hlod, hierarchy, boxes)

        self.compare_data(meshes, hlod, hierarchy, boxes)

    def test_bone_is_created_if_referenced_by_subObject_but_also_child_bones_roundtrip(
            self):
        hlod = get_hlod()
        boxes = [get_box()]
        hierarchy = get_hierarchy()
        hierarchy.pivot_fixups = []

        root = get_hierarchy_pivot("ROOTTRANSFORM", -1)
        root.translation = Vector()
        root.rotation = Quaternion()
        root.euler_angles = Vector((0.0, 0.0, 0.0))

        hierarchy.pivots = [root]

        hierarchy.pivots.append(get_hierarchy_pivot("waist", 0))
        hierarchy.pivots.append(get_hierarchy_pivot("hip", 1))
        hierarchy.pivots.append(get_hierarchy_pivot("shoulderl", 2))
        hierarchy.pivots.append(get_hierarchy_pivot("arml", 3))
        hierarchy.pivots.append(get_hierarchy_pivot("shield", 4))
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
            bone=5, name="containerName.shield"))
        array.sub_objects.append(get_hlod_sub_object(
            bone=0, name="containerName.PICK"))

        array.header.model_count = len(array.sub_objects)

        hlod.lod_array = array

        meshes = [
            get_mesh(name="sword"),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="shield"),
            get_mesh(name="PICK")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        create_data(self, meshes, hlod, hierarchy, boxes)

        self.compare_data(meshes, hlod, hierarchy, boxes)

    def test_PICK_mesh_roundtrip(self):
        hlod = get_hlod(hierarchy_name="containerName")
        hlod.lod_arrays[0].sub_objects = [
            get_hlod_sub_object(bone=1, name="containerName.building"),
            get_hlod_sub_object(bone=0, name="containerName.PICK")]
        hlod.lod_arrays[0].header.model_count = len(hlod.lod_arrays[0].sub_objects)

        meshes = [
            get_mesh(name="building"),
            get_mesh(name="PICK")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        hierarchy = get_hierarchy("containerName")
        hierarchy.pivot_fixups = []
        hierarchy.pivots = [
            get_roottransform(),
            get_hierarchy_pivot("building", 0)]
        hierarchy.header.num_pivots = len(hierarchy.pivots)

        create_data(self, meshes, hlod, hierarchy)

        self.compare_data(meshes, hlod, hierarchy)

    def test_meshes_roundtrip(self):
        hlod = get_hlod()
        boxes = [get_box()]
        hierarchy = get_hierarchy()
        meshes = [
            get_mesh(name="sword", skin=True),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="TRUNK", shader_mats=True),
            get_mesh(name="pike")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture_nrm.dds")

        create_data(self, meshes, hlod, hierarchy, boxes)

        self.compare_data(meshes, hlod, hierarchy, boxes)

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
        hierarchy = get_hierarchy()
        hierarchy.pivot_fixups = []

        meshes = [
            get_mesh(name="sword", skin=True),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="TRUNK"),
            get_mesh(name="PICK")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        create_data(self, meshes, hlod, hierarchy, [], animation)

        self.compare_data(meshes, hlod, hierarchy, [], animation)

    def test_compressed_animation_roundtrip(self):
        expected = get_compressed_animation(
            flavor=0,
            bit_channels=False,
            motion_tc=False,
            motion_ad4=False,
            motion_ad8=False,
            random_interpolation=False)
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

        create_data(self, meshes, hlod, hierarchy, [], None, expected)

        self.compare_data(meshes, hlod, hierarchy, [], None, expected)

    def test_bone_is_created_if_referenced_by_subObject_but_also_child_bones_roundtrip(
            self):
        hlod = get_hlod()
        hierarchy = get_hierarchy()
        hierarchy.pivot_fixups = []
        hierarchy.pivots = [get_roottransform()]

        hierarchy.pivots.append(get_hierarchy_pivot("bone_pivot", 0))
        hierarchy.pivots.append(get_hierarchy_pivot("bone_pivot2", 1))
        hierarchy.pivots.append(get_hierarchy_pivot("bone_pivot4", 2))
        hierarchy.pivots.append(get_hierarchy_pivot("bone_pivot3", 1))

        hierarchy.header.num_pivots = len(hierarchy.pivots)

        array = HLodArray(
            header=get_hlod_array_header(),
            sub_objects=[])

        array.sub_objects.append(get_hlod_sub_object(
            bone=0, name="containerName.BOUNDINGBOX"))
        array.sub_objects.append(get_hlod_sub_object(
            bone=0, name="containerName.mesh"))
        array.sub_objects.append(get_hlod_sub_object(
            bone=1, name="containerName.bone_pivot"))

        array.header.model_count = len(array.sub_objects)
        hlod.lod_arrays = [array]
        meshes = [
            get_mesh(name="mesh", skin=True),
            get_mesh(name="bone_pivot")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        create_data(self, meshes, hlod, hierarchy)

        self.compare_data(meshes, hlod, hierarchy)


    def compare_data(self, meshes, hlod=None, hierarchy=None, boxes=[], animation=None, compressed_animation=None):
        container_name = "containerName"
        rig = None
        actual_hiera = None
        actual_hlod = None
        if hierarchy is not None:
            (actual_hiera, rig) = retrieve_hierarchy(container_name)
            hierarchy.pivot_fixups = [] # roundtrip not supported
            compare_hierarchies(self, hierarchy, actual_hiera)

        if hlod is not None:
            actual_hlod = create_hlod(container_name, actual_hiera.header.name)
            compare_hlods(self, hlod, actual_hlod)

        actual_meshes = retrieve_meshes(self, actual_hiera, rig, actual_hlod, container_name)
        self.assertEqual(len(meshes), len(actual_meshes))
        for i, mesh in enumerate(meshes):
            compare_meshes(self, mesh, actual_meshes[i])

        if boxes:
            actual_boxes = retrieve_boxes(hlod, hierarchy)
        
            self.assertEqual(len(boxes), len(actual_boxes))
            for i, box in enumerate(boxes):
                compare_boxes(self, box, actual_boxes[i])

        if animation is not None:
            actual_animation = retrieve_animation(animation.header.name, actual_hiera, rig, timecoded=False)
            compare_animations(self, animation, actual_animation)

        if compressed_animation is not None:
            actual_compressed_animation = retrieve_animation(compressed_animation.header.name, hierarchy, rig, timecoded=True)
            compare_compressed_animations(self, compressed_animation, actual_compressed_animation)


