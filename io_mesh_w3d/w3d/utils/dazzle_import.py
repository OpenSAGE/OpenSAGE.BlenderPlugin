# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy
from bpy_extras import node_shader_utils
from io_mesh_w3d.common.utils.primitives import *
from io_mesh_w3d.common.utils.helpers import *


def create_dazzle(context, dazzle, coll):
    # TODO: proper dimensions for cone
    (dazzle_mesh, dazzle_cone) = create_cone(dazzle.name())
    dazzle_cone.data.object_type = 'DAZZLE'
    dazzle_cone.data.dazzle_type = dazzle.type_name
    link_object_to_active_scene(dazzle_cone, coll)

    material = bpy.data.materials.new(dazzle.name())
    material.use_nodes = True
    material.blend_method = 'BLEND'
    material.show_transparent_back = False

    principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
    principled.base_color = (255, 255, 255)
    principled.base_color_texture.image = find_texture(context, 'SunDazzle.tga')
    dazzle_mesh.materials.append(material)
