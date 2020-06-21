# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import xml.etree.ElementTree as ET
from mathutils import Vector, Quaternion, Matrix


def create_node(self, identifier):
    return ET.SubElement(self, identifier)


def write_struct(struct, path):
    root = create_root()
    struct.create(root)
    write(root, path)


def pretty_print(elem, level=0):
    i = '\n' + level * '  '
    if elem:
        elem.text = i + '  '
        elem.tail = i
        for elem in elem:
            pretty_print(elem, level + 1)
        elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def write(root, path):
    pretty_print(root)
    xml_spec = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
    data = bytes(xml_spec, 'utf-8') + ET.tostring(root)

    file = open(path, 'wb')
    file.write(data)
    file.close()


def strip_namespaces(it):
    for _, el in it:
        el.tag = el.tag.split('}', 1)[-1]


def find_root(context, source):
    try:
        it = ET.iterparse(source)
        strip_namespaces(it)
        root = it.root
    except BaseException:
        context.error('file: ' + source + ' does not contain valid XML data!')
        return None

    if root.tag != 'AssetDeclaration':
        context.error('file: ' + source + ' does not contain a AssetDeclaration node!')
        return None
    return root


def create_root():
    root = ET.Element('AssetDeclaration')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xmlns', 'uri:ea.com:eala:asset')
    return root


def parse_value(xml_obj, cast_func=str):
    return cast_func(xml_obj.text)


def create_value(value, parent, identifier):
    xml_obj = create_node(parent, identifier)
    xml_obj.text = str(value)


def parse_objects(parent, name, parse_func, par1=None):
    result = []
    objects = parent.findall(name)
    if not objects:
        return result
    for obj in objects:
        if par1 is not None:
            result.append(parse_func(obj, par1))
        else:
            result.append(parse_func(obj))
    return result


def create_object_list(parent, name, objects, write_func, par1=None):
    xml_objects_list = create_node(parent, name)
    for obj in objects:
        if par1 is not None:
            write_func(obj, xml_objects_list, par1)
        else:
            write_func(obj, xml_objects_list)


def format(value):
    return '{:.6f}'.format(value)


def parse_vector2(xml_vector2):
    return Vector((
        float(xml_vector2.get('X', 0.0)),
        float(xml_vector2.get('Y', 0.0))))


def create_vector2(vec2, parent, name):
    vector = create_node(parent, name)
    vector.set('X', format(vec2.x))
    vector.set('Y', format(vec2.y))


def parse_vector(xml_vector):
    return Vector((
        float(xml_vector.get('X', 0.0)),
        float(xml_vector.get('Y', 0.0)),
        float(xml_vector.get('Z', 0.0))))


def create_vector(vec, parent, name):
    vector = create_node(parent, name)
    vector.set('X', format(vec.x))
    vector.set('Y', format(vec.y))
    vector.set('Z', format(vec.z))


def parse_quaternion(xml_quaternion):
    return Quaternion((
        float(xml_quaternion.get('W', 1.0)),
        float(xml_quaternion.get('X', 0.0)),
        float(xml_quaternion.get('Y', 0.0)),
        float(xml_quaternion.get('Z', 0.0))))


def create_quaternion(quat, parent, identifier='Rotation'):
    quaternion = create_node(parent, identifier)
    quaternion.set('W', format(quat[0]))
    quaternion.set('X', format(quat[1]))
    quaternion.set('Y', format(quat[2]))
    quaternion.set('Z', format(quat[3]))


def parse_matrix(xml_matrix):
    return Matrix((
        [float(xml_matrix.get('M00', 1.0)),
         float(xml_matrix.get('M01', 0.0)),
         float(xml_matrix.get('M02', 0.0)),
         float(xml_matrix.get('M03', 0.0))],

        [float(xml_matrix.get('M10', 0.0)),
         float(xml_matrix.get('M11', 1.0)),
         float(xml_matrix.get('M12', 0.0)),
         float(xml_matrix.get('M13', 0.0))],

        [float(xml_matrix.get('M20', 0.0)),
         float(xml_matrix.get('M21', 0.0)),
         float(xml_matrix.get('M22', 1.0)),
         float(xml_matrix.get('M23', 0.0))]))


def create_matrix(mat, parent, identifier='FixupMatrix'):
    matrix = create_node(parent, identifier)
    matrix.set('M00', format(mat[0][0]))
    matrix.set('M01', format(mat[0][1]))
    matrix.set('M02', format(mat[0][2]))
    matrix.set('M03', format(mat[0][3]))

    matrix.set('M10', format(mat[1][0]))
    matrix.set('M11', format(mat[1][1]))
    matrix.set('M12', format(mat[1][2]))
    matrix.set('M13', format(mat[1][3]))

    matrix.set('M20', format(mat[2][0]))
    matrix.set('M21', format(mat[2][1]))
    matrix.set('M22', format(mat[2][2]))
    matrix.set('M23', format(mat[2][3]))
