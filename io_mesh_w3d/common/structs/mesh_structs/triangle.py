# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector
from io_mesh_w3d.w3d.io_binary import *
from io_mesh_w3d.w3x.io_xml import *


surface_types = [
    'LightMetal',
    'HeavyMetal',
    'Water',
    'Sand',
    'Dirt',
    'Mud',
    'Grass',
    'Wood',
    'Concrete',
    'Flesh',
    'Rock',
    'Snow',
    'Ice',
    'Default',
    'Glass',
    'Cloth',
    'TiberiumField',
    'FoliagePermeable',
    'GlassPermeable',
    'IcePermeable',
    'ClothPermeable',
    'Electrical',
    'Flammable',
    'Steam',
    'ElectricalPermeable',
    'FlammablePermeable',
    'SteamPermeable',
    'WaterPermeable',
    'TiberiumWater',
    'TiberiumWaterPermeable',
    'UnderwaterDirt',
    'UnderwaterTiberiumDirt']


class Triangle:
    def __init__(self, vert_ids=None, surface_type=13, normal=Vector((0.0, 0.0, 0.0)), distance=0.0):
        self.vert_ids = vert_ids if vert_ids is not None else []
        self.surface_type = surface_type
        self.normal = normal
        self.distance = distance

    @staticmethod
    def validate_face_map_names(context, face_map_names):
        for name in face_map_names:
            if not name in surface_types:
                context.warning('name of face map: ' + name + ' is not one of valid surface types ' + str(surface_types))

    def get_surface_type_name(self):
        return surface_types[self.surface_type]

    def set_surface_type(self, name):
        if not name in surface_types:
            return
        self.surface_type = surface_types.index(name)

    @staticmethod
    def read(io_stream):
        return Triangle(
            vert_ids=[read_ulong(io_stream), read_ulong(io_stream), read_ulong(io_stream)],
            surface_type=read_ulong(io_stream),
            normal=read_vector(io_stream),
            distance=read_float(io_stream))

    @staticmethod
    def size():
        return 32

    def write(self, io_stream):
        write_ulong(self.vert_ids[0], io_stream)
        write_ulong(self.vert_ids[1], io_stream)
        write_ulong(self.vert_ids[2], io_stream)
        write_ulong(self.surface_type, io_stream)
        write_vector(self.normal, io_stream)
        write_float(self.distance, io_stream)

    @staticmethod
    def parse(xml_triangle):
        result = Triangle(vert_ids=[])

        for i, xml_vert in enumerate(xml_triangle.findall('V')):
            result.vert_ids.append(int(xml_vert.text))

        result.normal = parse_vector(xml_triangle.find('Nrm'))
        result.distance = float(xml_triangle.find('Dist').text)
        return result

    def create(self, parent):
        triangle = create_node(parent, 'T')
        for vert_id in self.vert_ids:
            xml_vert = create_node(triangle, 'V')
            xml_vert.text = str(vert_id)

        create_vector(self.normal, triangle, 'Nrm')
        xml_distance = create_node(triangle, 'Dist')
        xml_distance.text = format(self.distance)
