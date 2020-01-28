# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from bpy_extras.io_utils import ImportHelper, ExportHelper

from io_mesh_w3d.custom_properties import *

bl_info = {
    'name': 'Import/Export Westwood W3D Format (.w3d/.w3x)',
    'author': 'OpenSage Developers',
    'version': (0, 4, 0),
    "blender": (2, 81, 0),
    'location': 'File > Import/Export > Westwood W3D (.w3d/.w3x)',
    'description': 'Import or Export the Westwood W3D-Format (.w3d/.w3x)',
    'warning': 'Still in Progress',
    'wiki_url': 'https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin',
    'tracker_url': 'https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin/issues',
    'support': 'OFFICIAL',
    'category': 'Import-Export'}


class ExportW3D(bpy.types.Operator, ExportHelper):
    '''Export to Westwood 3D file format (.w3d)'''
    bl_idname = 'export_mesh.westwood_w3d'
    bl_label = 'Export W3D/W3X'
    bl_options = {'UNDO', 'PRESET'}

    filename_ext = ''

    filter_glob: StringProperty(default='*.w3d;*.w3x', options={'HIDDEN'})

    file_format: bpy.props.EnumProperty(
        name="Format",
        items=(
            ('W3D',
             'Westwood 3D Binary (.w3d)',
             'Exports to W3D format, which was used in earlier SAGE games.'
             'Namely Command and Conquer Generals and the Battle for Middleearth series'),
            ('W3X',
             'Westwood 3D XML (.w3x)',
             'Exports to W3X format, which was used in later SAGE games.'
             'Namely everything starting from Command and Conquer 3')),
        description="Select the export file format",
        default='W3D')

    export_mode: EnumProperty(
        name='Mode',
        items=(
            ('HM',
             'Hierarchical Model',
             'This will export all the meshes of the scene with hierarchy/skeleton data'),
            ('HAM',
             'Hierarchical Animated Model',
             'This will export all the meshes of the scene with hierarchy/skeleton and animation data'),
            ('A',
             'Animation',
             'This will export the animation without any geometry or hierarchy/skeleton data'),
            ('H',
             'Hierarchy',
             'This will export the hierarchy/skeleton without any geometry or animation data'),
            ('M',
             'Mesh',
             'This will export a simple mesh (only the first of the scene if there are multiple), \
                without any hierarchy/skeleton and animation data')),
        description='Select the export mode',
        default='HM')

    use_existing_skeleton: BoolProperty(
        name='Use existing skeleton', description='Use an already existing skeleton (.skn)', default=False)

    animation_compression: EnumProperty(
        name='Compression',
        items=(('U', 'Uncompressed', 'This will not compress the animations'),
               ('TC', 'TimeCoded', 'This will export the animation with keyframes'),
               # ('AD', 'AdaptiveDelta',
               # 'This will use adaptive delta compression to reduce size'),
               ),
        description='The method used for compressing the animation data',
        default='U')

    create_texture_xmls: BoolProperty(
        name='Create texture xml files', description='Creates an .xml file for each used texture', default=False)

    will_save_settings: BoolProperty(default=False)

    scene_key = 'w3dExportSettings'

    def warning(self, msg):
        print('WARNING: ' + msg)
        self.report({'WARNING'}, msg)

    def error(self, msg):
        print('ERROR: ' + msg)
        self.report({'ERROR'}, msg)

    def invoke(self, context, event):
        settings = context.scene.get(self.scene_key)
        self.will_save_settings = False
        if settings:
            try:
                for (k, v) in settings.items():
                    setattr(self, k, v)
                self.will_save_settings = True

            except (AttributeError, TypeError):
                self.error('Loading export settings failed. Removed corrupted settings')
                del context.scene[self.scene_key]

        return ExportHelper.invoke(self, context, event)

    def save_settings(self, context):
        all_props = self.properties
        export_props = {x: getattr(self, x) for x in dir(
            all_props) if x.startswith('export_') and all_props.get(x) is not None}

        context.scene[self.scene_key] = export_props

    def execute(self, context):
        if self.will_save_settings:
            self.save_settings(context)

        export_settings = {}
        export_settings['mode'] = self.export_mode
        export_settings['compression'] = self.animation_compression
        export_settings['use_existing_skeleton'] = self.use_existing_skeleton
        export_settings['create_texture_xmls'] = self.create_texture_xmls

        data_context = DataContext(
            container_name='',
            rig=None,
            meshes=[],
            textures=[],
            collision_boxes=[],
            dazzles=[],
            hierarchy=None,
            hlod=None)

        if not retrieve_data(self, export_settings, data_context):
            return {'CANCELLED'}

        if self.file_format == 'W3X':
            self.filename_ext = '.w3x'
            self.filepath += '.w3x'
            from .w3x.export_w3x import save
            return save(self, export_settings, data_context)
        else:
            self.filename_ext = '.w3d'
            self.filepath += '.w3d'
            from .w3d.export_w3d import save
            return save(self, export_settings, data_context)

    def draw(self, _context):
        self.draw_general_settings()
        if self.export_mode == 'HM':
            self.draw_use_existing_skeleton()

        if self.file_format == 'W3X' and (self.export_mode == 'HM' or self.export_mode == 'HAM'):
            self.draw_create_texture_xmls()

        if (self.export_mode == 'A' or self.export_mode == 'HAM') \
                and not self.file_format == 'W3X':
            self.draw_animation_settings()

    def draw_general_settings(self):
        col = self.layout.box().column()
        col.prop(self, 'file_format')
        col = self.layout.box().column()
        col.prop(self, 'export_mode')

    def draw_use_existing_skeleton(self):
        col = self.layout.box().column()
        col.prop(self, 'use_existing_skeleton')

    def draw_animation_settings(self):
        col = self.layout.box().column()
        col.prop(self, 'animation_compression')

    def draw_create_texture_xmls(self):
        col = self.layout.box().column()
        col.prop(self, 'create_texture_xmls')


class ImportW3D(bpy.types.Operator, ImportHelper):
    '''Import from Westwood 3D file format (.w3d)'''
    bl_idname = 'import_mesh.westwood_w3d'
    bl_label = 'Import W3D/W3X'
    bl_options = {'UNDO'}

    filter_glob: StringProperty(default='*.w3d;*.w3x', options={'HIDDEN'})

    def warning(self, msg):
        print('WARNING: ' + msg)
        self.report({'WARNING'}, msg)

    def error(self, msg):
        print('ERROR: ' + msg)
        self.report({'ERROR'}, msg)

    def execute(self, context):
        if self.filepath.lower().endswith('.w3d'):
            from .w3d.import_w3d import load
            load(self, import_settings={})
        else:
            from .w3x.import_w3x import load
            load(self, import_settings={})

        print('finished')
        return {'FINISHED'}


def menu_func_export(self, _context):
    self.layout.operator(ExportW3D.bl_idname, text='Westwood W3D (.w3d/.w3x)')


def menu_func_import(self, _context):
    self.layout.operator(ImportW3D.bl_idname, text='Westwood W3D (.w3d/.w3x)')


CLASSES = (
    ExportW3D,
    ImportW3D,
    OBJECT_PANEL_PT_w3d,
    MATERIAL_PROPERTIES_PANEL_PT_w3d,
    MATERIAL_SHADER_PROPERTIES_PANEL_PT_w3d
)


def register():
    for class_ in CLASSES:
        bpy.utils.register_class(class_)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    for class_ in reversed(CLASSES):
        bpy.utils.unregister_class(class_)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == '__main__':
    register()
