# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

from tests.w3x.helpers.include import *
from tests.utils import TestCase


class TestInclude(TestCase):
    def test_write_read_xml(self):
        self.write_read_xml_test(get_include(), 'Include', Include.parse, compare_includes)
