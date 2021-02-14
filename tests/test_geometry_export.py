# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import os
import bmesh
from io_mesh_w3d.common.utils.mesh_export import *
from io_mesh_w3d.geometry_export import *
from tests.utils import *

XML_FILE = 'output.xml'


class TestGeometryExport(TestCase):
    def tester_geometry_export(self):
        create_shape(self, 'BOX', 'NONE')
        create_shape(self, 'SPHERE', 'VEHICLE', Vector((2, 2, 5)))
        create_shape(self, 'CYLINDER', 'STRUCTURE', Vector((22, 2, -5)))

        xmlFile = None

        try:
            export_geometry_data(self, XML_FILE)

            xmlFile = open(XML_FILE, 'r')

            self.assertEqual('<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n', xmlFile.readline())
            self.assertEqual('<Geometry isSmall="False">\n', xmlFile.readline())
            self.assertEqual('  <Shape Height="1.000" MajorRadius="0.500" MinorRadius="0.500" Type="BOX">\n', xmlFile.readline())
            self.assertEqual('    <Offset X="0.000000" Y="0.000000" Z="0.000000" />\n', xmlFile.readline())
            self.assertEqual('  </Shape>\n', xmlFile.readline())
            self.assertEqual('  <Shape ContactPointGeneration="VEHICLE" MajorRadius="0.500" Type="SPHERE">\n', xmlFile.readline())
            self.assertEqual('    <Offset X="0.000000" Y="0.000000" Z="0.000000" />\n', xmlFile.readline())
            self.assertEqual('  </Shape>\n', xmlFile.readline())
            self.assertEqual('  <Shape ContactPointGeneration="STRUCTURE" Height="1.000" MajorRadius="0.500" MinorRadius="0.500" Type="CYLINDER">\n', xmlFile.readline())
            self.assertEqual('    <Offset X="0.000000" Y="0.000000" Z="0.000000" />\n', xmlFile.readline())
            self.assertEqual('  </Shape>\n', xmlFile.readline())
            self.assertEqual('</Geometry>\n', xmlFile.readline())

            xmlFile.close()

        except Exception as e:
            raise e
        finally:
            xmlFile.close()
            os.remove(XML_FILE)

def create_shape(context, type, contact_point_type, location = Vector((0, 0, 0))):
    mesh = bpy.data.meshes.new('box')
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