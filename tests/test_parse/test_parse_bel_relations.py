# -*- coding: utf-8 -*-

import logging
import unittest

from pyparsing import ParseException

from pybel import BELGraph
from pybel.canonicalize import edge_to_bel
from pybel.constants import (
    ABUNDANCE, ACTIVITY, ANNOTATIONS, BEL_DEFAULT_NAMESPACE, BIOPROCESS, CITATION, COMPLEX, COMPOSITE, DECREASES,
    DIRECTLY_DECREASES, DIRECTLY_INCREASES, EFFECT, EQUIVALENT_TO, EVIDENCE, FROM_LOC, FUNCTION, GENE, GMOD,
    HAS_COMPONENT, HAS_MEMBER, HAS_PRODUCT, HAS_REACTANT, HAS_VARIANT, HGVS, IDENTIFIER, INCREASES, IS_A, KIND,
    LOCATION, MEMBERS, MODIFIER, NAME, NAMESPACE, NEGATIVE_CORRELATION, OBJECT, ORTHOLOGOUS, PART_OF, PATHOLOGY, PMOD,
    PRODUCTS, PROTEIN, REACTANTS, REACTION, REGULATES, RELATION, RNA, SUBJECT, SUBPROCESS_OF, TARGET, TO_LOC,
    TRANSCRIBED_TO, TRANSLATED_TO, TRANSLOCATION, VARIANTS,
)
from pybel.dsl import abundance, activity, entity, pmod, protein, rna
from pybel.parser import BelParser
from pybel.parser.exc import (
    MissingNamespaceNameWarning, NestedRelationWarning, RelabelWarning, UndefinedNamespaceWarning,
)
from pybel.tokens import node_to_tuple
from tests.constants import TestTokenParserBase, test_citation_dict, test_evidence_text

log = logging.getLogger(__name__)


class TestRelations(TestTokenParserBase):
    @classmethod
    def setUpClass(cls):
        super(TestRelations, cls).setUpClass()
        cls.parser.relation.streamline()

    def setUp(self):
        super(TestRelations, self).setUp()
        self.add_default_provenance()

    def test_ensure_no_dup_nodes(self):
        """Ensure node isn't added twice, even if from different statements"""
        self.parser.gene.addParseAction(self.parser.handle_term)
        result = self.parser.bel_term.parseString('g(HGNC:AKT1)')

        expected_result_dict = {
            FUNCTION: GENE,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1'
        }

        self.assertEqual(expected_result_dict, result.asDict())

        self.parser.degradation.addParseAction(self.parser.handle_term)
        self.parser.degradation.parseString('deg(g(HGNC:AKT1))')

        gene = GENE, 'HGNC', 'AKT1'

        self.assertEqual(1, self.parser.graph.number_of_nodes())
        self.assert_has_node(gene, **{FUNCTION: GENE, NAMESPACE: 'HGNC', NAME: 'AKT1'})

    def test_singleton(self):
        """Test singleton composite in subject."""
        statement = 'composite(p(HGNC:CASP8),p(HGNC:FADD),a(ADO:"Abeta_42"))'
        result = self.parser.statement.parseString(statement)

        expected = [
            COMPOSITE,
            [PROTEIN, 'HGNC', 'CASP8'],
            [PROTEIN, 'HGNC', 'FADD'],
            [ABUNDANCE, 'ADO', 'Abeta_42']
        ]
        self.assertEqual(expected, result.asList())

        sub = node_to_tuple(result)
        self.assert_has_node(sub)

        sub_member_1 = PROTEIN, 'HGNC', 'CASP8'
        self.assert_has_node(sub_member_1)

        sub_member_2 = PROTEIN, 'HGNC', 'FADD'
        self.assert_has_node(sub_member_2)

        self.assert_has_edge(sub, sub_member_1, relation=HAS_COMPONENT)
        self.assert_has_edge(sub, sub_member_2, relation=HAS_COMPONENT)

    def test_predicate_failure(self):
        """Checks that if there's a problem with the relation/object, that an error gets thrown"""
        statement = 'composite(p(HGNC:CASP8),p(HGNC:FADD),a(ADO:"Abeta_42")) -> nope(GOBP:"neuron apoptotic process")'

        with self.assertRaises(ParseException):
            self.parser.relation.parseString(statement)

    def test_increases(self):
        """Test composite in subject. See BEL 2.0 specification
        `3.1.1 <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xincreases>`_
        """
        statement = 'composite(p(HGNC:CASP8),p(HGNC:FADD),a(ADO:"Abeta_42")) -> bp(GOBP:"neuron apoptotic process")'
        result = self.parser.relation.parseString(statement)

        expected = [
            [COMPOSITE, [PROTEIN, 'HGNC', 'CASP8'], [PROTEIN, 'HGNC', 'FADD'],
             [ABUNDANCE, 'ADO', 'Abeta_42']],
            INCREASES,
            [BIOPROCESS, 'GOBP', 'neuron apoptotic process']
        ]
        self.assertEqual(expected, result.asList())

        sub = node_to_tuple(result[SUBJECT])
        self.assert_has_node(sub)

        sub_member_1 = PROTEIN, 'HGNC', 'CASP8'
        self.assert_has_node(sub_member_1)

        sub_member_2 = PROTEIN, 'HGNC', 'FADD'
        self.assert_has_node(sub_member_2)

        self.assert_has_edge(sub, sub_member_1, relation=HAS_COMPONENT)
        self.assert_has_edge(sub, sub_member_2, relation=HAS_COMPONENT)

        obj = BIOPROCESS, 'GOBP', 'neuron apoptotic process'
        self.assert_has_node(obj)

        self.assert_has_edge(sub, obj, relation=INCREASES)

    def test_directlyIncreases_withTlocObject(self):
        """Test translocation in object. See BEL 2.0 specification
        `3.1.2 <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XdIncreases>`_
        """
        statement = 'a(ADO:"Abeta_42") => tloc(a(CHEBI:"calcium(2+)"),fromLoc(MESHCS:"Cell Membrane"),' \
                    'toLoc(MESHCS:"Intracellular Space"))'
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
                EFFECT: {
                    FROM_LOC: {NAMESPACE: 'MESHCS', NAME: 'Cell Membrane'},
                    TO_LOC: {NAMESPACE: 'MESHCS', NAME: 'Intracellular Space'}
                }
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = ABUNDANCE, 'ADO', 'Abeta_42'
        self.assert_has_node(sub)

        obj = ABUNDANCE, 'CHEBI', 'calcium(2+)'
        self.assert_has_node(obj)

        expected_annotations = {
            RELATION: DIRECTLY_INCREASES,
            OBJECT: {
                MODIFIER: TRANSLOCATION,
                EFFECT: {
                    FROM_LOC: {NAMESPACE: 'MESHCS', NAME: 'Cell Membrane'},
                    TO_LOC: {NAMESPACE: 'MESHCS', NAME: 'Intracellular Space'}
                }
            }
        }

        self.assert_has_edge(sub, obj, **expected_annotations)

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
                    NAMESPACE: 'SFAM',
                    NAME: 'CAPN Family',
                    LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}
                },
                EFFECT: {
                    NAME: 'pep',
                    NAMESPACE: BEL_DEFAULT_NAMESPACE
                },
            },
            RELATION: 'decreases',
            OBJECT: {
                FUNCTION: REACTION,
                REACTANTS: [
                    {FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'CDK5R1'}
                ],
                PRODUCTS: [
                    {FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'CDK5'}
                ]

            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = PROTEIN, 'SFAM', 'CAPN Family'
        self.assert_has_node(sub)

        obj = node_to_tuple(result[OBJECT])
        self.assert_has_node(obj)

        obj_member_1 = PROTEIN, 'HGNC', 'CDK5R1'
        self.assert_has_node(obj_member_1)

        obj_member_2 = PROTEIN, 'HGNC', 'CDK5'
        self.assert_has_node(obj_member_2)

        self.assert_has_edge(obj, obj_member_1, relation=HAS_REACTANT)
        self.assert_has_edge(obj, obj_member_2, relation=HAS_PRODUCT)

        expected_edge_attributes = {
            RELATION: DECREASES,
            SUBJECT: {
                MODIFIER: ACTIVITY,
                EFFECT: {
                    NAME: 'pep',
                    NAMESPACE: BEL_DEFAULT_NAMESPACE
                },
                LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}
            }
        }

        self.assertEqual(expected_edge_attributes[SUBJECT],
                         activity(name='pep', location=entity(name='intracellular', namespace='GOCC')))

        self.assert_has_edge(sub, obj, **expected_edge_attributes)

    def test_directlyDecreases(self):
        """
        3.1.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XdDecreases
        Tests simple triple"""
        statement = 'proteinAbundance(HGNC:CAT, location(GOCC:intracellular)) directlyDecreases abundance(CHEBI:"hydrogen peroxide")'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            SUBJECT: {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'CAT',
                LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}
            },
            RELATION: 'directlyDecreases',
            OBJECT: {
                FUNCTION: ABUNDANCE,
                NAMESPACE: 'CHEBI',
                NAME: 'hydrogen peroxide'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = PROTEIN, 'HGNC', 'CAT'
        self.assert_has_node(sub)

        obj = ABUNDANCE, 'CHEBI', 'hydrogen peroxide'
        self.assert_has_node(obj)

        expected_attrs = {
            SUBJECT: {
                LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}
            },
            RELATION: 'directlyDecreases',
        }
        self.assert_has_edge(sub, obj, **expected_attrs)

    def test_directlyDecreases_annotationExpansion(self):
        """
        3.1.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XdDecreases
        Tests simple triple"""
        statement = 'g(HGNC:CAT, location(GOCC:intracellular)) directlyDecreases abundance(CHEBI:"hydrogen peroxide")'

        annotations = {
            'ListAnnotation': {'a', 'b'},
            'ScalarAnnotation': {'c'}
        }

        self.parser.control_parser.annotations.update(annotations)

        result = self.parser.relation.parseString(statement)

        expected_dict = {
            SUBJECT: {
                FUNCTION: GENE,
                NAMESPACE: 'HGNC',
                NAME: 'CAT',
                LOCATION: {
                    NAMESPACE: 'GOCC',
                    NAME: 'intracellular'
                }
            },
            RELATION: DIRECTLY_DECREASES,
            OBJECT: {
                FUNCTION: ABUNDANCE,
                NAMESPACE: 'CHEBI',
                NAME: 'hydrogen peroxide'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = GENE, 'HGNC', 'CAT'
        self.assert_has_node(sub)

        obj = ABUNDANCE, 'CHEBI', 'hydrogen peroxide'
        self.assert_has_node(obj)

        expected_attrs = {
            SUBJECT: {
                LOCATION: {
                    NAMESPACE: 'GOCC',
                    NAME: 'intracellular'
                }
            },
            RELATION: DIRECTLY_DECREASES,
            CITATION: test_citation_dict,
            EVIDENCE: test_evidence_text,
            ANNOTATIONS: {
                'ListAnnotation': {'a': True, 'b': True},
                'ScalarAnnotation': {'c': True}
            }
        }
        self.assert_has_edge(sub, obj, **expected_attrs)

    def test_rateLimitingStepOf_subjectActivity(self):
        """3.1.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_ratelimitingstepof"""
        statement = 'act(p(HGNC:HMGCR), ma(cat)) rateLimitingStepOf bp(GOBP:"cholesterol biosynthetic process")'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            SUBJECT: {
                MODIFIER: ACTIVITY,
                TARGET: {
                    FUNCTION: PROTEIN,
                    NAMESPACE: 'HGNC',
                    NAME: 'HMGCR'
                },
                EFFECT: {
                    NAME: 'cat',
                    NAMESPACE: BEL_DEFAULT_NAMESPACE
                },
            },
            RELATION: 'rateLimitingStepOf',
            OBJECT: {
                FUNCTION: BIOPROCESS,
                NAMESPACE: 'GOBP',
                NAME: 'cholesterol biosynthetic process'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = PROTEIN, 'HGNC', 'HMGCR'
        self.assert_has_node(sub)

        obj = BIOPROCESS, 'GOBP', 'cholesterol biosynthetic process'
        self.assert_has_node(obj)

        self.assert_has_edge(sub, obj, relation=expected_dict[RELATION])

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
                NAMESPACE: 'HGNC',
                NAME: 'APP',
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
                NAMESPACE: 'MESHD',
                NAME: 'Alzheimer Disease'
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = GENE, 'HGNC', 'APP', (HGVS, 'c.275341G>C')
        self.assert_has_node(sub)

        obj = PATHOLOGY, 'MESHD', 'Alzheimer Disease'
        self.assert_has_node(obj)

        self.assert_has_edge(sub, obj, relation=expected_dict[RELATION])

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
                    MEMBERS: [
                        {FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'F3'},
                        {FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'F7'}
                    ]
                }
            },
            RELATION: REGULATES,
            OBJECT: {
                MODIFIER: ACTIVITY,
                EFFECT: {
                    NAME: 'pep',
                    NAMESPACE: BEL_DEFAULT_NAMESPACE
                },
                TARGET: {
                    FUNCTION: PROTEIN,
                    NAMESPACE: 'HGNC',
                    NAME: 'F9'
                }

            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = node_to_tuple(result[SUBJECT])
        self.assert_has_node(sub)

        sub_member_1 = PROTEIN, 'HGNC', 'F3'
        self.assert_has_node(sub_member_1)

        sub_member_2 = PROTEIN, 'HGNC', 'F7'
        self.assert_has_node(sub_member_2)

        self.assert_has_edge(sub, sub_member_1)
        self.assert_has_edge(sub, sub_member_2)

        obj = PROTEIN, 'HGNC', 'F9'
        self.assert_has_node(obj)

        self.assert_has_edge(sub, obj, relation=expected_dict[RELATION])

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

        self.assert_has_edge((PROTEIN, 'HGNC', 'CAT'), (ABUNDANCE, 'CHEBI', "hydrogen peroxide"))
        self.assert_has_edge((ABUNDANCE, 'CHEBI', "hydrogen peroxide"),
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
                    NAMESPACE: 'SFAM',
                    NAME: 'GSK3 Family'
                }
            },
            RELATION: NEGATIVE_CORRELATION,
            OBJECT: {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'MAPT',
                VARIANTS: [pmod('Ph')]
            }
        }
        self.assertEqual(expected_dict, result.asDict())

        sub = PROTEIN, 'SFAM', 'GSK3 Family'
        self.assert_has_node(sub)

        obj = PROTEIN, 'HGNC', 'MAPT', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'))
        self.assert_has_node(obj)

        self.assert_has_edge(sub, obj, relation=expected_dict[RELATION])
        self.assert_has_edge(obj, sub, relation=expected_dict[RELATION])

    def test_positiveCorrelation_withSelfReferential(self):
        """
        3.2.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XposCor
        Self-referential relationships"""
        statement = 'p(HGNC:GSK3B, pmod(P, S, 9)) pos act(p(HGNC:GSK3B), ma(kin))'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            SUBJECT: {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'GSK3B',
                VARIANTS: [pmod('Ph', position=9, code='Ser')]
            },
            RELATION: 'positiveCorrelation',
            OBJECT: {
                MODIFIER: ACTIVITY,
                TARGET: {
                    FUNCTION: PROTEIN,
                    NAMESPACE: 'HGNC',
                    NAME: 'GSK3B'
                },
                EFFECT: {
                    NAME: 'kin',
                    NAMESPACE: BEL_DEFAULT_NAMESPACE
                }
            },
        }
        self.assertEqual(expected_dict, result.asDict())

        subject_node = PROTEIN, 'HGNC', 'GSK3B', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 9)
        self.assert_has_node(subject_node)

        object_node = PROTEIN, 'HGNC', 'GSK3B'
        self.assert_has_node(object_node)

        self.assert_has_edge(subject_node, object_node, relation=expected_dict[RELATION])
        self.assert_has_edge(object_node, subject_node, relation=expected_dict[RELATION])

    def test_orthologous(self):
        """
        3.3.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_orthologous
        """
        statement = 'g(HGNC:AKT1) orthologous g(MGI:AKT1)'
        result = self.parser.relation.parseString(statement)
        expected_result = [[GENE, 'HGNC', 'AKT1'], ORTHOLOGOUS, [GENE, 'MGI', 'AKT1']]
        self.assertEqual(expected_result, result.asList())

        sub = GENE, 'HGNC', 'AKT1'
        self.assert_has_node(sub)

        obj = GENE, 'MGI', 'AKT1'
        self.assert_has_node(obj)

        self.assert_has_edge(sub, obj, relation=ORTHOLOGOUS)
        self.assert_has_edge(obj, sub, relation=ORTHOLOGOUS)

    def test_transcription(self):
        """
        3.3.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_transcribedto
        """
        statement = 'g(HGNC:AKT1) :> r(HGNC:AKT1)'
        result = self.parser.relation.parseString(statement)

        expected_result = [[GENE, 'HGNC', 'AKT1'], TRANSCRIBED_TO, [RNA, 'HGNC', 'AKT1']]
        self.assertEqual(expected_result, result.asList())

        sub = GENE, 'HGNC', 'AKT1'
        self.assert_has_node(sub)

        obj = RNA, 'HGNC', 'AKT1'
        self.assert_has_node(obj)

        self.assert_has_edge(sub, obj, **{RELATION: TRANSCRIBED_TO})

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
                NAMESPACE: 'HGNC',
                NAME: 'AKT1',
                LOCATION: {
                    NAMESPACE: 'GOCC',
                    NAME: 'intracellular'
                }
            },
            RELATION: TRANSLATED_TO,
            OBJECT: {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'AKT1',
            }
        }
        self.assertEqual(expected_result, result.asDict())

        self.assertEqual(2, self.graph.number_of_nodes())

        source = RNA, 'HGNC', 'AKT1'
        source_dict = rna(name='AKT1', namespace='HGNC')
        self.assertIn(source, self.graph)
        self.assertEqual(source_dict, self.graph.node[source])
        self.assertTrue(self.graph.has_node_with_data(source_dict))

        target = PROTEIN, 'HGNC', 'AKT1'
        target_dict = protein(name='AKT1', namespace='HGNC')
        self.assertIn(target, self.graph)
        self.assertEqual(target_dict, self.graph.node[target])
        self.assertTrue(self.graph.has_node_with_data(target_dict))

        self.assertEqual(1, self.graph.number_of_edges())
        self.assertTrue(self.graph.has_edge(source, target))

        key_data = self.parser.graph.edge[source][target]
        self.assertEqual(1, len(key_data))

        key = list(key_data)[0]
        data = key_data[key]

        self.assertIn(RELATION, data)
        self.assertEqual(TRANSLATED_TO, data[RELATION])

        calculated_source_data = self.graph.node[source]
        self.assertTrue(calculated_source_data)

        calculated_target_data = self.graph.node[target]
        self.assertTrue(calculated_target_data)

        calculated_edge_bel = edge_to_bel(calculated_source_data, calculated_target_data, data=data)
        self.assertEqual('r(HGNC:AKT1, loc(GOCC:intracellular)) translatedTo p(HGNC:AKT1)', calculated_edge_bel)

    def test_component_list(self):
        s = 'complex(SCOMP:"C1 Complex") hasComponents list(p(HGNC:C1QB), p(HGNC:C1S))'
        result = self.parser.relation.parseString(s)

        expected_result_list = [
            [COMPLEX, 'SCOMP', 'C1 Complex'],
            'hasComponents',
            [
                [PROTEIN, 'HGNC', 'C1QB'],
                [PROTEIN, 'HGNC', 'C1S']
            ]
        ]
        self.assertEqual(expected_result_list, result.asList())

        sub = COMPLEX, 'SCOMP', 'C1 Complex'
        self.assert_has_node(sub)
        child_1 = PROTEIN, 'HGNC', 'C1QB'
        self.assert_has_node(child_1)
        self.assert_has_edge(sub, child_1, **{RELATION: HAS_COMPONENT})
        child_2 = PROTEIN, 'HGNC', 'C1S'
        self.assert_has_node(child_2)
        self.assert_has_edge(sub, child_2, **{RELATION: HAS_COMPONENT})

    def test_member_list(self):
        """
        3.4.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_hasmembers
        """
        statement = 'p(PKC:a) hasMembers list(p(HGNC:PRKCA), p(HGNC:PRKCB), p(HGNC:PRKCD), p(HGNC:PRKCE))'
        result = self.parser.relation.parseString(statement)
        expected_result = [
            [PROTEIN, 'PKC', 'a'],
            'hasMembers',
            [
                [PROTEIN, 'HGNC', 'PRKCA'],
                [PROTEIN, 'HGNC', 'PRKCB'],
                [PROTEIN, 'HGNC', 'PRKCD'],
                [PROTEIN, 'HGNC', 'PRKCE']
            ]
        ]
        self.assertEqual(expected_result, result.asList())

        sub = PROTEIN, 'PKC', 'a'
        obj1 = PROTEIN, 'HGNC', 'PRKCA'
        obj2 = PROTEIN, 'HGNC', 'PRKCB'
        obj3 = PROTEIN, 'HGNC', 'PRKCD'
        obj4 = PROTEIN, 'HGNC', 'PRKCE'

        self.assert_has_node(sub)

        self.assert_has_node(obj1)
        self.assert_has_edge(sub, obj1, relation=HAS_MEMBER)

        self.assert_has_node(obj2)
        self.assert_has_edge(sub, obj2, relation=HAS_MEMBER)

        self.assert_has_node(obj3)
        self.assert_has_edge(sub, obj3, relation=HAS_MEMBER)

        self.assert_has_node(obj4)
        self.assert_has_edge(sub, obj4, relation=HAS_MEMBER)

    def test_isA(self):
        """
        3.4.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_isa
        """
        statement = 'pathology(MESH:Psoriasis) isA pathology(MESH:"Skin Diseases")'
        result = self.parser.relation.parseString(statement)

        expected_result = [[PATHOLOGY, 'MESH', 'Psoriasis'], 'isA', [PATHOLOGY, 'MESH', 'Skin Diseases']]
        self.assertEqual(expected_result, result.asList())

        sub = PATHOLOGY, 'MESH', 'Psoriasis'
        self.assert_has_node(sub)

        obj = PATHOLOGY, 'MESH', 'Skin Diseases'
        self.assert_has_node(obj)

        self.assert_has_edge(sub, obj, relation=IS_A)

    def test_label_1(self):
        statement = 'g(HGNC:APOE, var(c.526C>T), var(c.388T>C)) labeled "APOE E2"'
        result = self.parser.relation.parseString(statement)

        expected_dict = {
            SUBJECT: {
                FUNCTION: GENE,
                NAMESPACE: 'HGNC',
                NAME: 'APOE',
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

        expected_node = node_to_tuple(result[SUBJECT])

        self.assert_has_node(expected_node)
        self.assertTrue(self.parser.graph.has_node_description(expected_node))
        self.assertEqual('APOE E2', self.parser.graph.get_node_description(expected_node))

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
                NAMESPACE: 'dbSNP',
                NAME: 'rs123456',
            },
            RELATION: EQUIVALENT_TO,
            OBJECT: {
                FUNCTION: GENE,
                NAMESPACE: 'HGNC',
                NAME: 'YFG',
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
        self.assert_has_node(sub)

        obj = GENE, 'HGNC', 'YFG', (HGVS, 'c.123G>A')
        self.assert_has_node(obj)

        self.assert_has_edge(sub, obj, **{RELATION: EQUIVALENT_TO})
        self.assert_has_edge(obj, sub, **{RELATION: EQUIVALENT_TO})

    def test_partOf(self):
        statement = 'a(UBERON:"corpus striatum") partOf a(UBERON:"basal ganglion")'
        self.parser.relation.parseString(statement)

        corpus_striatum = abundance(namespace='UBERON', name='corpus striatum')
        basal_ganglion = abundance(namespace='UBERON', name='basal ganglion')

        self.assertTrue(self.parser.graph.has_node_with_data(corpus_striatum))
        self.assertTrue(self.parser.graph.has_node_with_data(basal_ganglion))

        cs_node = node_to_tuple(corpus_striatum)
        bg_node = node_to_tuple(basal_ganglion)

        self.assertIn(bg_node, self.parser.graph.edge[cs_node])

        v = list(self.parser.graph.edge[cs_node][bg_node].values())
        self.assertEqual(1, len(v))

        v = v[0]
        self.assertIn(RELATION, v)
        self.assertEqual(PART_OF, v[RELATION])

    def test_subProcessOf(self):
        """
        3.4.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_subprocessof
        """
        statement = 'rxn(reactants(a(CHEBI:"(S)-3-hydroxy-3-methylglutaryl-CoA"),a(CHEBI:NADPH), \
            a(CHEBI:hydron)),products(a(CHEBI:mevalonate), a(CHEBI:"CoA-SH"), a(CHEBI:"NADP(+)"))) \
            subProcessOf bp(GOBP:"cholesterol biosynthetic process")'
        result = self.parser.relation.parseString(statement)
        expected_result = [
            [
                REACTION,
                [
                    [ABUNDANCE, 'CHEBI', '(S)-3-hydroxy-3-methylglutaryl-CoA'],
                    [ABUNDANCE, 'CHEBI', 'NADPH'],
                    [ABUNDANCE, 'CHEBI', 'hydron'],
                ],
                [
                    [ABUNDANCE, 'CHEBI', 'mevalonate'],
                    [ABUNDANCE, 'CHEBI', 'CoA-SH'],
                    [ABUNDANCE, 'CHEBI', 'NADP(+)']
                ]
            ],
            SUBPROCESS_OF,
            [BIOPROCESS, 'GOBP', 'cholesterol biosynthetic process']]
        self.assertEqual(expected_result, result.asList())

        sub = node_to_tuple(result[SUBJECT])
        self.assert_has_node(sub)

        sub_reactant_1 = ABUNDANCE, 'CHEBI', '(S)-3-hydroxy-3-methylglutaryl-CoA'
        sub_reactant_2 = ABUNDANCE, 'CHEBI', 'NADPH'
        sub_reactant_3 = ABUNDANCE, 'CHEBI', 'hydron'
        sub_product_1 = ABUNDANCE, 'CHEBI', 'mevalonate'
        sub_product_2 = ABUNDANCE, 'CHEBI', 'CoA-SH'
        sub_product_3 = ABUNDANCE, 'CHEBI', 'NADP(+)'

        self.assert_has_node(sub_reactant_1)
        self.assert_has_node(sub_reactant_2)
        self.assert_has_node(sub_reactant_3)
        self.assert_has_node(sub_product_1)
        self.assert_has_node(sub_product_2)
        self.assert_has_node(sub_product_3)

        self.assert_has_edge(sub, sub_reactant_1, relation=HAS_REACTANT)
        self.assert_has_edge(sub, sub_reactant_2, relation=HAS_REACTANT)
        self.assert_has_edge(sub, sub_reactant_3, relation=HAS_REACTANT)
        self.assert_has_edge(sub, sub_product_1, relation=HAS_PRODUCT)
        self.assert_has_edge(sub, sub_product_2, relation=HAS_PRODUCT)
        self.assert_has_edge(sub, sub_product_3, relation=HAS_PRODUCT)

        obj = cls, ns, val = BIOPROCESS, 'GOBP', 'cholesterol biosynthetic process'
        self.assert_has_node(obj, **{FUNCTION: cls, NAMESPACE: ns, NAME: val})

        self.assert_has_edge(sub, obj, **{RELATION: 'subProcessOf'})

    def test_extra_1(self):
        statement = 'abundance(CHEBI:"nitric oxide") increases cellSurfaceExpression(complexAbundance(proteinAbundance(HGNC:ITGAV),proteinAbundance(HGNC:ITGB3)))'
        self.parser.relation.parseString(statement)

    def test_has_variant(self):
        statement = 'g(HGNC:AKT1) hasVariant g(HGNC:AKT1, gmod(M))'
        self.parser.relation.parseString(statement)

        expected_parent = GENE, 'HGNC', 'AKT1'
        expected_child = GENE, 'HGNC', 'AKT1', (GMOD, (BEL_DEFAULT_NAMESPACE, 'Me'))

        self.assert_has_node(expected_parent, **{FUNCTION: GENE, NAMESPACE: 'HGNC', NAME: 'AKT1'})
        self.assert_has_node(expected_child)

        self.assertEqual('g(HGNC:AKT1)', self.graph.node_to_bel(expected_parent))
        self.assertEqual('g(HGNC:AKT1, gmod(Me))', self.graph.node_to_bel(expected_child))

        self.assert_has_edge(expected_parent, expected_child, **{RELATION: HAS_VARIANT})

    def test_has_reaction_component(self):
        statement = 'rxn(reactants(a(CHEBI:"(S)-3-hydroxy-3-methylglutaryl-CoA"),a(CHEBI:NADPH), \
                    a(CHEBI:hydron)),products(a(CHEBI:mevalonate), a(CHEBI:"CoA-SH"), a(CHEBI:"NADP(+)"))) \
                    hasReactant a(CHEBI:"(S)-3-hydroxy-3-methylglutaryl-CoA")'
        result = self.parser.relation.parseString(statement)

        sub = node_to_tuple(result[SUBJECT])
        self.assert_has_node(sub)

        sub_reactant_1 = ABUNDANCE, 'CHEBI', '(S)-3-hydroxy-3-methylglutaryl-CoA'
        sub_reactant_2 = ABUNDANCE, 'CHEBI', 'NADPH'
        sub_reactant_3 = ABUNDANCE, 'CHEBI', 'hydron'
        sub_product_1 = ABUNDANCE, 'CHEBI', 'mevalonate'
        sub_product_2 = ABUNDANCE, 'CHEBI', 'CoA-SH'
        sub_product_3 = ABUNDANCE, 'CHEBI', 'NADP(+)'

        self.assert_has_node(sub_reactant_1)
        self.assert_has_node(sub_reactant_2)
        self.assert_has_node(sub_reactant_3)
        self.assert_has_node(sub_product_1)
        self.assert_has_node(sub_product_2)
        self.assert_has_node(sub_product_3)

        self.assert_has_edge(sub, sub_reactant_1, relation=HAS_REACTANT)
        self.assert_has_edge(sub, sub_reactant_2, relation=HAS_REACTANT)
        self.assert_has_edge(sub, sub_reactant_3, relation=HAS_REACTANT)
        self.assert_has_edge(sub, sub_product_1, relation=HAS_PRODUCT)
        self.assert_has_edge(sub, sub_product_2, relation=HAS_PRODUCT)
        self.assert_has_edge(sub, sub_product_3, relation=HAS_PRODUCT)


class TestCustom(unittest.TestCase):
    def setUp(self):
        graph = BELGraph()

        namespace_dict = {
            'HGNC': {
                'AKT1': 'GRP',
                'YFG': 'GRP'
            },
            'MESHCS': {
                'nucleus': 'A'
            }
        }

        self.parser = BelParser(graph, namespace_dict=namespace_dict, autostreamline=False)

    def test_tloc_undefined_namespace(self):
        s = 'tloc(p(HGNC:AKT1), fromLoc(MESHCS:nucleus), toLoc(MISSING:"undefined"))'

        with self.assertRaises(UndefinedNamespaceWarning):
            self.parser.translocation.parseString(s)

    def test_tloc_undefined_name(self):
        s = 'tloc(p(HGNC:AKT1), fromLoc(MESHCS:nucleus), toLoc(MESHCS:"undefined"))'

        with self.assertRaises(MissingNamespaceNameWarning):
            self.parser.translocation.parseString(s)

    def test_location_undefined_namespace(self):
        s = 'p(HGNC:AKT1, loc(MISSING:"nucleus")'

        with self.assertRaises(UndefinedNamespaceWarning):
            self.parser.protein.parseString(s)

    def test_location_undefined_name(self):
        s = 'p(HGNC:AKT1, loc(MESHCS:"undefined")'

        with self.assertRaises(MissingNamespaceNameWarning):
            self.parser.protein.parseString(s)


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
            bel = self.graph.node_to_bel(node_to_tuple(result))
            self.assertEqual(expected_bel, bel)
