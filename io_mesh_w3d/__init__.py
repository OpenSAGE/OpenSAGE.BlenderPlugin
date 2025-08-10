# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.types import Panel,Operator
from bpy_extras.io_utils import ImportHelper, ExportHelper
from io_mesh_w3d.utils import ReportHelper
from io_mesh_w3d.export_utils import save_data
from io_mesh_w3d.custom_properties import *
from io_mesh_w3d.geometry_export import *
from io_mesh_w3d.bone_volume_export import *

from io_mesh_w3d.blender_addon_updater import addon_updater_ops

VERSION = (0, 8, 2)

bl_info = {
    'name': 'Import/Export Westwood W3D Format (.w3d/.w3x)',
    'author': 'OpenSage Developers',
    'version': (0, 8, 2),
    "blender": (2, 90, 0),
    'location': 'File > Import/Export > Westwood W3D (.w3d/.w3x)',
    'description': 'Import or Export the Westwood W3D-Format (.w3d/.w3x)',
    'warning': 'Still in Progress',
    'doc_url': 'https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin',
    'tracker_url': 'https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin/issues',
    'support': 'OFFICIAL',
    'category': 'Import-Export'}


def print_version(info):
    version = str(VERSION).replace('(', '').replace(')', '')
    version = version.replace(',', '.').replace(' ', '')
    info(f'plugin version: {version}  unofficial')


class ExportW3D(bpy.types.Operator, ExportHelper, ReportHelper):
    """Export to Westwood 3D file format (.w3d/.w3x)"""
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
             'Hierarchy + Mesh + Contatiner',
             'This will export all the meshes of the scene with hierarchy/skeleton data'),
            ('HAM',
             'Hierarchy + Mesh + Contatiner + Animation',
             'This will export all the meshes of the scene with hierarchy/skeleton and animation data'),
            ('A',
             'Animation',
             'This will export the animation without any geometry or hierarchy/skeleton data'),
            ('H',
             'Hierarchy',
             'This will export the hierarchy/skeleton without any geometry or animation data'),
            ('M',
             'Mesh + Contatiner',
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
        name='Individual files (3DS Max Style)',
        description='Creates an individual file for each mesh, boundingbox and the hierarchy',
        default=False)

    create_texture_xmls: BoolProperty(
        name='Create texture xml files', description='Creates an .xml file for each used texture', default=False)

    will_save_settings: BoolProperty(default=False)

    scene_key = 'w3dExportSettings'

    def invoke(self, context, event):
        settings = context.scene.get(self.scene_key)
        self.will_save_settings = False
        if settings:
            try:
                for (k, v) in settings.items():
                    setattr(self, k, v)
                self.will_save_settings = True

            except (AttributeError, TypeError):
                self.error('Loading export settings failed. Removed corrupted settings.')
                del context.scene[self.scene_key]

        return ExportHelper.invoke(self, context, event)

    def save_settings(self, context):
        all_props = self.properties
        export_props = {x: getattr(self, x) for x in dir(
            all_props) if x.startswith('export_') and all_props.get(x) is not None}

        context.scene[self.scene_key] = export_props

    def execute(self, context):
        print_version(self.info)
        if self.will_save_settings:
            self.save_settings(context)

        export_settings = {'mode': self.export_mode,
                           'compression': self.animation_compression,
                           'use_existing_skeleton': self.use_existing_skeleton,
                           'individual_files': self.individual_files,
                           'create_texture_xmls': self.create_texture_xmls}

        return save_data(self, export_settings)

    def draw(self, _context):
        self.draw_general_settings()
        # if self.export_mode == 'HM':
        #     self.draw_use_existing_skeleton()
        if self.file_format == 'W3X':
            self.draw_individual_files()

        #if self.file_format == 'W3X' and 'M' in self.export_mode:
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


class ImportW3D(bpy.types.Operator, ImportHelper, ReportHelper):
    """Import from Westwood 3D file format (.w3d/.w3x)"""
    bl_idname = 'import_mesh.westwood_w3d'
    bl_label = 'Import W3D/W3X'
    bl_options = {'UNDO'}

    file_format = ''

    filter_glob: StringProperty(default='*.w3d;*.w3x', options={'HIDDEN'})

    def execute(self, context):
        print_version(self.info)
        if self.filepath.lower().endswith('.w3d'):
            from .w3d.import_w3d import load
            file_format = 'W3D'
            load(self)
        else:
            from .w3x.import_w3x import load
            file_format = 'W3X'
            load(self)

        self.info('finished')
        return {'FINISHED'}


def menu_func_export(self, _context):
    self.layout.operator(ExportW3D.bl_idname, text='Westwood W3D (.w3d/.w3x)')


def menu_func_import(self, _context):
    self.layout.operator(ImportW3D.bl_idname, text='Westwood W3D (.w3d/.w3x)')


class MESH_PROPERTIES_PANEL_PT_w3d(Panel):
    bl_label = 'W3D Properties'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    def draw(self, context):
        obj = context.active_object
        if (obj.type != 'MESH'):
            return

        layout = self.layout
        col = layout.column()
        mesh = context.active_object.data
        col.prop(mesh, 'object_type')
        col = layout.column()
        if mesh.object_type == 'MESH':
            col.prop(mesh, 'sort_level')
            col = layout.column()
            col.prop(mesh, 'casts_shadow')
            col = layout.column()
            col.prop(mesh, 'two_sided')
            col = layout.column()
            col.prop(mesh, 'userText')
        elif mesh.object_type == 'DAZZLE':
            col = layout.column()
            col.prop(mesh, 'dazzle_type')
        elif mesh.object_type == 'BOX':
            col = layout.column()
            col.prop(mesh, 'box_type')
            col = layout.column()
            col.prop(mesh, 'box_collision_types')
        elif mesh.object_type == 'GEOMETRY':
            col = layout.column()
            col.prop(mesh, 'geometry_type')
            col = layout.column()
            col.prop(mesh, 'contact_points_type')
        elif mesh.object_type == 'BONE_VOLUME':
            col = layout.column()
            col.prop(mesh, 'mass')
            col = layout.column()
            col.prop(mesh, 'spinniness')
            col = layout.column()
            col.prop(mesh, 'contact_tag')


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
        col.prop(mat, 'material_type')
        col = layout.column()
        col.prop(mat, 'technique')

        name, material_map = get_material_parameter_map(mat.material_type)
        for key, value in material_map.items(): # internal functions
            if "__" in key: 
                col = layout.column()
                col.prop(mat, value)

        box = layout.box()
        box.label(text="Shader Parameters", icon='PREFERENCES')
        row = box.row()
        for key, value in material_map.items():
            if not "__" in key: 
                col = row.column()
                box.prop(mat, value)

class TOOLS_PANEL_PT_w3d(bpy.types.Panel):
    bl_label = 'W3D Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        self.layout.operator('scene.export_geometry_data', icon='CUBE', text='Export Geometry Data')
        self.layout.operator('scene.export_bone_volume_data', icon='BONE_DATA', text='Export Bone Volume Data')






##############################
# 
#  Blender Add-on Preference Page
#
##############################

class TexturePathItem(PropertyGroup):
    path: StringProperty(
        name="Folder Path",
        description="A folder path to search for textures",
        default="",
    )

class Operator_AddTexturePath(Operator):
    bl_idname = "addonname.add_texture_path"
    bl_label = "Add Texture Path"
    
    directory: StringProperty(
        subtype='DIR_PATH',
        default="",
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        if self.directory:
            prefs = context.preferences.addons[__name__].preferences
            new_path = prefs.texture_paths.add()
            new_path.name = self.directory
        return {'FINISHED'}

class Operator_RemoveTexturePath(Operator):
    bl_idname = "addonname.remove_texture_path"
    bl_label = "Remove Texture Path"
    
    index: IntProperty(default=0)
    
    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        if len(prefs.texture_paths) > self.index:
            prefs.texture_paths.remove(self.index)
        return {'FINISHED'}

class Operator_MessageBox(Operator):
    bl_idname = "wm.message_box"
    bl_label = "Message"
    bl_description = "Show a message box"

    message: bpy.props.StringProperty(default="")

    def execute(self, context):
        self.report({'INFO'}, self.message)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text=self.message)

class Operator_ImportMaterialProperties(Operator):
    bl_idname = "object.import_module"
    bl_label = "Import Selected Module"
    bl_description = "Manually trigger import of the selected module"

    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        preferences.import_selected_module(context)
        return {'FINISHED'}

MATERIAL_MODULES = [
    ("RA3", "RA3 Material", "Import RA3 Material module"),
    ("CNC3", "CNC3 Material", "Import CNC3 Material module"),
    ("Generals", "Generals Material", "Import Generals Material module"),
]
def set_selected_module(self, context):
    print(self.selected_module)
    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path)
    file_path = current_dir + os.path.sep + 'selected_module.py'
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"from io_mesh_w3d.common.materials.{self.selected_module} import *\n")
        bpy.ops.wm.message_box(
                'INVOKE_DEFAULT',
                message=f'Using {self.selected_module} Material Group. Take effect at next launch!'
            )
    except:
        bpy.ops.wm.message_box(
                'INVOKE_DEFAULT',
                message=f"Error! Materal group unchanged! Check {file_path}"
            )


class OBJECT_PT_DemoUpdaterPanel(bpy.types.Panel):
    bl_label = 'Updater Demo Panel'
    bl_idname = 'OBJECT_PT_hello'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = 'objectmode'
    bl_category = 'Tools'

    def draw(self, context):
        layout = self.layout

        addon_updater_ops.check_for_update_background()

        layout.label(text='Demo Updater Addon')
        layout.label(text='')

        col = layout.column()
        col.scale_y = 0.7
        col.label(text='If an update is ready,')
        col.label(text='popup triggered by opening')
        col.label(text='this panel, plus a box ui')

        if addon_updater_ops.updater.update_ready:
            layout.label(text='An update for the W3D/W3X plugin is available', icon='INFO')
        layout.label(text='')

        addon_updater_ops.update_notice_box_ui(self, context)


@addon_updater_ops.make_annotations
class PreferencesPanel(bpy.types.AddonPreferences):
    bl_idname = __package__

    selected_module: EnumProperty(
        name="Choose",
        description="Load pre-defined materials of a specific game.\nYou can still import models from other games, the shader parameters will be converted.",
        items=MATERIAL_MODULES,
        default="RA3",
        update=set_selected_module
    )

    texture_paths: CollectionProperty(
            type=TexturePathItem,
            name="Texture Search Paths",
            description="List of folders to search for texture files",
    )
    

    auto_check_update = bpy.props.BoolProperty(
        name='Auto-check for Update',
        description='If enabled, auto-check for updates using an interval',
        default=False,
    )
    updater_interval_months = bpy.props.IntProperty(
        name='Months',
        description='Number of months between checking for updates',
        default=0,
        min=0
    )
    updater_interval_days = bpy.props.IntProperty(
        name='Days',
        description='Number of days between checking for updates',
        default=7,
        min=0,
        max=31
    )
    updater_interval_hours = bpy.props.IntProperty(
        name='Hours',
        description='Number of hours between checking for updates',
        default=0,
        min=0,
        max=23
    )
    updater_interval_minutes = bpy.props.IntProperty(
        name='Minutes',
        description='Number of minutes between checking for updates',
        default=0,
        min=0,
        max=59
    )


    active_path_index: IntProperty(default=0)

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="Material Definition Group", icon='MATERIAL')
        box.prop(self, "selected_module")

        box = layout.box()
        box.label(text="Paths to find textures", icon='PREFERENCES')
        row = box.row()
        col = row.column()
        col.template_list(
            "UI_UL_list", 
            "texture_paths_list",  
            self, 
            "texture_paths",  
            self,  
            "active_path_index", 
            rows=4, 
        )
        col = row.column(align=True)
        col.operator("addonname.add_texture_path", icon='ADD', text="")
        col.operator("addonname.remove_texture_path", icon='REMOVE', text="").index = self.active_path_index


        addon_updater_ops.update_settings_ui(self, context)


CLASSES = (
    ExportW3D,
    ImportW3D,
    ShaderProperties,
    MESH_PROPERTIES_PANEL_PT_w3d,
    BONE_PROPERTIES_PANEL_PT_w3d,
    MATERIAL_PROPERTIES_PANEL_PT_w3d,
    ExportGeometryData,
    ExportBoneVolumeData,
    TOOLS_PANEL_PT_w3d,

    TexturePathItem,
    Operator_AddTexturePath,
    Operator_RemoveTexturePath,
    Operator_MessageBox,
    Operator_ImportMaterialProperties,
    PreferencesPanel,
    OBJECT_PT_DemoUpdaterPanel
)


def register():
    addon_updater_ops._package = 'io_mesh_w3d'
    addon_updater_ops.updater.addon = 'io_mesh_w3d'
    addon_updater_ops.updater.user = "OpenSAGE"
    addon_updater_ops.updater.repo = "OpenSAGE.BlenderPlugin"
    addon_updater_ops.updater.website = "https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin"
    addon_updater_ops.updater.subfolder_path = "io_mesh_w3d"
    addon_updater_ops.updater.include_branch_list = ['master']
    addon_updater_ops.updater.verbose = False

    addon_updater_ops.register(bl_info)

    for class_ in CLASSES:
        bpy.utils.register_class(class_)

    Material.shader = PointerProperty(type=ShaderProperties)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    addon_updater_ops.unregister()

    for class_ in reversed(CLASSES):
        bpy.utils.unregister_class(class_)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == '__main__':
    register()
