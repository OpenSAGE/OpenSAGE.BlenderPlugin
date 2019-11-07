# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from tests import utils
from shutil import copyfile

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


class TestUtils(utils.W3dTestCase):
    def test_vertex_material_roundtrip(self):
        mesh = get_mesh()
        context = utils.ImportWrapper(self.outpath())

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        for source in mesh.vert_materials:
            material = create_material_from_vertex_material(
                context, mesh, source)
            actual = retrieve_vertex_material(material)
            compare_vertex_materials(self, source, actual)

    def test_shader_material_roundtrip(self):
        mesh = get_mesh()
        context = utils.ImportWrapper(self.outpath())

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        for source in mesh.shader_materials:
            material = create_material_from_shader_material(
                context, mesh, source)
            principled = retrieve_principled_bsdf(material)
            actual = retrieve_shader_material(material, principled)
            compare_shader_materials(self, source, actual)

    def test_shader_roundtrip(self):
        mesh = get_mesh()
        context = utils.ImportWrapper(self.outpath())

        material = create_material_from_vertex_material(
            context, mesh, mesh.vert_materials[0])
        expected = mesh.shaders[0]
        set_shader_properties(material, expected)
        actual = retrieve_shader(material)
        compare_shaders(self, expected, actual)

    def test_box_roundtrip(self):
        expected = get_box()
        hlod = get_hlod()
        create_box(expected, get_collection(None))

        boxes = retrieve_boxes(hlod)
        compare_boxes(self, expected, boxes[0])

    def test_hierarchy_roundtrip(self):
        context = utils.ImportWrapper(self.outpath())
        expected = get_hierarchy()
        hlod = get_hlod()
        meshes = [
            get_mesh(name="sword"),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="shield"),
            get_mesh(name="pike")]

        coll = get_collection(hlod)
        rig = get_or_create_skeleton(hlod, expected, coll)

        for mesh in meshes:
            create_mesh(context, mesh, expected, rig)

        for mesh in meshes:
            rig_mesh(mesh, expected, hlod, rig, coll)

        get_or_create_skeleton(hlod, expected, get_collection(None))
        (actual, rig) = retrieve_hierarchy("containerName")
        compare_hierarchies(self, expected, actual)

    def test_hlod_roundtrip(self):
        context = utils.ImportWrapper(self.outpath())
        expected = get_hlod()
        box = get_box()
        hierarchy = get_hierarchy()
        meshes = [
            get_mesh(name="sword"),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="shield"),
            get_mesh(name="pike")]

        coll = get_collection(expected)
        rig = get_or_create_skeleton(expected, hierarchy, coll)
        create_box(box, coll)

        for mesh in meshes:
            create_mesh(context, mesh, hierarchy, rig)

        for mesh in meshes:
            rig_mesh(mesh, hierarchy, expected, rig, coll)

        actual = create_hlod("containerName", hierarchy.header.name)
        retrieve_boxes(actual)
        retrieve_meshes(hierarchy, rig, actual, "containerName")
        compare_hlods(self, expected, actual)

    def test_meshes_roundtrip(self):
        context = utils.ImportWrapper(self.outpath())
        hlod = get_hlod()
        box = get_box()
        hierarchy = get_hierarchy()
        expecteds = [
            get_mesh(name="sword"),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="shield", shader_mats=True),
            get_mesh(name="pike")]

        coll = get_collection(hlod)
        rig = get_or_create_skeleton(hlod, hierarchy, coll)
        create_box(box, coll)

        copyfile(self.relpath() + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        for mesh in expecteds:
            create_mesh(context, mesh, hierarchy, rig)

        for mesh in expecteds:
            rig_mesh(mesh, hierarchy, hlod, rig, coll)

        hlod = create_hlod("containerName", hierarchy.header.name)
        retrieve_boxes(hlod)
        actuals = retrieve_meshes(hierarchy, rig, hlod, "containerName")

        self.assertEqual(len(expecteds), len(actuals))
        for i, expected in enumerate(expecteds):
            compare_meshes(self, expected, actuals[i])


    def test_animation_roundtrip(self):
        context = utils.ImportWrapper(self.outpath())
        expected = get_animation()
        hlod = get_hlod()
        hierarchy = get_hierarchy()

        meshes = [
            get_mesh(name="sword"),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="shield", shader_mats=True),
            get_mesh(name="pike")]

        coll = get_collection(hlod)
        rig = get_or_create_skeleton(hlod, hierarchy, coll)

        for mesh in meshes:
            create_mesh(context, mesh, hierarchy, rig)

        for mesh in meshes:
            rig_mesh(mesh, hierarchy, hlod, rig, coll)

        create_animation(rig, expected, hierarchy)

        actual = retrieve_animation(expected.header.name, hierarchy, rig)
        compare_animations(self, expected, actual)

    def test_compressed_animation_roundtrip(self):
        context = utils.ImportWrapper(self.outpath())
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
        meshes = [
            get_mesh(name="sword"),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="shield")]

        coll = get_collection(hlod)
        rig = get_or_create_skeleton(hlod, hierarchy, coll)

        for mesh in meshes:
            create_mesh(context, mesh, hierarchy, rig)

        for mesh in meshes:
            rig_mesh(mesh, hierarchy, hlod, rig, coll)

        create_animation(rig, expected, hierarchy, compressed=True)
        actual = retrieve_animation("containerName", hierarchy, rig, timecoded=True)
        compare_compressed_animations(self, expected, actual)
