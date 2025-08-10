# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from io_mesh_w3d.utils import ReportHelper
from bpy_extras.io_utils import ExportHelper
from io_mesh_w3d.w3x.io_xml import *
from io_mesh_w3d.common.utils.helpers import *


def format_str(value):
    return '{:.3f}'.format(value)


class ExportBoneVolumeData(bpy.types.Operator, ExportHelper, ReportHelper):
    bl_idname = 'scene.export_bone_volume_data'
    bl_label = 'Export Bone Volume Data'
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = '.xml'

    def execute(self, context):
        export_bone_volume_data(self, self.filepath)
        return {'FINISHED'}


def export_bone_volume_data(context, filepath):
    context.info(f'exporting bone volume data to xml: {filepath}')

    root = create_named_root('BoneVolumes')

    for mesh in get_objects('MESH'):
        if not mesh.data.object_type == 'BONE_VOLUME':
            continue

        node = create_node(root, 'BoneVolume')
        node.set('BoneName', mesh.name)
        node.set('ContactTag', mesh.data.contact_tag)
        node.set('Mass', format_str(mesh.data.mass))
        node.set('Spinniness', format_str(mesh.data.spinniness))

        location, rotation, scale = mesh.matrix_world.decompose()
        extend = get_aa_box(mesh.data.vertices)
        center = get_aa_center(mesh.data.vertices)
        halfX = extend.x * scale.x * 0.5
        halfY = extend.y * scale.y * 0.5
        halfZ = extend.z * scale.z * 0.5

        box = create_node(node, 'Box')
        box.set('HalfSizeX', format_str(halfX))
        box.set('HalfSizeY', format_str(halfY))
        box.set('HalfSizeZ', format_str(halfZ))

        create_vector(location + center, box, 'Translation')
        create_quaternion(rotation, box, 'Rotation')

    write(root, filepath)
    context.info('exporting bone volume data finished')
