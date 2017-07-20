# -*- coding: utf-8 -*-

import logging
import os
import unittest
from collections import Counter

import sqlalchemy.exc

import pybel
from pybel import from_database, to_database
from pybel import from_path
from pybel.constants import *
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

        graph_copy = self.graph.copy()
        graph_copy.document[METADATA_VERSION] = '1.0.1'
        network_copy = self.manager.insert_graph(graph_copy)

        self.assertEqual(2, self.manager.count_networks())

        query_ids = {-1, network.id, network_copy.id}
        query_networks_result = self.manager.get_networks_by_ids(query_ids)
        self.assertEqual(2, len(query_networks_result))
        self.assertEqual({network.id, network_copy.id}, {network.id for network in query_networks_result})

        expected_versions = {'1.0.1', self.graph.version}
        self.assertEqual(expected_versions, set(self.manager.get_network_versions(self.graph.name)))

        exact_name_version = from_database(self.graph.name, self.graph.version, connection=self.manager)
        self.assertEqual(self.graph.name, exact_name_version.name)
        self.assertEqual(self.graph.version, exact_name_version.version)

        exact_name_version = from_database(self.graph.name, '1.0.1', connection=self.manager)
        self.assertEqual(self.graph.name, exact_name_version.name)
        self.assertEqual('1.0.1', exact_name_version.version)


# FIXME @kono need proper deletion cascades
# @unittest.skipUnless('PYBEL_TEST_EXPERIMENTAL' in os.environ, 'Experimental features not ready for Travis')
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

    # ============================================================
    #
    # @mock_bel_resources
    # def test_get_or_create_citation(self, mock_get):
    #     basic_citation = {
    #         CITATION_TYPE: 'PubMed',
    #         CITATION_NAME: 'TestCitation_basic',
    #         CITATION_REFERENCE: '1234AB',
    #     }
    #     full_citation = {
    #         CITATION_TYPE: 'Other',
    #         CITATION_NAME: 'TestCitation_full',
    #         CITATION_REFERENCE: 'CD5678',
    #         CITATION_DATE: '2017-04-11',
    #         CITATION_AUTHORS: 'Jackson M|Lajoie J'
    #     }
    #     full_citation_basic = {
    #         CITATION_TYPE: 'Other',
    #         CITATION_NAME: 'TestCitation_full',
    #         CITATION_REFERENCE: 'CD5678'
    #     }
    #     basic_citation_sha512 = hashlib.sha512(json.dumps(basic_citation, sort_keys=True).encode('utf-8')).hexdigest()
    #     full_citation_sha512 = hashlib.sha512(
    #         json.dumps(full_citation_basic, sort_keys=True).encode('utf-8')).hexdigest()
    #
    #     # Create
    #     basic = self.manager.get_or_create_citation(**basic_citation)
    #     self.assertIsInstance(basic, models.Citation)
    #     self.assertEqual(basic.data, basic_citation)
    #     self.assertIn(basic_citation_sha512, self.manager.object_cache['citation'])
    #
    #     full = self.manager.get_or_create_citation(**full_citation)
    #     self.assertIsInstance(full, models.Citation)
    #     self.assertEqual(full.data, full_citation)
    #     self.assertIn(full_citation_sha512, self.manager.object_cache['citation'])
    #
    #     # Different objects created
    #     self.assertNotEqual(basic, full)
    #
    #     # Two ojbects in object_cache
    #     self.assertEqual(2, len(self.manager.object_cache['citation'].keys()))
    #
    #     # Reload from object cache
    #     reloaded_basic = self.manager.get_or_create_citation(**basic_citation)
    #     self.assertEqual(basic, reloaded_basic)
    #
    #     reloaded_full = self.manager.get_or_create_citation(**full_citation)
    #     self.assertEqual(full, reloaded_full)
    #
    #     # No new entries in object_cache
    #     self.assertEqual(2, len(self.manager.object_cache['citation'].keys()))
    #
    # @mock_bel_resources
    # def test_get_or_create_evidence(self, mock_get):
    #     basic_citation = {
    #         CITATION_TYPE: 'PubMed',
    #         CITATION_NAME: 'TestCitation_basic',
    #         CITATION_REFERENCE: '1234AB',
    #     }
    #     basic_citation = self.manager.get_or_create_citation(**basic_citation)
    #     evidence_txt = "Yes, all the information is true!"
    #     evidence_data = {
    #         CITATION: basic_citation.data,
    #         EVIDENCE: evidence_txt
    #     }
    #
    #     evidence_hash = hashlib.sha512(json.dumps(evidence_data, sort_keys=True).encode('utf-8')).hexdigest()
    #
    #     # Create
    #     evidence = self.manager.get_or_create_evidence(basic_citation, evidence_txt)
    #     self.assertIsInstance(evidence, models.Evidence)
    #     self.assertEqual(evidence.data, evidence_data)
    #
    #     self.assertIn(evidence_hash, self.manager.object_cache['evidence'])
    #     self.assertEqual(1, len(self.manager.object_cache['evidence']))
    #
    #     # Objects cached?
    #     reloaded_evidence = self.manager.get_or_create_evidence(basic_citation, evidence_txt)
    #     self.assertEqual(evidence, reloaded_evidence)
    #
    # @mock_bel_resources
    # def test_get_or_create_property(self, mock_get):
    #     activity = {
    #         'data': {
    #             SUBJECT: {
    #                 EFFECT: {
    #                     NAME: 'pep',
    #                     NAMESPACE: BEL_DEFAULT_NAMESPACE
    #                 },
    #                 MODIFIER: ACTIVITY
    #             }
    #         },
    #         'participant': SUBJECT
    #     }
    #     translocation = {
    #         'data': {
    #             SUBJECT: {
    #                 EFFECT: {
    #                     FROM_LOC: {
    #                         NAME: 'host intracellular organelle',
    #                         NAMESPACE: GOCC_KEYWORD
    #                     },
    #                     TO_LOC: {
    #                         NAME: 'host outer membrane',
    #                         NAMESPACE: GOCC_KEYWORD
    #                     },
    #                 },
    #                 MODIFIER: TRANSLOCATION
    #             }
    #         },
    #         'participant': SUBJECT
    #     }
    #     location = {
    #         'data': {
    #             SUBJECT: {
    #                 LOCATION: {
    #                     NAMESPACE: GOCC_KEYWORD,
    #                     NAME: 'Herring body'
    #                 }
    #             }
    #         },
    #         'participant': SUBJECT
    #     }
    #     degradation = {
    #         'data': {
    #             SUBJECT: {
    #                 MODIFIER: DEGRADATION
    #             }
    #         },
    #         'participant': SUBJECT
    #     }
    #     edge_data = self.simple_graph.edge[('Protein', 'HGNC', 'AKT1')][('Protein', 'HGNC', 'EGFR')][0]
    #
    #     activity_hash = hashlib.sha512(json.dumps({
    #         'participant': SUBJECT,
    #         'modifier': ACTIVITY,
    #         'effectNamespace': BEL_DEFAULT_NAMESPACE,
    #         'effectName': 'pep'
    #     }, sort_keys=True).encode('utf-8')).hexdigest()
    #     translocation_from_hash = hashlib.sha512(json.dumps({
    #         'participant': SUBJECT,
    #         'modifier': TRANSLOCATION,
    #         'relativeKey': FROM_LOC,
    #         'namespaceEntry': self.manager.namespace_object_cache[GOCC_LATEST]['host intracellular organelle']
    #     }, sort_keys=True).encode('utf-8')).hexdigest()
    #     translocation_to_hash = hashlib.sha512(json.dumps({
    #         'participant': SUBJECT,
    #         'modifier': TRANSLOCATION,
    #         'relativeKey': TO_LOC,
    #         'namespaceEntry': self.manager.namespace_object_cache[GOCC_LATEST]['host outer membrane']
    #     }, sort_keys=True).encode('utf-8')).hexdigest()
    #     location_hash = hashlib.sha512(json.dumps({
    #         'participant': SUBJECT,
    #         'modifier': LOCATION,
    #         'namespaceEntry': self.manager.namespace_object_cache[GOCC_LATEST]['Herring body']
    #     }, sort_keys=True).encode('utf-8')).hexdigest()
    #     degradation_hash = hashlib.sha512(json.dumps({
    #         'participant': SUBJECT,
    #         'modifier': DEGRADATION
    #     }, sort_keys=True).encode('utf-8')).hexdigest()
    #
    #     # Create
    #     edge_data.update(activity['data'])
    #     activity_ls = self.manager.get_or_create_property(self.simple_graph, edge_data)
    #     self.assertIsInstance(activity_ls, list)
    #     self.assertIsInstance(activity_ls[0], models.Property)
    #     self.assertEqual(activity_ls[0].data, activity)
    #
    #     # Activity was stored with hash in object cache
    #     self.assertIn(activity_hash, self.manager.object_cache['property'])
    #     self.assertEqual(1, len(self.manager.object_cache['property'].keys()))
    #
    #     reloaded_activity_ls = self.manager.get_or_create_property(self.simple_graph, edge_data)
    #     self.assertEqual(activity_ls, reloaded_activity_ls)
    #
    #     # No new activity object was created
    #     self.assertEqual(1, len(self.manager.object_cache['property'].keys()))
    #
    #     # Create
    #     edge_data.update(location['data'])
    #     location_ls = self.manager.get_or_create_property(self.simple_graph, edge_data)
    #     self.assertEqual(location_ls[0].data, location)
    #
    #     self.assertIn(location_hash, self.manager.object_cache['property'])
    #     self.assertEqual(2, len(self.manager.object_cache['property'].keys()))
    #
    #     # Get
    #     reloaded_location_ls = self.manager.get_or_create_property(self.simple_graph, edge_data)
    #     self.assertEqual(location_ls, reloaded_location_ls)
    #
    #     # No second location property object was created
    #     self.assertEqual(2, len(self.manager.object_cache['property'].keys()))
    #
    #     # Create
    #     edge_data.update(degradation['data'])
    #     degradation_ls = self.manager.get_or_create_property(self.simple_graph, edge_data)
    #     self.assertEqual(degradation_ls[0].data, degradation)
    #
    #     self.assertIn(degradation_hash, self.manager.object_cache['property'])
    #     self.assertEqual(3, len(self.manager.object_cache['property'].keys()))
    #
    #     # Get
    #     reloaded_degradation_ls = self.manager.get_or_create_property(self.simple_graph, edge_data)
    #     self.assertEqual(degradation_ls, reloaded_degradation_ls)
    #
    #     # No second degradation property object was created
    #     self.assertEqual(3, len(self.manager.object_cache['property'].keys()))
    #
    #     # Create
    #     edge_data.update(translocation['data'])
    #     translocation_ls = self.manager.get_or_create_property(self.simple_graph, edge_data)
    #     # self.assertEqual(translocation_ls[0].data, translocation)
    #
    #     # 2 translocation objects addaed
    #     self.assertEqual(5, len(self.manager.object_cache['property'].keys()))
    #     self.assertIn(translocation_from_hash, self.manager.object_cache['property'])
    #     self.assertIn(translocation_to_hash, self.manager.object_cache['property'])
    #
    # @mock_bel_resources
    # def test_get_or_create_edge(self, mock_get):
    #
    #     edge_data = self.simple_graph.edge[('Protein', 'HGNC', 'AKT1')][('Protein', 'HGNC', 'EGFR')]
    #     source_node = self.manager.get_or_create_node(self.simple_graph, ('Protein', 'HGNC', 'AKT1'))
    #     target_node = self.manager.get_or_create_node(self.simple_graph, ('Protein', 'HGNC', 'EGFR'))
    #     citation = self.manager.get_or_create_citation(**edge_data[0][CITATION])
    #     evidence = self.manager.get_or_create_evidence(citation, edge_data[0][EVIDENCE])
    #     properties = self.manager.get_or_create_property(self.simple_graph, edge_data[0])
    #     annotations = []
    #     basic_edge = {
    #         'graph_key': 0,
    #         'source': source_node,
    #         'target': target_node,
    #         'evidence': evidence,
    #         'bel': 'p(HGNC:AKT1) -> p(HGNC:EGFR)',
    #         'relation': edge_data[0][RELATION],
    #         'properties': properties,
    #         'annotations': annotations,
    #         'blob': pickle.dumps(edge_data[0])
    #     }
    #     source_data = source_node.data
    #     target_data = target_node.data
    #     database_data = {
    #         'source': {
    #             'node': (source_data['key'], source_data['data']),
    #             'key': source_data['key']
    #         },
    #         'target': {
    #             'node': (target_data['key'], target_data['data']),
    #             'key': target_data['key']
    #         },
    #         'data': {
    #             RELATION: edge_data[0][RELATION],
    #             CITATION: citation.data,
    #             EVIDENCE: edge_data[0][EVIDENCE],
    #             ANNOTATIONS: {}
    #         },
    #         'key': 0
    #     }
    #
    #     edge_hash = hashlib.sha512(json.dumps({
    #         'graphIdentifier': 0,
    #         'source': source_node,
    #         'target': target_node,
    #         'evidence': evidence,
    #         'bel': 'p(HGNC:AKT1) -> p(HGNC:EGFR)',
    #         'relation': edge_data[0][RELATION],
    #         'annotations': annotations,
    #         'properties': properties
    #     }, sort_keys=True).encode('utf-8')).hexdigest()
    #
    #     # Create
    #     edge = self.manager.get_or_create_edge(**basic_edge)
    #     self.assertIsInstance(edge, models.Edge)
    #     self.assertEqual(edge.data, database_data)
    #
    #     self.assertIn(edge_hash, self.manager.object_cache['edge'])
    #
    #     # Get
    #     reloaded_edge = self.manager.get_or_create_edge(**basic_edge)
    #     self.assertEqual(edge.data, reloaded_edge.data)
    #     self.assertEqual(edge, reloaded_edge)
    #
    #     self.assertEqual(1, len(self.manager.object_cache['edge'].keys()))
    #
    # @mock_bel_resources
    # def test_get_or_create_author(self, mock_get):
    #     author_name = "Jackson M"
    #
    #     # Create
    #     author = self.manager.get_or_create_author(author_name)
    #     self.assertIsInstance(author, models.Author)
    #     self.assertEqual(author.name, author_name)
    #
    #     self.assertIn(author_name, self.manager.object_cache['author'])
    #
    #     # Get
    #     reloaded_author = self.manager.get_or_create_author(author_name)
    #     self.assertEqual(author.name, reloaded_author.name)
    #     self.assertEqual(author, reloaded_author)
    #
    #     self.assertEqual(1, len(self.manager.object_cache['author'].keys()))
    #
    # @mock_bel_resources
    # def test_get_or_create_modification(self, mock_get):
    #     # self.manager.ensure_graph_definitions(self.simple_graph, cache_objects=True)
    #     node_data = self.simple_graph.node[(PROTEIN, 'HGNC', 'FADD')]
    #     fusion_missing = {
    #         FUSION: {
    #             PARTNER_3P: {
    #                 NAMESPACE: 'HGNC',
    #                 NAME: 'AKT1',
    #             },
    #             RANGE_3P: {
    #                 FUSION_MISSING: '?',
    #             },
    #             PARTNER_5P: {
    #                 NAMESPACE: 'HGNC',
    #                 NAME: 'EGFR'
    #             },
    #             RANGE_5P: {
    #                 FUSION_MISSING: '?',
    #             }
    #         }
    #     }
    #     fusion_full = {
    #         FUSION: {
    #             PARTNER_3P: {
    #                 NAMESPACE: 'HGNC',
    #                 NAME: 'AKT1',
    #             },
    #             RANGE_3P: {
    #                 FUSION_REFERENCE: 'A',
    #                 FUSION_START: 'START_1',
    #                 FUSION_STOP: 'STOP_1',
    #             },
    #             PARTNER_5P: {
    #                 NAMESPACE: 'HGNC',
    #                 NAME: 'EGFR'
    #             },
    #             RANGE_5P: {
    #                 FUSION_REFERENCE: 'E',
    #                 FUSION_START: 'START_2',
    #                 FUSION_STOP: 'STOP_2',
    #             }
    #         }
    #     }
    #     hgvs = {
    #         KIND: HGVS,
    #         IDENTIFIER: 'hgvs_ident'
    #     }
    #     fragment_missing = {
    #         KIND: FRAGMENT,
    #         FRAGMENT_MISSING: '?',
    #     }
    #     fragment_full = {
    #         KIND: FRAGMENT,
    #         FRAGMENT_START: 'START_FRAG',
    #         FRAGMENT_STOP: 'STOP_FRAG'
    #     }
    #     gmod = {
    #         KIND: GMOD,
    #         IDENTIFIER: {
    #             NAMESPACE: 'test_NS',
    #             NAME: 'test_GMOD'
    #         }
    #     }
    #     pmod_simple = {
    #         KIND: PMOD,
    #         IDENTIFIER: {
    #             NAMESPACE: 'test_NS',
    #             NAME: 'test_PMOD'
    #         }
    #     }
    #     pmod_full = {
    #         KIND: PMOD,
    #         IDENTIFIER: {
    #             NAMESPACE: 'test_NS',
    #             NAME: 'test_PMOD_2'
    #         },
    #         PMOD_CODE: 'Tst',
    #         PMOD_POSITION: 12,
    #     }
    #
    #     hgnc_url = self.simple_graph.namespace_url['HGNC']
    #     AKT1_object = self.manager.namespace_object_cache[hgnc_url]['AKT1']
    #     EGFR_object = self.manager.namespace_object_cache[hgnc_url]['EGFR']
    #
    #     fusion_missing_hash = hashlib.sha512(json.dumps({
    #         'modType': FUSION,
    #         'p3Partner': AKT1_object,
    #         'p5Partner': EGFR_object,
    #         'p3Missing': '?',
    #         'p5Missing': '?',
    #     }, sort_keys=True).encode('utf-8')).hexdigest()
    #     fusion_full_hash = hashlib.sha512(json.dumps({
    #         'modType': FUSION,
    #         'p3Partner': AKT1_object,
    #         'p5Partner': EGFR_object,
    #         'p3Reference': 'A',
    #         'p3Start': 'START_1',
    #         'p3Stop': 'STOP_1',
    #         'p5Reference': 'E',
    #         'p5Start': 'START_2',
    #         'p5Stop': 'STOP_2'
    #     }, sort_keys=True).encode('utf-8')).hexdigest()
    #     hgvs_hash = hashlib.sha512(json.dumps({
    #         'modType': HGVS,
    #         'variantString': 'hgvs_ident'
    #     }, sort_keys=True).encode('utf-8')).hexdigest()
    #     fragment_missing_hash = hashlib.sha512(json.dumps({
    #         'modType': FRAGMENT,
    #         'p3Missing': '?'
    #     }, sort_keys=True).encode('utf-8')).hexdigest()
    #     fragment_full_hash = hashlib.sha512(json.dumps({
    #         'modType': FRAGMENT,
    #         'p3Start': 'START_FRAG',
    #         'p3Stop': 'STOP_FRAG'
    #     }, sort_keys=True).encode('utf-8')).hexdigest()
    #     gmod_hash = hashlib.sha512(json.dumps({
    #         'modType': GMOD,
    #         'modNamespace': 'test_NS',
    #         'modName': 'test_GMOD'
    #     }, sort_keys=True).encode('utf-8')).hexdigest()
    #     pmod_simple_hash = hashlib.sha512(json.dumps({
    #         'modType': PMOD,
    #         'modNamespace': 'test_NS',
    #         'modName': 'test_PMOD',
    #         'aminoA': None,
    #         'position': None
    #     }, sort_keys=True).encode('utf-8')).hexdigest()
    #     pmod_full_hash = hashlib.sha512(json.dumps({
    #         'modType': PMOD,
    #         'modNamespace': 'test_NS',
    #         'modName': 'test_PMOD_2',
    #         'aminoA': 'Tst',
    #         'position': 12
    #     }, sort_keys=True).encode('utf-8')).hexdigest()
    #
    #     # Create
    #     node_data.update(fusion_missing)
    #     fusion_missing_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
    #     self.assertIsInstance(fusion_missing_ls, list)
    #     self.assertIsInstance(fusion_missing_ls[0], models.Modification)
    #     self.assertEqual(fusion_missing[FUSION], fusion_missing_ls[0].data['mod_data'])
    #
    #     self.assertIn(fusion_missing_hash, self.manager.object_cache['modification'])
    #
    #     # Get
    #     reloaded_fusion_missing_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
    #     self.assertEqual(fusion_missing_ls, reloaded_fusion_missing_ls)
    #
    #     # Create
    #     node_data.update(fusion_full)
    #     fusion_full_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
    #     self.assertIsInstance(fusion_full_ls, list)
    #     self.assertIsInstance(fusion_full_ls[0], models.Modification)
    #     self.assertEqual(fusion_full[FUSION], fusion_full_ls[0].data['mod_data'])
    #
    #     self.assertIn(fusion_full_hash, self.manager.object_cache['modification'])
    #
    #     # Get
    #     reloaded_fusion_full_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
    #     self.assertEqual(fusion_full_ls, reloaded_fusion_full_ls)
    #
    #     del node_data[FUSION]
    #
    #     # Create
    #     node_data[VARIANTS] = [hgvs]
    #     hgvs_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
    #     self.assertEqual(hgvs, hgvs_ls[0].data['mod_data'])
    #
    #     self.assertIn(hgvs_hash, self.manager.object_cache['modification'])
    #
    #     # Get
    #     reloaded_hgvs_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
    #     self.assertEqual(hgvs_ls, reloaded_hgvs_ls)
    #
    #     # Create
    #     node_data[VARIANTS] = [fragment_missing]
    #     fragment_missing_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
    #     self.assertEqual(fragment_missing, fragment_missing_ls[0].data['mod_data'])
    #
    #     self.assertIn(fragment_missing_hash, self.manager.object_cache['modification'])
    #
    #     # Get
    #     reloaded_fragment_missing_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
    #     self.assertEqual(fragment_missing_ls, reloaded_fragment_missing_ls)
    #
    #     # Create
    #     node_data[VARIANTS] = [fragment_full]
    #     fragment_full_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
    #     self.assertEqual(fragment_full, fragment_full_ls[0].data['mod_data'])
    #
    #     self.assertIn(fragment_full_hash, self.manager.object_cache['modification'])
    #
    #     # Get
    #     reloaded_fragment_full_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
    #     self.assertEqual(fragment_full_ls, reloaded_fragment_full_ls)
    #
    #     # Create
    #     node_data[VARIANTS] = [gmod]
    #     gmod_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
    #     self.assertEqual(gmod, gmod_ls[0].data['mod_data'])
    #
    #     self.assertIn(gmod_hash, self.manager.object_cache['modification'])
    #
    #     # Get
    #     reloaded_gmod_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
    #     self.assertEqual(gmod_ls, reloaded_gmod_ls)
    #
    #     # Create
    #     node_data[VARIANTS] = [pmod_simple]
    #     pmod_simple_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
    #     self.assertEqual(pmod_simple, pmod_simple_ls[0].data['mod_data'])
    #
    #     self.assertIn(pmod_simple_hash, self.manager.object_cache['modification'])
    #
    #     # Get
    #     reloaded_pmod_simple_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
    #     self.assertEqual(pmod_simple_ls, reloaded_pmod_simple_ls)
    #
    #     # Create
    #     node_data[VARIANTS] = [pmod_full]
    #     pmod_full_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
    #     self.assertEqual(pmod_full, pmod_full_ls[0].data['mod_data'])
    #
    #     self.assertIn(pmod_full_hash, self.manager.object_cache['modification'])
    #
    #     # Get
    #     reloaded_pmod_full_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
    #     self.assertEqual(pmod_full_ls, reloaded_pmod_full_ls)
    #
    #     # Every modification was added only once to the object cache
    #     self.assertEqual(8, len(self.manager.object_cache['modification'].keys()))

    # ============================================================

    @mock_bel_resources
    def test_query_node(self, mock_get):
        akt1_dict = {
            'key': (PROTEIN, 'HGNC', 'AKT1'),
            'data': {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            },
            'bel': 'p(HGNC:AKT1)'
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

        protein_list = self.manager.get_node(type=PROTEIN)
        self.assertEqual(len(protein_list), 4)

    @mock_bel_resources
    def test_query_edge(self, mock_get):
        fadd_casp = {
            'source': {
                'node': ((PROTEIN, 'HGNC', 'FADD'), {
                    FUNCTION: PROTEIN,
                    NAMESPACE: 'HGNC',
                    NAME: 'FADD'
                }),
                'key': (PROTEIN, 'HGNC', 'FADD')
            },
            'target': {
                'node': ((PROTEIN, 'HGNC', 'CASP8'), {
                    FUNCTION: PROTEIN,
                    NAMESPACE: 'HGNC',
                    NAME: 'CASP8'
                }),
                'key': (PROTEIN, 'HGNC', 'CASP8')
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
