import os
import tempfile
import unittest

import pybel
from pybel.parser.canonicalize import decanonicalize_graph
from tests.constants import test_bel_0, test_bel_1, test_bel_3, test_bel_4


class TestCanonicalize(unittest.TestCase):
    def setUp(self):
        self.tdir = tempfile.mkdtemp()

    def doCleanups(self):
        os.rmdir(self.tdir)

    def canonicalize_tester_helper(self, test_path):
        g_out = pybel.from_path(test_path)

        tpath = os.path.join(self.tdir, 'out.bel')

        with open(tpath, 'w') as f:
            decanonicalize_graph(g_out, f)

        g_in = pybel.from_path(tpath)

        os.remove(tpath)
        self.assertFalse(os.path.exists(tpath))

        self.assertEqual(g_out.document, g_in.document)
        self.assertEqual(g_out.namespace_owl, g_out.namespace_owl)
        self.assertEqual(g_out.namespace_url, g_out.namespace_url)
        self.assertEqual(g_out.namespace_list, g_out.namespace_list)
        self.assertEqual(g_out.annotation_url, g_out.annotation_url)
        self.assertEqual(g_out.annotation_list, g_out.annotation_list)

        # self.assertEqual(set(g_out.nodes()), set(g_in.nodes()))
        self.assertEqual(set(g_out.edges()), set(g_in.edges()))

    def test_canonicalize_0(self):
        self.canonicalize_tester_helper(test_bel_0)

    def test_canonicalize_1(self):
        self.canonicalize_tester_helper(test_bel_1)

    def test_canonicalize_3(self):
        self.canonicalize_tester_helper(test_bel_3)

    def test_canonicalize_4(self):
        self.canonicalize_tester_helper(test_bel_4)
