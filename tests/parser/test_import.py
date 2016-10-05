import os
import unittest

import pybel

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestImport(unittest.TestCase):
    def test_full(self):

        path = os.path.join(dir_path, os.pardir, 'bel', 'test_bel_1.bel')
        g = pybel.load(path)

        expected_document_metadata = {
            'Name': "PyBEL Test Document",
            "Description": "Made for testing PyBEL parsing",
            'Version': "1.6",
            'Copyright': "Copyright (c) Charles Tapley Hoyt. All Rights Reserved.",
            'Authors': "Charles Tapley Hoyt",
            'Licenses': "Other / Proprietary",
            'ContactInfo': "charles.hoyt@scai.fraunhofer.de"
        }

        self.assertEqual(expected_document_metadata, g.mdp.document_metadata)
