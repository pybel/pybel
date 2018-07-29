# -*- coding: utf-8 -*-

import unittest

from pybel import BELGraph
from pybel.canonicalize import _to_bel_lines_body, canonicalize_edge, fusion_range_to_bel, variant_to_bel
from pybel.constants import (
    ABUNDANCE, BEL_DEFAULT_NAMESPACE, BIOPROCESS, COMPLEX, COMPOSITE, FRAGMENT, GENE, KIND, MODIFIER,
    PATHOLOGY, PMOD, PROTEIN, REACTION, RNA,
)
from pybel.dsl import (
    abundance, activity, bioprocess, complex_abundance, composite_abundance, degradation, entity, extracellular,
    fragment, fusion_range, gene, gene_fusion, gmod, hgvs, intracellular, mirna, named_complex_abundance, pathology,
    pmod, protein, protein_substitution, reaction, rna, rna_fusion, secretion, translocation,
)
from pybel.testing.utils import n


class TestCanonicalize(unittest.TestCase):
    def test_variant_to_bel_key_error(self):
        with self.assertRaises(Exception):
            variant_to_bel({})

    def test_variant_to_bel_value_error(self):
        with self.assertRaises(ValueError):
            variant_to_bel({KIND: 'nope'})

    def test_canonicalize_variant(self):
        self.assertEqual('var(p.Val600Glu)', variant_to_bel(hgvs('p.Val600Glu')))
        self.assertEqual('var(p.Val600Glu)', variant_to_bel(protein_substitution('Val', 600, 'Glu')))

        self.assertEqual('pmod(Ph)', variant_to_bel(pmod('Ph')))
        self.assertEqual('pmod(TEST:Ph)', variant_to_bel(pmod('Ph', namespace='TEST')))
        self.assertEqual('pmod(TEST:Ph, Ser)', variant_to_bel(pmod('Ph', namespace='TEST', code='Ser')))
        self.assertEqual('pmod(TEST:Ph, Ser, 5)', variant_to_bel(pmod('Ph', namespace='TEST', code='Ser', position=5)))
        self.assertEqual('pmod(GO:"protein phosphorylation", Thr, 308)',
                         variant_to_bel(pmod(name='protein phosphorylation', namespace='GO', code='Thr', position=308)))

        self.assertEqual('frag(?)', variant_to_bel(fragment()))
        self.assertEqual('frag(672_713)', variant_to_bel(fragment(start=672, stop=713)))
        self.assertEqual('frag(?, "descr")', variant_to_bel(fragment(description='descr')))
        self.assertEqual('frag(672_713, "descr")', variant_to_bel(fragment(start=672, stop=713, description='descr')))

        self.assertEqual('gmod(Me)', variant_to_bel(gmod('Me')))
        self.assertEqual('gmod(TEST:Me)', variant_to_bel(gmod('Me', namespace='TEST')))
        self.assertEqual('gmod(GO:"DNA Methylation")', variant_to_bel(gmod('DNA Methylation', namespace='GO')))

    def test_canonicalize_variant_dsl(self):
        """Uses the __str__ functions in the DSL to create BEL instead of external pybel.canonicalize"""
        self.assertEqual('var(p.Val600Glu)', str(hgvs('p.Val600Glu')))
        self.assertEqual('var(p.Val600Glu)', str(protein_substitution('Val', 600, 'Glu')))

        self.assertEqual('pmod(Ph)', str(pmod('Ph')))
        self.assertEqual('pmod(TEST:Ph)', str(pmod('Ph', namespace='TEST')))
        self.assertEqual('pmod(TEST:Ph, Ser)', str(pmod('Ph', namespace='TEST', code='Ser')))
        self.assertEqual('pmod(TEST:Ph, Ser, 5)', str(pmod('Ph', namespace='TEST', code='Ser', position=5)))
        self.assertEqual('pmod(GO:"protein phosphorylation", Thr, 308)',
                         str(pmod(name='protein phosphorylation', namespace='GO', code='Thr', position=308)))

        self.assertEqual('frag(?)', str(fragment()))
        self.assertEqual('frag(672_713)', str(fragment(start=672, stop=713)))
        self.assertEqual('frag(?, "descr")', str(fragment(description='descr')))
        self.assertEqual('frag(672_713, "descr")', str(fragment(start=672, stop=713, description='descr')))

        self.assertEqual('gmod(Me)', str(gmod('Me')))
        self.assertEqual('gmod(TEST:Me)', str(gmod('Me', namespace='TEST')))
        self.assertEqual('gmod(GO:"DNA Methylation")', str(gmod('DNA Methylation', namespace='GO')))

    def test_canonicalize_fusion_range(self):
        self.assertEqual('p.1_15', fusion_range_to_bel(fusion_range('p', 1, 15)))
        self.assertEqual('p.*_15', fusion_range_to_bel(fusion_range('p', '*', 15)))

    def test_canonicalize_fusion_range_dsl(self):
        self.assertEqual('p.1_15', str(fusion_range('p', 1, 15)))
        self.assertEqual('p.*_15', str(fusion_range('p', '*', 15)))

    def test_abundance(self):
        short = abundance(namespace='CHEBI', name='water')
        self.assertEqual('a(CHEBI:water)', str(short))
        self.assertEqual((ABUNDANCE, 'CHEBI', 'water'), short.as_tuple())

        long = abundance(namespace='CHEBI', name='test name')
        self.assertEqual('a(CHEBI:"test name")', str(long))
        self.assertEqual((ABUNDANCE, 'CHEBI', 'test name'), long.as_tuple())

    def test_protein_reference(self):
        self.assertEqual('p(HGNC:AKT1)', str(protein(namespace='HGNC', name='AKT1')))

    def test_gene_reference(self):
        node = gene(namespace='EGID', name='780')

        self.assertEqual('g(EGID:780)', str(node))
        self.assertEqual((GENE, 'EGID', '780'), node.as_tuple())

    def test_protein_pmod(self):
        node = protein(name='PLCG1', namespace='HGNC', variants=[pmod(name='Ph', code='Tyr')])
        self.assertEqual('p(HGNC:PLCG1, pmod(Ph, Tyr))', str(node))
        self.assertEqual((PROTEIN, 'HGNC', 'PLCG1', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Tyr')), node.as_tuple())

    def test_protein_fragment(self):
        node = protein(name='APP', namespace='HGNC', variants=[fragment(start=672, stop=713)])

        self.assertEqual('p(HGNC:APP, frag(672_713))', str(node))
        self.assertEqual((PROTEIN, 'HGNC', 'APP', ((FRAGMENT, (672, 713)))), node.as_tuple())

    def test_mirna_reference(self):
        self.assertEqual('m(HGNC:MIR1)', str(mirna(namespace='HGNC', name='MIR1')))

    def test_rna_fusion_specified(self):
        node = rna_fusion(
            partner_5p=rna(namespace='HGNC', name='TMPRSS2'),
            range_5p=fusion_range('r', 1, 79),
            partner_3p=rna(namespace='HGNC', name='ERG'),
            range_3p=fusion_range('r', 312, 5034)
        )
        self.assertEqual('r(fus(HGNC:TMPRSS2, r.1_79, HGNC:ERG, r.312_5034))', str(node))

    def test_rna_fusion_unspecified(self):
        node = rna_fusion(
            partner_5p=rna(namespace='HGNC', name='TMPRSS2'),
            partner_3p=rna(namespace='HGNC', name='ERG'),
        )
        self.assertEqual('r(fus(HGNC:TMPRSS2, ?, HGNC:ERG, ?))', str(node))

        t = RNA, ('HGNC', 'TMPRSS2'), ('?',), ('HGNC', 'ERG'), ('?',)
        self.assertEqual(t, node.as_tuple())

    def test_gene_fusion_specified(self):
        node = gene_fusion(
            partner_5p=gene(namespace='HGNC', name='TMPRSS2'),
            range_5p=fusion_range('c', 1, 79),
            partner_3p=gene(namespace='HGNC', name='ERG'),
            range_3p=fusion_range('c', 312, 5034)
        )

        self.assertEqual('g(fus(HGNC:TMPRSS2, c.1_79, HGNC:ERG, c.312_5034))', str(node))
        t = GENE, ('HGNC', 'TMPRSS2'), ('c', 1, 79), ('HGNC', 'ERG'), ('c', 312, 5034)
        self.assertEqual(t, node.as_tuple())

    def test_pathology(self):
        node = pathology(namespace='DO', name='Alzheimer disease')
        self.assertEqual('path(DO:"Alzheimer disease")', str(node))
        self.assertEqual((PATHOLOGY, 'DO', 'Alzheimer disease'), node.as_tuple())

    def test_bioprocess(self):
        node = bioprocess(namespace='GO', name='apoptosis')
        self.assertEqual('bp(GO:apoptosis)', str(node))
        self.assertEqual((BIOPROCESS, 'GO', 'apoptosis'), node.as_tuple())

    def test_named_complex_abundance(self):
        node = named_complex_abundance(namespace='SCOMP', name='Calcineurin Complex')

        self.assertEqual('complex(SCOMP:"Calcineurin Complex")', str(node))
        self.assertEqual((COMPLEX, 'SCOMP', 'Calcineurin Complex'), node.as_tuple())

    def test_complex_abundance(self):
        node = complex_abundance(members=[protein(namespace='HGNC', name='FOS'), protein(namespace='HGNC', name='JUN')])
        t = COMPLEX, (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')
        self.assertEqual('complex(p(HGNC:FOS), p(HGNC:JUN))', str(node))
        self.assertEqual(t, node.as_tuple())

    def test_composite_abundance(self):
        node = composite_abundance(members=[
            protein(namespace='HGNC', name='FOS'),
            protein(namespace='HGNC', name='JUN')
        ])
        t = COMPOSITE, (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')
        self.assertEqual('composite(p(HGNC:FOS), p(HGNC:JUN))', str(node))
        self.assertEqual(t, node.as_tuple())

    def test_reaction(self):
        node = reaction(
            reactants=[abundance(namespace='CHEBI', name='A')],
            products=[abundance(namespace='CHEBI', name='B')]
        )
        t = REACTION, ((ABUNDANCE, 'CHEBI', 'A'),), ((ABUNDANCE, 'CHEBI', 'B'),)
        self.assertEqual('rxn(reactants(a(CHEBI:A)), products(a(CHEBI:B)))', str(node))
        self.assertEqual(t, node.as_tuple())


class TestCanonicalizeEdge(unittest.TestCase):
    """This class houses all testing for the canonicalization of edges such that the relation/modifications can be used
    as a second level hash"""

    def setUp(self):
        self.g = BELGraph()
        self.u = self.g.add_node_from_data(protein(name='u', namespace='TEST'))
        self.v = self.g.add_node_from_data(protein(name='v', namespace='TEST'))
        self.key = 0

    def get_data(self, k):
        return self.g.edge[self.u][self.v][k]

    def add_edge(self, subject_modifier=None, object_modifier=None, annotations=None):
        self.key += 1

        self.g.add_increases(
            self.u,
            self.v,
            evidence=n(),
            citation=n(),
            subject_modifier=subject_modifier,
            object_modifier=object_modifier,
            annotations=annotations,
            key=self.key
        )

        return canonicalize_edge(self.get_data(self.key))

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
                subject_modifier=degradation(location=entity(name='somewhere', namespace='GOCC'))
            ),
            self.add_edge(
                subject_modifier=degradation(location=entity(name='somewhere', namespace='GOCC'))
            )
        )

        self.assertNotEqual(
            self.add_edge(
                subject_modifier=degradation()
            ),
            self.add_edge(
                subject_modifier=degradation(location=entity(name='somewhere', namespace='GOCC'))
            )
        )

    def test_translocation(self):
        self.assertEqual(
            self.add_edge(subject_modifier=secretion()),
            self.add_edge(subject_modifier=secretion()),
        )

        self.assertEqual(
            self.add_edge(subject_modifier=secretion()),
            self.add_edge(subject_modifier=translocation(from_loc=intracellular, to_loc=extracellular)),
        )


class TestSerializeBEL(unittest.TestCase):
    def setUp(self):
        self.citation = n()
        self.evidence = n()
        self.url = n()
        self.graph = BELGraph()
        self.graph.namespace_url['HGNC'] = self.url

    def help_check_lines(self, lines):
        """Checks the given lines match the graph built during the tests

        :type lines: list[str]
        """
        self.assertEqual(lines, list(_to_bel_lines_body(self.graph)))

    def test_simple(self):
        """Tests a scenario with a qualified edge, but no annotaitons"""
        self.graph.add_increases(
            protein(namespace='HGNC', name='YFG1'),
            protein(namespace='HGNC', name='YFG'),
            citation=self.citation,
            evidence=self.evidence
        )

        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertEqual(1, self.graph.number_of_edges())

        expected_lines = [
            '#' * 80,
            'SET Citation = {{"PubMed", "{}"}}'.format(self.citation),
            'SET SupportingText = "{}"'.format(self.evidence),
            'p(HGNC:YFG1) increases p(HGNC:YFG)',
            'UNSET SupportingText',
            'UNSET Citation'
        ]

        self.help_check_lines(expected_lines)

    def test_single_annotation(self):
        """Tests a scenario with a qualified edge, but no annotaitons"""
        a1, v1 = map(lambda _: n(), range(2))

        self.graph.add_increases(
            protein(namespace='HGNC', name='YFG1'),
            protein(namespace='HGNC', name='YFG'),
            citation=self.citation,
            evidence=self.evidence,
            annotations={
                a1: {v1}
            }
        )

        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertEqual(1, self.graph.number_of_edges())

        expected_lines = [
            '#' * 80,
            'SET Citation = {{"PubMed", "{}"}}'.format(self.citation),
            'SET SupportingText = "{}"'.format(self.evidence),
            'SET {} = "{}"'.format(a1, v1),
            'p(HGNC:YFG1) increases p(HGNC:YFG)',
            'UNSET {}'.format(a1),
            'UNSET SupportingText',
            'UNSET Citation'
        ]

        self.help_check_lines(expected_lines)

    def test_multiple_annotations(self):
        a1, v1, v2 = map(lambda _: n(), range(3))
        v1, v2 = sorted([v1, v2])

        self.graph.add_increases(
            protein(namespace='HGNC', name='YFG1'),
            protein(namespace='HGNC', name='YFG'),
            citation=self.citation,
            evidence=self.evidence,
            annotations={
                a1: {v1, v2}
            }
        )

        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertEqual(1, self.graph.number_of_edges())

        expected_lines = [
            '#' * 80,
            'SET Citation = {{"PubMed", "{}"}}'.format(self.citation),
            'SET SupportingText = "{}"'.format(self.evidence),
            'SET {} = {{"{}", "{}"}}'.format(a1, v1, v2),
            'p(HGNC:YFG1) increases p(HGNC:YFG)',
            'UNSET {}'.format(a1),
            'UNSET SupportingText',
            'UNSET Citation',
        ]

        self.help_check_lines(expected_lines)
