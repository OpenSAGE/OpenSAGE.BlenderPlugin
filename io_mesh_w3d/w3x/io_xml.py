# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import xml.etree.ElementTree as ET
from mathutils import Vector, Quaternion, Matrix

from xml.dom import minidom



def childs(self):
    return [node for node in self.childNodes if node.nodeType == minidom.Node.ELEMENT_NODE]


minidom.Node.childs = childs


def write_struct_to_file(struct, path):
    doc = minidom.Document()
    asset = create_asset_declaration(doc)
    asset.appendChild(struct.create(doc))
    doc.appendChild(asset)

    file = open(path, 'wb')
    file.write(bytes(doc.toprettyxml(indent='   '), 'UTF-8'))
    file.close()


def create_asset_declaration(doc):
    asset_decl = doc.createElement('AssetDeclaration')
    asset_decl.setAttribute('xmlns', 'uri:ea.com:eala:asset')
    asset_decl.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    return asset_decl


def parse_value(xml_obj, cast_func=str):
    return cast_func(xml_obj.childNodes[0].nodeValue)


def create_value(value, doc, identifier):
    xml_obj = doc.createElement(identifier)
    xml_obj.appendChild(doc.createTextNode(str(value)))
    return xml_obj


def parse_vector2(xml_vector2):
    return Vector((
        float(xml_vector2.attributes['X'].value),
        float(xml_vector2.attributes['Y'].value)))


def create_vector2(vec2, doc, name):
    vector = doc.createElement(name)
    vector.setAttribute('X', str(vec2.x))
    vector.setAttribute('Y', str(vec2.y))
    return vector


def parse_vector(xml_vector):
    return Vector((
        float(xml_vector.attributes['X'].value),
        float(xml_vector.attributes['Y'].value),
        float(xml_vector.attributes['Z'].value)))


def create_vector(vec, doc, name):
    vector = doc.createElement(name)
    vector.setAttribute('X', str(vec.x))
    vector.setAttribute('Y', str(vec.y))
    vector.setAttribute('Z', str(vec.z))
    return vector


def parse_quaternion(xml_quaternion):
    return Quaternion((
        float(xml_quaternion.attributes['W'].value),
        float(xml_quaternion.attributes['X'].value),
        float(xml_quaternion.attributes['Y'].value),
        float(xml_quaternion.attributes['Z'].value)))


def create_quaternion(quat, doc, identifier='Rotation'):
    quaternion = doc.createElement(identifier)
    quaternion.setAttribute('W', str(quat[0]))
    quaternion.setAttribute('X', str(quat[1]))
    quaternion.setAttribute('Y', str(quat[2]))
    quaternion.setAttribute('Z', str(quat[3]))
    return quaternion


def parse_matrix(xml_quaternion):
    return Matrix((
        [float(xml_quaternion.attributes['M00'].value),
         float(xml_quaternion.attributes['M10'].value),
         float(xml_quaternion.attributes['M20'].value),
         float(xml_quaternion.attributes['M30'].value)],

        [float(xml_quaternion.attributes['M01'].value),
         float(xml_quaternion.attributes['M11'].value),
         float(xml_quaternion.attributes['M21'].value),
         float(xml_quaternion.attributes['M31'].value)],

        [float(xml_quaternion.attributes['M02'].value),
         float(xml_quaternion.attributes['M12'].value),
         float(xml_quaternion.attributes['M22'].value),
         float(xml_quaternion.attributes['M32'].value)]))


def create_matrix(mat, doc):
    matrix = doc.createElement('FixupMatrix')
    matrix.setAttribute('M00', str(mat[0][0]))
    matrix.setAttribute('M10', str(mat[0][1]))
    matrix.setAttribute('M20', str(mat[0][2]))
    matrix.setAttribute('M30', str(mat[0][3]))

    matrix.setAttribute('M01', str(mat[1][0]))
    matrix.setAttribute('M11', str(mat[1][1]))
    matrix.setAttribute('M21', str(mat[1][2]))
    matrix.setAttribute('M31', str(mat[1][3]))

    matrix.setAttribute('M02', str(mat[2][0]))
    matrix.setAttribute('M12', str(mat[2][1]))
    matrix.setAttribute('M22', str(mat[2][2]))
    matrix.setAttribute('M32', str(mat[2][3]))
    return matrix


def parse_objects(parent, name, parse_func, par1=None):
    result = []
    objects = parent.getElementsByTagName(name)
    if not objects:
        return result
    for obj in objects:
        if par1 is not None:
            result.append(parse_func(obj, par1))
        else:
            result.append(parse_func(obj))
    return result


def create_object_list(doc, name, objects, write_func, par1=None):
    xml_objects_list = doc.createElement(name)
    for obj in objects:
        if par1 is not None:
            xml_objects_list.appendChild(write_func(obj, doc, par1))
        else:
            xml_objects_list.appendChild(write_func(obj, doc))
    return xml_objects_list


#####################################################
#### new stuff

def create_node(self, identifier):
    return ET.SubElement(self, identifier)


def write_struct(struct, path):
    root = create_root()
    struct.create(root)
    write(root, path)


def write(root, path):
    file = open(path, 'w')
    # TODO: find a ElementTree only variant
    data = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")
    file.write(data)
    file.close()


def find_root(context, path):
    root = ET.parse(path).getroot()

    if root.tag != 'AssetDeclaration':
        context.error('file: ' + path  + ' does not contain a AssetDeclaration node!')
        return None
    return root


def create_root():
    root = ET.Element('AssetDeclaration')
    root.set('xmlns', 'uri:ea.com:eala:asset')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    return root


def parse_value_(xml_obj, cast_func=str):
    return cast_func(xml_obj.text)


def create_value_(value, parent, identifier):
    xml_obj = ET.SubElement(parent, identifier)
    xml_obj.text = str(value)


def parse_objects_(parent, name, parse_func, par1=None):
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


def create_object_list_(parent, name, objects, write_func, par1=None):
    xml_objects_list = ET.SubElement(parent, name)
    for obj in objects:
        if par1 is not None:
            write_func(obj, xml_objects_list, par1)
        else:
            write_func(obj, xml_objects_list)


def parse_vector2_(xml_vector2):
    return Vector((
        float(xml_vector2.get('X', 0.0)),
        float(xml_vector2.get('Y', 0.0))))


def create_vector2_(vec2, parent, name):
    vector = ET.SubElement(parent, name)
    vector.set('X', vec2.x)
    vector.set('Y', vec2.y)


def parse_vector_(xml_vector):
    return Vector((
        float(xml_vector.get('X', 0.0)),
        float(xml_vector.get('Y', 0.0)),
        float(xml_vector.get('Z', 0.0))))


def create_vector_(vec, parent, name):
    vector = ET.SubElement(parent, name)
    vector.set('X', vec.x)
    vector.set('Y', vec.y)
    vector.set('Z', vec.z)


def parse_quaternion_(xml_quaternion):
    return Quaternion((
        float(xml_quaternion.get('W', 1.0)),
        float(xml_quaternion.get('X', 0.0)),
        float(xml_quaternion.get('Y', 0.0)),
        float(xml_quaternion.get('Z', 0.0))))


def create_quaternion_(quat, parent, identifier='Rotation'):
    quaternion = ET.SubElement(parent, identifier)
    quaternion.set('W', quat[0])
    quaternion.set('X', quat[1])
    quaternion.set('Y', quat[2])
    quaternion.set('Z', quat[3])


def parse_matrix_(xml_matrix):
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


def create_matrix_(mat, parent, identifier='FixupMatrix'):
    matrix = ET.SubElement(parent, identifier)
    matrix.set('M00', mat[0][0])
    matrix.set('M01', mat[0][1])
    matrix.set('M02', mat[0][2])
    matrix.set('M03', mat[0][3])

    matrix.set('M10', mat[1][0])
    matrix.set('M11', mat[1][1])
    matrix.set('M12', mat[1][2])
    matrix.set('M13', mat[1][3])

    matrix.set('M20', mat[2][0])
    matrix.set('M21', mat[2][1])
    matrix.set('M22', mat[2][2])
    matrix.set('M23', mat[2][3])


