import logging

from pybel.parser.canonicalize import decanonicalize_node
from pybel.parser.parse_bel import canonicalize_modifier, canonicalize_node
from pybel.parser.parse_exceptions import NestedRelationNotSupportedException, IllegalTranslocationException
from tests.constants import TestTokenParserBase, test_citation_bel, test_evidence_bel

log = logging.getLogger(__name__)


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
            'function': 'Abundance',
            'identifier': dict(namespace='CHEBI', name='oxygen atom')
        }

        self.assertEqual(expected_result, result.asDict())

        node = canonicalize_node(result)
        expected_node = cls, ns, val = 'Abundance', 'CHEBI', 'oxygen atom'
        self.assertEqual(expected_node, node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'a(CHEBI:"oxygen atom")'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        expected_modifier = {}
        self.assertEqual(expected_modifier, canonicalize_modifier(result))

        self.assertHasNode(node, type=cls, namespace=ns, name=val)

    def test_long_abundance(self):
        """small molecule"""
        statement = 'abundance(CHEBI:"oxygen atom", loc(GOCC:intracellular))'

        result = self.parser.general_abundance.parseString(statement)

        expected_result = {
            'function': 'Abundance',
            'identifier': dict(namespace='CHEBI', name='oxygen atom'),
            'location': dict(namespace='GOCC', name='intracellular')
        }

        self.assertEqual(expected_result, result.asDict())

        node = canonicalize_node(result)
        expected_node = cls, ns, val = 'Abundance', 'CHEBI', 'oxygen atom'
        self.assertEqual(expected_node, node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'a(CHEBI:"oxygen atom")'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        modifier = canonicalize_modifier(result)
        expected_modifier = {
            'location': dict(namespace='GOCC', name='intracellular')
        }
        self.assertEqual(expected_modifier, modifier)

        self.assertHasNode(node, type=cls, namespace=ns, name=val)


class TestGene(TestTokenParserBase):
    """2.1.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XgeneA"""

    def setUp(self):
        self.parser.clear()
        self.parser.gene.setParseAction(self.parser.handle_term)

    def test_214a(self):
        statement = 'g(HGNC:AKT1)'

        result = self.parser.gene.parseString(statement)
        expected_list = ['Gene', ['HGNC', 'AKT1']]
        self.assertEqual(expected_list, result.asList())

        expected_dict = {
            'function': 'Gene',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'AKT1'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        expected_node = cls, ns, val = 'Gene', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'g(HGNC:AKT1)'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        self.assertEqual(1, len(self.parser.graph))
        self.assertHasNode(node, type=cls, namespace=ns, name=val)

    def test_214b(self):
        statement = 'g(HGNC:AKT1, loc(GOCC:intracellular))'

        result = self.parser.gene.parseString(statement)

        expected_dict = {
            'function': 'Gene',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'AKT1'
            },
            'location': {
                'namespace': 'GOCC',
                'name': 'intracellular'
            }
        }

        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        expected_node = cls, ns, val = 'Gene', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'g(HGNC:AKT1)'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        self.assertHasNode(node, type=cls, namespace=ns, name=val)

    def test_214c(self):
        """Test variant"""
        statement = 'g(HGNC:AKT1, var(p.Phe508del))'
        result = self.parser.gene.parseString(statement)

        expected_result = {
            'function': 'Gene',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'AKT1'
            },
            'variants': [
                ['Variant', 'p.', 'Phe', 508, 'del']
            ]

        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = 'GeneVariant', 'HGNC', 'AKT1', ('Variant', 'p.', 'Phe', 508, 'del')
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, type='GeneVariant', namespace='HGNC',
                           name='AKT1', variants=(('Variant', 'p.', 'Phe', 508, 'del'),))

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'g(HGNC:AKT1, var(p.Phe508del))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        parent = 'Gene', 'HGNC', 'AKT1'
        self.assertHasNode(parent, type='Gene', namespace='HGNC', name='AKT1')
        self.assertHasEdge(parent, expected_node, relation='hasVariant')

    def test_214d(self):
        """Test BEL 1.0 gene substitution"""
        statement = 'g(HGNC:AKT1,sub(G,308,A))'
        result = self.parser.gene.parseString(statement)

        expected_result = {
            'function': 'Gene',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'AKT1'
            },
            'variants': [
                ['Variant', 'g.', 308, 'G', '>', 'A']
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, type='GeneVariant')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'g(HGNC:AKT1, var(g.308G>A))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        parent = 'Gene', 'HGNC', 'AKT1'
        self.assertHasNode(parent, type='Gene', namespace='HGNC', name='AKT1')

        self.assertHasEdge(parent, expected_node, relation='hasVariant')

    def test_variant_location(self):
        """Test BEL 1.0 gene substitution with location tag"""
        statement = 'g(HGNC:AKT1,sub(G,308,A),loc(GOCC:intracellular))'
        result = self.parser.gene.parseString(statement)

        expected_result = {
            'function': 'Gene',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'AKT1'
            },
            'variants': [
                ['Variant', 'g.', 308, 'G', '>', 'A']
            ],
            'location': {
                'namespace': 'GOCC',
                'name': 'intracellular'
            }
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, type='GeneVariant', namespace='HGNC', name='AKT1')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'g(HGNC:AKT1, var(g.308G>A))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        parent = 'Gene', 'HGNC', 'AKT1'
        self.assertHasNode(parent, type='Gene', namespace='HGNC', name='AKT1')

        self.assertHasEdge(parent, expected_node, relation='hasVariant')

    def test_214e(self):
        """Test multiple variants"""
        statement = 'g(HGNC:AKT1, var(p.Phe508del), sub(G,308,A), var(delCTT))'
        result = self.parser.gene.parseString(statement)

        expected_result = {
            'function': 'Gene',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'AKT1'
            },
            'variants': [
                ['Variant', 'p.', 'Phe', 508, 'del'],
                ['Variant', 'g.', 308, 'G', '>', 'A'],
                ['Variant', 'del', 'CTT']
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, type='GeneVariant')
        self.assertEqual(decanonicalize_node(self.parser.graph, expected_node),
                         'g(HGNC:AKT1, var(delCTT), var(g.308G>A), var(p.Phe508del))')

        parent = 'Gene', 'HGNC', 'AKT1'
        self.assertHasNode(parent, type='Gene', namespace='HGNC', name='AKT1')

        self.assertHasEdge(parent, expected_node, relation='hasVariant')

    def test_gene_fusion_1(self):
        statement = 'g(fus(HGNC:TMPRSS2, c.1_79, HGNC:ERG, c.312_5034))'
        result = self.parser.gene.parseString(statement)
        expected_dict = {
            'function': 'Gene',
            'fusion': {
                'partner_5p': dict(namespace='HGNC', name='TMPRSS2'),
                'partner_3p': dict(namespace='HGNC', name='ERG'),
                'range_5p': ['c', 1, 79],
                'range_3p': ['c', 312, 5034]
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        self.assertHasNode(node)

        canonical_bel = decanonicalize_node(self.parser.graph, node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_gene_fusion_legacy_1(self):
        statement = "g(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626))"
        result = self.parser.gene.parseString(statement)

        expected_dict = {
            'function': 'Gene',
            'fusion': {
                'partner_5p': dict(namespace='HGNC', name='BCR'),
                'partner_3p': dict(namespace='HGNC', name='JAK2'),
                'range_5p': ['c', '?', 1875],
                'range_3p': ['c', 2626, '?']
            }
        }

        self.assertEqual(expected_dict, result.asDict())
        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'g(fus(HGNC:BCR, c.?_1875, HGNC:JAK2, c.2626_?))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_gene_fusion_legacy_2(self):
        statement = "g(HGNC:CHCHD4, fusion(HGNC:AIFM1))"
        result = self.parser.gene.parseString(statement)

        expected_dict = {
            'function': 'Gene',
            'fusion': {
                'partner_5p': dict(namespace='HGNC', name='CHCHD4'),
                'partner_3p': dict(namespace='HGNC', name='AIFM1'),
                'range_5p': '?',
                'range_3p': '?'
            }
        }
        self.assertEqual(expected_dict, result.asDict())
        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'g(fus(HGNC:CHCHD4, ?, HGNC:AIFM1, ?))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_gene_variant_snp(self):
        """2.2.2 SNP"""
        statement = 'g(SNP:rs113993960, var(delCTT))'
        result = self.parser.gene.parseString(statement)

        expected_result = ['Gene', ['SNP', 'rs113993960'], ['Variant', 'del', 'CTT']]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'g(SNP:rs113993960, var(delCTT))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        gene_node = 'Gene', 'SNP', 'rs113993960'
        self.assertHasNode(gene_node, type='Gene', namespace='SNP', name='rs113993960')

        self.assertHasEdge(gene_node, expected_node, relation='hasVariant')

    def test_gene_variant_chromosome(self):
        """2.2.2 chromosome"""
        statement = 'g(REF:"NC_000007.13", var(g.117199646_117199648delCTT))'
        result = self.parser.gene.parseString(statement)

        expected_result = ['Gene', ['REF', 'NC_000007.13'], ['Variant', 'g.', 117199646, '_', 117199648, 'del', 'CTT']]
        self.assertEqual(expected_result, result.asList())

        gene_node = 'Gene', 'REF', 'NC_000007.13'
        expected_node = canonicalize_node(result)

        self.assertHasNode(gene_node, type='Gene', namespace='REF', name='NC_000007.13')
        self.assertHasNode(expected_node, type='GeneVariant')
        self.assertHasEdge(gene_node, expected_node, relation='hasVariant')

    def test_gene_variant_deletion(self):
        """2.2.2 gene-coding DNA reference sequence"""
        statement = 'g(HGNC:CFTR, var(c.1521_1523delCTT))'
        result = self.parser.gene.parseString(statement)

        expected_result = ['Gene', ['HGNC', 'CFTR'], ['Variant', 'c.', 1521, '_', 1523, 'del', 'CTT']]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, type='GeneVariant')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        gene_node = 'Gene', 'HGNC', 'CFTR'
        self.assertHasNode(gene_node, type='Gene', namespace='HGNC', name='CFTR')

        self.assertHasEdge(gene_node, expected_node, relation='hasVariant')


class TestMiRNA(TestTokenParserBase):
    """2.1.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XmicroRNAA"""

    def setUp(self):
        self.parser.clear()
        self.parser.mirna.setParseAction(self.parser.handle_term)

    def test_short(self):
        statement = 'm(HGNC:MIR21)'
        result = self.parser.mirna.parseString(statement)
        expected_result = ['miRNA', ['HGNC', 'MIR21']]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            'function': 'miRNA',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'MIR21'
            }
        }

        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        expected_node = 'miRNA', 'HGNC', 'MIR21'
        self.assertEqual(expected_node, node)

        self.assertHasNode(node)

    def test_long(self):
        statement = 'microRNAAbundance(HGNC:MIR21)'
        result = self.parser.mirna.parseString(statement)
        expected_result = ['miRNA', ['HGNC', 'MIR21']]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            'function': 'miRNA',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'MIR21'
            }
        }

        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        expected_node = 'miRNA', 'HGNC', 'MIR21'
        self.assertEqual(expected_node, node)

        self.assertHasNode(node)

    def test_mirna_location(self):
        statement = 'm(HGNC:MIR21,loc(GOCC:intracellular))'
        result = self.parser.mirna.parseString(statement)

        expected_dict = {
            'function': 'miRNA',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'MIR21'
            },
            'location': {
                'namespace': 'GOCC',
                'name': 'intracellular'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        expected_node = 'miRNA', 'HGNC', 'MIR21'
        self.assertEqual(expected_node, node)

        self.assertHasNode(node)

    def test_mirna_variant(self):
        statement = 'm(HGNC:MIR21,var(p.Phe508del))'
        result = self.parser.mirna.parseString(statement)

        expected_dict = {
            'function': 'miRNA',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'MIR21'
            },
            'variants': [
                ['Variant', 'p.', 'Phe', 508, 'del'],
            ]
        }
        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        self.assertHasNode(node)

        self.assertEqual(2, self.parser.graph.number_of_nodes())

        expected_parent = 'miRNA', 'HGNC', 'MIR21'
        self.assertHasNode(expected_parent)

        self.assertHasEdge(expected_parent, node, relation='hasVariant')

    def test_mirna_variant_location(self):
        statement = 'm(HGNC:MIR21,var(p.Phe508del),loc(GOCC:intracellular))'
        result = self.parser.mirna.parseString(statement)

        expected_dict = {
            'function': 'miRNA',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'MIR21'
            },
            'variants': [
                ['Variant', 'p.', 'Phe', 508, 'del'],
            ],
            'location': {
                'namespace': 'GOCC',
                'name': 'intracellular'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        self.assertHasNode(node)

        self.assertEqual(2, self.parser.graph.number_of_nodes())

        expected_parent = 'miRNA', 'HGNC', 'MIR21'
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
        expected_result = ['Protein', ['HGNC', 'AKT1']]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            'function': 'Protein',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'AKT1'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        expected_node = 'Protein', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)
        self.assertHasNode(node)

        canonical_bel = decanonicalize_node(self.parser.graph, node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_protein_wLocation(self):
        statement = 'p(HGNC:AKT1, loc(GOCC:intracellular))'

        result = self.parser.protein.parseString(statement)

        expected_dict = {
            'function': 'Protein',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'AKT1'
            },
            'location': {
                'namespace': 'GOCC',
                'name': 'intracellular'
            }
        }

        self.assertEqual(expected_dict, result.asDict())

        node = canonicalize_node(result)
        expected_node = 'Protein', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)
        self.assertHasNode(node, type='Protein', namespace='HGNC', name='AKT1')

        canonical_bel = decanonicalize_node(self.parser.graph, node)
        expected_canonical_bel = 'p(HGNC:AKT1)'
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_multiVariant(self):
        statement = 'p(HGNC:AKT1,sub(A,127,Y),pmod(Ph, Ser),loc(GOCC:intracellular))'

        result = self.parser.protein.parseString(statement)

        expected_dict = {
            'function': 'Protein',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'AKT1'
            },
            'location': {
                'namespace': 'GOCC',
                'name': 'intracellular'
            },
            'variants': [
                ['Variant', 'p.', 'Ala', 127, 'Tyr'],
                {
                    'identifier': 'Ph',
                    'code': 'Ser'
                }
            ]
        }

        self.assertEqual(expected_dict, result.asDict())

        node = (
            'ProteinVariant', 'HGNC', 'AKT1', ('ProteinModification', 'Ph', 'Ser'),
            ('Variant', 'p.', 'Ala', 127, 'Tyr'))
        self.assertEqual(node, canonicalize_node(result))
        self.assertHasNode(node, type='ProteinVariant')

        canonical_bel = decanonicalize_node(self.parser.graph, node)
        expected_canonical_bel = 'p(HGNC:AKT1, pmod(Ph, Ser), var(p.Ala127Tyr))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        parent = 'Protein', 'HGNC', 'AKT1'
        self.assertHasNode(parent, type='Protein', namespace='HGNC', name='AKT1')
        self.assertHasEdge(parent, node, relation='hasVariant')

    def test_protein_fusion_1(self):
        statement = 'p(fus(HGNC:TMPRSS2, p.1_79, HGNC:ERG, p.312_5034))'
        result = self.parser.protein.parseString(statement)
        expected_dict = {
            'function': 'Protein',
            'fusion': {
                'partner_5p': dict(namespace='HGNC', name='TMPRSS2'),
                'partner_3p': dict(namespace='HGNC', name='ERG'),
                'range_5p': ['p', 1, 79],
                'range_3p': ['p', 312, 5034]
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = 'ProteinFusion', ('HGNC', 'TMPRSS2'), ('p', 1, 79), ('HGNC', 'ERG'), ('p', 312, 5034)
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_protein_fusion_legacy_1(self):
        statement = 'p(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626))'
        result = self.parser.protein.parseString(statement)

        expected_dict = {
            'function': 'Protein',
            'fusion': {
                'partner_5p': dict(namespace='HGNC', name='BCR'),
                'partner_3p': dict(namespace='HGNC', name='JAK2'),
                'range_5p': ['p', '?', 1875],
                'range_3p': ['p', 2626, '?']
            }
        }

        self.assertEqual(expected_dict, result.asDict())
        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'p(fus(HGNC:BCR, p.?_1875, HGNC:JAK2, p.2626_?))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_protein_fusion_legacy_2(self):
        statement = "p(HGNC:CHCHD4, fusion(HGNC:AIFM1))"
        result = self.parser.protein.parseString(statement)

        expected_dict = {
            'function': 'Protein',
            'fusion': {
                'partner_5p': dict(namespace='HGNC', name='CHCHD4'),
                'partner_3p': dict(namespace='HGNC', name='AIFM1'),
                'range_5p': '?',
                'range_3p': '?'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = 'ProteinFusion', ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'p(fus(HGNC:CHCHD4, ?, HGNC:AIFM1, ?))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_protein_trunc_1(self):
        statement = 'p(HGNC:AKT1, trunc(40))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'AKT1'], ['Variant', 'p.', 40, '*']]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, type='ProteinVariant')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'p(HGNC:AKT1, var(p.40*))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = 'Protein', 'HGNC', 'AKT1'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='AKT1')

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_trunc_2(self):
        statement = 'p(HGNC:AKT1, var(p.C40*))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'AKT1'], ['Variant', 'p.', 'Cys', 40, '*']]
        self.assertEqual(expected_result, result.asList())

        expected_node = 'ProteinVariant', 'HGNC', 'AKT1', ('Variant', 'p.', 'Cys', 40, '*')
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, type='ProteinVariant', namespace='HGNC', name='AKT1')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'p(HGNC:AKT1, var(p.Cys40*))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = cls, ns, val = 'Protein', 'HGNC', 'AKT1'
        self.assertHasNode(protein_node, type='Protein', namespace=ns, name=val)

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_trunc_3(self):
        statement = 'p(HGNC:AKT1, var(p.Arg1851*))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'AKT1'], ['Variant', 'p.', 'Arg', 1851, '*']]
        self.assertEqual(expected_result, result.asList())

        expected_node = 'ProteinVariant', 'HGNC', 'AKT1', ('Variant', 'p.', 'Arg', 1851, '*')
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, type='ProteinVariant', namespace='HGNC', name='AKT1')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = cls, ns, val = 'Protein', 'HGNC', 'AKT1'
        self.assertHasNode(protein_node, type='Protein', namespace=ns, name=val)

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_pmod_1(self):
        """2.2.1 Test default BEL namespace and 1-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(Ph, S, 473))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'AKT1'], ['ProteinModification', 'Ph', 'Ser', 473]]
        self.assertEqual(expected_result, result.asList())

        expected_node = ('ProteinVariant', 'HGNC', 'AKT1', ('ProteinModification', 'Ph', 'Ser', 473))
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, type='ProteinVariant', namespace='HGNC', name='AKT1')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'p(HGNC:AKT1, pmod(Ph, Ser, 473))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = 'Protein', 'HGNC', 'AKT1'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='AKT1')
        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_pmod_2(self):
        """2.2.1 Test default BEL namespace and 3-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(Ph, Ser, 473))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'AKT1'], ['ProteinModification', 'Ph', 'Ser', 473]]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, type='ProteinVariant')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'p(HGNC:AKT1, pmod(Ph, Ser, 473))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = 'Protein', 'HGNC', 'AKT1'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='AKT1')

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_pmod_3(self):
        """2.2.1 Test PSI-MOD namespace and 3-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(MOD:PhosRes, Ser, 473))'
        result = self.parser.protein.parseString(statement)
        expected_result = ['Protein', ['HGNC', 'AKT1'], ['ProteinModification', ['MOD', 'PhosRes'], 'Ser', 473]]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = 'Protein', 'HGNC', 'AKT1'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='AKT1')

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_pmod_4(self):
        """2.2.1 Test HRAS palmitoylated at an unspecified residue. Default BEL namespace"""
        statement = 'p(HGNC:HRAS, pmod(Palm))'
        result = self.parser.protein.parseString(statement)
        expected_result = ['Protein', ['HGNC', 'HRAS'], ['ProteinModification', 'Palm']]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, type='ProteinVariant')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = 'Protein', 'HGNC', 'HRAS'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='HRAS')

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_variant_reference(self):
        """2.2.2 Test reference allele"""
        statement = 'p(HGNC:CFTR, var(=))'
        result = self.parser.protein.parseString(statement)
        expected_result = ['Protein', ['HGNC', 'CFTR'], ['Variant', '=']]
        self.assertEqual(expected_result, result.asList())

        expected_node = 'ProteinVariant', 'HGNC', 'CFTR', ('Variant', '=')
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, type='ProteinVariant')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = 'Protein', 'HGNC', 'CFTR'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='CFTR')

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_variant_unspecified(self):
        """2.2.2 Test unspecified variant"""
        statement = 'p(HGNC:CFTR, var(?))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'CFTR'], ['Variant', '?']]
        self.assertEqual(expected_result, result.asList())

        expected_node = 'ProteinVariant', 'HGNC', 'CFTR', ('Variant', '?')
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, type='ProteinVariant')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = 'Protein', 'HGNC', 'CFTR'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='CFTR')

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_variant_substitution(self):
        """2.2.2 Test substitution"""
        statement = 'p(HGNC:CFTR, var(p.Gly576Ala))'
        result = self.parser.protein.parseString(statement)
        expected_result = ['Protein', ['HGNC', 'CFTR'], ['Variant', 'p.', 'Gly', 576, 'Ala']]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, type='ProteinVariant')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = 'Protein', 'HGNC', 'CFTR'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='CFTR')

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_variant_deletion(self):
        """2.2.2 deletion"""
        statement = 'p(HGNC:CFTR, var(p.Phe508del))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'CFTR'], ['Variant', 'p.', 'Phe', 508, 'del']]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = 'Protein', 'HGNC', 'CFTR'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='CFTR')

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_fragment_known(self):
        """2.2.3 fragment with known start/stop"""
        statement = 'p(HGNC:YFG, frag(5_20))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'YFG'], ['Fragment', 5, '_', 20]]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, type='ProteinVariant')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = 'Protein', 'HGNC', 'YFG'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='YFG')

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_fragment_unbounded(self):
        """2.2.3 amino-terminal fragment of unknown length"""
        statement = 'p(HGNC:YFG, frag(1_?))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'YFG'], ['Fragment', 1, '_', '?']]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, type='ProteinVariant')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = 'Protein', 'HGNC', 'YFG'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='YFG')

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_fragment_unboundTerminal(self):
        """2.2.3 carboxyl-terminal fragment of unknown length"""
        statement = 'p(HGNC:YFG, frag(?_*))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'YFG'], ['Fragment', '?', '_', '*']]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, type='ProteinVariant')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = 'Protein', 'HGNC', 'YFG'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='YFG')

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_fragment_unknown(self):
        """2.2.3 fragment with unknown start/stop"""
        statement = 'p(HGNC:YFG, frag(?))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'YFG'], ['Fragment', '?']]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, type='ProteinVariant')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = 'Protein', 'HGNC', 'YFG'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='YFG')

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_protein_fragment_descriptor(self):
        """2.2.3 fragment with unknown start/stop and a descriptor"""
        statement = 'p(HGNC:YFG, frag(?, 55kD))'
        result = self.parser.protein.parseString(statement)
        expected_result = ['Protein', ['HGNC', 'YFG'], ['Fragment', '?', '55kD']]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, type='ProteinVariant')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        protein_node = 'Protein', 'HGNC', 'YFG'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='YFG')

        self.assertHasEdge(protein_node, expected_node, relation='hasVariant')

    def test_complete_origin(self):
        """"""
        statement = 'p(HGNC:AKT1)'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'AKT1']]
        self.assertEqual(expected_result, result.asList())

        protein = 'Protein', 'HGNC', 'AKT1'
        rna = 'RNA', 'HGNC', 'AKT1'
        gene = 'Gene', 'HGNC', 'AKT1'

        self.assertHasNode(protein, type='Protein', namespace='HGNC', name='AKT1')
        self.assertHasNode(rna, type='RNA', namespace='HGNC', name='AKT1')
        self.assertHasNode(gene, type='Gene', namespace='HGNC', name='AKT1')

        self.assertEqual(2, self.parser.graph.number_of_edges())

        self.assertHasEdge(gene, rna, relation='transcribedTo')
        self.assertEqual(1, self.parser.graph.number_of_edges(gene, rna))

        self.assertHasEdge(rna, protein, relation='translatedTo')
        self.assertEqual(1, self.parser.graph.number_of_edges(rna, protein))

    def test_ensure_no_dup_nodes(self):
        """Ensure node isn't added twice, even if from different statements"""
        s1 = 'g(HGNC:AKT1)'
        s2 = 'deg(g(HGNC:AKT1))'

        self.parser.bel_term.parseString(s1)
        self.parser.bel_term.parseString(s2)

        gene = 'Gene', 'HGNC', 'AKT1'

        self.assertEqual(1, self.parser.graph.number_of_nodes())
        self.assertHasNode(gene, type='Gene', namespace='HGNC', name='AKT1')

    def test_ensure_no_dup_edges(self):
        """Ensure node and edges aren't added twice, even if from different statements and has origin completion"""
        s1 = 'p(HGNC:AKT1)'
        s2 = 'deg(p(HGNC:AKT1))'

        self.parser.bel_term.parseString(s1)
        self.parser.bel_term.parseString(s2)

        protein = 'Protein', 'HGNC', 'AKT1'
        rna = 'RNA', 'HGNC', 'AKT1'
        gene = 'Gene', 'HGNC', 'AKT1'

        self.assertEqual(3, self.parser.graph.number_of_nodes())
        self.assertHasNode(protein, type='Protein', namespace='HGNC', name='AKT1')
        self.assertHasNode(rna, type='RNA', namespace='HGNC', name='AKT1')
        self.assertHasNode(gene, type='Gene', namespace='HGNC', name='AKT1')

        self.assertEqual(2, self.parser.graph.number_of_edges())

        self.assertHasEdge(gene, rna, relation='transcribedTo')
        self.assertEqual(1, self.parser.graph.number_of_edges(gene, rna))

        self.assertHasEdge(rna, protein, relation='translatedTo')
        self.assertEqual(1, self.parser.graph.number_of_edges(rna, protein))


class TestRna(TestTokenParserBase):
    """2.1.7 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XrnaA"""

    def setUp(self):
        self.parser.clear()
        self.parser.rna.setParseAction(self.parser.handle_term)

    def test_217a(self):
        statement = 'r(HGNC:AKT1)'

        result = self.parser.rna.parseString(statement)
        expected_result = ['RNA', ['HGNC', 'AKT1']]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            'function': 'RNA',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'AKT1'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = 'RNA', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, type='RNA', namespace='HGNC', name='AKT1')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_214e(self):
        """Test multiple variants"""
        statement = 'r(HGNC:AKT1, var(p.Phe508del), var(delCTT))'
        result = self.parser.rna.parseString(statement)

        expected_result = {
            'function': 'RNA',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'AKT1'
            },
            'variants': [
                ['Variant', 'p.', 'Phe', 508, 'del'],
                ['Variant', 'del', 'CTT']
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node, type='RNAVariant')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'r(HGNC:AKT1, var(delCTT), var(p.Phe508del))'  # sorted
        self.assertEqual(expected_canonical_bel, canonical_bel)

        parent = 'RNA', 'HGNC', 'AKT1'
        self.assertHasNode(parent, type='RNA', namespace='HGNC', name='AKT1')

        self.assertHasEdge(parent, expected_node, relation='hasVariant')

    def test_rna_fusion_1(self):
        """2.6.1 RNA abundance of fusion with known breakpoints"""
        statement = 'r(fus(HGNC:TMPRSS2, r.1_79, HGNC:ERG, r.312_5034))'
        result = self.parser.rna.parseString(statement)

        expected_result = ['RNA', ['Fusion', ['HGNC', 'TMPRSS2'], ['r', 1, 79], ['HGNC', 'ERG'], ['r', 312, 5034]]]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_rna_fusion_2(self):
        """2.6.1 RNA abundance of fusion with unspecified breakpoints"""
        statement = 'r(fus(HGNC:TMPRSS2, ?, HGNC:ERG, ?))'
        result = self.parser.rna.parseString(statement)

        expected_result = ['RNA', ['Fusion', ['HGNC', 'TMPRSS2'], '?', ['HGNC', 'ERG'], '?']]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_rna_fusion_legacy_1(self):
        statement = "r(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626))"
        result = self.parser.rna.parseString(statement)

        expected_dict = {
            'function': 'RNA',
            'fusion': {
                'partner_5p': dict(namespace='HGNC', name='BCR'),
                'partner_3p': dict(namespace='HGNC', name='JAK2'),
                'range_5p': ['r', '?', 1875],
                'range_3p': ['r', 2626, '?']
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'r(fus(HGNC:BCR, r.?_1875, HGNC:JAK2, r.2626_?))'
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_rna_fusion_legacy_2(self):
        statement = "r(HGNC:CHCHD4, fusion(HGNC:AIFM1))"
        result = self.parser.rna.parseString(statement)

        expected_dict = {
            'function': 'RNA',
            'fusion': {
                'partner_5p': dict(namespace='HGNC', name='CHCHD4'),
                'partner_3p': dict(namespace='HGNC', name='AIFM1'),
                'range_5p': '?',
                'range_3p': '?'
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

        expected_result = ['RNA', ['HGNC', 'CFTR'], ['Variant', 'r.', 1521, '_', 1523, 'del', 'cuu']]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        rna_node = 'RNA', 'HGNC', 'CFTR'
        self.assertHasNode(rna_node, type='RNA', namespace='HGNC', name='CFTR')

        self.assertHasEdge(rna_node, expected_node, relation='hasVariant')

    def test_rna_variant_reference(self):
        """2.2.2 RNA reference sequence"""
        statement = 'r(HGNC:CFTR, var(r.1653_1655delcuu))'
        result = self.parser.rna.parseString(statement)

        expected_result = ['RNA', ['HGNC', 'CFTR'], ['Variant', 'r.', 1653, '_', 1655, 'del', 'cuu']]
        self.assertEqual(expected_result, result.asList())

        expected_node = canonicalize_node(result)
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        rna_node = 'RNA', 'HGNC', 'CFTR'
        self.assertHasNode(rna_node, type='RNA', namespace='HGNC', name='CFTR')

        self.assertHasEdge(rna_node, expected_node, relation='hasVariant')


class TestComplex(TestTokenParserBase):
    """2.1.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcomplexA"""

    def setUp(self):
        self.parser.clear()
        self.parser.complex_abundances.setParseAction(self.parser.handle_term)

    def test_complex_singleton(self):
        statement = 'complex(SCOMP:"AP-1 Complex")'
        result = self.parser.complex_abundances.parseString(statement)

        expected_result = ['Complex', ['SCOMP', 'AP-1 Complex']]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            'function': 'Complex',
            'identifier': {
                'namespace': 'SCOMP',
                'name': 'AP-1 Complex'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = 'Complex', 'SCOMP', 'AP-1 Complex'
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, type='Complex', namespace='SCOMP', name='AP-1 Complex')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

    def test_complex_list_short(self):
        statement = 'complex(p(HGNC:FOS), p(HGNC:JUN))'
        result = self.parser.parseString(statement)

        expected_result = ['Complex', ['Protein', ['HGNC', 'FOS']], ['Protein', ['HGNC', 'JUN']]]
        self.assertEqual(expected_result, result.asList())

        expected_result = {
            'function': 'Complex',
            'members': [
                {
                    'function': 'Protein',
                    'identifier': dict(namespace='HGNC', name='FOS')
                }, {
                    'function': 'Protein',
                    'identifier': dict(namespace='HGNC', name='JUN')
                }
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        expected_node = 'Complex', ('Protein', 'HGNC', 'FOS'), ('Protein', 'HGNC', 'JUN')
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node, type='Complex')

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        child_1 = 'Protein', 'HGNC', 'FOS'
        self.assertHasNode(child_1)
        self.assertHasEdge(expected_node, child_1, relation='hasComponent')

        child_2 = 'Protein', 'HGNC', 'JUN'
        self.assertHasNode(child_2)
        self.assertHasEdge(expected_node, child_2, relation='hasComponent')

    def test_complex_list_long(self):
        statement = 'complexAbundance(proteinAbundance(HGNC:HBP1),geneAbundance(HGNC:NCF1))'
        result = self.parser.parseString(statement)


class TestComposite(TestTokenParserBase):
    """2.1.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcompositeA"""

    def setUp(self):
        self.parser.clear()
        self.parser.composite_abundance.setParseAction(self.parser.handle_term)

    def test_213a(self):
        statement = 'composite(p(HGNC:IL6), complex(GOCC:"interleukin-23 complex"))'
        result = self.parser.composite_abundance.parseString(statement)

        expected_result = ['Composite', ['Protein', ['HGNC', 'IL6']], ['Complex', ['GOCC', 'interleukin-23 complex']]]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            'function': 'Composite',
            'members': [
                {
                    'function': 'Protein',
                    'identifier': dict(namespace='HGNC', name='IL6')
                }, {
                    'function': 'Complex',
                    'identifier': dict(namespace='GOCC', name='interleukin-23 complex')
                }
            ]
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = 'Composite', ('Complex', 'GOCC', 'interleukin-23 complex'), ('Protein', 'HGNC', 'IL6')
        self.assertEqual(expected_node, canonicalize_node(result))

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = 'composite(complex(GOCC:"interleukin-23 complex"), p(HGNC:IL6))'  # sorted
        self.assertEqual(expected_canonical_bel, canonical_bel)

        self.assertEqual(5, self.parser.graph.number_of_nodes())
        self.assertHasNode(expected_node)
        self.assertHasNode(('Protein', 'HGNC', 'IL6'), type='Protein', namespace='HGNC', name='IL6')
        self.assertHasNode(('RNA', 'HGNC', 'IL6'), type='RNA', namespace='HGNC', name='IL6')
        self.assertHasNode(('Gene', 'HGNC', 'IL6'), type='Gene', namespace='HGNC', name='IL6')
        self.assertHasNode(('Complex', 'GOCC', 'interleukin-23 complex'), type='Complex', namespace='GOCC',
                           name='interleukin-23 complex')

        self.assertEqual(4, self.parser.graph.number_of_edges())


class TestBiologicalProcess(TestTokenParserBase):
    def setUp(self):
        self.parser.clear()
        self.parser.biological_process.setParseAction(self.parser.handle_term)

    def test_231a(self):
        """"""
        statement = 'bp(GOBP:"cell cycle arrest")'
        result = self.parser.biological_process.parseString(statement)

        expected_result = ['BiologicalProcess', ['GOBP', 'cell cycle arrest']]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            'function': 'BiologicalProcess',
            'identifier': dict(namespace='GOBP', name='cell cycle arrest')
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = 'BiologicalProcess', 'GOBP', 'cell cycle arrest'
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node,
                           type='BiologicalProcess',
                           namespace='GOBP',
                           name='cell cycle arrest')

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

        expected_result = ['Pathology', ['MESHD', 'adenocarcinoma']]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            'function': 'Pathology',
            'identifier': dict(namespace='MESHD', name='adenocarcinoma')
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = 'Pathology', 'MESHD', 'adenocarcinoma'
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node,
                           type='Pathology',
                           namespace='MESHD',
                           name='adenocarcinoma')

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

        expected_result = ['Activity', ['Protein', ['HGNC', 'AKT1']]]
        self.assertEqual(expected_result, result.asList())

        mod = canonicalize_modifier(result)
        expected_mod = {
            'modifier': 'Activity',
            'effect': {}
        }
        self.assertEqual(expected_mod, mod)

    def test_activity_withMolecularActivityDefault(self):
        """Tests activity modifier with molecular activity from default BEL namespace"""
        statement = 'act(p(HGNC:AKT1), ma(kin))'
        result = self.parser.activity.parseString(statement)

        expected_dict = {
            'modifier': 'Activity',
            'effect': {
                'MolecularActivity': 'KinaseActivity'
            },
            'target': {
                'function': 'Protein',
                'identifier': dict(namespace='HGNC', name='AKT1')
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = canonicalize_modifier(result)
        expected_mod = {
            'modifier': 'Activity',
            'effect': {
                'MolecularActivity': 'KinaseActivity'
            }
        }
        self.assertEqual(expected_mod, mod)

    def test_activity_withMolecularActivityDefaultLong(self):
        """Tests activity modifier with molecular activity from custom namespaced"""
        statement = 'act(p(HGNC:AKT1), ma(catalyticActivity))'
        result = self.parser.activity.parseString(statement)

        expected_dict = {
            'modifier': 'Activity',
            'effect': {
                'MolecularActivity': 'CatalyticActivity'
            },
            'target': {
                'function': 'Protein',
                'identifier': dict(namespace='HGNC', name='AKT1')
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = canonicalize_modifier(result)
        expected_mod = {
            'modifier': 'Activity',
            'effect': {
                'MolecularActivity': 'CatalyticActivity'
            }
        }
        self.assertEqual(expected_mod, mod)

    def test_activity_withMolecularActivityCustom(self):
        """Tests activity modifier with molecular activity from custom namespaced"""
        statement = 'act(p(HGNC:AKT1), ma(GOMF:"catalytic activity"))'
        result = self.parser.activity.parseString(statement)

        expected_dict = {
            'modifier': 'Activity',
            'effect': {
                'MolecularActivity': dict(namespace='GOMF', name='catalytic activity')
            },
            'target': {
                'function': 'Protein',
                'identifier': dict(namespace='HGNC', name='AKT1')
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = canonicalize_modifier(result)
        expected_mod = {
            'modifier': 'Activity',
            'effect': {
                'MolecularActivity': dict(namespace='GOMF', name='catalytic activity')
            }
        }
        self.assertEqual(expected_mod, mod)

    def test_activity_legacy(self):
        """Test BEL 1.0 style molecular activity annotation"""
        statement = 'kin(p(HGNC:AKT1))'
        result = self.parser.activity.parseString(statement)

        expected_dict = {
            'modifier': 'Activity',
            'effect': {
                'MolecularActivity': 'KinaseActivity'
            },
            'target': {
                'function': 'Protein',
                'identifier': dict(namespace='HGNC', name='AKT1')
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = canonicalize_modifier(result)
        expected_mod = {
            'modifier': 'Activity',
            'effect': {
                'MolecularActivity': 'KinaseActivity'
            }
        }
        self.assertEqual(expected_mod, mod)

        node = 'Protein', 'HGNC', 'AKT1'
        self.assertEqual(node, canonicalize_node(result))
        self.assertHasNode(node)


class TestTransformation(TestTokenParserBase):
    def setUp(self):
        self.parser.clear()
        self.parser.transformation.setParseAction(self.parser.handle_term)

    def test_degredation_1(self):
        statement = 'deg(p(HGNC:AKT1))'
        result = self.parser.transformation.parseString(statement)

        expected_result = ['Degradation', ['Protein', ['HGNC', 'AKT1']]]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            'modifier': 'Degradation',
            'target': {
                'function': 'Protein',
                'identifier': dict(namespace='HGNC', name='AKT1')
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = canonicalize_modifier(result)
        expected_mod = {
            'modifier': 'Degradation',
        }
        self.assertEqual(expected_mod, mod)

    def test_degradation_2(self):
        """"""
        statement = 'deg(p(HGNC:EGFR))'
        result = self.parser.transformation.parseString(statement)

        expected_result = ['Degradation', ['Protein', ['HGNC', 'EGFR']]]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            'modifier': 'Degradation',
            'target': {
                'function': 'Protein',
                'identifier': dict(namespace='HGNC', name='EGFR')
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = canonicalize_modifier(result)
        expected_mod = {
            'modifier': 'Degradation',
        }
        self.assertEqual(expected_mod, mod)

        node = 'Protein', 'HGNC', 'EGFR'
        self.assertEqual(node, canonicalize_node(result))
        self.assertHasNode(node)

    def test_translocation_standard(self):
        """translocation example"""
        statement = 'tloc(p(HGNC:EGFR), fromLoc(GOCC:"cell surface"), toLoc(GOCC:endosome))'
        result = self.parser.transformation.parseString(statement)

        expected_dict = {
            'modifier': 'Translocation',
            'target': {
                'function': 'Protein',
                'identifier': dict(namespace='HGNC', name='EGFR')
            },
            'effect': {
                'fromLoc': dict(namespace='GOCC', name='cell surface'),
                'toLoc': dict(namespace='GOCC', name='endosome')
            }
        }

        self.assertEqual(expected_dict, result.asDict())

        mod = canonicalize_modifier(result)
        expected_mod = {
            'modifier': 'Translocation',
            'effect': {
                'fromLoc': dict(namespace='GOCC', name='cell surface'),
                'toLoc': dict(namespace='GOCC', name='endosome')
            }
        }
        self.assertEqual(expected_mod, mod)

        node = 'Protein', 'HGNC', 'EGFR'
        self.assertEqual(node, canonicalize_node(result))
        self.assertHasNode(node)

    def test_translocation_bare(self):
        """translocation example"""
        statement = 'tloc(p(HGNC:EGFR), GOCC:"cell surface", GOCC:endosome)'
        result = self.parser.transformation.parseString(statement)

        expected_dict = {
            'modifier': 'Translocation',
            'target': {
                'function': 'Protein',
                'identifier': dict(namespace='HGNC', name='EGFR')
            },
            'effect': {
                'fromLoc': dict(namespace='GOCC', name='cell surface'),
                'toLoc': dict(namespace='GOCC', name='endosome')
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        mod = canonicalize_modifier(result)
        expected_mod = {
            'modifier': 'Translocation',
            'effect': {
                'fromLoc': dict(namespace='GOCC', name='cell surface'),
                'toLoc': dict(namespace='GOCC', name='endosome')
            }
        }
        self.assertEqual(expected_mod, mod)

        node = 'Protein', 'HGNC', 'EGFR'
        self.assertEqual(node, canonicalize_node(result))
        self.assertHasNode(node)

    def test_translocation_invalid(self):
        """Fail on an improperly written single argument translocation"""
        statement = 'tloc(a(NS:"T-Lymphocytes"))'
        with self.assertRaises(IllegalTranslocationException):
            self.parser.translocation.parseString(statement)

    def test_translocation_secretion(self):
        """cell secretion short form"""
        statement = 'sec(p(HGNC:EGFR))'
        result = self.parser.transformation.parseString(statement)

        expected_result = ['CellSecretion', ['Protein', ['HGNC', 'EGFR']]]
        self.assertEqual(expected_result, result.asList())

        mod = canonicalize_modifier(result)
        expected_mod = {
            'modifier': 'Translocation',
            'effect': {
                'fromLoc': dict(namespace='GOCC', name='intracellular'),
                'toLoc': dict(namespace='GOCC', name='extracellular space')
            }
        }
        self.assertEqual(expected_mod, mod)

        node = 'Protein', 'HGNC', 'EGFR'
        self.assertEqual(node, canonicalize_node(result))
        self.assertHasNode(node)

    def test_translocation_surface(self):
        """cell surface expression short form"""
        statement = 'surf(p(HGNC:EGFR))'
        result = self.parser.transformation.parseString(statement)

        expected_result = ['CellSurfaceExpression', ['Protein', ['HGNC', 'EGFR']]]
        self.assertEqual(expected_result, result.asList())

        expected_mod = {
            'modifier': 'Translocation',
            'effect': {
                'fromLoc': dict(namespace='GOCC', name='intracellular'),
                'toLoc': dict(namespace='GOCC', name='cell surface')
            }
        }
        self.assertEqual(expected_mod, canonicalize_modifier(result))

        node = 'Protein', 'HGNC', 'EGFR'
        self.assertEqual(node, canonicalize_node(result))
        self.assertHasNode(node)

    def test_reaction_1(self):
        """"""
        statement = 'rxn(reactants(a(CHEBI:superoxide)), products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:oxygen)))'
        result = self.parser.transformation.parseString(statement)

        expected_result = [
            'Reaction',
            [['Abundance', ['CHEBI', 'superoxide']]],
            [['Abundance', ['CHEBI', 'hydrogen peroxide']], ['Abundance', ['CHEBI', 'oxygen']]]
        ]
        self.assertEqual(expected_result, result.asList())

        expected_dict = {
            'transformation': 'Reaction',
            'reactants': [
                {
                    'function': 'Abundance',
                    'identifier': dict(namespace='CHEBI', name='superoxide')
                }
            ],
            'products': [
                {
                    'function': 'Abundance',
                    'identifier': dict(namespace='CHEBI', name='hydrogen peroxide')
                }, {

                    'function': 'Abundance',
                    'identifier': dict(namespace='CHEBI', name='oxygen')
                }

            ]
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = 'Reaction', (('Abundance', ('CHEBI', 'superoxide')),), (
            ('Abundance', ('CHEBI', 'hydrogen peroxide')), ('Abundance', ('CHEBI', 'oxygen')))
        self.assertEqual(expected_node, canonicalize_node(result))
        self.assertHasNode(expected_node)

        canonical_bel = decanonicalize_node(self.parser.graph, expected_node)
        expected_canonical_bel = statement
        self.assertEqual(expected_canonical_bel, canonical_bel)

        self.assertHasNode(('Abundance', 'CHEBI', 'superoxide'))
        self.assertHasEdge(expected_node, ('Abundance', 'CHEBI', 'superoxide'))

        self.assertHasNode(('Abundance', 'CHEBI', 'hydrogen peroxide'))
        self.assertHasEdge(expected_node, ('Abundance', 'CHEBI', 'hydrogen peroxide'))

        self.assertHasNode(('Abundance', 'CHEBI', 'oxygen'))
        self.assertHasEdge(expected_node, ('Abundance', 'CHEBI', 'oxygen'))

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
        self.parser.parseString(test_citation_bel)
        self.parser.parseString(test_evidence_bel)

    def test_language(self):
        self.assertIsNotNone(self.parser.get_language())

    def test_increases(self):
        """
        3.1.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xincreases
        Test composite in subject
        """
        statement = 'composite(p(HGNC:CASP8),p(HGNC:FADD),a(ADO:"Abeta_42")) -> bp(GOBP:"neuron apoptotic process")'
        result = self.parser.relation.parseString(statement)

        expected = [
            ['Composite', ['Protein', ['HGNC', 'CASP8']], ['Protein', ['HGNC', 'FADD']],
             ['Abundance', ['ADO', 'Abeta_42']]],
            'increases',
            ['BiologicalProcess', ['GOBP', 'neuron apoptotic process']]
        ]
        self.assertEqual(expected, result.asList())

        sub = canonicalize_node(result['subject'])
        self.assertHasNode(sub)

        sub_member_1 = 'Protein', 'HGNC', 'CASP8'
        self.assertHasNode(sub_member_1)

        sub_member_2 = 'Protein', 'HGNC', 'FADD'
        self.assertHasNode(sub_member_2)

        self.assertHasEdge(sub, sub_member_1, relation='hasComponent')
        self.assertHasEdge(sub, sub_member_2, relation='hasComponent')

        obj = 'BiologicalProcess', 'GOBP', 'neuron apoptotic process'
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
            'subject': {
                'function': 'Abundance',
                'identifier': {
                    'namespace': 'ADO',
                    'name': 'Abeta_42'
                }
            },
            'relation': 'directlyIncreases',
            'object': {
                'target': {
                    'function': 'Abundance',
                    'identifier': {
                        'namespace': 'CHEBI',
                        'name': 'calcium(2+)'
                    }
                },
                'modifier': 'Translocation',
                'effect': {
                    'fromLoc': {'namespace': 'MESHCS', 'name': 'Cell Membrane'},
                    'toLoc': {'namespace': 'MESHCS', 'name': 'Intracellular Space'}
                }
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = 'Abundance', 'ADO', 'Abeta_42'
        self.assertHasNode(sub)

        obj = 'Abundance', 'CHEBI', 'calcium(2+)'
        self.assertHasNode(obj)

        expected_annotations = {
            'relation': 'directlyIncreases',
            'object': {
                'modifier': 'Translocation',
                'effect': {
                    'fromLoc': {'namespace': 'MESHCS', 'name': 'Cell Membrane'},
                    'toLoc': {'namespace': 'MESHCS', 'name': 'Intracellular Space'}
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
            'subject': {
                'modifier': 'Activity',
                'target': {
                    'function': 'Protein',
                    'identifier': {'namespace': 'SFAM', 'name': 'CAPN Family'},
                    'location': dict(namespace='GOCC', name='intracellular')
                },
                'effect': {'MolecularActivity': 'PeptidaseActivity'},
            },
            'relation': 'decreases',
            'object': {
                'transformation': 'Reaction',
                'reactants': [
                    {'function': 'Protein', 'identifier': dict(namespace='HGNC', name='CDK5R1')}
                ],
                'products': [
                    {'function': 'Protein', 'identifier': dict(namespace='HGNC', name='CDK5')}
                ]

            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = 'Protein', 'SFAM', 'CAPN Family'
        self.assertHasNode(sub)

        obj = canonicalize_node(result['object'])
        self.assertHasNode(obj)

        obj_member_1 = 'Protein', 'HGNC', 'CDK5R1'
        self.assertHasNode(obj_member_1)

        obj_member_2 = 'Protein', 'HGNC', 'CDK5'
        self.assertHasNode(obj_member_2)

        self.assertHasEdge(obj, obj_member_1, relation='hasReactant')
        self.assertHasEdge(obj, obj_member_2, relation='hasProduct')

        expected_edge_attributes = {
            'relation': 'decreases',
            'subject': {
                'modifier': 'Activity',
                'effect': {'MolecularActivity': 'PeptidaseActivity'},
                'location': dict(namespace='GOCC', name='intracellular')
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
            'subject': {
                'function': 'Protein',
                'identifier': dict(namespace='HGNC', name='CAT'),
                'location': dict(namespace='GOCC', name='intracellular')
            },
            'relation': 'directlyDecreases',
            'object': {
                'function': 'Abundance',
                'identifier': dict(namespace='CHEBI', name='hydrogen peroxide')
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = 'Protein', 'HGNC', 'CAT'
        self.assertHasNode(sub)

        obj = 'Abundance', 'CHEBI', 'hydrogen peroxide'
        self.assertHasNode(obj)

        expected_attrs = {
            'subject': {
                'location': dict(namespace='GOCC', name='intracellular')
            },
            'relation': 'directlyDecreases',
        }
        self.assertHasEdge(sub, obj, **expected_attrs)

    def test_directlyDecreases_annotationExpansion(self):
        """
        3.1.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XdDecreases
        Tests simple triple"""
        statement = 'g(HGNC:CAT, location(GOCC:intracellular)) directlyDecreases abundance(CHEBI:"hydrogen peroxide")'

        self.parser.control_parser.annotations.update({
            'ListAnnotation': set('ab'),
            'ScalarAnnotation': 'c'
        })

        result = self.parser.relation.parseString(statement)

        expected_dict = {
            'subject': {
                'function': 'Gene',
                'identifier': dict(namespace='HGNC', name='CAT'),
                'location': dict(namespace='GOCC', name='intracellular')
            },
            'relation': 'directlyDecreases',
            'object': {
                'function': 'Abundance',
                'identifier': dict(namespace='CHEBI', name='hydrogen peroxide')
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = 'Gene', 'HGNC', 'CAT'
        self.assertHasNode(sub)

        obj = 'Abundance', 'CHEBI', 'hydrogen peroxide'
        self.assertHasNode(obj)

        expected_attrs = {
            'subject': {
                'location': dict(namespace='GOCC', name='intracellular')
            },
            'relation': 'directlyDecreases',
        }
        self.assertEqual(2, self.parser.graph.number_of_edges())
        self.assertHasEdge(sub, obj, ListAnnotation='a', ScalarAnnotation='c', **expected_attrs)
        self.assertHasEdge(sub, obj, ListAnnotation='b', ScalarAnnotation='c', **expected_attrs)

    def test_rateLimitingStepOf_subjectActivity(self):
        """3.1.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_ratelimitingstepof"""
        statement = 'act(p(HGNC:HMGCR), ma(cat)) rateLimitingStepOf bp(GOBP:"cholesterol biosynthetic process")'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            'subject': {
                'modifier': 'Activity',
                'target': {
                    'function': 'Protein',
                    'identifier': dict(namespace='HGNC', name='HMGCR')
                },
                'effect': {
                    'MolecularActivity': 'CatalyticActivity'
                },
            },
            'relation': 'rateLimitingStepOf',
            'object': {
                'function': 'BiologicalProcess',
                'identifier': dict(namespace='GOBP', name='cholesterol biosynthetic process')
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = 'Protein', 'HGNC', 'HMGCR'
        self.assertHasNode(sub)

        obj = 'BiologicalProcess', 'GOBP', 'cholesterol biosynthetic process'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation=expected_dict['relation'])

    def test_cnc_withSubjectVariant(self):
        """
        3.1.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xcnc
        Test SNP annotation
        """
        statement = 'g(HGNC:APP,sub(G,275341,C)) cnc path(MESHD:"Alzheimer Disease")'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            'subject': {
                'function': 'Gene',
                'identifier': dict(namespace='HGNC', name='APP'),
                'variants': [
                    ['Variant', 'g.', 275341, 'G', '>', 'C']
                ]
            },
            'relation': 'causesNoChange',
            'object': {
                'function': 'Pathology',
                'identifier': dict(namespace='MESHD', name='Alzheimer Disease')
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = 'GeneVariant', 'HGNC', 'APP', ('Variant', 'g.', 275341, 'G', '>', 'C')
        self.assertHasNode(sub)

        obj = 'Pathology', 'MESHD', 'Alzheimer Disease'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation=expected_dict['relation'])

    def test_regulates_multipleAnnotations(self):
        """
        3.1.7 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_regulates_reg
        Test nested definitions"""
        statement = 'pep(complex(p(HGNC:F3),p(HGNC:F7))) regulates pep(p(HGNC:F9))'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            'subject': {
                'modifier': 'Activity',
                'effect': {
                    'MolecularActivity': 'PeptidaseActivity'
                },
                'target': {
                    'function': 'Complex',
                    'members': [
                        {'function': 'Protein', 'identifier': dict(namespace='HGNC', name='F3')},
                        {'function': 'Protein', 'identifier': dict(namespace='HGNC', name='F7')}
                    ]
                }
            },
            'relation': 'regulates',
            'object': {
                'modifier': 'Activity',
                'effect': {
                    'MolecularActivity': 'PeptidaseActivity'
                },
                'target': {
                    'function': 'Protein',
                    'identifier': dict(namespace='HGNC', name='F9')
                }

            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = canonicalize_node(result['subject'])
        self.assertHasNode(sub)

        sub_member_1 = 'Protein', 'HGNC', 'F3'
        self.assertHasNode(sub_member_1)

        sub_member_2 = 'Protein', 'HGNC', 'F7'
        self.assertHasNode(sub_member_2)

        self.assertHasEdge(sub, sub_member_1)
        self.assertHasEdge(sub, sub_member_2)

        obj = 'Protein', 'HGNC', 'F9'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation=expected_dict['relation'])

    def test_nested_failure(self):
        """
        3.1 \
        Test nested statement"""
        statement = 'p(HGNC:CAT) -| (a(CHEBI:"hydrogen peroxide") -> bp(GO:"apoptotic process"))'
        with self.assertRaises(NestedRelationNotSupportedException):
            self.parser.relation.parseString(statement)

    def test_nested_lenient(self):
        """ 3.1 \ Test nested statement"""
        statement = 'p(HGNC:CAT) -| (a(CHEBI:"hydrogen peroxide") -> bp(GO:"apoptotic process"))'
        self.parser.lenient = True

        result = self.parser.relation.parseString(statement)

        self.assertHasEdge(('Protein', 'HGNC', 'CAT'), ('Abundance', 'CHEBI', "hydrogen peroxide"))
        self.assertHasEdge(('Abundance', 'CHEBI', "hydrogen peroxide"),
                           ('BiologicalProcess', 'GO', "apoptotic process"))

        self.parser.lenient = False

    def test_negativeCorrelation_withObjectVariant(self):
        """
        3.2.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XnegCor
        Test phosphoralation tag"""
        statement = 'kin(p(SFAM:"GSK3 Family")) neg p(HGNC:MAPT,pmod(P))'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            'subject': {
                'modifier': 'Activity',
                'effect': {
                    'MolecularActivity': 'KinaseActivity'
                },
                'target': {
                    'function': 'Protein',
                    'identifier': dict(namespace='SFAM', name='GSK3 Family')
                }
            },
            'relation': 'negativeCorrelation',
            'object': {
                'function': 'Protein',
                'identifier': dict(namespace='HGNC', name='MAPT'),
                'variants': [
                    {
                        'identifier': 'Ph',
                    }
                ]
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = 'Protein', 'SFAM', 'GSK3 Family'
        self.assertHasNode(sub)

        obj = 'ProteinVariant', 'HGNC', 'MAPT', ('ProteinModification', 'Ph')
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation=expected_dict['relation'])
        self.assertHasEdge(obj, sub, relation=expected_dict['relation'])

    def test_positiveCorrelation_withSelfReferential(self):
        """
        3.2.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XposCor
        Self-referential relationships"""
        statement = 'p(HGNC:GSK3B, pmod(P, S, 9)) pos act(p(HGNC:GSK3B), ma(kin))'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            'subject': {
                'function': 'Protein',
                'identifier': dict(namespace='HGNC', name='GSK3B'),
                'variants': [
                    {
                        'code': 'Ser',
                        'identifier': 'Ph',
                        'pos': 9
                    }
                ]
            },
            'relation': 'positiveCorrelation',
            'object': {
                'modifier': 'Activity',
                'target': {
                    'function': 'Protein',
                    'identifier': dict(namespace='HGNC', name='GSK3B')
                },
                'effect': {
                    'MolecularActivity': 'KinaseActivity'
                }
            },
        }
        self.assertEqual(expected_dict, result.asDict())

        subject_node = 'ProteinVariant', 'HGNC', 'GSK3B', ('ProteinModification', 'Ph', 'Ser', 9)
        self.assertHasNode(subject_node)

        object_node = 'Protein', 'HGNC', 'GSK3B'
        self.assertHasNode(object_node)

        self.assertHasEdge(subject_node, object_node, relation=expected_dict['relation'])
        self.assertHasEdge(object_node, subject_node, relation=expected_dict['relation'])

    def test_orthologous(self):
        """
        3.3.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_orthologous
        """
        statement = 'g(HGNC:AKT1) orthologous g(MGI:AKT1)'
        result = self.parser.relation.parseString(statement)
        expected_result = [['Gene', ['HGNC', 'AKT1']], 'orthologous', ['Gene', ['MGI', 'AKT1']]]
        self.assertEqual(expected_result, result.asList())

        sub = 'Gene', 'HGNC', 'AKT1'
        self.assertHasNode(sub)

        obj = 'Gene', 'MGI', 'AKT1'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation='orthologous')
        self.assertHasEdge(obj, sub, relation='orthologous')

    def test_transcription(self):
        """
        3.3.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_transcribedto
        """
        statement = 'g(HGNC:AKT1) :> r(HGNC:AKT1)'
        result = self.parser.relation.parseString(statement)

        expected_result = [['Gene', ['HGNC', 'AKT1']], 'transcribedTo', ['RNA', ['HGNC', 'AKT1']]]
        self.assertEqual(expected_result, result.asList())

        sub = 'Gene', 'HGNC', 'AKT1'
        self.assertHasNode(sub)

        obj = 'RNA', 'HGNC', 'AKT1'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation='transcribedTo')

    def test_translation(self):
        """
        3.3.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_translatedto
        """
        statement = 'r(HGNC:AKT1) >> p(HGNC:AKT1)'
        result = self.parser.relation.parseString(statement)

        expected_result = [['RNA', ['HGNC', 'AKT1']], 'translatedTo', ['Protein', ['HGNC', 'AKT1']]]
        self.assertEqual(expected_result, result.asList())

        sub = 'RNA', 'HGNC', 'AKT1'
        self.assertHasNode(sub)

        obj = 'Protein', 'HGNC', 'AKT1'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation='translatedTo')

    def test_member_list(self):
        """
        3.4.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_hasmembers
        """
        statement = 'p(PKC:a) hasMembers list(p(HGNC:PRKCA), p(HGNC:PRKCB), p(HGNC:PRKCD), p(HGNC:PRKCE))'
        result = self.parser.relation.parseString(statement)
        expected_result = [
            ['Protein', ['PKC', 'a']],
            'hasMembers',
            [
                ['Protein', ['HGNC', 'PRKCA']],
                ['Protein', ['HGNC', 'PRKCB']],
                ['Protein', ['HGNC', 'PRKCD']],
                ['Protein', ['HGNC', 'PRKCE']]
            ]
        ]
        self.assertEqual(expected_result, result.asList())

        sub = 'Protein', 'PKC', 'a'
        obj1 = 'Protein', 'HGNC', 'PRKCA'
        obj2 = 'Protein', 'HGNC', 'PRKCB'
        obj3 = 'Protein', 'HGNC', 'PRKCD'
        obj4 = 'Protein', 'HGNC', 'PRKCE'

        self.assertHasNode(sub)

        self.assertHasNode(obj1)
        self.assertHasEdge(sub, obj1, relation='hasMember')

        self.assertHasNode(obj2)
        self.assertHasEdge(sub, obj2, relation='hasMember')

        self.assertHasNode(obj3)
        self.assertHasEdge(sub, obj3, relation='hasMember')

        self.assertHasNode(obj4)
        self.assertHasEdge(sub, obj4, relation='hasMember')

    def test_isA(self):
        """
        3.4.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_isa
        """
        statement = 'pathology(MESH:Psoriasis) isA pathology(MESH:"Skin Diseases")'
        result = self.parser.relation.parseString(statement)

        expected_result = [['Pathology', ['MESH', 'Psoriasis']], 'isA', ['Pathology', ['MESH', 'Skin Diseases']]]
        self.assertEqual(expected_result, result.asList())

        sub = 'Pathology', 'MESH', 'Psoriasis'
        self.assertHasNode(sub)

        obj = 'Pathology', 'MESH', 'Skin Diseases'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation='isA')

    def test_subProcessOf(self):
        """
        3.4.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_subprocessof
        """
        statement = 'rxn(reactants(a(CHEBI:"(S)-3-hydroxy-3-methylglutaryl-CoA"),a(CHEBI:NADPH), \
            a(CHEBI:hydron)),products(a(CHEBI:mevalonate), a(CHEBI:"CoA-SH"), a(CHEBI:"NADP(+)"))) \
            subProcessOf bp(GOBP:"cholesterol biosynthetic process")'
        result = self.parser.relation.parseString(statement)
        expected_result = [['Reaction',
                            [['Abundance', ['CHEBI', '(S)-3-hydroxy-3-methylglutaryl-CoA']],
                             ['Abundance', ['CHEBI', 'NADPH']],
                             ['Abundance', ['CHEBI', 'hydron']],
                             ],
                            [['Abundance', ['CHEBI', 'mevalonate']],
                             ['Abundance', ['CHEBI', 'CoA-SH']],
                             ['Abundance', ['CHEBI', 'NADP(+)']]
                             ]],
                           'subProcessOf',
                           ['BiologicalProcess', ['GOBP', 'cholesterol biosynthetic process']]]
        self.assertEqual(expected_result, result.asList())

        sub = canonicalize_node(result['subject'])
        self.assertHasNode(sub)

        sub_reactant_1 = 'Abundance', 'CHEBI', '(S)-3-hydroxy-3-methylglutaryl-CoA'
        sub_reactant_2 = 'Abundance', 'CHEBI', 'NADPH'
        sub_reactant_3 = 'Abundance', 'CHEBI', 'hydron'
        sub_product_1 = 'Abundance', 'CHEBI', 'mevalonate'
        sub_product_2 = 'Abundance', 'CHEBI', 'CoA-SH'
        sub_product_3 = 'Abundance', 'CHEBI', 'NADP(+)'

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

        obj = cls, ns, val = 'BiologicalProcess', 'GOBP', 'cholesterol biosynthetic process'
        self.assertHasNode(obj, type=cls, namespace=ns, name=val)

        self.assertHasEdge(sub, obj, relation='subProcessOf')

    def test_extra_1(self):
        statement = 'abundance(CHEBI:"nitric oxide") increases cellSurfaceExpression(complexAbundance(proteinAbundance(HGNC:ITGAV),proteinAbundance(HGNC:ITGB3)))'
        result = self.parser.parseString(statement)


class TestWrite(TestTokenParserBase):
    def test_1(self):
        cases = [
            ('abundance(CHEBI:"superoxide")', 'a(CHEBI:superoxide)'),
            ('g(HGNC:AKT1,var(p.Phe508del))', 'g(HGNC:AKT1, var(p.Phe508del))'),
            ('geneAbundance(HGNC:AKT1, variant(p.Phe508del), sub(G,308,A), var(delCTT))',
             'g(HGNC:AKT1, var(delCTT), var(g.308G>A), var(p.Phe508del))'),
            ('p(HGNC:MAPT,proteinModification(P))', 'p(HGNC:MAPT, pmod(Ph))'),
            ('proteinAbundance(HGNC:SFN)', 'p(HGNC:SFN)'),
            ('complex(proteinAbundance(HGNC:SFN), p(HGNC:YWHAB))', 'complex(p(HGNC:SFN), p(HGNC:YWHAB))'),
            ('composite(proteinAbundance(HGNC:SFN), p(HGNC:YWHAB))', 'composite(p(HGNC:SFN), p(HGNC:YWHAB))'),
            ('reaction(reactants(a(CHEBI:superoxide)),products(a(CHEBI:"oxygen"),a(CHEBI:"hydrogen peroxide")))',
             'rxn(reactants(a(CHEBI:superoxide)), products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:oxygen)))'),
            ('rxn(reactants(a(CHEBI:superoxide)),products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:"oxygen")))',
             'rxn(reactants(a(CHEBI:superoxide)), products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:oxygen)))')
        ]

        for source_bel, expected_bel in cases:
            result = self.parser.parseString(source_bel)
            bel = decanonicalize_node(self.parser.graph, canonicalize_node(result))
            self.assertEqual(expected_bel, bel)
