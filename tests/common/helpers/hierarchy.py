# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from io_mesh_w3d.common.structs.hierarchy import *
from tests.mathutils import *
from tests.w3d.helpers.version import get_version, compare_versions


def get_hierarchy_header(name='TestHierarchy'):
    return HierarchyHeader(
        version=get_version(major=4, minor=1),
        name=name,
        num_pivots=0,
        center_pos=get_vec(0.0, 0.0, 0.0))


def compare_hierarchy_headers(self, expected, actual):
    compare_versions(self, expected.version, actual.version)
    self.assertEqual(expected.name, actual.name)
    self.assertEqual(expected.num_pivots, actual.num_pivots)
    compare_vectors(self, expected.center_pos, actual.center_pos)


def get_hierarchy_pivot(name='', name_id=None, parent=-1):
    return HierarchyPivot(
        name=name,
        name_id=name_id,
        parent_id=parent,
        translation=get_vec(22.0, 33.0, 1.0),
        euler_angles=get_vec(0.32, -0.65, 0.67),
        rotation=get_quat(0.86, 0.25, -0.25, 0.36),
        fixup_matrix=get_mat())


def get_roottransform():
    return HierarchyPivot(
        name='ROOTTRANSFORM',
        name_id=None,
        parent_id=-1,
        translation=get_vec(2.0, 3.0, -1.0),
        euler_angles=get_vec(),
        rotation=get_quat(0.86, 0.25, -0.25, 0.36),
        fixup_matrix=get_mat())


def compare_hierarchy_pivots(self, expected, actual):
    self.assertEqual(expected.name, actual.name)
    if expected.name_id is not None:
        self.assertEqual(expected.name_id, actual.name_id)
    self.assertEqual(expected.parent_id, actual.parent_id)

    compare_vectors(self, expected.translation, actual.translation)
    # dont care for those
    # if expected.euler_angles :
    # compare_vectors(self, expected.euler_angles, actual.euler_angles)
    compare_quats(self, expected.rotation, actual.rotation)
    compare_mats(self, expected.fixup_matrix, actual.fixup_matrix)


def get_hierarchy(name='TestHierarchy', xml=False):
    hierarchy = Hierarchy(
        header=get_hierarchy_header(name),
        pivots=[],
        pivot_fixups=[])

    hierarchy.pivots = [
        get_roottransform(),
        get_hierarchy_pivot(name='b_waist', parent=0),
        get_hierarchy_pivot(name='b_hip', parent=1),
        get_hierarchy_pivot(name='shoulderl', parent=2),
        get_hierarchy_pivot(name='arml', parent=3),
        get_hierarchy_pivot(name='armr', parent=3),
        get_hierarchy_pivot(name='TRUNK', parent=5),
        get_hierarchy_pivot(name='sword', parent=0)]

    if xml:
        hierarchy.pivots.append(
            get_hierarchy_pivot(name_id=4, parent=0))
    else:
        hierarchy.header.num_pivots = len(hierarchy.pivots)
        hierarchy.pivot_fixups = [
            get_vec(),
            get_vec(),
            get_vec(),
            get_vec(),
            get_vec(),
            get_vec(),
            get_vec(),
            get_vec()]

    return hierarchy


def get_hierarchy_minimal(xml=False):
    hierarchy = Hierarchy(
        header=get_hierarchy_header(),
        pivots=[get_hierarchy_pivot()],
        pivot_fixups=[])

    if not xml:
        hierarchy.pivot_fixups = [get_vec()]
    return hierarchy


def get_hierarchy_empty():
    return Hierarchy(
        header=get_hierarchy_header(),
        pivots=[],
        pivot_fixups=[])


def compare_hierarchies(self, expected, actual):
    compare_hierarchy_headers(self, expected.header, actual.header)

    self.assertEqual(len(expected.pivots), len(actual.pivots))
    for i in range(len(expected.pivots)):
        compare_hierarchy_pivots(self, expected.pivots[i], actual.pivots[i])

    if expected.pivot_fixups:
        self.assertEqual(len(expected.pivot_fixups), len(actual.pivot_fixups))
        for i in range(len(expected.pivot_fixups)):
            compare_vectors(
                self, expected.pivot_fixups[i], actual.pivot_fixups[i])
