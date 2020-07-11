# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel


class DataContext:
    def __init__(self, container_name='', rig=None, hierarchy=None, meshes=None, dazzles=None, hlod=None, textures=None,
                 collision_boxes=None, animation=None, compressed_animation=None):
        self.container_name = container_name
        self.rig = rig
        self.hierarchy = hierarchy
        self.meshes = meshes if meshes is not None else []
        self.dazzles = dazzles if dazzles is not None else []
        self.hlod = hlod
        self.textures = textures if textures is not None else []
        self.collision_boxes = collision_boxes if collision_boxes is not None else []
        self.animation = animation
        self.compressed_animation = compressed_animation
