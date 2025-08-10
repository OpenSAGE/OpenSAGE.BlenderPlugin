# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector
from io_mesh_w3d.common.structs.mesh_structs.aabbtree import *
from io_mesh_w3d.common.structs.mesh_structs.shader_material import *
from io_mesh_w3d.common.structs.mesh_structs.triangle import *
from io_mesh_w3d.common.structs.mesh_structs.vertex_influence import *
from io_mesh_w3d.w3d.structs.mesh_structs.prelit import *
from io_mesh_w3d.w3d.structs.version import Version
from io_mesh_w3d.w3x.structs.mesh_structs.bounding_box import *
from io_mesh_w3d.w3x.structs.mesh_structs.bounding_sphere import *

W3D_CHUNK_MESH_HEADER = 0x0000001F

# Geometry types
GEOMETRY_TYPE_NORMAL = 0x00000000
GEOMETRY_TYPE_HIDDEN = 0x00001000
GEOMETRY_TYPE_TWO_SIDED = 0x00002000
GEOMETRY_TYPE_CAST_SHADOW = 0x00008000
GEOMETRY_TYPE_CAMERA_ALIGNED = 0x00010000
GEOMETRY_TYPE_SKIN = 0x00020000
GEOMETRY_TYPE_CAMERA_ORIENTED = 0x00060000

# Prelit types
PRELIT_MASK = 0x0F000000
PRELIT_UNLIT = 0x01000000
PRELIT_VERTEX = 0x02000000
PRELIT_LIGHTMAP_MULTI_PASS = 0x04000000
PRELIT_LIGHTMAP_MULTI_TEXTURE = 0x08000000

# Vertex channels
VERTEX_CHANNEL_LOCATION = 0x01
VERTEX_CHANNEL_NORMAL = 0x02
VERTEX_CHANNEL_BONE_ID = 0x10
VERTEX_CHANNEL_TANGENT = 0x20
VERTEX_CHANNEL_BITANGENT = 0x40


class MeshHeader:
    def __init__(
            self,
            version=Version(
                major=4,
                minor=2),
            attrs=GEOMETRY_TYPE_NORMAL,
            mesh_name='',
            container_name='',
            face_count=0,
            vert_count=0,
            matl_count=0,
            damage_stage_count=0,
            sort_level=0,
            prelit_version=0,
            future_count=0,
            vert_channel_flags=0,
            face_channel_flags=1,
            min_corner=Vector(),
            max_corner=Vector(),
            sph_center=Vector(),
            sph_radius=0.0):
        self.version = version
        self.attrs = attrs
        self.mesh_name = mesh_name
        self.container_name = container_name
        self.face_count = face_count
        self.vert_count = vert_count
        self.matl_count = matl_count
        self.damage_stage_count = damage_stage_count
        self.sort_level = sort_level
        self.prelit_version = prelit_version
        self.future_count = future_count
        self.vert_channel_flags = vert_channel_flags
        self.face_channel_flags = face_channel_flags
        self.min_corner = min_corner
        self.max_corner = max_corner
        self.sph_center = sph_center
        self.sph_radius = sph_radius

    @staticmethod
    def read(io_stream):
        return MeshHeader(
            version=Version.read(io_stream),
            attrs=read_ulong(io_stream),
            mesh_name=read_fixed_string(io_stream),
            container_name=read_fixed_string(io_stream),
            face_count=read_ulong(io_stream),
            vert_count=read_ulong(io_stream),
            matl_count=read_ulong(io_stream),
            damage_stage_count=read_ulong(io_stream),
            sort_level=read_ulong(io_stream),
            prelit_version=read_ulong(io_stream),
            future_count=read_ulong(io_stream),
            vert_channel_flags=read_ulong(io_stream),
            face_channel_flags=read_ulong(io_stream),
            # bounding volumes
            min_corner=read_vector(io_stream),
            max_corner=read_vector(io_stream),
            sph_center=read_vector(io_stream),
            sph_radius=read_float(io_stream))

    @staticmethod
    def size(include_head=True):
        return const_size(116, include_head)

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_MESH_HEADER, io_stream, self.size(False))
        self.version.write(io_stream)
        write_ulong(self.attrs, io_stream)
        write_fixed_string(self.mesh_name, io_stream)
        write_fixed_string(self.container_name, io_stream)
        write_ulong(self.face_count, io_stream)
        write_ulong(self.vert_count, io_stream)
        write_ulong(self.matl_count, io_stream)
        write_ulong(self.damage_stage_count, io_stream)
        write_ulong(self.sort_level, io_stream)
        write_ulong(self.prelit_version, io_stream)
        write_ulong(self.future_count, io_stream)
        write_ulong(self.vert_channel_flags, io_stream)
        write_ulong(self.face_channel_flags, io_stream)
        write_vector(self.min_corner, io_stream)
        write_vector(self.max_corner, io_stream)
        write_vector(self.sph_center, io_stream)
        write_float(self.sph_radius, io_stream)


W3D_CHUNK_MESH = 0x00000000
W3D_CHUNK_VERTICES = 0x00000002
W3D_CHUNK_VERTICES_2 = 0xC00
W3D_CHUNK_VERTEX_NORMALS = 0x00000003
W3D_CHUNK_NORMALS_2 = 0xC01
W3D_CHUNK_MESH_USER_TEXT = 0x0000000C
W3D_CHUNK_VERTEX_INFLUENCES = 0x0000000E
W3D_CHUNK_TRIANGLES = 0x00000020
W3D_CHUNK_VERTEX_SHADE_INDICES = 0x00000022
W3D_CHUNK_SHADER_MATERIALS = 0x50
W3D_CHUNK_TANGENTS = 0x60
W3D_CHUNK_BITANGENTS = 0x61

# avoid naming collapse
class W3DMesh:
    def __init__(self):
        self.header = None
        self.user_text = ''
        self.verts = []
        self.normals = []
        self.verts_2 = []
        self.normals_2 = []
        self.tangents = []
        self.bitangents = []
        self.vert_infs = []
        self.triangles = []
        self.shade_ids = []
        self.mat_info = None
        self.shaders = []
        self.vert_materials = []
        self.textures = []
        self.shader_materials = []
        self.material_passes = []
        self.aabbtree = None
        self.prelit_unlit = None
        self.prelit_vertex = None
        self.prelit_lightmap_multi_pass = None
        self.prelit_lightmap_multi_texture = None

        # non struct properties
        self.multi_bone_skinned = False

    def validate(self, context):
        if len(self.header.mesh_name) >= STRING_LENGTH and context.file_format == 'W3D':
            context.error(f'mesh name \'{self.header.mesh_name}\' exceeds max length of {STRING_LENGTH}')
            return False
        return True

    def casts_shadow(self):
        return (self.header.attrs & GEOMETRY_TYPE_CAST_SHADOW) == GEOMETRY_TYPE_CAST_SHADOW

    def two_sided(self):
        return (self.header.attrs & GEOMETRY_TYPE_TWO_SIDED) == GEOMETRY_TYPE_TWO_SIDED

    def is_hidden(self):
        return (self.header.attrs & GEOMETRY_TYPE_HIDDEN) == GEOMETRY_TYPE_HIDDEN

    def is_skin(self):
        return (self.header.attrs & GEOMETRY_TYPE_SKIN) == GEOMETRY_TYPE_SKIN

    def is_camera_oriented(self):
        return (self.header.attrs & GEOMETRY_TYPE_CAMERA_ORIENTED) == GEOMETRY_TYPE_CAMERA_ORIENTED

    def is_camera_aligned(self):
        return (self.header.attrs & GEOMETRY_TYPE_CAMERA_ALIGNED) == GEOMETRY_TYPE_CAMERA_ALIGNED

    def container_name(self):
        return self.header.container_name

    # pure name. e.g. NEWSKIN
    def name(self):
        return self.header.mesh_name

    # unique name. e.g. SUANTIAIRSHIP_SKN.NEWSKIN
    def identifier(self):
        return self.header.container_name + '.' + self.name()

    def get_material_pass(self):
        if not self.material_passes:
            mat_pass = MaterialPass(shader_material_ids=[0])
            self.material_passes.append(mat_pass)
        return self.material_passes[0]

    @staticmethod
    def read(context, io_stream, chunk_end):
        result = W3DMesh()

        while io_stream.tell() < chunk_end:
            (chunk_type, chunk_size, subchunk_end) = read_chunk_head(io_stream)

            if chunk_type == W3D_CHUNK_VERTICES:
                result.verts = read_list(io_stream, subchunk_end, read_vector)
            elif chunk_type == W3D_CHUNK_VERTICES_2:
                context.info('-> vertices 2 chunk is not supported')
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_VERTEX_NORMALS:
                result.normals = read_list(io_stream, subchunk_end, read_vector)
            elif chunk_type == W3D_CHUNK_NORMALS_2:
                context.info('-> normals 2 chunk is not supported')
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_MESH_USER_TEXT:
                result.user_text = read_string(io_stream)
            elif chunk_type == W3D_CHUNK_VERTEX_INFLUENCES:
                result.vert_infs = read_list(io_stream, subchunk_end, VertexInfluence.read)
            elif chunk_type == W3D_CHUNK_MESH_HEADER:
                result.header = MeshHeader.read(io_stream)
            elif chunk_type == W3D_CHUNK_TRIANGLES:
                result.triangles = read_list(io_stream, subchunk_end, Triangle.read)
            elif chunk_type == W3D_CHUNK_VERTEX_SHADE_INDICES:
                result.shade_ids = read_list(io_stream, subchunk_end, read_long)
            elif chunk_type == W3D_CHUNK_MATERIAL_INFO:
                result.mat_info = MaterialInfo.read(io_stream)
            elif chunk_type == W3D_CHUNK_SHADERS:
                result.shaders = read_list(io_stream, subchunk_end, Shader.read)
            elif chunk_type == W3D_CHUNK_VERTEX_MATERIALS:
                result.vert_materials = read_chunk_array(context, io_stream, subchunk_end, W3D_CHUNK_VERTEX_MATERIAL,
                                                         VertexMaterial.read)
            elif chunk_type == W3D_CHUNK_TEXTURES:
                result.textures = read_chunk_array(context, io_stream, subchunk_end, W3D_CHUNK_TEXTURE, Texture.read)
            elif chunk_type == W3D_CHUNK_MATERIAL_PASS:
                result.material_passes.append(MaterialPass.read(context, io_stream, subchunk_end))
            elif chunk_type == W3D_CHUNK_SHADER_MATERIALS:
                result.shader_materials = read_chunk_array(context, io_stream, subchunk_end, W3D_CHUNK_SHADER_MATERIAL,
                                                           ShaderMaterial.read)
            elif chunk_type == W3D_CHUNK_TANGENTS:
                context.info('-> tangents are computed in blender')
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_BITANGENTS:
                context.info('-> bitangents are computed in blender')
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_AABBTREE:
                result.aabbtree = AABBTree.read(context, io_stream, subchunk_end)
            elif chunk_type == W3D_CHUNK_PRELIT_UNLIT:
                result.prelit_unlit = PrelitBase.read(context, io_stream, subchunk_end, chunk_type)
            elif chunk_type == W3D_CHUNK_PRELIT_VERTEX:
                result.prelit_vertex = PrelitBase.read(context, io_stream, subchunk_end, chunk_type)
            elif chunk_type == W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_PASS:
                result.prelit_lightmap_multi_pass = PrelitBase.read(context, io_stream, subchunk_end, chunk_type)
            elif chunk_type == W3D_CHUNK_PRELIT_LIGHTMAP_MULTI_TEXTURE:
                result.prelit_lightmap_multi_texture = PrelitBase.read(context, io_stream, subchunk_end, chunk_type)
            elif chunk_type == W3D_CHUNK_DEFORM:
                context.info('-> deform chunk is not supported')
                io_stream.seek(chunk_size, 1)
            elif chunk_type == W3D_CHUNK_PS2_SHADERS:
                context.info('-> ps2 shaders chunk is not supported')
                io_stream.seek(chunk_size, 1)
            else:
                skip_unknown_chunk(context, io_stream, chunk_type, chunk_size)
        return result

    def size(self, include_head=True):
        size = const_size(0, include_head)
        size += self.header.size()
        size += text_size(self.user_text)
        size += vec_list_size(self.verts)
        size += vec_list_size(self.normals)
        if self.multi_bone_skinned and self.verts_2:
            size += vec_list_size(self.verts_2)
        if self.multi_bone_skinned and self.normals_2:
            size += vec_list_size(self.normals_2)
        size += vec_list_size(self.tangents)
        size += vec_list_size(self.bitangents)
        size += list_size(self.triangles)
        size += list_size(self.vert_infs)
        size += list_size(self.shaders)
        size += list_size(self.textures)
        size += long_list_size(self.shade_ids)
        size += list_size(self.shader_materials)
        if self.mat_info is not None:
            size += self.mat_info.size()
        size += list_size(self.vert_materials)
        size += list_size(self.material_passes, False)
        if self.aabbtree is not None:
            size += self.aabbtree.size()
        if self.prelit_unlit is not None:
            size += self.prelit_unlit.size()
        if self.prelit_vertex is not None:
            size += self.prelit_vertex.size()
        if self.prelit_lightmap_multi_pass is not None:
            size += self.prelit_lightmap_multi_pass.size()
        if self.prelit_lightmap_multi_texture is not None:
            size += self.prelit_lightmap_multi_texture.size()
        return size

    def write(self, io_stream):
        write_chunk_head(W3D_CHUNK_MESH, io_stream, self.size(False), has_sub_chunks=True)
        self.header.write(io_stream)

        if len(self.user_text) > 0:
            write_chunk_head(
                W3D_CHUNK_MESH_USER_TEXT,
                io_stream,
                text_size(self.user_text, False))
            write_string(self.user_text, io_stream)

        write_chunk_head(W3D_CHUNK_VERTICES, io_stream, vec_list_size(self.verts, False))
        write_list(self.verts, io_stream, write_vector)

        if self.multi_bone_skinned and self.verts_2:
            write_chunk_head(W3D_CHUNK_VERTICES_2, io_stream, vec_list_size(self.verts_2, False))
            write_list(self.verts_2, io_stream, write_vector)

        write_chunk_head(W3D_CHUNK_VERTEX_NORMALS, io_stream, vec_list_size(self.normals, False))
        write_list(self.normals, io_stream, write_vector)

        if self.multi_bone_skinned and self.normals_2:
            write_chunk_head(W3D_CHUNK_NORMALS_2, io_stream, vec_list_size(self.normals_2, False))
            write_list(self.normals_2, io_stream, write_vector)

        if self.tangents:
            write_chunk_head(W3D_CHUNK_TANGENTS, io_stream, vec_list_size(self.tangents, False))
            write_list(self.tangents, io_stream, write_vector)

        if self.bitangents:
            write_chunk_head(W3D_CHUNK_BITANGENTS, io_stream, vec_list_size(self.bitangents, False))
            write_list(self.bitangents, io_stream, write_vector)

        write_chunk_head(W3D_CHUNK_TRIANGLES, io_stream, list_size(self.triangles, False))
        write_list(self.triangles, io_stream, Triangle.write)

        if self.vert_infs:
            write_chunk_head(W3D_CHUNK_VERTEX_INFLUENCES, io_stream, list_size(self.vert_infs, False))
            write_list(self.vert_infs, io_stream, VertexInfluence.write)

        if self.shade_ids:
            write_chunk_head(W3D_CHUNK_VERTEX_SHADE_INDICES, io_stream, long_list_size(self.shade_ids, False))
            write_list(self.shade_ids, io_stream, write_long)

        if self.mat_info is not None:
            self.mat_info.write(io_stream)

        if self.vert_materials:
            write_chunk_head(
                W3D_CHUNK_VERTEX_MATERIALS,
                io_stream,
                list_size(self.vert_materials, False),
                has_sub_chunks=True)
            write_list(self.vert_materials, io_stream, VertexMaterial.write)

        if self.shaders:
            write_chunk_head(W3D_CHUNK_SHADERS, io_stream, list_size(self.shaders, False))
            write_list(self.shaders, io_stream, Shader.write)

        if self.textures:
            write_chunk_head(
                W3D_CHUNK_TEXTURES,
                io_stream,
                list_size(self.textures, False),
                has_sub_chunks=True)
            write_list(self.textures, io_stream, Texture.write)

        if self.shader_materials:
            write_chunk_head(
                W3D_CHUNK_SHADER_MATERIALS,
                io_stream,
                list_size(self.shader_materials, False),
                has_sub_chunks=True)
            write_list(self.shader_materials, io_stream, ShaderMaterial.write)

        if self.material_passes:
            write_list(self.material_passes, io_stream, MaterialPass.write)

        if self.aabbtree is not None:
            self.aabbtree.write(io_stream)

        if self.prelit_unlit is not None:
            self.prelit_unlit.write(io_stream)

        if self.prelit_vertex is not None:
            self.prelit_vertex.write(io_stream)

        if self.prelit_lightmap_multi_pass is not None:
            self.prelit_lightmap_multi_pass.write(io_stream)

        if self.prelit_lightmap_multi_texture is not None:
            self.prelit_lightmap_multi_texture.write(io_stream)

    @staticmethod
    def parse(context, xml_mesh):
        result = W3DMesh()
        result.header = MeshHeader()

        identifier = xml_mesh.get('id')
        if '.' in identifier:
            (container_name, name) = identifier.split('.', 1)
            result.header.mesh_name = name
            result.header.container_name = container_name
        else:
            result.header.mesh_name = identifier

        result.header.attrs = GEOMETRY_TYPE_NORMAL
        if xml_mesh.get('GeometryType') == 'Skin':
            result.header.attrs |= GEOMETRY_TYPE_SKIN

        if bool(xml_mesh.get('Hidden', False)):
            result.header.attrs |= GEOMETRY_TYPE_HIDDEN

        if bool(xml_mesh.get('CastShadow', False)):
            result.header.attrs |= GEOMETRY_TYPE_CAST_SHADOW

        result.header.sort_level = int(xml_mesh.get('SortLevel', 0))

        bone_influences = []

        for child in xml_mesh:
            if child.tag == 'BoundingBox':
                bounding_box = BoundingBox.parse(child)
                result.header.min_corner = bounding_box.min
                result.header.max_corner = bounding_box.max
            elif child.tag == 'BoundingSphere':
                bounding_sphere = BoundingSphere.parse(child)
                result.header.sph_center = bounding_sphere.center
                result.header.sph_radius = bounding_sphere.radius
            elif child.tag == 'Vertices':
                if not result.verts:
                    result.header.vert_channel_flags |= VERTEX_CHANNEL_LOCATION
                    result.verts = parse_objects(child, 'V', parse_vector)
                    result.header.vert_count = len(result.verts)
                else:
                    context.info('secondary vertices are not supported')
            elif child.tag == 'Normals':
                if not result.normals:
                    result.header.vert_channel_flags |= VERTEX_CHANNEL_NORMAL
                    result.normals = parse_objects(child, 'N', parse_vector)
                else:
                    context.info('secondary normals are not supported')
            elif child.tag == 'Tangents':
                result.header.vert_channel_flags |= VERTEX_CHANNEL_TANGENT
                result.tangents = parse_objects(child, 'T', parse_vector)
            elif child.tag == 'Binormals':
                result.header.vert_channel_flags |= VERTEX_CHANNEL_BITANGENT
                result.bitangents = parse_objects(child, 'B', parse_vector)
            elif child.tag == 'Triangles':
                result.triangles = parse_objects(child, 'T', Triangle.parse)
                result.header.face_count = len(result.triangles)
            elif child.tag == 'VertexColors':
                mat_pass = result.get_material_pass()
                mat_pass.dcg = parse_objects(child, 'C', RGBA.parse)
            elif child.tag == 'TexCoords':
                mat_pass = result.get_material_pass()
                if not mat_pass.tx_coords:
                    mat_pass.tx_coords = parse_objects(child, 'T', parse_vector2)
                elif not mat_pass.tx_coords_2:
                    mat_pass.tx_coords_2 = parse_objects(child, 'T', parse_vector2)
                else:
                    context.warning('more than 2 uv coords in the file!')
            elif child.tag == 'ShadeIndices':
                result.shade_ids = parse_objects(child, 'I', parse_int_value)
                context.info('shade indices are not supported')
            elif child.tag == 'BoneInfluences':
                result.header.vert_channel_flags |= VERTEX_CHANNEL_BONE_ID
                bone_influences.append(child.findall('I'))
            elif child.tag == 'FXShader':
                result.shader_materials.append(ShaderMaterial.parse(child))
                result.header.matl_count = len(result.shader_materials)
            elif child.tag == 'AABTree':
                result.aabbtree = AABBTree.parse(child)
            else:
                context.warning(f'unhandled node \'{child.tag}\' in W3DMesh!')

        if bone_influences:
            bone_infs = bone_influences[0]
            xtra_infs = [None] * len(bone_influences[0])

            if len(bone_influences) > 1:
                xtra_infs = bone_influences[1]

            for i, inf in enumerate(bone_infs):
                result.vert_infs.append(VertexInfluence.parse(inf, xtra_infs[i]))

        result.mat_info = MaterialInfo(pass_count=len(result.material_passes))
        return result

    def create(self, parent):
        xml_mesh = create_node(parent, 'W3DMesh')
        identifier = self.header.container_name + "." + self.header.mesh_name
        xml_mesh.set('id', identifier)

        if self.casts_shadow():
            xml_mesh.set('CastShadow', 'true')

        if self.is_hidden():
            xml_mesh.set('Hidden', 'true')

        xml_mesh.set('SortLevel', str(self.header.sort_level))

        xml_mesh.set('GeometryType', 'Normal')
        if self.is_camera_aligned():
            xml_mesh.set('GeometryType', 'CameraAligned')
        if self.is_camera_oriented():
            xml_mesh.set('GeometryType', 'CameraOriented')
        if self.is_skin():
            xml_mesh.set('GeometryType', 'Skin')

        box = BoundingBox(
            min=self.header.min_corner,
            max=self.header.max_corner)
        box.create(xml_mesh)

        sphere = BoundingSphere(
            center=self.header.sph_center,
            radius=self.header.sph_radius)
        sphere.create(xml_mesh)

        create_object_list(xml_mesh, 'Vertices', self.verts, create_vector, 'V')

        if self.multi_bone_skinned and self.verts_2:
            create_object_list(xml_mesh, 'Vertices', self.verts_2, create_vector, 'V')

        create_object_list(xml_mesh, 'Normals', self.normals, create_vector, 'N')

        if self.multi_bone_skinned and self.normals_2:
            create_object_list(xml_mesh, 'Normals', self.normals_2, create_vector, 'N')

        if self.tangents:
            create_object_list(xml_mesh, 'Tangents', self.tangents, create_vector, 'T')

        if self.bitangents:
            create_object_list(xml_mesh, 'Binormals', self.bitangents, create_vector, 'B')

        if self.material_passes:
            if self.material_passes[0].dcg:
                create_object_list(xml_mesh, 'VertexColors', self.get_material_pass().dcg, RGBA.create)
            create_object_list(xml_mesh, 'TexCoords', self.material_passes[0].tx_coords, create_vector2, 'T')
            if self.material_passes[0].tx_coords_2:
                create_object_list(xml_mesh, 'TexCoords', self.material_passes[0].tx_coords_2, create_vector2, 'T')

        if self.vert_infs:
            vertex_influences = create_node(xml_mesh, 'BoneInfluences')
            vertex_influences2 = None
            if self.multi_bone_skinned:
                vertex_influences2 = create_node(xml_mesh, 'BoneInfluences')

            for vert_inf in self.vert_infs:
                vert_inf.create(vertex_influences, vertex_influences2)

        create_object_list(xml_mesh, 'ShadeIndices', self.shade_ids, create_value, 'I')

        create_object_list(xml_mesh, 'Triangles', self.triangles, Triangle.create)

        for shader_material in self.shader_materials:
            shader_material.create(xml_mesh)

        if self.aabbtree is not None:
            self.aabbtree.create(xml_mesh)


##########################################################################
# Unsupported
##########################################################################


W3D_CHUNK_DEFORM = 0x00000058
W3D_CHUNK_PS2_SHADERS = 0x00000080
