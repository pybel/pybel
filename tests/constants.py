# -*- coding: utf-8 -*-

"""Constants for PyBEL tests."""

import logging
import unittest
from json import dumps

from pybel import BELGraph
from pybel.constants import (
    ANNOTATIONS, ASSOCIATION, CITATION, CITATION_NAME, CITATION_REFERENCE, CITATION_TYPE, DECREASES, DIRECTLY_DECREASES,
    EVIDENCE, INCREASES, METADATA_AUTHORS, METADATA_DESCRIPTION, METADATA_LICENSES, METADATA_NAME, METADATA_VERSION,
    OPENBEL_ANNOTATION_RESOURCES, RELATION, hbp_namespace,
)
from pybel.dsl import BaseEntity, complex_abundance, pathology, protein
from pybel.dsl.namespaces import hgnc
from pybel.parser.exc import (
    BELParserWarning, BELSyntaxError, IllegalAnnotationValueWarning, InvalidCitationLengthException,
    InvalidCitationType, InvalidFunctionSemantic, InvalidPubMedIdentifierWarning, MalformedTranslocationWarning,
    MissingAnnotationKeyWarning, MissingAnnotationRegexWarning, MissingCitationException, MissingMetadataException,
    MissingNamespaceNameWarning, MissingNamespaceRegexWarning, MissingSupportWarning, NakedNameWarning,
    NestedRelationWarning, PlaceholderAminoAcidWarning, UndefinedAnnotationWarning, UndefinedNamespaceWarning,
    VersionFormatWarning,
)
from pybel.parser.parse_bel import BELParser
from pybel.parser.parse_control import ControlParser
from pybel.testing.constants import test_bel_thorough
from pybel.utils import subdict_matches
from tests.constant_helper import (
    BEL_THOROUGH_EDGES, BEL_THOROUGH_NODES, citation_1, evidence_1, expected_test_simple_metadata,
    expected_test_thorough_metadata,
)

log = logging.getLogger(__name__)

test_citation_dict = {
    CITATION_TYPE: 'PubMed',
    CITATION_NAME: 'TestName',
    CITATION_REFERENCE: '1235813'
}
SET_CITATION_TEST = 'SET Citation = {{"{type}","{name}","{reference}"}}'.format(**test_citation_dict)
test_evidence_text = 'I read it on Twitter'
test_set_evidence = 'SET Evidence = "{}"'.format(test_evidence_text)

HGNC_KEYWORD = 'HGNC'
HGNC_URL = hbp_namespace('hgnc')
MESH_DISEASES_KEYWORD = 'MeSHDisease'
MESH_DISEASES_URL = OPENBEL_ANNOTATION_RESOURCES + "mesh-diseases.belanno"

akt1 = hgnc(name='AKT1')
egfr = hgnc(name='EGFR')
fadd = hgnc(name='FADD')
casp8 = hgnc(name='CASP8')


def update_provenance(control_parser: ControlParser) -> None:
    """Put a default evidence and citation in a BEL parser."""
    control_parser.citation.update(test_citation_dict)
    control_parser.evidence = test_evidence_text


def assert_has_node(self: unittest.TestCase, node: BaseEntity, graph: BELGraph, **kwargs):
    """Check if a node with the given properties is contained within a graph."""
    self.assertIsInstance(node, BaseEntity)

    self.assertIn(
        node,
        graph,
        msg='{} not found in graph. Other nodes:\n{}'.format(node.as_bel(), '\n'.join(
            n.as_bel()
            for n in graph
        )),
    )

    if kwargs:
        missing = set(kwargs) - set(graph.nodes[node])
        self.assertFalse(missing, msg="Missing {} in node data".format(', '.join(sorted(missing))))
        self.assertTrue(all(kwarg in graph.nodes[node] for kwarg in kwargs),
                        msg="Missing kwarg in node data")
        self.assertEqual(kwargs, {k: graph.nodes[node][k] for k in kwargs},
                         msg="Wrong values in node data")


def any_dict_matches(dict_of_dicts, query_dict):
    """

    :param dict_of_dicts:
    :param query_dict:
    :return:
    """
    return any(
        query_dict == sd
        for sd in dict_of_dicts.values()
    )


def any_subdict_matches(dict_of_dicts, query_dict):
    """Checks if dictionary target_dict matches one of the subdictionaries of a

    :param dict[any,dict] dict_of_dicts: dictionary of dictionaries
    :param dict query_dict: dictionary
    :return: if dictionary target_dict matches one of the subdictionaries of a
    :rtype: bool
    """
    return any(
        subdict_matches(sub_dict, query_dict)
        for sub_dict in dict_of_dicts.values()
    )


def assert_has_edge(self: unittest.TestCase, u: BaseEntity, v: BaseEntity, graph: BELGraph, permissive=True, **kwargs):
    """A helper function for checking if an edge with the given properties is contained within a graph."""
    self.assertIsInstance(u, BaseEntity)
    self.assertIsInstance(v, BaseEntity)

    self.assertTrue(
        graph.has_edge(u, v),
        msg='Edge ({}, {}) not in graph. Other edges:\n{}'.format(u, v, '\n'.join(
            '{} {} {}'.format(u.as_bel(), d[RELATION], v.as_bel())
            for u, v, d in graph.edges(data=True)
        ))
    )

    if not kwargs:
        return

    if permissive:
        matches = any_subdict_matches(graph[u][v], kwargs)
    else:
        matches = any_dict_matches(graph[u][v], kwargs)

    msg = 'No edge ({}, {}) with correct properties. expected:\n {}\nbut got:\n{}'.format(
        u,
        v,
        dumps(kwargs, indent=2, sort_keys=True),
        str(graph[u][v])
    )
    self.assertTrue(matches, msg=msg)


class TestGraphMixin(unittest.TestCase):
    """A test case with additional functions for testing graphs."""

    def assert_has_node(self, g: BELGraph, n: BaseEntity, **kwargs):
        """Help assert node membership."""
        assert_has_node(self, n, g, **kwargs)

    def assert_has_edge(self, g: BELGraph, u: BaseEntity, v: BaseEntity, **kwargs):
        """Help assert edge membership."""
        assert_has_edge(self, u, v, g, **kwargs)


class TestTokenParserBase(unittest.TestCase):
    """A test case that has a BEL parser available."""

    @classmethod
    def setUpClass(cls):
        """Build a BEL graph and BEL parser that persist through the class."""
        cls.graph = BELGraph()
        cls.parser = BELParser(
            cls.graph,
            autostreamline=False,
            disallow_unqualified_translocations=True,
        )

    def setUp(self):
        """Clear the parser at the beginning of each test."""
        self.parser.clear()

    def assert_has_node(self, member: BaseEntity, **kwargs):
        """Assert that this test case's graph has the given node."""
        assert_has_node(self, member, self.graph, **kwargs)

    def assert_has_edge(self, u: BaseEntity, v: BaseEntity, **kwargs):
        """Assert that this test case's graph has the given edge."""
        assert_has_edge(self, u, v, self.graph, **kwargs)

    def add_default_provenance(self):
        """Add a default citation and evidence to the parser."""
        update_provenance(self.parser.control_parser)


def help_check_hgnc(test_case: unittest.TestCase, namespace_dict) -> None:
    """Assert that the namespace dictionary is correct."""
    test_case.assertIn(HGNC_KEYWORD, namespace_dict)

    test_case.assertIn('MHS2', namespace_dict[HGNC_KEYWORD])
    test_case.assertEqual(set('G'), set(namespace_dict[HGNC_KEYWORD]['MHS2']))

    test_case.assertIn('MIATNB', namespace_dict[HGNC_KEYWORD])
    test_case.assertEqual(set('GR'), set(namespace_dict[HGNC_KEYWORD]['MIATNB']))

    test_case.assertIn('MIA', namespace_dict[HGNC_KEYWORD])
    test_case.assertEqual(set('GRP'), set(namespace_dict[HGNC_KEYWORD]['MIA']))


class BelReconstitutionMixin(TestGraphMixin):
    """A test case that has checks for properly loading several BEL Scripts."""

    def bel_simple_reconstituted(self, graph: BELGraph, check_metadata: bool = True):
        """Check that test_bel.bel was loaded properly."""
        self.assertIsNotNone(graph)
        self.assertIsInstance(graph, BELGraph)

        if check_metadata:
            self.assertIsNotNone(graph.document)
            self.assertEqual(expected_test_simple_metadata[METADATA_NAME], graph.name)
            self.assertEqual(expected_test_simple_metadata[METADATA_VERSION], graph.version)

        self.assertEqual(4, graph.number_of_nodes())

        # FIXME this should work, but is getting 8 for the upgrade function
        # self.assertEqual(6, graph.number_of_edges(),
        #                  msg='Edges:\n{}'.format('\n'.join(map(str, graph.edges(keys=True, data=True)))))

        for node in graph:
            self.assertIsInstance(node, BaseEntity)

        self.assertIn(akt1, graph)
        self.assertIn(egfr, graph)
        self.assertIn(fadd, graph)
        self.assertIn(casp8, graph)

        bel_simple_citation_1 = {
            CITATION_NAME: "That one article from last week",
            CITATION_REFERENCE: "123455",
            CITATION_TYPE: "PubMed"
        }

        bel_simple_citation_2 = {
            CITATION_NAME: "That other article from last week",
            CITATION_REFERENCE: "123456",
            CITATION_TYPE: "PubMed"
        }

        evidence_1_extra = "Evidence 1 w extra notes"
        evidence_2 = 'Evidence 2'
        evidence_3 = 'Evidence 3'

        assert_has_edge(self, akt1, egfr, graph, **{
            RELATION: INCREASES,
            CITATION: bel_simple_citation_1,
            EVIDENCE: evidence_1_extra,
            ANNOTATIONS: {
                'Species': {'9606': True}
            }
        })
        assert_has_edge(self, egfr, fadd, graph, **{
            RELATION: DECREASES,
            ANNOTATIONS: {
                'Species': {'9606': True},
                'CellLine': {'10B9 cell': True}
            },
            CITATION: bel_simple_citation_1,
            EVIDENCE: evidence_2
        })
        assert_has_edge(self, egfr, casp8, graph, **{
            RELATION: DIRECTLY_DECREASES,
            ANNOTATIONS: {
                'Species': {'9606': True},
                'CellLine': {'10B9 cell': True}
            },
            CITATION: bel_simple_citation_1,
            EVIDENCE: evidence_2,
        })
        assert_has_edge(self, fadd, casp8, graph, **{
            RELATION: INCREASES,
            ANNOTATIONS: {
                'Species': {'10116': True}
            },
            CITATION: bel_simple_citation_2,
            EVIDENCE: evidence_3,
        })
        assert_has_edge(self, akt1, casp8, graph, **{
            RELATION: ASSOCIATION,
            ANNOTATIONS: {
                'Species': {'10116': True}
            },
            CITATION: bel_simple_citation_2,
            EVIDENCE: evidence_3,
        })
        assert_has_edge(self, casp8, akt1, graph, **{
            RELATION: ASSOCIATION,
            ANNOTATIONS: {
                'Species': {'10116': True}
            },
            CITATION: bel_simple_citation_2,
            EVIDENCE: evidence_3,
        })

    def bel_thorough_reconstituted(self,
                                   graph: BELGraph,
                                   check_metadata: bool = True,
                                   check_warnings: bool = True,
                                   check_provenance: bool = True,
                                   check_citation_name: bool = True,
                                   check_path: bool = True,
                                   ):
        """Check that thorough.bel was loaded properly.

        :param graph: A BEL graph
        :param check_metadata: Check the graph's document section is correct
        :param check_warnings: Check the graph produced the expected warnings
        :param check_provenance: Check the graph's definition section is correct
        :param check_citation_name: Check that the names in the citations get reconstituted. This isn't strictly
                                         necessary since this data can be looked up
        :param check_path: Check the graph contains provenance for its original file
        """
        self.assertIsNotNone(graph)
        self.assertIsInstance(graph, BELGraph)

        if check_warnings:
            self.assertEqual(0, len(graph.warnings),
                             msg='Document warnings:\n{}'.format('\n'.join(map(str, graph.warnings))))

        if check_metadata:
            self.assertLessEqual(set(expected_test_thorough_metadata), set(graph.document))
            self.assertEqual(expected_test_thorough_metadata[METADATA_NAME], graph.name)
            self.assertEqual(expected_test_thorough_metadata[METADATA_VERSION], graph.version)
            self.assertEqual(expected_test_thorough_metadata[METADATA_DESCRIPTION], graph.description)

        if check_path:
            self.assertEqual(test_bel_thorough, graph.path)

        if check_provenance:
            self.assertEqual({'CHEBI', 'HGNC', 'GO', 'MESHD', 'TESTNS2'}, set(graph.namespace_url))
            self.assertEqual({'dbSNP'}, set(graph.namespace_pattern))
            self.assertIn('TESTAN1', graph.annotation_list)
            self.assertIn('TESTAN2', graph.annotation_list)
            self.assertEqual(2, len(graph.annotation_list), msg='Wrong number of locally defined annotations')
            self.assertEqual({'TestRegex'}, set(graph.annotation_pattern))

        for node in graph:
            self.assertIsInstance(node, BaseEntity)

        self.assertEqual(set(BEL_THOROUGH_NODES), set(graph), msg='Nodes not equal')

        # FIXME
        # self.assertEqual(set((u, v) for u, v, _ in e), set(g.edges()))

        self.assertLess(0, graph.number_of_edges())

        for u, v, data in BEL_THOROUGH_EDGES:
            if not check_citation_name and CITATION in data and CITATION_NAME in data[CITATION]:
                data[CITATION] = data[CITATION].copy()
                del data[CITATION][CITATION_NAME]

            assert_has_edge(self, u, v, graph, permissive=True, **data)

    def bel_slushy_reconstituted(self, graph: BELGraph, check_metadata: bool = True, check_warnings: bool = True):
        """Check that slushy.bel was loaded properly."""
        self.assertIsNotNone(graph)
        self.assertIsInstance(graph, BELGraph)

        if check_metadata:
            self.assertIsNotNone(graph.document)
            self.assertIsInstance(graph.document, dict)

            expected_test_slushy_metadata = {
                METADATA_NAME: "Worst. BEL Document. Ever.",
                METADATA_DESCRIPTION: "This document outlines all of the evil and awful work that is possible during BEL curation",
                METADATA_VERSION: "0.0",
                METADATA_AUTHORS: "Charles Tapley Hoyt",
                METADATA_LICENSES: "WTF License",
            }

            self.assertEqual(expected_test_slushy_metadata[METADATA_NAME], graph.name)
            self.assertEqual(expected_test_slushy_metadata[METADATA_VERSION], graph.version)
            self.assertEqual(expected_test_slushy_metadata[METADATA_DESCRIPTION], graph.description)

        if check_warnings:
            expected_warnings = [
                (0, MissingMetadataException),
                (3, VersionFormatWarning),
                (26, MissingAnnotationKeyWarning),
                (29, MissingAnnotationKeyWarning),
                (34, InvalidCitationLengthException),
                (37, InvalidCitationType),
                (40, InvalidPubMedIdentifierWarning),
                (43, MissingCitationException),
                (48, MissingAnnotationKeyWarning),
                (51, MissingAnnotationKeyWarning),
                (54, MissingSupportWarning),
                (59, NakedNameWarning),
                (62, UndefinedNamespaceWarning),
                (65, MissingNamespaceNameWarning),
                (68, UndefinedAnnotationWarning),
                (71, MissingAnnotationKeyWarning),
                (74, IllegalAnnotationValueWarning),
                (77, MissingAnnotationRegexWarning),
                (80, MissingNamespaceRegexWarning),
                (83, MalformedTranslocationWarning),
                (86, PlaceholderAminoAcidWarning),
                (89, NestedRelationWarning),
                (92, InvalidFunctionSemantic),
                # (95, Exception),
                (98, BELSyntaxError),
            ]

            for warning_tuple in graph.warnings:
                self.assertEqual(3, len(warning_tuple), msg='Warning tuple is wrong size: {}'.format(warning_tuple))

            for (el, ew), (_, exc, _) in zip(expected_warnings, graph.warnings):
                self.assertIsInstance(exc, BELParserWarning)
                self.assertIsInstance(exc.line, str)
                self.assertIsInstance(exc.line_number, int)
                self.assertIsInstance(exc.position, int)
                self.assertEqual(el, exc.line_number, msg="Expected {} on line {} but got {} on line {}: {}".format(
                    ew, el, exc.__class__, exc.line_number, exc
                ))
                self.assertIsInstance(exc, ew, msg='Line: {}'.format(el))

        for node in graph:
            self.assertIsInstance(node, BaseEntity)

        self.assertIn(akt1, graph, msg='AKT1 not in graph')
        self.assertIn(egfr, graph, msg='EGFR not in graph')

        self.assertEqual(2, graph.number_of_nodes(), msg='Wrong number of nodes retrieved from slushy.bel')
        self.assertEqual(1, graph.number_of_edges(), msg='Wrong nunber of edges retrieved from slushy.bel')

        assert_has_edge(self, akt1, egfr, graph, **{
            RELATION: INCREASES,
            CITATION: citation_1,
            EVIDENCE: evidence_1,
        })

    def bel_isolated_reconstituted(self, graph: BELGraph):
        """Run the isolated node test."""
        self.assertIsNotNone(graph)
        self.assertIsInstance(graph, BELGraph)

        adgrb1 = protein(namespace='HGNC', name='ADGRB1')
        adgrb2 = protein(namespace='HGNC', name='ADGRB2')
        adgrb_complex = complex_abundance([adgrb1, adgrb2])
        achlorhydria = pathology(namespace='MESHD', name='Achlorhydria')

        for node in graph:
            self.assertIsInstance(node, BaseEntity)

        self.assertIn(adgrb1, graph)
        self.assertIn(adgrb2, graph)
        self.assertIn(adgrb_complex, graph)
        self.assertIn(achlorhydria, graph)

        assert_has_edge(self, adgrb_complex, adgrb1, graph)
        assert_has_edge(self, adgrb_complex, adgrb2, graph)
