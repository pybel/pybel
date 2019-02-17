# -*- coding: utf-8 -*-

"""Tests for interchange with JGIF."""

from __future__ import unicode_literals

import json
import logging
import sys
import unittest

from pybel import from_cbn_jgif, to_jgif
from pybel.constants import (
    ACTIVITY, ANNOTATIONS, BEL_DEFAULT_NAMESPACE, CITATION, CITATION_REFERENCE, CITATION_TYPE, CITATION_TYPE_OTHER,
    CITATION_TYPE_PUBMED, DECREASES, DIRECTLY_INCREASES, EFFECT, EVIDENCE, MODIFIER, NAME, NAMESPACE, OBJECT, RELATION,
)
from pybel.dsl import Abundance, BiologicalProcess, ComplexAbundance, NamedComplexAbundance, Pathology, Protein, pmod
from pybel.testing.constants import test_jgif_path
from tests.constants import TestGraphMixin

logging.getLogger('pybel.parser').setLevel(20)

calcium = Abundance('SCHEM', 'Calcium')
calcineurin_complex = NamedComplexAbundance('SCOMP', 'Calcineurin Complex')
foxo3 = Protein('HGNC', 'FOXO3')
tcell_proliferation = BiologicalProcess('GO', 'CD8-positive, alpha-beta T cell proliferation')
il15 = Protein('HGNC', 'IL15')
il2rg = Protein('MGI', 'Il2rg')
jgif_expected_nodes = {
    calcium,
    calcineurin_complex,
    foxo3,
    tcell_proliferation,
    il15,
    il2rg,
    Protein('HGNC', 'CXCR6'),
    Protein('HGNC', 'IL15RA'),
    BiologicalProcess('GO', 'lymphocyte chemotaxis'),
    Protein('HGNC', 'IL2RG'),
    Protein('HGNC', 'ZAP70'),
    NamedComplexAbundance('SCOMP', 'T Cell Receptor Complex'),
    BiologicalProcess('GO', 'T cell activation'),
    Protein('HGNC', 'CCL3'),
    Protein('HGNC', 'PLCG1'),
    Protein('HGNC', 'FASLG'),
    Protein('HGNC', 'IDO1'),
    Protein('HGNC', 'IL2'),
    Protein('HGNC', 'CD8A'),
    Protein('HGNC', 'CD8B'),
    Protein('HGNC', 'PLCG1'),
    Protein('HGNC', 'BCL2'),
    Protein('HGNC', 'CCR3'),
    Protein('HGNC', 'IL2RB'),
    Protein('HGNC', 'CD28'),
    Pathology('SDIS', 'Cytotoxic T-cell activation'),
    Protein('HGNC', 'FYN'),
    Protein('HGNC', 'CXCL16'),
    Protein('HGNC', 'CCR5'),
    Protein('HGNC', 'LCK'),
    Protein('SFAM', 'Chemokine Receptor Family'),
    Protein('HGNC', 'CXCL9'),
    Pathology('SDIS', 'T-cell migration'),
    Protein('HGNC', 'CXCR3'),
    Abundance('CHEBI', 'acrolein'),
    Protein('HGNC', 'IDO2'),
    Pathology('MESHD', 'Pulmonary Disease, Chronic Obstructive'),
    Protein('HGNC', 'IFNG'),
    Protein('HGNC', 'TNFRSF4'),
    Protein('HGNC', 'CTLA4'),
    Protein('HGNC', 'GZMA'),
    Protein('HGNC', 'PRF1'),
    Protein('HGNC', 'TNF'),
    Protein('SFAM', 'Chemokine Receptor Family'),
    ComplexAbundance([Protein('HGNC', 'CD8A'), Protein('HGNC', 'CD8B')]),
    ComplexAbundance([Protein('HGNC', 'CD8A'), Protein('HGNC', 'CD8B')]),
    Protein('HGNC', 'PLCG1', variants=pmod('Ph', 'Tyr')),
    Protein('EGID', '21577'),
}

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

    @unittest.skipIf(sys.platform.startswith("win"), "does not work on Windows")
    def test_jgif_interchange(self):
        """Tests data from CBN"""
        with open(test_jgif_path) as f:
            graph_jgif_dict = json.load(f)

        graph = from_cbn_jgif(graph_jgif_dict)

        self.assertEqual(jgif_expected_nodes, set(graph))

        for u, v, d in jgif_expected_edges:
            self.assert_has_edge(graph, u, v, **d)

        # TODO test more thoroughly?
        export_jgif = to_jgif(graph)
        self.assertIsInstance(export_jgif, dict)
