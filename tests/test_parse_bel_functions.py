import logging

from tests.constants import TestTokenParserBase

log = logging.getLogger(__name__)


class TestAbundance(TestTokenParserBase):
    """2.1.1"""

    def setUp(self):
        self.parser.clear()
        self.parser.general_abundance.setParseAction(self.parser.handle_term)

    def test_211a(self):
        """small molecule"""
        statement = 'a(CHEBI:"oxygen atom")'

        result = self.parser.general_abundance.parseString(statement)

        expected_result = {
            'function': 'Abundance',
            'identifier': dict(namespace='CHEBI', name='oxygen atom')
        }

        self.assertEqual(expected_result, result.asDict())

        node = self.parser.canonicalize_node(result)
        expected_node = cls, ns, val = 'Abundance', 'CHEBI', 'oxygen atom'
        self.assertEqual(expected_node, node)

        modifier = self.parser.canonicalize_modifier(result)
        expected_modifier = {}
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

        node = self.parser.canonicalize_node(result)
        expected_node = 'Gene', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)

        self.assertEqual(1, len(self.parser.graph))
        self.assertHasNode(node)

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

        node = self.parser.canonicalize_node(result)
        expected_node = 'Gene', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)

        self.assertHasNode(node)

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
                ['Variant', 'Phe', 508, 'del']
            ]

        }
        self.assertEqual(expected_result, result.asDict())

        name = self.parser.canonicalize_node(result)
        self.assertHasNode(name, type='GeneVariant')

        parent = 'Gene', 'HGNC', 'AKT1'
        self.assertHasNode(parent, type='Gene', namespace='HGNC', name='AKT1')

        self.assertHasEdge(parent, name, relation='hasVariant')

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
                {
                    'reference': 'G',
                    'position': 308,
                    'variant': 'A'
                }
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        name = self.parser.canonicalize_node(result)
        self.assertHasNode(name, type='GeneVariant')

        parent = 'Gene', 'HGNC', 'AKT1'
        self.assertHasNode(parent, type='Gene', namespace='HGNC', name='AKT1')

        self.assertHasEdge(parent, name, relation='hasVariant')

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
                {
                    'reference': 'G',
                    'position': 308,
                    'variant': 'A'
                }
            ],
            'location': {
                'namespace': 'GOCC',
                'name': 'intracellular'
            }
        }
        self.assertEqual(expected_result, result.asDict())

        name = self.parser.canonicalize_node(result)
        self.assertHasNode(name, type='GeneVariant')

        parent = 'Gene', 'HGNC', 'AKT1'
        self.assertHasNode(parent, type='Gene', namespace='HGNC', name='AKT1')

        self.assertHasEdge(parent, name, relation='hasVariant')

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
                ['Variant', 'Phe', 508, 'del'],
                {
                    'reference': 'G',
                    'position': 308,
                    'variant': 'A'
                },
                ['Variant', 'del', 'CTT']
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        name = self.parser.canonicalize_node(result)
        self.assertHasNode(name, type='GeneVariant')

        parent = 'Gene', 'HGNC', 'AKT1'
        self.assertHasNode(parent, type='Gene', namespace='HGNC', name='AKT1')

        self.assertHasEdge(parent, name, relation='hasVariant')

    def test_gene_fusion_1(self):
        statement = 'g(fus(HGNC:TMPRSS2, r.1_79, HGNC:ERG, r.312_5034))'
        result = self.parser.gene.parseString(statement)
        expected_dict = {
            'function': 'Gene',
            'fusion': {
                'partner_5p': dict(namespace='HGNC', name='TMPRSS2'),
                'partner_3p': dict(namespace='HGNC', name='ERG'),
                'range_5p': ['r', 1, 79],
                'range_3p': ['r', 312, 5034]
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        name = self.parser.canonicalize_node(result)
        self.assertHasNode(name)

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
        name = self.parser.canonicalize_node(result)
        self.assertHasNode(name)

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
        name = self.parser.canonicalize_node(result)
        self.assertHasNode(name)

    def test_gene_variant_snp(self):
        """2.2.2 SNP"""
        statement = 'g(SNP:rs113993960, var(delCTT))'
        result = self.parser.gene.parseString(statement)

        expected_result = ['Gene', ['SNP', 'rs113993960'], ['Variant', 'del', 'CTT']]
        self.assertEqual(expected_result, result.asList())

        mod_node = self.parser.canonicalize_node(result)
        self.assertHasNode(mod_node)

        gene_node = 'Gene', 'SNP', 'rs113993960'
        self.assertHasNode(gene_node, type='Gene', namespace='SNP', name='rs113993960')

        self.assertHasEdge(gene_node, mod_node, relation='hasVariant')

    def test_gene_variant_chromosome(self):
        """2.2.2 chromosome"""
        statement = 'g(REF:"NC_000007.13", var(g.117199646_117199648delCTT))'
        result = self.parser.gene.parseString(statement)

        expected_result = ['Gene', ['REF', 'NC_000007.13'], ['Variant', 117199646, 117199648, 'del', 'CTT']]
        self.assertEqual(expected_result, result.asList())

        gene_node = 'Gene', 'REF', 'NC_000007.13'
        mod_node = self.parser.canonicalize_node(result)

        self.assertHasNode(gene_node, type='Gene', namespace='REF', name='NC_000007.13')
        self.assertHasNode(mod_node, type='GeneVariant')
        self.assertHasEdge(gene_node, mod_node, relation='hasVariant')

    def test_gene_variant_deletion(self):
        """2.2.2 gene-coding DNA reference sequence"""
        statement = 'g(HGNC:CFTR, var(c.1521_1523delCTT))'
        result = self.parser.gene.parseString(statement)

        expected_result = ['Gene', ['HGNC', 'CFTR'], ['Variant', 1521, 1523, 'del', 'CTT']]
        self.assertEqual(expected_result, result.asList())

        mod_node = self.parser.canonicalize_node(result)
        self.assertHasNode(mod_node, type='GeneVariant')

        gene_node = 'Gene', 'HGNC', 'CFTR'
        self.assertHasNode(gene_node, type='Gene', namespace='HGNC', name='CFTR')

        self.assertHasEdge(gene_node, mod_node, relation='hasVariant')


class TestMiRNA(TestTokenParserBase):
    """2.1.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XmicroRNAA"""

    def setUp(self):
        self.parser.clear()
        self.parser.mirna.setParseAction(self.parser.handle_term)

    def test_215a(self):
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

        node = self.parser.canonicalize_node(result)
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

        node = self.parser.canonicalize_node(result)
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
                ['Variant', 'Phe', 508, 'del'],
            ]
        }
        self.assertEqual(expected_dict, result.asDict())

        node = self.parser.canonicalize_node(result)
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
                ['Variant', 'Phe', 508, 'del'],
            ],
            'location': {
                'namespace': 'GOCC',
                'name': 'intracellular'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        node = self.parser.canonicalize_node(result)
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

        node = self.parser.canonicalize_node(result)
        expected_node = 'Protein', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)

        self.assertHasNode(node)

    def test_214b(self):
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

        node = self.parser.canonicalize_node(result)
        expected_node = 'Protein', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)

        self.assertHasNode(node, type='Protein', namespace='HGNC', name='AKT1')

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
                {
                    'reference': 'A',
                    'position': 127,
                    'variant': 'Y'
                },
                {
                    'identifier': 'Ph',
                    'code': 'Ser'
                }
            ]
        }

        self.assertEqual(expected_dict, result.asDict())

        node = self.parser.canonicalize_node(result)
        self.assertHasNode(node, type='ProteinVariant')

        parent = 'Protein', 'HGNC', 'AKT1'
        self.assertHasNode(parent, type='Protein', namespace='HGNC', name='AKT1')
        self.assertHasEdge(parent, node, relation='hasVariant')

    def test_protein_fusion_1(self):
        statement = 'p(fus(HGNC:TMPRSS2, r.1_79, HGNC:ERG, r.312_5034))'
        result = self.parser.protein.parseString(statement)
        expected_dict = {
            'function': 'Protein',
            'fusion': {
                'partner_5p': dict(namespace='HGNC', name='TMPRSS2'),
                'partner_3p': dict(namespace='HGNC', name='ERG'),
                'range_5p': ['r', 1, 79],
                'range_3p': ['r', 312, 5034]
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        name = self.parser.canonicalize_node(result)
        self.assertHasNode(name)

    def test_protein_fusion_legacy_1(self):
        statement = "p(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626))"
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
        name = self.parser.canonicalize_node(result)
        self.assertHasNode(name)

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
        name = self.parser.canonicalize_node(result)
        self.assertHasNode(name)

    def test_protein_trunc_1(self):
        statement = 'p(HGNC:AKT1, trunc(40))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'AKT1'], ['Variant', 'C', 40, '*']]
        self.assertEqual(expected_result, result.asList())

        mod_node = self.parser.canonicalize_node(result)
        self.assertHasNode(mod_node, type='ProteinVariant')

        protein_node = 'Protein', 'HGNC', 'AKT1'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='AKT1')

        self.assertHasEdge(protein_node, mod_node, relation='hasVariant')

    def test_protein_trunc_2(self):
        statement = 'p(HGNC:AKT1, var(p.C40*))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'AKT1'], ['Variant', 'C', 40, '*']]
        self.assertEqual(expected_result, result.asList())

        mod_node = self.parser.canonicalize_node(result)
        self.assertHasNode(mod_node, type='ProteinVariant')

        protein_node = 'Protein', 'HGNC', 'AKT1'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='AKT1')

        self.assertHasEdge(protein_node, mod_node, relation='hasVariant')

    def test_protein_pmod_1(self):
        """2.2.1 Test default BEL namespace and 1-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(Ph, S, 473))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'AKT1'], ['ProteinModification', 'Ph', 'S', 473]]
        self.assertEqual(expected_result, result.asList())

        protein_node = 'Protein', 'HGNC', 'AKT1'
        mod_node = self.parser.canonicalize_node(result)

        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='AKT1')
        self.assertHasNode(mod_node, type='ProteinVariant')
        # self.assertHasEdge(mod_node, protein_node, relation='hasParent')
        self.assertHasEdge(protein_node, mod_node, relation='hasVariant')

    def test_protein_pmod_2(self):
        """2.2.1 Test default BEL namespace and 3-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(Ph, Ser, 473))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'AKT1'], ['ProteinModification', 'Ph', 'Ser', 473]]
        self.assertEqual(expected_result, result.asList())

        protein_node = 'Protein', 'HGNC', 'AKT1'
        mod_node = self.parser.canonicalize_node(result)

        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='AKT1')
        self.assertHasNode(mod_node, type='ProteinVariant')
        # self.assertHasEdge(mod_node, protein_node, relation='hasParent')
        self.assertHasEdge(protein_node, mod_node, relation='hasVariant')

    def test_protein_pmod_3(self):
        """2.2.1 Test PSI-MOD namespace and 3-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(MOD:PhosRes, Ser, 473))'
        result = self.parser.protein.parseString(statement)
        expected_result = ['Protein', ['HGNC', 'AKT1'], ['ProteinModification', ['MOD', 'PhosRes'], 'Ser', 473]]
        self.assertEqual(expected_result, result.asList())

        mod_node = self.parser.canonicalize_node(result)
        self.assertHasNode(mod_node)

        protein_node = 'Protein', 'HGNC', 'AKT1'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='AKT1')

        # self.assertHasEdge(mod_node, protein_node, relation='hasParent)
        self.assertHasEdge(protein_node, mod_node, relation='hasVariant')

    def test_protein_pmod_4(self):
        """2.2.1 Test HRAS palmitoylated at an unspecified residue. Default BEL namespace"""
        statement = 'p(HGNC:HRAS, pmod(Palm))'
        result = self.parser.protein.parseString(statement)
        expected_result = ['Protein', ['HGNC', 'HRAS'], ['ProteinModification', 'Palm']]
        self.assertEqual(expected_result, result.asList())

        protein_node = 'Protein', 'HGNC', 'HRAS'
        mod_node = self.parser.canonicalize_node(result)

        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='HRAS')
        self.assertHasNode(mod_node, type='ProteinVariant')
        # self.assertHasEdge(mod_node, protein_node, relation='hasParent')
        self.assertHasEdge(protein_node, mod_node, relation='hasVariant')

    def test_protein_variant_reference(self):
        """2.2.2 Test reference allele"""
        statement = 'p(HGNC:CFTR, var(=))'
        result = self.parser.protein.parseString(statement)
        expected_result = ['Protein', ['HGNC', 'CFTR'], ['Variant', '=']]
        self.assertEqual(expected_result, result.asList())

        # mod_node = 'Protein', 'HGNC', 'CFTR', 'Variant', '='
        # self.assertEqual(mod_node, self.parser.canonicalize_node(result))

        mod_node = self.parser.canonicalize_node(result)
        self.assertHasNode(mod_node, type='ProteinVariant')

        protein_node = 'Protein', 'HGNC', 'CFTR'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='CFTR')

        self.assertHasEdge(protein_node, mod_node, relation='hasVariant')

    def test_protein_variant_unspecified(self):
        """2.2.2 Test unspecified variant"""
        statement = 'p(HGNC:CFTR, var(?))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'CFTR'], ['Variant', '?']]
        self.assertEqual(expected_result, result.asList())

        protein_node = 'Protein', 'HGNC', 'CFTR'
        # mod_node = 'Protein', 'HGNC', 'CFTR', 'Variant', '?'
        mod_node = self.parser.canonicalize_node(result)

        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='CFTR')
        self.assertHasNode(mod_node, type='ProteinVariant')
        self.assertHasEdge(protein_node, mod_node, relation='hasVariant')

    def test_protein_variant_substitution(self):
        """2.2.2 Test substitution"""
        statement = 'p(HGNC:CFTR, var(p.Gly576Ala))'
        result = self.parser.protein.parseString(statement)
        expected_result = ['Protein', ['HGNC', 'CFTR'], ['Variant', 'Gly', 576, 'Ala']]
        self.assertEqual(expected_result, result.asList())

        protein_node = 'Protein', 'HGNC', 'CFTR'
        # mod_node = 'Protein', 'HGNC', 'CFTR', 'Variant', 'Gly', 576, 'Ala'
        mod_node = self.parser.canonicalize_node(result)

        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='CFTR')
        self.assertHasNode(mod_node, type='ProteinVariant')
        self.assertHasEdge(protein_node, mod_node, relation='hasVariant')

    def test_protein_variant_deletion(self):
        """2.2.2 deletion"""
        statement = 'p(HGNC:CFTR, var(p.Phe508del))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'CFTR'], ['Variant', 'Phe', 508, 'del']]
        self.assertEqual(expected_result, result.asList())

        protein_node = 'Protein', 'HGNC', 'CFTR'
        mod_node = self.parser.canonicalize_node(result)

        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='CFTR')
        self.assertHasNode(mod_node)
        self.assertHasEdge(protein_node, mod_node, relation='hasVariant')

    def test_protein_fragment_known(self):
        """2.2.3 fragment with known start/stop"""
        statement = 'p(HGNC:YFG, frag(5_20))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'YFG'], ['Fragment', 5, 20]]
        self.assertEqual(expected_result, result.asList())

        mod_node = self.parser.canonicalize_node(result)
        self.assertHasNode(mod_node, type='ProteinVariant')

        protein_node = 'Protein', 'HGNC', 'YFG'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='YFG')

        self.assertHasEdge(protein_node, mod_node, relation='hasVariant')

    def test_protein_fragment_unbounded(self):
        """2.2.3 amino-terminal fragment of unknown length"""
        statement = 'p(HGNC:YFG, frag(1_?))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'YFG'], ['Fragment', 1, '?']]
        self.assertEqual(expected_result, result.asList())

        mod_node = self.parser.canonicalize_node(result)
        self.assertHasNode(mod_node, type='ProteinVariant')

        protein_node = 'Protein', 'HGNC', 'YFG'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='YFG')

        self.assertHasEdge(protein_node, mod_node, relation='hasVariant')

    def test_protein_fragment_unboundTerminal(self):
        """2.2.3 carboxyl-terminal fragment of unknown length"""
        statement = 'p(HGNC:YFG, frag(?_*))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'YFG'], ['Fragment', '?', '*']]
        self.assertEqual(expected_result, result.asList())

        mod_node = self.parser.canonicalize_node(result)
        self.assertHasNode(mod_node, type='ProteinVariant')

        protein_node = 'Protein', 'HGNC', 'YFG'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='YFG')

        self.assertHasEdge(protein_node, mod_node, relation='hasVariant')

    def test_protein_fragment_unknown(self):
        """2.2.3 fragment with unknown start/stop"""
        statement = 'p(HGNC:YFG, frag(?))'
        result = self.parser.protein.parseString(statement)

        expected_result = ['Protein', ['HGNC', 'YFG'], ['Fragment', '?']]
        self.assertEqual(expected_result, result.asList())

        mod_node = self.parser.canonicalize_node(result)
        self.assertHasNode(mod_node, type='ProteinVariant')

        protein_node = 'Protein', 'HGNC', 'YFG'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='YFG')

        self.assertHasEdge(protein_node, mod_node, relation='hasVariant')

    def test_protein_fragment_descriptor(self):
        """2.2.3 fragment with unknown start/stop and a descriptor"""
        statement = 'p(HGNC:YFG, frag(?, 55kD))'
        result = self.parser.protein.parseString(statement)
        expected_result = ['Protein', ['HGNC', 'YFG'], ['Fragment', '?', '55kD']]
        self.assertEqual(expected_result, result.asList())

        mod_node = self.parser.canonicalize_node(result)
        self.assertHasNode(mod_node, type='ProteinVariant')

        protein_node = 'Protein', 'HGNC', 'YFG'
        self.assertHasNode(protein_node, type='Protein', namespace='HGNC', name='YFG')

        self.assertHasEdge(protein_node, mod_node, relation='hasVariant')


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

        node = self.parser.canonicalize_node(result)
        expected_node = 'RNA', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)

        self.assertHasNode(node, type='RNA', namespace='HGNC', name='AKT1')

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
                ['Variant', 'Phe', 508, 'del'],
                ['Variant', 'del', 'CTT']
            ]
        }
        self.assertEqual(expected_result, result.asDict())

        name = self.parser.canonicalize_node(result)
        self.assertHasNode(name, type='RNAVariant')

        parent = 'RNA', 'HGNC', 'AKT1'
        self.assertHasNode(parent, type='RNA', namespace='HGNC', name='AKT1')

        self.assertHasEdge(parent, name, relation='hasVariant')

    def test_rna_fusion_1(self):
        """2.6.1 RNA abundance of fusion with known breakpoints"""
        statement = 'r(fus(HGNC:TMPRSS2, r.1_79, HGNC:ERG, r.312_5034))'
        result = self.parser.rna.parseString(statement)

        expected_result = ['RNA', ['Fusion', ['HGNC', 'TMPRSS2'], ['r', 1, 79], ['HGNC', 'ERG'], ['r', 312, 5034]]]
        self.assertEqual(expected_result, result.asList())

        node = self.parser.canonicalize_node(result)
        self.assertHasNode(node)

    def test_rna_fusion_2(self):
        """2.6.1 RNA abundance of fusion with unspecified breakpoints"""
        statement = 'r(fus(HGNC:TMPRSS2, ?, HGNC:ERG, ?))'
        result = self.parser.rna.parseString(statement)
        expected_result = ['RNA', ['Fusion', ['HGNC', 'TMPRSS2'], '?', ['HGNC', 'ERG'], '?']]

    def test_gene_fusion_legacy_1(self):
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
        name = self.parser.canonicalize_node(result)
        self.assertHasNode(name)

    def test_gene_fusion_legacy_2(self):
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
        name = self.parser.canonicalize_node(result)
        self.assertHasNode(name)

    def test_rna_variant_codingReference(self):
        """2.2.2 RNA coding reference sequence"""
        statement = 'r(HGNC:CFTR, var(c.1521_1523delCTT))'
        result = self.parser.rna.parseString(statement)

        expected_result = ['RNA', ['HGNC', 'CFTR'], ['Variant', 1521, 1523, 'del', 'CTT']]
        self.assertEqual(expected_result, result.asList())

        mod_node = self.parser.canonicalize_node(result)
        self.assertHasNode(mod_node)

        rna_node = 'RNA', 'HGNC', 'CFTR'
        self.assertHasNode(rna_node, type='RNA', namespace='HGNC', name='CFTR')

        self.assertHasEdge(rna_node, mod_node, relation='hasVariant')

    def test_rna_variant_reference(self):
        """2.2.2 RNA reference sequence"""
        statement = 'r(HGNC:CFTR, var(r.1653_1655delcuu))'
        result = self.parser.rna.parseString(statement)

        expected_result = ['RNA', ['HGNC', 'CFTR'], ['Variant', 1653, 1655, 'del', 'cuu']]
        self.assertEqual(expected_result, result.asList())

        mod_node = self.parser.canonicalize_node(result)
        self.assertHasNode(mod_node)

        rna_node = 'RNA', 'HGNC', 'CFTR'
        self.assertHasNode(rna_node, type='RNA', namespace='HGNC', name='CFTR')

        self.assertHasEdge(rna_node, mod_node, relation='hasVariant')


class TestComplex(TestTokenParserBase):
    """2.1.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcomplexA"""

    def setUp(self):
        self.parser.clear()
        self.parser.complex_abundances.setParseAction(self.parser.handle_term)

    def test_212a(self):
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

        node = self.parser.canonicalize_node(result)
        expected_node = 'Complex', 'SCOMP', 'AP-1 Complex'
        self.assertEqual(expected_node, node)

        self.assertHasNode(node, type='Complex', namespace='SCOMP', name='AP-1 Complex')

    def test_212b(self):
        statement = 'complex(p(HGNC:FOS), p(HGNC:JUN))'
        result = self.parser.complex_abundances.parseString(statement)

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

        expected_node = 'Complex', ('Protein', ('HGNC', 'FOS')), ('Protein', ('HGNC', 'JUN'))

        node = self.parser.canonicalize_node(result)
        self.assertEqual(expected_node, node)
        self.assertHasNode(node, type='Complex')

        child_1 = 'Protein', 'HGNC', 'FOS'
        self.assertHasNode(child_1)
        self.assertHasEdge(node, child_1, relation='hasComponent')

        child_2 = 'Protein', 'HGNC', 'JUN'
        self.assertHasNode(child_2)
        self.assertHasEdge(node, child_2, relation='hasComponent')

    def test_complex(self):
        """Test complex statement"""
        statement = 'complex(p(HGNC:CLSTN1), p(HGNC:KLC1))'
        result = self.parser.complex_abundances.parseString(statement)

        expected = ['Complex', ['Protein', ['HGNC', 'CLSTN1']], ['Protein', ['HGNC', 'KLC1']]]
        self.assertEqual(expected, result.asList())

        complex_name = 'Complex', ('Protein', ('HGNC', 'CLSTN1')), ('Protein', ('HGNC', 'KLC1'))
        self.assertEqual(complex_name, self.parser.canonicalize_node(result))
        self.assertHasNode(complex_name)

        p1_name = 'Protein', 'HGNC', 'CLSTN1'
        self.assertHasNode(p1_name)

        p2_name = 'Protein', 'HGNC', 'KLC1'
        self.assertHasNode(p2_name)

        self.assertHasEdge(complex_name, p1_name)
        self.assertHasEdge(complex_name, p2_name)


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

        node = 'Composite', ('Complex', ('GOCC', 'interleukin-23 complex')), ('Protein', ('HGNC', 'IL6'))
        self.assertEqual(node, self.parser.canonicalize_node(result))

        self.parser.graph[node]

        self.assertEqual(5, self.parser.graph.number_of_nodes())
        self.assertHasNode(node)
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

        node = 'BiologicalProcess', 'GOBP', 'cell cycle arrest'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node,
                           type='BiologicalProcess',
                           namespace='GOBP',
                           name='cell cycle arrest')


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

        node = 'Pathology', 'MESHD', 'adenocarcinoma'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node,
                           type='Pathology',
                           namespace='MESHD',
                           name='adenocarcinoma')
