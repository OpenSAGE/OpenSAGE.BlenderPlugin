# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os
import bmesh
from io_mesh_w3d.common.utils.mesh_export import *
from io_mesh_w3d.geometry_export import *
from tests.utils import *

XML_FILE = 'output.xml'
INI_FILE = 'output.ini'


class TestGeometryExport(TestCase):
    def test_geometry_export(self):
        create_mesh(self, 'mesh')
        create_shape(self, 'box', 'BOX', 'NONE')
        create_shape(self, 'sphere', 'SPHERE', 'VEHICLE', Vector((2, 2, 5)))
        create_shape(self, 'cylinder', 'CYLINDER', 'STRUCTURE', Vector((22.332, 2.11, -5)))

        create_empty(self, Vector((1, 3, -4)))
        create_empty(self, Vector((3.14, 3, 15)))

        bpy.context.view_layer.update()

        xmlFile = None
        iniFIle = None

        try:
            export_geometry_data(self, XML_FILE)

            xmlFile = open(XML_FILE, 'r')

            self.assertEqual('<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n', xmlFile.readline())
            self.assertEqual('<Geometry isSmall="False">\n', xmlFile.readline())
            self.assertEqual('  <Shape Height="1.000" MajorRadius="0.500" MinorRadius="0.500" Type="BOX">\n', xmlFile.readline())
            self.assertEqual('    <Offset X="0.000000" Y="0.000000" Z="0.000000" />\n', xmlFile.readline())
            self.assertEqual('  </Shape>\n', xmlFile.readline())
            self.assertEqual('  <Shape ContactPointGeneration="VEHICLE" MajorRadius="0.500" Type="SPHERE">\n', xmlFile.readline())
            self.assertEqual('    <Offset X="2.000000" Y="2.000000" Z="5.000000" />\n', xmlFile.readline())
            self.assertEqual('  </Shape>\n', xmlFile.readline())
            self.assertEqual('  <Shape ContactPointGeneration="STRUCTURE" Height="1.000" MajorRadius="0.500" MinorRadius="0.500" Type="CYLINDER">\n', xmlFile.readline())
            self.assertEqual('    <Offset X="22.332001" Y="2.110000" Z="-5.000000" />\n', xmlFile.readline())
            self.assertEqual('  </Shape>\n', xmlFile.readline())
            self.assertEqual('  <ContactPoint>\n', xmlFile.readline())
            self.assertEqual('    <Pos X="1.000000" Y="3.000000" Z="-4.000000" />\n', xmlFile.readline())
            self.assertEqual('  </ContactPoint>\n', xmlFile.readline())
            self.assertEqual('  <ContactPoint>\n', xmlFile.readline())
            self.assertEqual('    <Pos X="3.140000" Y="3.000000" Z="15.000000" />\n', xmlFile.readline())
            self.assertEqual('  </ContactPoint>\n', xmlFile.readline())
            self.assertEqual('</Geometry>\n', xmlFile.readline())

            xmlFile.close()

            iniFile = open(INI_FILE, 'r')

            self.assertEqual('\tGeometry\t\t\t\t= BOX\n', iniFile.readline())
            self.assertEqual('\tGeometryIsSmall\t\t\t= No\n', iniFile.readline())
            self.assertEqual('\tGeometryName\t\t\t= box\n', iniFile.readline())
            self.assertEqual('\tGeometryMajorRadius\t\t= 0.500\n', iniFile.readline())
            self.assertEqual('\tGeometryMinorRadius\t\t= 0.500\n', iniFile.readline())
            self.assertEqual('\tGeometryHeight\t\t\t= 1.000\n', iniFile.readline())

            self.assertEqual('\n', iniFile.readline())

            self.assertEqual('\tAdditionalGeometry\t\t= SPHERE\n', iniFile.readline())
            self.assertEqual('\tGeometryName\t\t\t= sphere\n', iniFile.readline())
            self.assertEqual('\tGeometryMajorRadius\t\t= 0.500\n', iniFile.readline())
            self.assertEqual('\tGeometryOffset\t\t\t= X:2.000 Y:2.000 Z:5.000\n', iniFile.readline())

            self.assertEqual('\n', iniFile.readline())

            self.assertEqual('\tAdditionalGeometry\t\t= CYLINDER\n', iniFile.readline())
            self.assertEqual('\tGeometryName\t\t\t= cylinder\n', iniFile.readline())
            self.assertEqual('\tGeometryMajorRadius\t\t= 0.500\n', iniFile.readline())
            self.assertEqual('\tGeometryMinorRadius\t\t= 0.500\n', iniFile.readline())
            self.assertEqual('\tGeometryHeight\t\t\t= 1.000\n', iniFile.readline())
            self.assertEqual('\tGeometryOffset\t\t\t= X:22.332 Y:2.110 Z:-5.000\n', iniFile.readline())

            self.assertEqual('\n', iniFile.readline())

            self.assertEqual('\tGeometryContactPoint\t= X:1.000 Y:3.000 Z:-4.000\n', iniFile.readline())
            self.assertEqual('\tGeometryContactPoint\t= X:3.140 Y:3.000 Z:15.000\n', iniFile.readline())

            iniFile.close()

        except Exception as e:
            raise e
        finally:
            xmlFile.close()
            iniFile.close()
            os.remove(XML_FILE)
            os.remove(INI_FILE)

def create_mesh(context, name):
    mesh = bpy.data.meshes.new(name)
    mesh.object_type = 'MESH'

    b_mesh = bmesh.new()
    bmesh.ops.create_cube(b_mesh, size=1)
    b_mesh.to_mesh(mesh)

    prepare_bmesh(context, mesh)

    object = bpy.data.objects.new(mesh.name, mesh)

    link_object_to_active_scene(object, bpy.context.scene.collection)


def create_shape(context, name, type, contact_point_type, location = Vector((0, 0, 0))):
    mesh = bpy.data.meshes.new(name)
    mesh.geometry_type = type
    mesh.contact_points_type = contact_point_type
    mesh.object_type = 'GEOMETRY'

    b_mesh = bmesh.new()
    bmesh.ops.create_cube(b_mesh, size=1)
    b_mesh.to_mesh(mesh)

    prepare_bmesh(context, mesh)

    object = bpy.data.objects.new(mesh.name, mesh)
    object.location = location

    link_object_to_active_scene(object, bpy.context.scene.collection)
    mesh.update()

def create_empty(context, location = Vector((0, 0, 0))):
    empty = bpy.data.objects.new("Empty", None)
    empty.location = location
    bpy.context.scene.collection.objects.link(empty)
