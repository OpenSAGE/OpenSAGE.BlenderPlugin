# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019
import bpy
from bpy.types import Operator, AddonPreferences
from bpy_extras.io_utils import ImportHelper, ExportHelper

from bpy.props import (CollectionProperty,
                       StringProperty,
                       BoolProperty,
                       EnumProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       IntProperty)


bl_info = {
    'name': 'Import/Export Westwood W3D Format (.w3d)',
    'author': 'OpenSage Developers',
    'version': (0, 0, 1),
    "blender": (2, 80, 0),
    'location': 'File > Import/Export > Westerwood W3D (.w3d)',
    'description': 'Import or Export the Westerwood W3D-Format (.w3d)',
    'warning': 'Still in Progress',
    'wiki_url': 'https://github.com/OpenSAGE/OpenSAGE',
    'tracker_url': 'https://github.com/OpenSAGE/OpenSAGE/issues',
    'support': 'OFFICIAL',
    'category': 'Import-Export'}


class ExportW3D(bpy.types.Operator, ExportHelper):
    '''Export from Westwood 3D file format (.w3d)'''
    bl_idname = 'export_mesh.westwood_w3d'
    bl_label = 'Export W3D'
    bl_options = {'UNDO', 'PRESET'}

    filename_ext = '.w3d'
    filter_glob: StringProperty(default='*.w3d', options={'HIDDEN'})

    ui_tab: EnumProperty(
        items=(('GENERAL', "General", "General settings"),
               #('MESHES', "Meshes", "Mesh settings"),
               #('OBJECTS', "Objects", "Object settings"),
               #('MATERIALS', "Materials", "Material settings"),
               ('ANIMATION', "Animation", "Animation settings")),
        name="ui_tab",
        description="Export setting categories",
    )

    export_mode: EnumProperty(
        name="Export Mode",
        items=(('M', "Model", "This will export all the meshes of the scene, without skeletons or animation"),
               ('H', "Hierarchy", "This will export the hierarchy tree without any geometry or animation data"),
               ('A', "Animation", "This will export the animation without any geometry data or skeletons"),
               ('HAM', "HierarchicalAnimatedModel",
                "This will export the meshes with the hierarchy and animation into one file")
               ),
        default='M',)

    animation_compression: EnumProperty(
        name="Compression",
        items=(('U', "Uncompressed", "This will not compress the animations"),
               ('TC', "TimeCoded", "This will export the animation with keyframes"),
               #('AD', "AdaptiveDelta",
               # "This will use adaptive delta compression to reduce size"),
               ),
        default='TC',)

    will_save_settings: BoolProperty(default=False)

    # Custom scene property for saving settings
    scene_key = "w3dExportSettings"

    def invoke(self, context, event):
        settings = context.scene.get(self.scene_key)
        self.will_save_settings = False
        if settings:
            try:
                for (k, v) in settings.items():
                    setattr(self, k, v)
                self.will_save_settings = True

            except (AttributeError, TypeError):
                self.report(
                    {"ERROR"}, "Loading export settings failed. Removed corrupted settings")
                del context.scene[self.scene_key]

        return ExportHelper.invoke(self, context, event)

    def save_settings(self, context):
        # find all export_ props
        all_props = self.properties
        export_props = {x: getattr(self, x) for x in dir(all_props)
                        if x.startswith("export_") and all_props.get(x) is not None}

        context.scene[self.scene_key] = export_props

    def execute(self, context):
        from . import export_w3d

        if self.will_save_settings:
            self.save_settings(context)

        # All custom export settings are stored in this container.
        export_settings = {}

        export_settings['w3d_mode'] = self.export_mode
        export_settings['w3d_compression'] = self.animation_compression

        return export_w3d.save(self.filepath, context, export_settings)

    def draw(self, _context):
        self.layout.prop(self, 'ui_tab', expand=True)
        if self.ui_tab == 'GENERAL':
            self.draw_general_settings()
        elif self.ui_tab == 'ANIMATION':
            self.draw_animation_settings()

    def draw_general_settings(self):
        col = self.layout.box().column()
        col.prop(self, 'export_mode')

    def draw_animation_settings(self):
        col = self.layout.box().column()
        col.prop(self, 'export_compress')


class ImportW3D(bpy.types.Operator, ImportHelper):
    '''Import from Westwood 3D file format (.w3d)'''
    bl_idname = 'import_mesh.westwood_w3d'
    bl_label = 'Import W3D'
    bl_options = {'UNDO'}

    filename_ext = '.w3d'
    filter_glob: StringProperty(default='*.w3d', options={'HIDDEN'})

    def execute(self, context):
        from . import import_w3d

        import_settings = {}

        import_w3d.load(self, context, import_settings)

        print('finished')
        return {'FINISHED'}


def menu_func_export(self, _context):
    self.layout.operator(ExportW3D.bl_idname, text='Westwood W3D (.w3d)')


def menu_func_import(self, _context):
    self.layout.operator(ImportW3D.bl_idname, text='Westwood W3D (.w3d)')

#custom property stuff

bpy.types.Object.UserText = bpy.props.StringProperty(
    name="UserText",
    description="This is a text defined by the user",
    default="")

class OBJECT_PANEL_PT_w3d(bpy.types.Panel):
    bl_label = "W3D Properties"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.active_object, "UserText")

bpy.types.Material.emission = bpy.props.FloatVectorProperty(  
    name="emission",
    subtype='COLOR',
    size=4,
    default=(1.0, 1.0, 1.0, 0.0),
    min=0.0, max=1.0,
    description="emission color")

bpy.types.Material.ambient = bpy.props.FloatVectorProperty(  
    name="ambient",
    subtype='COLOR',
    size=4,
    default=(1.0, 1.0, 1.0, 0.0),
    min=0.0, max=1.0,
    description="ambient color")

bpy.types.Material.translucency = bpy.props.FloatProperty(  
    name="translucency",
    default=0.0,
    min=0.0, max=1.0,
    description="translucency property")

bpy.types.Material.opacity = bpy.props.FloatProperty(  
    name="opacity",
    default=0.0,
    min=0.0, max=1.0,
    description="opacity property")

bpy.types.Material.vm_args_0 = bpy.props.StringProperty(
    name="vm_args_0",
    description="Vertex Material Arguments 0",
    default="")

bpy.types.Material.vm_args_1 = bpy.props.StringProperty(
    name="vm_args_1",
    description="Vertex Material Arguments 1",
    default="")

class MATERIAL_PANEL_PT_w3d(bpy.types.Panel):
    bl_label = "W3D Properties"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.object.active_material, "emission")
        col = layout.column()
        col.prop(context.object.active_material, "ambient")
        col = layout.column()
        col.prop(context.object.active_material, "translucency")
        col = layout.column()
        col.prop(context.object.active_material, "opacity")
        col = layout.column()
        col.prop(context.object.active_material, "vm_args_0")
        col = layout.column()
        col.prop(context.object.active_material, "vm_args_1")


CLASSES = (
    ExportW3D,
    ImportW3D,
    OBJECT_PANEL_PT_w3d,
    MATERIAL_PANEL_PT_w3d
)


def register():
    for class_ in CLASSES:
        bpy.utils.register_class(class_)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    for class_ in reversed(CLASSES):
        bpy.utils.unregister_class(class_)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
