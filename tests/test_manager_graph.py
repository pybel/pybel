# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from collections import Counter

import pybel
import sqlalchemy.exc
from pybel.constants import CITATION_AUTHORS, CITATION_DATE, CITATION_NAME, CITATION_TYPE, CITATION_REFERENCE
from pybel.constants import METADATA_NAME, METADATA_VERSION, EVIDENCE, CITATION, FUNCTION, NAMESPACE, NAME, RELATION, ANNOTATIONS
from pybel.manager import models
from pybel.manager.graph_cache import GraphCacheManager
from tests import constants
from tests.constants import BelReconstitutionMixin, test_bel_thorough, mock_bel_resources, \
    expected_test_thorough_metadata, test_bel_simple

TEST_BEL_NAME = 'PyBEL Test Document 1'
TEST_BEL_VERSION = '1.6'


class TestGraphCache(BelReconstitutionMixin, unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.dir, 'test.db')
        self.connection = 'sqlite:///' + self.db_path
        self.graph = pybel.from_path(test_bel_thorough, manager=self.connection, allow_nested=True)
        self.gcm = GraphCacheManager(connection=self.connection)

    def tearDown(self):
        os.remove(self.db_path)
        os.rmdir(self.dir)

    @mock_bel_resources
    def test_load_reload(self, mock_get):
        name = expected_test_thorough_metadata[METADATA_NAME]
        version = expected_test_thorough_metadata[METADATA_VERSION]

        self.gcm.insert_graph(self.graph)

        x = self.gcm.ls()

        self.assertEqual(1, len(x))
        self.assertEqual((1, name, version), x[0])

        g2 = self.gcm.get_graph(name, version)
        self.bel_thorough_reconstituted(g2)

    @mock_bel_resources
    def test_integrity_failure(self, mock_get):
        """Tests that a graph with the same name and version can't be added twice"""
        self.gcm.insert_graph(self.graph)

        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.gcm.insert_graph(self.graph)

    @mock_bel_resources
    def test_get_versions(self, mock_get):
        TEST_V1 = '0.9'
        TEST_V2 = expected_test_thorough_metadata[METADATA_VERSION]  # Actually is 1.0

        self.graph.document[METADATA_VERSION] = TEST_V1
        self.gcm.insert_graph(self.graph)

        self.graph.document[METADATA_VERSION] = TEST_V2
        self.gcm.insert_graph(self.graph)

        self.assertEqual({TEST_V1, TEST_V2}, set(self.gcm.get_graph_versions(self.graph.document[METADATA_NAME])))

        self.assertEqual(TEST_V2, self.gcm.get_graph(self.graph.document[METADATA_NAME]).document[METADATA_VERSION])


class TestGraphCacheSimple(BelReconstitutionMixin, unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.dir, 'test.db')
        self.connection = 'sqlite:///' + self.db_path
        self.simple_graph = pybel.from_path(test_bel_simple, manager=self.connection)
        self.gcm = GraphCacheManager(connection=self.connection)

    def tearDown(self):
        os.remove(self.db_path)
        os.rmdir(self.dir)

    @mock_bel_resources
    def test_get_or_create_node(self, mock_get):
        network = self.gcm.insert_graph(self.simple_graph, store_parts=True)

        citations = self.gcm.session.query(models.Citation).all()
        self.assertEqual(2, len(citations))

        citations_strs = {'123455', '123456'}
        self.assertEqual(citations_strs, {e.reference for e in citations})

        authors = {'Example Author', 'Example Author2'}
        self.assertEqual(authors, {a.name for a in self.gcm.session.query(models.Author).all()})

        evidences = self.gcm.session.query(models.Evidence).all()
        self.assertEqual(3, len(evidences))

        evidences_strs = {'Evidence 1 w extra notes', 'Evidence 2', 'Evidence 3'}
        self.assertEqual(evidences_strs, {e.text for e in evidences})

        nodes = self.gcm.session.query(models.Node).all()
        self.assertEqual(4, len(nodes))

        edges = self.gcm.session.query(models.Edge).all()

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

        network_edge_associations = self.gcm.session.query(models.network_edge).filter_by(network_id=network.id).all()
        self.assertEqual({nea.edge_id for nea in network_edge_associations},
                         {edge.id for edge in edges})

        g2 = self.gcm.get_graph(TEST_BEL_NAME, TEST_BEL_VERSION)
        self.bel_simple_reconstituted(g2)


class TestQuery(BelReconstitutionMixin, unittest.TestCase):
    """Tests that the cache can be queried"""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.dir, 'test.db')
        self.connection = 'sqlite:///' + self.db_path
        self.graph = pybel.from_path(test_bel_simple, manager=self.connection, allow_nested=True)
        self.gcm = GraphCacheManager(connection=self.connection)
        self.gcm.insert_graph(self.graph, True)

    @mock_bel_resources
    def test_query_node(self, mock_get):
        akt1_dict = {
            'key': ('Protein', 'HGNC', 'AKT1'),
            'data': {
                FUNCTION: 'Protein',
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            }
        }

        node_list = self.gcm.query_node(bel='p(HGNC:AKT1)')
        self.assertEqual(len(node_list), 1)

        node_dict_list = self.gcm.query_node(bel='p(HGNC:AKT1)', as_dict_list=True)
        self.assertIn(akt1_dict, node_dict_list)

        node_dict_list2 = self.gcm.query_node(namespace='HG%', as_dict_list=True)
        self.assertEqual(len(node_dict_list2), 4)
        self.assertIn(akt1_dict, node_dict_list2)

        node_dict_list3 = self.gcm.query_node(name='%A%', as_dict_list=True)
        self.assertEqual(len(node_dict_list3), 3)
        self.assertIn(akt1_dict, node_dict_list3)

        protein_list = self.gcm.query_node(type='Protein')
        self.assertEqual(len(protein_list), 4)


    @mock_bel_resources
    def test_query_edge(self, mock_get):
        fadd_casp = {
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

        # bel
        edge_list = self.gcm.query_edge(bel="p(HGNC:EGFR) decreases p(HGNC:FADD)")
        self.assertEqual(len(edge_list), 1)

        # relation like, data
        increased_list = self.gcm.query_edge(relation='increase%', as_dict_list=True)
        self.assertEqual(len(increased_list), 2)
        self.assertIn(fadd_casp, increased_list)

        # evidence like, data
        evidence_list = self.gcm.query_edge(evidence='%3%', as_dict_list=True)
        self.assertEqual(len(increased_list), 2)
        self.assertIn(fadd_casp, evidence_list)

        # no result
        empty_list = self.gcm.query_edge(source='p(HGNC:EGFR)', relation='increases',  as_dict_list=True)
        self.assertEqual(len(empty_list), 0)

        # source, relation, data
        source_list = self.gcm.query_edge(source='p(HGNC:FADD)', relation='increases', as_dict_list=True)
        self.assertEqual(len(source_list), 1)
        self.assertIn(fadd_casp, source_list)


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
        object_list = self.gcm.query_citation(type='PubMed')
        self.assertEqual(len(object_list), 2)

        # type, reference, data
        reference_list = self.gcm.query_citation(type='PubMed', reference='123456', as_dict_list=True)
        self.assertEqual(len(reference_list), 1)
        self.assertIn(citation_2, reference_list)

        # author
        author_list = self.gcm.query_citation(author="Example%")
        self.assertEqual(len(author_list), 1)

        # author, data
        author_dict_list = self.gcm.query_citation(author="Example Author", as_dict_list=True)
        self.assertIn(citation_1, author_dict_list)

        # author list, data
        author_dict_list2 = self.gcm.query_citation(author=["Example Author", "Example Author2"], as_dict_list=True)
        self.assertIn(citation_1, author_dict_list2)

        # type, name, data
        name_dict_list = self.gcm.query_citation(type='PubMed', name="That other article from last week",
                                                 as_dict_list=True)
        self.assertEqual(len(name_dict_list), 1)
        self.assertIn(citation_2, name_dict_list)

        # type, name like, data
        name_dict_list2 = self.gcm.query_citation(type='PubMed', name="%article from%", as_dict_list=True)
        self.assertEqual(len(name_dict_list2), 2)
        self.assertIn(citation_1, name_dict_list2)
        self.assertIn(citation_2, name_dict_list2)

        # type, name, evidence, data
        evidence_dict_list = self.gcm.query_citation(type='PubMed', name="That other article from last week",
                                                     evidence=True, as_dict_list=True)
        self.assertEqual(len(name_dict_list), 1)
        self.assertIn(evidence_citation_3, evidence_dict_list)

        # type, evidence like, data
        evidence_dict_list2 = self.gcm.query_citation(type='PubMed', evidence_text='%Evi%', as_dict_list=True)
        self.assertEqual(len(evidence_dict_list2), 3)
        self.assertIn(evidence_citation, evidence_dict_list2)
        self.assertIn(evidence_citation_2, evidence_dict_list2)
        self.assertIn(evidence_citation_3, evidence_dict_list2)


@unittest.skip('Feature not started yet')
class TestFilter(BelReconstitutionMixin, unittest.TestCase):
    """Tests that a graph can be reconstructed from the edge and node relational tables in the database

    1. Load graph (test BEL 1 or test thorough)
    2. Add sentinel annotation to ALL edges
    3. Store graph
    4. Query for all edges with sentinel annotation
    5. Compare to original graph
    """

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.dir, 'test.db')
        self.connection = 'sqlite:///' + self.db_path
        self.graph = pybel.from_path(test_bel_thorough, manager=self.connection, allow_nested=True)
        self.gcm = GraphCacheManager(connection=self.connection)

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

        self.gcm.insert_graph(original, store_parts=True)

        reloaded = self.gcm.rebuild_by_edge_filter({annotation_tag: value_tag})

        for u, v, k in reloaded.edges(keys=True):
            del reloaded.edge[u][v][k][annotation_tag]

        compare(reloaded, check_metadata=False)
