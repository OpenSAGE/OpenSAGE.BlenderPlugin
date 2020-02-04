# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
import os
from shutil import copyfile

from io_mesh_w3d.import_utils import *
from tests.shared.helpers.hierarchy import *
from tests.shared.helpers.hlod import *
from tests.shared.helpers.mesh import *
from tests.utils import *
from os.path import dirname as up


class TestImportUtils(TestCase):
    def test_texture_file_extensions(self):
        extensions = ['.dds', '.tga', '.jpg', '.jpeg', '.png', '.bmp']

        self.warning = lambda text: self.fail(text)

        for extension in extensions:
            copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture' + extension)

            find_texture(self, 'texture')

            # reset scene
            bpy.ops.wm.read_homefile(use_empty=True)
            os.remove(self.outpath() + 'texture' + extension)

    def test_invalid_texture_file_extension(self):
        extensions = ['.invalid']

        self.info = lambda text: self.fail(text)

        for extension in extensions:
            copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture' + extension)

            find_texture(self, 'texture')

            # reset scene
            bpy.ops.wm.read_homefile(use_empty=True)
            os.remove(self.outpath() + 'texture' + extension)

    def test_duplicate_shader_material_creation(self):
        shader_mats = [get_shader_material(), get_shader_material()]

        for mat in shader_mats:
            create_material_from_shader_material(self, 'meshName', mat)

        self.assertEqual(1, len(bpy.data.materials))
        self.assertTrue('meshName.ShaderMaterial.fx' in bpy.data.materials)

    def test_parent_is_none_if_parent_index_is_0_or_less_than_0(self):
        hlod = get_hlod()
        hierarchy = get_hierarchy()

        root = get_hierarchy_pivot("ROOTTRANSFORM", -1)
        root.translation = Vector()
        root.rotation = Quaternion()
        root.euler_angles = Vector((0.0, 0.0, 0.0))

        hierarchy.pivots = [get_roottransform(),
                            get_hierarchy_pivot(name="first", parent=0),
                            get_hierarchy_pivot(name="second", parent=-1)]

        hierarchy.header.num_pivots = len(hierarchy.pivots)

        array = HLodLodArray(
            header=get_hlod_array_header(),
            sub_objects=[])

        array.sub_objects.append(get_hlod_sub_object(
            bone=1, name="containerName.first"))
        array.sub_objects.append(get_hlod_sub_object(
            bone=2, name="containerName.second"))

        array.header.model_count = len(array.sub_objects)

        hlod.lod_arrays = [array]

        mesh_structs = [
            get_mesh(name="first"),
            get_mesh(name="second")]

        copyfile(up(up(self.relpath())) + "/testfiles/texture.dds",
                 self.outpath() + "texture.dds")

        coll = get_collection(hlod)

        for mesh_struct in mesh_structs:
            create_mesh(self, mesh_struct, hierarchy, coll)

        rig = get_or_create_skeleton(hlod, hierarchy, coll)

        for i, mesh_struct in enumerate(mesh_structs):
            rig_mesh(mesh_struct, hierarchy, hlod, rig)

        self.assertTrue("first" in bpy.data.objects)
        first = bpy.data.objects["first"]
        self.assertIsNone(first.parent)

        self.assertTrue("second" in bpy.data.objects)
        second = bpy.data.objects["second"]
        self.assertIsNone(second.parent)

    def test_read_chunk_array(self):
        output = io.BytesIO()

        mat_pass = get_material_pass()
        mat_pass.write(output)
        mat_pass.write(output)
        mat_pass.write(output)

        write_chunk_head(0x00, output, 9, has_sub_chunks=False)
        write_ubyte(0x00, output)

        io_stream = io.BytesIO(output.getvalue())
        read_chunk_array(self, io_stream, mat_pass.size()
                         * 3 + 9, W3D_CHUNK_MATERIAL_PASS, MaterialPass.read)

    def test_bone_visibility_channel_creation(self):
        armature = bpy.data.armatures.new('armature')
        rig = bpy.data.objects.new('rig', armature)
        bpy.context.scene.collection.objects.link(rig)
        bpy.context.view_layer.objects.active = rig
        rig.select_set(True)

        if rig.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        bone = armature.edit_bones.new('bone')
        bone.head = Vector((0.0, 0.0, 0.0))
        bone.tail = Vector((0.0, 1.0, 0.0))

        if rig.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        self.assertTrue('bone' in armature.bones)
        self.assertTrue('bone' in rig.data.bones)

        bone = rig.data.bones['bone']
        bone.hide = True
        bone.keyframe_insert(data_path='hide', frame=0)

        results = [fcu for fcu in armature.animation_data.action.fcurves if 'hide' in fcu.data_path]
        self.assertEqual(1, len(results))