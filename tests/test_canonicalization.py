# -*- coding: utf-8 -*-

"""Tests for canonicalization functions."""

import unittest
from typing import Iterable

from pybel import BELGraph
from pybel.canonicalize import _to_bel_lines_body, postpend_location
from pybel.constants import BEL_DEFAULT_NAMESPACE, EXTRACELLULAR, INTRACELLULAR, MODIFIER
from pybel.dsl import (
    Abundance, BiologicalProcess, ComplexAbundance, CompositeAbundance, EnumeratedFusionRange, Fragment, Gene,
    GeneFusion, GeneModification, Hgvs, MicroRna, NamedComplexAbundance, Pathology, Protein, ProteinModification,
    ProteinSubstitution, Reaction, Rna, RnaFusion, activity, degradation, secretion, translocation,
)
from pybel.language import Entity
from pybel.testing.utils import n
from pybel.utils import canonicalize_edge


class TestCanonicalize(unittest.TestCase):
    def test_postpend_location_failure(self):
        with self.assertRaises(ValueError):
            postpend_location('', dict(name='failure'))

    def test_canonicalize_variant_dsl(self):
        """Use the __str__ functions in the DSL to create BEL instead of external pybel.canonicalize."""
        self.assertEqual('var("p.Val600Glu")', str(Hgvs('p.Val600Glu')))
        self.assertEqual('var("p.Val600Glu")', str(ProteinSubstitution('Val', 600, 'Glu')))

        self.assertEqual('pmod(Ph)', str(ProteinModification('Ph')))
        self.assertEqual('pmod(TEST:Ph)', str(ProteinModification('Ph', namespace='TEST')))
        self.assertEqual('pmod(TEST:Ph, Ser)', str(ProteinModification('Ph', namespace='TEST', code='Ser')))
        self.assertEqual('pmod(TEST:Ph, Ser, 5)',
                         str(ProteinModification('Ph', namespace='TEST', code='Ser', position=5)))
        self.assertEqual('pmod(GO:"protein phosphorylation", Thr, 308)',
                         str(ProteinModification(name='protein phosphorylation', namespace='GO', code='Thr',
                                                 position=308)))

        self.assertEqual('frag("?")', str(Fragment()))
        self.assertEqual('frag("672_713")', str(Fragment(start=672, stop=713)))
        self.assertEqual('frag("?", "descr")', str(Fragment(description='descr')))
        self.assertEqual('frag("672_713", "descr")', str(Fragment(start=672, stop=713, description='descr')))

        self.assertEqual('gmod(Me)', str(GeneModification('Me')))
        self.assertEqual('gmod(TEST:Me)', str(GeneModification('Me', namespace='TEST')))
        self.assertEqual('gmod(GO:"DNA Methylation")', str(GeneModification('DNA Methylation', namespace='GO')))

    def test_canonicalize_fusion_range_dsl(self):
        """Test canonicalization of enumerated fusion ranges."""
        self.assertEqual('p.1_15', str(EnumeratedFusionRange('p', 1, 15)))
        self.assertEqual('p.*_15', str(EnumeratedFusionRange('p', '*', 15)))

    def test_Abundance(self):
        """Test canonicalization of abundances."""
        short = Abundance(namespace='CHEBI', name='water')
        self.assertEqual('a(CHEBI:water)', str(short))

        long = Abundance(namespace='CHEBI', name='test name')
        self.assertEqual('a(CHEBI:"test name")', str(long))

    def test_protein_reference(self):
        self.assertEqual('p(HGNC:AKT1)', str(Protein(namespace='HGNC', name='AKT1')))

    def test_gene_reference(self):
        node = Gene(namespace='EGID', name='780')
        self.assertEqual('g(EGID:780)', str(node))

    def test_protein_pmod(self):
        node = Protein(name='PLCG1', namespace='HGNC', variants=[ProteinModification(name='Ph', code='Tyr')])
        self.assertEqual('p(HGNC:PLCG1, pmod(Ph, Tyr))', str(node))

    def test_protein_fragment(self):
        node = Protein(name='APP', namespace='HGNC', variants=[Fragment(start=672, stop=713)])

        self.assertEqual('p(HGNC:APP, frag("672_713"))', str(node))

    def test_mirna_reference(self):
        self.assertEqual('m(HGNC:MIR1)', str(MicroRna(namespace='HGNC', name='MIR1')))

    def test_rna_fusion_specified(self):
        node = RnaFusion(
            partner_5p=Rna(namespace='HGNC', name='TMPRSS2'),
            range_5p=EnumeratedFusionRange('r', 1, 79),
            partner_3p=Rna(namespace='HGNC', name='ERG'),
            range_3p=EnumeratedFusionRange('r', 312, 5034)
        )
        self.assertEqual('r(fus(HGNC:TMPRSS2, "r.1_79", HGNC:ERG, "r.312_5034"))', str(node))

    def test_rna_fusion_unspecified(self):
        node = RnaFusion(
            partner_5p=Rna(namespace='HGNC', name='TMPRSS2'),
            partner_3p=Rna(namespace='HGNC', name='ERG'),
        )
        self.assertEqual('r(fus(HGNC:TMPRSS2, "?", HGNC:ERG, "?"))', str(node))

    def test_gene_fusion_specified(self):
        node = GeneFusion(
            partner_5p=Gene(namespace='HGNC', name='TMPRSS2'),
            range_5p=EnumeratedFusionRange('c', 1, 79),
            partner_3p=Gene(namespace='HGNC', name='ERG'),
            range_3p=EnumeratedFusionRange('c', 312, 5034)
        )

        self.assertEqual('g(fus(HGNC:TMPRSS2, "c.1_79", HGNC:ERG, "c.312_5034"))', str(node))

    def test_pathology(self):
        node = Pathology(namespace='DO', name='Alzheimer disease')
        self.assertEqual('path(DO:"Alzheimer disease")', str(node))

    def test_bioprocess(self):
        node = BiologicalProcess(namespace='GO', name='apoptosis')
        self.assertEqual('bp(GO:apoptosis)', str(node))

    def test_named_complex_abundance(self):
        node = NamedComplexAbundance(namespace='SCOMP', name='Calcineurin Complex')

        self.assertEqual('complex(SCOMP:"Calcineurin Complex")', str(node))

    def test_complex_abundance(self):
        node = ComplexAbundance(members=[Protein(namespace='HGNC', name='FOS'), Protein(namespace='HGNC', name='JUN')])
        self.assertEqual('complex(p(HGNC:FOS), p(HGNC:JUN))', str(node))

    def test_composite_abundance(self):
        node = CompositeAbundance(members=[
            Protein(namespace='HGNC', name='FOS'),
            Protein(namespace='HGNC', name='JUN')
        ])
        self.assertEqual('composite(p(HGNC:FOS), p(HGNC:JUN))', str(node))

    def test_reaction(self):
        node = Reaction(
            reactants=[Abundance(namespace='CHEBI', name='A')],
            products=[Abundance(namespace='CHEBI', name='B')]
        )
        self.assertEqual('rxn(reactants(a(CHEBI:A)), products(a(CHEBI:B)))', str(node))


class TestCanonicalizeEdge(unittest.TestCase):
    """This class houses all testing for the canonicalization of edges such that the relation/modifications can be used
    as a second level hash"""

    def setUp(self):
        self.g = BELGraph()
        self.u = Protein(name='u', namespace='TEST')
        self.v = Protein(name='v', namespace='TEST')
        self.g.add_node_from_data(self.u)
        self.g.add_node_from_data(self.v)

    def get_data(self, k):
        return self.g[self.u][self.v][k]

    def add_edge(self, subject_modifier=None, object_modifier=None, annotations=None):
        key = self.g.add_increases(
            self.u,
            self.v,
            evidence=n(),
            citation=n(),
            subject_modifier=subject_modifier,
            object_modifier=object_modifier,
            annotations=annotations,
        )

        return canonicalize_edge(self.get_data(key))

    def test_failure(self):
        with self.assertRaises(ValueError):
            self.add_edge(subject_modifier={MODIFIER: 'nope'})

    def test_canonicalize_edge_info(self):
        c1 = self.add_edge(
            annotations={
                'Species': '9606'
            }
        )

        c2 = self.add_edge(
            annotations={
                'Species': '9606'
            }
        )

        c3 = self.add_edge(
            subject_modifier=activity('tport'),
        )

        c4 = self.add_edge(
            subject_modifier=activity('tport', namespace=BEL_DEFAULT_NAMESPACE),
        )

        self.assertEqual(c1, c2)
        self.assertNotEqual(c1, c3)
        self.assertEqual(c3, c4)

    def test_subject_degradation_location(self):
        self.assertEqual(
            self.add_edge(
                subject_modifier=degradation()
            ),
            self.add_edge(
                subject_modifier=degradation()
            )
        )

        self.assertEqual(
            self.add_edge(
                subject_modifier=degradation(location=Entity(name='somewhere', namespace='GO'))
            ),
            self.add_edge(
                subject_modifier=degradation(location=Entity(name='somewhere', namespace='GO'))
            )
        )

        self.assertNotEqual(
            self.add_edge(
                subject_modifier=degradation()
            ),
            self.add_edge(
                subject_modifier=degradation(location=Entity(name='somewhere', namespace='GO'))
            )
        )

    def test_translocation(self):
        self.assertEqual(
            self.add_edge(subject_modifier=secretion()),
            self.add_edge(subject_modifier=secretion()),
        )

        self.assertEqual(
            self.add_edge(subject_modifier=secretion()),
            self.add_edge(subject_modifier=translocation(INTRACELLULAR, EXTRACELLULAR)),
        )


class TestSerializeBEL(unittest.TestCase):
    def setUp(self):
        self.citation = n()
        self.evidence = n()
        self.url = n()
        self.graph = BELGraph()
        self.graph.namespace_url['HGNC'] = self.url

    def _help_check_lines(self, lines: Iterable[str]):
        """Check the given lines match the graph built during the tests."""
        self.assertEqual(lines, list(_to_bel_lines_body(self.graph)))

    def test_simple(self):
        """Tests a scenario with a qualified edge, but no annotaitons"""
        self.graph.add_increases(
            Protein(namespace='HGNC', name='YFG1'),
            Protein(namespace='HGNC', name='YFG'),
            citation=self.citation,
            evidence=self.evidence
        )

        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertEqual(1, self.graph.number_of_edges())

        expected_lines = [
            'SET Citation = {{"PubMed", "{}"}}\n'.format(self.citation),
            'SET SupportingText = "{}"'.format(self.evidence),
            'p(HGNC:YFG1) increases p(HGNC:YFG)',
            'UNSET SupportingText',
            'UNSET Citation\n',
            '#' * 80,
        ]

        self._help_check_lines(expected_lines)

    def test_single_annotation(self):
        """Tests a scenario with a qualified edge, but no annotaitons"""
        a1, v1 = map(lambda _: n(), range(2))

        self.graph.add_increases(
            Protein(namespace='HGNC', name='YFG1'),
            Protein(namespace='HGNC', name='YFG'),
            citation=self.citation,
            evidence=self.evidence,
            annotations={
                a1: {v1}
            }
        )

        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertEqual(1, self.graph.number_of_edges())

        expected_lines = [
            'SET Citation = {{"PubMed", "{}"}}\n'.format(self.citation),
            'SET SupportingText = "{}"'.format(self.evidence),
            'SET {} = "{}"'.format(a1, v1),
            'p(HGNC:YFG1) increases p(HGNC:YFG)',
            'UNSET {}'.format(a1),
            'UNSET SupportingText',
            'UNSET Citation\n',
            '#' * 80,
        ]

        self._help_check_lines(expected_lines)

    def test_multiple_annotations(self):
        a1, v1, v2 = map(lambda _: n(), range(3))
        v1, v2 = sorted([v1, v2])

        self.graph.add_increases(
            Protein(namespace='HGNC', name='YFG1'),
            Protein(namespace='HGNC', name='YFG'),
            citation=self.citation,
            evidence=self.evidence,
            annotations={
                a1: {v1, v2}
            }
        )

        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertEqual(1, self.graph.number_of_edges())

        expected_lines = [
            'SET Citation = {{"PubMed", "{}"}}\n'.format(self.citation),
            'SET SupportingText = "{}"'.format(self.evidence),
            'SET {} = {{"{}", "{}"}}'.format(a1, v1, v2),
            'p(HGNC:YFG1) increases p(HGNC:YFG)',
            'UNSET {}'.format(a1),
            'UNSET SupportingText',
            'UNSET Citation\n',
            ('#' * 80),
        ]

        self._help_check_lines(expected_lines)
