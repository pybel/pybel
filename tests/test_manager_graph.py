# -*- coding: utf-8 -*-

import logging
import os
import unittest
from collections import Counter

import sqlalchemy.exc

import pybel
from pybel import from_path
from pybel.constants import *
from pybel import from_database, to_database
from pybel.manager import models
from tests import constants
from tests.constants import FleetingTemporaryCacheMixin, BelReconstitutionMixin, TemporaryCacheClsMixin
from tests.constants import test_bel_simple, expected_test_simple_metadata
from tests.constants import test_bel_thorough, expected_test_thorough_metadata
from tests.mocks import mock_bel_resources

log = logging.getLogger(__name__)


class TestNetworkCache(BelReconstitutionMixin, FleetingTemporaryCacheMixin):
    @mock_bel_resources
    def test_reload(self, mock_get):
        """Tests that a graph with the same name and version can't be added twice"""
        self.graph = from_path(test_bel_thorough, manager=self.manager, allow_nested=True)

        to_database(self.graph, connection=self.manager)

        self.assertEqual(1, self.manager.count_networks())

        networks = self.manager.list_networks()
        self.assertEqual(1, len(networks))

        network = networks[0]

        self.assertEqual(expected_test_thorough_metadata[METADATA_NAME], network.name)
        self.assertEqual(expected_test_thorough_metadata[METADATA_VERSION], network.version)
        self.assertEqual(expected_test_thorough_metadata[METADATA_DESCRIPTION], network.description)

        reconstituted = self.manager.get_network_by_name_version(
            expected_test_thorough_metadata[METADATA_NAME],
            expected_test_thorough_metadata[METADATA_VERSION]
        )
        self.bel_thorough_reconstituted(reconstituted)

        # Test that the graph can't be added a second time
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.manager.insert_graph(self.graph)

        self.manager.session.rollback()

        graphcopy = self.graph.copy()
        graphcopy.document[METADATA_VERSION] = '1.0.1'
        self.manager.insert_graph(graphcopy)

        expected_versions = {'1.0.1', self.graph.version}
        self.assertEqual(expected_versions, set(self.manager.get_network_versions(self.graph.name)))

        exact_name_version = from_database(self.graph.name, self.graph.version, connection=self.manager)
        self.assertEqual(self.graph.name, exact_name_version.name)
        self.assertEqual(self.graph.version, exact_name_version.version)

        exact_name_version = from_database(self.graph.name, '1.0.1', connection=self.manager)
        self.assertEqual(self.graph.name, exact_name_version.name)
        self.assertEqual('1.0.1', exact_name_version.version)


# FIXME @kono need proper deletion cascades
@unittest.skipUnless('PYBEL_TEST_EXPERIMENTAL' in os.environ, 'Experimental features not ready for Travis')
class TestEdgeStore(TemporaryCacheClsMixin, BelReconstitutionMixin):
    """Tests that the cache can be queried"""

    @classmethod
    def setUpClass(cls):
        super(TestEdgeStore, cls).setUpClass()

        @mock_bel_resources
        def get_graph(mock):
            return pybel.from_path(test_bel_simple, manager=cls.manager, allow_nested=True)

        cls.graph = get_graph()
        cls.network = cls.manager.insert_graph(cls.graph, store_parts=True)

    @mock_bel_resources
    def test_get_or_create_node(self, mock_get):
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
            network_id=self.network.id).all()
        self.assertEqual({nea.edge_id for nea in network_edge_associations},
                         {edge.id for edge in edges})

        g2 = self.manager.get_network_by_name_version(
            expected_test_simple_metadata[METADATA_NAME],
            expected_test_simple_metadata[METADATA_VERSION]
        )
        self.bel_simple_reconstituted(g2)

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

        node_list = self.manager.get_node(bel='p(HGNC:AKT1)')
        self.assertEqual(len(node_list), 1)

        node_dict_list = self.manager.get_node(bel='p(HGNC:AKT1)', as_dict_list=True)
        self.assertIn(akt1_dict, node_dict_list)

        node_dict_list2 = self.manager.get_node(namespace='HG%', as_dict_list=True)
        self.assertEqual(len(node_dict_list2), 4)
        self.assertIn(akt1_dict, node_dict_list2)

        node_dict_list3 = self.manager.get_node(name='%A%', as_dict_list=True)
        self.assertEqual(len(node_dict_list3), 3)
        self.assertIn(akt1_dict, node_dict_list3)

        protein_list = self.manager.get_node(type='Protein')
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

        edge_list = self.manager.get_edge(bel="p(HGNC:EGFR) decreases p(HGNC:FADD)")
        self.assertEqual(len(edge_list), 1)

        # relation like, data
        increased_list = self.manager.get_edge(relation='increase%', as_dict_list=True)
        self.assertEqual(len(increased_list), 2)
        self.assertIn(fadd_casp, increased_list)

        # evidence like, data
        evidence_list = self.manager.get_edge(evidence='%3%', as_dict_list=True)
        self.assertEqual(len(increased_list), 2)
        self.assertIn(fadd_casp, evidence_list)

        # no result
        empty_list = self.manager.get_edge(source='p(HGNC:EGFR)', relation='increases', as_dict_list=True)
        self.assertEqual(len(empty_list), 0)

        # source, relation, data
        source_list = self.manager.get_edge(source='p(HGNC:FADD)', relation='increases', as_dict_list=True)
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
class TestFilter(FleetingTemporaryCacheMixin, BelReconstitutionMixin):
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

    # TODO switch sentinel annotation to cell line
    def help_database_edge_filter(self, path, compare, annotation_tag='CellLine',
                                  value_tag='mouse x rat hybridoma cell line cell'):
        """Helps to test the graph that is created by a specific annotation.

        :param str path: Path to the test BEL file.
        :param types.FunctionType compare: Method that should be used to compare the original and resulting graph.
        :param str annotation_tag: Annotation that marks the nodes with an annotation.
        :param str value_tag: Annotation value for the given sentinel_annotation.
        """
        original = pybel.from_path(path, manager=self.manager)

        compare(original)

        for u, v, k in original.edges(keys=True):
            original.edge[u][v][k][annotation_tag] = value_tag

        self.manager.insert_graph(original, store_parts=True)

        reloaded = self.manager.rebuild_by_edge_filter(**{ANNOTATIONS: {annotation_tag: value_tag}})

        for u, v, k in reloaded.edges(keys=True):
            del reloaded.edge[u][v][k][annotation_tag]

        compare(reloaded, check_metadata=False)


if __name__ == '__main__':
    unittest.main()
