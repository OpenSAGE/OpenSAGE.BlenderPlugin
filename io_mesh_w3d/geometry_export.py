# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from io_mesh_w3d.utils import ReportHelper
from bpy_extras.io_utils import ExportHelper
from io_mesh_w3d.w3x.io_xml import *
from io_mesh_w3d.common.utils.helpers import *


def format_str(value):
    return '{:.3f}'.format(value)


class ExportGeometryData(bpy.types.Operator, ExportHelper, ReportHelper):
    bl_idname = 'scene.export_geometry_data'
    bl_label = 'Export Geometry Data'
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = '.xml'

    def execute(self, context):
        export_geometry_data(self, self.filepath)
        return {'FINISHED'}


def export_geometry_data(context, filepath):
    inifilepath = filepath.replace('.xml', '.ini')
    context.info(f'exporting geometry data to xml: {filepath}')
    context.info(f'exporting geometry data to ini: {inifilepath}')

    file = open(inifilepath, 'w')

    root = create_named_root('Geometry')
    root.set('isSmall', str(False))

    index = 0

    for mesh in get_objects('MESH'):
        if not mesh.data.object_type == 'GEOMETRY':
            continue

        type = str(mesh.data.geometry_type).upper()
        location, _, scale = mesh.matrix_world.decompose()
        extend = get_aa_box(mesh.data.vertices, mesh.matrix_local)
        majorRadius = extend.x * scale.x * 0.5
        minorRadius = extend.y * scale.y * 0.5
        height = extend.z * scale.z

        shape_node = create_node(root, 'Shape')
        shape_node.set('Type', type)
        if (index == 0):
            file.write(f'\tGeometry\t\t\t\t= {type}\n')
            file.write('\tGeometryIsSmall\t\t\t= No\n')
        else:
            file.write(f'\tAdditionalGeometry\t\t= {type}\n')

        file.write(f'\tGeometryName\t\t\t= {mesh.name}\n')

        shape_node.set('MajorRadius', format_str(majorRadius))
        file.write(f'\tGeometryMajorRadius\t\t= {format_str(majorRadius)}\n')

        if (mesh.data.geometry_type != 'SPHERE'):
            shape_node.set('MinorRadius', format_str(minorRadius))
            shape_node.set('Height', format_str(height))
            file.write(f'\tGeometryMinorRadius\t\t= {format_str(minorRadius)}\n')
            file.write(f'\tGeometryHeight\t\t\t= {format_str(height)}\n')

        if (mesh.data.contact_points_type != 'NONE'):
            shape_node.set('ContactPointGeneration', str(mesh.data.contact_points_type).upper())

        create_vector(location, shape_node, 'Offset')
        if (location.length > 0.01):
            file.write(
                f'\tGeometryOffset\t\t\t= X:{format_str(location.x)} Y:{format_str(location.y)} Z:{format_str(location.z)}\n')

        file.write('\n')
        index += 1

    for empty in get_objects('EMPTY'):
        contact_point_node = create_node(root, 'ContactPoint')
        location, _, _ = empty.matrix_world.decompose()
        create_vector(location, contact_point_node, 'Pos')
        file.write(
            f'\tGeometryContactPoint\t= X:{format_str(location.x)} Y:{format_str(location.y)} Z:{format_str(location.z)}\n')

    write(root, filepath)
    file.close()
    context.info('exporting geometry data finished')
