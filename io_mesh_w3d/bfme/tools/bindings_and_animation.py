# <pep8 compliant>
"""'Bindings and Animation' tab: skeleton binding and existing-animation search,
as two sub-tabs of one panel.
"""

import bpy
from bpy.props import EnumProperty
from bpy.types import Panel

from . import bindings, existing_animations

TABS = (
    ('EXISTING_ANIMATIONS', 'Existing Animations', 'Search the asset paths for existing animations', 'ANIM', 0),
    ('BINDINGS', 'Bindings', 'Bind loose meshes to a skeleton', 'ARMATURE_DATA', 1))


class BINDINGS_AND_ANIMATION_PT_panel(Panel):
    bl_label = 'Bindings and Animation'
    bl_idname = 'BINDINGS_AND_ANIMATION_PT_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'W3D Tools'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.row().prop(scene, 'bfme_binding_tab', expand=True)
        layout.separator()

        if scene.bfme_binding_tab == 'BINDINGS':
            bindings.draw(layout, scene)
        else:
            existing_animations.draw(layout, scene)


CLASSES = (BINDINGS_AND_ANIMATION_PT_panel,)


def register():
    for class_ in CLASSES:
        bpy.utils.register_class(class_)

    bpy.types.Scene.bfme_binding_tab = EnumProperty(
        name='Tab', items=TABS, default='EXISTING_ANIMATIONS')


def unregister():
    if hasattr(bpy.types.Scene, 'bfme_binding_tab'):
        del bpy.types.Scene.bfme_binding_tab

    for class_ in reversed(CLASSES):
        bpy.utils.unregister_class(class_)
