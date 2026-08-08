# <pep8 compliant>
"""BfMe modding tools.

Originally a separate add-on built on top of the W3D importer/exporter, now part of
it: the tools call this add-on's own import and export operators directly and reuse
its custom mesh and material properties.
"""

from . import settings
from .tools import (
    build_up_animation,
    destroy_animation,
    existing_animations,
    export_settings,
    model_browser,
    texture_finder,
    w3d_tools)

# display order of the top-level panels within the 'W3D Tools' sidebar tab
MODULES = (
    texture_finder,
    model_browser,
    existing_animations,
    build_up_animation,
    destroy_animation,
    export_settings,
    w3d_tools)


def register():
    settings.register()
    for module in MODULES:
        module.register()


def unregister():
    for module in reversed(MODULES):
        module.unregister()
    settings.unregister()
