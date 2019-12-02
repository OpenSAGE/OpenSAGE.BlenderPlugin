# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.types import Panel, Object, Material, Operator, AddonPreferences, PropertyGroup
from bpy_extras.io_utils import ImportHelper, ExportHelper

from bpy.props import StringProperty,\
    BoolProperty, \
    EnumProperty, \
    FloatProperty, \
    FloatVectorProperty, \
    IntProperty, \
    PointerProperty


bl_info = {
    'name': 'Import/Export Westwood W3D Format (.w3d)',
    'author': 'OpenSage Developers',
    'version': (0, 2, 1),
    "blender": (2, 80, 0),
    'location': 'File > Import/Export > Westerwood W3D (.w3d)',
    'description': 'Import or Export the Westerwood W3D-Format (.w3d)',
    'warning': 'Still in Progress',
    'wiki_url': 'https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin',
    'tracker_url': 'https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin/issues',
    'support': 'OFFICIAL',
    'category': 'Import-Export'}


class ExportW3D(bpy.types.Operator, ExportHelper):
    '''Export from Westwood 3D file format (.w3d)'''
    bl_idname = 'export_mesh.westwood_w3d'
    bl_label = 'Export W3D'
    bl_options = {'UNDO', 'PRESET'}

    filename_ext = '.w3d'
    filter_glob: StringProperty(default='*.w3d', options={'HIDDEN'})

    export_mode: EnumProperty(
        name="Mode",
        items=(
            ('M',
             "Model",
             "This will export all the meshes of the scene, without skeletons or animation"),
            ('H',
             "Hierarchy",
             "This will export the hierarchy tree without any geometry or animation data"),
            ('A',
             "Animation",
             "This will export the animation without any geometry data or skeletons"),
            ('HAM',
             "HierarchicalAnimatedModel",
             "This will export the meshes with the hierarchy and animation into one file")),
        description="Select the export mode",
        default='M',
    )

    animation_compression: EnumProperty(
        name="Compression",
        items=(('U', "Uncompressed", "This will not compress the animations"),
               ('TC', "TimeCoded", "This will export the animation with keyframes"),
               # ('AD', "AdaptiveDelta",
               # "This will use adaptive delta compression to reduce size"),
               ),
        description="The method used for compressing the animation data",
        default='U',)

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
                    {"ERROR"},
                    "Loading export settings failed. Removed corrupted settings")
                del context.scene[self.scene_key]

        return ExportHelper.invoke(self, context, event)

    def save_settings(self, context):
        # find all export_ props
        all_props = self.properties
        export_props = {x: getattr(self, x) for x in dir(
            all_props) if x.startswith("export_") and all_props.get(x) is not None}

        context.scene[self.scene_key] = export_props

    def execute(self, context):
        from . import export_w3d

        if self.will_save_settings:
            self.save_settings(context)

        # All custom export settings are stored in this container.
        export_settings = {}

        export_settings['w3d_mode'] = self.export_mode
        export_settings['w3d_compression'] = self.animation_compression

        return export_w3d.save(self, context, export_settings)

    def draw(self, _context):
        # self.layout.prop(self, 'ui_tab', expand=True)
        # if self.ui_tab == 'GENERAL':
        self.draw_general_settings()
        if self.export_mode == 'A':
            self.draw_animation_settings()

    def draw_general_settings(self):
        col = self.layout.box().column()
        col.prop(self, 'export_mode')

    def draw_animation_settings(self):
        col = self.layout.box().column()
        col.prop(self, 'animation_compression')


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

# custom property stuff


Object.UserText = StringProperty(
    name="UserText",
    description="This is a text defined by the user",
    default="")


class OBJECT_PANEL_PT_w3d(Panel):
    bl_label = "W3D Properties"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.active_object, "UserText")


Material.attributes = EnumProperty(
    name="attributes",
    description="Attributes that define the behaviour of this material",
    items=[
        ('DEFAULT', 'Default', 'desc: todo', 0),
        ('USE_DEPTH_CUE', 'UseDepthCue', 'desc: todo', 1),
        ('ARGB_EMISSIVE_ONLY', 'ArgbEmissiveOnly', 'desc: todo', 2),
        ('COPY_SPECULAR_TO_DIFFUSE', 'CopySpecularToDiffuse', 'desc: todo', 4),
        ('DEPTH_CUE_TO_ALPHA', 'DepthCueToAlpha', 'desc: todo', 8)],
    default={'DEFAULT'},
    options={'ENUM_FLAG'})

Material.emission = FloatVectorProperty(
    name="Emission",
    subtype='COLOR',
    size=4,
    default=(1.0, 1.0, 1.0, 0.0),
    min=0.0, max=1.0,
    description="Emission color")

Material.ambient = FloatVectorProperty(
    name="Ambient",
    subtype='COLOR',
    size=4,
    default=(1.0, 1.0, 1.0, 0.0),
    min=0.0, max=1.0,
    description="Ambient color")

Material.translucency = FloatProperty(
    name="Translucency",
    default=0.0,
    min=0.0, max=1.0,
    description="Translucency property")

Material.opacity = FloatProperty(
    name="Opacity",
    default=0.0,
    min=0.0, max=1.0,
    description="Opacity property")

Material.vm_args_0 = StringProperty(
    name="vm_args_0",
    description="Vertex Material Arguments 0",
    default="")

Material.vm_args_1 = StringProperty(
    name="vm_args_1",
    description="Vertex Material Arguments 1",
    default="")

Material.alpha_test = BoolProperty(
    name="Alpha test",
    description="Enable the alpha test",
    default=False)

Material.surface_type = EnumProperty(
    name='Surface type',
    description='Describes the surface type for this material',
    items=[
        ('0', 'LightMetal', 'desc: todo'),
        ('1', 'HeavyMetal', 'desc: todo'),
        ('2', 'Water', 'desc: todo'),
        ('3', 'Sand', 'desc: todo'),
        ('4', 'Dirt', 'desc: todo'),
        ('5', 'Mud', 'desc: todo'),
        ('6', 'Grass', 'desc: todo'),
        ('7', 'Wood', 'desc: todo'),
        ('8', 'Concrete', 'desc: todo'),
        ('9', 'Flesh', 'desc: todo'),
        ('10', 'Rock', 'desc: todo'),
        ('11', 'Snow', 'desc: todo'),
        ('12', 'Ice', 'desc: todo'),
        ('13', 'Default', 'desc: todo'),
        ('14', 'Glass', 'desc: todo'),
        ('15', 'Cloth', 'desc: todo'),
        ('16', 'TiberiumField', 'desc: todo'),
        ('17', 'FoliagePermeable', 'desc: todo'),
        ('18', 'GlassPermeable', 'desc: todo'),
        ('19', 'IcePermeable', 'desc: todo'),
        ('20', 'ClothPermeable', 'desc: todo'),
        ('21', 'Electrical', 'desc: todo'),
        ('22', 'Flammable', 'desc: todo'),
        ('23', 'Steam', 'desc: todo'),
        ('24', 'ElectricalPermeable', 'desc: todo'),
        ('25', 'FlammablePermeable', 'desc: todo'),
        ('26', 'SteamPermeable', 'desc: todo'),
        ('27', 'WaterPermeable', 'desc: todo'),
        ('28', 'TiberiumWater', 'desc: todo'),
        ('29', 'TiberiumWaterPermeable', 'desc: todo'),
        ('30', 'UnderwaterDirt', 'desc: todo'),
        ('31', 'UnderwaterTiberiumDirt', 'desc: todo')],
    default='13')

# not yet visible in gui

Material.blend_mode = IntProperty(
    name="Blend mode",
    description="Which blend mode should be used",
    default=0,
    min=0,
    max=5)

Material.bump_uv_scale = FloatVectorProperty(
    name="Bump UV Scale",
    subtype='TRANSLATION',
    size=2,
    default=(0.0, 0.0),
    min=0.0, max=1.0,
    description="Bump uv scale")

Material.sampler_clamp_uv_no_mip = FloatVectorProperty(
    name="Sampler clamp UV no MIP",
    subtype='TRANSLATION',
    size=3,
    default=(0.0, 0.0, 0.0),
    min=0.0, max=1.0,
    description="Sampler clampU clampV no mipmap")


class MATERIAL_PROPERTIES_PANEL_PT_w3d(Panel):
    bl_label = "W3D Properties"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.object.active_material, "attributes")
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
        col = layout.column()
        col.prop(context.object.active_material, "alpha_test")
        col = layout.column()
        col.prop(context.object.active_material, "surface_type")


class ShaderProperties(PropertyGroup):
    depth_compare: bpy.props.IntProperty(min=0, max=255)
    depth_mask: bpy.props.IntProperty(min=0, max=255)
    color_mask: bpy.props.IntProperty(min=0, max=255)
    dest_blend: bpy.props.IntProperty(min=0, max=255)
    fog_func: bpy.props.IntProperty(min=0, max=255)
    pri_gradient: bpy.props.IntProperty(min=0, max=255)
    sec_gradient: bpy.props.IntProperty(min=0, max=255)
    src_blend: bpy.props.IntProperty(min=0, max=255)
    texturing: bpy.props.IntProperty(min=0, max=255)
    detail_color_func: bpy.props.IntProperty(min=0, max=255)
    detail_alpha_func: bpy.props.IntProperty(min=0, max=255)
    shader_preset: bpy.props.IntProperty(min=0, max=255)
    alpha_test: bpy.props.IntProperty(min=0, max=255)
    post_detail_color_func: bpy.props.IntProperty(min=0, max=255)
    post_detail_alpha_func: bpy.props.IntProperty(min=0, max=255)


bpy.utils.register_class(ShaderProperties)
Material.shader = PointerProperty(type=ShaderProperties)


class MATERIAL_SHADER_PROPERTIES_PANEL_PT_w3d(Panel):
    bl_label = "W3D Shader Properties"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.object.active_material.shader, "depth_compare")
        col = layout.column()
        col.prop(context.object.active_material.shader, "depth_mask")
        col = layout.column()
        col.prop(context.object.active_material.shader, "color_mask")
        col = layout.column()
        col.prop(context.object.active_material.shader, "dest_blend")
        col = layout.column()
        col.prop(context.object.active_material.shader, "fog_func")
        col = layout.column()
        col.prop(context.object.active_material.shader, "pri_gradient")
        col = layout.column()
        col.prop(context.object.active_material.shader, "sec_gradient")
        col = layout.column()
        col.prop(context.object.active_material.shader, "src_blend")
        col = layout.column()
        col.prop(context.object.active_material.shader, "texturing")
        col = layout.column()
        col.prop(context.object.active_material.shader, "detail_color_func")
        col = layout.column()
        col.prop(context.object.active_material.shader, "detail_alpha_func")
        col = layout.column()
        col.prop(context.object.active_material.shader, "shader_preset")
        col = layout.column()
        col.prop(context.object.active_material.shader, "alpha_test")
        col = layout.column()
        col.prop(context.object.active_material.shader,
                 "post_detail_color_func")
        col = layout.column()
        col.prop(context.object.active_material.shader,
                 "post_detail_alpha_func")


CLASSES = (
    ExportW3D,
    ImportW3D,
    OBJECT_PANEL_PT_w3d,
    MATERIAL_PROPERTIES_PANEL_PT_w3d,
    MATERIAL_SHADER_PROPERTIES_PANEL_PT_w3d
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
