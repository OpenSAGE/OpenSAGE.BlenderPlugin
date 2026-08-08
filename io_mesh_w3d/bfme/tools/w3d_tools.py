# <pep8 compliant>
"""Utilities for preparing a model for W3D export."""

import math
from collections import deque

import bmesh
import bpy
import numpy as np
from bpy.props import CollectionProperty, IntProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup, UIList
from mathutils import Vector

from .. import utils

UV_EPSILON = 0.0001
MERGE_DISTANCE = 0.0001

Z_SLICE_COUNT = 10
Z_DENSITY_THRESHOLD = 0.3
CYLINDER_MAX_VARIANCE = 0.4
MIN_REGION_VERTICES = 10
MIN_CORNER_VERTICES = 20
MIN_CORNER_SIZE_RATIO = 0.2

OCTANTS = ((1, 1, 1), (-1, 1, 1), (1, -1, 1), (-1, -1, 1),
           (1, 1, -1), (-1, 1, -1), (1, -1, -1), (-1, -1, -1))


class W3D_BoneEntry(PropertyGroup):
    name: StringProperty(name='Name', description='Bone name prefix (e.g. FIRE, SMOKE)', default='BONE')
    count: IntProperty(name='Count', description='Number of bones to create', default=3, min=1, max=20)


class W3D_UL_bone_list(UIList):
    def draw_item(self, _context, layout, _data, item, _icon, _active_data, _active_propname, _index=0, _flt_flag=0):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, 'name', text='', emboss=False)
            row.prop(item, 'count', text='')


##########################################################################
# uv mapping
##########################################################################


class W3D_OT_fix_uv_mapping(Operator):
    bl_idname = 'w3d.fix_uv_mapping'
    bl_label = 'Fix UV Mapping'
    bl_description = 'Merge doubles and split the vertices along the UV island boundaries'

    def execute(self, context):
        mesh_objects = [obj for obj in context.scene.objects if obj.type == 'MESH' and obj.data.uv_layers]
        if not mesh_objects:
            self.report({'WARNING'}, 'No mesh objects with UV layers found')
            return {'CANCELLED'}

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        fixed = []
        for obj in mesh_objects:
            try:
                if self.fix_mesh(obj.data):
                    fixed.append(obj)
            except Exception as error:
                print(f'[W3D_TOOLS] UV fix failed for {obj.name}: {error}')

        # shade_smooth() on the mesh avoids the selection juggling an operator call needs
        for obj in fixed:
            obj.data.shade_smooth()

        if fixed:
            self.report({'INFO'}, f'Fixed UV mapping for {len(fixed)} mesh(es)')
        else:
            self.report({'INFO'}, 'No UV issues found')
        return {'FINISHED'}

    def fix_mesh(self, mesh):
        b_mesh = bmesh.new()
        try:
            b_mesh.from_mesh(mesh)

            before = len(b_mesh.verts)
            bmesh.ops.remove_doubles(b_mesh, verts=b_mesh.verts, dist=MERGE_DISTANCE)
            merged = before - len(b_mesh.verts)

            uv_layer = b_mesh.loops.layers.uv.active
            split = 0
            if uv_layer is not None:
                split = self.split_uv_islands(b_mesh, uv_layer)

            if not merged and not split:
                return False

            b_mesh.to_mesh(mesh)
            mesh.update()
            return True
        finally:
            b_mesh.free()

    @staticmethod
    def split_uv_islands(b_mesh, uv_layer):
        """Split every edge where the UVs of the two adjacent faces do not line up."""
        seams = []

        for edge in b_mesh.edges:
            if len(edge.link_faces) != 2:
                continue

            face_a, face_b = edge.link_faces
            # only the two vertices of this edge matter, so look their loops up
            # directly instead of building a loop map for both whole faces
            for vertex in edge.verts:
                uv_a = _loop_uv(face_a, vertex, uv_layer)
                uv_b = _loop_uv(face_b, vertex, uv_layer)
                if uv_a is None or uv_b is None:
                    continue
                if abs(uv_a[0] - uv_b[0]) > UV_EPSILON or abs(uv_a[1] - uv_b[1]) > UV_EPSILON:
                    seams.append(edge)
                    edge.seam = True
                    break

        if not seams:
            return 0

        bmesh.ops.split_edges(b_mesh, edges=seams)
        return len(seams)


def _loop_uv(face, vertex, uv_layer):
    for loop in face.loops:
        if loop.vert == vertex:
            return loop[uv_layer].uv
    return None


def uv_islands(b_mesh, uv_layer):
    """Faces grouped into UV islands, kept for callers that want the grouping."""
    visited = set()
    islands = []

    for start in b_mesh.faces:
        if start in visited:
            continue

        island = set()
        # a deque popleft is O(1), list.pop(0) would make the flood fill quadratic
        queue = deque([start])
        visited.add(start)

        while queue:
            face = queue.popleft()
            island.add(face)

            for edge in face.edges:
                for neighbour in edge.link_faces:
                    if neighbour is face or neighbour in visited:
                        continue
                    if all(_uv_matches(face, neighbour, vertex, uv_layer) for vertex in edge.verts):
                        visited.add(neighbour)
                        queue.append(neighbour)

        islands.append(island)

    return islands


def _uv_matches(face_a, face_b, vertex, uv_layer):
    uv_a = _loop_uv(face_a, vertex, uv_layer)
    uv_b = _loop_uv(face_b, vertex, uv_layer)
    if uv_a is None or uv_b is None:
        return True
    return abs(uv_a[0] - uv_b[0]) < UV_EPSILON and abs(uv_a[1] - uv_b[1]) < UV_EPSILON


##########################################################################
# structure
##########################################################################


class W3D_OT_create_structure(Operator):
    bl_idname = 'w3d.create_structure'
    bl_label = 'Create Structure'
    bl_description = 'Create the W3D armature structure for all meshes'

    def execute(self, context):
        scene = context.scene
        container_name = scene.w3d_structure_name

        if not container_name:
            self.report({'ERROR'}, 'Please enter a structure name')
            return {'CANCELLED'}

        existing = [obj.name for obj in scene.objects if obj.type == 'ARMATURE']
        if existing:
            self.report({'ERROR'}, f"Scene already contains armature(s): {', '.join(existing)}.")
            return {'CANCELLED'}

        mesh_objects = [obj for obj in scene.objects if obj.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, 'No mesh objects found in scene')
            return {'CANCELLED'}

        armature = bpy.data.armatures.new(container_name)
        armature_object = bpy.data.objects.new(container_name, armature)
        scene.collection.objects.link(armature_object)

        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = armature_object
        armature_object.select_set(True)

        armature_object.rotation_mode = 'XYZ'
        armature_object.rotation_euler[0] = -math.pi / 2
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

        bpy.ops.object.mode_set(mode='EDIT')
        for obj in mesh_objects:
            bone = armature.edit_bones.new(obj.name)
            bone.head = (0, 0, 0)
            bone.tail = (0, 1, 0)
        bpy.ops.object.mode_set(mode='OBJECT')

        for obj in mesh_objects:
            obj.parent = armature_object
            obj.parent_type = 'BONE'
            obj.parent_bone = obj.name

        self.report({'INFO'}, f"Created structure '{container_name}' with {len(mesh_objects)} bones")
        return {'FINISHED'}


##########################################################################
# collision geometry
##########################################################################


class W3D_OT_create_geometry(Operator):
    bl_idname = 'w3d.create_geometry'
    bl_label = 'Create Geometry'
    bl_description = 'Create adaptive collision geometry for the scene'

    SCALE_XY = 0.60
    SCALE_Z = 0.85

    def execute(self, context):
        scene = context.scene
        mesh_objects = [obj for obj in scene.objects
                        if obj.type == 'MESH' and obj.data.object_type == 'MESH']

        if not mesh_objects:
            self.report({'ERROR'}, 'No mesh objects found')
            return {'CANCELLED'}

        analysis = analyze_meshes(mesh_objects)
        if analysis is None:
            self.report({'ERROR'}, 'The meshes do not have any vertices')
            return {'CANCELLED'}

        geometries = self.create_geometries(context, analysis, scene.w3d_geometry_count)
        scene.w3d_geometry_ini_text = generate_ini_text(geometries)
        write_text_block(scene.w3d_geometry_ini_text)

        self.report({'INFO'}, f'Created {len(geometries)} adaptive geometries')
        return {'FINISHED'}

    def create_geometries(self, context, analysis, budget):
        geometries = [self.create_main_body(context, analysis)]
        budget -= 1

        cylinders = analysis['cylindrical_features']
        if budget > 0 and cylinders:
            cylinders.sort(key=lambda feature: feature['confidence'] * feature['height'], reverse=True)
            for index in range(min(budget, len(cylinders), 3)):
                geometries.append(self.create_cylinder(context, cylinders[index], index))
                budget -= 1

        corners = analysis['corner_features']
        if budget > 0 and corners:
            corners.sort(key=lambda corner: corner['size'].length, reverse=True)
            for index in range(min(budget, len(corners))):
                geometries.append(self.create_corner_box(context, corners[index], index))
                budget -= 1

        if budget > 0:
            geometries.extend(self.create_support_boxes(context, analysis, budget))

        return geometries

    @staticmethod
    def _add(context, primitive, location, scale, name, geometry_type):
        primitive(location=location)
        geometry = context.active_object
        geometry.scale = scale
        geometry.name = name
        geometry.data.object_type = 'GEOMETRY'
        geometry.data.geometry_type = geometry_type
        return geometry

    def create_main_body(self, context, analysis):
        center = analysis['center']
        size = analysis['size']
        scaled = Vector((size.x * self.SCALE_XY, size.y * self.SCALE_XY, size.z * self.SCALE_Z))
        location = Vector((center.x, center.y, center.z - size.z / 2 + scaled.z / 2))

        if analysis['is_round_base'] and analysis['height_ratio'] > 1.5:
            radius = min(scaled.x, scaled.y) / 2
            return self._add(context, bpy.ops.mesh.primitive_cylinder_add, location,
                             Vector((radius, radius, scaled.z / 2)), 'GEOMETRY_MainBody', 'CYLINDER')

        return self._add(context, bpy.ops.mesh.primitive_cube_add, location,
                         scaled / 2, 'GEOMETRY_MainBody', 'BOX')

    def create_cylinder(self, context, feature, index):
        radius = feature['radius'] * self.SCALE_XY
        height = feature['height'] * self.SCALE_Z
        location = Vector((feature['center'].x, feature['center'].y, feature['z_min'] + height / 2))

        return self._add(context, bpy.ops.mesh.primitive_cylinder_add, location,
                         Vector((radius, radius, height / 2)),
                         f'GEOMETRY_Tower_{index + 1:02d}', 'CYLINDER')

    def create_corner_box(self, context, corner, index):
        size = corner['size']
        scaled = Vector((size.x * self.SCALE_XY, size.y * self.SCALE_XY, size.z * self.SCALE_Z))
        center = corner['center']
        location = Vector((center.x, center.y, center.z - size.z / 2 + scaled.z / 2))

        return self._add(context, bpy.ops.mesh.primitive_cube_add, location, scaled / 2,
                         f'GEOMETRY_Corner_{index + 1:02d}', 'BOX')

    def create_support_boxes(self, context, analysis, count):
        center = analysis['center']
        size = analysis['size']
        bottom = center.z - size.z / 2
        radius = min(size.x, size.y) * 0.3 * self.SCALE_XY

        box_size = Vector((size.x * self.SCALE_XY * 0.3,
                           size.y * self.SCALE_XY * 0.3,
                           size.z * self.SCALE_Z * 0.3))

        boxes = []
        for index in range(count):
            angle = 2 * math.pi * index / count
            location = Vector((center.x + radius * math.cos(angle),
                               center.y + radius * math.sin(angle),
                               bottom + box_size.z / 2))
            boxes.append(self._add(context, bpy.ops.mesh.primitive_cube_add, location, box_size / 2,
                                   f'GEOMETRY_Support_{index + 1:02d}', 'BOX'))
        return boxes


def analyze_meshes(mesh_objects):
    """Bounds and shape features of the given meshes.

    All of this used to run as Python loops over every vertex, several times over.
    The coordinates are pulled out once as a numpy array and every measurement is a
    vectorised reduction over it.
    """
    coords = utils.stacked_world_coords(mesh_objects)
    if coords is None or not len(coords):
        return None

    minimum = coords.min(axis=0)
    maximum = coords.max(axis=0)
    size = Vector(maximum - minimum)
    center = Vector((minimum + maximum) / 2)

    regions = detect_z_regions(coords, minimum[2], maximum[2])
    height_ratio = size.z / ((size.x + size.y) / 2) if size.z > 0.001 else 0.1
    xy_ratio = size.x / size.y if size.y > 0.001 else 1.0

    return {
        'min': Vector(minimum),
        'max': Vector(maximum),
        'size': size,
        'center': center,
        'z_regions': regions,
        'cylindrical_features': detect_cylindrical_features(coords, regions),
        'corner_features': detect_corner_features(coords, center, size),
        'height_ratio': height_ratio,
        'is_round_base': 0.7 < xy_ratio < 1.3}


def detect_z_regions(coords, min_z, max_z):
    """Vertical bands of the model that carry a significant share of the vertices."""
    if max_z - min_z < 1e-9:
        return []

    densities, edges = np.histogram(coords[:, 2], bins=Z_SLICE_COUNT, range=(min_z, max_z))
    threshold = densities.max() * Z_DENSITY_THRESHOLD

    regions = []
    start = None

    for index, density in enumerate(densities):
        if density > threshold and start is None:
            start = index
        elif density <= threshold and start is not None:
            regions.append(_region(edges[start], edges[index]))
            start = None

    if start is not None:
        regions.append(_region(edges[start], max_z))

    return regions


def _region(low, high):
    return {'z_min': float(low), 'z_max': float(high),
            'z_center': float((low + high) / 2), 'height': float(high - low)}


def detect_cylindrical_features(coords, z_regions):
    """Bands whose vertices sit at a roughly constant radius, i.e. towers."""
    features = []
    heights = coords[:, 2]

    for region in z_regions:
        selected = coords[(heights >= region['z_min']) & (heights <= region['z_max'])]
        if len(selected) < MIN_REGION_VERTICES:
            continue

        center_xy = selected[:, :2].mean(axis=0)
        distances = np.linalg.norm(selected[:, :2] - center_xy, axis=1)

        average = float(distances.mean())
        if average <= 0.001:
            continue

        variance = float(distances.std()) / average
        if variance >= CYLINDER_MAX_VARIANCE:
            continue

        features.append({
            'center': Vector((center_xy[0], center_xy[1], region['z_center'])),
            'radius': average,
            'height': region['height'],
            'z_min': region['z_min'],
            'z_max': region['z_max'],
            'confidence': 1.0 - variance})

    return features


def detect_corner_features(coords, center, size):
    """Octants around the centre that hold a substantial chunk of the model."""
    corners = []
    offsets = coords - np.asarray(center, dtype=np.float64)
    diagonal = size.length

    for octant in OCTANTS:
        mask = np.all(offsets * np.asarray(octant, dtype=np.float64) >= 0, axis=1)
        selected = coords[mask]

        if len(selected) <= MIN_CORNER_VERTICES:
            continue

        corner_size = Vector(selected.max(axis=0) - selected.min(axis=0))
        if corner_size.length <= diagonal * MIN_CORNER_SIZE_RATIO:
            continue

        corners.append({
            'center': Vector(selected.mean(axis=0)),
            'size': corner_size,
            'octant': octant})

    return corners


def generate_ini_text(geometries):
    lines = []

    for index, obj in enumerate(geometries):
        geometry_type = obj.data.geometry_type

        if index == 0:
            lines.append(f'\tGeometry\t\t\t\t= {geometry_type}')
            lines.append('\tGeometryIsSmall\t\t\t= No')
        else:
            lines.append(f'\tAdditionalGeometry\t\t= {geometry_type}')

        lines.append(f'\tGeometryName\t\t\t= {obj.name}')

        scale = obj.scale
        if geometry_type == 'CYLINDER':
            lines.append(f'\tGeometryMajorRadius\t\t= {max(scale.x, scale.y):.3f}')
            lines.append(f'\tGeometryHeight\t\t\t= {scale.z * 2:.3f}')
        else:
            lines.append(f'\tGeometryMajorRadius\t\t= {scale.x:.3f}')
            lines.append(f'\tGeometryMinorRadius\t\t= {scale.y:.3f}')
            lines.append(f'\tGeometryHeight\t\t\t= {scale.z:.3f}')

        location = obj.location
        # the geometry offset is measured from the ground, so Z stays at zero
        if abs(location.x) > 0.01 or abs(location.y) > 0.01:
            lines.append(f'\tGeometryOffset\t\t\t= X:{location.x:.3f} Y:{location.y:.3f} Z:0.000')

        lines.append('')

    return '\n'.join(lines)


def write_text_block(content, name='W3D_Geometry.ini'):
    text_block = bpy.data.texts.get(name)
    if text_block is None:
        text_block = bpy.data.texts.new(name)
    else:
        text_block.clear()
    text_block.write(content)
    return text_block


class W3D_OT_export_geometry(Operator):
    bl_idname = 'w3d.export_geometry'
    bl_label = 'Export Geometry .ini'
    bl_description = 'Export the generated geometry data to an .ini file'

    filepath: StringProperty(subtype='FILE_PATH')
    filename_ext = '.ini'

    def execute(self, context):
        content = context.scene.w3d_geometry_ini_text
        if not content:
            self.report({'ERROR'}, 'No geometry data to export. Create geometries first.')
            return {'CANCELLED'}

        filepath = self.filepath
        if not filepath or filepath.endswith(('/', '\\')):
            filepath += 'untitled.ini'
        if not filepath.lower().endswith('.ini'):
            filepath += '.ini'

        try:
            with open(filepath, 'w') as file:
                file.write(content)
        except OSError as error:
            self.report({'ERROR'}, f'Export failed: {error}')
            return {'CANCELLED'}

        self.report({'INFO'}, f'Exported geometry to {filepath}')
        return {'FINISHED'}

    def invoke(self, context, _event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class W3D_OT_clean_geometry(Operator):
    bl_idname = 'w3d.clean_geometry'
    bl_label = 'Clean Geometry'
    bl_description = 'Delete the created geometry objects and clear the generated text'

    def execute(self, context):
        scene = context.scene

        doomed = [obj for obj in scene.objects
                  if obj.type == 'MESH' and getattr(obj.data, 'object_type', None) == 'GEOMETRY']
        for obj in doomed:
            bpy.data.objects.remove(obj, do_unlink=True)

        text_block = bpy.data.texts.get('W3D_Geometry.ini')
        if text_block is not None:
            bpy.data.texts.remove(text_block)

        scene.w3d_geometry_ini_text = ''

        self.report({'INFO'}, f'Deleted {len(doomed)} geometry object(s)')
        return {'FINISHED'}


##########################################################################
# bones
##########################################################################


class W3D_OT_add_bone_entry(Operator):
    bl_idname = 'w3d.add_bone_entry'
    bl_label = 'Add Bone Type'

    def execute(self, context):
        context.scene.w3d_bone_entries.add()
        return {'FINISHED'}


class W3D_OT_remove_bone_entry(Operator):
    bl_idname = 'w3d.remove_bone_entry'
    bl_label = 'Remove Bone Type'

    index: IntProperty()

    def execute(self, context):
        entries = context.scene.w3d_bone_entries
        if 0 <= self.index < len(entries):
            entries.remove(self.index)
        return {'FINISHED'}


class W3D_OT_create_bones(Operator):
    bl_idname = 'w3d.create_bones'
    bl_label = 'Create Bones'
    bl_description = 'Create bones evenly distributed over the upper outer surface'

    def execute(self, context):
        scene = context.scene

        if not len(scene.w3d_bone_entries):
            self.report({'ERROR'}, 'No bone types defined')
            return {'CANCELLED'}

        mesh_objects = [obj for obj in scene.objects if obj.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, 'No mesh objects found')
            return {'CANCELLED'}

        armature_object = next((obj for obj in scene.objects if obj.type == 'ARMATURE'), None)
        if armature_object is None:
            self.report({'ERROR'}, 'No armature found. Create the structure first.')
            return {'CANCELLED'}

        context.view_layer.objects.active = armature_object
        bpy.ops.object.mode_set(mode='EDIT')

        edit_bones = armature_object.data.edit_bones
        existing = {bone.name for bone in edit_bones}

        wanted = [f'{entry.name}{index + 1:02d}'
                  for entry in scene.w3d_bone_entries
                  for index in range(entry.count)]
        missing = [name for name in wanted if name not in existing]

        if not missing:
            bpy.ops.object.mode_set(mode='OBJECT')
            self.report({'WARNING'}, 'All bones already exist')
            return {'CANCELLED'}

        positions = distributed_surface_positions(mesh_objects, len(missing))

        created = 0
        for name, position in zip(missing, positions):
            bone = edit_bones.new(name)
            bone.head = position
            bone.tail = position + Vector((0, 0, 0.5))
            created += 1

        bpy.ops.object.mode_set(mode='OBJECT')

        self.report({'INFO'}, f'Created {created} new bones')
        return {'FINISHED'}


def distributed_surface_positions(mesh_objects, count):
    """Positions spread evenly around the upper outer surface of the meshes."""
    if count <= 0:
        return []

    coords = utils.stacked_world_coords(mesh_objects)
    if coords is None or not len(coords):
        return []

    minimum = coords.min(axis=0)
    maximum = coords.max(axis=0)
    center = (minimum + maximum) / 2

    # only the upper 30 percent of the model carries effect bones
    threshold = minimum[2] + (maximum[2] - minimum[2]) * 0.7
    upper = coords[coords[:, 2] >= threshold]
    if not len(upper):
        upper = coords

    offsets = upper[:, :2] - center[:2]
    lengths = np.linalg.norm(offsets, axis=1)
    valid = lengths > 0.001
    if not valid.any():
        return [Vector(point) for point in upper[:count]]

    upper = upper[valid]
    directions = offsets[valid] / lengths[valid, None]

    angles = 2 * math.pi * np.arange(count) / count
    wanted = np.stack((np.cos(angles), np.sin(angles)), axis=1)

    # one matrix product picks the best vertex for every direction at once, instead
    # of scanning all vertices again for each of them
    best = np.argmax(directions @ wanted.T, axis=0)
    return [Vector(upper[index]) for index in best]


##########################################################################
# panel
##########################################################################


class W3D_TOOLS_PT_panel(Panel):
    bl_label = 'W3D Tools'
    bl_idname = 'W3D_TOOLS_PT_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'SCENE_PT_bfme'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text='UV Mapping', icon='UV')
        box.operator('w3d.fix_uv_mapping', icon='UV')

        box = layout.box()
        box.label(text='Structure', icon='ARMATURE_DATA')
        box.prop(scene, 'w3d_structure_name')
        box.operator('w3d.create_structure', icon='BONE_DATA')

        box = layout.box()
        box.label(text='Collision Geometry', icon='MESH_CUBE')
        box.prop(scene, 'w3d_geometry_count', text='Count')

        row = box.row(align=True)
        row.operator('w3d.create_geometry', icon='ADD')
        row.operator('w3d.clean_geometry', icon='TRASH')

        if scene.w3d_geometry_ini_text:
            box.separator()
            box.operator('w3d.export_geometry', icon='EXPORT', text='Export .ini File')

        box = layout.box()
        box.label(text='Create Bones', icon='BONE_DATA')

        row = box.row()
        row.template_list('W3D_UL_bone_list', '', scene, 'w3d_bone_entries',
                          scene, 'w3d_bone_entries_index', rows=3)

        column = row.column(align=True)
        column.operator('w3d.add_bone_entry', icon='ADD', text='')
        column.operator('w3d.remove_bone_entry', icon='REMOVE', text='').index = scene.w3d_bone_entries_index

        box.operator('w3d.create_bones', icon='BONE_DATA')


DEFAULT_BONE_ENTRIES = (('FIRE', 3), ('SMOKE', 3), ('ARROW', 3))


@bpy.app.handlers.persistent
def init_default_bone_entries(_dummy=None):
    """Seed the bone list of every scene that does not have one yet.

    Defined at module level so re-registering the add-on finds the handler that is
    already installed, instead of appending a fresh closure every time.
    """
    # while Blender registers add-ons at startup 'bpy.data' is still restricted,
    # the load_post handler then does the seeding once the file is available
    scenes = getattr(bpy.data, 'scenes', None)
    if scenes is None:
        return

    for scene in scenes:
        if len(scene.w3d_bone_entries):
            continue
        for name, count in DEFAULT_BONE_ENTRIES:
            entry = scene.w3d_bone_entries.add()
            entry.name = name
            entry.count = count


CLASSES = (
    W3D_BoneEntry,
    W3D_UL_bone_list,
    W3D_OT_fix_uv_mapping,
    W3D_OT_create_structure,
    W3D_OT_create_geometry,
    W3D_OT_export_geometry,
    W3D_OT_clean_geometry,
    W3D_OT_add_bone_entry,
    W3D_OT_remove_bone_entry,
    W3D_OT_create_bones,
    W3D_TOOLS_PT_panel)

SCENE_PROPERTIES = (
    'w3d_structure_name',
    'w3d_bone_entries',
    'w3d_bone_entries_index',
    'w3d_geometry_ini_text',
    'w3d_geometry_count')


def register():
    for class_ in CLASSES:
        bpy.utils.register_class(class_)

    scene = bpy.types.Scene
    scene.w3d_structure_name = StringProperty(
        name='Name', description='Structure/container name', default='CONTAINER')
    scene.w3d_bone_entries = CollectionProperty(type=W3D_BoneEntry)
    scene.w3d_bone_entries_index = IntProperty(default=0)
    scene.w3d_geometry_ini_text = StringProperty(
        name='Geometry INI', description='Generated .ini text', default='')
    scene.w3d_geometry_count = IntProperty(
        name='Geometry Count', description='Number of geometry objects to create',
        default=1, min=1, max=10)

    if init_default_bone_entries not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(init_default_bone_entries)

    init_default_bone_entries()


def unregister():
    if init_default_bone_entries in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(init_default_bone_entries)

    for name in SCENE_PROPERTIES:
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)

    for class_ in reversed(CLASSES):
        bpy.utils.unregister_class(class_)
