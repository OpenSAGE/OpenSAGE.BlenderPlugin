# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy.types import NodeSocketInt, NodeSocketInterfaceInt


class NodeSocketInterfaceEnum(NodeSocketInterfaceInt):
    bl_socket_idname = 'NodeSocketEnum'

    default_value = '0'

    def draw(self, context, layout):
        pass

    def draw_color(self, context):
        return (1.0, 0.4, 0.216, 0.5)

    @staticmethod
    def register_classes():
        bpy.utils.register_class(NodeSocketInterfaceEnum)
        bpy.utils.register_class(NodeSocketEnum)
        bpy.utils.register_class(NodeSocketEnumMaterialAttributes)
        bpy.utils.register_class(NodeSocketEnumDepthCompare)
        bpy.utils.register_class(NodeSocketEnumDepthMaskWrite)
        bpy.utils.register_class(NodeSocketEnumAlphatest)
        bpy.utils.register_class(NodeSocketEnumDestBlendFunc)
        bpy.utils.register_class(NodeSocketEnumPriGradient)
        bpy.utils.register_class(NodeSocketEnumSecGradient)
        bpy.utils.register_class(NodeSocketEnumSrcBlendFunc)
        bpy.utils.register_class(NodeSocketEnumDetailColorFunc)
        bpy.utils.register_class(NodeSocketEnumDetailAlphaFunc)

    @staticmethod
    def unregister_classes():
        bpy.utils.unregister_class(NodeSocketInterfaceEnum)
        bpy.utils.unregister_class(NodeSocketEnum)
        bpy.utils.unregister_class(NodeSocketEnumMaterialAttributes)
        bpy.utils.unregister_class(NodeSocketEnumDepthCompare)
        bpy.utils.unregister_class(NodeSocketEnumDepthMaskWrite)
        bpy.utils.unregister_class(NodeSocketEnumAlphatest)
        bpy.utils.unregister_class(NodeSocketEnumDestBlendFunc)
        bpy.utils.unregister_class(NodeSocketEnumPriGradient)
        bpy.utils.unregister_class(NodeSocketEnumSecGradient)
        bpy.utils.unregister_class(NodeSocketEnumSrcBlendFunc)
        bpy.utils.unregister_class(NodeSocketEnumDetailColorFunc)
        bpy.utils.unregister_class(NodeSocketEnumDetailAlphaFunc)


class NodeSocketEnum(NodeSocketInt):
    bl_idname = 'NodeSocketEnum'
    label = 'Enum Node Socket'

    hide = True
    enabled = False
    display_shape = 'DIAMOND_DOT'

    default_value: bpy.props.EnumProperty(
        name='Direction',
        description='Just an example',
        items=[
            ('0', 'DOWN', 'Where your feet are'),
            ('1', 'UP', 'Where your head should be'),
            ('2', 'LEFT', 'Not right'),
            ('3', 'RIGHT', 'Not left')],
        default='0')

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, 'default_value', text=text)

    def draw_color(self, context, node):
        return (0.1, 0.2, 1.0, 1.0)

    def get(self):
        return int(self.default_value)


class NodeSocketEnumMaterialAttributes(NodeSocketEnum):
    bl_idname = 'NodeSocketEnumMaterialAttributes'
    bl_label = 'Material Attributes Enum Flag Node Socket'

    default_value: bpy.props.EnumProperty(
        name='Attributes',
        description='Attributes that define the behaviour of this material',
        items=[
            ('DEFAULT', 'Default', 'desc: todo', 0),
            ('USE_DEPTH_CUE', 'UseDepthCue', 'desc: todo', 1),
            ('ARGB_EMISSIVE_ONLY', 'ArgbEmissiveOnly', 'desc: todo', 2),
            ('COPY_SPECULAR_TO_DIFFUSE', 'CopySpecularToDiffuse', 'desc: todo', 4),
            ('DEPTH_CUE_TO_ALPHA', 'DepthCueToAlpha', 'desc: todo', 8)],
        default=set(),
        options={'ENUM_FLAG'})


class NodeSocketEnumDepthCompare(NodeSocketEnum):
    bl_idname = 'NodeSocketEnumDepthCompare'
    bl_label = 'Depth Compare Enum Node Socket'

    default_value: bpy.props.EnumProperty(
        name='DepthCompare',
        description='todo',
        items=[
            ('0', 'PASS_NEVER', 'pass never (i.e. always fail depth comparison test)'),
            ('1', 'PASS_LESS', 'pass if incoming less than stored'),
            ('2', 'PASS_EQUAL', 'pass if incoming equal to stored'),
            ('3', 'PASS_LEQUAL', 'pass if incoming less than or equal to stored (default)'),
            ('4', 'PASS_GREATER', 'pass if incoming greater than stored'),
            ('5', 'PASS_NOTEQUAL', 'pass if incoming not equal to stored'),
            ('6', 'PASS_GEQUAL', 'pass if incoming greater than or equal to stored'),
            ('7', 'PASS_ALWAYS', 'pass always')],
        default='3')


class NodeSocketEnumDepthMaskWrite(NodeSocketEnum):
    bl_idname = 'NodeSocketEnumDepthMaskWrite'
    bl_label = 'Depthmask Write Enum Node Socket'

    default_value: bpy.props.EnumProperty(
        name='DepthmaskWrite',
        description='todo',
        items=[
            ('0', 'DISABLE', 'disable depth buffer writes'),
            ('1', 'ENABLE', 'enable depth buffer writes (default)')],
        default='1')


class NodeSocketEnumAlphatest(NodeSocketEnum):
    bl_idname = 'NodeSocketEnumAlphaTest'
    bl_label = 'Alphatest Enum Node Socket'

    default_value: bpy.props.EnumProperty(
        name='Alphatest',
        description='todo',
        items=[
            ('0', 'DISABLE', 'disable alpha testing (default)'),
            ('1', 'ENABLE', 'enable alpha testing')],
        default='0')


class NodeSocketEnumDestBlendFunc(NodeSocketEnum):
    bl_idname = 'NodeSocketEnumDestBlendFunc'
    bl_label = 'DestBlendFunc Enum Node Socket'

    default_value: bpy.props.EnumProperty(
        name='DestBlendFunc',
        description='todo',
        items=[
            ('0', 'ZERO', 'destination pixel does not affect blending (default)'),
            ('1', 'ONE', 'destination pixel added unmodified'),
            ('2', 'SRC_COLOR', 'destination pixel multiplied by fragment RGB components'),
            ('3', 'ONE_MINUS_SRC_COLOR', 'destination pixel multiplied by one minus (i.e. inverse) fragment RGB components'),
            ('4', 'SRC_ALPHA', 'destination pixel multiplied by fragment alpha component'),
            ('5', 'ONE_MINUS_SRC_ALPHA', 'destination pixel multiplied by fragment inverse alpha'),
            ('6', 'SRC_COLOR_PREFOG', 'destination pixel multiplied by fragment RGB components prior to fogging')],
        default='0')


class NodeSocketEnumPriGradient(NodeSocketEnum):
    bl_idname = 'NodeSocketEnumPriGradient'
    bl_label = 'PriGradient Enum Node Socket'

    default_value: bpy.props.EnumProperty(
        name='PriGradient',
        description='todo',
        items=[
            ('0', 'DISABLE', 'disable primary gradient (same as OpenGL �decal� texture blend)'),
            ('1', 'MODULATE', 'modulate fragment ARGB by gradient ARGB (default)'),
            ('2', 'ADD', 'add gradient RGB to fragment RGB, copy gradient A to fragment A'),
            ('3', 'BUMPENVMAP', 'environment-mapped bump mapping')],
        default='1')


class NodeSocketEnumSecGradient(NodeSocketEnum):
    bl_idname = 'NodeSocketEnumSecGradient'
    bl_label = 'SecGradient Enum Node Socket'

    default_value: bpy.props.EnumProperty(
        name='SecGradient',
        description='todo',
        items=[
            ('0', 'DISABLE', 'do not draw secondary gradient (default)'),
            ('1', 'ENABLE', 'add secondary gradient RGB to fragment RGB')],
        default='0')


class NodeSocketEnumSrcBlendFunc(NodeSocketEnum):
    bl_idname = 'NodeSocketEnumSrcBlendFunc'
    bl_label = 'SrcBlendFunc Enum Node Socket'

    default_value: bpy.props.EnumProperty(
        name='SrcBlendFunc',
        description='todo',
        items=[
            ('0', 'ZERO', 'fragment not added to color buffer'),
            ('1', 'ONE', 'fragment added unmodified to color buffer (default)'),
            ('2', 'SRC_ALPHA', 'fragment RGB components multiplied by fragment A'),
            ('3', 'ONE_MINUS_SRC_ALPHA', 'fragment RGB components multiplied by fragment inverse (one minus) A')],
        default='1')


class NodeSocketEnumDetailColorFunc(NodeSocketEnum):
    bl_idname = 'NodeSocketEnumDetailColorFunc'
    bl_label = 'DetailColorFunc Enum Node Socket'

    default_value: bpy.props.EnumProperty(
        name='DetailColorFunc',
        description='todo',
        items=[
            ('0', 'DISABLE', 'local (default)'),
            ('1', 'DETAIL', 'other'),
            ('2', 'SCALE', 'local * other'),
            ('3', 'INVSCALE', '~(~local * ~other) = local + (1-local)*other'),
            ('4', 'ADD', 'local + other'),
            ('5', 'SUB', 'local - other'),
            ('6', 'SUBR', 'other - local'),
            ('7', 'BLEND', '(localAlpha)*local + (~localAlpha)*other'),
            ('8', 'DETAILBLEND', '(otherAlpha)*local + (~otherAlpha)*other'),
            ('9', '9_UNKNOWN', 'unknown'),
            ('10', '10_UNKNOWN', 'unknown'),
            ('11', '11_UNKNOWN', 'unknown'),
            ('12', 'MOD_ALPHA_ADD_COLOR', 'unknown')],
        default='0')


class NodeSocketEnumDetailAlphaFunc(NodeSocketEnum):
    bl_idname = 'NodeSocketEnumDetailAlphaFunc'
    bl_label = 'DetailAlphaFunc Enum Node Socket'

    default_value: bpy.props.EnumProperty(
        name='DetailAlphaFunc',
        description='todo',
        items=[
            ('0', 'DISABLE', 'local (default)'),
            ('1', 'DETAIL', 'other'),
            ('2', 'SCALE', 'local * other'),
            ('3', 'INVSCALE', '~(~local * ~other) = local + (1-local)*other')],
        default='0') 