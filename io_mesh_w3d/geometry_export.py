# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy_extras.io_utils import ExportHelper
from io_mesh_w3d.w3x.io_xml import *
from io_mesh_w3d.common.utils.helpers import get_objects


class ExportGeometryData(bpy.types.Operator, ExportHelper):
    bl_idname = 'scene.export_geometry_data'
    bl_label = 'Export Geometry Data'
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = '.xml'
 
    def execute(self, context):
        export_geometry_data(self.filepath)
        return {'FINISHED'}


def export_geometry_data(filepath):
    print('exporting geometry data to: ' + filepath)
    root = create_named_root('Geometry')
    root.set('isSmall', str(False));

    for mesh in get_objects('MESH'):
        if not mesh.data.object_type == 'GEOMETRY':
            continue

        location, _, scale = mesh.matrix_world.decompose()
        majorRadius = abs(mesh.bound_box[4][0] - mesh.bound_box[0][0]) * scale.x * 0.5
        minorRadius = abs(mesh.bound_box[2][1] - mesh.bound_box[0][1]) * scale.y * 0.5
        height = abs(mesh.bound_box[1][2] - mesh.bound_box[0][2]) * scale.z
        
        shape_node = create_node(root, 'Shape')
        shape_node.set('Type', str(mesh.data.geometry_type).upper())
        shape_node.set('MajorRadius', format(majorRadius))

        if (mesh.data.geometry_type != 'SPHERE'):
            shape_node.set('MinorRadius', format(minorRadius))
            shape_node.set('Height', format(height))

        if (mesh.data.contact_points_type != 'NONE'):
            shape_node.set('ContactPointGeneration', str(mesh.data.contact_points_type).upper())

        create_vector(location, shape_node, 'Offset')

    for empty in get_objects('EMPTY'):
        contact_point_node = create_node(root, 'ContactPoint')
        location, _, _ = empty.matrix_world.decompose()
        create_vector(location, contact_point_node, 'Pos')

    write(root, filepath)
    print('exporting geometry finished')