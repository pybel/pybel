# -*- coding: utf-8 -*-

import logging
import time
import unittest

from six import string_types

from pybel import to_ndex, from_ndex, from_path
from tests.constants import test_bel_thorough, TemporaryCacheMixin, BelReconstitutionMixin

log = logging.getLogger(__name__)

TEST_ID = '014e5957-3d96-11e7-8f50-0ac135e8bacf'


class TestConversion(TemporaryCacheMixin, BelReconstitutionMixin):
    def test_round_trip(self):
        """Tests that a document can be uploaded and downloaded. Sleeps in the middle so that NDEx can process"""
        graph = from_path(test_bel_thorough, manager=self.manager)

        network_id = to_ndex(graph, debug=True)
        self.assertIsInstance(network_id, string_types)

        time.sleep(15)

        reloaded = from_ndex(network_id)
        self.bel_thorough_reconstituted(reloaded)

    def test_download(self):
        """Tests the download of a CX document from NDEx"""
        graph = from_ndex(TEST_ID)
        self.bel_thorough_reconstituted(graph)


if __name__ == '__main__':
    unittest.main()
