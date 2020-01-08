# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from tests.utils import *
from shutil import copyfile
from tests.utils import TestCase, ImportWrapper

from tests.shared.helpers.mesh import get_mesh
from tests.shared.helpers.hierarchy import get_hierarchy
from tests.shared.helpers.hlod import get_hlod
from tests.shared.helpers.collision_box import get_collision_box
from tests.shared.helpers.animation import get_animation

from tests.w3d.helpers.compressed_animation import get_compressed_animation

from io_mesh_w3d.w3d.export_w3d import save
from io_mesh_w3d.w3d.import_w3d import load


class TestRoundtrip(TestCase):
    def test_roundtrip(self):
        hierarchy_name = "TestHiera_SKL"
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name="sword", skin=True),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="TRUNK")]
        hlod = get_hlod("TestModelName", hierarchy_name)
        box = get_collision_box()
        animation = get_animation(hierarchy_name)
        comp_animation = get_compressed_animation(hierarchy_name)

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        # write to file
        skn = open(self.outpath() + "base_skn.w3d", "wb")
        for mesh in meshes:
            mesh.write(skn)
        hlod.write(skn)
        box.write(skn)
        skn.close()

        skl = open(self.outpath() + hierarchy_name + ".w3d", "wb")
        hierarchy.write(skl)
        skl.close()

        ani = open(self.outpath() + "base_ani.w3d", "wb")
        animation.write(ani)
        comp_animation.write(ani)
        ani.close()

        comp_ani = open(self.outpath() + "base_comp_ani.w3d", "wb")
        comp_animation.write(comp_ani)
        comp_ani.close()

        # import
        model = ImportWrapper(self.outpath() + "base_skn.w3d")
        load(model, import_settings={})
        anim = ImportWrapper(self.outpath() + "base_ani.w3d")
        load(anim, import_settings={})
        comp_anim = ImportWrapper(self.outpath() + "base_comp_ani.w3d")
        load(comp_anim, import_settings={})

        # check created objects
        self.assertTrue("TestHiera_SKL" in bpy.data.objects)
        self.assertTrue("TestHiera_SKL" in bpy.data.armatures)
        amt = bpy.data.armatures["TestHiera_SKL"]
        self.assertEqual(6, len(amt.bones))

        self.assertTrue("sword" in bpy.data.objects)
        self.assertTrue("soldier" in bpy.data.objects)
        self.assertTrue("TRUNK" in bpy.data.objects)

        # export
        context = ImportWrapper(self.outpath() + "output_skn.w3d")
        export_settings = {}
        export_settings['w3d_mode'] = "M"
        save(context, export_settings)

        context = ImportWrapper(self.outpath() + "output_skl.w3d")
        export_settings['w3d_mode'] = "H"
        save(context, export_settings)

        context = ImportWrapper(self.outpath() + "output_ani.w3d")
        export_settings['w3d_mode'] = "A"
        export_settings['w3d_compression'] = "U"
        save(context, export_settings)

        context = ImportWrapper(self.outpath() + "output_comp_ani.w3d")
        export_settings['w3d_mode'] = "A"
        export_settings['w3d_compression'] = "TC"
        save(context, export_settings)

    def test_roundtrip_HAM(self):
        hierarchy_name = "TestName"
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name="sword", skin=True),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="TRUNK")]
        hlod = get_hlod(hierarchy_name, hierarchy_name)
        box = get_collision_box()
        animation = get_animation(hierarchy_name)
        comp_animation = get_compressed_animation(hierarchy_name)

        # write to file
        output = open(self.outpath() + "base.w3d", "wb")
        hierarchy.write(output)
        for mesh in meshes:
            mesh.write(output)
        hlod.write(output)
        box.write(output)
        animation.write(output)
        comp_animation.write(output)
        output.close()

        # import
        model = ImportWrapper(self.outpath() + "base.w3d")
        load(model, import_settings={})

        # check created objects
        self.assertTrue("TestName" in bpy.data.armatures)
        amt = bpy.data.armatures["TestName"]
        self.assertEqual(6, len(amt.bones))

        self.assertTrue("sword" in bpy.data.objects)
        self.assertTrue("soldier" in bpy.data.objects)
        self.assertTrue("TRUNK" in bpy.data.objects)

        # export
        export_settings = {}
        export_settings['w3d_mode'] = "HAM"
        export_settings['w3d_compression'] = "U"
        context = ImportWrapper(self.outpath() + "output.w3d")
        save(context, export_settings)

    def test_roundtrip_prelit(self):
        hierarchy_name = "TestHiera_SKL"
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [get_mesh(name="sword", skin=True, prelit=True),
                  get_mesh(name="soldier", skin=True),
                  get_mesh(name="TRUNK", prelit=True)]
        hlod = get_hlod("TestModelName", hierarchy_name)

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        # write to file
        skn = open(self.outpath() + "base_skn.w3d", "wb")
        for mesh in meshes:
            mesh.write(skn)
        hlod.write(skn)
        skn.close()

        skl = open(self.outpath() + hierarchy_name + ".w3d", "wb")
        hierarchy.write(skl)
        skl.close()

        # import
        model = ImportWrapper(self.outpath() + "base_skn.w3d")
        load(model, import_settings={})

        # check created objects
        self.assertTrue("TestHiera_SKL" in bpy.data.objects)
        self.assertTrue("TestHiera_SKL" in bpy.data.armatures)
        amt = bpy.data.armatures["TestHiera_SKL"]
        self.assertEqual(6, len(amt.bones))

        self.assertTrue("sword" in bpy.data.objects)
        self.assertTrue("soldier" in bpy.data.objects)
        self.assertTrue("TRUNK" in bpy.data.objects)

        # export
        context = ImportWrapper(self.outpath() + "output_skn.w3d")
        export_settings = {}
        export_settings['w3d_mode'] = "M"
        save(context, export_settings)
