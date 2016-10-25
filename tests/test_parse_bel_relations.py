"""
This class requires the parser to be fully compiled, and takes a long time to run.
"""

import logging

from pybel.parser.parse_exceptions import NestedRelationNotSupportedException
from tests.constants import TestTokenParserBase

log = logging.getLogger(__name__)


class TestRelationshipsRandom(TestTokenParserBase):
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

        sub = self.parser.canonicalize_node(result['subject'])
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

        obj = self.parser.canonicalize_node(result['object'])
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
                    dict(reference='G', position=275341, variant='C')
                ]
            },
            'relation': 'causesNoChange',
            'object': {
                'function': 'Pathology',
                'identifier': dict(namespace='MESHD', name='Alzheimer Disease')
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = 'GeneVariant', 'HGNC', 'APP', ('Variant', 'G', 275341, 'C')
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

        sub = self.parser.canonicalize_node(result['subject'])
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

    def test_nested(self):
        """
        3.1 \
        Test nested statement"""
        statement = 'p(HGNC:CAT) -| (a(CHEBI:"hydrogen peroxide") -> bp(GO:"apoptotic process"))'
        with self.assertRaises(NestedRelationNotSupportedException):
            self.parser.relation.parseString(statement)

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
                    {'identifier': 'P'}
                ]

            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = 'Protein', 'SFAM', 'GSK3 Family'
        self.assertHasNode(sub)

        obj = 'ProteinVariant', 'HGNC', 'MAPT', ('ProteinModification', 'P')
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
                    dict(identifier='P', code='S', pos=9)
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

        subject_node = 'ProteinVariant', 'HGNC', 'GSK3B', ('ProteinModification', 'P', 'S', 9)
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

        sub = self.parser.canonicalize_node(result['subject'])
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
