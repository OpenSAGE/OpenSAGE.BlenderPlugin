# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from shutil import copyfile

from io_mesh_w3d.w3x.import_w3x import *
from io_mesh_w3d.w3x.io_xml import *
from tests.shared.helpers.collision_box import get_collision_box
from tests.shared.helpers.hierarchy import get_hierarchy
from tests.shared.helpers.hlod import get_hlod
from tests.shared.helpers.mesh import get_mesh
from tests.shared.helpers.animation import get_animation
from tests.utils import *
from os.path import dirname as up


class TestObjectImport(TestCase):
    def test_import_animation_only_no_include(self):
        hierarchy_name = 'TestHiera_SKL'
        hierarchy = get_hierarchy(hierarchy_name)
        animation = get_animation(hierarchy_name)

        copyfile(up(up(self.relpath())) + '/testfiles/texture.dds',
                 self.outpath() + 'texture.dds')

        # write to file
        doc = minidom.Document()
        asset = create_asset_declaration(doc)
        asset.appendChild(hierarchy.create(doc))
        doc.appendChild(asset)

        file = open(self.outpath() + hierarchy_name + '.w3x', "wb")
        file.write(bytes(doc.toprettyxml(indent='   '), 'UTF-8'))
        file.close()

        doc = minidom.Document()
        asset = create_asset_declaration(doc)
        asset.appendChild(animation.create(doc))
        doc.appendChild(asset)

        file = open(self.outpath() + 'animation.w3x', "wb")
        file.write(bytes(doc.toprettyxml(indent='   '), 'UTF-8'))
        file.close()

        # import
        ani = IOWrapper(self.outpath() + 'animation.w3x')
        load(ani, import_settings={})

        self.assertTrue(hierarchy_name in bpy.data.objects)
        self.assertTrue(hierarchy_name in bpy.data.armatures)