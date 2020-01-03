# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector
from io_mesh_w3d.struct import Struct
from io_mesh_w3d.w3x.io_xml import *

from io_mesh_w3d.shared.structs.mesh_structs.triangle import *
from io_mesh_w3d.w3x.structs.mesh_structs.bounding_box import *
from io_mesh_w3d.w3x.structs.mesh_structs.bounding_sphere import *
from io_mesh_w3d.w3x.structs.mesh_structs.fx_shader import *
from io_mesh_w3d.w3x.structs.mesh_structs.aabbtree import *


class Mesh(Struct):
    id = ""
    geometry_type = ""
    bounding_box = None
    bounding_sphere = None
    verts = []
    normals = []
    tangents = []
    bitangents = []
    tex_coords = []
    shade_indices = []
    triangles = []
    fx_shader = None
    aabbtree = None

    @staticmethod
    def parse(xml_mesh):
        result = Mesh(
            id=xml_mesh.attributes['id'].value,
            geometry_type=xml_mesh.attributes['GeometryType'].value,
            bounding_box=None,
            bounding_sphere=None,
            verts=[],
            normals=[],
            tangents=[],
            bitangents=[],
            tex_coords=[],
            shade_indices=[],
            triangles=[],
            fx_shader=None,
            aabbtree=None)

        xml_bounding_box = xml_mesh.getElementsByTagName('BoundingBox')[0]
        result.bounding_box = BoundingBox.parse(xml_bounding_box)

        xml_bounding_sphere = xml_mesh.getElementsByTagName('BoundingSphere')[0]
        result.bounding_sphere = BoundingSphere.parse(xml_bounding_sphere)

        result.verts = parse_object_list(xml_mesh, 'Vertices', 'V', parse_vector)
        result.normals = parse_object_list(xml_mesh, 'Normals', 'N', parse_vector)
        result.tangents = parse_object_list(xml_mesh, 'Tangents', 'T', parse_vector)
        result.bitangents = parse_object_list(xml_mesh, 'Bitangents', 'B', parse_vector)
        result.tex_coords = parse_object_list(xml_mesh, 'TexCoords', 'T', parse_vector2)
        result.shade_indices = parse_object_list(xml_mesh, 'ShadeIndices', 'I', parse_value, int)
        result.triangles = parse_object_list(xml_mesh, 'Triangles', 'T', Triangle.parse)

        xml_fx_shader = xml_mesh.getElementsByTagName('FXShader')[0]
        result.fx_shader = FXShader.parse(xml_fx_shader)

        xml_aabbtrees = xml_mesh.getElementsByTagName('AABTree')
        if xml_aabbtrees:
            result.aabbtree = AABBTree.parse(xml_aabbtrees[0])

        return result


    def create(self, doc):
        xml_mesh = doc.createElement('W3DMesh')
        xml_mesh.setAttribute('id', self.id)
        xml_mesh.setAttribute('GeometryType', self.geometry_type)

        xml_mesh.appendChild(self.bounding_box.create(doc))
        xml_mesh.appendChild(self.bounding_sphere.create(doc))

        xml_mesh.appendChild(create_object_list(doc, 'Vertices', self.verts, create_vector, 'V'))
        xml_mesh.appendChild(create_object_list(doc, 'Normals', self.normals, create_vector, 'N'))

        if self.tangents:
            xml_mesh.appendChild(create_object_list(doc, 'Tangents', self.tangents, create_vector, 'T'))

        if self.bitangents:
            xml_mesh.appendChild(create_object_list(doc, 'Bitangents', self.bitangents, create_vector, 'B'))

        xml_mesh.appendChild(create_object_list(doc, 'TexCoords', self.tex_coords, create_vector2, 'T'))
        xml_mesh.appendChild(create_object_list(doc, 'ShadeIndices', self.shade_indices, create_value, 'I'))
        xml_mesh.appendChild(create_object_list(doc, 'Triangles', self.triangles, Triangle.create))

        xml_mesh.appendChild(self.fx_shader.create(doc))
        xml_mesh.appendChild(self.aabbtree.create(doc))

        return xml_mesh