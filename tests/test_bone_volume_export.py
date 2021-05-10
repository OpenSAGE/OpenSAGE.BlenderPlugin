# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os
import bmesh
from io_mesh_w3d.common.utils.mesh_export import *
from io_mesh_w3d.bone_volume_export import *
from tests.utils import *


class TestBoneVolumeExport(TestCase):
    def test_bone_volume_export(self):
        create_volume(self, 'volume1', 33, 1.22, 'DEBRIS')
        create_volume(self, 'volume2', 21, 3.22, 'DEBRIS', Vector((22.332, 2.11, -5)))

        bpy.context.view_layer.update()

        xmlFile = None

        try:
            export_bone_volume_data(self, 'output.xml')

            xmlFile = open('output.xml', 'r')

            self.assertEqual('<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n', xmlFile.readline())
            self.assertEqual('<BoneVolumes>\n', xmlFile.readline())
            self.assertEqual(
                '  <BoneVolume BoneName="volume1" ContactTag="DEBRIS" Mass="33.000" Spinniness="1.220">\n',
                xmlFile.readline())
            self.assertEqual('    <Box HalfSizeX="0.500" HalfSizeY="0.500" HalfSizeZ="0.500">\n', xmlFile.readline())
            self.assertEqual('      <Translation X="0.000000" Y="0.000000" Z="0.000000" />\n', xmlFile.readline())
            self.assertEqual(
                '      <Rotation W="1.000000" X="0.000000" Y="0.000000" Z="0.000000" />\n',
                xmlFile.readline())
            self.assertEqual('    </Box>\n', xmlFile.readline())
            self.assertEqual('  </BoneVolume>\n', xmlFile.readline())
            self.assertEqual(
                '  <BoneVolume BoneName="volume2" ContactTag="DEBRIS" Mass="21.000" Spinniness="3.220">\n',
                xmlFile.readline())
            self.assertEqual('    <Box HalfSizeX="0.500" HalfSizeY="0.500" HalfSizeZ="0.500">\n', xmlFile.readline())
            self.assertEqual('      <Translation X="22.332001" Y="2.110000" Z="-5.000000" />\n', xmlFile.readline())
            self.assertEqual(
                '      <Rotation W="1.000000" X="0.000000" Y="0.000000" Z="0.000000" />\n',
                xmlFile.readline())
            self.assertEqual('    </Box>\n', xmlFile.readline())
            self.assertEqual('  </BoneVolume>\n',
                             xmlFile.readline())
            self.assertEqual('</BoneVolumes>\n', xmlFile.readline())

            xmlFile.close()

        except Exception as e:
            raise e
        finally:
            xmlFile.close()
            os.remove('output.xml')


def create_volume(context, name, mass, spinniness, contact_tag, location=Vector((0, 0, 0))):
    mesh = bpy.data.meshes.new(name)
    mesh.mass = mass
    mesh.spinniness = spinniness
    mesh.contact_tag = contact_tag
    mesh.object_type = 'BONE_VOLUME'

    b_mesh = bmesh.new()
    bmesh.ops.create_cube(b_mesh, size=1)
    b_mesh.to_mesh(mesh)

    prepare_bmesh(context, mesh)

    object = bpy.data.objects.new(mesh.name, mesh)
    object.location = location

    link_object_to_active_scene(object, bpy.context.scene.collection)
    mesh.update()
