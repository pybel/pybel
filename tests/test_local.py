import unittest

try:
    from unittest import mock
except ImportError:
    import mock

import pybel
from tests.constants import BelReconstitutionMixin, MockSession, test_bel_1


# TODO make patch global for testing
class TestImportLocal(BelReconstitutionMixin, unittest.TestCase):
    @mock.patch('pybel.utils.requests.Session', side_effect=MockSession)
    def test_local_2(self, mock_get):
        g = pybel.from_path(test_bel_1)
        self.bel_1_reconstituted(g)
