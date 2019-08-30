# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 08.2019
import unittest
import io
import struct
import os
from io_mesh_w3d.import_w3d import *

class ImportWrapper:
    def __init__(self,filepath):  
        self.filepath = filepath

class TestObjectImport(unittest.TestCase):
    def test_import_structure(self):
        dirname = os.path.dirname(__file__)
        file = ImportWrapper(dirname + "/dol_amroth_citadel/gbdolamr.w3d")
        import_settings = {}
        load(file,bpy.context,import_settings)