# -*- coding: utf-8 -*-

import logging
import unittest

from pybel.canonicalize import decanonicalize_node, decanonicalize_edge
from pybel.constants import *
from pybel.parser.modifiers import FusionParser, LocationParser, GmodParser, FragmentParser, PmodParser
from pybel.parser.modifiers import GsubParser, TruncParser, PsubParser, VariantParser
from pybel.parser.parse_bel import canonicalize_modifier, canonicalize_node
from pybel.parser.parse_exceptions import NestedRelationWarning, MalformedTranslocationWarning
from tests.constants import TestTokenParserBase, SET_CITATION_TEST, test_set_evidence, build_variant_dict, \
    test_citation_dict, test_evidence_text

log = logging.getLogger(__name__)

TEST_GENE_VARIANT = 'c.308G>A'
TEST_PROTEIN_VARIANT = 'p.Phe508del'


def identifier(namespace, name):
    return {NAMESPACE: namespace, NAME: name}


def default_identifier(name):
    """Convenience function for building a default namespace/name pair"""
    return identifier(BEL_DEFAULT_NAMESPACE, name)


class TestVariantParser(unittest.TestCase):
    def setUp(self):
        self.parser = VariantParser()

    def test_protein_del(self):
        statement = 'variant(p.Phe508del)'
        expected = build_variant_dict('p.Phe508del')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_protein_mut(self):
        statement = 'var(p.Gly576Ala)'
        expected = build_variant_dict('p.Gly576Ala')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_unspecified(self):
        statement = 'var(=)'
        expected = build_variant_dict('=')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_frameshift(self):
        statement = 'variant(p.Thr1220Lysfs)'
        expected = build_variant_dict('p.Thr1220Lysfs')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_snp(self):
        statement = 'var(c.1521_1523delCTT)'
        expected = build_variant_dict('c.1521_1523delCTT')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_chromosome_1(self):
        statement = 'variant(g.117199646_117199648delCTT)'
        expected = build_variant_dict('g.117199646_117199648delCTT')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_chromosome_2(self):
        statement = 'var(c.1521_1523delCTT)'
        expected = build_variant_dict('c.1521_1523delCTT')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_rna_del(self):
        statement = 'var(r.1653_1655delcuu)'
        expected = build_variant_dict('r.1653_1655delcuu')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_protein_trunc_triple(self):
        statement = 'var(p.Cys65*)'
        result = self.parser.parseString(statement)
        expected = build_variant_dict('p.Cys65*')
        self.assertEqual(expected, result.asDict())

    def test_protein_trunc_legacy(self):
        statement = 'var(p.65*)'
        result = self.parser.parseString(statement)
        expected = build_variant_dict('p.65*')
        self.assertEqual(expected, result.asDict())


class TestPmod(unittest.TestCase):
    def setUp(self):
        self.parser = PmodParser()

    def test_pmod1(self):
        statement = 'pmod(Ph, Ser, 473)'
        result = self.parser.parseString(statement)

        expected = {
            KIND: PMOD,
            IDENTIFIER: identifier(BEL_DEFAULT_NAMESPACE, 'Ph'),
            PmodParser.CODE: 'Ser',
            PmodParser.POSITION: 473
        }
        self.assertEqual(expected, result.asDict())

    def test_pmod2(self):
        statement = 'pmod(Ph, Ser)'
        result = self.parser.parseString(statement)

        expected = {
            KIND: PMOD,
            IDENTIFIER: identifier(BEL_DEFAULT_NAMESPACE, 'Ph'),
            PmodParser.CODE: 'Ser',
        }
        self.assertEqual(expected, result.asDict())

    def test_pmod3(self):
        statement = 'pmod(Ph)'
        result = self.parser.parseString(statement)

        expected = {
            KIND: PMOD,
            IDENTIFIER: identifier(BEL_DEFAULT_NAMESPACE, 'Ph'),
        }
        self.assertEqual(expected, result.asDict())

    def test_pmod4(self):
        statement = 'pmod(P, S, 473)'
        result = self.parser.parseString(statement)

        expected = {
            KIND: PMOD,
            IDENTIFIER: identifier(BEL_DEFAULT_NAMESPACE, 'Ph'),
            PmodParser.CODE: 'Ser',
            PmodParser.POSITION: 473
        }
        self.assertEqual(expected, result.asDict())

    def test_pmod5(self):
        statement = 'pmod(MOD:PhosRes, Ser, 473)'
        result = self.parser.parseString(statement)

        expected = {
            KIND: PMOD,
            IDENTIFIER: identifier('MOD', 'PhosRes'),
            PmodParser.CODE: 'Ser',
            PmodParser.POSITION: 473
        }
        self.assertEqual(expected, result.asDict())


class TestGmod(unittest.TestCase):
    def setUp(self):
        self.parser = GmodParser()

        self.expected = {
            KIND: GMOD,
            IDENTIFIER: identifier(BEL_DEFAULT_NAMESPACE, 'Me')
        }

    def test_gmod_short(self):
        statement = 'gmod(M)'
        result = self.parser.parseString(statement)
        self.assertEqual(self.expected, result.asDict())

    def test_gmod_unabbreviated(self):
        statement = 'gmod(Me)'
        result = self.parser.parseString(statement)
        self.assertEqual(self.expected, result.asDict())

    def test_gmod_long(self):
        statement = 'geneModification(methylation)'
        result = self.parser.parseString(statement)
        self.assertEqual(self.expected, result.asDict())


class TestPsub(unittest.TestCase):
    def setUp(self):
        self.parser = PsubParser()

    def test_psub_1(self):
        statement = 'sub(A, 127, Y)'
        result = self.parser.parseString(statement)

        expected_list = build_variant_dict('p.Ala127Tyr')
        self.assertEqual(expected_list, result.asDict())

    def test_psub_2(self):
        statement = 'sub(Ala, 127, Tyr)'
        result = self.parser.parseString(statement)

        expected_list = build_variant_dict('p.Ala127Tyr')
        self.assertEqual(expected_list, result.asDict())


class TestGsubParser(unittest.TestCase):
    def setUp(self):
        self.parser = GsubParser()

    def test_gsub(self):
        statement = 'sub(G,308,A)'
        result = self.parser.parseString(statement)

        expected_dict = build_variant_dict('c.308G>A')
        self.assertEqual(expected_dict, result.asDict())


class TestFragmentParser(unittest.TestCase):
    """See http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_examples_2"""

    def setUp(self):
        self.parser = FragmentParser()

    def test_known_length(self):
        """test known length"""
        s = 'frag(5_20)'
        result = self.parser.parseString(s)
        expected = {
            KIND: FRAGMENT,
            FragmentParser.START: 5,
            FragmentParser.STOP: 20
        }
        self.assertEqual(expected, result.asDict())

    def test_unknown_length(self):
        """amino-terminal fragment of unknown length"""
        s = 'frag(1_?)'
        result = self.parser.parseString(s)
        expected = {
            KIND: FRAGMENT,
            FragmentParser.START: 1,
            FragmentParser.STOP: '?'
        }
        self.assertEqual(expected, result.asDict())

    def test_unknown_start_stop(self):
        """fragment with unknown start/stop"""
        s = 'frag(?_*)'
        result = self.parser.parseString(s)
        expected = {
            KIND: FRAGMENT,
            FragmentParser.START: '?',
            FragmentParser.STOP: '*'
        }
        self.assertEqual(expected, result.asDict())

    def test_descriptor(self):
        """fragment with unknown start/stop and a descriptor"""
        s = 'frag(?, 55kD)'
        result = self.parser.parseString(s)
        expected = {
            KIND: FRAGMENT,
            FragmentParser.MISSING: '?',
            FragmentParser.DESCRIPTION: '55kD'
        }
        self.assertEqual(expected, result.asDict())


class TestTruncationParser(unittest.TestCase):
    def setUp(self):
        self.parser = TruncParser()

    def test_trunc_1(self):
        statement = 'trunc(40)'
        result = self.parser.parseString(statement)

        expected = build_variant_dict('p.40*')
        self.assertEqual(expected, result.asDict())


class TestFusionParser(unittest.TestCase):
    def setUp(self):
        self.parser = FusionParser()

    def test_rna_fusion_known_breakpoints(self):
        """RNA abundance of fusion with known breakpoints"""
        statement = 'fus(HGNC:TMPRSS2, r.1_79, HGNC:ERG, r.312_5034)'
        result = self.parser.parseString(statement)

        expected = {
            PARTNER_5P: {
                NAMESPACE: 'HGNC',
                NAME: 'TMPRSS2'
            },
            RANGE_5P: {
                FusionParser.REFERENCE: 'r',
                FusionParser.START: 1,
                FusionParser.STOP: 79

            },
            PARTNER_3P: {
                NAMESPACE: 'HGNC',
                NAME: 'ERG'
            },
            RANGE_3P: {
                FusionParser.REFERENCE: 'r',
                FusionParser.START: 312,
                FusionParser.STOP: 5034
            }
        }

        self.assertEqual(expected, result.asDict())

    def test_rna_fusion_unspecified_breakpoints(self):
        """RNA abundance of fusion with unspecified breakpoints"""
        statement = 'fus(HGNC:TMPRSS2, ?, HGNC:ERG, ?)'
        result = self.parser.parseString(statement)

        expected = {
            PARTNER_5P: {
                NAMESPACE: 'HGNC',
                NAME: 'TMPRSS2'
            },
            RANGE_5P: {
                FusionParser.MISSING: '?'

            },
            PARTNER_3P: {
                NAMESPACE: 'HGNC',
                NAME: 'ERG'
            },
            RANGE_3P: {
                FusionParser.MISSING: '?'
            }
        }

        self.assertEqual(expected, result.asDict())

    def test_rna_fusion_specified_one_fuzzy_breakpoint(self):
        """RNA abundance of fusion with unspecified breakpoints"""
        statement = 'fusion(HGNC:TMPRSS2, r.1_79, HGNC:ERG, r.?_1)'
        result = self.parser.parseString(statement)

        expected = {
            PARTNER_5P: {
                NAMESPACE: 'HGNC',
                NAME: 'TMPRSS2'
            },
            RANGE_5P: {
                FusionParser.REFERENCE: 'r',
                FusionParser.START: 1,
                FusionParser.STOP: 79

            },
            PARTNER_3P: {
                NAMESPACE: 'HGNC',
                NAME: 'ERG'
            },
            RANGE_3P: {
                FusionParser.REFERENCE: 'r',
                FusionParser.START: '?',
                FusionParser.STOP: 1
            }
        }

        self.assertEqual(expected, result.asDict())

    def test_rna_fusion_specified_fuzzy_breakpoints(self):
        """RNA abundance of fusion with unspecified breakpoints"""
        statement = 'fusion(HGNC:TMPRSS2, r.1_?, HGNC:ERG, r.?_1)'
        result = self.parser.parseString(statement)

        expected = {
            PARTNER_5P: {
                NAMESPACE: 'HGNC',
                NAME: 'TMPRSS2'
            },
            RANGE_5P: {
                FusionParser.REFERENCE: 'r',
                FusionParser.START: 1,
                FusionParser.STOP: '?'

            },
            PARTNER_3P: {
                NAMESPACE: 'HGNC',
                NAME: 'ERG'
            },
            RANGE_3P: {
                FusionParser.REFERENCE: 'r',
                FusionParser.START: '?',
                FusionParser.STOP: 1
            }
        }

        self.assertEqual(expected, result.asDict())


class TestLocation(unittest.TestCase):
    def setUp(self):
        self.parser = LocationParser()

    def test_a(self):
        statement = 'loc(GOCC:intracellular)'
        result = self.parser.parseString(statement)
        expected = {
            LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}
        }
        self.assertEqual(expected, result.asDict())


class TestAbundance(TestTokenParserBase):
    """2.1.1"""

    def setUp(self):
        self.parser.clear()
        self.parser.general_abundance.setParseAction(self.parser.handle_term)

    def test_short_abundance(self):
        """small molecule"""
        statement = 'a(CHEBI:"oxygen atom")'

        result = self.parser.general_abundance.parseString(statement)

        expected_result = {
            FUNCTION: ABUNDANCE,
            IDENTIFIER: {NAMESPACE: 'CHEBI', NAME: 'oxygen atom'}
        }

        self.assertEqual(expected_result, result.asDict())

        node = canonicalize_node(result)
        expected_node = cls, ns, val = ABUNDANCE, 'CHEBI', 'oxygen atom'
        self.assertEqual(expected_node, node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'a(CHEBI:"oxygen atom")'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        expected_modifier = {}
        self.assertEqual(expected_modifier, canonicalize_modifier(result))

        self.assertHasNode(node, **{FUNCTION: cls, NAMESPACE: ns, NAME: val})

    def test_long_abundance(self):
        """small molecule"""
        statement = 'abundance(CHEBI:"oxygen atom", loc(GOCC:intracellular))'

        result = self.parser.general_abundance.parseString(statement)

        expected_result = {
            FUNCTION: ABUNDANCE,
            IDENTIFIER: {NAMESPACE: 'CHEBI', NAME: 'oxygen atom'},
            LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}
        }

        self.assertEqual(expected_result, result.asDict())

        node = canonicalize_node(result)
        expected_node = cls, ns, val = ABUNDANCE, 'CHEBI', 'oxygen atom'
        self.assertEqual(expected_node, node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'a(CHEBI:"oxygen atom")'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        modifier = canonicalize_modifier(result)
        expected_modifier = {
            LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}
        }
        self.assertEqual(expected_modifier, modifier)

        self.assertHasNode(node, **{FUNCTION: cls, NAMESPACE: ns, NAME: val})


class TestGene(TestTokenParserBase):
    """2.1.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XgeneA"""

    def setUp(self):
        self.parser.clear()
        self.parser.gene.setParseAction(self.parser.handle_term)

    def test_214a(self):
        statement = 'g(HGNC:AKT1)'

        result = self.parser.gene.parseString(statement)
        expected_list = [GENE, ['HGNC', 'AKT1']]
        self.assertEqual(expected_list, result.asList())

        expected_dict = {
            FUNCTION: GENE,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        expected_node = cls, ns, val = GENE, 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'g(HGNC:AKT1)'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        self.assertEqual(1, len(self.parser.graph))
        self.assertHasNode(node, **{FUNCTION: cls, NAMESPACE: ns, NAME: val})

    def test_214b(self):
        statement = 'g(HGNC:AKT1, loc(GOCC:intracellular))'

        result = self.parser.gene.parseString(statement)

        expected_dict = {
            FUNCTION: GENE,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            },
            LOCATION: {
                NAMESPACE: 'GOCC',
                NAME: 'intracellular'
            }
        }

        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        expected_node = cls, ns, val = GENE, 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'g(HGNC:AKT1)'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        self.assertHasNode(node, **{FUNCTION: cls, NAMESPACE: ns, NAME: val})

    def test_214c(self):
        """Test variant"""
        statement = 'g(HGNC:AKT1, var(p.Phe508del))'
        result = self.parser.gene.parseString(statement)

        expected_result = {
            FUNCTION: GENE,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            },
            VARIANTS: [
                {
                    KIND: HGVS,
                    IDENTIFIER: TEST_PROTEIN_VARIANT
                }
            ]

        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = GENE, 'HGNC', 'AKT1', (HGVS, TEST_PROTEIN_VARIANT)
        self.assertEqual(expected_node, canonicalize_node(result))

        self.assertEqual(self.parser.graph.node[expected_node], {
            FUNCTION: GENE,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1',
            VARIANTS: [
                {
                    KIND: HGVS,
                    IDENTIFIER: 'p.Phe508del'
                }
            ]
        })

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'g(HGNC:AKT1, var(p.Phe508del))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        parent = GENE, 'HGNC', 'AKT1'
        self.assertHasNode(parent, **{FUNCTION: GENE, NAMESPACE: 'HGNC', NAME: 'AKT1'})
        self.assertHasEdge(parent, expected_node, relation='hasVariant')

    def test_gmod(self):
        """Test Gene Modification"""
        statement = 'geneAbundance(HGNC:AKT1,gmod(M))'
        result = self.parser.gene.parseString(statement)

        expected_result = {
            FUNCTION: GENE,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            },
            VARIANTS: [
                {
                    KIND: GMOD,
                    IDENTIFIER: default_identifier('Me')
                }
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = GENE, 'HGNC', 'AKT1', (GMOD, (BEL_DEFAULT_NAMESPACE, 'Me'))
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: GENE})

        self.assertEqual('g(HGNC:AKT1, gmod(Me))', decanonicalize_node(self.parser.graph, expected_node))

        parent = GENE, 'HGNC', 'AKT1'
        self.assertHasNode(parent, **{FUNCTION: GENE, NAMESPACE: 'HGNC', NAME: 'AKT1'})

        self.assertHasEdge(parent, expected_node, relation='hasVariant')

    def test_214d(self):
        """Test BEL 1.0 gene substitution"""
        statement = 'g(HGNC:AKT1,sub(G,308,A))'
        result = self.parser.gene.parseString(statement)

        expected_result = {
            FUNCTION: GENE,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            },
            VARIANTS: [
                {
                    KIND: HGVS,
                    IDENTIFIER: TEST_GENE_VARIANT
                }
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, **{FUNCTION: GENE})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'g(HGNC:AKT1, var(c.308G>A))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        parent = GENE, 'HGNC', 'AKT1'
        self.assertHasNode(parent, **{FUNCTION: GENE, NAMESPACE: 'HGNC', NAME: 'AKT1'})

        self.assertHasEdge(parent, expected_node, relation='hasVariant')

    def test_variant_location(self):
        """Test BEL 1.0 gene substitution with location tag"""
        statement = 'g(HGNC:AKT1,sub(G,308,A),loc(GOCC:intracellular))'
        result = self.parser.gene.parseString(statement)

        expected_result = {
            FUNCTION: GENE,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            },
            VARIANTS: [
                {
                    KIND: HGVS,
                    IDENTIFIER: TEST_GENE_VARIANT
                }
            ],
            LOCATION: {
                NAMESPACE: 'GOCC',
                NAME: 'intracellular'
            }
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, **{FUNCTION: GENE, NAMESPACE: 'HGNC', NAME: 'AKT1'})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'g(HGNC:AKT1, var(c.308G>A))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        parent = GENE, 'HGNC', 'AKT1'
        self.assertHasNode(parent, **{FUNCTION: GENE, NAMESPACE: 'HGNC', NAME: 'AKT1'})

        self.assertHasEdge(parent, expected_node, relation='hasVariant')

    def test_multiple_variants(self):
        """Test multiple variants"""
        statement = 'g(HGNC:AKT1, var(p.Phe508del), sub(G,308,A), var(c.1521_1523delCTT))'
        result = self.parser.gene.parseString(statement)

        expected_result = {
            FUNCTION: GENE,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            },
            VARIANTS: [
                build_variant_dict(TEST_PROTEIN_VARIANT),
                build_variant_dict(TEST_GENE_VARIANT),
                build_variant_dict('c.1521_1523delCTT')
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = (
            GENE, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, TEST_GENE_VARIANT), (HGVS, TEST_PROTEIN_VARIANT))
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, function=GENE)
        self.assertEqual(decanonicalize_node(self.parser.graph, expected_node),
                         'g(HGNC:AKT1, var(c.1521_1523delCTT), var(c.308G>A), var(p.Phe508del))')

        parent = GENE, 'HGNC', 'AKT1'
        self.assertHasNode(parent, **{FUNCTION: GENE, NAMESPACE: 'HGNC', NAME: 'AKT1'})

        self.assertHasEdge(parent, expected_node, relation='hasVariant')

    def test_gene_fusion_1(self):
        self.maxDiff = None
        statement = 'g(fus(HGNC:TMPRSS2, c.1_79, HGNC:ERG, c.312_5034))'
        result = self.parser.gene.parseString(statement)
        expected_dict = {
            FUNCTION: GENE,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'TMPRSS2'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'ERG'},
                RANGE_5P: {
                    FusionParser.REFERENCE: 'c',
                    FusionParser.START: 1,
                    FusionParser.STOP: 79

                },
                RANGE_3P: {
                    FusionParser.REFERENCE: 'c',
                    FusionParser.START: 312,
                    FusionParser.STOP: 5034
                }
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = GENE, ('HGNC', 'TMPRSS2'), ('c', 1, 79), ('HGNC', 'ERG'), ('c', 312, 5034)
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node)

        self.assertEqual(expected_dict, self.parser.graph.node[expected_node])

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_gene_fusion_2(self):
        self.maxDiff = None
        statement = 'g(fus(HGNC:TMPRSS2, c.1_?, HGNC:ERG, c.312_5034))'
        result = self.parser.gene.parseString(statement)
        expected_dict = {
            FUNCTION: GENE,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'TMPRSS2'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'ERG'},
                RANGE_5P: {
                    FusionParser.REFERENCE: 'c',
                    FusionParser.START: 1,
                    FusionParser.STOP: '?'

                },
                RANGE_3P: {
                    FusionParser.REFERENCE: 'c',
                    FusionParser.START: 312,
                    FusionParser.STOP: 5034
                }
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = GENE, ('HGNC', 'TMPRSS2'), ('c', 1, '?'), ('HGNC', 'ERG'), ('c', 312, 5034)
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node)

        self.assertEqual(expected_dict, self.parser.graph.node[expected_node])

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_gene_fusion_3(self):
        self.maxDiff = None
        statement = 'g(fus(HGNC:TMPRSS2, ?, HGNC:ERG, c.312_5034))'
        result = self.parser.gene.parseString(statement)
        expected_dict = {
            FUNCTION: GENE,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'TMPRSS2'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'ERG'},
                RANGE_5P: {
                    FusionParser.MISSING: '?'
                },
                RANGE_3P: {
                    FusionParser.REFERENCE: 'c',
                    FusionParser.START: 312,
                    FusionParser.STOP: 5034
                }
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = GENE, ('HGNC', 'TMPRSS2'), ('?',), ('HGNC', 'ERG'), ('c', 312, 5034)
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node)

        self.assertEqual(expected_dict, self.parser.graph.node[expected_node])

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_gene_fusion_legacy_1(self):
        self.maxDiff = None
        statement = 'g(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626))'
        result = self.parser.gene.parseString(statement)

        expected_dict = {
            FUNCTION: GENE,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'BCR'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'JAK2'},
                RANGE_5P: {
                    FusionParser.REFERENCE: 'c',
                    FusionParser.START: '?',
                    FusionParser.STOP: 1875

                },
                RANGE_3P: {
                    FusionParser.REFERENCE: 'c',
                    FusionParser.START: 2626,
                    FusionParser.STOP: '?'
                }
            }
        }

        self.assertEqual(expected_dict, result.asDict())
        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        expected_node = GENE, ('HGNC', 'BCR'), ('c', '?', 1875), ('HGNC', 'JAK2'), ('c', 2626, '?')
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node)

        self.assertEqual(expected_dict, self.parser.graph.node[expected_node])

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'g(fus(HGNC:BCR, c.?_1875, HGNC:JAK2, c.2626_?))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_gene_fusion_legacy_2(self):
        statement = 'g(HGNC:CHCHD4, fusion(HGNC:AIFM1))'
        result = self.parser.gene.parseString(statement)

        expected_dict = {
            FUNCTION: GENE,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'CHCHD4'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'AIFM1'},
                RANGE_5P: {FusionParser.MISSING: '?'},
                RANGE_3P: {FusionParser.MISSING: '?'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())
        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        expected_node = GENE, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node)

        self.assertEqual(expected_dict, self.parser.graph.node[expected_node])

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'g(fus(HGNC:CHCHD4, ?, HGNC:AIFM1, ?))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_gene_variant_snp(self):
        """2.2.2 SNP"""
        statement = 'g(SNP:rs113993960, var(c.1521_1523delCTT))'
        result = self.parser.gene.parseString(statement)

        expected_result = [GENE, ['SNP', 'rs113993960'], [HGVS, 'c.1521_1523delCTT']]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'g(SNP:rs113993960, var(c.1521_1523delCTT))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        gene_node = GENE, 'SNP', 'rs113993960'
        self.assertHasNode(gene_node, **{FUNCTION: GENE, NAMESPACE: 'SNP', NAME: 'rs113993960'})

        self.assertHasEdge(gene_node, expected_node, relation='hasVariant')

    def test_gene_variant_chromosome(self):
        """2.2.2 chromosome"""
        statement = 'g(REF:"NC_000007.13", var(g.117199646_117199648delCTT))'
        result = self.parser.gene.parseString(statement)

        expected_result = [GENE, ['REF', 'NC_000007.13'], [HGVS, 'g.117199646_117199648delCTT']]
        self.assertEqual(expected_result, result.asList())

        gene_node = GENE, 'REF', 'NC_000007.13'
        expected_node = canonicalize_node(result)

        self.assertHasNode(gene_node, **{FUNCTION: GENE, NAMESPACE: 'REF', NAME: 'NC_000007.13'})
        self.assertHasNode(expected_node, function=GENE)
        self.assertHasEdge(gene_node, expected_node, relation='hasVariant')

    def test_gene_variant_deletion(self):
        """2.2.2 gene-coding DNA reference sequence"""
        statement = 'g(HGNC:CFTR, var(c.1521_1523delCTT))'
        result = self.parser.gene.parseString(statement)

        expected_result = {
            FUNCTION: GENE,
            IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'CFTR'},
            VARIANTS: [
                {KIND: HGVS, IDENTIFIER: 'c.1521_1523delCTT'}
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT'))
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, function=GENE)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        gene_node = GENE, 'HGNC', 'CFTR'
        self.assertHasNode(gene_node, **{FUNCTION: GENE, NAMESPACE: 'HGNC', NAME: 'CFTR'})

        self.assertHasEdge(gene_node, expected_node, relation='hasVariant')


class TestMiRNA(TestTokenParserBase):
    """2.1.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XmicroRNAA"""

    def setUp(self):
        self.parser.clear()
        self.parser.mirna.setParseAction(self.parser.handle_term)

    def test_short(self):
        statement = 'm(HGNC:MIR21)'
        result = self.parser.mirna.parseString(statement)
        expected_result = [MIRNA, ['HGNC', 'MIR21']]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            FUNCTION: MIRNA,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'MIR21'
            }
        }

        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        expected_node = MIRNA, 'HGNC', 'MIR21'
        self.assertEqual(expected_node, node)

        self.assertHasNode(node)

    def test_long(self):
        statement = 'microRNAAbundance(HGNC:MIR21)'
        result = self.parser.mirna.parseString(statement)
        expected_result = [MIRNA, ['HGNC', 'MIR21']]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            FUNCTION: MIRNA,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'MIR21'
            }
        }

        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        expected_node = MIRNA, 'HGNC', 'MIR21'
        self.assertEqual(expected_node, node)

        self.assertHasNode(node)

    def test_mirna_location(self):
        statement = 'm(HGNC:MIR21,loc(GOCC:intracellular))'
        result = self.parser.mirna.parseString(statement)

        expected_dict = {
            FUNCTION: MIRNA,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'MIR21'
            },
            LOCATION: {
                NAMESPACE: 'GOCC',
                NAME: 'intracellular'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        expected_node = MIRNA, 'HGNC', 'MIR21'
        self.assertEqual(expected_node, node)

        self.assertHasNode(node)

    def test_mirna_variant(self):
        statement = 'm(HGNC:MIR21,var(p.Phe508del))'
        result = self.parser.mirna.parseString(statement)

        expected_dict = {
            FUNCTION: MIRNA,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'MIR21'
            },
            VARIANTS: [
                {
                    KIND: HGVS,
                    IDENTIFIER: TEST_PROTEIN_VARIANT
                },
            ]
        }
        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        self.assertHasNode(node)

        self.assertEqual(2, self.parser.graph.number_of_nodes())

        expected_parent = MIRNA, 'HGNC', 'MIR21'
        self.assertHasNode(expected_parent)

        self.assertHasEdge(expected_parent, node, relation='hasVariant')

    def test_mirna_variant_location(self):
        statement = 'm(HGNC:MIR21,var(p.Phe508del),loc(GOCC:intracellular))'
        result = self.parser.mirna.parseString(statement)

        expected_dict = {
            FUNCTION: MIRNA,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'MIR21'
            },
            VARIANTS: [
                {
                    KIND: HGVS,
                    IDENTIFIER: 'p.Phe508del'
                },
            ],
            LOCATION: {
                NAMESPACE: 'GOCC',
                NAME: 'intracellular'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        self.assertHasNode(node)

        self.assertEqual(2, self.parser.graph.number_of_nodes())

        expected_parent = MIRNA, 'HGNC', 'MIR21'
        self.assertHasNode(expected_parent)

        self.assertHasEdge(expected_parent, node, relation='hasVariant')


class TestProtein(TestTokenParserBase):
    """2.1.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XproteinA"""

    def setUp(self):
        self.parser.clear()
        self.parser.protein.setParseAction(self.parser.handle_term)

    def test_216a(self):
        statement = 'p(HGNC:AKT1)'

        result = self.parser.protein.parseString(statement)
        expected_result = [PROTEIN, ['HGNC', 'AKT1']]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            FUNCTION: PROTEIN,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        expected_node = PROTEIN, 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)
        self.assertHasNode(node)

        canonical_bel = decanonicalize_node(self.parser.graph, node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_protein_wLocation(self):
        statement = 'p(HGNC:AKT1, loc(GOCC:intracellular))'

        result = self.parser.protein.parseString(statement)

        expected_dict = {
            FUNCTION: PROTEIN,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            },
            LOCATION: {
                NAMESPACE: 'GOCC',
                NAME: 'intracellular'
            }
        }

        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        expected_node = PROTEIN, 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)
        self.assertHasNode(node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'AKT1'})

        canonical_bel = decanonicalize_node(self.parser.graph, node)
        expected_canonical_bel = 'p(HGNC:AKT1)'
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_multiVariant(self):
        statement = 'p(HGNC:AKT1,sub(A,127,Y),pmod(Ph, Ser),loc(GOCC:intracellular))'

        result = self.parser.protein.parseString(statement)

        expected_dict = {
            FUNCTION: PROTEIN,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            },
            LOCATION: {
                NAMESPACE: 'GOCC',
                NAME: 'intracellular'
            },
            VARIANTS: [
                {
                    KIND: HGVS,
                    IDENTIFIER: 'p.Ala127Tyr'
                },
                {
                    KIND: PMOD,
                    IDENTIFIER: default_identifier('Ph'),
                    'code': 'Ser'
                }
            ]
        }

        self.assertEqual(expected_dict, result.asDict())

        node = (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Ala127Tyr'), (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser'))
        self.assertEqual(node, canonicalize_node(result))
        self.assertHasNode(node, function=PROTEIN)

        canonical_bel = decanonicalize_node(self.parser.graph, node)
        expected_canonical_bel = 'p(HGNC:AKT1, pmod(Ph, Ser), var(p.Ala127Tyr))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        parent = PROTEIN, 'HGNC', 'AKT1'
        self.assertHasNode(parent, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'AKT1'})
        self.assertHasEdge(parent, node, relation='hasVariant')

    def test_protein_fusion_1(self):
        statement = 'p(fus(HGNC:TMPRSS2, p.1_79, HGNC:ERG, p.312_5034))'
        result = self.parser.protein.parseString(statement)
        expected_dict = {
            FUNCTION: PROTEIN,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'TMPRSS2'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'ERG'},
                RANGE_5P: {
                    FusionParser.REFERENCE: 'p',
                    FusionParser.START: 1,
                    FusionParser.STOP: 79

                },
                RANGE_3P: {
                    FusionParser.REFERENCE: 'p',
                    FusionParser.START: 312,
                    FusionParser.STOP: 5034

                }
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = PROTEIN, ('HGNC', 'TMPRSS2'), ('p', 1, 79), ('HGNC', 'ERG'), ('p', 312, 5034)
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_protein_fusion_legacy_1(self):
        self.maxDiff = None
        statement = 'p(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626))'
        result = self.parser.protein.parseString(statement)

        expected_dict = {
            FUNCTION: PROTEIN,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'BCR'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'JAK2'},
                RANGE_5P: {
                    FusionParser.REFERENCE: 'p',
                    FusionParser.START: '?',
                    FusionParser.STOP: 1875

                },
                RANGE_3P: {
                    FusionParser.REFERENCE: 'p',
                    FusionParser.START: 2626,
                    FusionParser.STOP: '?'

                }
            }
        }

        self.assertEqual(expected_dict, result.asDict())
        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'p(fus(HGNC:BCR, p.?_1875, HGNC:JAK2, p.2626_?))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_protein_fusion_legacy_2(self):
        statement = 'p(HGNC:CHCHD4, fusion(HGNC:AIFM1))'
        result = self.parser.protein.parseString(statement)

        expected_dict = {
            FUNCTION: PROTEIN,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'CHCHD4'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'AIFM1'},
                RANGE_5P: {FusionParser.MISSING: '?'},
                RANGE_3P: {FusionParser.MISSING: '?'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = PROTEIN, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'p(fus(HGNC:CHCHD4, ?, HGNC:AIFM1, ?))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_protein_trunc_1(self):
        statement = 'p(HGNC:AKT1, trunc(40))'
        result = self.parser.protein.parseString(statement)

        expected_node = PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.40*')
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: PROTEIN})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'p(HGNC:AKT1, var(p.40*))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = PROTEIN, 'HGNC', 'AKT1'
        self.assertHasNode(protein_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'AKT1'})

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_trunc_2(self):
        statement = 'p(HGNC:AKT1, var(p.Cys40*))'
        result = self.parser.protein.parseString(statement)

        expected_result = [PROTEIN, ['HGNC', 'AKT1'], [HGVS, 'p.Cys40*']]
        self.assertEqual(expected_result, result.asList())

        expected_node = PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Cys40*')
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'AKT1'})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'p(HGNC:AKT1, var(p.Cys40*))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = cls, ns, val = PROTEIN, 'HGNC', 'AKT1'
        self.assertHasNode(protein_node, **{FUNCTION: PROTEIN, NAMESPACE: ns, NAME: val})

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_trunc_3(self):
        statement = 'p(HGNC:AKT1, var(p.Arg1851*))'
        result = self.parser.protein.parseString(statement)

        expected_result = [PROTEIN, ['HGNC', 'AKT1'], [HGVS, 'p.Arg1851*']]
        self.assertEqual(expected_result, result.asList())

        expected_node = PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Arg1851*')
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'AKT1'})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = cls, ns, val = PROTEIN, 'HGNC', 'AKT1'
        self.assertHasNode(protein_node, **{FUNCTION: PROTEIN, NAMESPACE: ns, NAME: val})

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_pmod_1(self):
        """2.2.1 Test default BEL namespace and 1-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(Ph, S, 473))'
        result = self.parser.protein.parseString(statement)

        expected_node = (PROTEIN, 'HGNC', 'AKT1', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 473))
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'AKT1'})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'p(HGNC:AKT1, pmod(Ph, Ser, 473))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = PROTEIN, 'HGNC', 'AKT1'
        self.assertHasNode(protein_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'AKT1'})
        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_pmod_2(self):
        """2.2.1 Test default BEL namespace and 3-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(Ph, Ser, 473))'
        result = self.parser.protein.parseString(statement)

        expected_node = PROTEIN, 'HGNC', 'AKT1', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 473)
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: PROTEIN})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'p(HGNC:AKT1, pmod(Ph, Ser, 473))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = PROTEIN, 'HGNC', 'AKT1'
        self.assertHasNode(protein_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'AKT1'})

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_pmod_3(self):
        """2.2.1 Test PSI-MOD namespace and 3-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(MOD:PhosRes, Ser, 473))'
        result = self.parser.protein.parseString(statement)

        expected_node = PROTEIN, 'HGNC', 'AKT1', (PMOD, ('MOD', 'PhosRes'), 'Ser', 473)
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = PROTEIN, 'HGNC', 'AKT1'
        self.assertHasNode(protein_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'AKT1'})

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_pmod_4(self):
        """2.2.1 Test HRAS palmitoylated at an unspecified residue. Default BEL namespace"""
        statement = 'p(HGNC:HRAS, pmod(Palm))'
        result = self.parser.protein.parseString(statement)

        expected_node = PROTEIN, 'HGNC', 'HRAS', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Palm'))
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: PROTEIN})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = PROTEIN, 'HGNC', 'HRAS'
        self.assertHasNode(protein_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'HRAS'})

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_variant_reference(self):
        """2.2.2 Test reference allele"""
        statement = 'p(HGNC:CFTR, var(=))'
        result = self.parser.protein.parseString(statement)
        expected_result = [PROTEIN, ['HGNC', 'CFTR'], [HGVS, '=']]
        self.assertEqual(expected_result, result.asList())

        expected_node = PROTEIN, 'HGNC', 'CFTR', (HGVS, '=')
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: PROTEIN})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = PROTEIN, 'HGNC', 'CFTR'
        self.assertHasNode(protein_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'CFTR'})

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_variant_unspecified(self):
        """2.2.2 Test unspecified variant"""
        statement = 'p(HGNC:CFTR, var(?))'
        result = self.parser.protein.parseString(statement)

        expected_result = [PROTEIN, ['HGNC', 'CFTR'], [HGVS, '?']]
        self.assertEqual(expected_result, result.asList())

        expected_node = PROTEIN, 'HGNC', 'CFTR', (HGVS, '?')
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: PROTEIN})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = PROTEIN, 'HGNC', 'CFTR'
        self.assertHasNode(protein_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'CFTR'})

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_variant_substitution(self):
        """2.2.2 Test substitution"""
        statement = 'p(HGNC:CFTR, var(p.Gly576Ala))'
        result = self.parser.protein.parseString(statement)
        expected_result = [PROTEIN, ['HGNC', 'CFTR'], [HGVS, 'p.Gly576Ala']]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, **{FUNCTION: PROTEIN})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = PROTEIN, 'HGNC', 'CFTR'
        self.assertHasNode(protein_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'CFTR'})

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_variant_deletion(self):
        """2.2.2 deletion"""
        statement = 'p(HGNC:CFTR, var(p.Phe508del))'
        result = self.parser.protein.parseString(statement)

        expected_result = [PROTEIN, ['HGNC', 'CFTR'], [HGVS, TEST_PROTEIN_VARIANT]]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = PROTEIN, 'HGNC', 'CFTR'
        self.assertHasNode(protein_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'CFTR'})

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_fragment_known(self):
        """2.2.3 fragment with known start/stop"""
        statement = 'p(HGNC:YFG, frag(5_20))'
        result = self.parser.protein.parseString(statement)

        expected_node = PROTEIN, 'HGNC', 'YFG', (FRAGMENT, (5, 20))
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: PROTEIN})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = PROTEIN, 'HGNC', 'YFG'
        self.assertHasNode(protein_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'YFG'})

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_fragment_unbounded(self):
        """2.2.3 amino-terminal fragment of unknown length"""
        statement = 'p(HGNC:YFG, frag(1_?))'
        result = self.parser.protein.parseString(statement)

        expected_node = PROTEIN, 'HGNC', 'YFG', (FRAGMENT, (1, '?'))
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: PROTEIN})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = PROTEIN, 'HGNC', 'YFG'
        self.assertHasNode(protein_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'YFG'})

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_fragment_unboundTerminal(self):
        """2.2.3 carboxyl-terminal fragment of unknown length"""
        statement = 'p(HGNC:YFG, frag(?_*))'
        result = self.parser.protein.parseString(statement)

        expected_node = PROTEIN, 'HGNC', 'YFG', (FRAGMENT, ('?', '*'))
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: PROTEIN})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = PROTEIN, 'HGNC', 'YFG'
        self.assertHasNode(protein_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'YFG'})

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_fragment_unknown(self):
        """2.2.3 fragment with unknown start/stop"""
        statement = 'p(HGNC:YFG, frag(?))'
        result = self.parser.protein.parseString(statement)

        expected_result = [PROTEIN, ['HGNC', 'YFG'], [FRAGMENT, '?']]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, **{FUNCTION: PROTEIN})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = PROTEIN, 'HGNC', 'YFG'
        self.assertHasNode(protein_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'YFG'})

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_fragment_descriptor(self):
        """2.2.3 fragment with unknown start/stop and a descriptor"""
        statement = 'p(HGNC:YFG, frag(?, 55kD))'
        result = self.parser.protein.parseString(statement)

        expected_node = PROTEIN, 'HGNC', 'YFG', (FRAGMENT, '?', '55kD')
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: PROTEIN})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = PROTEIN, 'HGNC', 'YFG'
        self.assertHasNode(protein_node, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'YFG'})

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_complete_origin(self):
        """"""
        statement = 'p(HGNC:AKT1)'
        result = self.parser.protein.parseString(statement)

        expected_result = [PROTEIN, ['HGNC', 'AKT1']]
        self.assertEqual(expected_result, result.asList())

        protein = PROTEIN, 'HGNC', 'AKT1'
        rna = RNA, 'HGNC', 'AKT1'
        gene = GENE, 'HGNC', 'AKT1'

        self.assertHasNode(protein, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'AKT1'})
        self.assertHasNode(rna, **{FUNCTION: RNA, NAMESPACE: 'HGNC', NAME: 'AKT1'})
        self.assertHasNode(gene, **{FUNCTION: GENE, NAMESPACE: 'HGNC', NAME: 'AKT1'})

        self.assertEqual(2, self.parser.graph.number_of_edges())

        self.assertHasEdge(gene, rna, relation='transcribedTo')
        self.assertEqual(1, self.parser.graph.number_of_edges(gene, rna))

        self.assertHasEdge(rna, protein, relation=TRANSLATED_TO)
        self.assertEqual(1, self.parser.graph.number_of_edges(rna, protein))

    def test_ensure_no_dup_nodes(self):
        """Ensure node isn't added twice, even if from different statements"""
        s1 = 'g(HGNC:AKT1)'
        s2 = 'deg(g(HGNC:AKT1))'

        self.parser.bel_term.parseString(s1)
        self.parser.bel_term.parseString(s2)

        gene = GENE, 'HGNC', 'AKT1'

        self.assertEqual(1, self.parser.graph.number_of_nodes())
        self.assertHasNode(gene, **{FUNCTION: GENE, NAMESPACE: 'HGNC', NAME: 'AKT1'})

    def test_ensure_no_dup_edges(self):
        """Ensure node and edges aren't added twice, even if from different statements and has origin completion"""
        s1 = 'p(HGNC:AKT1)'
        s2 = 'deg(p(HGNC:AKT1))'

        self.parser.bel_term.parseString(s1)
        self.parser.bel_term.parseString(s2)

        protein = PROTEIN, 'HGNC', 'AKT1'
        rna = RNA, 'HGNC', 'AKT1'
        gene = GENE, 'HGNC', 'AKT1'

        self.assertEqual(3, self.parser.graph.number_of_nodes())
        self.assertHasNode(protein, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'AKT1'})
        self.assertHasNode(rna, **{FUNCTION: RNA, NAMESPACE: 'HGNC', NAME: 'AKT1'})
        self.assertHasNode(gene, **{FUNCTION: GENE, NAMESPACE: 'HGNC', NAME: 'AKT1'})

        self.assertEqual(2, self.parser.graph.number_of_edges())

        self.assertHasEdge(gene, rna, relation='transcribedTo')
        self.assertEqual(1, self.parser.graph.number_of_edges(gene, rna))

        self.assertHasEdge(rna, protein, relation=TRANSLATED_TO)
        self.assertEqual(1, self.parser.graph.number_of_edges(rna, protein))


class TestRna(TestTokenParserBase):
    """2.1.7 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XrnaA"""

    def setUp(self):
        self.parser.clear()
        self.parser.rna.setParseAction(self.parser.handle_term)

    def test_217a(self):
        statement = 'r(HGNC:AKT1)'

        result = self.parser.rna.parseString(statement)
        expected_result = [RNA, ['HGNC', 'AKT1']]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            FUNCTION: RNA,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = RNA, 'HGNC', 'AKT1'
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: RNA, NAMESPACE: 'HGNC', NAME: 'AKT1'})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_214e(self):
        """Test multiple variants"""
        statement = 'r(HGNC:AKT1, var(p.Phe508del), var(c.1521_1523delCTT))'
        result = self.parser.rna.parseString(statement)

        expected_result = {
            FUNCTION: RNA,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            },
            VARIANTS: [
                {
                    KIND: HGVS,
                    IDENTIFIER: TEST_PROTEIN_VARIANT
                },
                {
                    KIND: HGVS,
                    IDENTIFIER: 'c.1521_1523delCTT'
                }
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = (RNA, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, TEST_PROTEIN_VARIANT))
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: RNA})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'r(HGNC:AKT1, var(c.1521_1523delCTT), var(p.Phe508del))'  # sorted
        self.assertEqual(expected_canonical_bel, canonical_bel)

        parent = RNA, 'HGNC', 'AKT1'
        self.assertHasNode(parent, **{FUNCTION: RNA, NAMESPACE: 'HGNC', NAME: 'AKT1'})

        self.assertHasEdge(parent, expected_node, relation='hasVariant')

    def test_rna_fusion_1(self):
        """2.6.1 RNA abundance of fusion with known breakpoints"""
        statement = 'r(fus(HGNC:TMPRSS2, r.1_79, HGNC:ERG, r.312_5034))'
        result = self.parser.rna.parseString(statement)

        expected_dict = {
            FUNCTION: RNA,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'TMPRSS2'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'ERG'},
                RANGE_5P: {
                    FusionParser.REFERENCE: 'r',
                    FusionParser.START: 1,
                    FusionParser.STOP: 79

                },
                RANGE_3P: {
                    FusionParser.REFERENCE: 'r',
                    FusionParser.START: 312,
                    FusionParser.STOP: 5034
                }
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_rna_fusion_2(self):
        """2.6.1 RNA abundance of fusion with unspecified breakpoints"""
        statement = 'r(fus(HGNC:TMPRSS2, ?, HGNC:ERG, ?))'
        result = self.parser.rna.parseString(statement)

        expected_dict = {
            FUNCTION: RNA,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'TMPRSS2'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'ERG'},
                RANGE_5P: {
                    FusionParser.MISSING: '?',
                },
                RANGE_3P: {
                    FusionParser.MISSING: '?',
                }
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = canonicalize_node(result)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_rna_fusion_legacy_1(self):
        statement = 'r(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626))'
        result = self.parser.rna.parseString(statement)

        expected_dict = {
            FUNCTION: RNA,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'BCR'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'JAK2'},
                RANGE_5P: {
                    FusionParser.REFERENCE: 'r',
                    FusionParser.START: '?',
                    FusionParser.STOP: 1875

                },
                RANGE_3P: {
                    FusionParser.REFERENCE: 'r',
                    FusionParser.START: 2626,
                    FusionParser.STOP: '?'
                }
            }

        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'r(fus(HGNC:BCR, r.?_1875, HGNC:JAK2, r.2626_?))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_rna_fusion_legacy_2(self):
        statement = 'r(HGNC:CHCHD4, fusion(HGNC:AIFM1))'
        result = self.parser.rna.parseString(statement)

        expected_dict = {
            FUNCTION: RNA,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'CHCHD4'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'AIFM1'},
                RANGE_5P: {FusionParser.MISSING: '?'},
                RANGE_3P: {FusionParser.MISSING: '?'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'r(fus(HGNC:CHCHD4, ?, HGNC:AIFM1, ?))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_rna_variant_codingReference(self):
        """2.2.2 RNA coding reference sequence"""
        statement = 'r(HGNC:CFTR, var(r.1521_1523delcuu))'
        result = self.parser.rna.parseString(statement)

        expected_dict = {
            FUNCTION: RNA,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'CFTR'
            },
            VARIANTS: [
                {
                    KIND: HGVS,
                    IDENTIFIER: 'r.1521_1523delcuu'
                }
            ]
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        rna_node = RNA, 'HGNC', 'CFTR'
        self.assertHasNode(rna_node, **{FUNCTION: RNA, NAMESPACE: 'HGNC', NAME: 'CFTR'})

        self.assertHasEdge(rna_node, expected_node, relation='hasVariant')


class TestComplex(TestTokenParserBase):
    """2.1.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcomplexA"""

    def setUp(self):
        self.parser.clear()
        self.parser.complex_abundances.setParseAction(self.parser.handle_term)

    def test_complex_singleton(self):
        statement = 'complex(SCOMP:"AP-1 Complex")'
        result = self.parser.complex_abundances.parseString(statement)

        expected_result = [COMPLEX, ['SCOMP', 'AP-1 Complex']]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            FUNCTION: COMPLEX,
            IDENTIFIER: {
                NAMESPACE: 'SCOMP',
                NAME: 'AP-1 Complex'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = COMPLEX, 'SCOMP', 'AP-1 Complex'
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: COMPLEX, NAMESPACE: 'SCOMP', NAME: 'AP-1 Complex'})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_complex_list_short(self):
        statement = 'complex(p(HGNC:FOS), p(HGNC:JUN))'
        result = self.parser.parseString(statement)

        expected_result = [COMPLEX, [PROTEIN, ['HGNC', 'FOS']], [PROTEIN, ['HGNC', 'JUN']]]
        self.assertEqual(expected_result, result.asList())

        expected_result = {
            FUNCTION: COMPLEX,
            'members': [
                {
                    FUNCTION: PROTEIN,
                    IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'FOS'}
                }, {
                    FUNCTION: PROTEIN,
                    IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'JUN'}
                }
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = COMPLEX, (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{FUNCTION: COMPLEX})

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        child_1 = PROTEIN, 'HGNC', 'FOS'
        self.assertHasNode(child_1)
        self.assertHasEdge(expected_node, child_1, relation='hasComponent')

        child_2 = PROTEIN, 'HGNC', 'JUN'
        self.assertHasNode(child_2)
        self.assertHasEdge(expected_node, child_2, relation='hasComponent')

    def test_complex_list_long(self):
        statement = 'complexAbundance(proteinAbundance(HGNC:HBP1),geneAbundance(HGNC:NCF1))'
        self.parser.parseString(statement)


class TestComposite(TestTokenParserBase):
    """2.1.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcompositeA"""

    def setUp(self):
        self.parser.clear()
        self.parser.composite_abundance.setParseAction(self.parser.handle_term)

    def test_213a(self):
        statement = 'composite(p(HGNC:IL6), complex(GOCC:"interleukin-23 complex"))'
        result = self.parser.composite_abundance.parseString(statement)

        expected_result = [COMPOSITE, [PROTEIN, ['HGNC', 'IL6']], [COMPLEX, ['GOCC', 'interleukin-23 complex']]]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            FUNCTION: COMPOSITE,
            'members': [
                {
                    FUNCTION: PROTEIN,
                    IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'IL6'}
                }, {
                    FUNCTION: COMPLEX,
                    IDENTIFIER: {NAMESPACE: 'GOCC', NAME: 'interleukin-23 complex'}
                }
            ]
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = COMPOSITE, (COMPLEX, 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')
        self.assertEqual(expected_node, canonicalize_node(result))

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'composite(complex(GOCC:"interleukin-23 complex"), p(HGNC:IL6))'  # sorted
        self.assertEqual(expected_canonical_bel, canonical_bel)

        self.assertEqual(5, self.parser.graph.number_of_nodes())
        self.assertHasNode(expected_node)
        self.assertHasNode((PROTEIN, 'HGNC', 'IL6'), **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'IL6'})
        self.assertHasNode((RNA, 'HGNC', 'IL6'), **{FUNCTION: RNA, NAMESPACE: 'HGNC', NAME: 'IL6'})
        self.assertHasNode((GENE, 'HGNC', 'IL6'), **{FUNCTION: GENE, NAMESPACE: 'HGNC', NAME: 'IL6'})
        self.assertHasNode((COMPLEX, 'GOCC', 'interleukin-23 complex'), **{
            FUNCTION: COMPLEX,
            NAMESPACE: 'GOCC',
            NAME: 'interleukin-23 complex'
        })

        self.assertEqual(4, self.parser.graph.number_of_edges())


class TestBiologicalProcess(TestTokenParserBase):
    def setUp(self):
        self.parser.clear()
        self.parser.biological_process.setParseAction(self.parser.handle_term)

    def test_231a(self):
        """"""
        statement = 'bp(GOBP:"cell cycle arrest")'
        result = self.parser.biological_process.parseString(statement)

        expected_result = [BIOPROCESS, ['GOBP', 'cell cycle arrest']]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            FUNCTION: BIOPROCESS,
            IDENTIFIER: {NAMESPACE: 'GOBP', NAME: 'cell cycle arrest'}
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = BIOPROCESS, 'GOBP', 'cell cycle arrest'
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{
            FUNCTION: BIOPROCESS,
            NAMESPACE: 'GOBP',
            NAME: 'cell cycle arrest'
        })

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)


class TestPathology(TestTokenParserBase):
    def setUp(self):
        self.parser.clear()
        self.parser.pathology.setParseAction(self.parser.handle_term)

    def test_232a(self):
        statement = 'pathology(MESHD:adenocarcinoma)'
        result = self.parser.pathology.parseString(statement)

        expected_result = [PATHOLOGY, ['MESHD', 'adenocarcinoma']]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            FUNCTION: PATHOLOGY,
            IDENTIFIER: {NAMESPACE: 'MESHD', NAME: 'adenocarcinoma'}
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = PATHOLOGY, 'MESHD', 'adenocarcinoma'
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, **{
            FUNCTION: PATHOLOGY,
            NAMESPACE: 'MESHD',
            NAME: 'adenocarcinoma'
        })

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'path(MESHD:adenocarcinoma)'
        self.assertEqual(expected_canonical_bel, canonical_bel)


class TestActivity(TestTokenParserBase):
    def setUp(self):
        self.parser.clear()
        self.parser.activity.setParseAction(self.parser.handle_term)

    def test_activity_bare(self):
        """"""
        statement = 'act(p(HGNC:AKT1))'
        result = self.parser.activity.parseString(statement)

        expected_result = [ACTIVITY, [PROTEIN, ['HGNC', 'AKT1']]]
        self.assertEqual(expected_result, result.asList())

        mod = canonicalize_modifier(result)
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
                IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'AKT1'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = canonicalize_modifier(result)
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
                IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'AKT1'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = canonicalize_modifier(result)
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
                IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'AKT1'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = canonicalize_modifier(result)
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
                IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'AKT1'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = canonicalize_modifier(result)
        expected_mod = {
            MODIFIER: ACTIVITY,
            EFFECT: {
                NAME: 'kin',
                NAMESPACE: BEL_DEFAULT_NAMESPACE
            }
        }
        self.assertEqual(expected_mod, mod)

        node = PROTEIN, 'HGNC', 'AKT1'
        self.assertEqual(node, canonicalize_node(result))
        self.assertHasNode(node)


class TestTransformation(TestTokenParserBase):
    def setUp(self):
        self.parser.clear()
        self.parser.transformation.setParseAction(self.parser.handle_term)

    def test_degredation_1(self):
        statement = 'deg(p(HGNC:AKT1))'
        result = self.parser.transformation.parseString(statement)

        expected_result = [DEGRADATION, [PROTEIN, ['HGNC', 'AKT1']]]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            MODIFIER: DEGRADATION,
            TARGET: {
                FUNCTION: PROTEIN,
                IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'AKT1'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = canonicalize_modifier(result)
        expected_mod = {
            MODIFIER: DEGRADATION,
        }
        self.assertEqual(expected_mod, mod)

    def test_degradation_2(self):
        """"""
        statement = 'deg(p(HGNC:EGFR))'
        result = self.parser.transformation.parseString(statement)

        expected_result = [DEGRADATION, [PROTEIN, ['HGNC', 'EGFR']]]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            MODIFIER: DEGRADATION,
            TARGET: {
                FUNCTION: PROTEIN,
                IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'EGFR'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = canonicalize_modifier(result)
        expected_mod = {
            MODIFIER: DEGRADATION,
        }
        self.assertEqual(expected_mod, mod)

        node = PROTEIN, 'HGNC', 'EGFR'
        self.assertEqual(node, canonicalize_node(result))
        self.assertHasNode(node)

    def test_translocation_standard(self):
        """translocation example"""
        statement = 'tloc(p(HGNC:EGFR), fromLoc(GOCC:"cell surface"), toLoc(GOCC:endosome))'
        result = self.parser.transformation.parseString(statement)

        expected_dict = {
            MODIFIER: TRANSLOCATION,
            TARGET: {
                FUNCTION: PROTEIN,
                IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'EGFR'}
            },
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'cell surface'},
                TO_LOC: {NAMESPACE: 'GOCC', NAME: 'endosome'}
            }
        }

        self.assertEqual(expected_dict, result.asDict())

        mod = canonicalize_modifier(result)
        expected_mod = {
            MODIFIER: TRANSLOCATION,
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'cell surface'},
                TO_LOC: {NAMESPACE: 'GOCC', NAME: 'endosome'}
            }
        }
        self.assertEqual(expected_mod, mod)

        node = PROTEIN, 'HGNC', 'EGFR'
        self.assertEqual(node, canonicalize_node(result))
        self.assertHasNode(node)

    def test_translocation_bare(self):
        """translocation example"""
        statement = 'tloc(p(HGNC:EGFR), GOCC:"cell surface", GOCC:endosome)'
        result = self.parser.transformation.parseString(statement)

        expected_dict = {
            MODIFIER: TRANSLOCATION,
            TARGET: {
                FUNCTION: PROTEIN,
                IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'EGFR'}
            },
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'cell surface'},
                TO_LOC: {NAMESPACE: 'GOCC', NAME: 'endosome'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = canonicalize_modifier(result)
        expected_mod = {
            MODIFIER: TRANSLOCATION,
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'cell surface'},
                TO_LOC: {NAMESPACE: 'GOCC', NAME: 'endosome'}
            }
        }
        self.assertEqual(expected_mod, mod)

        node = PROTEIN, 'HGNC', 'EGFR'
        self.assertEqual(node, canonicalize_node(result))
        self.assertHasNode(node)

    def test_translocation_invalid(self):
        """Fail on an improperly written single argument translocation"""
        statement = 'tloc(a(NS:"T-Lymphocytes"))'
        with self.assertRaises(MalformedTranslocationWarning):
            self.parser.translocation.parseString(statement)

    def test_translocation_secretion(self):
        """cell secretion short form"""
        statement = 'sec(p(HGNC:EGFR))'
        result = self.parser.transformation.parseString(statement)

        expected_result = ['CellSecretion', [PROTEIN, ['HGNC', 'EGFR']]]
        self.assertEqual(expected_result, result.asList())

        mod = canonicalize_modifier(result)
        expected_mod = {
            MODIFIER: TRANSLOCATION,
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'intracellular'},
                TO_LOC: {NAMESPACE: 'GOCC', NAME: 'extracellular space'}
            }
        }
        self.assertEqual(expected_mod, mod)

        node = PROTEIN, 'HGNC', 'EGFR'
        self.assertEqual(node, canonicalize_node(result))
        self.assertHasNode(node)

    def test_translocation_surface(self):
        """cell surface expression short form"""
        statement = 'surf(p(HGNC:EGFR))'
        result = self.parser.transformation.parseString(statement)

        expected_result = ['CellSurfaceExpression', [PROTEIN, ['HGNC', 'EGFR']]]
        self.assertEqual(expected_result, result.asList())

        expected_mod = {
            MODIFIER: TRANSLOCATION,
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'intracellular'},
                TO_LOC: {NAMESPACE: 'GOCC', NAME: 'cell surface'}
            }
        }
        self.assertEqual(expected_mod, canonicalize_modifier(result))

        node = PROTEIN, 'HGNC', 'EGFR'
        self.assertEqual(node, canonicalize_node(result))
        self.assertHasNode(node)

    def test_reaction_1(self):
        """"""
        statement = 'rxn(reactants(a(CHEBI:superoxide)), products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:oxygen)))'
        result = self.parser.transformation.parseString(statement)

        expected_result = [
            REACTION,
            [[ABUNDANCE, ['CHEBI', 'superoxide']]],
            [[ABUNDANCE, ['CHEBI', 'hydrogen peroxide']], [ABUNDANCE, ['CHEBI', 'oxygen']]]
        ]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            FUNCTION: REACTION,
            REACTANTS: [
                {
                    FUNCTION: ABUNDANCE,
                    IDENTIFIER: {NAMESPACE: 'CHEBI', NAME: 'superoxide'}
                }
            ],
            PRODUCTS: [
                {
                    FUNCTION: ABUNDANCE,
                    IDENTIFIER: {NAMESPACE: 'CHEBI', NAME: 'hydrogen peroxide'}
                }, {

                    FUNCTION: ABUNDANCE,
                    IDENTIFIER: {NAMESPACE: 'CHEBI', NAME: 'oxygen'}
                }

            ]
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = REACTION, ((ABUNDANCE, ('CHEBI', 'superoxide')),), (
            (ABUNDANCE, ('CHEBI', 'hydrogen peroxide')), (ABUNDANCE, ('CHEBI', 'oxygen')))
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        self.assertHasNode((ABUNDANCE, 'CHEBI', 'superoxide'))
        self.assertHasEdge(expected_node, (ABUNDANCE, 'CHEBI', 'superoxide'))

        self.assertHasNode((ABUNDANCE, 'CHEBI', 'hydrogen peroxide'))
        self.assertHasEdge(expected_node, (ABUNDANCE, 'CHEBI', 'hydrogen peroxide'))

        self.assertHasNode((ABUNDANCE, 'CHEBI', 'oxygen'))
        self.assertHasEdge(expected_node, (ABUNDANCE, 'CHEBI', 'oxygen'))

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


class TestRelations(TestTokenParserBase):
    def setUp(self):
        TestTokenParserBase.setUp(self)
        self.parser.parseString(SET_CITATION_TEST)
        self.parser.parseString(test_set_evidence)

    def test_increases(self):
        """
        3.1.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xincreases
        Test composite in subject
        """
        statement = 'composite(p(HGNC:CASP8),p(HGNC:FADD),a(ADO:"Abeta_42")) -> bp(GOBP:"neuron apoptotic process")'
        result = self.parser.relation.parseString(statement)

        expected = [
            [COMPOSITE, [PROTEIN, ['HGNC', 'CASP8']], [PROTEIN, ['HGNC', 'FADD']],
             [ABUNDANCE, ['ADO', 'Abeta_42']]],
            'increases',
            [BIOPROCESS, ['GOBP', 'neuron apoptotic process']]
        ]
        self.assertEqual(expected, result.asList())

        sub = canonicalize_node(result[SUBJECT])
        self.assertHasNode(sub)

        sub_member_1 = PROTEIN, 'HGNC', 'CASP8'
        self.assertHasNode(sub_member_1)

        sub_member_2 = PROTEIN, 'HGNC', 'FADD'
        self.assertHasNode(sub_member_2)

        self.assertHasEdge(sub, sub_member_1, relation='hasComponent')
        self.assertHasEdge(sub, sub_member_2, relation='hasComponent')

        obj = BIOPROCESS, 'GOBP', 'neuron apoptotic process'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation='increases')

    def test_directlyIncreases_withTlocObject(self):
        """
        3.1.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XdIncreases
        Test translocation in object
        """
        statement = 'a(ADO:"Abeta_42") => tloc(a(CHEBI:"calcium(2+)"),fromLoc(MESHCS:"Cell Membrane"),' \
                    'toLoc(MESHCS:"Intracellular Space"))'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            SUBJECT: {
                FUNCTION: ABUNDANCE,
                IDENTIFIER: {
                    NAMESPACE: 'ADO',
                    NAME: 'Abeta_42'
                }
            },
            RELATION: 'directlyIncreases',
            OBJECT: {
                TARGET: {
                    FUNCTION: ABUNDANCE,
                    IDENTIFIER: {
                        NAMESPACE: 'CHEBI',
                        NAME: 'calcium(2+)'
                    }
                },
                MODIFIER: TRANSLOCATION,
                EFFECT: {
                    FROM_LOC: {NAMESPACE: 'MESHCS', NAME: 'Cell Membrane'},
                    TO_LOC: {NAMESPACE: 'MESHCS', NAME: 'Intracellular Space'}
                }
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = ABUNDANCE, 'ADO', 'Abeta_42'
        self.assertHasNode(sub)

        obj = ABUNDANCE, 'CHEBI', 'calcium(2+)'
        self.assertHasNode(obj)

        expected_annotations = {
            RELATION: 'directlyIncreases',
            OBJECT: {
                MODIFIER: TRANSLOCATION,
                EFFECT: {
                    FROM_LOC: {NAMESPACE: 'MESHCS', NAME: 'Cell Membrane'},
                    TO_LOC: {NAMESPACE: 'MESHCS', NAME: 'Intracellular Space'}
                }
            }
        }

        self.assertHasEdge(sub, obj, **expected_annotations)

    def test_decreases(self):
        """
        3.1.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xdecreases
        Test decreases with reaction"""
        statement = 'pep(p(SFAM:"CAPN Family", location(GOCC:intracellular))) -| reaction(reactants(p(HGNC:CDK5R1)),products(p(HGNC:CDK5)))'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            SUBJECT: {
                MODIFIER: ACTIVITY,
                TARGET: {
                    FUNCTION: PROTEIN,
                    IDENTIFIER: {NAMESPACE: 'SFAM', NAME: 'CAPN Family'},
                    LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}
                },
                EFFECT: {
                    NAME: 'pep',
                    NAMESPACE: BEL_DEFAULT_NAMESPACE},
            },
            RELATION: 'decreases',
            OBJECT: {
                FUNCTION: REACTION,
                REACTANTS: [
                    {FUNCTION: PROTEIN, IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'CDK5R1'}}
                ],
                PRODUCTS: [
                    {FUNCTION: PROTEIN, IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'CDK5'}}
                ]

            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = PROTEIN, 'SFAM', 'CAPN Family'
        self.assertHasNode(sub)

        obj = canonicalize_node(result[OBJECT])
        self.assertHasNode(obj)

        obj_member_1 = PROTEIN, 'HGNC', 'CDK5R1'
        self.assertHasNode(obj_member_1)

        obj_member_2 = PROTEIN, 'HGNC', 'CDK5'
        self.assertHasNode(obj_member_2)

        self.assertHasEdge(obj, obj_member_1, relation='hasReactant')
        self.assertHasEdge(obj, obj_member_2, relation='hasProduct')

        expected_edge_attributes = {
            RELATION: 'decreases',
            SUBJECT: {
                MODIFIER: ACTIVITY,
                EFFECT: {
                    NAME: 'pep',
                    NAMESPACE: BEL_DEFAULT_NAMESPACE
                },
                LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}
            }
        }
        self.assertHasEdge(sub, obj, **expected_edge_attributes)

    def test_directlyDecreases(self):
        """
        3.1.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XdDecreases
        Tests simple triple"""
        statement = 'proteinAbundance(HGNC:CAT, location(GOCC:intracellular)) directlyDecreases abundance(CHEBI:"hydrogen peroxide")'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            SUBJECT: {
                FUNCTION: PROTEIN,
                IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'CAT'},
                LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}
            },
            RELATION: 'directlyDecreases',
            OBJECT: {
                FUNCTION: ABUNDANCE,
                IDENTIFIER: {NAMESPACE: 'CHEBI', NAME: 'hydrogen peroxide'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = PROTEIN, 'HGNC', 'CAT'
        self.assertHasNode(sub)

        obj = ABUNDANCE, 'CHEBI', 'hydrogen peroxide'
        self.assertHasNode(obj)

        expected_attrs = {
            SUBJECT: {
                LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}
            },
            RELATION: 'directlyDecreases',
        }
        self.assertHasEdge(sub, obj, **expected_attrs)

    def test_directlyDecreases_annotationExpansion(self):
        """
        3.1.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XdDecreases
        Tests simple triple"""
        statement = 'g(HGNC:CAT, location(GOCC:intracellular)) directlyDecreases abundance(CHEBI:"hydrogen peroxide")'

        annotations = {
            'ListAnnotation': {'a', 'b'},
            'ScalarAnnotation': 'c'
        }

        self.parser.control_parser.annotations.update(annotations)

        result = self.parser.relation.parseString(statement)

        expected_dict = {
            SUBJECT: {
                FUNCTION: GENE,
                IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'CAT'},
                LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}
            },
            RELATION: DIRECTLY_DECREASES,
            OBJECT: {
                FUNCTION: ABUNDANCE,
                IDENTIFIER: {NAMESPACE: 'CHEBI', NAME: 'hydrogen peroxide'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = GENE, 'HGNC', 'CAT'
        self.assertHasNode(sub)

        obj = ABUNDANCE, 'CHEBI', 'hydrogen peroxide'
        self.assertHasNode(obj)

        expected_attrs = {
            SUBJECT: {
                LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}
            },
            RELATION: DIRECTLY_DECREASES,
            CITATION: test_citation_dict,
            EVIDENCE: test_evidence_text
        }

        expected_attrs[ANNOTATIONS] = {
            'ListAnnotation': 'a',
            'ScalarAnnotation': 'c'
        }
        self.assertHasEdge(sub, obj, **expected_attrs)

        expected_attrs[ANNOTATIONS] = {
            'ListAnnotation': 'b',
            'ScalarAnnotation': 'c'
        }
        self.assertHasEdge(sub, obj, **expected_attrs)

    def test_rateLimitingStepOf_subjectActivity(self):
        """3.1.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_ratelimitingstepof"""
        statement = 'act(p(HGNC:HMGCR), ma(cat)) rateLimitingStepOf bp(GOBP:"cholesterol biosynthetic process")'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            SUBJECT: {
                MODIFIER: ACTIVITY,
                TARGET: {
                    FUNCTION: PROTEIN,
                    IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'HMGCR'}
                },
                EFFECT: {
                    NAME: 'cat',
                    NAMESPACE: BEL_DEFAULT_NAMESPACE
                },
            },
            RELATION: 'rateLimitingStepOf',
            OBJECT: {
                FUNCTION: BIOPROCESS,
                IDENTIFIER: {NAMESPACE: 'GOBP', NAME: 'cholesterol biosynthetic process'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = PROTEIN, 'HGNC', 'HMGCR'
        self.assertHasNode(sub)

        obj = BIOPROCESS, 'GOBP', 'cholesterol biosynthetic process'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation=expected_dict[RELATION])

    def test_cnc_withSubjectVariant(self):
        """
        3.1.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xcnc
        Test SNP annotation
        """
        statement = 'g(HGNC:APP,sub(G,275341,C)) cnc path(MESHD:"Alzheimer Disease")'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            SUBJECT: {
                FUNCTION: GENE,
                IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'APP'},
                VARIANTS: [
                    {
                        KIND: HGVS,
                        IDENTIFIER: 'c.275341G>C'
                    }
                ]
            },
            RELATION: 'causesNoChange',
            OBJECT: {
                FUNCTION: PATHOLOGY,
                IDENTIFIER: {NAMESPACE: 'MESHD', NAME: 'Alzheimer Disease'}
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = GENE, 'HGNC', 'APP', (HGVS, 'c.275341G>C')
        self.assertHasNode(sub)

        obj = PATHOLOGY, 'MESHD', 'Alzheimer Disease'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation=expected_dict[RELATION])

    def test_regulates_multipleAnnotations(self):
        """
        3.1.7 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_regulates_reg
        Test nested definitions"""
        statement = 'pep(complex(p(HGNC:F3),p(HGNC:F7))) regulates pep(p(HGNC:F9))'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            SUBJECT: {
                MODIFIER: ACTIVITY,
                EFFECT: {
                    NAME: 'pep',
                    NAMESPACE: BEL_DEFAULT_NAMESPACE
                },
                TARGET: {
                    FUNCTION: COMPLEX,
                    'members': [
                        {FUNCTION: PROTEIN, IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'F3'}},
                        {FUNCTION: PROTEIN, IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'F7'}}
                    ]
                }
            },
            RELATION: 'regulates',
            OBJECT: {
                MODIFIER: ACTIVITY,
                EFFECT: {
                    NAME: 'pep',
                    NAMESPACE: BEL_DEFAULT_NAMESPACE
                },
                TARGET: {
                    FUNCTION: PROTEIN,
                    IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'F9'}
                }

            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = canonicalize_node(result[SUBJECT])
        self.assertHasNode(sub)

        sub_member_1 = PROTEIN, 'HGNC', 'F3'
        self.assertHasNode(sub_member_1)

        sub_member_2 = PROTEIN, 'HGNC', 'F7'
        self.assertHasNode(sub_member_2)

        self.assertHasEdge(sub, sub_member_1)
        self.assertHasEdge(sub, sub_member_2)

        obj = PROTEIN, 'HGNC', 'F9'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation=expected_dict[RELATION])

    def test_nested_failure(self):
        """
        3.1 \
        Test nested statement"""
        statement = 'p(HGNC:CAT) -| (a(CHEBI:"hydrogen peroxide") -> bp(GO:"apoptotic process"))'
        with self.assertRaises(NestedRelationWarning):
            self.parser.relation.parseString(statement)

    def test_nested_lenient(self):
        """ 3.1 \ Test nested statement"""
        statement = 'p(HGNC:CAT) -| (a(CHEBI:"hydrogen peroxide") -> bp(GO:"apoptotic process"))'
        self.parser.allow_nested = True

        self.parser.relation.parseString(statement)

        self.assertHasEdge((PROTEIN, 'HGNC', 'CAT'), (ABUNDANCE, 'CHEBI', "hydrogen peroxide"))
        self.assertHasEdge((ABUNDANCE, 'CHEBI', "hydrogen peroxide"),
                           (BIOPROCESS, 'GO', "apoptotic process"))

        self.parser.lenient = False

    def test_negativeCorrelation_withObjectVariant(self):
        """
        3.2.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XnegCor
        Test phosphoralation tag"""
        statement = 'kin(p(SFAM:"GSK3 Family")) neg p(HGNC:MAPT,pmod(P))'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            SUBJECT: {
                MODIFIER: ACTIVITY,
                EFFECT: {
                    NAME: 'kin',
                    NAMESPACE: BEL_DEFAULT_NAMESPACE
                },
                TARGET: {
                    FUNCTION: PROTEIN,
                    IDENTIFIER: {NAMESPACE: 'SFAM', NAME: 'GSK3 Family'}
                }
            },
            RELATION: 'negativeCorrelation',
            OBJECT: {
                FUNCTION: PROTEIN,
                IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'MAPT'},
                VARIANTS: [
                    {
                        KIND: PMOD,
                        IDENTIFIER: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'Ph'},
                    }
                ]
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = PROTEIN, 'SFAM', 'GSK3 Family'
        self.assertHasNode(sub)

        obj = PROTEIN, 'HGNC', 'MAPT', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'))
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation=expected_dict[RELATION])
        self.assertHasEdge(obj, sub, relation=expected_dict[RELATION])

    def test_positiveCorrelation_withSelfReferential(self):
        """
        3.2.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XposCor
        Self-referential relationships"""
        statement = 'p(HGNC:GSK3B, pmod(P, S, 9)) pos act(p(HGNC:GSK3B), ma(kin))'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            SUBJECT: {
                FUNCTION: PROTEIN,
                IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'GSK3B'},
                VARIANTS: [
                    {
                        KIND: PMOD,
                        IDENTIFIER: default_identifier('Ph'),
                        PmodParser.CODE: 'Ser',
                        PmodParser.POSITION: 9
                    }
                ]
            },
            RELATION: 'positiveCorrelation',
            OBJECT: {
                MODIFIER: ACTIVITY,
                TARGET: {
                    FUNCTION: PROTEIN,
                    IDENTIFIER: {NAMESPACE: 'HGNC', NAME: 'GSK3B'}
                },
                EFFECT: {
                    NAME: 'kin',
                    NAMESPACE: BEL_DEFAULT_NAMESPACE
                }
            },
        }
        self.assertEqual(expected_dict, result.asDict())

        subject_node = PROTEIN, 'HGNC', 'GSK3B', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 9)
        self.assertHasNode(subject_node)

        object_node = PROTEIN, 'HGNC', 'GSK3B'
        self.assertHasNode(object_node)

        self.assertHasEdge(subject_node, object_node, relation=expected_dict[RELATION])
        self.assertHasEdge(object_node, subject_node, relation=expected_dict[RELATION])

    def test_orthologous(self):
        """
        3.3.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_orthologous
        """
        statement = 'g(HGNC:AKT1) orthologous g(MGI:AKT1)'
        result = self.parser.relation.parseString(statement)
        expected_result = [[GENE, ['HGNC', 'AKT1']], 'orthologous', [GENE, ['MGI', 'AKT1']]]
        self.assertEqual(expected_result, result.asList())

        sub = GENE, 'HGNC', 'AKT1'
        self.assertHasNode(sub)

        obj = GENE, 'MGI', 'AKT1'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation='orthologous')
        self.assertHasEdge(obj, sub, relation='orthologous')

    def test_transcription(self):
        """
        3.3.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_transcribedto
        """
        statement = 'g(HGNC:AKT1) :> r(HGNC:AKT1)'
        result = self.parser.relation.parseString(statement)

        expected_result = [[GENE, ['HGNC', 'AKT1']], 'transcribedTo', [RNA, ['HGNC', 'AKT1']]]
        self.assertEqual(expected_result, result.asList())

        sub = GENE, 'HGNC', 'AKT1'
        self.assertHasNode(sub)

        obj = RNA, 'HGNC', 'AKT1'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, **{RELATION: TRANSCRIBED_TO})

    def test_translation(self):
        """
        3.3.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_translatedto
        """
        statement = 'r(HGNC:AKT1,loc(GOCC:intracellular)) >> p(HGNC:AKT1)'
        result = self.parser.relation.parseString(statement)

        # [[RNA, ['HGNC', 'AKT1']], TRANSLATED_TO, [PROTEIN, ['HGNC', 'AKT1']]]
        expected_result = {
            SUBJECT: {
                FUNCTION: RNA,
                IDENTIFIER: {
                    NAMESPACE: 'HGNC',
                    NAME: 'AKT1'
                },
                LOCATION: {
                    NAMESPACE: 'GOCC',
                    NAME: 'intracellular'
                }
            },
            RELATION: TRANSLATED_TO,
            OBJECT: {
                FUNCTION: PROTEIN,
                IDENTIFIER: {
                    NAMESPACE: 'HGNC',
                    NAME: 'AKT1'
                }
            }
        }
        self.assertEqual(expected_result, result.asDict())

        sub = RNA, 'HGNC', 'AKT1'
        self.assertHasNode(sub)

        obj = PROTEIN, 'HGNC', 'AKT1'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation=TRANSLATED_TO)

        self.assertEqual('r(HGNC:AKT1, loc(GOCC:intracellular)) translatedTo p(HGNC:AKT1)',
                         decanonicalize_edge(self.parser.graph, sub, obj, 1))

    def test_member_list(self):
        """
        3.4.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_hasmembers
        """
        statement = 'p(PKC:a) hasMembers list(p(HGNC:PRKCA), p(HGNC:PRKCB), p(HGNC:PRKCD), p(HGNC:PRKCE))'
        result = self.parser.relation.parseString(statement)
        expected_result = [
            [PROTEIN, ['PKC', 'a']],
            'hasMembers',
            [
                [PROTEIN, ['HGNC', 'PRKCA']],
                [PROTEIN, ['HGNC', 'PRKCB']],
                [PROTEIN, ['HGNC', 'PRKCD']],
                [PROTEIN, ['HGNC', 'PRKCE']]
            ]
        ]
        self.assertEqual(expected_result, result.asList())

        sub = PROTEIN, 'PKC', 'a'
        obj1 = PROTEIN, 'HGNC', 'PRKCA'
        obj2 = PROTEIN, 'HGNC', 'PRKCB'
        obj3 = PROTEIN, 'HGNC', 'PRKCD'
        obj4 = PROTEIN, 'HGNC', 'PRKCE'

        self.assertHasNode(sub)

        self.assertHasNode(obj1)
        self.assertHasEdge(sub, obj1, relation=HAS_MEMBER)

        self.assertHasNode(obj2)
        self.assertHasEdge(sub, obj2, relation=HAS_MEMBER)

        self.assertHasNode(obj3)
        self.assertHasEdge(sub, obj3, relation=HAS_MEMBER)

        self.assertHasNode(obj4)
        self.assertHasEdge(sub, obj4, relation=HAS_MEMBER)

    def test_isA(self):
        """
        3.4.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_isa
        """
        statement = 'pathology(MESH:Psoriasis) isA pathology(MESH:"Skin Diseases")'
        result = self.parser.relation.parseString(statement)

        expected_result = [[PATHOLOGY, ['MESH', 'Psoriasis']], 'isA', [PATHOLOGY, ['MESH', 'Skin Diseases']]]
        self.assertEqual(expected_result, result.asList())

        sub = PATHOLOGY, 'MESH', 'Psoriasis'
        self.assertHasNode(sub)

        obj = PATHOLOGY, 'MESH', 'Skin Diseases'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation='isA')

    def test_equivalentTo(self):
        statement = 'g(dbSNP:"rs123456") eq g(HGNC:YFG, var(c.123G>A))'
        result = self.parser.relation.parseString(statement)

        expected_result = {
            SUBJECT: {
                FUNCTION: GENE,
                IDENTIFIER: {
                    NAMESPACE: 'dbSNP',
                    NAME: 'rs123456'
                }
            },
            RELATION: EQUIVALENT_TO,
            OBJECT: {
                FUNCTION: GENE,
                IDENTIFIER: {
                    NAMESPACE: 'HGNC',
                    NAME: 'YFG',
                },
                VARIANTS: [
                    {
                        KIND: HGVS,
                        IDENTIFIER: 'c.123G>A'
                    }
                ]
            }
        }
        self.assertEqual(expected_result, result.asDict())

        sub = GENE, 'dbSNP', 'rs123456'
        self.assertHasNode(sub)

        obj = GENE, 'HGNC', 'YFG', (HGVS, 'c.123G>A')
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, **{RELATION: EQUIVALENT_TO})
        self.assertHasEdge(obj, sub, **{RELATION: EQUIVALENT_TO})

    def test_subProcessOf(self):
        """
        3.4.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_subprocessof
        """
        statement = 'rxn(reactants(a(CHEBI:"(S)-3-hydroxy-3-methylglutaryl-CoA"),a(CHEBI:NADPH), \
            a(CHEBI:hydron)),products(a(CHEBI:mevalonate), a(CHEBI:"CoA-SH"), a(CHEBI:"NADP(+)"))) \
            subProcessOf bp(GOBP:"cholesterol biosynthetic process")'
        result = self.parser.relation.parseString(statement)
        expected_result = [[REACTION,
                            [[ABUNDANCE, ['CHEBI', '(S)-3-hydroxy-3-methylglutaryl-CoA']],
                             [ABUNDANCE, ['CHEBI', 'NADPH']],
                             [ABUNDANCE, ['CHEBI', 'hydron']],
                             ],
                            [[ABUNDANCE, ['CHEBI', 'mevalonate']],
                             [ABUNDANCE, ['CHEBI', 'CoA-SH']],
                             [ABUNDANCE, ['CHEBI', 'NADP(+)']]
                             ]],
                           'subProcessOf',
                           [BIOPROCESS, ['GOBP', 'cholesterol biosynthetic process']]]
        self.assertEqual(expected_result, result.asList())

        sub = canonicalize_node(result[SUBJECT])
        self.assertHasNode(sub)

        sub_reactant_1 = ABUNDANCE, 'CHEBI', '(S)-3-hydroxy-3-methylglutaryl-CoA'
        sub_reactant_2 = ABUNDANCE, 'CHEBI', 'NADPH'
        sub_reactant_3 = ABUNDANCE, 'CHEBI', 'hydron'
        sub_product_1 = ABUNDANCE, 'CHEBI', 'mevalonate'
        sub_product_2 = ABUNDANCE, 'CHEBI', 'CoA-SH'
        sub_product_3 = ABUNDANCE, 'CHEBI', 'NADP(+)'

        self.assertHasNode(sub_reactant_1)
        self.assertHasNode(sub_reactant_2)
        self.assertHasNode(sub_reactant_3)
        self.assertHasNode(sub_product_1)
        self.assertHasNode(sub_product_2)
        self.assertHasNode(sub_product_3)

        self.assertHasEdge(sub, sub_reactant_1, relation='hasReactant')
        self.assertHasEdge(sub, sub_reactant_2, relation='hasReactant')
        self.assertHasEdge(sub, sub_reactant_3, relation='hasReactant')
        self.assertHasEdge(sub, sub_product_1, relation='hasProduct')
        self.assertHasEdge(sub, sub_product_2, relation='hasProduct')
        self.assertHasEdge(sub, sub_product_3, relation='hasProduct')

        obj = cls, ns, val = BIOPROCESS, 'GOBP', 'cholesterol biosynthetic process'
        self.assertHasNode(obj, **{FUNCTION: cls, NAMESPACE: ns, NAME: val})

        self.assertHasEdge(sub, obj, relation='subProcessOf')

    def test_extra_1(self):
        statement = 'abundance(CHEBI:"nitric oxide") increases cellSurfaceExpression(complexAbundance(proteinAbundance(HGNC:ITGAV),proteinAbundance(HGNC:ITGB3)))'
        self.parser.parseString(statement)


class TestWrite(TestTokenParserBase):
    def test_1(self):
        cases = [
            ('abundance(CHEBI:"superoxide")', 'a(CHEBI:superoxide)'),
            ('g(HGNC:AKT1,var(p.Phe508del))', 'g(HGNC:AKT1, var(p.Phe508del))'),
            ('geneAbundance(HGNC:AKT1, variant(p.Phe508del), sub(G,308,A), var(c.1521_1523delCTT))',
             'g(HGNC:AKT1, var(c.1521_1523delCTT), var(c.308G>A), var(p.Phe508del))'),
            ('p(HGNC:MAPT,proteinModification(P))', 'p(HGNC:MAPT, pmod(Ph))'),
            ('proteinAbundance(HGNC:SFN)', 'p(HGNC:SFN)'),
            ('complex(proteinAbundance(HGNC:SFN), p(HGNC:YWHAB))', 'complex(p(HGNC:SFN), p(HGNC:YWHAB))'),
            ('composite(proteinAbundance(HGNC:SFN), p(HGNC:YWHAB))', 'composite(p(HGNC:SFN), p(HGNC:YWHAB))'),
            ('reaction(reactants(a(CHEBI:superoxide)),products(a(CHEBI:"oxygen"),a(CHEBI:"hydrogen peroxide")))',
             'rxn(reactants(a(CHEBI:superoxide)), products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:oxygen)))'),
            ('rxn(reactants(a(CHEBI:superoxide)),products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:"oxygen")))',
             'rxn(reactants(a(CHEBI:superoxide)), products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:oxygen)))'),
            ('g(HGNC:AKT1, geneModification(M))', 'g(HGNC:AKT1, gmod(Me))'),
            'g(fus(HGNC:TMPRSS2, p.1_79, HGNC:ERG, p.312_5034))',
            'g(fus(HGNC:TMPRSS2, r.1_?, HGNC:ERG, r.312_5034))',
            'g(fus(HGNC:TMPRSS2, r.1_79, HGNC:ERG, r.?_5034))',
            ('g(HGNC:CHCHD4, fusion(HGNC:AIFM1))', 'g(fus(HGNC:CHCHD4, ?, HGNC:AIFM1, ?))'),
            ('g(HGNC:CHCHD4, fusion(HGNC:AIFM1, ?, ?))', 'g(fus(HGNC:CHCHD4, ?, HGNC:AIFM1, ?))'),
            'g(fus(HGNC:TMPRSS2, ?, HGNC:ERG, ?))',
        ]

        for case in cases:
            source_bel, expected_bel = case if 2 == len(case) else (case, case)

            result = self.parser.parseString(source_bel)
            bel = decanonicalize_node(self.parser.graph, canonicalize_node(result))
            self.assertEqual(expected_bel, bel)
