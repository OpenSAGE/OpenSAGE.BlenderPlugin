# <pep8 compliant>
"""Scene level settings shared by the BfMe tools."""

import platform

import bpy
from bpy.props import BoolProperty, CollectionProperty, StringProperty
from bpy.types import PropertyGroup


class BigFileItem(PropertyGroup):
    name: StringProperty(name='Filename')
    filepath: StringProperty(name='Filepath', subtype='FILE_PATH')
    selected: BoolProperty(name='Use', default=False)


class TextureSearchPath(PropertyGroup):
    path: StringProperty(name='Search Path', subtype='DIR_PATH')
    load_to_cache: BoolProperty(
        name='Load to cache',
        description='Copy files from this path to the cache for faster access (may take a while initially)',
        default=False)


INSTALL_REGISTRY_KEYS = (
    ('bfmeII_install_path',
     r'SOFTWARE\WOW6432Node\Electronic Arts\Electronic Arts\The Battle for Middle-earth II'),
    ('rotwk_install_path',
     r'SOFTWARE\WOW6432Node\Electronic Arts\Electronic Arts\The Lord of the Rings, The Rise of the Witch-king'))


def detect_install_paths():
    """Read the BfMe II and RotWK install paths from the registry (Windows only)."""
    paths = {name: '' for name, _ in INSTALL_REGISTRY_KEYS}

    if platform.system() != 'Windows':
        return paths

    try:
        import winreg
    except ImportError:
        return paths

    for name, key in INSTALL_REGISTRY_KEYS:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key, 0, winreg.KEY_READ) as sub_key:
                paths[name] = winreg.QueryValueEx(sub_key, 'InstallPath')[0]
        except OSError:
            continue

    return paths


CLASSES = (
    BigFileItem,
    TextureSearchPath)

SCENE_PROPERTIES = (
    'texture_search_paths',
    'use_bfme2_assets',
    'use_rotwk_assets',
    'bfmeII_install_path',
    'rotwk_install_path',
    'bfme2_big_files',
    'rotwk_big_files',
    'show_bfme2_bigs',
    'show_rotwk_bigs')


def register():
    for class_ in CLASSES:
        bpy.utils.register_class(class_)

    scene = bpy.types.Scene
    install_paths = detect_install_paths()

    scene.texture_search_paths = CollectionProperty(type=TextureSearchPath)

    scene.use_bfme2_assets = BoolProperty(
        name='Use BfMe 2 assets',
        description='Include assets from the installed BfMe II .big archives',
        default=True)
    scene.use_rotwk_assets = BoolProperty(
        name='Use BfMe RotWk assets',
        description='Include assets from the installed RotWK .big archives',
        default=True)

    scene.bfmeII_install_path = StringProperty(
        name='BfMe II Install Path', default=install_paths['bfmeII_install_path'], subtype='DIR_PATH')
    scene.rotwk_install_path = StringProperty(
        name='RotWK Install Path', default=install_paths['rotwk_install_path'], subtype='DIR_PATH')

    scene.bfme2_big_files = CollectionProperty(type=BigFileItem)
    scene.rotwk_big_files = CollectionProperty(type=BigFileItem)

    scene.show_bfme2_bigs = BoolProperty(name='Show BfMe2 .big list', default=True)
    scene.show_rotwk_bigs = BoolProperty(name='Show RotWK .big list', default=True)


def unregister():
    for name in SCENE_PROPERTIES:
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)

    for class_ in reversed(CLASSES):
        bpy.utils.unregister_class(class_)
