import logging
import unittest

from pybel.parsers.bel_parser import Parser

log = logging.getLogger(__name__)


class TestTokenParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = Parser()

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
        statement = 'proteinAbundance(HGNC:CAT) decreases (abundance(CHEBI:"hydrogen peroxide") increases biologicalProcess(GO:"apoptotic process"))'
        result = self.parser.parse(statement)
        expected = [
            ['Protein', ['HGNC', 'CAT']],
            'decreases',
            ['Abundance', ['CHEBI', 'hydrogen peroxide']],
            'increases',
            ['Process', ['GO', 'apoptotic process']]
        ]
        self.assertEqual(expected, result)

    def test_112(self):
        """Test when object is simple triple, with whitespace"""
        statement = 'proteinAbundance(HGNC:CAT) decreases ( abundance(CHEBI:"hydrogen peroxide") increases biologicalProcess(GO:"apoptotic process") )'
        result = self.parser.parse(statement)
        expected = [
            ['Protein', ['HGNC', 'CAT']],
            'decreases',
            ['Abundance', ['CHEBI', 'hydrogen peroxide']],
            'increases',
            ['Process', ['GO', 'apoptotic process']]
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
        statement = 'peptidaseActivity(complexAbundance(proteinAbundance(HGNC:F3),proteinAbundance(HGNC:F7))) directlyIncreases peptidaseActivity(proteinAbundance(HGNC:F9))'
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
            ['Process', ['GOBP', 'neuron apoptotic process']]
        ]
        self.assertEqual(expected, result)

    def test_136(self):
        """Test translocation in object"""
        statement = 'a(ADO:"Abeta_42") -> translocation(a(CHEBI:"calcium(2+)"), fromLoc(MESHCS:"Cell Membrane"), toLoc(MESHCS:"Intracellular Space"))'
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

    def test_139(self):
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
