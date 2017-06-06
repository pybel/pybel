# -*- coding: utf-8 -*-

import json
import unittest

from pybel import BELGraph
from pybel.constants import *
from pybel.struct.operations import left_full_join, left_outer_join

HGNC = 'HGNC'


class TestMerge(unittest.TestCase):
    """Tests various graph merging procedures"""

    def test_left_full_hash_join(self):
        """Tests left full hash join"""
        p1 = PROTEIN, HGNC, 'a'
        p2 = PROTEIN, HGNC, 'b'
        p3 = PROTEIN, HGNC, 'c'

        g = BELGraph()

        g.add_simple_node(*p1)
        g.add_simple_node(*p2)

        g.add_edge(p1, p2, attr_dict={
            RELATION: INCREASES,
            CITATION: {
                CITATION_TYPE: 'PubMed',
                CITATION_REFERENCE: 1,
                CITATION_NAME: 'PMID1'
            },
            EVIDENCE: 'Evidence 1',
            ANNOTATIONS: {}
        })

        h = BELGraph()

        h.add_simple_node(*p1)
        h.add_simple_node(*p2)
        h.add_simple_node(*p3)

        h.node[p1]['EXTRANEOUS'] = 'MOST DEFINITELY'
        h.node[p3]['EXTRANEOUS'] = 'MOST DEFINITELY'

        h.add_edge(p1, p2, attr_dict={
            RELATION: INCREASES,
            CITATION: {
                CITATION_TYPE: 'PubMed',
                CITATION_REFERENCE: 1,
                CITATION_NAME: 'PMID1'
            },
            EVIDENCE: 'Evidence 1',
            ANNOTATIONS: {}
        })

        h.add_edge(p1, p2, attr_dict={
            RELATION: INCREASES,
            CITATION: {
                CITATION_TYPE: 'PubMed',
                CITATION_REFERENCE: 2,
                CITATION_NAME: 'PMID2'
            },
            EVIDENCE: 'Evidence 2',
            ANNOTATIONS: {}
        })

        h.add_edge(p1, p3, attr_dict={
            RELATION: INCREASES,
            CITATION: {
                CITATION_TYPE: 'PubMed',
                CITATION_REFERENCE: 1,
                CITATION_NAME: 'PMID1'
            },
            EVIDENCE: 'Evidence 3',
            ANNOTATIONS: {}
        })

        self.assertEqual(2, g.number_of_nodes())
        self.assertEqual(1, g.number_of_edges())
        self.assertEqual(3, h.number_of_nodes())
        self.assertEqual(3, h.number_of_edges())

        left_full_join(g, h, use_hash=True)

        self.assertNotIn('EXTRANEOUS', g.node[p1])
        self.assertIn('EXTRANEOUS', g.node[p3])
        self.assertEqual('MOST DEFINITELY', g.node[p3]['EXTRANEOUS'])

        self.assertEqual(3, g.number_of_nodes())
        self.assertEqual(3, g.number_of_edges(), msg="G edges:\n{}".format(json.dumps(g.edges(data=True), indent=2)))
        self.assertEqual(3, h.number_of_nodes())
        self.assertEqual(3, h.number_of_edges())

    def test_left_full_exhaustive_join(self):
        """Tests left full merge"""
        p1 = PROTEIN, HGNC, 'a'
        p2 = PROTEIN, HGNC, 'b'
        p3 = PROTEIN, HGNC, 'c'

        g = BELGraph()

        g.add_simple_node(*p1)
        g.add_simple_node(*p2)

        g.add_edge(p1, p2, attr_dict={
            RELATION: INCREASES,
            CITATION: {
                CITATION_TYPE: 'PubMed',
                CITATION_REFERENCE: 1,
                CITATION_NAME: 'PMID1'
            },
            EVIDENCE: 'Evidence 1',
            ANNOTATIONS: {}
        })

        h = BELGraph()

        h.add_simple_node(*p1)
        h.add_simple_node(*p2)
        h.add_simple_node(*p3)

        h.node[p1]['EXTRANEOUS'] = 'MOST DEFINITELY'
        h.node[p3]['EXTRANEOUS'] = 'MOST DEFINITELY'

        h.add_edge(p1, p2, attr_dict={
            RELATION: INCREASES,
            CITATION: {
                CITATION_TYPE: 'PubMed',
                CITATION_REFERENCE: 1,
                CITATION_NAME: 'PMID1'
            },
            EVIDENCE: 'Evidence 1',
            ANNOTATIONS: {}
        })

        h.add_edge(p1, p2, attr_dict={
            RELATION: INCREASES,
            CITATION: {
                CITATION_TYPE: 'PubMed',
                CITATION_REFERENCE: 2,
                CITATION_NAME: 'PMID2'
            },
            EVIDENCE: 'Evidence 2',
            ANNOTATIONS: {}
        })

        h.add_edge(p1, p3, attr_dict={
            RELATION: INCREASES,
            CITATION: {
                CITATION_TYPE: 'PubMed',
                CITATION_REFERENCE: 1,
                CITATION_NAME: 'PMID1'
            },
            EVIDENCE: 'Evidence 3',
            ANNOTATIONS: {}
        })

        self.assertEqual(2, g.number_of_nodes())
        self.assertEqual(1, g.number_of_edges())
        self.assertEqual(3, h.number_of_nodes())
        self.assertEqual(3, h.number_of_edges())

        left_full_join(g, h, use_hash=False)

        self.assertNotIn('EXTRANEOUS', g.node[p1])
        self.assertIn('EXTRANEOUS', g.node[p3])
        self.assertEqual('MOST DEFINITELY', g.node[p3]['EXTRANEOUS'])

        self.assertEqual(3, g.number_of_nodes())
        self.assertEqual(3, g.number_of_edges(), msg="G edges:\n{}".format(json.dumps(g.edges(data=True), indent=2)))
        self.assertEqual(3, h.number_of_nodes())
        self.assertEqual(3, h.number_of_edges())

    def test_left_outer_join(self):
        g = BELGraph()

        g.add_node(1)
        g.add_node(2)
        g.add_edge(1, 2)

        self.assertEqual(2, g.number_of_nodes())
        self.assertEqual(1, g.number_of_edges())

        h = BELGraph()
        h.add_node(1)
        h.add_node(3)
        h.add_node(4)
        h.add_edge(1, 3)
        h.add_edge(1, 4)

        h.add_node(5)
        h.add_node(6)
        h.add_edge(5, 6)

        h.add_node(7)

        self.assertEqual(6, h.number_of_nodes())
        self.assertEqual({1, 3, 4, 5, 6, 7}, set(h.nodes_iter()))
        self.assertEqual(3, h.number_of_edges())
        self.assertEqual({(1, 3), (1, 4), (5, 6)}, set(h.edges_iter()))

        left_outer_join(g, h)

        self.assertEqual(4, g.number_of_nodes())
        self.assertEqual({1, 2, 3, 4}, set(g.nodes_iter()))
        self.assertEqual(3, g.number_of_edges())
        self.assertEqual({(1, 2), (1, 3), (1, 4)}, set(g.edges_iter()))

        self.assertEqual(6, h.number_of_nodes())
        self.assertEqual({1, 3, 4, 5, 6, 7}, set(h.nodes_iter()))
        self.assertEqual(3, h.number_of_edges())
        self.assertEqual({(1, 3), (1, 4), (5, 6)}, set(h.edges_iter()))


if __name__ == '__main__':
    unittest.main()
