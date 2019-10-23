# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
import io
from tests import utils
from shutil import copyfile

from io_mesh_w3d.import_utils_w3d import *
from io_mesh_w3d.export_utils_w3d import *
from tests.helpers.w3d_mesh import get_mesh, compare_meshes
from tests.helpers.w3d_material import compare_vertex_materials
from tests.helpers.w3d_shader_material import compare_shader_materials
from tests.helpers.w3d_shader import get_shader, compare_shaders
from tests.helpers.w3d_box import get_box, compare_boxes
from tests.helpers.w3d_hierarchy import get_hierarchy, compare_hierarchies
from tests.helpers.w3d_hlod import get_hlod, compare_hlods


class TestUtils(utils.W3dTestCase):
    def test_vertex_material_roundtrip(self):
        mesh = get_mesh()
        context = utils.ImportWrapper(self.outpath())

        copyfile(self.relpath() + "/testfiles/texture.dds", self.outpath() + "texture.dds")

        for source in mesh.vert_materials:
            material = create_material_from_vertex_material(context, mesh, source)
            actual = retrieve_vertex_material(material)
            compare_vertex_materials(self, source, actual)


    def test_shader_material_roundtrip(self):
        mesh = get_mesh()
        context = utils.ImportWrapper(self.outpath())

        copyfile(self.relpath() + "/testfiles/texture.dds", self.outpath() + "texture.dds")

        for source in mesh.shader_materials:
            material = create_material_from_shader_material(context, mesh, source)
            principled = retrieve_principled_bsdf(material)
            actual = retrieve_shader_material(material, principled)
            compare_shader_materials(self, source, actual)


    def test_shader_roundtrip(self):
        mesh = get_mesh()
        context = utils.ImportWrapper(self.outpath())

        material = create_material_from_vertex_material(context, mesh, mesh.vert_materials[0])
        expected = mesh.shaders[0]
        set_shader_properties(material, expected)
        actual = retrieve_shader(material)
        compare_shaders(self, expected, actual)


    def test_box_roundtrip(self):
        expected = get_box()
        hlod = get_hlod()
        create_box(expected, get_collection(None))

        boxes = retrieve_boxes(hlod)
        compare_boxes(self, expected, boxes[0])


    def test_hierarchy_roundtrip(self):
        context = utils.ImportWrapper(self.outpath())
        expected = get_hierarchy()
        hlod = get_hlod()
        meshes = [
            get_mesh(name="sword"), 
            get_mesh(name="soldier", skin=True), 
            get_mesh(name="shield")]

        coll = get_collection(hlod)
        rig = get_or_create_skeleton(hlod, expected, coll)

        for mesh in meshes:
            create_mesh(context, mesh, expected, rig)

        for mesh in meshes:
            rig_mesh(mesh, expected, rig, coll)

        get_or_create_skeleton(hlod, expected, get_collection(None))
        (actual, rig) = retrieve_hierarchy("containerName")
        compare_hierarchies(self, expected, actual)



