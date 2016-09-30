import logging
import unittest

from pybel.parsers.bel_parser import Parser

log = logging.getLogger(__name__)


# TODO test ensure node

class TestTokenParserBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = Parser()

    def setUp(self):
        self.parser.graph.clear()
        self.parser.node_count = 0
        self.parser.annotations = {}

    def assertHasNode(self, member, msg=None):
        self.assertIn(member, self.parser.graph)

    def assertHasEdge(self, u, v, msg=None, **kwargs):
        msg = 'Edge ({}, {}) not in graph'.format(u, v) if msg is None else msg
        self.assertTrue(self.parser.graph.has_edge(u, v), msg)


class TestEnsure(TestTokenParserBase):
    def test_complete(self):
        """"""
        statement = 'p(HGNC:AKT1)'
        result = self.parser.parse(statement)
        expected_result = ['Protein', ['HGNC', 'AKT1']]
        self.assertEqual(expected_result, result)

        protein = 'Protein', 'HGNC', 'AKT1'
        rna = 'RNA', 'HGNC', 'AKT1'
        gene = 'Gene', 'HGNC', 'AKT1'

        self.assertHasNode(protein)
        self.assertHasNode(rna)
        self.assertHasNode(gene)

        self.assertHasEdge(gene, rna, relation='transcribedTo')
        self.assertHasEdge(rna, protein, relation='translatedTo')

    def ensure_no_dups(self):
        """Ensure node isn't added twice, even if from different statements"""
        s1 = 'g(HGNC:AKT1)'
        s2 = 'deg(g(HGNC:AKT1))'
        s3 = 'g(HGNC:AKT1) -- g(HGNC:AKT1)'

        self.parser.parse(s1)
        self.parser.parse(s2)
        self.parser.parse(s3)

        self.assertEqual(1, self.parser.graph)
        self.assertHasNode(('Gene', 'HGNC', 'AKT1'))


class TestInternal(TestTokenParserBase):
    def test_pmod1(self):
        statement = 'pmod(Ph, Ser, 473)'
        expected = ['ProteinModification', 'Ph', 'Ser', 473]
        result = self.parser.pmod.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_pmod2(self):
        statement = 'pmod(Ph, Ser)'
        expected = ['ProteinModification', 'Ph', 'Ser']
        result = self.parser.pmod.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_pmod3(self):
        statement = 'pmod(Ph)'
        expected = ['ProteinModification', 'Ph']
        result = self.parser.pmod.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_pmod4(self):
        statement = 'pmod(P, S, 9)'
        expected = ['ProteinModification', 'P', 'S', 9]
        result = self.parser.pmod.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_pmod5(self):
        statement = 'pmod(MOD:PhosRes, Ser, 473)'
        expected = ['ProteinModification', ['MOD', 'PhosRes'], 'Ser', 473]
        result = self.parser.pmod.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_psub(self):
        statement = 'sub(A, 127, Y)'
        expected = ['Variant', 'A', 127, 'Y']
        result = self.parser.psub.parseString(statement)
        self.assertEqual(expected, result.asList())


class TestAnnotations(TestTokenParserBase):
    def test_activity_1(self):
        """"""
        statement = 'act(p(HGNC:AKT1))'
        result = self.parser.parse(statement)
        expected_result = ['Activity', ['Protein', ['HGNC', 'AKT1']]]
        self.assertEqual(expected_result, result)

        mod = self.parser.canonicalize_modifier(result)
        expected_mod = {
            'modification': 'Activity',
            'params': {}
        }
        self.assertEqual(expected_mod, mod)

    def test_activity_2(self):
        """"""
        statement = 'act(p(HGNC:AKT1), ma(kin))'
        result = self.parser.parse(statement)
        expected_result = ['Activity', ['Protein', ['HGNC', 'AKT1']], ['MolecularActivity', 'KinaseActivity']]
        self.assertEqual(expected_result, result)

        mod = self.parser.canonicalize_modifier(result)
        expected_mod = {
            'modification': 'Activity',
            'params': {
                'MolecularActivity': 'KinaseActivity'
            }
        }
        self.assertEqual(expected_mod, mod)

    def test_activity_3(self):
        """"""
        statement = 'act(p(HGNC:AKT1), ma(NS:VAL))'
        result = self.parser.parse(statement)
        expected_result = ['Activity', ['Protein', ['HGNC', 'AKT1']], ['MolecularActivity', ['NS', 'VAL']]]
        self.assertEqual(expected_result, result)

        mod = self.parser.canonicalize_modifier(result)
        expected_mod = {
            'modification': 'Activity',
            'params': {
                'MolecularActivity': ('NS', 'VAL')
            }
        }
        self.assertEqual(expected_mod, mod)

    def test_degredation_1(self):
        statement = 'deg(p(HGNC:AKT1))'
        result = self.parser.parse(statement)
        expected_result = ['Degradation', ['Protein', ['HGNC', 'AKT1']]]
        self.assertEqual(expected_result, result)

        mod = self.parser.canonicalize_modifier(result)
        expected_mod = {
            'modification': 'Degradation',
            'params': {}
        }
        self.assertEqual(expected_mod, mod)

    def test_tloc_1(self):
        """translocation example"""
        statement = 'tloc(p(HGNC:EGFR), fromLoc(GOCC:"cell surface"), toLoc(GOCC:endosome))'
        result = self.parser.parse(statement)
        expected_result = [
            'Translocation',
            ['Protein', ['HGNC', 'EGFR']],
            ['GOCC', 'cell surface'],
            ['GOCC', 'endosome']
        ]
        self.assertEqual(expected_result, result)

        mod = self.parser.canonicalize_modifier(result)
        expected_mod = {
            'modification': 'Translocation',
            'params': {
                'fromLoc': ('GOCC', 'cell surface'),
                'toLoc': ('GOCC', 'endosome')
            }
        }
        self.assertEqual(expected_mod, mod)


class TestTerms(TestTokenParserBase):
    def test_211a(self):
        """small molecule"""
        statement = 'a(CHEBI:"oxygen atom")'

        result = self.parser.parse(statement)
        expected_result = ['Abundance', ['CHEBI', 'oxygen atom']]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'Abundance', 'CHEBI', 'oxygen atom'
        self.assertEqual(expected_node, node)

        self.assertIn(node, self.parser.graph)

    def test_211b(self):
        statement = 'abundance(CHEBI:"carbon atom")'

        result = self.parser.parse(statement)
        expected_result = ['Abundance', ['CHEBI', 'carbon atom']]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'Abundance', 'CHEBI', 'carbon atom'
        self.assertEqual(expected_node, node)

        self.assertIn(node, self.parser.graph)

    def test_212a(self):
        statement = 'complex(SCOMP:"AP-1 Complex")'

        result = self.parser.parse(statement)
        expected_result = ['Complex', ['SCOMP', 'AP-1 Complex']]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'Complex', 'SCOMP', 'AP-1 Complex'
        self.assertEqual(expected_node, node)

        self.assertIn(node, self.parser.graph)

    def test_212b(self):
        statement = 'complex(p(HGNC:FOS), p(HGNC:JUN))'

        result = self.parser.parse(statement)
        expected_result = ['ComplexList', ['Protein', ['HGNC', 'FOS']], ['Protein', ['HGNC', 'JUN']]]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'ComplexList', 1
        self.assertEqual(expected_node, node)

        self.assertIn(node, self.parser.graph)

    def test_213a(self):
        statement = 'composite(p(HGNC:IL6), complex(GOCC:"interleukin-23 complex"))'

        result = self.parser.parse(statement)
        expected_result = ['Composite', ['Protein', ['HGNC', 'IL6']], ['Complex', ['GOCC', 'interleukin-23 complex']]]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'Composite', 1
        self.assertEqual(expected_node, node)

        self.assertEqual(3, len(self.parser.graph))
        self.assertIn(node, self.parser.graph)
        self.assertIn(('Protein', 'HGNC', 'IL6'), self.parser.graph)
        self.assertIn(('Complex', 'GOCC', 'interleukin-23 complex'), self.parser.graph)

    def test_214a(self):
        statement = 'geneAbundance(HGNC:AKT1)'

        result = self.parser.parse(statement)
        expected_result = ['Gene', ['HGNC', 'AKT1']]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'Gene', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)

        self.assertEqual(1, len(self.parser.graph))
        self.assertIn(node, self.parser.graph)

    def test_214b(self):
        statement = 'geneAbundance(HGNC:AKT2)'

        result = self.parser.parse(statement)
        expected_result = ['Gene', ['HGNC', 'AKT2']]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'Gene', 'HGNC', 'AKT2'
        self.assertEqual(expected_node, node)

        self.assertIn(node, self.parser.graph)

    def test_214c(self):
        statement = 'geneAbundance(HGNC:AKT1)'

        result = self.parser.parse(statement)
        expected_result = ['Gene', ['HGNC', 'AKT1']]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'Gene', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)

        self.assertIn(node, self.parser.graph)

    def test_215a(self):
        statement = 'm(HGNC:MIR21)'

        result = self.parser.parse(statement)
        expected_result = ['miRNA', ['HGNC', 'MIR21']]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'miRNA', 'HGNC', 'MIR21'
        self.assertEqual(expected_node, node)

        self.assertIn(node, self.parser.graph)

    def test_216a(self):
        statement = 'p(HGNC:AKT1)'

        result = self.parser.parse(statement)
        expected_result = ['Protein', ['HGNC', 'AKT1']]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'Protein', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)

        self.assertIn(node, self.parser.graph)

    def test_217a(self):
        statement = 'r(HGNC:AKT1)'

        result = self.parser.parse(statement)
        expected_result = ['RNA', ['HGNC', 'AKT1']]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'RNA', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)

        self.assertIn(node, self.parser.graph)

    def test_221a(self):
        """Test default BEL namespace and 1-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(Ph, S, 473))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinVariant', ['HGNC', 'AKT1'], ['ProteinModification', 'Ph', 'S', 473]]
        self.assertEqual(expected_result, result)

        protein_node = 'Protein', 'HGNC', 'AKT1'
        mod_node = 'ProteinVariant', 'HGNC', 'AKT1', 'ProteinModification', 'Ph', 'S', 473
        self.assertEqual(mod_node, self.parser.canonicalize_node(result))

        self.assertHasNode(protein_node)
        self.assertHasNode(mod_node)
        self.assertHasEdge(mod_node, protein_node)

    def test_221b(self):
        """Test default BEL namespace and 3-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(Ph, Ser, 473))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinVariant', ['HGNC', 'AKT1'], ['ProteinModification', 'Ph', 'Ser', 473]]
        self.assertEqual(expected_result, result)

        protein_node = 'Protein', 'HGNC', 'AKT1'
        mod_node = 'ProteinVariant', 'HGNC', 'AKT1', 'ProteinModification', 'Ph', 'Ser', 473
        self.assertEqual(mod_node, self.parser.canonicalize_node(result))

        self.assertHasNode(protein_node)
        self.assertHasNode(mod_node)
        self.assertHasEdge(mod_node, protein_node)

    def test_221c(self):
        """Test PSI-MOD namespace and 3-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(MOD:PhosRes, Ser, 473))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinVariant', ['HGNC', 'AKT1'], ['ProteinModification', ['MOD', 'PhosRes'], 'Ser', 473]]
        self.assertEqual(expected_result, result)

        mod_node = 'ProteinVariant', 'HGNC', 'AKT1', 'ProteinModification', ('MOD', 'PhosRes'), 'Ser', 473
        self.assertEqual(mod_node, self.parser.canonicalize_node(result))
        self.assertHasNode(mod_node)

        protein_node = 'Protein', 'HGNC', 'AKT1'
        self.assertHasNode(protein_node)

        self.assertHasEdge(mod_node, protein_node)

    def test_221e(self):
        """Test HRAS palmitoylated at an unspecified residue. Default BEL namespace"""
        statement = 'p(HGNC:HRAS, pmod(Palm))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinVariant', ['HGNC', 'HRAS'], ['ProteinModification', 'Palm']]
        self.assertEqual(expected_result, result)

        protein_node = 'Protein', 'HGNC', 'HRAS'
        mod_node = 'ProteinVariant', 'HGNC', 'HRAS', 'ProteinModification', 'Palm'
        self.assertEqual(mod_node, self.parser.canonicalize_node(result))

        self.assertHasNode(protein_node)
        self.assertHasNode(mod_node)
        self.assertHasEdge(mod_node, protein_node)

    def test_222a(self):
        """Test reference allele"""
        statement = 'p(HGNC:CFTR, var(=))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinVariant', ['HGNC', 'CFTR'], ['Variant', '=']]
        self.assertEqual(expected_result, result)

        mod_node = 'ProteinVariant', 'HGNC', 'CFTR', 'Variant', '='
        self.assertEqual(mod_node, self.parser.canonicalize_node(result))
        self.assertHasNode(mod_node)

        protein_node = 'Protein', 'HGNC', 'CFTR'
        self.assertHasNode(protein_node)

        self.assertHasEdge(mod_node, protein_node)

    def test_222b(self):
        """Test unspecified variant"""
        statement = 'p(HGNC:CFTR, var(?))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinVariant', ['HGNC', 'CFTR'], ['Variant', '?']]
        self.assertEqual(expected_result, result)

        protein_node = 'Protein', 'HGNC', 'CFTR'
        mod_node = 'ProteinVariant', 'HGNC', 'CFTR', 'Variant', '?'

        self.assertHasNode(protein_node)
        self.assertHasNode(mod_node)
        self.assertHasEdge(mod_node, protein_node)

    def test_222c(self):
        """Test substitution"""
        statement = 'p(HGNC:CFTR, var(p.Gly576Ala))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinVariant', ['HGNC', 'CFTR'], ['Variant', 'Gly', 576, 'Ala']]
        self.assertEqual(expected_result, result)

        protein_node = 'Protein', 'HGNC', 'CFTR'
        mod_node = 'ProteinVariant', 'HGNC', 'CFTR', 'Variant', 'Gly', 576, 'Ala'

        self.assertHasNode(protein_node)
        self.assertHasNode(mod_node)
        self.assertHasEdge(mod_node, protein_node)

    def test_222d(self):
        """deletion"""
        statement = 'p(HGNC:CFTR, var(p.Phe508del))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinVariant', ['HGNC', 'CFTR'], ['Variant', 'Phe', 508, 'del']]
        self.assertEqual(expected_result, result)

        protein_node = 'Protein', 'HGNC', 'CFTR'
        mod_node = 'ProteinVariant', 'HGNC', 'CFTR', 'Variant', 'Phe', 508, 'del'

        self.assertHasNode(protein_node)
        self.assertHasNode(mod_node)
        self.assertHasEdge(mod_node, protein_node)

    def test_222e(self):
        """SNP"""
        statement = 'g(SNP:rs113993960, var(delCTT))'
        result = self.parser.parse(statement)
        expected_result = ['GeneVariant', ['SNP', 'rs113993960'], ['Variant', 'del', 'CTT']]
        self.assertEqual(expected_result, result)

        gene_node = 'Gene', 'SNP', 'rs113993960'
        mod_node = 'GeneVariant', 'SNP', 'rs113993960', 'Variant', 'del', 'CTT'

        self.assertHasNode(gene_node)
        self.assertHasNode(mod_node)
        self.assertHasEdge(mod_node, gene_node)

    def test_222f(self):
        """chromosome"""
        statement = 'g(REF:"NC_000007.13", var(g.117199646_117199648delCTT))'
        result = self.parser.parse(statement)
        expected_result = ['GeneVariant', ['REF', 'NC_000007.13'], ['Variant', 117199646, 117199648, 'del', 'CTT']]
        self.assertEqual(expected_result, result)

        gene_node = 'Gene', 'REF', 'NC_000007.13'
        mod_node = 'GeneVariant', 'REF', 'NC_000007.13', 'Variant', 117199646, 117199648, 'del', 'CTT'

        self.assertHasNode(gene_node)
        self.assertHasNode(mod_node)
        self.assertHasEdge(mod_node, gene_node)

    def test_222g(self):
        """gene-coding DNA reference sequence"""
        statement = 'g(HGNC:CFTR, var(c.1521_1523delCTT))'
        result = self.parser.parse(statement)
        expected_result = ['GeneVariant', ['HGNC', 'CFTR'], ['Variant', 1521, 1523, 'del', 'CTT']]
        self.assertEqual(expected_result, result)

        mod_node = 'GeneVariant', 'HGNC', 'CFTR', 'Variant', 1521, 1523, 'del', 'CTT'
        self.assertHasNode(mod_node)

        gene_node = 'Gene', 'HGNC', 'CFTR'
        self.assertHasNode(gene_node)

        self.assertHasEdge(mod_node, gene_node)

    def test_222h(self):
        """RNA coding reference sequence"""
        statement = 'r(HGNC:CFTR, var(c.1521_1523delCTT))'
        result = self.parser.parse(statement)
        expected_result = ['RNAVariant', ['HGNC', 'CFTR'], ['Variant', 1521, 1523, 'del', 'CTT']]
        self.assertEqual(expected_result, result)

        mod_node = 'RNAVariant', 'HGNC', 'CFTR', 'Variant', 1521, 1523, 'del', 'CTT'
        self.assertHasNode(mod_node)

        rna_node = 'RNA', 'HGNC', 'CFTR'
        self.assertHasNode(rna_node)

        self.assertHasEdge(mod_node, rna_node)

    def test_222i(self):
        """RNA reference sequence"""
        statement = 'r(HGNC:CFTR, var(r.1653_1655delcuu))'
        result = self.parser.parse(statement)
        expected_result = ['RNAVariant', ['HGNC', 'CFTR'], ['Variant', 1653, 1655, 'del', 'cuu']]
        self.assertEqual(expected_result, result)

        print(self.parser.graph.nodes())

        mod_node = 'RNAVariant', 'HGNC', 'CFTR', 'Variant', 1653, 1655, 'del', 'cuu'
        self.assertHasNode(mod_node)

        rna_node = 'RNA', 'HGNC', 'CFTR'
        self.assertHasNode(rna_node)

        self.assertHasEdge(mod_node, rna_node)

    def test_223a(self):
        """fragment with known start/stop"""
        statement = 'p(HGNC:YFG, frag(5_20))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinVariant', ['HGNC', 'YFG'], ['Fragment', 5, 20]]
        self.assertEqual(expected_result, result)

        mod_node = 'ProteinVariant', 'HGNC', 'YFG', 'Fragment', 5, 20
        self.assertHasNode(mod_node)

        protein_node = 'Protein', 'HGNC', 'YFG'
        self.assertHasNode(protein_node)

        self.assertHasEdge(mod_node, protein_node)

    def test_223b(self):
        """amino-terminal fragment of unknown length"""
        statement = 'p(HGNC:YFG, frag(1_?))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinVariant', ['HGNC', 'YFG'], ['Fragment', 1, '?']]
        self.assertEqual(expected_result, result)

        mod_node = 'ProteinVariant', 'HGNC', 'YFG', 'Fragment', 1, '?'
        self.assertHasNode(mod_node)

        protein_node = 'Protein', 'HGNC', 'YFG'
        self.assertHasNode(protein_node)

        self.assertHasEdge(mod_node, protein_node)

    def test_223c(self):
        """carboxyl-terminal fragment of unknown length"""
        statement = 'p(HGNC:YFG, frag(?_*))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinVariant', ['HGNC', 'YFG'], ['Fragment', '?', '*']]
        self.assertEqual(expected_result, result)

        mod_node = 'ProteinVariant', 'HGNC', 'YFG', 'Fragment', '?', '*'
        self.assertHasNode(mod_node)

        protein_node = 'Protein', 'HGNC', 'YFG'
        self.assertHasNode(protein_node)

        self.assertHasEdge(mod_node, protein_node)

    def test_223d(self):
        """fragment with unknown start/stop"""
        statement = 'p(HGNC:YFG, frag(?))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinVariant', ['HGNC', 'YFG'], ['Fragment', '?']]
        self.assertEqual(expected_result, result)

        mod_node = 'ProteinVariant', 'HGNC', 'YFG', 'Fragment', '?'
        self.assertHasNode(mod_node)

        protein_node = 'Protein', 'HGNC', 'YFG'
        self.assertHasNode(protein_node)

        self.assertHasEdge(mod_node, protein_node)

    def test_223e(self):
        """fragment with unknown start/stop and a descriptor"""
        statement = 'p(HGNC:YFG, frag(?, 55kD))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinVariant', ['HGNC', 'YFG'], ['Fragment', '?', '55kD']]
        self.assertEqual(expected_result, result)

        mod_node = 'ProteinVariant', 'HGNC', 'YFG', 'Fragment', '?', '55kD'
        self.assertHasNode(mod_node)

        protein_node = 'Protein', 'HGNC', 'YFG'
        self.assertHasNode(protein_node)

        self.assertHasEdge(mod_node, protein_node)

    def test_224a(self):
        statement = 'p(HGNC:AKT1, loc(MESHCS:Cytoplasm))'
        result = self.parser.parse(statement)
        expected_result = ['Protein', ['HGNC', 'AKT1'], ['Location', ['MESHCS', 'Cytoplasm']]]
        self.assertEqual(expected_result, result)

        node = 'Protein', 'HGNC', 'AKT1'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node)

    def test_231a(self):
        """"""
        statement = 'bp(GOBP:"cell cycle arrest")'
        result = self.parser.parse(statement)
        expected_result = ['BiologicalProcess', ['GOBP', 'cell cycle arrest']]
        self.assertEqual(expected_result, result)

        node = 'BiologicalProcess', 'GOBP', 'cell cycle arrest'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node)

    def test_231b(self):
        """"""
        statement = 'bp(GOBP:angiogenesis)'
        result = self.parser.parse(statement)
        expected_result = ['BiologicalProcess', ['GOBP', 'angiogenesis']]
        self.assertEqual(expected_result, result)

        node = 'BiologicalProcess', 'GOBP', 'angiogenesis'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node)

    def test_232a(self):
        statement = 'pathology(MESHD:adenocarcinoma)'
        result = self.parser.parse(statement)
        expected_result = ['Pathology', ['MESHD', 'adenocarcinoma']]
        self.assertEqual(expected_result, result)

        node = 'Pathology', 'MESHD', 'adenocarcinoma'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node)

    def test_233a(self):
        """"""
        statement = 'act(p(HGNC:AKT1))'
        result = self.parser.parse(statement)
        expected_result = ['Activity', ['Protein', ['HGNC', 'AKT1']]]
        self.assertEqual(expected_result, result)

        node = 'Protein', 'HGNC', 'AKT1'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node)

    def test_233b(self):
        """"""
        statement = 'kin(p(HGNC:AKT1))'
        result = self.parser.parse(statement)
        expected_result = ['Activity', ['Protein', ['HGNC', 'AKT1']], ['MolecularActivity', 'KinaseActivity']]
        self.assertEqual(expected_result, result)

        node = 'Protein', 'HGNC', 'AKT1'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node)

    def test_241a(self):
        """default BEL namespace, transcriptional activity"""
        statement = 'act(p(HGNC:FOXO1), ma(tscript))'
        result = self.parser.parse(statement)
        expected_result = ['Activity', ['Protein', ['HGNC', 'FOXO1']], ['MolecularActivity', 'TranscriptionalActivity']]
        self.assertEqual(expected_result, result)

        node = 'Protein', 'HGNC', 'FOXO1'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node)

    def test_241b(self):
        """GO molecular function namespace, transcriptional activity"""
        statement = 'act(p(HGNC:FOXO1), ma(GO:"nucleic acid binding transcription factor activity"))'
        result = self.parser.parse(statement)
        expected_result = ['Activity', ['Protein', ['HGNC', 'FOXO1']],
                           ['MolecularActivity', ['GO', 'nucleic acid binding transcription factor activity']]]
        self.assertEqual(expected_result, result)

        node = 'Protein', 'HGNC', 'FOXO1'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node)

    '''node = self.parser.canonicalize_node(result)
        expected_node = ()
        self.assertEqual(expected_node, node)'''

    def test_224c(self):
        """default BEL namespace, kinase activity"""
        statement = 'act(p(HGNC:AKT1), ma(kin))'
        result = self.parser.parse(statement)
        expected_result = ['Activity', ['Protein', ['HGNC', 'AKT1']], ['MolecularActivity', 'KinaseActivity']]
        self.assertEqual(expected_result, result)

        node = 'Protein', 'HGNC', 'AKT1'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node)

    def test_224d(self):
        """GO molecular function namespace, kinase activity"""
        statement = 'act(p(HGNC:AKT1), ma(GO:"kinase activity"))'
        result = self.parser.parse(statement)
        expected_result = ['Activity', ['Protein', ['HGNC', 'AKT1']], ['MolecularActivity', ['GO', 'kinase activity']]]
        self.assertEqual(expected_result, result)

        node = 'Protein', 'HGNC', 'AKT1'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node)

    def test_251a(self):
        """translocation example"""
        statement = 'tloc(p(HGNC:EGFR), fromLoc(GOCC:"cell surface"), toLoc(GOCC:endosome))'
        result = self.parser.parse(statement)
        expected_result = [
            'Translocation',
            ['Protein', ['HGNC', 'EGFR']],
            ['GOCC', 'cell surface'],
            ['GOCC', 'endosome']
        ]
        self.assertEqual(expected_result, result)

        node = 'Protein', 'HGNC', 'EGFR'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node)

    def test_251b(self):
        """cell secretion long form"""
        statement = 'tloc(p(HGNC:EGFR), fromLoc(GOCC:intracellular), toLoc(GOCC:"extracellular space"))'
        result = self.parser.parse(statement)
        expected_result = [
            'Translocation',
            ['Protein', ['HGNC', 'EGFR']],
            ['GOCC', 'intracellular'],
            ['GOCC', 'extracellular space']
        ]
        self.assertEqual(expected_result, result)

        node = 'Protein', 'HGNC', 'EGFR'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node)

    def test_251c(self):
        """cell secretion short form"""
        statement = 'sec(p(HGNC:EGFR))'
        result = self.parser.parse(statement)
        expected_result = ['CellSecretion', ['Protein', ['HGNC', 'EGFR']]]
        self.assertEqual(expected_result, result)

        node = 'Protein', 'HGNC', 'EGFR'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node)

    def test_251d(self):
        """cell surface expression long form"""
        statement = 'tloc(p(HGNC:EGFR), fromLoc(GOCC:intracellular), toLoc(GOCC:"cell surface"))'
        result = self.parser.parse(statement)
        expected_result = ['Translocation',
                           ['Protein', ['HGNC', 'EGFR']],
                           ['GOCC', 'intracellular'],
                           ['GOCC', 'cell surface']]
        self.assertEqual(expected_result, result)

        node = 'Protein', 'HGNC', 'EGFR'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node)

    def test_251e(self):
        """cell surface expression short form"""
        statement = 'surf(p(HGNC:EGFR))'
        result = self.parser.parse(statement)
        expected_result = ['CellSurfaceExpression', ['Protein', ['HGNC', 'EGFR']]]
        self.assertEqual(expected_result, result)

    def test_252a(self):
        """"""
        statement = 'deg(p(HGNC:EGFR))'
        result = self.parser.parse(statement)
        expected_result = ['Degradation', ['Protein', ['HGNC', 'EGFR']]]
        self.assertEqual(expected_result, result)

        node = 'Protein', 'HGNC', 'EGFR'
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node)

    def test_253a(self):
        """"""
        statement = 'rxn(reactants(a(CHEBI:superoxide)),products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:"oxygen")))'
        result = self.parser.parse(statement)
        expected_result = ['Reaction', [['Abundance', ['CHEBI', 'superoxide']]],
                           [['Abundance', ['CHEBI', 'hydrogen peroxide']], ['Abundance', ['CHEBI', 'oxygen']]]]
        self.assertEqual(expected_result, result)

        node = 'Reaction', 1
        self.assertEqual(node, self.parser.canonicalize_node(result))
        self.assertHasNode(node)

        self.assertHasNode(('Abundance', 'CHEBI', 'superoxide'))
        self.assertHasEdge(node, ('Abundance', 'CHEBI', 'superoxide'))

        self.assertHasNode(('Abundance', 'CHEBI', 'hydrogen peroxide'))
        self.assertHasEdge(node, ('Abundance', 'CHEBI', 'hydrogen peroxide'))

        self.assertHasNode(('Abundance', 'CHEBI', 'oxygen'))
        self.assertHasEdge(node, ('Abundance', 'CHEBI', 'oxygen'))

    def test_261a(self):
        """RNA abundance of fusion with known breakpoints"""
        statement = 'r(fus(HGNC:TMPRSS2, r.1_79, HGNC:ERG, r.312_5034))'
        result = self.parser.parse(statement)
        expected_result = ['RNA', ['Fusion', ['HGNC', 'TMPRSS2'], ['r', 1, 79], ['HGNC', 'ERG'], ['r', 312, 5034]]]
        self.assertEqual(expected_result, result)

        # TODO ?????

    def test_261b(self):
        """RNA abundance of fusion with unspecified breakpoints"""
        statement = 'r(fus(HGNC:TMPRSS2, ?, HGNC:ERG, ?))'
        result = self.parser.parse(statement)
        expected_result = ['RNA', ['Fusion', ['HGNC', 'TMPRSS2'], '?', ['HGNC', 'ERG'], '?']]
        self.assertEqual(expected_result, result)

    ''' ------------- OTHER TESTS -------------- '''

    def test_110(self):
        """Tests simple triple"""
        statement = 'proteinAbundance(HGNC:CAT) decreases abundance(CHEBI:"hydrogen peroxide")'
        result = self.parser.parse(statement)
        expected = [
            ['Protein', ['HGNC', 'CAT']],
            'decreases',
            ['Abundance', ['CHEBI', 'hydrogen peroxide']]
        ]
        log.warning(result)
        self.assertEqual(expected, result)

        sub = 'Protein', 'HGNC', 'CAT'
        self.assertHasNode(sub)

        obj = 'Abundance', 'CHEBI', 'hydrogen peroxide'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj)

    def test_111(self):
        """Test nested statement"""
        statement = 'p(HGNC:CAT) -| (a(CHEBI:"hydrogen peroxide") -> bp(GO:"apoptotic process"))'
        result = self.parser.parse(statement)
        expected = [
            ['Protein', ['HGNC', 'CAT']],
            'decreases',
            ['Abundance', ['CHEBI', 'hydrogen peroxide']],
            'increases',
            ['BiologicalProcess', ['GO', 'apoptotic process']]
        ]
        self.assertEqual(expected, result)

    def test_112(self):
        """Test when object is simple triple, with whitespace"""
        statement = 'p(HGNC:CAT) -| ( a(CHEBI:"hydrogen peroxide") -> bp(GO:"apoptotic process") )'
        result = self.parser.parse(statement)
        expected = [
            ['Protein', ['HGNC', 'CAT']],
            'decreases',
            ['Abundance', ['CHEBI', 'hydrogen peroxide']],
            'increases',
            ['BiologicalProcess', ['GO', 'apoptotic process']]
        ]
        self.assertEqual(expected, result)

        self.assertHasNode(('Protein', 'HGNC', 'CAT'))
        self.assertHasNode(('Abundance', 'CHEBI', 'hydrogen peroxide'))
        self.assertHasNode(('BiologicalProcess', 'GO', 'apoptotic process'))

    def test_113(self):
        """Test annotation"""
        statement = 'act(p(HGNC:CHIT1)) biomarkerFor path(MESHD:"Alzheimer Disease")'
        result = self.parser.parse(statement)
        expected = [
            ['Activity', ['Protein', ['HGNC', 'CHIT1']]],
            'biomarkerFor',
            ['Pathology', ['MESHD', 'Alzheimer Disease']]
        ]
        self.assertEqual(expected, result)

        sub = 'Protein', 'HGNC', 'CHIT1'
        self.assertHasNode(sub)

        obj = 'Pathology', 'MESHD', 'Alzheimer Disease'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj)

    def test_121(self):
        """Test nested definitions"""
        statement = 'pep(complex(p(HGNC:F3),p(HGNC:F7))) directlyIncreases pep(p(HGNC:F9))'
        result = self.parser.parse(statement)
        expected = [
            ['Activity',
             ['ComplexList', ['Protein', ['HGNC', 'F3']], ['Protein', ['HGNC', 'F7']]],
             ['MolecularActivity', 'PeptidaseActivity']
             ],
            'directlyIncreases',
            ['Activity', ['Protein', ['HGNC', 'F9']], ['MolecularActivity', 'PeptidaseActivity']]
        ]
        self.assertEqual(expected, result)

        sub = 'ComplexList', 1
        self.assertHasNode(sub)

        sub_member_1 = 'Protein', 'HGNC', 'F3'
        self.assertHasNode(sub_member_1)

        sub_member_2 = 'Protein', 'HGNC', 'F7'
        self.assertHasNode(sub_member_2)

        self.assertHasEdge(sub, sub_member_1)
        self.assertHasEdge(sub, sub_member_2)

        obj = 'Protein', 'HGNC', 'F9'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj)

    def test_131(self):
        """Test complex statement"""
        statement = 'complex(p(HGNC:CLSTN1), p(HGNC:KLC1))'
        result = self.parser.parse(statement)
        print(result)
        expected = ['ComplexList', ['Protein', ['HGNC', 'CLSTN1']], ['Protein', ['HGNC', 'KLC1']]],
        self.assertEqual(expected, result)

        complex_name = 'ComplexList', 1
        self.assertHasNode(complex_name)

        p1_name = 'Protein', 'HGNC', 'CLSTN1'
        self.assertHasNode(p1_name)

        p2_name = 'Protein', 'HGNC', 'KLC1'
        self.assertHasNode(p2_name)

        self.assertHasEdge(complex_name, p1_name)
        self.assertHasEdge(complex_name, p2_name)

    def test_132(self):
        """Test multiple nested annotations on object"""
        statement = 'complex(p(HGNC:ARRB2),p(HGNC:APH1A)) -> pep(complex(SCOMP:"gamma Secretase Complex"))'
        result = self.parser.parse(statement)
        expected = [
            ['ComplexList', ['Protein', ['HGNC', 'ARRB2']], ['Protein', ['HGNC', 'APH1A']]],
            'increases',
            ['Activity', ['Complex', ['SCOMP', 'gamma Secretase Complex']], ['MolecularActivity', 'PeptidaseActivity']]
        ]
        self.assertEqual(expected, result)

        sub = 'ComplexList', 1
        self.assertHasNode(sub)

        sub_member_1 = 'Protein', 'HGNC', 'ARRB2'
        self.assertHasNode(sub_member_1)

        sub_member_2 = 'Protein', 'HGNC', 'APH1A'
        self.assertHasNode(sub_member_2)

        self.assertHasEdge(sub, sub_member_1)
        self.assertHasEdge(sub, sub_member_2)

        obj = 'Complex', 'SCOMP', 'gamma Secretase Complex'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, rel='increases')

    def test_133(self):
        """Test SNP annotation"""
        statement = 'g(HGNC:APP,sub(G,275341,C)) -> path(MESHD:"Alzheimer Disease")'
        result = self.parser.parse(statement)
        expected = [
            ['GeneVariant', ['HGNC', 'APP'], ['Variant', 'G', 275341, 'C']],
            'increases',
            ['Pathology', ['MESHD', 'Alzheimer Disease']]
        ]
        self.assertEqual(expected, result)

        sub = 'GeneVariant', 'HGNC', 'APP', 'Variant', 'G', 275341, 'C'
        self.assertHasNode(sub)

        obj = 'Pathology', 'MESHD', 'Alzheimer Disease'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj)

    def test_134(self):
        """Test phosphoralation tag"""
        statement = 'kin(p(SFAM:"GSK3 Family")) -> p(HGNC:MAPT,pmod(P))'
        result = self.parser.parse(statement)
        expected = [
            ['Activity', ['Protein', ['SFAM', 'GSK3 Family']], ['MolecularActivity', 'KinaseActivity']],
            'increases',
            ['ProteinVariant', ['HGNC', 'MAPT'], ['ProteinModification', 'P']]
        ]
        self.assertEqual(expected, result)

        sub = 'Protein', 'SFAM', 'GSK3 Family'
        self.assertHasNode(sub)

        obj = 'ProteinVariant', 'HGNC', 'MAPT', 'ProteinModification', 'P'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj)

    def test_135(self):
        """Test composite in sibject"""
        statement = 'composite(p(HGNC:CASP8),p(HGNC:FADD),a(ADO:"Abeta_42")) -> bp(GOBP:"neuron apoptotic process")'
        result = self.parser.parse(statement)
        expected = [
            ['Composite', ['Protein', ['HGNC', 'CASP8']], ['Protein', ['HGNC', 'FADD']],
             ['Abundance', ['ADO', 'Abeta_42']]],
            'increases',
            ['BiologicalProcess', ['GOBP', 'neuron apoptotic process']]
        ]
        self.assertEqual(expected, result)

        sub = 'Composite', 1
        self.assertHasNode(sub)

        sub_member_1 = 'Protein', 'HGNC', 'CASP8'
        self.assertHasNode(sub_member_1)

        sub_member_2 = 'Protein', 'HGNC', 'FADD'
        self.assertHasNode(sub_member_2)

        self.assertHasEdge(sub, sub_member_1)
        self.assertHasEdge(sub, sub_member_2)

        obj = 'BiologicalProcess', 'GOBP', 'neuron apoptotic process'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj)

    def test_136(self):
        """Test translocation in object"""
        statement = 'a(ADO:"Abeta_42") -> tloc(a(CHEBI:"calcium(2+)"),fromLoc(MESHCS:"Cell Membrane"),' \
                    'toLoc(MESHCS:"Intracellular Space"))'
        result = self.parser.parse(statement)
        expected = [
            ['Abundance', ['ADO', 'Abeta_42']],
            'increases',
            ['Translocation',
             ['Abundance', ['CHEBI', 'calcium(2+)']],
             ['MESHCS', 'Cell Membrane'],
             ['MESHCS', 'Intracellular Space']
             ]
        ]
        self.assertEqual(expected, result)

        sub = 'Abundance', 'ADO', 'Abeta_42'
        self.assertHasNode(sub)

        obj = 'Abundance', 'CHEBI', 'calcium(2+)'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj)

    @unittest.expectedFailure
    def test_141(self):
        """F single argument translocation"""
        statement = 'tloc(a("T-Lymphocytes")) -- p(MGI:Cxcr3)'
        result = self.parser.parse(statement)

        expected = [
            ['Translocation', ['Abundance', ['T-Lymphocytes']]],
            'association',
            ['Protein', ['MGI', 'Cxcr3']]
        ]

        self.assertEqual(expected, result)

        sub = ''
        self.assertHasNode(sub)

        obj = ''
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj)

    def test_253b(self):
        """Test reaction"""
        statement = 'pep(p(SFAM:"CAPN Family")) -> reaction(reactants(p(HGNC:CDK5R1)),products(p(HGNC:CDK5)))'
        result = self.parser.parse(statement)
        expected = [
            ['Activity', ['Protein', ['SFAM', 'CAPN Family']], ['MolecularActivity', 'PeptidaseActivity']],
            'increases',
            ['Reaction',
             [['Protein', ['HGNC', 'CDK5R1']]],
             [['Protein', ['HGNC', 'CDK5']]]
             ]
        ]
        self.assertEqual(expected, result)

        sub = 'Protein', 'SFAM', 'CAPN Family'
        self.assertHasNode(sub)

        obj = 'Reaction', 1
        self.assertHasNode(obj)

        obj_member_1 = 'Protein', 'HGNC', 'CDK5R1'
        self.assertHasNode(obj_member_1)

        obj_member_2 = 'Protein', 'HGNC', 'CDK5'
        self.assertHasNode(obj_member_2)

        self.assertHasEdge(obj, obj_member_1)
        self.assertHasEdge(obj, obj_member_2)

        self.assertHasEdge(sub, obj)

    def test_140(self):
        """Test protein substitution"""
        statement = 'p(HGNC:APP,sub(N,10,Y)) -> path(MESHD:"Alzheimer Disease")'
        result = self.parser.parse(statement)
        expected = [
            ['ProteinVariant', ['HGNC', 'APP'], ['Variant', 'N', 10, 'Y']],
            'increases',
            ['Pathology', ['MESHD', 'Alzheimer Disease']]
        ]
        self.assertEqual(expected, result)

        sub = 'ProteinVariant', 'HGNC', 'APP', 'Variant', 'N', 10, 'Y'
        self.assertHasNode(sub)

        sub_parent = 'Protein', 'HGNC', 'APP'
        self.assertHasNode(sub_parent)
        self.assertHasEdge(sub, sub_parent)

        obj = 'Pathology', 'MESHD', 'Alzheimer Disease'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj)


class TestRelationships(TestTokenParserBase):
    def test_315a(self):
        """"""
        statement = 'act(p(HGNC:HMGCR), ma(cat)) rateLimitingStepOf bp(GOBP:"cholesterol biosynthetic process")'
        result = self.parser.parse(statement)
        expected_result = [
            ['Activity', ['Protein', ['HGNC', 'HMGCR']], ['MolecularActivity', 'CatalyticActivity']],
            'rateLimitingStepOf',
            ['BiologicalProcess', ['GOBP', 'cholesterol biosynthetic process']]
        ]
        self.assertEqual(expected_result, result)

        sub = 'Protein', 'HGNC', 'HMGCR'
        self.assertHasNode(sub)

        obj = 'BiologicalProcess', 'GOBP', 'cholesterol biosynthetic process'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj)

    def test_317a(self):
        """Abundances and activities"""
        statement = 'p(PFH:"Hedgehog Family") =| act(p(HGNC:PTCH1))'
        result = self.parser.parse(statement)
        expected_result = [
            ['Protein', ['PFH', 'Hedgehog Family']],
            'directlyDecreases',
            ['Activity', ['Protein', ['HGNC', 'PTCH1']]]
        ]
        self.assertEqual(expected_result, result)

        sub = 'Protein', 'PFH', 'Hedgehog Family'
        self.assertHasNode(sub)

        obj = 'Protein', 'HGNC', 'PTCH1'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation='directlyDecreases')

    def test_317b(self):
        """Transcription"""
        statement = 'act(p(HGNC:FOXO3),ma(tscript)) =| r(HGNC:MIR21)'
        result = self.parser.parse(statement)
        expected_result = [
            ['Activity', ['Protein', ['HGNC', 'FOXO3']], ['MolecularActivity', 'TranscriptionalActivity']],
            'directlyDecreases',
            ['RNA', ['HGNC', 'MIR21']]]
        self.assertEqual(expected_result, result)

        sub = 'Protein', 'HGNC', 'FOXO3'
        self.assertHasNode(sub)

        obj = 'RNA', 'HGNC', 'MIR21'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation='directlyDecreases')

    def test_317c(self):
        """Target is a BEL statement"""
        statement = 'p(HGNC:CLSPN) => (act(p(HGNC:ATR), ma(kin)) => p(HGNC:CHEK1, pmod(P)))'
        result = self.parser.parse(statement)
        expected_result = [['Protein', ['HGNC', 'CLSPN']], 'directlyIncreases',
                           ['Activity', ['Protein', ['HGNC', 'ATR']], ['MolecularActivity', 'KinaseActivity']],
                           'directlyIncreases',
                           ['ProteinVariant', ['HGNC', 'CHEK1'], ['ProteinModification', 'P']]]
        self.assertEqual(expected_result, result)

    def test_317d(self):
        """Self-referential relationships"""
        statement = 'p(HGNC:GSK3B, pmod(P, S, 9)) =| act(p(HGNC:GSK3B), ma(kin))'
        result = self.parser.parse(statement)
        expected_result = [['ProteinVariant', ['HGNC', 'GSK3B'], ['ProteinModification', 'P', 'S', 9]],
                           'directlyDecreases',
                           ['Activity', ['Protein', ['HGNC', 'GSK3B']], ['MolecularActivity', 'KinaseActivity']]]
        self.assertEqual(expected_result, result)

        sub = 'ProteinVariant', 'HGNC', 'GSK3B', 'ProteinModification', 'P', 'S', 9
        self.assertHasNode(sub)

        obj = 'Protein', 'HGNC', 'GSK3B'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation='directlyDecreases')

    def test_331a(self):
        """"""
        statement = 'g(HGNC:AKT1) orthologous g(MGI:AKT1)'
        result = self.parser.parse(statement)
        expected_result = [['Gene', ['HGNC', 'AKT1']], 'orthologous', ['Gene', ['MGI', 'AKT1']]]
        self.assertEqual(expected_result, result)

        sub = 'Gene', 'HGNC', 'AKT1'
        self.assertHasNode(sub)

        obj = 'Gene', 'MGI', 'AKT1'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation='orthologous')

    def test_332a(self):
        """"""
        statement = 'g(HGNC:AKT1) :> r(HGNC:AKT1)'
        result = self.parser.parse(statement)
        expected_result = [['Gene', ['HGNC', 'AKT1']], 'transcribedTo', ['RNA', ['HGNC', 'AKT1']]]
        self.assertEqual(expected_result, result)

        sub = 'Gene', 'HGNC', 'AKT1'
        self.assertHasNode(sub)

        obj = 'RNA', 'HGNC', 'AKT1'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation='transcribedTo')

    def test_333a(self):
        """"""
        statement = 'r(HGNC:AKT1) >> p(HGNC:AKT1)'
        result = self.parser.parse(statement)
        expected_result = [['RNA', ['HGNC', 'AKT1']], 'translatedTo', ['Protein', ['HGNC', 'AKT1']]]
        self.assertEqual(expected_result, result)

        sub = 'RNA', 'HGNC', 'AKT1'
        self.assertHasNode(sub)

        obj = 'Protein', 'HGNC', 'AKT1'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation='translatedTo')

    def test_345a(self):
        """"""
        statement = 'pathology(MESH:Psoriasis) isA pathology(MESH:"Skin Diseases")'
        result = self.parser.parse(statement)
        expected_result = [['Pathology', ['MESH', 'Psoriasis']], 'isA', ['Pathology', ['MESH', 'Skin Diseases']]]
        self.assertEqual(expected_result, result)

        sub = 'Pathology', 'MESH', 'Psoriasis'
        self.assertHasNode(sub)

        obj = 'Pathology', 'MESH', 'Skin Diseases'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation='isA')

    def test_346a(self):
        """"""
        statement = 'rxn(reactants(a(CHEBI:"(S)-3-hydroxy-3-methylglutaryl-CoA"),a(CHEBI:NADPH), \
            a(CHEBI:hydron)),products(a(CHEBI:mevalonate), a(CHEBI:"CoA-SH"), a(CHEBI:"NADP(+)"))) \
            subProcessOf bp(GOBP:"cholesterol biosynthetic process")'
        result = self.parser.parse(statement)
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
        self.assertEqual(expected_result, result)

        sub = 'Reaction', 1
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

        obj = 'BiologicalProcess', 'GOBP', 'cholesterol biosynthetic process'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation='subProcessOf')

    def test_member_list(self):
        statement = 'p(PKC:a) hasMembers list(p(HGNC:PRKCA), p(HGNC:PRKCB), p(HGNC:PRKCD), p(HGNC:PRKCE))'
        result = self.parser.parse(statement)
        expected_result = [['Protein', ['PKC', 'a']],
                           'hasMembers',
                           [['Protein', ['HGNC', 'PRKCA']],
                            ['Protein', ['HGNC', 'PRKCB']],
                            ['Protein', ['HGNC', 'PRKCD']],
                            ['Protein', ['HGNC', 'PRKCE']]]]
        self.assertEqual(expected_result, result)

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
