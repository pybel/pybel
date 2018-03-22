# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import logging
import os
import unittest

from pybel import from_cbn_jgif, to_jgif
from pybel.constants import (
    ACTIVITY, ANNOTATIONS, BEL_DEFAULT_NAMESPACE, CITATION, CITATION_REFERENCE, CITATION_TYPE,
    CITATION_TYPE_OTHER, CITATION_TYPE_PUBMED, DECREASES, DIRECTLY_INCREASES, EFFECT, EVIDENCE, MODIFIER, NAME,
    NAMESPACE, OBJECT, RELATION,
)
from pybel.dsl import abundance, bioprocess, complex_abundance, named_complex_abundance, pathology, pmod, protein
from tests.constants import any_subdict_matches, bel_dir_path

test_path = os.path.join(bel_dir_path, 'Cytotoxic T-cell Signaling-2.0-Hs.json')

logging.getLogger('pybel.parser').setLevel(20)

calcium = abundance(namespace='SCHEM', name='Calcium')
calcineurin_complex = named_complex_abundance(namespace='SCOMP', name='Calcineurin Complex')
foxo3 = protein(namespace='HGNC', name='FOXO3')
tcell_proliferation = bioprocess(namespace='GOBP', name='CD8-positive, alpha-beta T cell proliferation')
il15 = protein(namespace='HGNC', name='IL15')
il2rg = protein(namespace='MGI', name='Il2rg')

jgif_expected_nodes = [
    calcium,
    calcineurin_complex,
    foxo3,
    tcell_proliferation,
    il15,
    il2rg,
    protein(namespace='HGNC', name='CXCR6'),
    protein(namespace='HGNC', name='IL15RA'),
    bioprocess(namespace='GOBP', name='lymphocyte chemotaxis'),
    protein(namespace='HGNC', name='IL2RG'),
    protein(namespace='HGNC', name='ZAP70'),
    named_complex_abundance(namespace='SCOMP', name='T Cell Receptor Complex'),
    bioprocess(namespace='GOBP', name='T cell activation'),
    protein(namespace='HGNC', name='CCL3'),
    protein(namespace='HGNC', name='PLCG1'),
    protein(namespace='HGNC', name='FASLG'),
    protein(namespace='HGNC', name='IDO1'),
    protein(namespace='HGNC', name='IL2'),
    protein(namespace='HGNC', name='CD8A'),
    protein(namespace='HGNC', name='CD8B'),
    protein(namespace='HGNC', name='BCL2'),
    protein(namespace='HGNC', name='CCR3'),
    protein(namespace='HGNC', name='IL2RB'),
    protein(namespace='HGNC', name='CD28'),
    pathology(namespace='SDIS', name='Cytotoxic T-cell activation'),
    protein(namespace='HGNC', name='FYN'),
    protein(namespace='HGNC', name='CXCL16'),
    protein(namespace='HGNC', name='CCR5'),
    protein(namespace='HGNC', name='LCK'),
    protein(namespace='SFAM', name='Chemokine Receptor Family'),
    protein(namespace='HGNC', name='CXCL9'),
    pathology(namespace='SDIS', name='T-cell migration'),
    protein(namespace='HGNC', name='CXCR3'),
    abundance(namespace='CHEBI', name='acrolein'),
    protein(namespace='HGNC', name='IDO2'),
    pathology(namespace='MESHD', name='Pulmonary Disease, Chronic Obstructive'),
    protein(namespace='HGNC', name='IFNG'),
    protein(namespace='HGNC', name='TNFRSF4'),
    protein(namespace='HGNC', name='CTLA4'),
    protein(namespace='HGNC', name='GZMA'),
    protein(namespace='HGNC', name='PRF1'),
    protein(namespace='HGNC', name='TNF'),
    complex_abundance(members=[protein(namespace='HGNC', name='CD8A'), protein(namespace='HGNC', name='CD8B')]),
    protein(namespace='HGNC', name='PLCG1', variants=[pmod(name='Ph', code='Tyr')]),
    protein(namespace='EGID', name='21577'),
]

jgif_expected_edges = [
    (calcium, calcineurin_complex, {
        RELATION: DIRECTLY_INCREASES,
        EVIDENCE: 'NMDA-mediated influx of calcium led to activated of the calcium-dependent phosphatase calcineurin '
                  'and the subsequent dephosphorylation and activation of the protein-tyrosine phosphatase STEP',
        CITATION: {
            CITATION_TYPE: CITATION_TYPE_PUBMED,
            CITATION_REFERENCE: '12483215'
        },
        OBJECT: {
            MODIFIER: ACTIVITY,
            EFFECT: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'phos'}
        },
        ANNOTATIONS: {
            'Species': {'10116': True},
            'Cell': {'neuron': True}
        }
    }),
    (foxo3, tcell_proliferation, {
        RELATION: DECREASES,
        EVIDENCE: "\"These data suggested that FOXO3 downregulates the accumulation of CD8 T cells in tissue specific "
                  "fashion during an acute LCMV [lymphocytic choriomeningitis virus] infection.\" (p. 3)",
        CITATION: {
            CITATION_TYPE: CITATION_TYPE_OTHER,
            CITATION_REFERENCE: "22359505"
        },
        ANNOTATIONS: {
            'Species': {'10090': True},
            'Disease': {'Viral infection': True}
        }
    }),
    (il15, il2rg, {
        RELATION: DIRECTLY_INCREASES,
        EVIDENCE: "IL-15 utilizes ... the common cytokine receptor γ-chain (CD132) for signal transduction in "
                  "lymphocytes",
        CITATION: {
            CITATION_TYPE: CITATION_TYPE_OTHER,
            CITATION_REFERENCE: "20335267"
        },
        OBJECT: {
            MODIFIER: ACTIVITY,
            EFFECT: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'cat'}
        },
        ANNOTATIONS: {
            'Tissue': {'lung': True}
        }
    })
]


class TestCbnJgif(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """loads the data once to be shared by other test methods"""
        with open(test_path) as file:
            cls.graph_jgif_dict = json.load(file)

        cls.graph = from_cbn_jgif(cls.graph_jgif_dict)

    def test_no_duplicate_expected_nodes(self):
        self.assertEqual(sorted(set(map(str, jgif_expected_nodes))), sorted(map(str, jgif_expected_nodes)))

    def test_count_nodes(self):
        self.assertEqual(len(jgif_expected_nodes), self.graph.number_of_nodes(), msg='wrong number of nodes')

    def test_nodes(self):
        """Tests the nodes are loaded properly"""
        self.assertEqual({n.as_tuple() for n in jgif_expected_nodes}, set(self.graph), msg='wrong nodes')

    def test_calcium_downstream(self):
        """Checks that there is exactly one downstream effectors of calcium in the graph"""
        downstream = self.graph[calcium.as_tuple()]
        self.assertEqual(1, len(downstream))

    def assert_has_edge(self, graph, u, v, d):
        """A helper function for checking if an edge with the given properties is contained within a graph

        :param pybel.BELGraph graph: underlying graph
        :param tuple u: source node
        :param tuple v: target node
        :param dict d: pybel data dictionary
        """
        self.assertIn(v, graph[u], msg='Edge ({}, {}) not in graph'.format(u, v))

        # FIXME should be able to test hashed edge key
        # self.assertIn(hash_edge(u, v, d), graph[u][v])

        matches = any_subdict_matches(graph[u][v], d)

        msg = 'No edge ({}, {}) with correct properties. expected:\n {}\nbut got:\n{}'.format(
            u,
            v,
            json.dumps(d, indent=2, sort_keys=True),
            json.dumps(dict(graph[u][v]), indent=2, sort_keys=True)
        )
        self.assertTrue(matches, msg=msg)

    def test_edges(self):
        """Tests the edges are loaded properly"""
        for u, v, d in jgif_expected_edges:
            self.assert_has_edge(self.graph, u.as_tuple(), v.as_tuple(), d)

    @unittest.skip(reason='JGIF can not handle multiple annotations')
    def test_jgif_interchange(self):
        """Tests a graph can be serialized to JGIF properly"""
        export_jgif = to_jgif(self.graph)
        self.assertIsInstance(export_jgif, dict)
        self.assertEqual(self.graph_jgif_dict, export_jgif)


if __name__ == '__main__':
    unittest.main()
