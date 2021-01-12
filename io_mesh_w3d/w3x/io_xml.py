# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io
from io_mesh_w3d.common.io_xml import *
from mathutils import Vector, Quaternion, Matrix


def write_struct(struct, path):
    root = create_root()
    struct.create(root)
    write(root, path)


def find_asset_root(context, source):
    root = find_root(context, source)
    if root is None:
        return None

    if root.tag != 'AssetDeclaration':
        context.error('file \'' + source + '\' does not contain a AssetDeclaration node!')
        return None
    return root


def create_named_root(name):
    root = ET.Element(name)
    return root


def create_root():
    root = ET.Element('AssetDeclaration')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xmlns', 'uri:ea.com:eala:asset')
    return root


def parse_quaternion(xml_quaternion):
    return Quaternion((
        parse_float(xml_quaternion, 'W', 1.0),
        parse_float(xml_quaternion, 'X'),
        parse_float(xml_quaternion, 'Y'),
        parse_float(xml_quaternion, 'Z')))


def create_quaternion(quat, parent, identifier='Rotation'):
    quaternion = create_node(parent, identifier)
    quaternion.set('W', truncate(quat[0]))
    quaternion.set('X', truncate(quat[1]))
    quaternion.set('Y', truncate(quat[2]))
    quaternion.set('Z', truncate(quat[3]))


def parse_matrix(xml_matrix):
    return Matrix((
        [parse_float(xml_matrix, 'M00', 1.0),
         parse_float(xml_matrix, 'M01'),
         parse_float(xml_matrix, 'M02'),
         parse_float(xml_matrix, 'M03')],

        [parse_float(xml_matrix, 'M10'),
         parse_float(xml_matrix, 'M11', 1.0),
         parse_float(xml_matrix, 'M12'),
         parse_float(xml_matrix, 'M13')],

        [parse_float(xml_matrix, 'M20'),
         parse_float(xml_matrix, 'M21'),
         parse_float(xml_matrix, 'M22', 1.0),
         parse_float(xml_matrix, 'M23')]))


def create_matrix(mat, parent, identifier='FixupMatrix'):
    matrix = create_node(parent, identifier)
    matrix.set('M00', truncate(mat[0][0]))
    matrix.set('M01', truncate(mat[0][1]))
    matrix.set('M02', truncate(mat[0][2]))
    matrix.set('M03', truncate(mat[0][3]))

    matrix.set('M10', truncate(mat[1][0]))
    matrix.set('M11', truncate(mat[1][1]))
    matrix.set('M12', truncate(mat[1][2]))
    matrix.set('M13', truncate(mat[1][3]))

    matrix.set('M20', truncate(mat[2][0]))
    matrix.set('M21', truncate(mat[2][1]))
    matrix.set('M22', truncate(mat[2][2]))
    matrix.set('M23', truncate(mat[2][3]))
