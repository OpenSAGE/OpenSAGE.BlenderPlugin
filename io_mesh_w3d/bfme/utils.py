# <pep8 compliant>
"""Helpers shared by the BfMe tools."""

import os

import bpy
import numpy as np
from mathutils import Vector

from . import cache
from ..common.utils.helpers import iter_action_fcurves

IMPORT_OPERATOR = 'import_mesh.westwood_w3d'
EXPORT_OPERATOR = 'export_mesh.westwood_w3d'


##########################################################################
# scene snapshots
#
# The Blender API is not thread safe, so anything a worker thread needs has to be
# copied out of the scene into plain Python objects on the main thread first.
##########################################################################


def refresh_big_lists(scene):
    """Populate the per game .big file lists from the configured install paths."""
    for collection_name, path_name in (
            ('bfme2_big_files', 'bfmeII_install_path'),
            ('rotwk_big_files', 'rotwk_install_path')):
        collection = getattr(scene, collection_name)
        previous = {item.filepath: item.selected for item in collection}

        collection.clear()
        for filepath in sorted(cache.gather_big_filepaths(getattr(scene, path_name, ''))):
            item = collection.add()
            item.name = os.path.basename(filepath)
            item.filepath = filepath
            item.selected = previous.get(filepath, False)


def selected_big_paths(scene):
    """Selected .big archives, highest priority first."""
    paths = []
    for enabled_name, collection_name in (
            ('use_bfme2_assets', 'bfme2_big_files'),
            ('use_rotwk_assets', 'rotwk_big_files')):
        if not getattr(scene, enabled_name, False):
            continue
        selected = [item.filepath for item in getattr(scene, collection_name)
                    if item.selected and item.filepath and os.path.isfile(item.filepath)]
        selected.sort(reverse=True)
        paths.extend(selected)
    return paths


def search_paths(scene):
    paths = []
    for entry in getattr(scene, 'texture_search_paths', ()):
        if not entry.path:
            continue
        absolute = bpy.path.abspath(entry.path)
        if os.path.isdir(absolute):
            paths.append(absolute)
    return paths


##########################################################################
# w3d import / export
##########################################################################


def import_w3d(filepath):
    """Import a .w3d/.w3x through this add-on's own importer.

    The BfMe tools used to search all of bpy.ops for something that looked like a
    W3D importer. Now that both live in the same add-on the operator is known.
    """
    return bpy.ops.import_mesh.westwood_w3d(filepath=filepath)


##########################################################################
# animation
##########################################################################


BONE_PATH_PREFIX = 'pose.bones["'


def clear_bone_fcurves(animation_data, bone_names, properties=('location', 'rotation')):
    """Remove the given properties' f-curves of the given bones from the action.

    Collected in one walk over the action for all bones at once, instead of walking
    it again per bone, and routed through the channelbags because 'Action.fcurves'
    no longer exists since the slotted actions of Blender 4.4+. Removal happens
    after the walk so the collection is not mutated while it is being iterated.
    """
    if animation_data is None or animation_data.action is None:
        return 0

    wanted = set(bone_names)
    doomed = []

    for owner, fcurve in iter_action_channelbag_fcurves(animation_data):
        path = fcurve.data_path
        if not path.startswith(BONE_PATH_PREFIX):
            continue

        name, separator, prop = path[len(BONE_PATH_PREFIX):].partition('"].')
        if not separator or name not in wanted or not prop.startswith(properties):
            continue

        doomed.append((owner, fcurve))

    for owner, fcurve in doomed:
        try:
            owner.fcurves.remove(fcurve)
        except (RuntimeError, ReferenceError):
            continue
    return len(doomed)


def iter_action_channelbag_fcurves(animation_data):
    """Yield (owner, fcurve) pairs, where owner is what the curve can be removed from."""
    action = None if animation_data is None else animation_data.action
    if action is None:
        return

    action_slot = getattr(animation_data, 'action_slot', None)
    found = False

    for layer in getattr(action, 'layers', []):
        for strip in getattr(layer, 'strips', []):
            channelbag = None
            if hasattr(strip, 'channelbag'):
                channelbag = strip.channelbag(action_slot)
            else:
                channelbags = getattr(strip, 'channelbags', [])
                if action_slot is None and len(channelbags) == 1:
                    channelbag = channelbags[0]
                else:
                    for candidate in channelbags:
                        if getattr(candidate, 'slot', None) == action_slot:
                            channelbag = candidate
                            break
            if channelbag is not None:
                for fcurve in channelbag.fcurves:
                    found = True
                    yield channelbag, fcurve

    if not found and hasattr(action, 'fcurves'):
        for fcurve in action.fcurves:
            yield action, fcurve


def last_keyframe(obj):
    """Highest keyframe time of the object's action, or None."""
    if obj.animation_data is None:
        return None

    latest = None
    for fcurve in iter_action_fcurves(obj.animation_data):
        points = fcurve.keyframe_points
        if not points:
            continue
        # keyframes are stored in time order, so only the last one matters
        frame = points[-1].co[0]
        if latest is None or frame > latest:
            latest = frame
    return latest


##########################################################################
# geometry
#
# Transforming every vertex through 'matrix_world @ v.co' in Python costs a
# temporary Vector per vertex. foreach_get plus numpy does the same arithmetic on
# whole arrays and is orders of magnitude faster on real models.
##########################################################################


def mesh_world_coords(obj):
    """(n, 3) array of the object's vertices in world space, or None if it has none."""
    mesh = getattr(obj, 'data', None)
    if mesh is None:
        return None

    vertices = getattr(mesh, 'vertices', None)
    if not vertices:
        return None

    count = len(vertices)
    coords = np.empty(count * 3, dtype=np.float64)
    vertices.foreach_get('co', coords)
    coords = coords.reshape(count, 3)

    matrix = np.array(obj.matrix_world, dtype=np.float64)
    return coords @ matrix[:3, :3].T + matrix[:3, 3]


def stacked_world_coords(objects):
    """All vertices of all mesh objects in world space as one (n, 3) array."""
    chunks = [coords for coords in (mesh_world_coords(obj) for obj in objects if obj.type == 'MESH')
              if coords is not None and len(coords)]
    if not chunks:
        return None
    return np.concatenate(chunks) if len(chunks) > 1 else chunks[0]


def world_bounds(objects):
    """(min, max) vectors over all vertices of the given mesh objects."""
    coords = stacked_world_coords(objects)
    if coords is None:
        return None, None
    return Vector(coords.min(axis=0)), Vector(coords.max(axis=0))


def max_world_vertex_z(objects):
    """Highest vertex Z in world space, or None if there are no vertices."""
    highest = None
    for obj in objects:
        if obj.type != 'MESH':
            continue
        coords = mesh_world_coords(obj)
        if coords is None or not len(coords):
            continue
        value = float(coords[:, 2].max())
        if highest is None or value > highest:
            highest = value
    return highest
