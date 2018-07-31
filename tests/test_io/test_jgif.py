# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import logging
import unittest

from pybel import from_cbn_jgif, to_jgif
from pybel.constants import (
    ABUNDANCE, ACTIVITY, ANNOTATIONS, BEL_DEFAULT_NAMESPACE, BIOPROCESS, CITATION, CITATION_REFERENCE, CITATION_TYPE,
    CITATION_TYPE_OTHER, CITATION_TYPE_PUBMED, COMPLEX, DECREASES, DIRECTLY_INCREASES, EFFECT, EVIDENCE, MODIFIER, NAME,
    NAMESPACE, OBJECT, PATHOLOGY, PMOD, PROTEIN, RELATION,
)
from pybel.testing.constants import test_jgif_path
from tests.constants import TestGraphMixin

logging.getLogger('pybel.parser').setLevel(20)

calcium = (ABUNDANCE, 'SCHEM', 'Calcium')
calcineurin_complex = (COMPLEX, 'SCOMP', 'Calcineurin Complex')
foxo3 = (PROTEIN, 'HGNC', 'FOXO3')
tcell_proliferation = (BIOPROCESS, 'GOBP', 'CD8-positive, alpha-beta T cell proliferation')
il15 = (PROTEIN, 'HGNC', 'IL15')
il2rg = (PROTEIN, 'MGI', 'Il2rg')
jgif_expected_nodes = [
    calcium,
    calcineurin_complex,
    foxo3,
    tcell_proliferation,
    il15,
    il2rg,
    (PROTEIN, 'HGNC', 'CXCR6'),
    (PROTEIN, 'HGNC', 'IL15RA'),
    (BIOPROCESS, 'GOBP', 'lymphocyte chemotaxis'),
    (PROTEIN, 'HGNC', 'IL2RG'),
    (PROTEIN, 'HGNC', 'ZAP70'),
    (COMPLEX, 'SCOMP', 'T Cell Receptor Complex'),
    (BIOPROCESS, 'GOBP', 'T cell activation'),
    (PROTEIN, 'HGNC', 'CCL3'),
    (PROTEIN, 'HGNC', 'PLCG1'),
    (PROTEIN, 'HGNC', 'FASLG'),
    (PROTEIN, 'HGNC', 'IDO1'),
    (PROTEIN, 'HGNC', 'IL2'),
    (PROTEIN, 'HGNC', 'CD8A'),
    (PROTEIN, 'HGNC', 'CD8B'),
    (PROTEIN, 'HGNC', 'PLCG1'),
    (PROTEIN, 'HGNC', 'BCL2'),
    (PROTEIN, 'HGNC', 'CCR3'),
    (PROTEIN, 'HGNC', 'IL2RB'),
    (PROTEIN, 'HGNC', 'CD28'),
    (PATHOLOGY, 'SDIS', 'Cytotoxic T-cell activation'),
    (PROTEIN, 'HGNC', 'FYN'),
    (PROTEIN, 'HGNC', 'CXCL16'),
    (PROTEIN, 'HGNC', 'CCR5'),
    (PROTEIN, 'HGNC', 'LCK'),
    (PROTEIN, 'SFAM', 'Chemokine Receptor Family'),
    (PROTEIN, 'HGNC', 'CXCL9'),
    (PATHOLOGY, 'SDIS', 'T-cell migration'),
    (PROTEIN, 'HGNC', 'CXCR3'),
    (ABUNDANCE, 'CHEBI', 'acrolein'),
    (PROTEIN, 'HGNC', 'IDO2'),
    (PATHOLOGY, 'MESHD', 'Pulmonary Disease, Chronic Obstructive'),
    (PROTEIN, 'HGNC', 'IFNG'),
    (PROTEIN, 'HGNC', 'TNFRSF4'),
    (PROTEIN, 'HGNC', 'CTLA4'),
    (PROTEIN, 'HGNC', 'GZMA'),
    (PROTEIN, 'HGNC', 'PRF1'),
    (PROTEIN, 'HGNC', 'TNF'),
    (PROTEIN, 'SFAM', 'Chemokine Receptor Family'),
    (COMPLEX, (PROTEIN, 'HGNC', 'CD8A'), (PROTEIN, 'HGNC', 'CD8B')),
    (COMPLEX, (PROTEIN, 'HGNC', 'CD8A'), (PROTEIN, 'HGNC', 'CD8B')),
    (PROTEIN, 'HGNC', 'PLCG1', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Tyr')),
    (PROTEIN, 'EGID', '21577'),
]

jgif_expected_edges = [
    (calcium, calcineurin_complex, {
        RELATION: DIRECTLY_INCREASES,
        EVIDENCE: 'NMDA-mediated influx of calcium led to activated of the calcium-dependent phosphatase calcineurin and the subsequent dephosphorylation and activation of the protein-tyrosine phosphatase STEP',
        CITATION: {
            CITATION_TYPE: CITATION_TYPE_PUBMED,
            CITATION_REFERENCE: '12483215'
        },
        OBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'phos'}},
        ANNOTATIONS: {
            'Species': {'10116': True},
            'Cell': {'neuron': True}
        }
    }),
    (foxo3, tcell_proliferation, {
        RELATION: DECREASES,
        EVIDENCE: "\"These data suggested that FOXO3 downregulates the accumulation of CD8 T cells in tissue specific fashion during an acute LCMV [lymphocytic choriomeningitis virus] infection.\" (p. 3)",
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
        EVIDENCE: "IL-15 utilizes ... the common cytokine receptor γ-chain (CD132) for signal transduction in lymphocytes",
        CITATION: {
            CITATION_TYPE: CITATION_TYPE_OTHER,
            CITATION_REFERENCE: "20335267"
        },
        OBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'cat'}},
        ANNOTATIONS: {
            'Tissue': {'lung': True}
        }
    })
]


class TestJgif(TestGraphMixin):
    """Tests data interchange of """

    def test_jgif_interchange(self):
        """Tests data from CBN"""
        with open(test_jgif_path) as f:
            graph_jgif_dict = json.load(f)

        graph = from_cbn_jgif(graph_jgif_dict)

        self.assertEqual(set(jgif_expected_nodes), set(graph))

        for u, v, d in jgif_expected_edges:
            self.assert_has_edge(graph, u, v, **d)

        # TODO test more thoroughly?
        export_jgif = to_jgif(graph)
        self.assertIsInstance(export_jgif, dict)


if __name__ == '__main__':
    unittest.main()
