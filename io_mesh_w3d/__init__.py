# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os
import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from io_mesh_w3d.export_utils import save
from io_mesh_w3d.custom_properties import *


bl_info = {
    'name': 'Import/Export Westwood W3D Format (.w3d/.w3x)',
    'author': 'OpenSage Developers',
    'version': (0, 4, 6),
    "blender": (2, 82, 0),
    'location': 'File > Import/Export > Westwood W3D (.w3d/.w3x)',
    'description': 'Import or Export the Westwood W3D-Format (.w3d/.w3x)',
    'warning': 'Still in Progress',
    'wiki_url': 'https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin',
    'tracker_url': 'https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin/issues',
    'support': 'OFFICIAL',
    'category': 'Import-Export'}


class ExportW3D(bpy.types.Operator, ExportHelper):
    '''Export to Westwood 3D file format (.w3d/.w3x)'''
    bl_idname = 'export_mesh.westwood_w3d'
    bl_label = 'Export W3D/W3X'
    bl_options = {'UNDO', 'PRESET'}

    filename_ext = ''

    filter_glob: StringProperty(default='*.w3d;*.w3x', options={'HIDDEN'})

    file_format: bpy.props.EnumProperty(
        name="Format",
        items=(
            ('W3D',
             'Westwood 3D Binary (.w3d)',
             'Exports to W3D format, which was used in earlier SAGE games.'
             'Namely Command and Conquer Generals and the Battle for Middleearth series'),
            ('W3X',
             'Westwood 3D XML (.w3x)',
             'Exports to W3X format, which was used in later SAGE games.'
             'Namely everything starting from Command and Conquer 3')),
        description="Select the export file format",
        default='W3D')

    export_mode: EnumProperty(
        name='Mode',
        items=(
            ('HM',
             'Hierarchical Model',
             'This will export all the meshes of the scene with hierarchy/skeleton data'),
            ('HAM',
             'Hierarchical Animated Model',
             'This will export all the meshes of the scene with hierarchy/skeleton and animation data'),
            ('A',
             'Animation',
             'This will export the animation without any geometry or hierarchy/skeleton data'),
            ('H',
             'Hierarchy',
             'This will export the hierarchy/skeleton without any geometry or animation data'),
            ('M',
             'Mesh',
             'This will export a simple mesh (only the first of the scene if there are multiple), \
                without any hierarchy/skeleton and animation data')),
        description='Select the export mode',
        default='HM')

    use_existing_skeleton: BoolProperty(
        name='Use existing skeleton', description='Use an already existing skeleton (.skn)', default=False)

    animation_compression: EnumProperty(
        name='Compression',
        items=(('U', 'Uncompressed', 'This will not compress the animations'),
               ('TC', 'TimeCoded', 'This will export the animation with keyframes'),
               # ('AD', 'AdaptiveDelta',
               # 'This will use adaptive delta compression to reduce size'),
               ),
        description='The method used for compressing the animation data',
        default='U')

    force_vertex_materials: BoolProperty(
        name='Force Vertex Materials', description='Export all materials as Vertex Materials only', default=False)

    individual_files: BoolProperty(
        name='Individual files',
        description='Creates an individual file for each mesh, boundingbox and the hierarchy',
        default=False)

    create_texture_xmls: BoolProperty(
        name='Create texture xml files', description='Creates an .xml file for each used texture', default=False)

    will_save_settings: BoolProperty(default=False)

    scene_key = 'w3dExportSettings'

    def info(self, msg):
        print('INFO: ' + str(msg))
        self.report({'INFO'}, str(msg))

    def warning(self, msg):
        print('WARNING: ' + str(msg))
        self.report({'WARNING'}, str(msg))

    def error(self, msg):
        print('ERROR: ' + str(msg))
        self.report({'ERROR'}, str(msg))

    def invoke(self, context, event):
        settings = context.scene.get(self.scene_key)
        self.will_save_settings = False
        if settings:
            try:
                for (k, v) in settings.items():
                    setattr(self, k, v)
                self.will_save_settings = True

            except (AttributeError, TypeError):
                self.error('Loading export settings failed. Removed corrupted settings')
                del context.scene[self.scene_key]

        return ExportHelper.invoke(self, context, event)

    def save_settings(self, context):
        all_props = self.properties
        export_props = {x: getattr(self, x) for x in dir(
            all_props) if x.startswith('export_') and all_props.get(x) is not None}

        context.scene[self.scene_key] = export_props

    def execute(self, context):
        if self.will_save_settings:
            self.save_settings(context)

        export_settings = {'mode': self.export_mode,
                           'compression': self.animation_compression,
                           'use_existing_skeleton': self.use_existing_skeleton,
                           'individual_files': self.individual_files,
                           'create_texture_xmls': self.create_texture_xmls}

        return save(self, export_settings)

    def draw(self, _context):
        self.draw_general_settings()
        if self.export_mode == 'HM':
            self.draw_use_existing_skeleton()
            if self.file_format == 'W3X':
                self.draw_individual_files()

        if self.file_format == 'W3X' and 'M' in self.export_mode:
            self.draw_create_texture_xmls()

        if self.file_format == 'W3D' and 'M' in self.export_mode:
            self.draw_force_vertex_materials()

        if (self.export_mode == 'A' or self.export_mode == 'HAM') \
                and not self.file_format == 'W3X':
            self.draw_animation_settings()

    def draw_general_settings(self):
        col = self.layout.box().column()
        col.prop(self, 'file_format')
        col = self.layout.box().column()
        col.prop(self, 'export_mode')

    def draw_use_existing_skeleton(self):
        col = self.layout.box().column()
        col.prop(self, 'use_existing_skeleton')

    def draw_animation_settings(self):
        col = self.layout.box().column()
        col.prop(self, 'animation_compression')

    def draw_force_vertex_materials(self):
        col = self.layout.box().column()
        col.prop(self, 'force_vertex_materials')

    def draw_individual_files(self):
        col = self.layout.box().column()
        col.prop(self, 'individual_files')

    def draw_create_texture_xmls(self):
        col = self.layout.box().column()
        col.prop(self, 'create_texture_xmls')


class ImportW3D(bpy.types.Operator, ImportHelper):
    '''Import from Westwood 3D file format (.w3d/.w3x)'''
    bl_idname = 'import_mesh.westwood_w3d'
    bl_label = 'Import W3D/W3X'
    bl_options = {'UNDO'}

    filter_glob: StringProperty(default='*.w3d;*.w3x', options={'HIDDEN'})

    def info(self, msg):
        print('INFO: ' + str(msg))
        self.report({'INFO'}, str(msg))

    def warning(self, msg):
        print('WARNING: ' + str(msg))
        self.report({'WARNING'}, str(msg))

    def error(self, msg):
        print('ERROR: ' + str(msg))
        self.report({'ERROR'}, str(msg))

    def execute(self, context):
        if self.filepath.lower().endswith('.w3d'):
            from .w3d.import_w3d import load
            load(self)
        else:
            from .w3x.import_w3x import load
            load(self)

        self.info('finished')
        return {'FINISHED'}


def menu_func_export(self, _context):
    self.layout.operator(ExportW3D.bl_idname, text='Westwood W3D (.w3d/.w3x)')


def menu_func_import(self, _context):
    self.layout.operator(ImportW3D.bl_idname, text='Westwood W3D (.w3d/.w3x)')

from bpy.types import Panel

class MESH_PROPERTIES_PANEL_PT_w3d(Panel):
    bl_label = 'W3D Properties'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'mesh'

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.active_object, 'object_type')
        if context.active_object.object_type == 'DAZZLE':
            col = layout.column()
            col.prop(context.active_object, 'dazzle_type')
        col = layout.column()
        col.prop(context.active_object, 'userText')


class BONE_PROPERTIES_PANEL_PT_w3d(Panel):
    bl_label = 'W3D Properties'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'bone'

    def draw(self, context):
        layout = self.layout
        if context.active_bone is not None:
            col = layout.column()
            col.prop(context.active_bone, 'visibility')


class MATERIAL_PROPERTIES_PANEL_PT_w3d(Panel):
    bl_label = 'W3D Properties'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    def draw(self, context):
        layout = self.layout
        mat = context.object.active_material
        col = layout.column()
        col.prop(mat, 'surface_type')


import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem

# all categories in a list
node_categories = [
    # identifier, label, items list
    NodeCategory('SOMENODES', 'Some Nodes', items=[
        # our basic node
        NodeItem('DecisionNode'),
    ]),
    NodeCategory('OTHERNODES', "Other Nodes", items=[
        # the node item can have additional settings,
        # which are applied to new nodes
        # NB: settings values are stored as string expressions,
        # for this reason they should be converted to strings using repr()
        NodeItem("CustomNodeType", label="Node A", settings={
            "my_string_prop": repr("Lorem ipsum dolor sit amet"),
            "my_float_prop": repr(1.0),
        }),
        NodeItem("CustomNodeType", label="Node B", settings={
            "my_string_prop": repr("consectetur adipisicing elit"),
            "my_float_prop": repr(2.0),
        }),
    ]),
]


from io_mesh_w3d.common.shading.node_socket_texture import NodeSocketTexture
from io_mesh_w3d.common.shading.node_socket_texture_alpha import NodeSocketTextureAlpha
from io_mesh_w3d.common.shading.node_socket_vec2 import NodeSocketVector2
from io_mesh_w3d.common.shading.node_socket_vec4 import NodeSocketVector4
from io_mesh_w3d.common.shading.node_socket_enum import NodeSocketMaterialAttributes


CLASSES = (
    NodeSocketTexture,
    NodeSocketTextureAlpha,
    NodeSocketVector2,
    NodeSocketVector4,
    NodeSocketMaterialAttributes,
    ExportW3D,
    ImportW3D,
    MESH_PROPERTIES_PANEL_PT_w3d,
    BONE_PROPERTIES_PANEL_PT_w3d)

def register_node_groups():
    from io_mesh_w3d.common.utils.node_group_creator import NodeGroupCreator
    dirname = os.path.dirname(__file__)
    directory = os.path.join(dirname, 'node_group_templates')

    for file in os.listdir(directory):
        if not file.endswith(".xml"):
            continue
        NodeGroupCreator().create(directory, file)

    from io_mesh_w3d.common.shading.vertex_material_group import VertexMaterialGroup
    VertexMaterialGroup.register(VertexMaterialGroup.name)

def register():
    for class_ in CLASSES:
        bpy.utils.register_class(class_)

    nodeitems_utils.register_node_categories('CUSTOM_NODES', node_categories)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    # workaround to register the node group when the addon is active
    # since bpy.data is not yet accessible
    import time
    from threading import Timer

    Timer(1, register_node_groups, ()).start()


def unregister():
    nodeitems_utils.unregister_node_categories('CUSTOM_NODES')

    for class_ in reversed(CLASSES):
        bpy.utils.unregister_class(class_)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == '__main__':
    register()
    register_node_groups()
