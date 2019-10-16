# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 10.2019
import bpy
from tests import utils

from tests.helpers.w3d_mesh import get_mesh, compare_meshes
from tests.helpers.w3d_hlod import get_hlod, compare_hlods
from tests.helpers.w3d_hierarchy import get_hierarchy, compare_hierarchies
from tests.helpers.w3d_animation import get_animation, compare_animations
from tests.helpers.w3d_compressed_animation import get_compressed_animation, compare_compressed_animations

from io_mesh_w3d.export_w3d import save
from io_mesh_w3d.import_w3d import load


class TestRoundtrip(utils.W3dTestCase):
    #def test_roundtrip(self):
        #TODO

    def test_roundtrip_HAM(self):
        hierarchy = get_hierarchy()
        meshes = [get_mesh(), get_mesh(), get_mesh()]
        hlod = get_hlod()
        animation = get_animation()

        #write to file
        output = open(self.outpath() + "output.w3d", "wb")
        hierarchy.write(output)
        for mesh in meshes:
            mesh.write(output)
        hlod.write(output)
        animation.write(output)
        output.close()

        #TODO: import file
        #model = utils.ImportWrapper(self.outpath() + "output.w3d")
        #load(model, bpy.context, import_settings={})


        #TODO: compare structs to expected ones
        #TODO: export 
        #TODO: compare exported file with output.w3d
        


