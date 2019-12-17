# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from mathutils import Vector, Quaternion, Matrix

from io_mesh_w3d.struct import Struct
from io_mesh_w3d.io_xml import *

class HierarchyPivot(Struct):
    name = ""
    name_id = 0
    parent_id = -1
    translation = Vector((0.0, 0.0, 0.0))
    rotation = Quaternion((1.0, 0.0, 0.0, 0.0))
    fixup_matrix = Matrix(([0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]))

    @staticmethod
    def parse(xml_pivot):
        pivot = HierarchyPivot(
            name=xml_pivot.attributes['Name'].value,
            name_id=int(xml_pivot.attributes['NameID'].value),
            parent_id=int(xml_pivot.attributes['Parent'].value))

        xml_translation = xml_pivot.getElementsByTagName('Translation')[0]
        pivot.translation = parse_vector(xml_translation)
        xml_rotation = xml_pivot.getElementsByTagName('Rotation')[0]
        pivot.rotation = parse_quaternion(xml_rotation)
        xml_fixup_matrix = xml_pivot.getElementsByTagName('FixupMatrix')[0]
        pivot.fixup_matrix = parse_matrix(xml_fixup_matrix)
        return pivot


    def create(self, doc):
        pivot = doc.createElement('Pivot')
        pivot.setAttribute('Name', self.name)
        pivot.setAttribute('NameID', str(self.name_id))
        pivot.setAttribute('Parent', str(self.parent_id))
        pivot.appendChild(create_vector(self.translation, doc, 'Translation'))
        pivot.appendChild(create_quaternion(self.rotation, doc))
        pivot.appendChild(create_matrix(self.fixup_matrix, doc))
        return pivot


#W3DHierarchy
class Hierarchy(Struct):
    id = ""
    pivots = []

    @staticmethod
    def parse(xml_hierarchy):
        result = Hierarchy(
            id=xml_hierarchy.attributes['id'].value,
            pivots=[])
        xml_pivots = xml_hierarchy.getElementsByTagName('Pivot')
        for xml_pivot in xml_pivots:
            result.pivots.append(HierarchyPivot.parse(xml_pivot))
        return result


    def create(self, doc):
        hierarchy = doc.createElement('W3DHierarchy')
        hierarchy.setAttribute('id', self.id)

        for pivot in self.pivots:
            hierarchy.appendChild(pivot.create(doc))
        return hierarchy
