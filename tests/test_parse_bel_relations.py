"""
This class requires the parser to be fully compiled, and takes a long time to run.
"""


import json
import logging
import unittest

from pybel.parser import BelParser
from pybel.parser.utils import subdict_matches, any_subdict_matches

log = logging.getLogger(__name__)


class TestTokenParserBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = BelParser()

    def setUp(self):
        self.parser.graph.clear()
        self.parser.node_count = 0
        self.parser.annotations = {}

    def assertHasNode(self, member, msg=None, **kwargs):
        self.assertIn(member, self.parser.graph)
        if kwargs:
            msg_format = 'Wrong node properties. expected {} but got {}'
            self.assertTrue(subdict_matches(self.parser.graph.node[member], kwargs, ),
                            msg=msg_format.format(member, kwargs, self.parser.graph.node[member]))

    def assertHasEdge(self, u, v, msg=None, **kwargs):
        self.assertTrue(self.parser.graph.has_edge(u, v), msg='Edge ({}, {}) not in graph'.format(u, v))
        if kwargs:
            msg_format = 'No edge with correct properties. expected {} but got {}'
            self.assertTrue(any_subdict_matches(self.parser.graph.edge[u][v], kwargs),
                            msg=msg_format.format(kwargs, self.parser.graph.edge[u][v]))


class TestEnsure(TestTokenParserBase):
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

    def ensure_no_dup_nodes(self):
        """Ensure node isn't added twice, even if from different statements"""
        s1 = 'g(HGNC:AKT1)'
        s2 = 'deg(g(HGNC:AKT1))'
        s3 = 'deg(g(HGNC:AKT1)) -- g(HGNC:AKT1)'

        self.parser.parseString(s1)
        self.parser.parseString(s2)
        self.parser.parseString(s3)

        gene = 'Gene', 'HGNC', 'AKT1'

        self.assertEqual(1, self.parser.graph)
        self.assertHasNode(gene, type='Gene', namespace='HGNC', value='AKT1')

    def ensure_no_dup_edges(self):
        """Ensure node and edges aren't added twice, even if from different statements and has origin completion"""
        s1 = 'g(HGNC:AKT1)'
        s2 = 'deg(p(HGNC:AKT1))'
        s3 = 'deg(p(HGNC:AKT1)) -- g(HGNC:AKT1)'

        self.parser.parseString(s1)
        self.parser.parseString(s2)
        self.parser.parseString(s3)

        protein = 'Protein', 'HGNC', 'AKT1'
        rna = 'RNA', 'HGNC', 'AKT1'
        gene = 'Gene', 'HGNC', 'AKT1'

        self.assertEqual(3, self.parser.graph)
        self.assertHasNode(protein, type='Protein', namespace='HGNC', value='AKT1')
        self.assertHasNode(rna, type='RNA', namespace='HGNC', value='AKT1')
        self.assertHasNode(gene, type='Gene', namespace='HGNC', value='AKT1')

        self.assertEqual(2, self.parser.graph.number_of_edges())

        self.assertHasEdge(gene, rna, relation='transcribedTo')
        self.assertEqual(1, self.parser.graph.number_of_edges(gene, rna))

        self.assertHasEdge(rna, protein, relation='translatedTo')
        self.assertEqual(1, self.parser.graph.number_of_edges(rna, protein))

@unittest.skip
class TestRelationshipsRandom(TestTokenParserBase):
    def test_135(self):
        """Test composite in subject"""
        statement = 'composite(p(HGNC:CASP8),p(HGNC:FADD),a(ADO:"Abeta_42")) -> bp(GOBP:"neuron apoptotic process")'
        result = self.parser.parseString(statement).asList()
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

        self.assertHasEdge(sub, sub_member_1, relation='hasComponent')
        self.assertHasEdge(sub, sub_member_2, relation='hasComponent')

        obj = 'BiologicalProcess', 'GOBP', 'neuron apoptotic process'
        self.assertHasNode(obj)

        self.assertHasEdge(sub, obj, relation='increases')

    def test_increases_withTlocObject(self):
        """Test translocation in object"""
        statement = 'a(ADO:"Abeta_42") -> tloc(a(CHEBI:"calcium(2+)"),fromLoc(MESHCS:"Cell Membrane"),' \
                    'toLoc(MESHCS:"Intracellular Space"))'
        result = self.parser.parseString(statement)

        expected = [
            ['Abundance', ['ADO', 'Abeta_42']],
            'increases',
            ['Translocation',
             ['Abundance', ['CHEBI', 'calcium(2+)']],
             ['MESHCS', 'Cell Membrane'],
             ['MESHCS', 'Intracellular Space']
             ]
        ]
        self.assertEqual(expected, result.asList())

        expected_dict = {
            'subject': {
                'function': 'Abundance',
                'identifier': {
                    'namesapce': 'ADO',
                    'name': 'Abeta_42'
                }
            },
            'relation': 'increases',
            'object': {
                'function': 'Abundance',
                'identifier': {
                    'namesapce': 'CHEBI',
                    'name': 'calcium(2+)'
                },
                'modifier': {
                    'name': 'Translocation',
                }
            }
        }

        self.assertEqual(expected_dict, result.asDict())

        sub = 'Abundance', 'ADO', 'Abeta_42'
        self.assertHasNode(sub)

        obj = 'Abundance', 'CHEBI', 'calcium(2+)'
        self.assertHasNode(obj)

        expected_annotations = {
            'relation': 'increases',
            'object': {
                'modification': 'Translocation',
                'params': {
                    'fromLoc': dict(namespace='MESHCS', name='Cell Membrane'),
                    'toLoc': dict(namespace='MESHCS', name='Intracellular Space')
                }
            }
        }

        self.assertHasEdge(sub, obj, **expected_annotations)



    def test_increases(self):
        """Test increases with reaction"""
        statement = 'pep(p(SFAM:"CAPN Family")) -> reaction(reactants(p(HGNC:CDK5R1)),products(p(HGNC:CDK5)))'
        result = self.parser.parseString(statement).asList()
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

        self.assertHasEdge(obj, obj_member_1, relation='hasReactant')
        self.assertHasEdge(obj, obj_member_2, relation='hasProduct')

        expected_annotations = {
            'relation': 'increases',
            'subject': {
                'modification': 'Activity',
                'params': {
                    'molecularActivity': 'PeptidaseActivity'
                }
            }
        }

        self.assertHasEdge(sub, obj, **expected_annotations)

    def test_decreases(self):
        """Tests simple triple"""
        statement = 'proteinAbundance(HGNC:CAT) decreases abundance(CHEBI:"hydrogen peroxide")'
        result = self.parser.parseString(statement).asList()
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

        self.assertHasEdge(sub, obj, relation='decreases')

    def test_nested(self):
        """Test nested statement"""
        statement = 'p(HGNC:CAT) -| (a(CHEBI:"hydrogen peroxide") -> bp(GO:"apoptotic process"))'
        result = self.parser.parseString(statement)
        expected = [
            ['Protein', ['HGNC', 'CAT']],
            'decreases',
            [
                ['Abundance', ['CHEBI', 'hydrogen peroxide']],
                'increases',
                ['BiologicalProcess', ['GO', 'apoptotic process']]
            ]
        ]

        print(json.dumps(result.asDict(), indent=2))
        self.assertEqual(expected, result.asList())

    def test_biomarker(self):
        """Test annotation"""
        statement = 'act(p(HGNC:CHIT1)) biomarkerFor path(MESHD:"Alzheimer Disease")'
        result = self.parser.parseString(statement).asList()
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

        self.assertHasEdge(sub, obj, relation='biomarkerFor')

    def test_multipleAnnotations(self):
        """Test nested definitions"""
        statement = 'pep(complex(p(HGNC:F3),p(HGNC:F7))) directlyIncreases pep(p(HGNC:F9))'
        result = self.parser.parseString(statement).asList()
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

        self.assertHasEdge(sub, obj, relation='directlyIncreases')

    def test_increases_multipleAnnotations(self):
        """Test multiple nested annotations on object"""
        statement = 'complex(p(HGNC:ARRB2),p(HGNC:APH1A)) -> pep(complex(SCOMP:"gamma Secretase Complex"))'
        result = self.parser.parseString(statement).asList()
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

        self.assertHasEdge(sub, obj, relation='increases')

    def test_increases_subjectSubstitution(self):
        """Test SNP annotation"""
        statement = 'g(HGNC:APP,sub(G,275341,C)) -> path(MESHD:"Alzheimer Disease")'
        result = self.parser.parseString(statement).asList()
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

        self.assertHasEdge(sub, obj, relation='increases')

    def test_increases_withVariantObject(self):
        """Test phosphoralation tag"""
        statement = 'kin(p(SFAM:"GSK3 Family")) -> p(HGNC:MAPT,pmod(P))'
        result = self.parser.parseString(statement).asList()
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

        self.assertHasEdge(sub, obj, relation='increases')

    def test_increases_withSubstitutionSubject(self):
        """Test protein substitution"""
        statement = 'p(HGNC:APP,sub(N,10,Y)) -> path(MESHD:"Alzheimer Disease")'
        result = self.parser.parseString(statement).asList()
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

        self.assertHasEdge(sub, obj, relation='increases')

@unittest.skip
class TestRelationshipsNumbered(TestTokenParserBase):
    def test_315a(self):
        """"""
        statement = 'act(p(HGNC:HMGCR), ma(cat)) rateLimitingStepOf bp(GOBP:"cholesterol biosynthetic process")'
        result = self.parser.parseString(statement).asList()
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

        self.assertHasEdge(sub, obj, relation='rateLimitingStepOf')

    def test_317a(self):
        """Abundances and activities"""
        statement = 'p(PFH:"Hedgehog Family") =| act(p(HGNC:PTCH1))'
        result = self.parser.parseString(statement).asList()
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
        result = self.parser.parseString(statement).asList()
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
        result = self.parser.parseString(statement)
        expected_result = [
            ['Protein', ['HGNC', 'CLSPN']],
            'directlyIncreases',
            [
                ['Activity', ['Protein', ['HGNC', 'ATR']], ['MolecularActivity', 'KinaseActivity']],
                'directlyIncreases',
                ['ProteinVariant', ['HGNC', 'CHEK1'], ['ProteinModification', 'P']]]
        ]
        self.assertEqual(expected_result, result.asList())

    def test_317d(self):
        """Self-referential relationships"""
        statement = 'p(HGNC:GSK3B, pmod(P, S, 9)) =| act(p(HGNC:GSK3B), ma(kin))'
        result = self.parser.parseString(statement).asList()
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
        result = self.parser.parseString(statement).asList()
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
        result = self.parser.parseString(statement).asList()
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
        result = self.parser.parseString(statement).asList()
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
        result = self.parser.parseString(statement).asList()
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
        result = self.parser.parseString(statement).asList()
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
        result = self.parser.parseString(statement).asList()
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
