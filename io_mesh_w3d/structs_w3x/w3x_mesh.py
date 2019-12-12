# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector, Quaternion, Matrix

from io_mesh_w3d.structs_w3x.w3x_struct import Struct
from io_mesh_w3d.io_xml import *


class Triangle(Struct):
    verts = []
    normal = Vector((0, 0, 0))
    distance = 0.0

    @staticmethod
    def parse(xml_triangle):
        result = Triangle()

        xml_verts = xml_triangle.getElementsByTagName('V')
        for xml_vert in xml_verts:
            result.verts.append(xml_vert.value)

        result.normal = parse_vector(xml_triangle.getElementsByTagName('Nrm')[0])
        result.distance = xml_triangle.getElementsByTagName('Dist')[0].value
        return result

    def create(self, doc):
        result = doc.createElement('Triangle')
        for vert in self.verts:
            xml_vert = doc.createElement('V')
            xml_vert.value = vert
            result.appendChild(xml_vert)

        result.appendChild(create_vector(self.normal, doc, 'Nrm'))
        xml_distance = doc.createElement('Dist')
        xml_distance.value = self.distance
        result.appendChild(xml_distance)
        return result


class BoundingBox(Struct):
    min = Vector((0, 0, 0))
    max = Vector((0, 0, 0))

    @staticmethod
    def parse(xml_bounding_box):
        result = BoundingBox()

        xml_min = xml_bounding_box.getElementsByTagName('Min')[0]
        result.min = parse_vector(xml_min)

        xml_max = xml_bounding_box.getElementsByTagName('Max')[0]
        result.max = parse_vector(xml_max)
        return result

    def create(self, doc):
        result = doc.createElement('BoundingBox')
        result.appendChild(create_vector(self.min, doc, 'Min'))
        result.appendChild(create_vector(self.max, doc, 'Max'))
        return result


class BoundingSphere(Struct):
    radius = 0.0
    center = Vector((0, 0, 0))

    @staticmethod
    def parse(xml_bounding_sphere):
        result = BoundingSphere(
            radius=xml_mesh.attributes['Radius'].value)

        xml_center = xml_bounding_sphere.getElementsByTagName('Center')[0]
        result.center = parse_vector(xml_center)
        return result

    def create(self, doc):
        result = doc.createElement('BoundingSphere')
        result.appendChild(create_vector(self.center, doc, 'Center'))
        return result


#W3DMesh
class Mesh(Struct):
    id = ""
    geometry_type = ""
    bounding_box = None
    bounding_sphere = None
    vertices = []
    normals = []
    tex_coords = []
    shade_indices = []
    triangles = []
    fx_shader = None
    aabbtree = None

    @staticmethod
    def parse(xml_mesh):
        result = Mesh(
            id=xml_mesh.attributes['id'].value,
            geometry_type=xml_mesh.attributes['GeometryType'],
            bounding_box=None,
            bounding_sphere=None,
            vertices=[],
            normals=[],
            tex_coords=[],
            shade_indices=[],
            triangles=[],
            fx_shader=None,
            aabbtree=None)

        xml_bounding_box = xml_mesh.getElementsByTagName('BoundingBox')[0]
        result.bounding_box = BoundingBox.parse(xml_bounding_box)

        xml_bounding_sphere = xml_mesh.getElementsByTagName('BoundingSphere')[0]
        result.bounding_sphere = BoundingSphere.parse(xml_bounding_sphere)

        xml_vertices_object = xml_mesh.getElementsByTagName('Vertices')[0]
        xml_vertices = xml_vertices_object.getElementsByTagName('V')
        for xml_vertex in xml_vertices:
            result.vertices.append(parse_vector(xml_vertex))

        xml_normals_object = xml_mesh.getElementsByTagName('Normals')[0]
        xml_normals = xml_normals_object.getElementsByTagName('N')
        for xml_normal in xml_normals:
            result.normals.append(parse_vector(xml_normal))

        xml_texcoords_object = xml_mesh.getElementsByTagName('TexCoords')[0]
        xml_texcoords = xml_texcoords_object.getElementsByTagName('T')
        for xml_texcoord in xml_texcoords:
            result.tex_coords.append(parse_vector2(xml_texcoord))

        xml_shade_indices_object = xml_mesh.getElementsByTagName('ShadeIndices')[0]
        xml_shade_indices = xml_shade_indices_object.getElementsByTagName('I')
        for xml_shade_index in xml_shade_indices:
            result.shade_indices.append(xml_shade_index.value)

        xml_triangles_object = xml_mesh.getElementsByTagName('Triangles')[0]
        xml_triangles = xml_triangles_object.getElementsByTagName('T')
        for xml_triangle in xml_triangles:
            result.triangles.append(Triangle.parse(xml_triangle))

        #TODO: FxShader
        #TODO: AABTree

        return result


    def create(self, doc):
        #TODO

