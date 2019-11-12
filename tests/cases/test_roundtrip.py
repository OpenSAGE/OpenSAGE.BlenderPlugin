# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from tests import utils
from shutil import copyfile

from tests.helpers.w3d_mesh import get_mesh
from tests.helpers.w3d_hlod import get_hlod
from tests.helpers.w3d_hierarchy import get_hierarchy
from tests.helpers.w3d_animation import get_animation
from tests.helpers.w3d_compressed_animation import get_compressed_animation
from tests.helpers.w3d_box import get_box

from io_mesh_w3d.export_w3d import save
from io_mesh_w3d.import_w3d import load


class TestRoundtrip(utils.W3dTestCase):
    def test_roundtrip(self):
        hierarchy_name = "TestHiera_SKL"
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name="sword"),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="shield")]
        hlod = get_hlod("TestModelName", hierarchy_name)
        box = get_box()
        animation = get_animation(hierarchy_name)
        comp_animation = get_compressed_animation(hierarchy_name)

        copyfile(self.relpath() + "/testfiles/texture.dds",
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
        model = utils.ImportWrapper(self.outpath() + "base_skn.w3d")
        load(model, bpy.context, import_settings={})
        anim = utils.ImportWrapper(self.outpath() + "base_ani.w3d")
        load(anim, bpy.context, import_settings={})
        comp_anim = utils.ImportWrapper(self.outpath() + "base_comp_ani.w3d")
        load(comp_anim, bpy.context, import_settings={})

        # export
        export_settings = {}
        export_settings['w3d_mode'] = "M"
        save(self.outpath() + "output_skn.w3d", bpy.context, export_settings)

        export_settings['w3d_mode'] = "H"
        save(self.outpath() + "output_skl.w3d", bpy.context, export_settings)

        export_settings['w3d_mode'] = "A"
        export_settings['w3d_compression'] = "U"
        save(self.outpath() + "output_ani.w3d", bpy.context, export_settings)

        export_settings['w3d_mode'] = "A"
        export_settings['w3d_compression'] = "TC"
        save(self.outpath() + "output_comp_ani.w3d", bpy.context, export_settings)

    def test_roundtrip_HAM(self):
        hierarchy_name = "TestName"
        hierarchy = get_hierarchy(hierarchy_name)
        meshes = [
            get_mesh(name="sword"),
            get_mesh(name="soldier", skin=True),
            get_mesh(name="shield")]
        hlod = get_hlod(hierarchy_name, hierarchy_name)
        box = get_box()
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
        model = utils.ImportWrapper(self.outpath() + "base.w3d")
        load(model, bpy.context, import_settings={})

        # TODO: compare blender data to generated structs

        # export
        export_settings = {}
        export_settings['w3d_mode'] = "HAM"

        save(self.outpath() + "output.w3d", bpy.context, export_settings)

        # TODO: compare exported file with output.w3d
