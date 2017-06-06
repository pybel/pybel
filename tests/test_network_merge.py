# -*- coding: utf-8 -*-

import unittest

from pybel import BELGraph
from pybel.constants import *
from pybel.graph import left_full_merge

HGNC = 'HGNC'


class TestMerge(unittest.TestCase):
    """Tests various graph merging procedures"""

    def test_left_full_merge(self):
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

        left_full_merge(g, h)

        self.assertNotIn('EXTRANEOUS', g.node[p1])
        self.assertIn('EXTRANEOUS', g.node[p3])
        self.assertEqual('MOST DEFINITELY', g.node[p3]['EXTRANEOUS'])

        self.assertEqual(3, g.number_of_nodes())
        self.assertEqual(3, g.number_of_edges(), msg="G edges:\n{}".format(json.dumps(g.edges(data=True), indent=2)))
        self.assertEqual(3, h.number_of_nodes())
        self.assertEqual(3, h.number_of_edges())
