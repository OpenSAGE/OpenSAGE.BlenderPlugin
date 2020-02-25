# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from shutil import copyfile

from io_mesh_w3d.export_utils import *
from io_mesh_w3d.import_utils import *
from tests.common.helpers.animation import *
from tests.common.helpers.collision_box import *
from tests.common.helpers.hierarchy import *
from tests.common.helpers.hlod import *
from tests.common.helpers.mesh import *
from tests.common.helpers.mesh_structs.shader_material import *
from tests.utils import *
from tests.w3d.helpers.compressed_animation import *
from tests.w3d.helpers.dazzle import *
from tests.w3d.helpers.mesh_structs.shader import *
from tests.w3d.helpers.mesh_structs.vertex_material import *
from os.path import dirname as up


class TestUtils(TestCase):
    def test_vertex_material_roundtrip(self):
        mesh = get_mesh()

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        for source in mesh.vert_materials:
            (material, _) = create_material_from_vertex_material(
                self, mesh.name(), source)
            actual = retrieve_vertex_material(material)
            compare_vertex_materials(self, source, actual)

    def test_vertex_material_no_attributes_roundtrip(self):
        mesh = get_mesh()

        for source in mesh.vert_materials:
            source.vm_info.attributes = 0
            (material, _) = create_material_from_vertex_material(
                self, mesh.name(), source)
            actual = retrieve_vertex_material(material)
            compare_vertex_materials(self, source, actual)

    def test_shader_material_roundtrip(self):
        mesh = get_mesh()
        mesh.shader_materials = [get_shader_material()]

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        for source in mesh.shader_materials:
            (material, _) = create_material_from_shader_material(
                self, mesh.name(), source)
            principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
            actual = retrieve_shader_material(material, principled)
            compare_shader_materials(self, source, actual)

    def test_duplicate_shader_material_roundtrip(self):
        mesh = get_mesh()
        mesh.shader_materials = [get_shader_material(), get_shader_material()]

        materials = []
        for mat in mesh.shader_materials:
            (material, _) = create_material_from_shader_material(self, 'meshName', mat)
            materials.append(material)

        self.assertEqual(1, len(bpy.data.materials))
        self.assertTrue('meshName.ShaderMaterial.fx' in bpy.data.materials)

        for expected in mesh.shader_materials:
            principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
            actual = retrieve_shader_material(material, principled)
            compare_shader_materials(self, expected, actual)

    def test_shader_material_w3x_roundtrip(self):
        mesh = get_mesh()
        mesh.shader_materials = [get_shader_material(w3x=True)]
        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        for source in mesh.shader_materials:
            (material, _) = create_material_from_shader_material(
                self, mesh.name(), source)
            principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
            actual = retrieve_shader_material(material, principled, w3x=True)
            compare_shader_materials(self, source, actual)

    def test_shader_material_w3x_rgb_colors_roundtrip(self):
        mesh = get_mesh()
        mesh.shader_materials = [get_shader_material(w3x=True, rgb_colors=True)]

        for source in mesh.shader_materials:
            (material, _) = create_material_from_shader_material(
                self, mesh.name(), source)
            principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
            actual = retrieve_shader_material(material, principled, w3x=True)

            for prop in source.properties:
                if prop.name in ['ColorAmbient', 'ColorEmissive', 'ColorDiffuse', 'ColorSpecular']:
                    prop.type = 5
                    prop.value = Vector((prop.value[0], prop.value[1], prop.value[2], 1.0))

            compare_shader_materials(self, source, actual)

    def test_shader_material_w3x_two_tex_roundtrip(self):
        mesh = get_mesh()
        mesh.shader_materials = [get_shader_material(w3x=True, two_tex=True)]

        for source in mesh.shader_materials:
            (material, _) = create_material_from_shader_material(
                self, mesh.name(), source)
            principled = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
            actual = retrieve_shader_material(material, principled, w3x=True)
            compare_shader_materials(self, source, actual)

    def test_default_shader_material_properties_are_not_exported(self):
        mesh = get_mesh(shader_mats=True)
        mesh.shader_materials[0].properties = []

        (material, principled) = create_material_from_shader_material(self, mesh.name(), mesh.shader_materials[0])

        actual = retrieve_shader_material(material, principled, w3x=False)
        for prop in actual.properties:
            print (prop.name)
        self.assertEqual(0, len(actual.properties))

        actual = retrieve_shader_material(material, principled, w3x=True)
        self.assertEqual(0, len(actual.properties))

    def test_shader_material_minimal_roundtrip(self):
        mesh = get_mesh()

        for source in mesh.shader_materials:
            source.properties = []

            (material, _) = create_material_from_shader_material(
                self, mesh, source)
            principled = retrieve_principled_bsdf(material)
            actual = retrieve_shader_material(material, principled)
            source.properties = get_shader_material_properties_minimal()
            compare_shader_materials(self, source, actual)

    def test_shader_roundtrip(self):
        mesh = get_mesh()

        (material, _) = create_material_from_vertex_material(
            self, mesh.name(), mesh.vert_materials[0])
        expected = mesh.shaders[0]
        set_shader_properties(material, expected)
        actual = retrieve_shader(material)
        compare_shaders(self, expected, actual)

    def test_boxes_roundtrip(self):
        hlod = get_hlod()
        hlod.lod_arrays[0].sub_objects.append(
            get_hlod_sub_object(bone=1, name='containerName.WORLDBOX'))
        hierarchy = get_hierarchy()
        meshes = []
        boxes = [get_collision_box(), get_collision_box(
            'containerName.WORLDBOX')]

        create_data(self, meshes, hlod, hierarchy, boxes)

        self.compare_data([], None, None, boxes)

    def test_dazzles_roundtrip(self):
        hlod = get_hlod(hierarchy_name='containerName')
        hlod.lod_arrays[0].header.model_count = 3
        hlod.lod_arrays[0].sub_objects = [
            get_hlod_sub_object(bone=1, name='containerName.Backlight'),
            get_hlod_sub_object(bone=2, name='containerName.Headlight'),
            get_hlod_sub_object(bone=3, name='containerName.Blinklight')]

        hierarchy = get_hierarchy(name='containerName')
        hierarchy.header.num_pivots = 4
        hierarchy.pivots = [
            get_roottransform(),
            get_hierarchy_pivot(name='BacklightPivot', parent=0),
            get_hierarchy_pivot(name='HeadlightPivot', parent=1),
            get_hierarchy_pivot(name='Blinklight', parent=1)]
        meshes = []
        dazzles = [get_dazzle(name='containerName.Backlight', type='REN_BRAKELIGHT'),
                   get_dazzle(name='containerName.Headlight', type='REN_HEADLIGHT'),
                   get_dazzle(name='containerName.Blinklight', type='REN_HEADLIGHT')]

        create_data(self, [], hlod, hierarchy, [], None, None, dazzles)

        self.compare_data([], hlod, hierarchy, [], None, None, dazzles)

    def test_hierarchy_roundtrip(self):
        hierarchy = get_hierarchy()
        hlod = get_hlod()
        boxes = [get_collision_box()]
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK'),
            get_mesh(name='PICK')]

        create_data(self, meshes, hlod, hierarchy, boxes)

        self.compare_data([], None, hierarchy)

    def test_hierarchy_only_roundtrip(self):
        hierarchy = get_hierarchy()

        create_data(self, [], None, hierarchy)

        self.compare_data([], None, hierarchy)

    def test_hierarchy_roundtrip_pivot_order_is_correct(self):
        hierarchy = get_hierarchy()
        hierarchy.pivots = [
            get_roottransform(),
            get_hierarchy_pivot(name='bone_chassis01', parent=0),
            get_hierarchy_pivot(name='bone_treadlf', parent=1),
            get_hierarchy_pivot(name='bone_treadlr', parent=1),
            get_hierarchy_pivot(name='bone_treadrf', parent=1),
            get_hierarchy_pivot(name='bone_treadrr', parent=1),
            get_hierarchy_pivot(name='bone_turret', parent=1),
            get_hierarchy_pivot(name='bone_rocketpod', parent=6),
            get_hierarchy_pivot(name='turret01', parent=7),
            get_hierarchy_pivot(name='rocketlaunch01', parent=8),
            get_hierarchy_pivot(name='turret02', parent=7),
            get_hierarchy_pivot(name='rocketlaunch02', parent=10),
            get_hierarchy_pivot(name='bone_rails', parent=6),
            get_hierarchy_pivot(name='bone_barrel_01', parent=12),
            get_hierarchy_pivot(name='muzzlefx01', parent=13),
            get_hierarchy_pivot(name='muzzleflash_01', parent=13),
            get_hierarchy_pivot(name='muzzleflash_02', parent=13),
            get_hierarchy_pivot(name='ugrail_01', parent=13),
            get_hierarchy_pivot(name='bone_barrel_02', parent=12),
            get_hierarchy_pivot(name='muzzlefx02', parent=18),
            get_hierarchy_pivot(name='ugrail_02', parent=18),
            get_hierarchy_pivot(name='fxtrackslf', parent=1),
            get_hierarchy_pivot(name='fxtrackslr', parent=1),
            get_hierarchy_pivot(name='fxtracksrf', parent=1),
            get_hierarchy_pivot(name='fxtracksrr', parent=1)]
        hierarchy.header.num_pivots = len(hierarchy.pivots)

        hlod = get_hlod()
        hlod.lod_arrays[0].sub_objects = [
            get_hlod_sub_object(bone=0, name='containerName.treadsback'),
            get_hlod_sub_object(bone=0, name='containerName.treadsleft'),
            get_hlod_sub_object(bone=0, name='containerName.treadsmove'),
            get_hlod_sub_object(bone=0, name='containerName.treadsright'),
            get_hlod_sub_object(bone=0, name='containerName.treadsstop'),
            get_hlod_sub_object(bone=0, name='containerName.mammothtank'),
            get_hlod_sub_object(bone=20, name='containerName.ugrail_02'),
            get_hlod_sub_object(bone=17, name='containerName.ugrail_01'),
            get_hlod_sub_object(bone=16, name='containerName.muzzleflash_02'),
            get_hlod_sub_object(bone=15, name='containerName.muzzleflash_01'),
            get_hlod_sub_object(bone=0, name='containerName.rocketpods'), ]
        hlod.lod_arrays[0].header.model_count = len(hlod.lod_arrays[0].sub_objects)

        meshes = [
            get_mesh(name='treadsbaack', skin=True),
            get_mesh(name='treadsleft', skin=True),
            get_mesh(name='treadsmove', skin=True),
            get_mesh(name='treadsright', skin=True),
            get_mesh(name='treadsstop', skin=True),
            get_mesh(name='mammothtank', skin=True),
            get_mesh(name='ugrail_02'),
            get_mesh(name='ugrail_01'),
            get_mesh(name='muzzleflash_02'),
            get_mesh(name='muzzleflash_01'),
            get_mesh(name='rocketpods', skin=True)]

        create_data(self, meshes, hlod, hierarchy, [])

        (actual_hiera, rig) = retrieve_hierarchy(self, 'containerName')

        self.compare_data([], None, hierarchy)

    def test_too_many_hierarchies_roundtrip(self):
        hierarchy = get_hierarchy()
        hierarchy2 = get_hierarchy(name='TestHierarchy2')
        hlod = get_hlod()
        boxes = [get_collision_box()]
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK'),
            get_mesh(name='PICK')]

        create_data(self, meshes, hlod, hierarchy, boxes)
        coll = get_collection(hlod)
        rig2 = get_or_create_skeleton(hlod, hierarchy2, coll)

        self.assertEqual(2, len(get_objects('ARMATURE')))

        (actual_hiera, rig) = retrieve_hierarchy(self, 'containerName')
        self.assertIsNone(actual_hiera)
        self.assertIsNone(rig)

    def test_hlod_roundtrip(self):
        hlod = get_hlod()
        boxes = [get_collision_box()]
        hierarchy = get_hierarchy()
        dazzles = [get_dazzle()]
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK'),
            get_mesh(name='PICK')]

        create_data(self, meshes, hlod, hierarchy, boxes, None, None, dazzles)

        self.compare_data([], hlod, hierarchy)

    def test_mesh_only_hlod_roundtrip(self):
        hlod = get_hlod()
        hlod.header.hierarchy_name = 'containerName'
        hlod.lod_arrays[0].header.model_count = 1
        hlod.lod_arrays[0].sub_objects = [
            get_hlod_sub_object(bone=0, name='containerName.tree')]

        meshes = [get_mesh(name='tree')]

        create_data(self, meshes)

        self.compare_data([], hlod)

    def test_hlod_4_levels_roundtrip(self):
        hlod = get_hlod_4_levels()
        hlod.header.hierarchy_name = 'containerName'
        hierarchy = get_hierarchy()
        hierarchy.header.name = 'containerName'
        hierarchy.pivots = [
            get_roottransform(),
            get_hierarchy_pivot(name='parent', parent=0),
            get_hierarchy_pivot(name='child', parent=1)]
        hierarchy.header.num_pivots = len(hierarchy.pivots)

        meshes = [
            get_mesh(name='mesh1'),
            get_mesh(name='mesh2'),
            get_mesh(name='mesh3'),

            get_mesh(name='mesh1_1'),
            get_mesh(name='mesh2_1'),
            get_mesh(name='mesh3_1'),

            get_mesh(name='mesh1_2'),
            get_mesh(name='mesh2_2'),
            get_mesh(name='mesh3_2'),

            get_mesh(name='mesh1_3'),
            get_mesh(name='mesh2_3'),
            get_mesh(name='mesh3_3')]

        create_data(self, meshes, hlod, hierarchy)

        self.compare_data(meshes, hlod, hierarchy)

    def test_PICK_mesh_roundtrip(self):
        hlod = get_hlod()
        boxes = [get_collision_box()]
        hierarchy = get_hierarchy()
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK'),
            get_mesh(name='PICK')]
        dazzles = [get_dazzle()]

        create_data(self, meshes, hlod, hierarchy, boxes, None, None, dazzles)

        self.compare_data(meshes, hlod, hierarchy, boxes)

    def test_mesh_is_child_of_mesh_roundtrip(self):
        hlod = get_hlod()
        hlod.header.hierarchy_name = 'containerName'
        hlod.lod_arrays[0].sub_objects = [
            get_hlod_sub_object(bone=1, name='containerName.parent'),
            get_hlod_sub_object(bone=2, name='containerName.child')]
        hlod.lod_arrays[0].header.model_count = len(
            hlod.lod_arrays[0].sub_objects)

        hierarchy = get_hierarchy()
        hierarchy.header.name = 'containerName'
        hierarchy.pivots = [
            get_roottransform(),
            get_hierarchy_pivot(name='parent', parent=0),
            get_hierarchy_pivot(name='child', parent=1)]
        hierarchy.header.num_pivots = len(hierarchy.pivots)

        meshes = [
            get_mesh(name='parent'),
            get_mesh(name='child')]

        create_data(self, meshes, hlod, hierarchy)

        self.compare_data(meshes, hlod, hierarchy)

    def test_meshes_roundtrip(self):
        hlod = get_hlod()
        boxes = [get_collision_box()]
        hierarchy = get_hierarchy()
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK', shader_mats=True),
            get_mesh(name='PICK')]

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.tga')

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture_nrm.tga')

        create_data(self, meshes, hlod, hierarchy, boxes)

        self.compare_data(meshes)

    def test_mesh_too_many_vertex_groups_roundtrip(self):
        hlod = get_hlod()
        boxes = [get_collision_box()]
        hierarchy = get_hierarchy()
        meshes = [
            get_mesh(name='sword', skin=True)]

        create_data(self, meshes, hlod, hierarchy, boxes)

        sword = bpy.context.scene.objects['sword']
        sword.vertex_groups.new(name='number3')
        sword.vertex_groups['number3'].add([3], 0.4, 'REPLACE')

        self.compare_data(meshes)

    def test_meshes_only_roundtrip(self):
        meshes = [
            get_mesh(name='wall'),
            get_mesh(name='tower'),
            get_mesh(name='tower2', shader_mats=True),
            get_mesh(name='stone')]

        create_data(self, meshes)

        self.compare_data(meshes)

    def test_meshes_roundtrip_has_only_shader_materials_on_w3x_export(self):
        meshes = [
            get_mesh(name='wall'),
            get_mesh(name='tower'),
            get_mesh(name='tower2', shader_mats=True),
            get_mesh(name='stone')]

        create_data(self, meshes)

        (actual_hiera, rig) = retrieve_hierarchy(self, 'containerName')
        self.file_format = 'W3X'
        (actual_meshes, _) = retrieve_meshes(self, actual_hiera, rig, 'containerName')
        self.assertEqual(len(meshes), len(actual_meshes))
        for mesh in actual_meshes:
            self.assertEqual(0, len(mesh.vert_materials))
            self.assertEqual(0, len(mesh.shaders))
            self.assertTrue(mesh.shader_materials)

    def test_meshes_roundtrip_used_textures_are_correct(self):
        expected = ['texture.dds', 'texture_nrm.dds', 'texture_spec.dds', 'texture_env.tga', 'texture_scroll.dds']
        meshes = [
            get_mesh(name='wall'),
            get_mesh(name='tower'),
            get_mesh(name='tower2', shader_mats=True),
            get_mesh(name='stone')]

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture_nrm.dds')

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture_spec.dds')

        create_data(self, meshes)

        (actual_hiera, rig) = retrieve_hierarchy(self, 'containerName')
        (_, used_textures) = retrieve_meshes(self, actual_hiera, rig, 'containerName')

        self.assertEqual(len(expected), len(used_textures))
        for i, tex in enumerate(expected):
            self.assertEqual(tex, used_textures[i])

    def test_meshes_no_textures_found_roundtrip(self):
        meshes = [
            get_mesh(name='wall'),
            get_mesh(name='tower2', shader_mats=True)]

        create_data(self, meshes)

        self.compare_data(meshes)

    def test_hidden_meshes_roundtrip(self):
        meshes = [
            get_mesh(name='wall', hidden=True),
            get_mesh(name='tower', hidden=True),
            get_mesh(name='tower2', shader_mats=True),
            get_mesh(name='stone')]

        create_data(self, meshes)

        self.compare_data(meshes)

    def test_prelit_meshes_roundtrip(self):
        hlod = get_hlod()
        hierarchy = get_hierarchy()
        meshes = [get_mesh(name='sword', skin=True, prelit=True)]

        create_data(self, meshes, hlod, hierarchy)

        # not yet supported
        # self.compare_data(meshes, None, None)

    def test_animation_roundtrip(self):
        animation = get_animation()
        hlod = get_hlod()
        boxes = [get_collision_box()]
        hierarchy = get_hierarchy()
        hierarchy.pivot_fixups = []

        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK'),
            get_mesh(name='PICK')]

        create_data(self, meshes, hlod, hierarchy, boxes, animation)

        self.compare_data([], None, None, [], animation)

    def test_animation_only_roundtrip(self):
        animation = get_animation()
        hierarchy = get_hierarchy()

        create_data(self, [], None, hierarchy, [], animation)

        self.compare_data([], None, None, [], animation)

    def test_compressed_animation_roundtrip(self):
        compressed_animation = get_compressed_animation(
            flavor=0,
            bit_channels=False,
            motion_tc=False,
            motion_ad4=False,
            motion_ad8=False,
            random_interpolation=False)
        boxes = [get_collision_box()]
        hlod = get_hlod()
        hierarchy = get_hierarchy()
        hierarchy.pivot_fixups = []
        meshes = [
            get_mesh(name='sword', skin=True),
            get_mesh(name='soldier', skin=True),
            get_mesh(name='TRUNK'),
            get_mesh(name='PICK')]

        create_data(self, meshes, hlod, hierarchy,
                    boxes, None, compressed_animation)

        self.compare_data([], None, None, [], None, compressed_animation)

    def test_roundtrip_only_needed_keyframes(self):
        animation = get_compressed_animation_empty()
        animation.header.flavor = 0
        channel = TimeCodedAnimationChannel(
            num_time_codes=5,
            vector_len=1,
            pivot=1,
            type=1,
            time_codes=[TimeCodedDatum(time_code=0, value=3.0),
                        TimeCodedDatum(time_code=1, value=3.0),
                        TimeCodedDatum(time_code=2, value=3.0),
                        TimeCodedDatum(time_code=3, value=3.0),
                        TimeCodedDatum(time_code=4, value=3.0)])

        channel_q = TimeCodedAnimationChannel(
            num_time_codes=7,
            vector_len=4,
            pivot=1,
            type=6,
            time_codes=[TimeCodedDatum(time_code=0, value=Quaternion((0.1, 0.8, 0.7, 0.2))),
                        TimeCodedDatum(time_code=1, value=Quaternion((0.1, 0.8, 0.7, 0.2))),
                        TimeCodedDatum(time_code=2, value=Quaternion((0.1, 0.8, 0.7, 0.1))),
                        TimeCodedDatum(time_code=3, value=Quaternion((0.1, 0.8, 0.7, 0.1))),
                        TimeCodedDatum(time_code=4, value=Quaternion((0.1, 0.8, 0.7, 0.1))),
                        TimeCodedDatum(time_code=5, value=Quaternion((0.2, 0.8, 0.7, 0.1))),
                        TimeCodedDatum(time_code=6, value=Quaternion((0.2, 0.8, 0.7, 0.1)))])

        animation.time_coded_channels = [channel, channel_q]

        hierarchy = get_hierarchy()
        hierarchy.pivots = [get_roottransform(), HierarchyPivot(name='bone', parent_id=0)]

        self.filepath = self.outpath() + 'output'
        create_data(self, [], None, hierarchy, [], None, animation)

        channel = TimeCodedAnimationChannel(
            num_time_codes=2,
            vector_len=1,
            pivot=1,
            type=1,
            time_codes=[TimeCodedDatum(time_code=0, value=3.0),
                        TimeCodedDatum(time_code=4, value=3.0)])

        animation.time_coded_channels = [channel, channel_q]

        self.compare_data([], None, None, [], None, animation)

    def test_bone_is_created_if_referenced_by_subObject_but_also_child_bones_roundtrip(
            self):
        hlod = get_hlod()
        hierarchy = get_hierarchy()
        hierarchy.pivot_fixups = []
        hierarchy.pivots = [
            get_roottransform(),
            get_hierarchy_pivot(name='bone_pivot', parent=0),
            get_hierarchy_pivot(name='bone_pivot2', parent=1),
            get_hierarchy_pivot(name='bone_pivot3', parent=2)]

        hierarchy.header.num_pivots = len(hierarchy.pivots)

        array = HLodLodArray(
            header=get_hlod_array_header(),
            sub_objects=[get_hlod_sub_object(bone=0, name='containerName.BOUNDINGBOX'),
                         get_hlod_sub_object(bone=1, name='containerName.bone_pivot'),
                         get_hlod_sub_object(bone=2, name='containerName.bone_pivot2')])

        array.header.model_count = len(array.sub_objects)
        hlod.lod_arrays = [array]
        meshes = [
            get_mesh(name='bone_pivot'),
            get_mesh(name='bone_pivot2')]

        create_data(self, meshes, hlod, hierarchy)

        (_, rig) = retrieve_hierarchy(self, 'containerName')

        self.assertTrue('bone_pivot' in rig.pose.bones)
        self.assertTrue('bone_pivot2' in rig.pose.bones)
        self.assertTrue('bone_pivot3' in rig.pose.bones)

    def test_bone_is_created_if_referenced_by_subObject_but_names_dont_match(
            self):
        hlod = get_hlod()
        hlod.lod_arrays[0].sub_objects = [get_hlod_sub_object(bone=1, name='containerName.object')]
        hlod.lod_arrays[0].header.model_count = 1

        hierarchy = get_hierarchy()
        hierarchy.pivot_fixups = []
        hierarchy.pivots = [
            get_roottransform(),
            get_hierarchy_pivot(name='object_bone', parent=0),
            get_hierarchy_pivot(name='bone2', parent=0)]

        hierarchy.header.num_pivots = len(hierarchy.pivots)

        meshes = [get_mesh(name='object')]

        create_data(self, meshes, hlod, hierarchy)

        (_, rig) = retrieve_hierarchy(self, 'containerName')

        self.assertTrue('object_bone' in rig.pose.bones)

    def compare_data(
            self,
            meshes=[],
            hlod=None,
            hierarchy=None,
            boxes=[],
            animation=None,
            compressed_animation=None,
            dazzles=[]):
        container_name = 'containerName'
        rig = None
        actual_hiera = None
        actual_hlod = None

        (actual_hiera, rig) = retrieve_hierarchy(self, container_name)
        if hierarchy is not None:
            hierarchy.pivot_fixups = []  # roundtrip not supported
            compare_hierarchies(self, hierarchy, actual_hiera)

        actual_hlod = create_hlod(actual_hiera, container_name)
        if hlod is not None:
            compare_hlods(self, hlod, actual_hlod)

        if meshes:
            (actual_meshes, textures) = retrieve_meshes(
                self, actual_hiera, rig, container_name)
            self.assertEqual(len(meshes), len(actual_meshes))
            for i, mesh in enumerate(meshes):
                compare_meshes(self, mesh, actual_meshes[i])

        if boxes:
            actual_boxes = retrieve_boxes(container_name)

            self.assertEqual(len(boxes), len(actual_boxes))
            for i, box in enumerate(boxes):
                compare_collision_boxes(self, box, actual_boxes[i])

        if dazzles:
            actual_dazzles = retrieve_dazzles(container_name)

            self.assertEqual(len(dazzles), len(actual_dazzles))
            for i, dazzle in enumerate(dazzles):
                compare_dazzles(self, dazzle, actual_dazzles[i])

        if animation is not None:
            actual_animation = retrieve_animation(
                animation.header.name, actual_hiera, rig, timecoded=False)
            compare_animations(self, animation, actual_animation)

        if compressed_animation is not None:
            actual_compressed_animation = retrieve_animation(
                compressed_animation.header.name, actual_hiera, rig, timecoded=True)
            compare_compressed_animations(
                self, compressed_animation, actual_compressed_animation)
