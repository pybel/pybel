# -*- coding: utf-8 -*-

import logging

from pybel.canonicalize import decanonicalize_node, decanonicalize_edge
from pybel.constants import *
from pybel.parser.parse_bel import canonicalize_node
from pybel.parser.parse_exceptions import NestedRelationWarning, RelabelWarning
from tests.constants import TestTokenParserBase
from tests.constants import default_identifier, test_citation_dict, test_evidence_text, update_provenance

log = logging.getLogger(__name__)


class TestRelations(TestTokenParserBase):
    @classmethod
    def setUpClass(cls):
        super(TestRelations, cls).setUpClass()
        cls.parser.relation.streamline()

    def setUp(self):
        super(TestRelations, self).setUp()
        update_provenance(self.parser)

    def test_ensure_no_dup_nodes(self):
        """Ensure node isn't added twice, even if from different statements"""
        self.parser.gene.addParseAction(self.parser.handle_term)
        result = self.parser.bel_term.parseString('g(HGNC:AKT1)')

        expected_result_dict = {
            FUNCTION: GENE,
            IDENTIFIER: {
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            }
        }

        self.assertEqual(expected_result_dict, result.asDict())

        self.parser.degradation.addParseAction(self.parser.handle_term)
        self.parser.degradation.parseString('deg(g(HGNC:AKT1))')

        gene = GENE, 'HGNC', 'AKT1'

        self.assertEqual(1, self.parser.graph.number_of_nodes())
        self.assertHasNode(gene, **{FUNCTION: GENE, NAMESPACE: 'HGNC', NAME: 'AKT1'})

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
                        PMOD_CODE: 'Ser',
                        PMOD_POSITION: 9
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

        self.assertEqual(2, self.parser.graph.number_of_nodes())

        sub = RNA, 'HGNC', 'AKT1'
        self.assertHasNode(sub)

        obj = PROTEIN, 'HGNC', 'AKT1'
        self.assertHasNode(obj)

        self.assertEqual(1, self.parser.graph.number_of_edges())

        self.assertHasEdge(sub, obj, **{RELATION: TRANSLATED_TO})

        self.assertEqual('r(HGNC:AKT1, loc(GOCC:intracellular)) translatedTo p(HGNC:AKT1)',
                         decanonicalize_edge(self.parser.graph, sub, obj, 0))

    def test_component_list(self):
        s = 'complex(SCOMP:"C1 Complex") hasComponents list(p(HGNC:C1QB), p(HGNC:C1S))'
        result = self.parser.relation.parseString(s)

        expected_result_list = [
            [COMPLEX, ['SCOMP', 'C1 Complex']],
            'hasComponents',
            [
                [PROTEIN, ['HGNC', 'C1QB']],
                [PROTEIN, ['HGNC', 'C1S']]
            ]
        ]
        self.assertEqual(expected_result_list, result.asList())

        sub = COMPLEX, 'SCOMP', 'C1 Complex'
        self.assertHasNode(sub)
        child_1 = PROTEIN, 'HGNC', 'C1QB'
        self.assertHasNode(child_1)
        self.assertHasEdge(sub, child_1, **{RELATION: HAS_COMPONENT})
        child_2 = PROTEIN, 'HGNC', 'C1S'
        self.assertHasNode(child_2)
        self.assertHasEdge(sub, child_2, **{RELATION: HAS_COMPONENT})

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

    def test_label_1(self):
        statement = 'g(HGNC:APOE, var(c.526C>T), var(c.388T>C)) labeled "APOE E2"'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            SUBJECT: {
                FUNCTION: GENE,
                IDENTIFIER: {
                    NAMESPACE: 'HGNC',
                    NAME: 'APOE'
                },
                VARIANTS: [
                    {
                        KIND: HGVS,
                        IDENTIFIER: 'c.526C>T'
                    }, {
                        KIND: HGVS,
                        IDENTIFIER: 'c.388T>C'
                    }
                ]
            },
            OBJECT: 'APOE E2'
        }
        self.assertEqual(expected_dict, result.asDict())

        expected_node = canonicalize_node(result[SUBJECT])

        self.assertHasNode(expected_node)
        self.assertIn(LABEL, self.parser.graph.node[expected_node])
        self.assertEqual('APOE E2', self.parser.graph.node[expected_node][LABEL])

    def test_raise_on_relabel(self):
        s1 = 'g(HGNC:APOE, var(c.526C>T), var(c.388T>C)) labeled "APOE E2"'
        s2 = 'g(HGNC:APOE, var(c.526C>T), var(c.388T>C)) labeled "APOE E2 Variant"'
        self.parser.relation.parseString(s1)
        with self.assertRaises(RelabelWarning):
            self.parser.relation.parseString(s2)

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

        self.assertHasEdge(sub, obj, **{RELATION: 'subProcessOf'})

    def test_extra_1(self):
        statement = 'abundance(CHEBI:"nitric oxide") increases cellSurfaceExpression(complexAbundance(proteinAbundance(HGNC:ITGAV),proteinAbundance(HGNC:ITGB3)))'
        self.parser.relation.parseString(statement)

    def test_has_variant(self):
        statement = 'g(HGNC:AKT1) hasVariant g(HGNC:AKT1, gmod(M))'
        self.parser.relation.parseString(statement)

        expected_parent = GENE, 'HGNC', 'AKT1'
        expected_child = GENE, 'HGNC', 'AKT1', (GMOD, (BEL_DEFAULT_NAMESPACE, 'Me'))

        self.assertHasNode(expected_parent, **{FUNCTION: GENE, NAMESPACE: 'HGNC', NAME: 'AKT1'})
        self.assertHasNode(expected_child)

        self.assertEqual('g(HGNC:AKT1)', decanonicalize_node(self.parser.graph, expected_parent))
        self.assertEqual('g(HGNC:AKT1, gmod(Me))', decanonicalize_node(self.parser.graph, expected_child))

        self.assertHasEdge(expected_parent, expected_child, **{RELATION: HAS_VARIANT})

    def test_has_reaction_component(self):
        statement = 'rxn(reactants(a(CHEBI:"(S)-3-hydroxy-3-methylglutaryl-CoA"),a(CHEBI:NADPH), \
                    a(CHEBI:hydron)),products(a(CHEBI:mevalonate), a(CHEBI:"CoA-SH"), a(CHEBI:"NADP(+)"))) \
                    hasReactant a(CHEBI:"(S)-3-hydroxy-3-methylglutaryl-CoA")'
        result = self.parser.relation.parseString(statement)

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

        self.parser.bel_term.addParseAction(self.parser.handle_term)

        for case in cases:
            source_bel, expected_bel = case if 2 == len(case) else (case, case)

            result = self.parser.bel_term.parseString(source_bel)
            bel = decanonicalize_node(self.parser.graph, canonicalize_node(result))
            self.assertEqual(expected_bel, bel)
