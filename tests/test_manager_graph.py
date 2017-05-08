# -*- coding: utf-8 -*-

import logging
import unittest
from collections import Counter

import sqlalchemy.exc

import pybel
from pybel import from_path
from pybel.constants import *
from pybel.manager import models
from tests import constants
from tests.constants import test_bel_thorough, mock_bel_resources, \
    expected_test_thorough_metadata, test_bel_simple, expected_test_simple_metadata, TemporaryCacheMixin, \
    BelReconstitutionMixin

log = logging.getLogger(__name__)


class TestGraphCache(TemporaryCacheMixin, BelReconstitutionMixin):
    def setUp(self):
        super(TestGraphCache, self).setUp()
        self.graph = from_path(test_bel_thorough, manager=self.manager, allow_nested=True)

    @mock_bel_resources
    def test_reload(self, mock_get):
        """Tests that a graph with the same name and version can't be added twice"""
        self.manager.insert_graph(self.graph)

        x = self.manager.list_graphs()

        self.assertEqual(1, len(x))
        self.assertEqual((1, expected_test_thorough_metadata[METADATA_NAME],
                          expected_test_thorough_metadata[METADATA_VERSION],
                          expected_test_thorough_metadata[METADATA_DESCRIPTION]), x[0])

        reconstituted = self.manager.get_graph(expected_test_thorough_metadata[METADATA_NAME],
                                               expected_test_thorough_metadata[METADATA_VERSION])
        self.bel_thorough_reconstituted(reconstituted)

        # Test that the graph can't be added a second time
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.manager.insert_graph(self.graph)

    @mock_bel_resources
    def test_get_versions(self, mock_get):
        TEST_V1 = '0.9'
        TEST_V2 = expected_test_thorough_metadata[METADATA_VERSION]  # Actually is 1.0

        self.graph.document[METADATA_VERSION] = TEST_V1
        self.manager.insert_graph(self.graph)

        self.graph.document[METADATA_VERSION] = TEST_V2
        self.manager.insert_graph(self.graph)

        self.assertEqual({TEST_V1, TEST_V2}, set(self.manager.get_graph_versions(self.graph.document[METADATA_NAME])))

        self.assertEqual(TEST_V2, self.manager.get_graph(self.graph.document[METADATA_NAME]).document[METADATA_VERSION])


@unittest.skipUnless('PYBEL_TEST_EXPERIMENTAL' in os.environ, 'Experimental features not ready for Travis')
class TestGraphCacheSimple(TemporaryCacheMixin, BelReconstitutionMixin):
    def setUp(self):
        super(TestGraphCacheSimple, self).setUp()
        self.simple_graph = pybel.from_path(test_bel_simple, manager=self.manager)

    @mock_bel_resources
    def test_get_or_create_node(self, mock_get):
        network = self.manager.insert_graph(self.simple_graph, store_parts=True)

        citations = self.manager.session.query(models.Citation).all()
        self.assertEqual(2, len(citations))

        citations_strs = {'123455', '123456'}
        self.assertEqual(citations_strs, {e.reference for e in citations})

        authors = {'Example Author', 'Example Author2'}
        self.assertEqual(authors, {a.name for a in self.manager.session.query(models.Author).all()})

        evidences = self.manager.session.query(models.Evidence).all()
        self.assertEqual(3, len(evidences))

        evidences_strs = {'Evidence 1 w extra notes', 'Evidence 2', 'Evidence 3'}
        self.assertEqual(evidences_strs, {e.text for e in evidences})

        nodes = self.manager.session.query(models.Node).all()
        self.assertEqual(4, len(nodes))

        edges = self.manager.session.query(models.Edge).all()

        x = Counter((e.source.bel, e.target.bel) for e in edges)

        pfmt = 'p(HGNC:{})'
        d = {
            (pfmt.format(constants.AKT1[2]), pfmt.format(constants.EGFR[2])): 1,
            (pfmt.format(constants.EGFR[2]), pfmt.format(constants.FADD[2])): 1,
            (pfmt.format(constants.EGFR[2]), pfmt.format(constants.CASP8[2])): 1,
            (pfmt.format(constants.FADD[2]), pfmt.format(constants.CASP8[2])): 1,
            (pfmt.format(constants.AKT1[2]), pfmt.format(constants.CASP8[2])): 1,  # two way association
            (pfmt.format(constants.CASP8[2]), pfmt.format(constants.AKT1[2])): 1  # two way association
        }

        self.assertEqual(dict(x), d)

        network_edge_associations = self.manager.session.query(models.network_edge).filter_by(
            network_id=network.id).all()
        self.assertEqual({nea.edge_id for nea in network_edge_associations},
                         {edge.id for edge in edges})

        g2 = self.manager.get_graph(expected_test_simple_metadata[METADATA_NAME],
                                    expected_test_simple_metadata[METADATA_VERSION])
        self.bel_simple_reconstituted(g2)


@unittest.skipUnless('PYBEL_TEST_EXPERIMENTAL' in os.environ, 'Experimental features not ready for Travis')
class TestQueryNode(TemporaryCacheMixin, BelReconstitutionMixin):
    """Tests that the cache can be queried"""

    def setUp(self):
        super(TestQueryNode, self).setUp()
        self.graph = pybel.from_path(test_bel_simple, manager=self.manager, allow_nested=True)
        self.manager.insert_graph(self.graph, store_parts=True)

        self.akt1_dict = {
            'key': ('Protein', 'HGNC', 'AKT1'),
            'data': {
                FUNCTION: 'Protein',
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            }
        }

    @mock_bel_resources
    def test_query_node(self, mock_get):
        node_list = self.manager.get_node(bel='p(HGNC:AKT1)')
        self.assertEqual(len(node_list), 1)

        node_dict_list = self.manager.get_node(bel='p(HGNC:AKT1)', as_dict_list=True)
        self.assertIn(self.akt1_dict, node_dict_list)

        node_dict_list2 = self.manager.get_node(namespace='HG%', as_dict_list=True)
        self.assertEqual(len(node_dict_list2), 4)
        self.assertIn(self.akt1_dict, node_dict_list2)

        node_dict_list3 = self.manager.get_node(name='%A%', as_dict_list=True)
        self.assertEqual(len(node_dict_list3), 3)
        self.assertIn(self.akt1_dict, node_dict_list3)

        protein_list = self.manager.get_node(type='Protein')
        self.assertEqual(len(protein_list), 4)


@unittest.skipUnless('PYBEL_TEST_EXPERIMENTAL' in os.environ, 'Experimental features not ready for Travis')
class TestQueryEdge(TemporaryCacheMixin, BelReconstitutionMixin):
    """Tests that the cache can be queried"""

    def setUp(self):
        super(TestQueryEdge, self).setUp()
        self.graph = pybel.from_path(test_bel_simple, manager=self.manager, allow_nested=True)
        self.manager.insert_graph(self.graph, store_parts=True)
        self.fadd_casp = {
            'source': {
                'node': (('Protein', 'HGNC', 'FADD'), {
                    FUNCTION: 'Protein',
                    NAMESPACE: 'HGNC',
                    NAME: 'FADD'
                }),
                'key': ('Protein', 'HGNC', 'FADD')
            },
            'target': {
                'node': (('Protein', 'HGNC', 'CASP8'), {
                    FUNCTION: 'Protein',
                    NAMESPACE: 'HGNC',
                    NAME: 'CASP8'
                }),
                'key': ('Protein', 'HGNC', 'CASP8')
            },
            'data': {
                RELATION: 'increases',
                ANNOTATIONS: {
                    'Species': '10116'
                },
                CITATION: {
                    CITATION_TYPE: "PubMed",
                    CITATION_NAME: "That other article from last week",
                    CITATION_REFERENCE: "123456"
                },
                EVIDENCE: "Evidence 3"
            },
            'key': 0
        }

    @mock_bel_resources
    def test_query_edge(self, mock_get):
        # bel
        edge_list = self.manager.get_edge(bel="p(HGNC:EGFR) decreases p(HGNC:FADD)")
        self.assertEqual(len(edge_list), 1)

        # relation like, data
        increased_list = self.manager.get_edge(relation='increase%', as_dict_list=True)
        self.assertEqual(len(increased_list), 2)
        self.assertIn(self.fadd_casp, increased_list)

        # evidence like, data
        evidence_list = self.manager.get_edge(evidence='%3%', as_dict_list=True)
        self.assertEqual(len(increased_list), 2)
        self.assertIn(self.fadd_casp, evidence_list)

        # no result
        empty_list = self.manager.get_edge(source='p(HGNC:EGFR)', relation='increases', as_dict_list=True)
        self.assertEqual(len(empty_list), 0)

        # source, relation, data
        source_list = self.manager.get_edge(source='p(HGNC:FADD)', relation='increases', as_dict_list=True)
        self.assertEqual(len(source_list), 1)
        self.assertIn(self.fadd_casp, source_list)


@unittest.skipUnless('PYBEL_TEST_EXPERIMENTAL' in os.environ, 'Experimental features not ready for Travis')
class TestQueryCitation(TemporaryCacheMixin, BelReconstitutionMixin):
    """Tests that the cache can be queried"""

    def setUp(self):
        super(TestQueryCitation, self).setUp()
        self.graph = pybel.from_path(test_bel_simple, manager=self.manager, allow_nested=True)
        self.manager.insert_graph(self.graph, store_parts=True)

    @mock_bel_resources
    def test_query_citation(self, mock_get):
        citation_1 = {
            CITATION_TYPE: "PubMed",
            CITATION_NAME: "That one article from last week",
            CITATION_REFERENCE: "123455",
            CITATION_DATE: "2012-01-31",
            CITATION_AUTHORS: "Example Author|Example Author2"
        }
        citation_2 = {
            CITATION_TYPE: "PubMed",
            CITATION_NAME: "That other article from last week",
            CITATION_REFERENCE: "123456"
        }
        evidence_citation = {
            CITATION: citation_1,
            EVIDENCE: 'Evidence 1 w extra notes'
        }
        evidence_citation_2 = {
            CITATION: citation_1,
            EVIDENCE: 'Evidence 2'
        }
        evidence_citation_3 = {
            CITATION: citation_2,
            EVIDENCE: "Evidence 3"
        }

        # type
        object_list = self.manager.get_citation(type='PubMed')
        self.assertEqual(len(object_list), 2)

        # type, reference, data
        reference_list = self.manager.get_citation(type='PubMed', reference='123456', as_dict_list=True)
        self.assertEqual(len(reference_list), 1)
        self.assertIn(citation_2, reference_list)

        # author
        author_list = self.manager.get_citation(author="Example%")
        self.assertEqual(len(author_list), 1)

        # author, data
        author_dict_list = self.manager.get_citation(author="Example Author", as_dict_list=True)
        self.assertIn(citation_1, author_dict_list)

        # author list, data
        author_dict_list2 = self.manager.get_citation(author=["Example Author", "Example Author2"], as_dict_list=True)
        self.assertIn(citation_1, author_dict_list2)

        # type, name, data
        name_dict_list = self.manager.get_citation(type='PubMed', name="That other article from last week",
                                                   as_dict_list=True)
        self.assertEqual(len(name_dict_list), 1)
        self.assertIn(citation_2, name_dict_list)

        # type, name like, data
        name_dict_list2 = self.manager.get_citation(type='PubMed', name="%article from%", as_dict_list=True)
        self.assertEqual(len(name_dict_list2), 2)
        self.assertIn(citation_1, name_dict_list2)
        self.assertIn(citation_2, name_dict_list2)

        # type, name, evidence, data
        evidence_dict_list = self.manager.get_citation(type='PubMed', name="That other article from last week",
                                                       evidence=True, as_dict_list=True)
        self.assertEqual(len(name_dict_list), 1)
        self.assertIn(evidence_citation_3, evidence_dict_list)

        # type, evidence like, data
        evidence_dict_list2 = self.manager.get_citation(type='PubMed', evidence_text='%Evi%', as_dict_list=True)
        self.assertEqual(len(evidence_dict_list2), 3)
        self.assertIn(evidence_citation, evidence_dict_list2)
        self.assertIn(evidence_citation_2, evidence_dict_list2)
        self.assertIn(evidence_citation_3, evidence_dict_list2)


@unittest.skipUnless('PYBEL_TEST_EXPERIMENTAL' in os.environ, 'Experimental features not ready for Travis')
class TestFilter(TemporaryCacheMixin, BelReconstitutionMixin):
    """Tests that a graph can be reconstructed from the edge and node relational tables in the database

    1. Load graph (test BEL 1 or test thorough)
    2. Add sentinel annotation to ALL edges
    3. Store graph
    4. Query for all edges with sentinel annotation
    5. Compare to original graph
    """

    def setUp(self):
        super(TestFilter, self).setUp()
        self.graph = pybel.from_path(test_bel_thorough, manager=self.manager, allow_nested=True)

    @mock_bel_resources
    def test_database_edge_filter(self, mock_get):
        self.help_database_edge_filter(test_bel_simple, self.bel_simple_reconstituted)

    @mock_bel_resources
    def test_database_edge_filter(self, mock_get):
        self.help_database_edge_filter(test_bel_thorough, self.bel_thorough_reconstituted)

    def help_database_edge_filter(self, path, compare, annotation_tag='MeSHDisease', value_tag='Arm Injuries'):
        """Helps to test the graph that is created by a specific annotation.

        :param path: Path to the test BEL file.
        :type path: str
        :param compare: Method that should be used to compare the original and resulting graph.
        :type compare:
        :param annotation_tag: Annotation that marks the nodes with an annotation.
        :type annotation_tag: str
        :param value_tag: Annotation value for the given sentinel_annotation.
        :type value_tag: str
        """
        original = pybel.from_path(path)

        compare(original)

        for u, v, k in original.edges(keys=True):
            original.edge[u][v][k][annotation_tag] = value_tag

        self.manager.insert_graph(original, store_parts=True)

        reloaded = self.manager.rebuild_by_edge_filter(**{ANNOTATIONS: {annotation_tag: value_tag}})

        for u, v, k in reloaded.edges(keys=True):
            del reloaded.edge[u][v][k][annotation_tag]

        compare(reloaded, check_metadata=False)
