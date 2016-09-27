import logging
import unittest

from pybel.parsers.bel_parser import Parser

log = logging.getLogger(__name__)


class TestTokenParserBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = Parser()

    def setUp(self):
        self.parser.graph.clear()
        self.parser.node_count = 0
        self.parser.annotations = {}


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

        self.assertIn(node, self.parser.graph)

    def test_214a(self):
        statement = 'geneAbundance(HGNC:AKT1)'

        result = self.parser.parse(statement)
        expected_result = ['Gene', ['HGNC', 'AKT1']]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'Gene', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)

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
        expected_result = ['ProteinModified', ['HGNC', 'AKT1'], ['ProteinModification', 'Ph', 'S', 473]]
        self.assertEqual(expected_result, result)

    def test_221b(self):
        """Test default BEL namespace and 3-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(Ph, Ser, 473))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinModified', ['HGNC', 'AKT1'], ['ProteinModification', 'Ph', 'Ser', 473]]
        self.assertEqual(expected_result, result)

    def test_221c(self):
        """Test PSI-MOD namespace and 3-letter amino acid code:"""
        statement = 'p(HGNC:AKT1, pmod(MOD:PhosRes, Ser, 473))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinModifed', ['HGNC', 'AKT1'], ['ProteinModification', ['MOD', 'PhosRes'], 'Ser', 473]]
        self.assertEqual(expected_result, result)

    def test_221e(self):
        """Test HRAS palmitoylated at an unspecified residue. Default BEL namespace"""
        statement = 'p(HGNC:HRAS, pmod(Palm))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinModified', ['HGNC', 'HRAS'], ['ProteinModification', 'Palm']]
        self.assertEqual(expected_result, result)

    def test_222a(self):
        """Test reference allele"""
        statement = 'p(HGNC:CFTR, var(=))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinModified', ['HGNC', 'CFTR'], ['Variant', '=']]
        self.assertEqual(expected_result, result)

    def test_222b(self):
        """Test unspecified variant"""
        statement = 'p(HGNC:CFTR, var(?))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinModified', ['HGNC', 'CFTR'], ['Variant', '?']]
        self.assertEqual(expected_result, result)

    def test_222c(self):
        """Test substitution"""
        statement = 'p(HGNC:CFTR, var(p.Gly576Ala))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinModified', ['HGNC', 'CFTR'], ['Variant', 'Gly', 576, 'Ala']]
        self.assertEqual(expected_result, result)

    def test_222d(self):
        """deletion"""
        statement = 'p(HGNC:CFTR, var(p.Phe508del))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinModified', ['HGNC', 'CFTR'], ['Variant', 'Phe', 508, 'del']]
        self.assertEqual(expected_result, result)

    def test_222e(self):
        """SNP"""
        statement = 'g(SNP:rs113993960, var(delCTT))'
        result = self.parser.parse(statement)
        expected_result = ['GeneModified', ['SNP', 'rs113993960'], ['Variant', 'del', 'CTT']]
        self.assertEqual(expected_result, result)

    def test_222f(self):
        """chromosome"""
        statement = 'g(REF:NC_000007.13, var(g.117199646_117199648delCTT))'
        result = self.parser.parse(statement)
        expected_result = ['GeneModified', ['REF', 'NC_000007.13'], ['Variant', 117199646, 117199648, 'del', 'CTT']]
        self.assertEqual(expected_result, result)

    def test_222g(self):
        """gene-coding DNA reference sequence"""
        statement = 'g(HGNC:CFTR, var(c.1521_1523delCTT))'
        result = self.parser.parse(statement)
        expected_result = ['Gene', ['HGNC', 'CFTR'], ['Variant', 'c', 1521, 1523, 'del', 'CTT']]
        self.assertEqual(expected_result, result)

    def test_222h(self):
        """RNA coding reference sequence"""
        statement = 'r(HGNC:CFTR, var(c.1521_1523delCTT))'
        result = self.parser.parse(statement)
        expected_result = ['RNAModified', ['HGNC', 'CFTR'], ['Variant', 'c', 1521, 1523, 'del', 'CTT']]
        self.assertEqual(expected_result, result)

    def test_222i(self):
        """RNA reference sequence"""
        statement = 'r(HGNC:CFTR, var(r.1653_1655delcuu))'
        result = self.parser.parse(statement)
        expected_result = ['RNAModified', ['HGNC', 'CFTR'], ['Variant', 'r', 1653, 1655, 'del', 'cuu']]
        self.assertEqual(expected_result, result)

    def test_223a(self):
        """fragment with known start/stop"""
        statement = 'p(HGNC:YFG, frag(5_20))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinModified', ['HGNC', 'YFG'], ['Fragment', 5, 20]]
        self.assertEqual(expected_result, result)

    def test_223b(self):
        """amino-terminal fragment of unknown length"""
        statement = 'p(HGNC:YFG, frag(1_?))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinModified', ['HGNC', 'YFG'], ['Fragment', 1, '?']]
        self.assertEqual(expected_result, result)

    def test_223c(self):
        """carboxyl-terminal fragment of unknown length"""
        statement = 'p(HGNC:YFG, frag(?_*))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinModified', ['HGNC', 'YFG'], ['Fragment', '?', '*']]
        self.assertEqual(expected_result, result)

    def test_223d(self):
        """fragment with unknown start/stop"""
        statement = 'p(HGNC:YFG, frag(?))'
        result = self.parser.parse(statement)
        expected_result = ['ProteinModified', ['HGNC', 'YFG'], ['Fragment', '?']]
        self.assertEqual(expected_result, result)

    def test_223e(self):
        """fragment with unknown start/stop and a descriptor"""
        statement = 'p(HGNC:YFG, frag(?, 55kD))'
        result = self.parser.parse(statement)
        expected_result = []
        self.assertEqual(expected_result, result)

    def test_224a(self):
        statement = 'p(HGNC:AKT1, loc(MESHCS:Cytoplasm))'
        result = self.parser.parse(statement)
        expected_result = ['Protein', ['HGNC', 'AKT1'], ['Location', ['MESHCS', 'Cytoplasm']]]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = ('Protein', 'HGNC', 'AKT1')
        self.assertEqual(expected_node, node)

    def test_231a(self):
        """"""
        statement = 'bp(GOBP:"cell cycle arrest")'
        result = self.parser.parse(statement)
        expected_result = ['BiologicalProcess', ['GOBP', 'cell cycle arrest']]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = ('BiologicalProcess', 'GOBP', 'cell cycle arrest')
        self.assertEqual(expected_node, node)

    def test_231b(self):
        """"""
        statement = 'bp(GOBP:angiogenesis)'
        result = self.parser.parse(statement)
        expected_result = ['BiologicalProcess', ['GOBP', 'angiogenesis']]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = ('BiologicalProcess', 'GOBP', 'angiogenesis')
        self.assertEqual(expected_node, node)

    def test_232a(self):
        statement = 'pathology(MESHD:adenocarcinoma)'
        result = self.parser.parse(statement)
        expected_result = ['Pathology', ['MESHD', 'adenocarcinoma']]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'Pathology', 'MESHD', 'adenocarcinoma'
        self.assertEqual(expected_node, node)

    def test_233a(self):
        """"""
        statement = 'act(p(HGNC:AKT1))'
        result = self.parser.parse(statement)
        expected_result = ['Activity', ['Protein', ['HGNC', 'AKT1']]]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'Protein', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)

    def test_233b(self):
        """"""
        statement = 'kin(p(HGNC:AKT1))'
        result = self.parser.parse(statement)
        expected_result = ['Activity', ['Protein', ['HGNC', 'AKT1']], ['MolecularActivity', 'KinaseActivity']]
        self.assertEqual(expected_result, result)

    def test_241a(self):
        """default BEL namespace, transcriptional activity"""
        statement = 'act(p(HGNC:FOXO1), ma(tscript))'
        result = self.parser.parse(statement)
        expected_result = ['Activity', ['Protein', ['HGNC', 'FOXO1']], ['MolecularActivity', 'TranscriptionalActivity']]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'Protein', 'HGNC', 'FOXO1'
        self.assertEqual(expected_node, node)

    def test_241b(self):
        """GO molecular function namespace, transcriptional activity"""
        statement = 'act(p(HGNC:FOXO1), ma(GO:"nucleic acid binding transcription factor activity"))'
        result = self.parser.parse(statement)
        expected_result = ['Activity', ['Protein', ['HGNC', 'FOXO1']],
                           ['MolecularActivity', ['GO', 'nucleic acid binding transcription factor activity']]]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'Protein', 'HGNC', 'FOXO1'
        self.assertEqual(expected_node, node)

    '''node = self.parser.canonicalize_node(result)
        expected_node = ()
        self.assertEqual(expected_node, node)'''

    def test_224c(self):
        """default BEL namespace, kinase activity"""
        statement = 'act(p(HGNC:AKT1), ma(kin))'
        result = self.parser.parse(statement)
        expected_result = ['Activity', ['Protein', ['HGNC', 'AKT1']], ['MolecularActivity', 'KinaseActivity']]
        self.assertEqual(expected_result, result)

        node = self.parser.canonicalize_node(result)
        expected_node = 'Protein', 'HGNC', 'AKT1'
        self.assertEqual(expected_node, node)

    def test_224d(self):
        """GO molecular function namespace, kinase activity"""
        statement = 'act(p(HGNC:AKT1), ma(GO:"kinase activity"))'
        result = self.parser.parse(statement)
        expected_result = ['Activity', ['Protein', ['HGNC', 'AKT1']], ['MolecularActivity', ['GO', 'kinase activity']]]
        self.assertEqual(expected_result, result)

    def test_251a(self):
        """translocation example"""
        statement = 'tloc(p(HGNC:EGFR), fromLoc(GOCC:"cell surface"), toLoc(GOCC:endosome))'
        result = self.parser.parse(statement)
        expected_result = ['Translocation', ['Protein', ['HGNC', 'EGFR']], ['GOCC', 'cell surface'],
                           ['GOCC', 'endosome']]
        self.assertEqual(expected_result, result)

    def test_251b(self):
        """cell secretion long form"""
        statement = 'tloc(p(HGNC:EGFR), fromLoc(GOCC:intracellular), toLoc(GOCC:"extracellular space"))'
        result = self.parser.parse(statement)
        expected_result = ['Translocation', ['Protein', ['HGNC', 'EGFR']], ['GOCC', 'intracellular'],
                           ['GOCC', 'extracellular space']]
        self.assertEqual(expected_result, result)

    def test_251c(self):
        """cell secretion short form"""
        statement = 'sec(p(HGNC:EGFR))'
        result = self.parser.parse(statement)
        expected_result = ['CellSecretion', ['Protein', ['HGNC', 'EGFR']]]
        self.assertEqual(expected_result, result)

    def test_251d(self):
        """cell surface expression long form"""
        statement = 'tloc(p(HGNC:EGFR), fromLoc(GOCC:intracellular), toLoc(GOCC:"cell surface"))'
        result = self.parser.parse(statement)
        expected_result = ['Translocation', ['Protein', ['HGNC', 'EGFR']], ['GOCC', 'intracellular'],
                           ['GOCC', 'cell surface']]
        self.assertEqual(expected_result, result)

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

    def test_253a(self):
        """"""
        statement = 'rxn(reactants(a(CHEBI:superoxide)),products(a(CHEBI:"hydrogen peroxide"), a(CHEBI: "oxygen"))'
        result = self.parser.parse(statement)
        expected_result = ['Reaction', [['Abundance', ['CHEBI', 'superoxide']]],
                           [['Abundance', ['CHEBI', 'hydrogen peroxide']], ['Abundance', ['CHEBI', 'oxygen']]]]
        self.assertEqual(expected_result, result)

    def test_261a(self):
        """RNA abundance of fusion with known breakpoints"""
        statement = 'r(fus(HGNC:TMPRSS2, r.1_79, HGNC:ERG, r.312_5034))'
        result = self.parser.parse(statement)
        expected_result = ['RNA', ['Fusion', ['HGNC', 'TMPRSS2'], ['r', 1, 79], ['HGNC', 'ERG'], ['r', 312, 5034]]]
        self.assertEqual(expected_result, result)

    def test_261b(self):
        """RNA abundance of fusion with unspecified breakpoints"""
        statement = 'r(fus(HGNC:TMPRSS2, ?, HGNC:ERG, ?))'
        result = self.parser.parse(statement)
        expected_result = ['RNA', ['Fusion', ['HGNC', 'TMPRSS2'], '?', ['HGNC', 'ERG'], '?']]
        self.assertEqual(expected_result, result)


class TestRelationships(TestTokenParserBase):
    def test_315a(self):
        """"""
        statement = 'act(p(HGNC:HMGCR), ma(cat)) rateLimitingStepOf bp(GOBP:"cholesterol biosynthetic process")'
        result = self.parser.parse(statement)
        expected_result = [[], 'rateLimitingStepOf', []]
        self.assertEqual(expected_result, result)

    def test_317a(self):
        """Abundances and activities"""
        statement = 'p(PFH:"Hedgehog Family") =| act(p(HGNC:PTCH1))'
        result = self.parser.parse(statement)
        expected_result = [['Protein', ['PFH', 'Hedgehog Family']], 'decreases',
                           ['Activity', ['Protein', ['HGNC', 'PTCH1']]]]
        self.assertEqual(expected_result, result)

    def test_317b(self):
        """Transcription"""
        statement = 'act(p(HGNC:FOXO3),ma(tscript)) =| r(HGNC:MIR21)'
        result = self.parser.parse(statement)
        expected_result = [
            ['Activity', ['Protein', ['HGNC', 'FOXO3']], ['MolecularActivity', 'TranscriptionalActivity']], 'decreases',
            ['RNA', ['HGNC', 'MIR21']]]
        self.assertEqual(expected_result, result)

    def test_317c(self):
        """Target is a BEL statement"""
        statement = 'p(HGNC:CLSPN) => (act(p(HGNC:ATR), ma(kin)) => p(HGNC:CHEK1, pmod(P)))'
        result = self.parser.parse(statement)
        expected_result = [['Protein', ['HGNC', 'CLSPN']], 'directlyIncreases',
                           ['Activity', ['Protein', ['HGNC', 'ATR']], ['MolecularActivity', 'KinaseActivity']],
                           'directlyIncreases',
                           ['ProteinModified', ['HGNC', 'CHEK1'], ['ProteinModification', 'phosphorylation']]]
        self.assertEqual(expected_result, result)

    def test_317d(self):
        """Self-referential relationships"""
        statement = 'p(HGNC:GSK3B, pmod(P, S, 9)) =| act(p(HGNC:GSK3B), ma(kin))'
        result = self.parser.parse(statement)
        expected_result = [['ProteinModified', ['HGNC', 'GSK3B'], ['ProteinModification', 'P', 'S', 9]],
                           'directlyDecreases',
                           ['Activity', ['Protein', ['HGNC', 'GSK3B']], ['MolecularActivity', 'KinaseActivity']]]
        self.assertEqual(expected_result, result)

    def test_331a(self):
        """"""
        statement = 'g(HGNC:AKT1) orthologous g(MGI:AKT1)'
        result = self.parser.parse(statement)
        expected_result = [['Gene', ['HGNC', 'AKT1']], 'orthologous', ['Gene', ['MGI', 'AKT1']]]
        self.assertEqual(expected_result, result)

    def test_332a(self):
        """"""
        statement = 'g(HGNC:AKT1) :> r(HGNC:AKT1)'
        result = self.parser.parse(statement)
        expected_result = [['Gene', ['HGNC', 'AKT1']], 'transcribedTo', ['RNA', ['HGNC', 'AKT1']]]
        self.assertEqual(expected_result, result)

    def test_333a(self):
        """"""
        statement = 'r(HGNC:AKT1) >> p(HGNC:AKT1)'
        result = self.parser.parse(statement)
        expected_result = [['RNA', ['HGNC', 'AKT1']], 'translatedTo', ['Protein', ['HGNC', 'AKT1']]]
        self.assertEqual(expected_result, result)

    def test_345a(self):
        """"""
        statement = 'pathology(MESH:Psoriasis) isA pathology(MESH:"Skin Diseases")'
        result = self.parser.parse(statement)
        expected_result = [['Pathology', ['MESH', 'Psoriasis']], 'isA', ['Pathology', ['MESH', 'Skin Diseases']]]
        self.assertEqual(expected_result, result)

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
                             ]], 'subProcessOf', ['BiologicalProcess', ['GOBP', 'cholesterol biosynthetic process']]]
        self.assertEqual(expected_result, result)


class Test2(TestTokenParserBase):
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

    def test_113(self):
        """Test annotation"""
        statement = 'act(p(HGNC:CHIT1)) biomarkerFor path(MESHD:"Alzheimer Disease")'
        result = self.parser.parse(statement)
        expected = [
            ['activity', ['Protein', ['HGNC', 'CHIT1']]],
            'biomarkerFor',
            ['Pathology', ['MESHD', 'Alzheimer Disease']]
        ]
        self.assertEqual(expected, result)

    def test_121(self):
        """Test nested definitions"""
        statement = 'pep(complex(p(HGNC:F3),p(HGNC:F7))) directlyIncreases pep(p(HGNC:F9))'
        result = self.parser.parse(statement)
        expected = [
            ['peptidaseActivity',
             ['Complex', ['Protein', ['HGNC', 'F3']], ['Protein', ['HGNC', 'F7']]]
             ],
            'directlyIncreases',
            ['peptidaseActivity', ['Protein', ['HGNC', 'F9']]]
        ]
        self.assertEqual(expected, result)

    def test_131(self):
        """Test complex statement"""
        statement = 'complex(p(HGNC:CLSTN1),p(HGNC:KLC1)) -> tport(p(HGNC:KLC1))'
        result = self.parser.parse(statement)
        expected = [
            ['Complex', ['Protein', ['HGNC', 'CLSTN1']], ['Protein', ['HGNC', 'KLC1']]],
            'increases',
            ['tport', ['Protein', ['HGNC', 'KLC1']]]
        ]
        self.assertEqual(expected, result)

    def test_132(self):
        """Test multiple nested annotations on object"""
        statement = 'complex(p(HGNC:ARRB2),p(HGNC:APH1A)) -> pep(complex(SCOMP:"gamma Secretase Complex"))'
        result = self.parser.parse(statement)
        expected = [
            ['Complex', ['Protein', ['HGNC', 'ARRB2']], ['Protein', ['HGNC', 'APH1A']]],
            'increases',
            ['pep', ['Complex', ['SCOMP', 'gamma Secretase Complex']]]
        ]
        self.assertEqual(expected, result)

    def test_133(self):
        """Test SNP annotation"""
        statement = 'g(HGNC:APP,sub(G,275341,C)) -> path(MESHD:"Alzheimer Disease")'
        result = self.parser.parse(statement)
        expected = [
            ['Gene', ['HGNC', 'APP'], ['GeneSubstitution', 'G', 275341, 'C']],
            'increases',
            ['Pathology', ['MESHD', 'Alzheimer Disease']]
        ]
        self.assertEqual(expected, result)

    def test_134(self):
        """Test phosphoralation tag"""
        statement = 'kin(p(SFAM:"GSK3 Family")) -> p(HGNC:MAPT,pmod(P))'
        result = self.parser.parse(statement)
        expected = [
            ['kin', ['Protein', ['SFAM', 'GSK3 Family']]],
            'increases',
            ['Protein', ['HGNC', 'MAPT'], ['ProteinModification', 'P']]
        ]
        self.assertEqual(expected, result)

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

    def test_136(self):
        """Test translocation in object"""
        statement = 'a(ADO:"Abeta_42") -> tloc(a(CHEBI:"calcium(2+)"),fromLoc(MESHCS:"Cell Membrane"),' \
                    'toLoc(MESHCS:"Intracellular Space"))'
        result = self.parser.parse(statement)
        expected = [
            ['Abundance', ['ADO', 'Abeta_42']],
            'increases',
            ['translocation',
             ['Abundance', ['CHEBI', 'calcium(2+)']],
             ['MESHCS', 'Cell Membrane'],
             ['MESHCS', 'Intracellular Space']
             ]
        ]
        self.assertEqual(expected, result)

    def test_141(self):
        """F single argument translocation"""
        statement = 'tloc(a("T-Lymphocytes")) -- p(MGI:Cxcr3)'
        result = self.parser.parse(statement)
        '''
        expected = [
            ['tloc', ['Abundance', ['T-Lymphocytes']]],
            'association',
            ['Protein', ['MGI', 'Cxcr3']]
        ]
        '''

        expected = [
            ['activity', ['Abundance', ['T-Lymphocytes']], ['molecularActivity', 'tloc']],
            'association',
            ['Protein', ['MGI', 'Cxcr3']]
        ]

        self.assertEqual(expected, result)

    def test_253b(self):
        """Test reaction"""
        statement = 'pep(p(SFAM:"CAPN Family")) -> reaction(reactants(p(HGNC:CDK5R1)),products(p(HGNC:CDK5)))'
        result = self.parser.parse(statement)
        expected = [
            ['pep', ['Protein', ['SFAM', 'CAPN Family']]],
            'increases',
            ['Reaction',
             [['Protein', ['HGNC', 'CDK5R1']],
              [['Protein', ['HGNC', 'CDK5']]]
              ]
             ]
        ]
        self.assertEqual(expected, result)

    def test_140(self):
        """Test protein substitution"""
        statement = 'p(HGNC:APP,sub(N,10,Y)) -> path(MESHD:"Alzheimer Disease")'
        result = self.parser.parse(statement)
        expected = [
            ['Protein', ['HGNC', 'APP'], ['ProteinSubstitution', 'N', 10, 'Y']],
            'increases',
            ['Pathology', ['MESHD', 'Alzheimer Disease']]
        ]
        self.assertEqual(expected, result)
