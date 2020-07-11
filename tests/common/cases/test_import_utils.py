# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
import io
from mathutils import Vector
from tests.common.helpers.mesh import *
from tests.utils import *


class TestImportUtils(TestCase):
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
