# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import io

from tests.w3x.helpers.include import *
from tests.utils import TestCase


class TestInclude(TestCase):
    def test_write_read_xml(self):
        expected = get_include()

        root = create_root()
        expected.create(root)

        io_stream = io.BytesIO()
        write(root, io_stream)
        io_stream = io.BytesIO(io_stream.getvalue())

        root = find_root(self, io_stream)
        print(root)
        xml_includes = root.findall('Include')
        self.assertEqual(1, len(xml_includes))

        actual = Include.parse(self, xml_includes[0])
        compare_includes(self, expected, actual)
