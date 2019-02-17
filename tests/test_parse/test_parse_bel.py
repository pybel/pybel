# -*- coding: utf-8 -*-

"""Tests for the BEL parser."""

import logging
import unittest

from pybel import BELGraph
from pybel.constants import (
    ABUNDANCE, ACTIVITY, BEL_DEFAULT_NAMESPACE, BIOPROCESS, COMPLEX, COMPOSITE, DEGRADATION, DIRECTLY_INCREASES, DIRTY,
    EFFECT, FRAGMENT, FROM_LOC, FUNCTION, FUSION, FUSION_MISSING, FUSION_REFERENCE, FUSION_START, FUSION_STOP, GENE,
    HAS_COMPONENT, HAS_VARIANT, HGVS, IDENTIFIER, KIND, LOCATION, MEMBERS, MIRNA, MODIFIER, NAME, NAMESPACE,
    OBJECT, PARTNER_3P, PARTNER_5P, PATHOLOGY, PRODUCTS, PROTEIN, RANGE_3P, RANGE_5P, REACTANTS, REACTION,
    RELATION, RNA, SUBJECT, TARGET, TO_LOC, TRANSLOCATION, VARIANTS,
)
from pybel.dsl import (
    Fragment, abundance, bioprocess, cell_surface_expression, complex_abundance, composite_abundance, fragment,
    fusion_range, gene, gene_fusion, gmod, hgvs, mirna, named_complex_abundance, pathology, pmod, protein,
    protein_fusion, reaction, rna, rna_fusion, secretion, translocation,
)
from pybel.dsl.namespaces import hgnc
from pybel.language import Entity
from pybel.parser import BELParser
from pybel.parser.exc import MalformedTranslocationWarning
from pybel.parser.parse_bel import modifier_po_to_dict
from tests.constants import TestTokenParserBase, assert_has_edge, assert_has_node, update_provenance

log = logging.getLogger(__name__)

TEST_GENE_VARIANT = 'c.308G>A'
TEST_PROTEIN_VARIANT = 'p.Phe508del'


class TestAbundance(TestTokenParserBase):
    """2.1.1"""

    def setUp(self):
        self.parser.clear()
        self.parser.general_abundance.setParseAction(self.parser.handle_term)

        self.expected_node_data = abundance(namespace='CHEBI', name='oxygen atom')
        self.expected_canonical_bel = 'a(CHEBI:"oxygen atom")'

    def _test_abundance_helper(self, statement):
        result = self.parser.general_abundance.parseString(statement)
        self.assertEqual(dict(self.expected_node_data), result.asDict())

        self.assertIn(self.expected_node_data, self.graph)
        self.assertEqual(self.expected_canonical_bel, self.graph.node_to_bel(self.expected_node_data))

        self.assertEqual({}, modifier_po_to_dict(result), msg='The modifier dictionary should be empty')

    def test_abundance(self):
        """Test short/long abundance name."""
        self._test_abundance_helper('a(CHEBI:"oxygen atom")')
        self._test_abundance_helper('abundance(CHEBI:"oxygen atom")')

    def _test_abundance_with_location_helper(self, statement):
        result = self.parser.general_abundance.parseString(statement)

        expected_result = {
            FUNCTION: ABUNDANCE,
            NAMESPACE: 'CHEBI',
            NAME: 'oxygen atom',
            LOCATION: {
                NAMESPACE: 'GO',
                NAME: 'intracellular'
            }
        }

        self.assertEqual(expected_result, result.asDict())

        self.assertIn(self.expected_node_data, self.graph)
        self.assertEqual(self.expected_canonical_bel, self.graph.node_to_bel(self.expected_node_data))

        modifier = modifier_po_to_dict(result)
        expected_modifier = {
            LOCATION: {NAMESPACE: 'GO', NAME: 'intracellular'}
        }
        self.assertEqual(expected_modifier, modifier)

    def test_abundance_with_location(self):
        """Test short/long abundance name and short/long location name."""
        self._test_abundance_with_location_helper('a(CHEBI:"oxygen atom", loc(GO:intracellular))')
        self._test_abundance_with_location_helper('abundance(CHEBI:"oxygen atom", loc(GO:intracellular))')
        self._test_abundance_with_location_helper('a(CHEBI:"oxygen atom", location(GO:intracellular))')
        self._test_abundance_with_location_helper('abundance(CHEBI:"oxygen atom", location(GO:intracellular))')


class TestGene(TestTokenParserBase):
    """2.1.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XgeneA"""

    def setUp(self):
        self.parser.clear()
        self.parser.gene.setParseAction(self.parser.handle_term)

    def test_214a(self):
        statement = 'g(HGNC:AKT1)'

        result = self.parser.gene.parseString(statement)
        expected_list = [GENE, 'HGNC', 'AKT1']
        self.assertEqual(expected_list, result.asList())

        expected_dict = {
            FUNCTION: GENE,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1'
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = gene('HGNC', 'AKT1')
        self.assert_has_node(expected_node)
        self.assertEqual('g(HGNC:AKT1)', self.graph.node_to_bel(expected_node))
        self.assertEqual(1, len(self.graph))

    def test_214b(self):
        statement = 'g(HGNC:AKT1, loc(GO:intracellular))'

        result = self.parser.gene.parseString(statement)

        expected_dict = {
            FUNCTION: GENE,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1',
            LOCATION: {
                NAMESPACE: 'GO',
                NAME: 'intracellular'
            }
        }

        self.assertEqual(expected_dict, result.asDict())

        expected_node = gene('HGNC', 'AKT1')
        self.assert_has_node(expected_node)
        self.assertEqual('g(HGNC:AKT1)', self.graph.node_to_bel(expected_node))

    def test_214c(self):
        """Test variant"""
        statement = 'g(HGNC:AKT1, var(p.Phe508del))'
        result = self.parser.gene.parseString(statement)

        expected_result = {
            FUNCTION: GENE,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1',
            VARIANTS: [hgvs(TEST_PROTEIN_VARIANT)]
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = gene('HGNC', 'AKT1', variants=hgvs(TEST_PROTEIN_VARIANT))
        self.assert_has_node(expected_node)
        self.assertEqual('g(HGNC:AKT1, var("p.Phe508del"))', self.graph.node_to_bel(expected_node))

        parent = gene('HGNC', 'AKT1')
        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_gmod(self):
        """Test Gene Modification"""
        statement = 'geneAbundance(HGNC:AKT1,gmod(M))'
        result = self.parser.gene.parseString(statement)

        expected_result = {
            FUNCTION: GENE,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1',
            VARIANTS: [gmod('Me')]
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = gene('HGNC', 'AKT1', variants=gmod('Me'))
        self.assert_has_node(expected_node)
        self.assertEqual('g(HGNC:AKT1, gmod(Me))', self.graph.node_to_bel(expected_node))

        parent = gene('HGNC', 'AKT1')
        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_214d(self):
        """Test BEL 1.0 gene substitution"""
        statement = 'g(HGNC:AKT1,sub(G,308,A))'
        result = self.parser.gene.parseString(statement)

        expected_result = gene(
            name='AKT1',
            namespace='HGNC',
            variants=[hgvs(TEST_GENE_VARIANT)]
        )
        self.assertEqual(dict(expected_result), result.asDict())

        expected_node = gene('HGNC', 'AKT1', variants=hgvs("c.308G>A"))
        self.assert_has_node(expected_node)
        self.assertEqual('g(HGNC:AKT1, var("c.308G>A"))', self.graph.node_to_bel(expected_node))

        parent = gene('HGNC', 'AKT1')
        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_variant_location(self):
        """Test BEL 1.0 gene substitution with location tag"""
        statement = 'g(HGNC:AKT1,sub(G,308,A),loc(GO:intracellular))'
        result = self.parser.gene.parseString(statement)

        expected_result = {
            FUNCTION: GENE,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1',
            VARIANTS: [
                {
                    KIND: HGVS,
                    IDENTIFIER: TEST_GENE_VARIANT
                }
            ],
            LOCATION: {
                NAMESPACE: 'GO',
                NAME: 'intracellular'
            }
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = gene('HGNC', 'AKT1', variants=hgvs("c.308G>A"))
        self.assert_has_node(expected_node)
        self.assertEqual('g(HGNC:AKT1, var("c.308G>A"))', self.graph.node_to_bel(expected_node))

        parent = gene('HGNC', 'AKT1')
        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_multiple_variants(self):
        """Test multiple variants"""
        statement = 'g(HGNC:AKT1, var(p.Phe508del), sub(G,308,A), var(c.1521_1523delCTT))'
        result = self.parser.gene.parseString(statement)

        expected_result = {
            FUNCTION: GENE,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1',
            VARIANTS: [
                hgvs(TEST_PROTEIN_VARIANT),
                hgvs(TEST_GENE_VARIANT),
                hgvs('c.1521_1523delCTT')
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = gene('HGNC', 'AKT1', variants=[
            hgvs('c.1521_1523delCTT'), hgvs(TEST_GENE_VARIANT), hgvs(TEST_PROTEIN_VARIANT)
        ])
        self.assert_has_node(expected_node)
        self.assertEqual(
            'g(HGNC:AKT1, var("c.1521_1523delCTT"), var("c.308G>A"), var("p.Phe508del"))',
            self.graph.node_to_bel(expected_node),
        )

        parent = gene('HGNC', 'AKT1')
        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def _help_test_gene_fusion_1(self, statement):
        result = self.parser.gene.parseString(statement)
        expected_dict = {
            FUNCTION: GENE,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'TMPRSS2'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'ERG'},
                RANGE_5P: {
                    FUSION_REFERENCE: 'c',
                    FUSION_START: 1,
                    FUSION_STOP: 79

                },
                RANGE_3P: {
                    FUSION_REFERENCE: 'c',
                    FUSION_START: 312,
                    FUSION_STOP: 5034
                }
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        en = gene_fusion(
            partner_5p=gene('HGNC', 'TMPRSS2'), range_5p=fusion_range('c', 1, 79),
            partner_3p=gene('HGNC', 'ERG'), range_3p=fusion_range('c', 312, 5034)
        )
        self.assert_has_node(en)

        self.assertEqual('g(fus(HGNC:TMPRSS2, "c.1_79", HGNC:ERG, "c.312_5034"))', self.graph.node_to_bel(en))

    def test_gene_fusion_1(self):
        # no quotes
        self._help_test_gene_fusion_1('g(fus(HGNC:TMPRSS2, c.1_79, HGNC:ERG, c.312_5034))')
        # quotes
        self._help_test_gene_fusion_1('g(fus(HGNC:TMPRSS2, "c.1_79", HGNC:ERG, "c.312_5034"))')

    def _help_test_gene_fusion_2(self, statement):
        result = self.parser.gene.parseString(statement)
        expected_dict = {
            FUNCTION: GENE,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'TMPRSS2'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'ERG'},
                RANGE_5P: {
                    FUSION_REFERENCE: 'c',
                    FUSION_START: 1,
                    FUSION_STOP: '?'

                },
                RANGE_3P: {
                    FUSION_REFERENCE: 'c',
                    FUSION_START: 312,
                    FUSION_STOP: 5034
                }
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = gene_fusion(gene('HGNC', 'TMPRSS2'), gene('HGNC', 'ERG'), fusion_range('c', 1, '?'),
                                    fusion_range('c', 312, 5034))
        self.assert_has_node(expected_node)

        canonical_bel = self.graph.node_to_bel(expected_node)
        self.assertEqual('g(fus(HGNC:TMPRSS2, "c.1_?", HGNC:ERG, "c.312_5034"))', canonical_bel)

    def test_gene_fusion_2(self):
        # no quotes
        self._help_test_gene_fusion_2('g(fus(HGNC:TMPRSS2, c.1_?, HGNC:ERG, c.312_5034))')
        # correct
        self._help_test_gene_fusion_2('g(fus(HGNC:TMPRSS2, "c.1_?", HGNC:ERG, "c.312_5034"))')

    def _help_test_gene_fusion_3(self, statement):
        result = self.parser.gene.parseString(statement)
        expected_dict = {
            FUNCTION: GENE,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'TMPRSS2'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'ERG'},
                RANGE_5P: {
                    FUSION_MISSING: '?'
                },
                RANGE_3P: {
                    FUSION_REFERENCE: 'c',
                    FUSION_START: 312,
                    FUSION_STOP: 5034
                }
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = gene_fusion(gene('HGNC', 'TMPRSS2'), gene('HGNC', 'ERG'), range_3p=fusion_range('c', 312, 5034))
        self.assert_has_node(expected_node)

        self.assertEqual('g(fus(HGNC:TMPRSS2, "?", HGNC:ERG, "c.312_5034"))', self.graph.node_to_bel(expected_node))

    def test_gene_fusion_3(self):
        # no quotes
        self._help_test_gene_fusion_3('g(fus(HGNC:TMPRSS2, ?, HGNC:ERG, c.312_5034))')
        # correct
        self._help_test_gene_fusion_3('g(fus(HGNC:TMPRSS2, "?", HGNC:ERG, "c.312_5034"))')

    def _help_test_gene_fusion_legacy_1(self, statement):
        result = self.parser.gene.parseString(statement)

        expected_dict = {
            FUNCTION: GENE,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'BCR'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'JAK2'},
                RANGE_5P: {
                    FUSION_REFERENCE: 'c',
                    FUSION_START: '?',
                    FUSION_STOP: 1875

                },
                RANGE_3P: {
                    FUSION_REFERENCE: 'c',
                    FUSION_START: 2626,
                    FUSION_STOP: '?'
                }
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = gene_fusion(gene('HGNC', 'BCR'), gene('HGNC', 'JAK2'), fusion_range('c', '?', 1875),
                                    fusion_range('c', 2626, '?'))
        self.assert_has_node(expected_node)
        self.assertEqual('g(fus(HGNC:BCR, "c.?_1875", HGNC:JAK2, "c.2626_?"))', self.graph.node_to_bel(expected_node))

    def test_gene_fusion_legacy_1(self):
        # legacy
        self._help_test_gene_fusion_legacy_1('g(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626))')
        # no quotes
        self._help_test_gene_fusion_legacy_1('g(fus(HGNC:BCR, c.?_1875, HGNC:JAK2, c.2626_?))')
        # correct
        self._help_test_gene_fusion_legacy_1('g(fus(HGNC:BCR, "c.?_1875", HGNC:JAK2, "c.2626_?"))')

    def _help_test_gene_fusion_legacy_2(self, statement):
        result = self.parser.gene.parseString(statement)

        expected_dict = {
            FUNCTION: GENE,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'CHCHD4'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'AIFM1'},
                RANGE_5P: {FUSION_MISSING: '?'},
                RANGE_3P: {FUSION_MISSING: '?'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = gene_fusion(gene('HGNC', 'CHCHD4'), gene('HGNC', 'AIFM1'))
        self.assert_has_node(expected_node)
        self.assertEqual('g(fus(HGNC:CHCHD4, "?", HGNC:AIFM1, "?"))', self.graph.node_to_bel(expected_node))

    def test_gene_fusion_legacy_2(self):
        # legacy
        self._help_test_gene_fusion_legacy_2('g(HGNC:CHCHD4, fusion(HGNC:AIFM1))')
        # no quotes
        self._help_test_gene_fusion_legacy_2('g(fus(HGNC:CHCHD4, ?, HGNC:AIFM1, ?))')
        # correct
        self._help_test_gene_fusion_legacy_2('g(fus(HGNC:CHCHD4, "?", HGNC:AIFM1, "?"))')

    def test_gene_variant_snp(self):
        """2.2.2 SNP"""
        statement = 'g(SNP:rs113993960, var(c.1521_1523delCTT))'
        result = self.parser.gene.parseString(statement)

        expected_result = [GENE, 'SNP', 'rs113993960', [HGVS, 'c.1521_1523delCTT']]
        self.assertEqual(expected_result, result.asList())

        expected_node = gene('SNP', 'rs113993960', variants=hgvs('c.1521_1523delCTT'))
        self.assert_has_node(expected_node)
        self.assertEqual('g(SNP:rs113993960, var("c.1521_1523delCTT"))', self.graph.node_to_bel(expected_node))

        gene_node = expected_node.get_parent()
        self.assert_has_node(gene_node)
        self.assert_has_edge(gene_node, expected_node, relation=HAS_VARIANT)

    def test_gene_variant_chromosome(self):
        """2.2.2 chromosome"""
        statement = 'g(REF:"NC_000007.13", var(g.117199646_117199648delCTT))'
        result = self.parser.gene.parseString(statement)

        expected_result = [GENE, 'REF', 'NC_000007.13', [HGVS, 'g.117199646_117199648delCTT']]
        self.assertEqual(expected_result, result.asList())

        gene_node = gene('REF', 'NC_000007.13', variants=hgvs('g.117199646_117199648delCTT'))
        self.assert_has_node(gene_node)

        parent = gene_node.get_parent()
        self.assert_has_node(parent)
        self.assert_has_edge(parent, gene_node, relation=HAS_VARIANT)

    def test_gene_variant_deletion(self):
        """2.2.2 gene-coding DNA reference sequence"""
        statement = 'g(HGNC:CFTR, var(c.1521_1523delCTT))'
        result = self.parser.gene.parseString(statement)

        expected_result = {
            FUNCTION: GENE,
            NAMESPACE: 'HGNC',
            NAME: 'CFTR',
            VARIANTS: [
                {KIND: HGVS, IDENTIFIER: 'c.1521_1523delCTT'}
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = gene('HGNC', 'CFTR', variants=hgvs('c.1521_1523delCTT'))
        self.assert_has_node(expected_node)
        self.assertEqual('g(HGNC:CFTR, var("c.1521_1523delCTT"))', self.graph.node_to_bel(expected_node))

        gene_node = expected_node.get_parent()
        self.assert_has_node(gene_node)
        self.assert_has_edge(gene_node, expected_node, relation=HAS_VARIANT)


class TestMiRNA(TestTokenParserBase):
    """2.1.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XmicroRNAA"""

    def setUp(self):
        self.parser.clear()
        self.parser.mirna.setParseAction(self.parser.handle_term)

    def _test_no_variant_helper(self, statement):
        result = self.parser.mirna.parseString(statement)
        expected_result = [MIRNA, 'HGNC', 'MIR21']
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            FUNCTION: MIRNA,
            NAMESPACE: 'HGNC',
            NAME: 'MIR21'
        }

        self.assertEqual(expected_dict, result.asDict())

        node = mirna('HGNC', 'MIR21')
        self.assert_has_node(node)

    def test_short(self):
        self._test_no_variant_helper('m(HGNC:MIR21)')
        self._test_no_variant_helper('microRNAAbundance(HGNC:MIR21)')

    def test_mirna_location(self):
        statement = 'm(HGNC:MIR21,loc(GO:intracellular))'
        result = self.parser.mirna.parseString(statement)

        expected_dict = {
            FUNCTION: MIRNA,
            NAMESPACE: 'HGNC',
            NAME: 'MIR21',
            LOCATION: {
                NAMESPACE: 'GO',
                NAME: 'intracellular'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = mirna('HGNC', 'MIR21')
        self.assert_has_node(expected_node)

    def test_mirna_variant(self):
        statement = 'm(HGNC:MIR21,var(p.Phe508del))'
        result = self.parser.mirna.parseString(statement)

        expected_dict = {
            FUNCTION: MIRNA,
            NAMESPACE: 'HGNC',
            NAME: 'MIR21',
            VARIANTS: [
                {
                    KIND: HGVS,
                    IDENTIFIER: TEST_PROTEIN_VARIANT
                },
            ]
        }
        self.assertEqual(expected_dict, result.asDict())

        node = mirna('HGNC', 'MIR21', variants=hgvs(TEST_PROTEIN_VARIANT))
        self.assert_has_node(node)
        self.assertEqual('m(HGNC:MIR21, var("p.Phe508del"))', self.graph.node_to_bel(node))

        self.assertEqual(2, self.parser.graph.number_of_nodes())

        expected_parent = node.get_parent()
        self.assert_has_node(expected_parent)
        self.assert_has_edge(expected_parent, node, relation=HAS_VARIANT)

    def test_mirna_variant_location(self):
        statement = 'm(HGNC:MIR21,var(p.Phe508del),loc(GO:intracellular))'
        result = self.parser.mirna.parseString(statement)

        expected_dict = {
            FUNCTION: MIRNA,
            NAMESPACE: 'HGNC',
            NAME: 'MIR21',
            VARIANTS: [
                {
                    KIND: HGVS,
                    IDENTIFIER: 'p.Phe508del'
                },
            ],
            LOCATION: {
                NAMESPACE: 'GO',
                NAME: 'intracellular'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        node = mirna('HGNC', 'MIR21', variants=hgvs(TEST_PROTEIN_VARIANT))
        self.assert_has_node(node)
        self.assertEqual('m(HGNC:MIR21, var("p.Phe508del"))', self.graph.node_to_bel(node))

        self.assertEqual(2, self.parser.graph.number_of_nodes())

        expected_parent = node.get_parent()
        self.assert_has_node(expected_parent)
        self.assert_has_edge(expected_parent, node, relation=HAS_VARIANT)


class TestProtein(TestTokenParserBase):
    """2.1.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XproteinA"""

    def setUp(self):
        self.parser.clear()
        self.parser.protein.setParseAction(self.parser.handle_term)

    def _test_reference_helper(self, statement):
        result = self.parser.protein.parseString(statement)
        expected_result = [PROTEIN, 'HGNC', 'AKT1']
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            FUNCTION: PROTEIN,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1',
        }
        self.assertEqual(expected_dict, result.asDict())

        node = protein('HGNC', 'AKT1')
        self.assert_has_node(node)
        self.assertEqual('p(HGNC:AKT1)', self.graph.node_to_bel(node))

    def test_reference(self):
        self._test_reference_helper('p(HGNC:AKT1)')
        self._test_reference_helper('proteinAbundance(HGNC:AKT1)')

    def test_protein_with_location(self):
        statement = 'p(HGNC:AKT1, loc(GO:intracellular))'

        result = self.parser.protein.parseString(statement)

        expected_dict = {
            FUNCTION: PROTEIN,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1',
            LOCATION: {
                NAMESPACE: 'GO',
                NAME: 'intracellular'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        node = protein('HGNC', 'AKT1')
        self.assert_has_node(node)
        self.assertEqual('p(HGNC:AKT1)', self.graph.node_to_bel(node))

    def test_multiple_variants(self):
        statement = 'p(HGNC:AKT1,sub(A,127,Y),pmod(Ph, Ser),loc(GO:intracellular))'

        result = self.parser.protein.parseString(statement)

        expected_dict = {
            FUNCTION: PROTEIN,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1',
            LOCATION: {
                NAMESPACE: 'GO',
                NAME: 'intracellular'
            },
            VARIANTS: [
                hgvs('p.Ala127Tyr'),
                pmod(name='Ph', code='Ser')
            ]
        }
        self.assertEqual(expected_dict, result.asDict())

        parent = protein('HGNC', 'AKT1')
        node = parent.with_variants([hgvs('p.Ala127Tyr'), pmod('Ph', code='Ser')])
        self.assert_has_node(node)
        self.assertEqual('p(HGNC:AKT1, pmod(Ph, Ser), var("p.Ala127Tyr"))', self.graph.node_to_bel(node))

        self.assert_has_node(parent)
        self.assert_has_edge(parent, node, relation=HAS_VARIANT)

    def _help_test_protein_fusion_1(self, statement):
        result = self.parser.protein.parseString(statement)
        expected_dict = {
            FUNCTION: PROTEIN,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'TMPRSS2'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'ERG'},
                RANGE_5P: {
                    FUSION_REFERENCE: 'p',
                    FUSION_START: 1,
                    FUSION_STOP: 79

                },
                RANGE_3P: {
                    FUSION_REFERENCE: 'p',
                    FUSION_START: 312,
                    FUSION_STOP: 5034

                }
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = protein_fusion(
            protein('HGNC', 'TMPRSS2'),
            protein('HGNC', 'ERG'),
            fusion_range('p', 1, 79),
            fusion_range('p', 312, 5034)
        )
        self.assert_has_node(expected_node)
        self.assertEqual(
            'p(fus(HGNC:TMPRSS2, "p.1_79", HGNC:ERG, "p.312_5034"))',
            self.graph.node_to_bel(expected_node),
        )

    def test_protein_fusion_1(self):
        # no quotes
        self._help_test_protein_fusion_1('p(fus(HGNC:TMPRSS2, p.1_79, HGNC:ERG, p.312_5034))')
        # quotes
        self._help_test_protein_fusion_1('p(fus(HGNC:TMPRSS2, "p.1_79", HGNC:ERG, "p.312_5034"))')

    def _help_test_protein_fusion_legacy_1(self, statement):
        result = self.parser.protein.parseString(statement)

        expected_dict = {
            FUNCTION: PROTEIN,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'BCR'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'JAK2'},
                RANGE_5P: {
                    FUSION_REFERENCE: 'p',
                    FUSION_START: '?',
                    FUSION_STOP: 1875

                },
                RANGE_3P: {
                    FUSION_REFERENCE: 'p',
                    FUSION_START: 2626,
                    FUSION_STOP: '?'

                }
            }
        }

        self.assertEqual(expected_dict, result.asDict())

        expected_node = protein_fusion(
            protein('HGNC', 'BCR'),
            protein('HGNC', 'JAK2'),
            fusion_range('p', '?', 1875),
            fusion_range('p', 2626, '?')
        )
        self.assert_has_node(expected_node)
        canonical_bel = self.graph.node_to_bel(expected_node)
        self.assertEqual('p(fus(HGNC:BCR, "p.?_1875", HGNC:JAK2, "p.2626_?"))', canonical_bel)

    def test_protein_fusion_legacy_1(self):
        # legacy (BEL 1.0)
        self._help_test_protein_fusion_legacy_1('p(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626))')
        # missing quotes
        self._help_test_protein_fusion_legacy_1('p(fus(HGNC:BCR, p.?_1875, HGNC:JAK2, p.2626_?))')
        # correct
        self._help_test_protein_fusion_legacy_1('p(fus(HGNC:BCR, "p.?_1875", HGNC:JAK2, "p.2626_?"))')

    def _help_test_protein_legacy_fusion_2(self, statement):
        result = self.parser.protein.parseString(statement)

        expected_dict = {
            FUNCTION: PROTEIN,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'CHCHD4'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'AIFM1'},
                RANGE_5P: {FUSION_MISSING: '?'},
                RANGE_3P: {FUSION_MISSING: '?'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = protein_fusion(
            protein('HGNC', 'CHCHD4'),
            protein('HGNC', 'AIFM1'),
        )
        self.assert_has_node(expected_node)

        canonical_bel = self.graph.node_to_bel(expected_node)
        self.assertEqual('p(fus(HGNC:CHCHD4, "?", HGNC:AIFM1, "?"))', canonical_bel)

    def test_protein_fusion_legacy_2(self):
        # legacy (BEL 1.0)
        self._help_test_protein_legacy_fusion_2('proteinAbundance(HGNC:CHCHD4, fusion(HGNC:AIFM1))')
        # legacy shorthand (BEL 1.0)
        self._help_test_protein_legacy_fusion_2('p(HGNC:CHCHD4, fus(HGNC:AIFM1))')
        # missing quotes
        self._help_test_protein_legacy_fusion_2('p(fus(HGNC:CHCHD4, ?, HGNC:AIFM1, ?))')
        # correct
        self._help_test_protein_legacy_fusion_2('p(fus(HGNC:CHCHD4, "?", HGNC:AIFM1, "?"))')

    def _help_test_protein_trunc_1(self, statement):
        result = self.parser.protein.parseString(statement)

        expected_node = protein('HGNC', 'AKT1', variants=hgvs('p.40*'))
        self.assert_has_node(expected_node)

        canonical_bel = self.graph.node_to_bel(expected_node)
        self.assertEqual('p(HGNC:AKT1, var("p.40*"))', canonical_bel)

        protein_node = expected_node.get_parent()
        self.assert_has_node(protein_node)
        self.assert_has_edge(protein_node, expected_node, relation=HAS_VARIANT)

    def test_protein_trunc_1(self):
        # legacy
        self._help_test_protein_trunc_1('p(HGNC:AKT1, trunc(40))')
        # missing quotes
        self._help_test_protein_trunc_1('p(HGNC:AKT1, var(p.40*))')
        # correct
        self._help_test_protein_trunc_1('p(HGNC:AKT1, var("p.40*"))')

    def test_protein_trunc_2(self):
        statement = 'p(HGNC:AKT1, var(p.Cys40*))'
        result = self.parser.protein.parseString(statement)

        expected_result = [PROTEIN, 'HGNC', 'AKT1', [HGVS, 'p.Cys40*']]
        self.assertEqual(expected_result, result.asList())

        parent = protein('HGNC', 'AKT1')
        expected_node = parent.with_variants(hgvs('p.Cys40*'))
        self.assert_has_node(expected_node)
        self.assertEqual('p(HGNC:AKT1, var("p.Cys40*"))', self.graph.node_to_bel(expected_node))

        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_protein_trunc_3(self):
        statement = 'p(HGNC:AKT1, var(p.Arg1851*))'
        result = self.parser.protein.parseString(statement)

        expected_result = [PROTEIN, 'HGNC', 'AKT1', [HGVS, 'p.Arg1851*']]
        self.assertEqual(expected_result, result.asList())

        parent = protein('HGNC', 'AKT1')
        expected_node = parent.with_variants(hgvs('p.Arg1851*'))
        self.assert_has_node(expected_node)
        self.assertEqual('p(HGNC:AKT1, var("p.Arg1851*"))', self.graph.node_to_bel(expected_node))

        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_protein_pmod_1(self):
        """2.2.1 Test default BEL namespace and 1-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(Ph, S, 473))'
        result = self.parser.protein.parseString(statement)

        parent = protein('HGNC', 'AKT1')
        expected_node = parent.with_variants(pmod('Ph', code='Ser', position=473))
        self.assert_has_node(expected_node)
        self.assertEqual('p(HGNC:AKT1, pmod(Ph, Ser, 473))', self.graph.node_to_bel(expected_node))

        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_protein_pmod_2(self):
        """2.2.1 Test default BEL namespace and 3-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(Ph, Ser, 473))'
        result = self.parser.protein.parseString(statement)

        parent = protein('HGNC', 'AKT1')
        expected_node = parent.with_variants(pmod('Ph', code='Ser', position=473))
        self.assert_has_node(expected_node)
        self.assertEqual('p(HGNC:AKT1, pmod(Ph, Ser, 473))', self.graph.node_to_bel(expected_node))

        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_protein_pmod_3(self):
        """2.2.1 Test PSI-MOD namespace and 3-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(MOD:PhosRes,Ser,473))'
        result = self.parser.protein.parseString(statement)

        parent = protein('HGNC', 'AKT1')
        expected_node = parent.with_variants(pmod(namespace='MOD', name='PhosRes', code='Ser', position=473))
        self.assert_has_node(expected_node)
        self.assertEqual('p(HGNC:AKT1, pmod(MOD:PhosRes, Ser, 473))', self.graph.node_to_bel(expected_node))

        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_protein_pmod_4(self):
        """2.2.1 Test HRAS palmitoylated at an unspecified residue. Default BEL namespace"""
        statement = 'p(HGNC:HRAS,pmod(Palm))'
        result = self.parser.protein.parseString(statement)

        parent = protein('HGNC', 'HRAS')
        expected_node = parent.with_variants(pmod('Palm'))
        self.assert_has_node(expected_node)
        self.assertEqual('p(HGNC:HRAS, pmod(Palm))', self.graph.node_to_bel(expected_node))

        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_protein_variant_reference(self):
        """2.2.2 Test reference allele"""
        statement = 'p(HGNC:CFTR, var(=))'
        result = self.parser.protein.parseString(statement)
        expected_result = [PROTEIN, 'HGNC', 'CFTR', [HGVS, '=']]
        self.assertEqual(expected_result, result.asList())

        expected_node = protein('HGNC', 'CFTR', variants=hgvs('='))
        self.assert_has_node(expected_node)
        self.assertEqual('p(HGNC:CFTR, var("="))', self.graph.node_to_bel(expected_node))

        protein_node = expected_node.get_parent()
        self.assert_has_node(protein_node)
        self.assert_has_edge(protein_node, expected_node, relation=HAS_VARIANT)

    def test_protein_variant_unspecified(self):
        """2.2.2 Test unspecified variant"""
        statement = 'p(HGNC:CFTR, var(?))'
        result = self.parser.protein.parseString(statement)

        expected_result = [PROTEIN, 'HGNC', 'CFTR', [HGVS, '?']]
        self.assertEqual(expected_result, result.asList())

        expected_node = protein('HGNC', 'CFTR', variants=hgvs('?'))
        self.assert_has_node(expected_node)
        self.assertEqual('p(HGNC:CFTR, var("?"))', self.graph.node_to_bel(expected_node))

        parent = expected_node.get_parent()
        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_protein_variant_substitution(self):
        """2.2.2 Test substitution"""
        statement = 'p(HGNC:CFTR, var(p.Gly576Ala))'
        result = self.parser.protein.parseString(statement)
        expected_result = [PROTEIN, 'HGNC', 'CFTR', [HGVS, 'p.Gly576Ala']]
        self.assertEqual(expected_result, result.asList())

        expected_node = protein('HGNC', 'CFTR', variants=hgvs('p.Gly576Ala'))
        self.assert_has_node(expected_node)
        self.assertEqual('p(HGNC:CFTR, var("p.Gly576Ala"))', self.graph.node_to_bel(expected_node))

        parent = expected_node.get_parent()
        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_protein_variant_deletion(self):
        """2.2.2 deletion"""
        statement = 'p(HGNC:CFTR, var(p.Phe508del))'
        result = self.parser.protein.parseString(statement)

        expected_result = [PROTEIN, 'HGNC', 'CFTR', [HGVS, TEST_PROTEIN_VARIANT]]
        self.assertEqual(expected_result, result.asList())

        expected_node = protein('HGNC', 'CFTR', variants=hgvs('p.Phe508del'))
        self.assert_has_node(expected_node)
        self.assertEqual('p(HGNC:CFTR, var("p.Phe508del"))', self.graph.node_to_bel(expected_node))

        protein_node = expected_node.get_parent()
        self.assert_has_node(protein_node)
        self.assert_has_edge(protein_node, expected_node, relation=HAS_VARIANT)

    def test_protein_fragment_known(self):
        """2.2.3 fragment with known start/stop"""
        statement = 'p(HGNC:YFG, frag(5_20))'
        self.parser.protein.parseString(statement)

        parent = protein('HGNC', 'YFG')
        expected_node = parent.with_variants(fragment(5, 20))
        self.assert_has_node(expected_node)
        self.assertEqual('p(HGNC:YFG, frag("5_20"))', self.graph.node_to_bel(expected_node))

        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_protein_fragment_unbounded(self):
        """2.2.3 amino-terminal fragment of unknown length"""
        statement = 'p(HGNC:YFG, frag(1_?))'
        result = self.parser.protein.parseString(statement)

        parent = protein('HGNC', 'YFG')
        expected_node = parent.with_variants(fragment(1, '?'))
        self.assert_has_node(expected_node)
        self.assertEqual('p(HGNC:YFG, frag("1_?"))', self.graph.node_to_bel(expected_node))

        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_protein_fragment_unboundTerminal(self):
        """2.2.3 carboxyl-terminal fragment of unknown length"""
        statement = 'p(HGNC:YFG, frag(?_*))'
        result = self.parser.protein.parseString(statement)

        parent = protein('HGNC', 'YFG')
        expected_node = parent.with_variants(fragment('?', '*'))
        self.assert_has_node(expected_node)
        self.assertEqual('p(HGNC:YFG, frag("?_*"))', self.graph.node_to_bel(expected_node))

        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_protein_fragment_unknown(self):
        """2.2.3 fragment with unknown start/stop"""
        statement = 'p(HGNC:YFG, frag(?))'
        result = self.parser.protein.parseString(statement)

        expected_result = [PROTEIN, 'HGNC', 'YFG', [FRAGMENT, '?']]
        self.assertEqual(expected_result, result.asList())

        parent = protein('HGNC', 'YFG')
        expected_node = parent.with_variants(fragment())
        self.assert_has_node(expected_node)
        self.assertEqual('p(HGNC:YFG, frag("?"))', self.graph.node_to_bel(expected_node))

        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_protein_fragment_descriptor(self):
        """2.2.3 fragment with unknown start/stop and a descriptor"""
        statement = 'p(HGNC:YFG, frag(?, "55kD"))'
        result = self.parser.protein.parseString(statement)

        parent = protein('HGNC', 'YFG')
        expected_node = parent.with_variants(fragment('?', description='55kD'))
        self.assert_has_node(expected_node)
        self.assertEqual('p(HGNC:YFG, frag("?", "55kD"))', self.graph.node_to_bel(expected_node))

        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def test_ensure_no_dup_edges(self):
        """Ensure node and edges aren't added twice, even if from different statements and has origin completion"""
        s1 = 'p(HGNC:AKT1)'
        s2 = 'deg(p(HGNC:AKT1))'
        node = protein('HGNC', 'AKT1')

        self.parser.bel_term.parseString(s1)
        self.assert_has_node(node)
        self.assertEqual(1, self.parser.graph.number_of_nodes())
        self.assertEqual(0, self.parser.graph.number_of_edges())

        self.parser.bel_term.parseString(s2)
        self.assert_has_node(node)
        self.assertEqual(1, self.parser.graph.number_of_nodes())
        self.assertEqual(0, self.parser.graph.number_of_edges())


class TestRna(TestTokenParserBase):
    """2.1.7 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XrnaA"""

    def setUp(self):
        self.parser.clear()
        self.parser.rna.setParseAction(self.parser.handle_term)

    def _help_test_reference(self, statement):
        result = self.parser.rna.parseString(statement)
        expected_result = [RNA, 'HGNC', 'AKT1']
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            FUNCTION: RNA,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1'
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = rna('HGNC', 'AKT1')
        self.assert_has_node(expected_node)

        self.assertEqual('r(HGNC:AKT1)', self.graph.node_to_bel(expected_node))

    def test_reference(self):
        # short
        self._help_test_reference('r(HGNC:AKT1)')
        # long
        self._help_test_reference('rnaAbundance(HGNC:AKT1)')

    def test_multiple_variants(self):
        """Test multiple variants."""
        statement = 'r(HGNC:AKT1, var(p.Phe508del), var(c.1521_1523delCTT))'
        result = self.parser.rna.parseString(statement)

        expected_result = {
            FUNCTION: RNA,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1',
            VARIANTS: [
                hgvs(TEST_PROTEIN_VARIANT),
                hgvs('c.1521_1523delCTT')
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        parent = rna('HGNC', 'AKT1')
        expected_node = parent.with_variants([hgvs('c.1521_1523delCTT'), hgvs(TEST_PROTEIN_VARIANT)])
        self.assert_has_node(expected_node)

        self.assertEqual(
            'r(HGNC:AKT1, var("c.1521_1523delCTT"), var("p.Phe508del"))',
            self.graph.node_to_bel(expected_node),
        )

        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)

    def _help_test_rna_fusion_1(self, statement):
        result = self.parser.rna.parseString(statement)

        expected_dict = {
            FUNCTION: RNA,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'TMPRSS2'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'ERG'},
                RANGE_5P: {
                    FUSION_REFERENCE: 'r',
                    FUSION_START: 1,
                    FUSION_STOP: 79

                },
                RANGE_3P: {
                    FUSION_REFERENCE: 'r',
                    FUSION_START: 312,
                    FUSION_STOP: 5034
                }
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = rna_fusion(
            rna('HGNC', 'TMPRSS2'),
            rna('HGNC', 'ERG'),
            fusion_range('r', 1, 79),
            fusion_range('r', 312, 5034)
        )
        self.assert_has_node(expected_node)

        self.assertEqual('r(fus(HGNC:TMPRSS2, "r.1_79", HGNC:ERG, "r.312_5034"))',
                         self.graph.node_to_bel(expected_node))

    def test_rna_fusion_known_breakpoints(self):
        """Test RNA fusions (2.6.1) with known breakpoints (2.6.1)."""
        # missing quotes
        self._help_test_rna_fusion_1('r(fus(HGNC:TMPRSS2, r.1_79, HGNC:ERG, r.312_5034))')
        # correct (short form)
        self._help_test_rna_fusion_1('r(fus(HGNC:TMPRSS2, "r.1_79", HGNC:ERG, "r.312_5034"))')
        # correct (long form)
        self._help_test_rna_fusion_1('rnaAbundance(fusion(HGNC:TMPRSS2, "r.1_79", HGNC:ERG, "r.312_5034"))')

    def _help_test_rna_fusion_unspecified_breakpoints(self, statement):
        result = self.parser.rna.parseString(statement)

        expected_dict = {
            FUNCTION: RNA,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'TMPRSS2'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'ERG'},
                RANGE_5P: {
                    FUSION_MISSING: '?',
                },
                RANGE_3P: {
                    FUSION_MISSING: '?',
                }
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = rna_fusion(
            rna('HGNC', 'TMPRSS2'),
            rna('HGNC', 'ERG'),
        )
        self.assert_has_node(expected_node)
        self.assertEqual('r(fus(HGNC:TMPRSS2, "?", HGNC:ERG, "?"))', self.graph.node_to_bel(expected_node))

    def test_rna_fusion_unspecified_breakpoints(self):
        """Test RNA fusions (2.6.1) with unspecified breakpoints."""
        # legacy
        self._help_test_rna_fusion_unspecified_breakpoints('r(HGNC:TMPRSS2, fusion(HGNC:ERG))')
        # missing quotes
        self._help_test_rna_fusion_unspecified_breakpoints('r(fus(HGNC:TMPRSS2, ?, HGNC:ERG, ?))')
        # correct (short form)
        self._help_test_rna_fusion_unspecified_breakpoints('r(fus(HGNC:TMPRSS2, "?", HGNC:ERG, "?"))')
        # correct (long form)
        self._help_test_rna_fusion_unspecified_breakpoints('rnaAbundance(fusion(HGNC:TMPRSS2, "?", HGNC:ERG, "?"))')

    def _help_test_rna_fusion_legacy_1(self, statement):
        result = self.parser.rna.parseString(statement)

        expected_dict = {
            FUNCTION: RNA,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'BCR'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'JAK2'},
                RANGE_5P: {
                    FUSION_REFERENCE: 'r',
                    FUSION_START: '?',
                    FUSION_STOP: 1875

                },
                RANGE_3P: {
                    FUSION_REFERENCE: 'r',
                    FUSION_START: 2626,
                    FUSION_STOP: '?'
                }
            }

        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = rna_fusion(
            rna('HGNC', 'BCR'),
            rna('HGNC', 'JAK2'),
            fusion_range('r', '?', 1875),
            fusion_range('r', 2626, '?')
        )
        self.assert_has_node(expected_node)
        self.assertEqual('r(fus(HGNC:BCR, "r.?_1875", HGNC:JAK2, "r.2626_?"))', self.graph.node_to_bel(expected_node))

    def test_rna_fusion_legacy_1(self):
        # legacy
        self._help_test_rna_fusion_legacy_1('r(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626))')
        # no quotes
        self._help_test_rna_fusion_legacy_1('r(fus(HGNC:BCR, r.?_1875, HGNC:JAK2, r.2626_?))')
        # correct
        self._help_test_rna_fusion_legacy_1('r(fus(HGNC:BCR, "r.?_1875", HGNC:JAK2, "r.2626_?"))')

    def test_rna_variant_codingReference(self):
        """2.2.2 RNA coding reference sequence"""
        statement = 'r(HGNC:CFTR, var(r.1521_1523delcuu))'
        result = self.parser.rna.parseString(statement)

        expected_dict = {
            FUNCTION: RNA,
            NAMESPACE: 'HGNC',
            NAME: 'CFTR',
            VARIANTS: [hgvs('r.1521_1523delcuu')]
        }
        self.assertEqual(expected_dict, result.asDict())

        parent = rna('HGNC', 'CFTR')
        expected_node = parent.with_variants(hgvs('r.1521_1523delcuu'))
        self.assert_has_node(expected_node)

        self.assertEqual('r(HGNC:CFTR, var("r.1521_1523delcuu"))', self.graph.node_to_bel(expected_node))
        self.assert_has_node(parent)
        self.assert_has_edge(parent, expected_node, relation=HAS_VARIANT)


class TestComplex(TestTokenParserBase):
    """2.1.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcomplexA"""

    def setUp(self):
        self.parser.clear()
        self.parser.complex_abundances.setParseAction(self.parser.handle_term)

    def test_named_complex_singleton(self):
        statement = 'complex(SCOMP:"AP-1 Complex")'
        result = self.parser.complex_abundances.parseString(statement)

        expected_dict = {
            FUNCTION: COMPLEX,
            NAMESPACE: 'SCOMP',
            NAME: 'AP-1 Complex'
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = named_complex_abundance('SCOMP', 'AP-1 Complex')
        self.assert_has_node(expected_node)

    def test_complex_list_short(self):
        statement = 'complex(p(HGNC:FOS), p(HGNC:JUN))'
        result = self.parser.complex_abundances.parseString(statement)

        expected_result = [COMPLEX, [PROTEIN, 'HGNC', 'FOS'], [PROTEIN, 'HGNC', 'JUN']]
        self.assertEqual(expected_result, result.asList())

        expected_result = {
            FUNCTION: COMPLEX,
            MEMBERS: [
                {
                    FUNCTION: PROTEIN,
                    NAMESPACE: 'HGNC',
                    NAME: 'FOS'
                }, {
                    FUNCTION: PROTEIN,
                    NAMESPACE: 'HGNC',
                    NAME: 'JUN'
                }
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        child_1 = protein('HGNC', 'FOS')
        self.assert_has_node(child_1)

        child_2 = protein('HGNC', 'JUN')
        self.assert_has_node(child_2)

        expected_node = complex_abundance([child_1, child_2])
        self.assert_has_node(expected_node)

        self.assert_has_edge(expected_node, child_1, relation=HAS_COMPONENT)
        self.assert_has_edge(expected_node, child_2, relation=HAS_COMPONENT)

    def test_complex_list_long(self):
        statement = 'complexAbundance(proteinAbundance(HGNC:HBP1),geneAbundance(HGNC:NCF1))'
        self.parser.complex_abundances.parseString(statement)


class TestComposite(TestTokenParserBase):
    """Tests the parsing of the composite function

    .. seealso::

            `BEL 2.0 Specification 2.1.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XcompositeA>`_
    """

    def setUp(self):
        self.parser.clear()
        self.parser.composite_abundance.setParseAction(self.parser.handle_term)

    def test_213a(self):
        """Evidence: ``IL-6 and IL-23 synergistically induce Th17 differentiation"""
        statement = 'composite(p(HGNC:IL6), complex(GO:"interleukin-23 complex"))'
        result = self.parser.composite_abundance.parseString(statement)

        expected_result = [COMPOSITE, [PROTEIN, 'HGNC', 'IL6'], [COMPLEX, 'GO', 'interleukin-23 complex']]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            FUNCTION: COMPOSITE,
            MEMBERS: [
                {
                    FUNCTION: PROTEIN,
                    NAMESPACE: 'HGNC',
                    NAME: 'IL6'
                }, {
                    FUNCTION: COMPLEX,
                    NAMESPACE: 'GO',
                    NAME: 'interleukin-23 complex'
                }
            ]
        }
        self.assertEqual(expected_dict, result.asDict())

        il23 = named_complex_abundance('GO', 'interleukin-23 complex')
        il6 = protein('HGNC', 'IL6')
        expected_node = composite_abundance([il23, il6])
        self.assert_has_node(expected_node)

        self.assertEqual(2, len(expected_node[MEMBERS]))
        self.assertEqual(il23, expected_node[MEMBERS][0])
        self.assertEqual(il6, expected_node[MEMBERS][1])

        self.assertEqual('composite(complex(GO:"interleukin-23 complex"), p(HGNC:IL6))',
                         self.graph.node_to_bel(expected_node))

        self.assertEqual(3, self.parser.graph.number_of_nodes())
        self.assert_has_node(expected_node)
        self.assert_has_node(il23)
        self.assert_has_node(il6)
        self.assertEqual(2, self.parser.graph.number_of_edges())


class TestBiologicalProcess(TestTokenParserBase):
    def setUp(self):
        self.parser.clear()
        self.parser.biological_process.setParseAction(self.parser.handle_term)

    def test_231a(self):
        """"""
        statement = 'bp(GO:"cell cycle arrest")'
        result = self.parser.biological_process.parseString(statement)

        expected_result = [BIOPROCESS, 'GO', 'cell cycle arrest']
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            FUNCTION: BIOPROCESS,
            NAMESPACE: 'GO',
            NAME: 'cell cycle arrest'
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = bioprocess('GO', 'cell cycle arrest')
        self.assert_has_node(expected_node)


class TestPathology(TestTokenParserBase):
    def setUp(self):
        self.parser.clear()
        self.parser.pathology.setParseAction(self.parser.handle_term)

    def test_232a(self):
        statement = 'pathology(MESH:adenocarcinoma)'
        result = self.parser.pathology.parseString(statement)

        expected_dict = {
            FUNCTION: PATHOLOGY,
            NAMESPACE: 'MESH',
            NAME: 'adenocarcinoma'
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = pathology('MESH', 'adenocarcinoma')
        self.assert_has_node(expected_node)

        self.assertEqual('path(MESH:adenocarcinoma)', self.graph.node_to_bel(expected_node))


class TestActivity(TestTokenParserBase):
    """Tests for molecular activity terms."""

    def setUp(self):
        """Set up parser for testing the activity language."""
        self.parser.clear()
        self.parser.activity.setParseAction(self.parser.handle_term)

    def test_activity_bare(self):
        statement = 'act(p(HGNC:AKT1))'
        result = self.parser.activity.parseString(statement)

        expected_result = [ACTIVITY, [PROTEIN, 'HGNC', 'AKT1']]
        self.assertEqual(expected_result, result.asList())

        mod = modifier_po_to_dict(result)
        expected_mod = {
            MODIFIER: ACTIVITY
        }
        self.assertEqual(expected_mod, mod)

    def test_activity_withMolecularActivityDefault(self):
        """Tests activity modifier with molecular activity from default BEL namespace"""
        statement = 'act(p(HGNC:AKT1), ma(kin))'
        result = self.parser.activity.parseString(statement)

        expected_dict = {
            MODIFIER: ACTIVITY,
            EFFECT: {
                NAME: 'kin',
                NAMESPACE: BEL_DEFAULT_NAMESPACE
            },
            TARGET: {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = modifier_po_to_dict(result)
        expected_mod = {
            MODIFIER: ACTIVITY,
            EFFECT: {
                NAME: 'kin',
                NAMESPACE: BEL_DEFAULT_NAMESPACE
            }
        }
        self.assertEqual(expected_mod, mod)

    def test_activity_withMolecularActivityDefaultLong(self):
        """Tests activity modifier with molecular activity from custom namespaced"""
        statement = 'act(p(HGNC:AKT1), ma(catalyticActivity))'
        result = self.parser.activity.parseString(statement)

        expected_dict = {
            MODIFIER: ACTIVITY,
            EFFECT: {
                NAME: 'cat',
                NAMESPACE: BEL_DEFAULT_NAMESPACE
            },
            TARGET: {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = modifier_po_to_dict(result)
        expected_mod = {
            MODIFIER: ACTIVITY,
            EFFECT: {
                NAME: 'cat',
                NAMESPACE: BEL_DEFAULT_NAMESPACE
            }
        }
        self.assertEqual(expected_mod, mod)

    def test_activity_withMolecularActivityCustom(self):
        """Tests activity modifier with molecular activity from custom namespaced"""
        statement = 'act(p(HGNC:AKT1), ma(GOMF:"catalytic activity"))'
        result = self.parser.activity.parseString(statement)

        expected_dict = {
            MODIFIER: ACTIVITY,
            EFFECT: {
                NAMESPACE: 'GOMF',
                NAME: 'catalytic activity'
            },
            TARGET: {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = modifier_po_to_dict(result)
        expected_mod = {
            MODIFIER: ACTIVITY,
            EFFECT: {
                NAMESPACE: 'GOMF',
                NAME: 'catalytic activity'
            }
        }
        self.assertEqual(expected_mod, mod)

    def test_activity_legacy(self):
        """Test BEL 1.0 style molecular activity annotation"""
        statement = 'kin(p(HGNC:AKT1))'
        result = self.parser.activity.parseString(statement)

        expected_dict = {
            MODIFIER: ACTIVITY,
            EFFECT: {
                NAME: 'kin',
                NAMESPACE: BEL_DEFAULT_NAMESPACE
            },
            TARGET: {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = modifier_po_to_dict(result)
        expected_mod = {
            MODIFIER: ACTIVITY,
            EFFECT: {
                NAME: 'kin',
                NAMESPACE: BEL_DEFAULT_NAMESPACE
            }
        }
        self.assertEqual(expected_mod, mod)

        node = protein('HGNC', 'AKT1')
        self.assert_has_node(node)

    def test_kinase_activity_on_named_complex(self):
        statement = 'kin(complex(FPLX:C1))'
        self.parser.activity.parseString(statement)

    def test_activity_on_named_complex(self):
        statement = 'act(complex(FPLX:C1), ma(kin))'
        self.parser.activity.parseString(statement)

    def test_kinase_activity_on_listed_complex(self):
        statement = 'kin(complex(p(HGNC:A), p(HGNC:B)))'
        self.parser.activity.parseString(statement)

    def test_activity_on_listed_complex(self):
        statement = 'act(complex(p(HGNC:A), p(HGNC:B)), ma(kin))'
        self.parser.activity.parseString(statement)


class TestTranslocationPermissive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = BELGraph()
        cls.parser = BELParser(
            cls.graph,
            disallow_unqualified_translocations=False,
        )

    def setUp(self):
        self.parser.clear()
        self.parser.transformation.setParseAction(self.parser.handle_term)

    def assert_has_node(self, member, **kwargs):
        assert_has_node(self, member, self.parser.graph, **kwargs)

    def assert_has_edge(self, u, v, **kwargs):
        assert_has_edge(self, u, v, self.parser.graph, **kwargs)

    def test_unqualified_translocation_single(self):
        """translocation example"""
        statement = 'tloc(p(HGNC:EGFR))'
        result = self.parser.transformation.parseString(statement)

        expected_dict = {
            MODIFIER: TRANSLOCATION,
            TARGET: {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'EGFR'
            },
        }

        self.assertEqual(expected_dict, result.asDict())

        mod = modifier_po_to_dict(result)
        expected_mod = {
            MODIFIER: TRANSLOCATION,
        }
        self.assertEqual(expected_mod, mod)

        node = protein('HGNC', 'EGFR')
        self.assert_has_node(node)

    def test_unqualified_translocation_relation(self):
        """Test translocation in object.

        3.1.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XdIncreases
        """
        update_provenance(self.parser.control_parser)

        statement = 'a(ADO:"Abeta_42") => tloc(a(CHEBI:"calcium(2+)"))'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            SUBJECT: {
                FUNCTION: ABUNDANCE,
                NAMESPACE: 'ADO',
                NAME: 'Abeta_42'
            },
            RELATION: DIRECTLY_INCREASES,
            OBJECT: {
                TARGET: {
                    FUNCTION: ABUNDANCE,
                    NAMESPACE: 'CHEBI',
                    NAME: 'calcium(2+)'
                },
                MODIFIER: TRANSLOCATION,
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = abundance('ADO', 'Abeta_42')
        self.assert_has_node(sub)

        obj = abundance('CHEBI', 'calcium(2+)')
        self.assert_has_node(obj)

        expected_annotations = {
            RELATION: DIRECTLY_INCREASES,
            OBJECT: {
                MODIFIER: TRANSLOCATION,
            }
        }

        self.assert_has_edge(sub, obj, **expected_annotations)


class TestTransformation(TestTokenParserBase):
    def setUp(self):
        self.parser.clear()
        self.parser.transformation.setParseAction(self.parser.handle_term)

    def test_degredation_short(self):
        """Test the short form of degradation works"""
        statement = 'deg(p(HGNC:AKT1))'
        result = self.parser.transformation.parseString(statement)

        expected_result = [DEGRADATION, [PROTEIN, 'HGNC', 'AKT1']]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            MODIFIER: DEGRADATION,
            TARGET: {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = modifier_po_to_dict(result)
        expected_mod = {
            MODIFIER: DEGRADATION,
        }
        self.assertEqual(expected_mod, mod)

    def test_degradation_long(self):
        """Test the long form of degradation works"""
        statement = 'degradation(p(HGNC:EGFR))'
        result = self.parser.transformation.parseString(statement)

        expected_dict = {
            MODIFIER: DEGRADATION,
            TARGET: {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'EGFR'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = modifier_po_to_dict(result)
        expected_mod = {
            MODIFIER: DEGRADATION,
        }
        self.assertEqual(expected_mod, mod)

        node = protein('HGNC', 'EGFR')
        self.assert_has_node(node)

    def test_translocation_standard(self):
        """translocation example"""
        statement = 'tloc(p(HGNC:EGFR), fromLoc(GO:"cell surface"), toLoc(GO:endosome))'
        result = self.parser.transformation.parseString(statement)

        expected_dict = {
            MODIFIER: TRANSLOCATION,
            TARGET: {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'EGFR'
            },
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GO', NAME: 'cell surface'},
                TO_LOC: {NAMESPACE: 'GO', NAME: 'endosome'}
            }
        }

        self.assertEqual(expected_dict, result.asDict())

        mod = modifier_po_to_dict(result)
        expected_mod = translocation(
            from_loc=Entity(namespace='GO', name='cell surface'),
            to_loc=Entity(namespace='GO', name='endosome'),
        )

        self.assertEqual(expected_mod, mod)

        node = protein('HGNC', 'EGFR')
        self.assert_has_node(node)

    def test_translocation_bare(self):
        """translocation example"""
        statement = 'tloc(p(HGNC:EGFR), GO:"cell surface", GO:endosome)'
        result = self.parser.transformation.parseString(statement)

        expected_dict = {
            MODIFIER: TRANSLOCATION,
            TARGET: {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'EGFR'
            },
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GO', NAME: 'cell surface'},
                TO_LOC: {NAMESPACE: 'GO', NAME: 'endosome'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = modifier_po_to_dict(result)
        expected_mod = {
            MODIFIER: TRANSLOCATION,
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GO', NAME: 'cell surface'},
                TO_LOC: {NAMESPACE: 'GO', NAME: 'endosome'}
            }
        }
        self.assertEqual(expected_mod, mod)

        node = protein('HGNC', 'EGFR')
        self.assert_has_node(node)

    def test_unqualified_translocation_strict(self):
        """Fail on an improperly written single argument translocation"""
        statement = 'tloc(a(NS:"T-Lymphocytes"))'
        with self.assertRaises(MalformedTranslocationWarning):
            self.parser.translocation.parseString(statement)

    def test_translocation_secretion(self):
        """cell secretion short form"""
        statement = 'sec(p(HGNC:EGFR))'
        result = self.parser.transformation.parseString(statement)

        expected_result = ['CellSecretion', [PROTEIN, 'HGNC', 'EGFR']]
        self.assertEqual(expected_result, result.asList())

        mod = modifier_po_to_dict(result)
        expected_mod = secretion()
        self.assertEqual(expected_mod, mod)

        node = protein('HGNC', 'EGFR')
        self.assert_has_node(node)

    def test_translocation_surface(self):
        """cell surface expression short form"""
        statement = 'surf(p(HGNC:EGFR))'
        result = self.parser.transformation.parseString(statement)

        expected_result = ['CellSurfaceExpression', [PROTEIN, 'HGNC', 'EGFR']]
        self.assertEqual(expected_result, result.asList())

        expected_mod = cell_surface_expression()
        self.assertEqual(expected_mod, modifier_po_to_dict(result))

        node = protein('HGNC', 'EGFR')
        self.assert_has_node(node)

    def test_reaction_1(self):
        statement = 'rxn(reactants(a(CHEBI:superoxide)), products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:oxygen)))'
        result = self.parser.transformation.parseString(statement)

        expected_dict = {
            FUNCTION: REACTION,
            REACTANTS: [
                {
                    FUNCTION: ABUNDANCE,
                    NAMESPACE: 'CHEBI',
                    NAME: 'superoxide'
                }
            ],
            PRODUCTS: [
                {
                    FUNCTION: ABUNDANCE,
                    NAMESPACE: 'CHEBI',
                    NAME: 'hydrogen peroxide'
                }, {

                    FUNCTION: ABUNDANCE,
                    NAMESPACE: 'CHEBI',
                    NAME: 'oxygen'
                }

            ]
        }
        self.assertEqual(expected_dict, result.asDict())

        superoxide_node = abundance('CHEBI', 'superoxide')
        hydrogen_peroxide = abundance('CHEBI', 'hydrogen peroxide')
        oxygen_node = abundance('CHEBI', 'oxygen')
        expected_node = reaction([superoxide_node], [hydrogen_peroxide, oxygen_node])

        self.assert_has_node(expected_node)

        self.assertEqual(statement, self.graph.node_to_bel(expected_node))

        self.assert_has_node(superoxide_node)
        self.assert_has_edge(expected_node, superoxide_node)

        self.assert_has_node(hydrogen_peroxide)
        self.assert_has_edge(expected_node, hydrogen_peroxide)

        self.assert_has_node(oxygen_node)
        self.assert_has_edge(expected_node, oxygen_node)

    def test_reaction_2(self):
        statement = 'rxn(reactants(p(HGNC:APP)), products(p(HGNC:APP, frag(672_713))))'
        self.parser.transformation.parseString(statement)

        app = hgnc('APP')
        self.assertIn(app, self.graph)

        amyloid_beta_42 = app.with_variants(Fragment(start=672, stop=713))
        self.assertIn(amyloid_beta_42, self.graph)

        expected_node = reaction(app, amyloid_beta_42)
        self.assertIn(expected_node, self.graph)

    def test_clearance(self):
        """Tests that after adding things, the graph and parser can be cleared properly"""
        s1 = 'surf(p(HGNC:EGFR))'
        s2 = 'rxn(reactants(a(CHEBI:superoxide)),products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:"oxygen")))'

        self.parser.transformation.parseString(s1)
        self.parser.transformation.parseString(s2)
        self.assertGreater(self.parser.graph.number_of_nodes(), 0)
        self.assertGreater(self.parser.graph.number_of_edges(), 0)

        self.parser.clear()
        self.assertEqual(0, self.parser.graph.number_of_nodes())
        self.assertEqual(0, self.parser.graph.number_of_edges())
        self.assertEqual(0, len(self.parser.control_parser.annotations))
        self.assertEqual(0, len(self.parser.control_parser.citation))


class TestSemantics(unittest.TestCase):
    def test_lenient_semantic_no_failure(self):
        graph = BELGraph()
        parser = BELParser(graph, allow_naked_names=True)

        update_provenance(parser.control_parser)

        parser.bel_term.addParseAction(parser.handle_term)
        parser.bel_term.parseString('bp(ABASD)')

        node_data = bioprocess(namespace=DIRTY, name='ABASD')
        self.assertIn(node_data, graph)
