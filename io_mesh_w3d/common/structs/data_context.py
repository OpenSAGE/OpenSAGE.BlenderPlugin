# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.struct import Struct


class DataContext(Struct):
    container_name = ''
    rig = None
    hierarchy = None
    meshes = []
    dazzles = []
    hlod = None
    textures = []
    collision_boxes = []
    animation = None
    compressed_animation = None
