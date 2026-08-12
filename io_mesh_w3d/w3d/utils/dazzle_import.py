# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy_extras import node_shader_utils
from ...common.utils.primitives import *
from ...common.utils.helpers import *


def create_dazzle(context, dazzle, coll):
    # Todo: proper dimensions for cone
    (dazzle_mesh, dazzle_cone) = create_cone(dazzle.name())
    dazzle_cone.data.object_type = 'DAZZLE'
    dazzle_cone.data.dazzle_type = dazzle.type_name
    link_object_to_active_scene(dazzle_cone, coll)

    material = bpy.data.materials.new(dazzle.name())
    enable_nodes(material)
    set_blend_method(material, 'BLEND')
    set_transparency_overlap(material, False)

    principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
    principled.base_color = (255, 255, 255)
    principled.base_color_texture.image = find_texture(context, 'SunDazzle.tga')
    dazzle_mesh.materials.append(material)
