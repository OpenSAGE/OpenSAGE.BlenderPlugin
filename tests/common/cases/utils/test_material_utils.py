# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import bpy

from tests.utils import TestCase
from unittest.mock import patch

from tests.common.helpers.mesh_structs.shader_material import *
from tests.w3d.helpers.mesh_structs.vertex_material import *
from io_mesh_w3d.common.utils.material_import import *


class TestMaterialUtils(TestCase):
    def test_shader_material_creation_unimplemented_property(self):
        shader_mat = get_shader_material()
        shader_mat.properties.append(get_shader_material_property(2, 'UnimplementedProp'))

        with (patch.object(self, 'error')) as report_func:
            create_material_from_shader_material(self, 'lorem ipsum', shader_mat)
            report_func.assert_called_with('shader property not implemented: UnimplementedProp')


class TestZeroSpecular(TestCase):
    """Every import path (File > Import, the BfMe model browser, its preview
    renderer) is expected to leave a model looking the same, which for the
    Principled BSDF's specular input means zero: W3D materials do not carry one,
    and the shininess value the importer maps onto that socket does not correspond
    to it.
    """

    def principled_specular(self, material):
        for node in material.node_tree.nodes:
            if node.type != 'BSDF_PRINCIPLED':
                continue
            for name in ('Specular IOR Level', 'IOR Level', 'Specular'):
                socket = node.inputs.get(name)
                if socket is not None:
                    return socket.default_value
        return None

    def test_a_freshly_imported_vertex_material_has_nonzero_specular(self):
        """Establishes the premise: without the fix, an imported material's
        specular comes straight from the file's shininess value.
        """
        vert_mat = get_vertex_material()
        material, principled = create_material_from_vertex_material('mesh', vert_mat)

        self.assertAlmostEqual(vert_mat.vm_info.shininess, self.principled_specular(material), places=5)
        self.assertNotEqual(0.0, self.principled_specular(material))

    def test_zero_specular_clears_it(self):
        vert_mat = get_vertex_material()
        material, _ = create_material_from_vertex_material('mesh', vert_mat)

        zero_specular([material])

        self.assertEqual(0.0, self.principled_specular(material))

    def test_zero_specular_of_a_material_without_a_node_tree(self):
        material = bpy.data.materials.new('no_nodes')

        zero_specular([material])  # must not raise

    def test_flatten_materials_collects_from_children_without_duplicates(self):
        parent_mesh = bpy.data.meshes.new('parent')
        parent = bpy.data.objects.new('parent', parent_mesh)
        child_mesh = bpy.data.meshes.new('child')
        child = bpy.data.objects.new('child', child_mesh)
        child.parent = parent

        shared = bpy.data.materials.new('shared')
        parent_mesh.materials.append(shared)
        child_mesh.materials.append(shared)
        child_mesh.materials.append(bpy.data.materials.new('child_only'))

        bpy.context.scene.collection.objects.link(parent)
        bpy.context.scene.collection.objects.link(child)

        materials = flatten_materials([parent])

        self.assertEqual(['shared', 'child_only'], [m.name for m in materials])

    def test_flatten_materials_skips_empty_slots(self):
        mesh = bpy.data.meshes.new('mesh')
        mesh.materials.append(None)
        obj = bpy.data.objects.new('mesh', mesh)
        bpy.context.scene.collection.objects.link(obj)

        self.assertEqual([], flatten_materials([obj]))
