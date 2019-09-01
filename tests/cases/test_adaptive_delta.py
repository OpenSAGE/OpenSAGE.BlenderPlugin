# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019
from io_mesh_w3d.w3d_adaptive_delta import to_signed, get_deltas
from tests import utils


class TestAdaptiveDelta(utils.W3dTestCase):
    def test_to_signed(self):
        self.assertEqual(to_signed(255), -1)
        self.assertEqual(to_signed(100), 100)

    def test_get_deltas(self):
        deltaBytes = [-3, 17, -32, -101, -120, -88, -20, -1]
        deltas = get_deltas(deltaBytes, 4)
        expected = [-3, -1, 1, 1, 0, -2, -5, -7, -8, -8, -8, -6, -4, -2, -1, -1]
        self.assertEqual(deltas, expected)

        deltaBytes = [-49, -50, -53, -57, -62, -69, -73, -75, -82, -94, -111, 123, 82, 37, 12, 4]
        deltas = get_deltas(deltaBytes, 8)
        expected = [79, 78, 75, 71, 66, 59, 55, 53, 46, 34, 17, -5, -46, -91, -116, -124]
        self.assertEqual(deltas, expected)
