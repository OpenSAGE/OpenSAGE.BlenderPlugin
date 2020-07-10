# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from io_mesh_w3d.w3d.structs.mesh_structs.vertex_material import *


class VertexMaterialGroup():
    @staticmethod
    def create(node_tree, vert_mat, shader):
        instance = node_tree.nodes.new(type='ShaderNodeGroup')
        instance.location = (0, 300)
        instance.width = 300

        instance.node_tree = bpy.data.node_groups['VertexMaterial']
        instance.label = vert_mat.vm_name

        # TODO: this should be done in parsing of vm_info?
        attributes = {'DEFAULT'}
        if vert_mat.vm_info.attributes & USE_DEPTH_CUE:
            attributes.add('USE_DEPTH_CUE')
        if vert_mat.vm_info.attributes & ARGB_EMISSIVE_ONLY:
            attributes.add('ARGB_EMISSIVE_ONLY')
        if vert_mat.vm_info.attributes & COPY_SPECULAR_TO_DIFFUSE:
            attributes.add('COPY_SPECULAR_TO_DIFFUSE')
        if vert_mat.vm_info.attributes & DEPTH_CUE_TO_ALPHA:
            attributes.add('DEPTH_CUE_TO_ALPHA')

        instance.inputs['Attributes'].default_value = attributes

        # TODO: translate those to shader properties
        # floats: UPerSec, VPerSec, UScale, VScale, FPS, Speed, UCenter, VCenter, UAmp, UFreq, UPhase, VAmp, VFreq, VPhase,
        #        UStep, VStep, StepsPerSecond, Offset, Axis, UOffset, VOffset, ClampFix, UseReflect, Period, VPerScale,
        #        BumpRotation, BumpScale
        # ints: Log1Width, Log2Width, Last(Frame)

        instance.inputs['VM_ARGS_0'].default_value = vert_mat.vm_args_0
        instance.inputs['VM_ARGS_1'].default_value = vert_mat.vm_args_1

        instance.inputs['Diffuse'].default_value = vert_mat.vm_info.diffuse.to_vector_rgba()
        instance.inputs['Ambient'].default_value = vert_mat.vm_info.ambient.to_vector_rgba()
        instance.inputs['Specular'].default_value = vert_mat.vm_info.specular.to_vector_rgba()
        instance.inputs['Emissive'].default_value = vert_mat.vm_info.emissive.to_vector_rgba()
        instance.inputs['Shininess'].default_value = vert_mat.vm_info.shininess
        instance.inputs['Opacity'].default_value = vert_mat.vm_info.shininess
        instance.inputs['Translucency'].default_value = vert_mat.vm_info.shininess

        instance.inputs['DepthCompare'].default_value = str(shader.depth_compare)
        instance.inputs['DepthMaskWrite'].default_value = str(shader.depth_mask)
        instance.inputs['ColorMask'].default_value = shader.color_mask
        instance.inputs['FogFunc'].default_value = shader.fog_func
        instance.inputs['DestBlendFunc'].default_value = str(shader.dest_blend)
        instance.inputs['PriGradient'].default_value = str(shader.pri_gradient)
        instance.inputs['SecGradient'].default_value = str(shader.sec_gradient)
        instance.inputs['SrcBlendFunc'].default_value = str(shader.src_blend)
        instance.inputs['DetailColorFunc'].default_value = str(shader.detail_color_func)
        instance.inputs['DetailAlphaFunc'].default_value = str(shader.detail_alpha_func)
        instance.inputs['Preset'].default_value = shader.shader_preset
        instance.inputs['AlphaTest'].default_value = str(shader.alpha_test)
        instance.inputs['PostDetailColorFunc'].default_value = str(shader.post_detail_color_func)
        instance.inputs['PostDetailAlphaFunc'].default_value = str(shader.post_detail_alpha_func)

        return instance

    @staticmethod
    def addInputInt(group, name, default=0, min=0, max=255):
        group.inputs.new('NodeSocketInt', name)
        group.inputs[name].default_value = default
        group.inputs[name].min_value = min
        group.inputs[name].max_value = max

    @staticmethod
    def register():
        group = bpy.data.node_groups.new('VertexMaterial', 'ShaderNodeTree')
        node_tree = group
        node_tree.name = 'VertexMaterial'
        links = node_tree.links

        # create group inputs
        group_inputs = group.nodes.new('NodeGroupInput')
        group_inputs.location = (-350,0)

        group.inputs.new('NodeSocketEnumMaterialAttributes', 'Attributes')
        group.inputs.new('NodeSocketString', 'VM_ARGS_0')
        group.inputs.new('NodeSocketString', 'VM_ARGS_1')
        group.inputs.new('NodeSocketColor', 'Diffuse')
        group.inputs['Diffuse'].default_value = (0.8, 0.8, 0.8, 1.0)
        # TODO: Add secondary diffuse texture here?
        group.inputs.new('NodeSocketTexture', 'DiffuseTexture')
        group.inputs['DiffuseTexture'].default_value = (0.0, 0.0, 0.0, 0.0)
        group.inputs.new('NodeSocketTextureAlpha', 'DiffuseTextureAlpha')
        group.inputs.new('NodeSocketColor', 'Ambient')
        group.inputs['Ambient'].default_value = (0.8, 0.8, 0.8, 1.0)
        group.inputs.new('NodeSocketColor', 'Specular')
        group.inputs['Specular'].default_value = (0.8, 0.8, 0.8, 1.0)
        group.inputs.new('NodeSocketColor', 'Emissive')
        group.inputs['Emissive'].default_value = (0.8, 0.8, 0.8, 1.0)
        group.inputs.new('NodeSocketFloat', 'Shininess')
        group.inputs.new('NodeSocketFloat', 'Opacity')
        group.inputs.new('NodeSocketFloat', 'Translucency')

        group.inputs.new('NodeSocketEnumDepthCompare', 'DepthCompare')
        group.inputs.new('NodeSocketEnumDepthMaskWrite', 'DepthMaskWrite')
        VertexMaterialGroup.addInputInt(group, 'ColorMask') # obsolete (w3d_file.h)
        VertexMaterialGroup.addInputInt(group, 'FogFunc') # obsolete (w3d_file.h)
        group.inputs.new('NodeSocketEnumDestBlendFunc', 'DestBlendFunc')
        group.inputs.new('NodeSocketInt', 'DestBlendFunc')
        group.inputs.new('NodeSocketEnumPriGradient', 'PriGradient')
        group.inputs.new('NodeSocketEnumSecGradient', 'SecGradient')
        group.inputs.new('NodeSocketEnumSrcBlendFunc', 'SrcBlendFunc')
        group.inputs.new('NodeSocketEnumDetailColorFunc', 'DetailColorFunc')
        group.inputs.new('NodeSocketEnumDetailAlphaFunc', 'DetailAlphaFunc')
        VertexMaterialGroup.addInputInt(group, 'Preset') # obsolete (w3d_file.h)
        group.inputs.new('NodeSocketEnumAlphaTest', 'AlphaTest')
        group.inputs.new('NodeSocketEnumDetailColorFunc', 'PostDetailColorFunc')
        group.inputs.new('NodeSocketEnumDetailAlphaFunc', 'PostDetailAlphaFunc')

        # create group outputs
        group_outputs = group.nodes.new('NodeGroupOutput')
        group_outputs.location = (300,0)
        group.outputs.new('NodeSocketShader', 'BSDF')

        # create and link nodes
        alpha_pipeline = node_tree.nodes.new(type='ShaderNodeGroup')
        alpha_pipeline.location = (-100, 0)
        alpha_pipeline.node_tree = bpy.data.node_groups['AlphaPipeline']
        links.new(group_inputs.outputs['DiffuseTexture'], alpha_pipeline.inputs['Diffuse'])
        links.new(group_inputs.outputs['DiffuseTextureAlpha'], alpha_pipeline.inputs['Alpha'])
        links.new(group_inputs.outputs['AlphaTest'], alpha_pipeline.inputs['DestBlend'])

        shader = node_tree.nodes.new('ShaderNodeEeveeSpecular')
        shader.label = 'Shader'
        shader.location = (100, 0)
        shader.inputs['Normal'].hide = True

        links.new(group_inputs.outputs['DiffuseTexture'], shader.inputs['Base Color'])
        links.new(group_inputs.outputs['Specular'], shader.inputs['Specular'])
        links.new(group_inputs.outputs['Shininess'], shader.inputs['Roughness'])
        links.new(group_inputs.outputs['Emissive'], shader.inputs['Emissive Color'])
        links.new(alpha_pipeline.outputs['Alpha'], shader.inputs['Transparency'])
        links.new(shader.outputs['BSDF'], group_outputs.inputs['BSDF'])

    @staticmethod
    def unregister():
        if not 'VertexMaterial' in bpy.data.node_groups:
            return
        bpy.data.node_groups.remove(bpy.data.node_groups['VertexMaterial'])
