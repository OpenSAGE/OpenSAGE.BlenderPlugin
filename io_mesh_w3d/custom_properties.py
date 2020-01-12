# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.types import Panel, Object, Material, Operator, AddonPreferences, PropertyGroup
from bpy.props import *


##########################################################################
# Object
##########################################################################

Object.userText = StringProperty(
    name="User Text",
    description="This is a text defined by the user",
    default="")


Object.object_type = EnumProperty(
    name="Type",
    description="Attributes that define the type of this object",
    items=[
        ('NORMAL', 'Normal', 'desc: just a normal mesh'),
        ('BOX', 'Box', 'desc: this object defines a boundingbox'),
        ('DAZZLE', 'Dazzle', 'desc: todo')],
    default='NORMAL')


class OBJECT_PANEL_PT_w3d(Panel):
    bl_label = "W3D Properties"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.active_object, "object_type")
        col = layout.column()
        col.prop(context.active_object, "userText")


##########################################################################
# Material
##########################################################################


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

Material.technique = IntProperty(
    name="Technique",
    description="Dont know yet",
    default=0,
    min=0,
    max=1)

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


##########################################################################
# Material.Shader
##########################################################################


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