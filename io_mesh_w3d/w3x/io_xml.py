# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector, Quaternion, Matrix


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


def create_quaternion(quat, doc):
    quaternion = doc.createElement('Rotation')
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
    matrix= doc.createElement('FixupMatrix')
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


def parse_object_list(parent, name, identifier, parse_func, par1=None):
    result = []
    list_objects = parent.getElementsByTagName(name)
    if not list_objects:
        return result
    if len(list_objects) > 1:
        print("Error") # TODO: concrete error with report

    return parse_objects(list_objects[0], identifier, parse_func, par1)


def create_object_list(doc, name, objects, write_func, par1=None):
    xml_objects_list = doc.createElement(name)
    for obj in objects:
        if par1 is not None:
            xml_objects_list.appendChild(write_func(obj, doc, par1))
        else:
            xml_objects_list.appendChild(write_func(obj, doc))
    return xml_objects_list