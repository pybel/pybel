# -*- coding: utf-8 -*-

"""Tests for manager functions handling BEL networks."""

from __future__ import unicode_literals

import logging
import time
import unittest
from collections import Counter, defaultdict

import sqlalchemy.exc
from sqlalchemy import not_

from pybel import BELGraph, from_database, from_path, to_database
from pybel.constants import (
    ABUNDANCE, BEL_DEFAULT_NAMESPACE, BIOPROCESS, CITATION, CITATION_AUTHORS, CITATION_DATE, CITATION_NAME,
    CITATION_REFERENCE, CITATION_TYPE, CITATION_TYPE_OTHER, CITATION_TYPE_PUBMED, COMPLEX, COMPOSITE, DECREASES,
    EVIDENCE, FUNCTION, FUSION, FUSION_MISSING, FUSION_REFERENCE, FUSION_START, FUSION_STOP, GENE,
    HAS_COMPONENT, HAS_PRODUCT, HAS_REACTANT, HGVS, IDENTIFIER, INCREASES, KIND, LOCATION, MEMBERS,
    METADATA_DESCRIPTION, METADATA_NAME, METADATA_VERSION, NAME, NAMESPACE, PARTNER_3P, PARTNER_5P, PATHOLOGY, PRODUCTS,
    PROTEIN, RANGE_3P, RANGE_5P, REACTANTS, REACTION, RELATION, VARIANTS, unqualified_edge_code,
)
from pybel.dsl import (
    activity, complex_abundance, degradation, entity, fragment, gene, gmod, pmod, protein, protein_fusion, reaction,
    secretion, translocation,
)
from pybel.dsl.namespaces import chebi, hgnc
from pybel.manager import models
from pybel.manager.models import Author, Evidence
from pybel.testing.cases import FleetingTemporaryCacheMixin, TemporaryCacheClsMixin, TemporaryCacheMixin
from pybel.testing.constants import test_bel_simple, test_bel_thorough
from pybel.testing.mocks import mock_bel_resources
from pybel.testing.utils import make_dummy_annotations, make_dummy_namespaces, n
from pybel.utils import hash_citation, hash_evidence, hash_node
from tests import constants
from tests.constants import (
    BelReconstitutionMixin, expected_test_simple_metadata, expected_test_thorough_metadata, test_citation_dict,
    test_evidence_text,
)

log = logging.getLogger(__name__)


def protein_tuple(name):
    return PROTEIN, 'HGNC', name


def protein_pair(name):
    return protein_tuple(name), hgnc(name=name)


fos = fos_tuple, fos_data = protein_pair('FOS')
jun = jun_tuple, jun_data = protein_pair('JUN')

ap1_complex_tuple = COMPLEX, fos_tuple, jun_tuple
ap1_complex_data = complex_abundance([fos_data, jun_data])

egfr_tuple, egfr_data = protein_pair('EGFR')
egfr_dimer = COMPLEX, egfr_tuple, egfr_tuple
egfr_dimer_data = complex_abundance([egfr_data, egfr_data])

yfg_tuple, yfg_data = protein_pair('YFG')

e2f4 = e2f4_tuple, e2f4_data = protein_pair('E2F4')

bound_ap1_e2f4_tuple = COMPLEX, ap1_complex_tuple, e2f4_tuple
bound_ap1_e2f4_data = complex_abundance([ap1_complex_data, e2f4_data])

superoxide = chebi('superoxide')
hydrogen_peroxide = chebi('hydrogen peroxide')
oxygen = chebi('oxygen')

reaction_1 = reaction(reactants=[superoxide], products=[hydrogen_peroxide, oxygen])

has_component_code = unqualified_edge_code[HAS_COMPONENT]
has_reactant_code = unqualified_edge_code[HAS_REACTANT]
has_product_code = unqualified_edge_code[HAS_PRODUCT]


class TestNetworkCache(BelReconstitutionMixin, FleetingTemporaryCacheMixin):

    def test_get_network_missing(self):
        network = self.manager.get_most_recent_network_by_name('This network is not here')
        self.assertIsNone(network)

    def test_get_graph_missing(self):
        network = self.manager.get_graph_by_most_recent('This network is not here')
        self.assertIsNone(network)

    @mock_bel_resources
    def test_reload(self, mock_get):
        """Tests that a graph with the same name and version can't be added twice"""
        self.graph = from_path(test_bel_thorough, manager=self.manager, allow_nested=True)
        self.assertEqual('1.0.0', self.graph.version)

        to_database(self.graph, manager=self.manager, store_parts=False)

        time.sleep(1)

        self.assertEqual(1, self.manager.count_networks())

        networks = self.manager.list_networks()
        self.assertEqual(1, len(networks))

        network = networks[0]

        self.assertEqual(expected_test_thorough_metadata[METADATA_NAME], network.name)
        self.assertEqual(expected_test_thorough_metadata[METADATA_VERSION], network.version)
        self.assertEqual(expected_test_thorough_metadata[METADATA_DESCRIPTION], network.description)

        reconstituted = self.manager.get_graph_by_name_version(
            expected_test_thorough_metadata[METADATA_NAME],
            expected_test_thorough_metadata[METADATA_VERSION]
        )
        self.bel_thorough_reconstituted(reconstituted)

        # Test that the graph can't be added a second time
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.manager.insert_graph(self.graph, store_parts=False)

        self.manager.session.rollback()

        time.sleep(1)

        self.assertEqual(1, self.manager.count_networks())

        graph_copy = self.graph.copy()
        graph_copy.document[METADATA_VERSION] = '1.0.1'
        network_copy = self.manager.insert_graph(graph_copy, store_parts=False)

        time.sleep(1)  # Sleep so the first graph always definitely goes in first

        self.assertTrue(self.manager.has_name_version(graph_copy.name, graph_copy.version))
        self.assertFalse(self.manager.has_name_version('wrong name', '0.1.2'))
        self.assertFalse(self.manager.has_name_version(graph_copy.name, '0.1.2'))
        self.assertFalse(self.manager.has_name_version('wrong name', graph_copy.version))

        self.assertEqual(2, self.manager.count_networks())

        self.assertEqual('1.0.1', self.manager.get_most_recent_network_by_name(self.graph.name).version)

        query_ids = {-1, network.id, network_copy.id}
        query_networks_result = self.manager.get_networks_by_ids(query_ids)
        self.assertEqual(2, len(query_networks_result))
        self.assertEqual({network.id, network_copy.id}, {network.id for network in query_networks_result})

        expected_versions = {'1.0.1', self.graph.version}
        self.assertEqual(expected_versions, set(self.manager.get_network_versions(self.graph.name)))

        exact_name_version = from_database(self.graph.name, self.graph.version, manager=self.manager)
        self.assertEqual(self.graph.name, exact_name_version.name)
        self.assertEqual(self.graph.version, exact_name_version.version)

        exact_name_version = from_database(self.graph.name, '1.0.1', manager=self.manager)
        self.assertEqual(self.graph.name, exact_name_version.name)
        self.assertEqual('1.0.1', exact_name_version.version)

        most_recent_version = from_database(self.graph.name, manager=self.manager)
        self.assertEqual(self.graph.name, most_recent_version.name)
        self.assertEqual('1.0.1', exact_name_version.version)

        recent_networks = list(self.manager.list_recent_networks())  # just try it to see if it fails
        self.assertIsNotNone(recent_networks)
        self.assertEqual([(network.name, '1.0.1')], [(n.name, n.version) for n in recent_networks])
        self.assertEqual('1.0.1', recent_networks[0].version)


class TestTemporaryInsertNetwork(TemporaryCacheMixin):
    @mock_bel_resources
    def test_insert_with_list_annotations(self, mock):
        """This test checks that graphs that contain list annotations, which aren't cached, can be loaded properly
        into the database."""
        graph = BELGraph(name='test', version='0.0.0')
        graph.annotation_list['TEST'] = {'a', 'b', 'c'}

        graph.add_increases(
            fos_data,
            jun_data,
            evidence=test_evidence_text,
            citation=test_citation_dict,
            annotations={'TEST': 'a'}
        )

        make_dummy_namespaces(self.manager, graph, {'HGNC': ['FOS', 'JUN']})

        self.manager.insert_graph(graph, store_parts=True)

        # TODO check that the database doesn't have anything for TEST in it


class TestQuery(TemporaryCacheMixin):
    def setUp(self):
        super(TestQuery, self).setUp()
        graph = BELGraph(name='test', version='0.0.0')
        graph.annotation_list['TEST'] = {'a', 'b', 'c'}

        graph.add_increases(
            fos_data,
            jun_data,
            evidence=test_evidence_text,
            citation=test_citation_dict,
            annotations={
                'TEST': 'a'
            }
        )

        make_dummy_namespaces(self.manager, graph, {'HGNC': ['FOS', 'JUN']})

        @mock_bel_resources
        def insert(mock):
            self.manager.insert_graph(graph, store_parts=True)

        insert()

    def test_query_node_bel_1(self):
        rv = self.manager.query_nodes(bel='p(HGNC:FOS)')
        self.assertEqual(1, len(rv))
        self.assertEqual(fos_data, rv[0].to_json())

    def test_query_node_bel_2(self):
        rv = self.manager.query_nodes(bel='p(HGNC:JUN)')
        self.assertEqual(1, len(rv))
        self.assertEqual(jun_data, rv[0].to_json())

    def test_query_node_namespace_wildcard(self):
        rv = self.manager.query_nodes(namespace='HG%')
        self.assertEqual(2, len(rv))
        self.assertTrue(any(x.to_json() == fos_data for x in rv))
        self.assertTrue(any(x.to_json() == jun_data for x in rv))

    def test_query_node_name_wildcard(self):
        rv = self.manager.query_nodes(name='%J%')
        self.assertEqual(1, len(rv), 1)
        self.assertEqual(jun_data, rv[0].to_json())

    def test_query_node_type(self):
        rv = self.manager.query_nodes(type=PROTEIN)
        self.assertEqual(2, len(rv))

    def test_query_node_type_missing(self):
        rv = self.manager.query_nodes(type=ABUNDANCE)
        self.assertEqual(0, len(rv))

    def test_query_edge_by_bel(self):
        rv = self.manager.query_edges(bel="p(HGNC:FOS) increases p(HGNC:JUN)")
        self.assertEqual(1, len(rv))

    def test_query_edge_by_relation_wildcard(self):
        # relation like, data
        increased_list = self.manager.query_edges(relation='increase%')
        self.assertEqual(1, len(increased_list))
        # self.assertIn(..., increased_list)

    def test_query_edge_by_evidence_wildcard(self):
        # evidence like, data
        evidence_list = self.manager.search_edges_with_evidence(evidence='%3%')
        self.assertEqual(len(evidence_list), 0)

        evidence_list = self.manager.search_edges_with_evidence(evidence='%Twit%')
        self.assertEqual(len(evidence_list), 1)

    def test_query_edge_by_mixed_no_result(self):
        # no result
        empty_list = self.manager.query_edges(source='p(HGNC:FADD)', relation=DECREASES)
        self.assertEqual(len(empty_list), 0)

    def test_query_edge_by_mixed(self):
        # source, relation, data
        source_list = self.manager.query_edges(source='p(HGNC:FOS)', relation=INCREASES)
        self.assertEqual(len(source_list), 1)

    def test_query_edge_by_source_function(self):
        edges = self.manager.query_edges(source_function=PROTEIN)
        self.assertEqual(1, len(edges), msg='Wrong number of edges: {}'.format(edges))

        edges = self.manager.query_edges(source_function=BIOPROCESS)
        self.assertEqual(0, len(edges), msg='Wrong number of edges: {}'.format(edges))

    def test_query_edge_by_target_function(self):
        edges = self.manager.query_edges(target_function=PROTEIN)
        self.assertEqual(1, len(edges), msg='Wrong number of edges: {}'.format(edges))

        edges = self.manager.query_edges(target_function=PATHOLOGY)
        self.assertEqual(0, len(edges), msg='Wrong number of edges: {}'.format(edges))

    def test_query_citation(self):
        citation_1 = {
            CITATION_TYPE: CITATION_TYPE_PUBMED,
            CITATION_NAME: "That one article from last week",
            CITATION_REFERENCE: "123455",
            CITATION_DATE: "2012-01-31",
            CITATION_AUTHORS: "Example Author|Example Author2"
        }
        citation_2 = {
            CITATION_TYPE: CITATION_TYPE_PUBMED,
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

    def test_query_citation_by_type(self):
        rv = self.manager.query_citations(type=CITATION_TYPE_PUBMED)
        self.assertEqual(1, len(rv))
        self.assertTrue(rv[0].is_pubmed)
        self.assertFalse(rv[0].is_enriched)

    def test_query_citaiton_by_reference(self):
        rv = self.manager.query_citations(type=CITATION_TYPE_PUBMED, reference=test_citation_dict[CITATION_REFERENCE])
        self.assertEqual(1, len(rv))
        self.assertTrue(rv[0].is_pubmed)
        self.assertFalse(rv[0].is_enriched)
        self.assertEqual(test_citation_dict, rv[0].to_json())

    @unittest.skip
    def test_query_by_author_wildcard(self):
        author_list = self.manager.query_citations(author="Example%")
        self.assertEqual(len(author_list), 1)

    @unittest.skip
    def test_query_by_author(self):
        author_dict_list = self.manager.query_citations(author="Example Author")
        # self.assertIn(..., author_dict_list)

    @unittest.skip
    def test_query_by_author_list(self):
        author_dict_list2 = self.manager.query_citations(author=["Example Author", "Example Author2"])
        # self.assertIn(..., author_dict_list2)

    @unittest.skip
    def test_query_by_name(self):
        # type, name, data
        name_dict_list = self.manager.query_citations(type=CITATION_TYPE_PUBMED,
                                                      name="That other article from last week")
        self.assertEqual(len(name_dict_list), 1)
        # self.assertIn(..., name_dict_list)

    @unittest.skip
    def test_query_by_name_wildcard(self):
        # type, name like, data
        name_dict_list2 = self.manager.query_citations(type=CITATION_TYPE_PUBMED, name="%article from%")
        self.assertEqual(len(name_dict_list2), 2)
        # self.assertIn(..., name_dict_list2)
        # self.assertIn(..., name_dict_list2)


class TestEnsure(TemporaryCacheMixin):
    def test_get_or_create_citation(self):
        reference = '1234AB'
        citation_dict = {
            CITATION_TYPE: CITATION_TYPE_PUBMED,
            CITATION_NAME: 'TestCitation_basic',
            CITATION_REFERENCE: reference,
        }

        citation_hash = hash_citation(citation_dict[CITATION_TYPE], citation_dict[CITATION_REFERENCE])

        citation = self.manager.get_or_create_citation(**citation_dict)
        self.manager.session.commit()

        self.assertIsInstance(citation, models.Citation)
        self.assertEqual(citation_dict, citation.to_json())

        citation_reloaded_from_reference = self.manager.get_citation_by_pmid(reference)
        self.assertIsNotNone(citation_reloaded_from_reference)
        self.assertEqual(citation_dict, citation_reloaded_from_reference.to_json())

        citation_reloaded_from_dict = self.manager.get_or_create_citation(**citation_dict)
        self.assertIsNotNone(citation_reloaded_from_dict)
        self.assertEqual(citation_dict, citation_reloaded_from_dict.to_json())

        citation_reloaded_from_hash = self.manager.get_citation_by_hash(citation_hash)
        self.assertIsNotNone(citation_reloaded_from_hash)
        self.assertEqual(citation_dict, citation_reloaded_from_hash.to_json())

    def test_get_or_create_citation_full(self):
        reference = 'CD5678'
        citation_dict = {
            CITATION_TYPE: CITATION_TYPE_OTHER,
            CITATION_NAME: 'TestCitation_full',
            CITATION_REFERENCE: reference,
            CITATION_DATE: '2017-04-11',
            CITATION_AUTHORS: sorted(['Jackson M', 'Lajoie J'])
        }

        citation_hash = hash_citation(citation_dict[CITATION_TYPE], citation_dict[CITATION_REFERENCE])

        citation = self.manager.get_or_create_citation(**citation_dict)
        self.manager.session.commit()

        self.assertIsInstance(citation, models.Citation)
        self.assertEqual(citation_dict, citation.to_json())

        citation_reloaded_from_reference = self.manager.get_citation_by_reference(CITATION_TYPE_OTHER, reference)
        self.assertIsNotNone(citation_reloaded_from_reference)
        self.assertEqual(citation_dict, citation_reloaded_from_reference.to_json())

        citation_reloaded_from_dict = self.manager.get_or_create_citation(**citation_dict)
        self.assertIsNotNone(citation_reloaded_from_dict)
        self.assertEqual(citation_dict, citation_reloaded_from_dict.to_json())

        citation_reloaded_from_hash = self.manager.get_citation_by_hash(citation_hash)
        self.assertIsNotNone(citation_reloaded_from_hash)
        self.assertEqual(citation_dict, citation_reloaded_from_hash.to_json())

        full_citation_basic = {
            CITATION_TYPE: 'Other',
            CITATION_NAME: 'TestCitation_full',
            CITATION_REFERENCE: 'CD5678'
        }

        citation_truncated = self.manager.get_or_create_citation(**full_citation_basic)
        self.assertIsNotNone(citation_truncated)
        self.assertEqual(citation_dict, citation_truncated.to_json())

    def test_get_or_create_evidence(self):
        basic_citation = self.manager.get_or_create_citation(**test_citation_dict)
        utf8_test_evidence = "Yes, all the information is true! This contains a unicode alpha: α"
        evidence_hash = hash_evidence(
            text=utf8_test_evidence,
            type=CITATION_TYPE_PUBMED,
            reference=test_citation_dict[CITATION_REFERENCE]
        )

        evidence = self.manager.get_or_create_evidence(basic_citation, utf8_test_evidence)
        self.assertIsInstance(evidence, Evidence)
        self.assertIn(evidence_hash, self.manager.object_cache_evidence)

        # Objects cached?
        reloaded_evidence = self.manager.get_or_create_evidence(basic_citation, utf8_test_evidence)
        self.assertEqual(evidence, reloaded_evidence)

    def test_get_or_create_author(self):
        """This tests getting or creating author with unicode characters"""
        author_name = "Jαckson M"

        # Create
        author = self.manager.get_or_create_author(author_name)
        self.manager.session.commit()

        self.assertIsInstance(author, Author)
        self.assertEqual(author.name, author_name)

        author_from_name = self.manager.get_author_by_name(author_name)
        self.assertIsNotNone(author_from_name)
        self.assertEqual(author_name, author_from_name.name)

        # Get
        author_from_get = self.manager.get_or_create_author(author_name)
        self.assertEqual(author.name, author_from_get.name)
        self.assertEqual(author, author_from_get)


class TestEdgeStore(TemporaryCacheClsMixin, BelReconstitutionMixin):
    """Tests that the cache can be queried."""

    @classmethod
    def setUpClass(cls):
        """Set up the class with a BEL graph and its corresponding SQLAlchemy model."""
        super(TestEdgeStore, cls).setUpClass()

        with mock_bel_resources:
            cls.graph = from_path(test_bel_simple, manager=cls.manager, allow_nested=True)
            cls.network = cls.manager.insert_graph(cls.graph, store_parts=True)

    def test_citations(self):
        citations = self.manager.session.query(models.Citation).all()
        self.assertEqual(2, len(citations), msg='Citations: {}'.format(citations))

        citation_references = {'123455', '123456'}
        self.assertEqual(citation_references, {
            citation.reference
            for citation in citations
        })

    def test_authors(self):
        authors = {'Example Author', 'Example Author2'}
        self.assertEqual(authors, {
            author.name
            for author in self.manager.session.query(models.Author).all()
        })

    def test_evidences(self):
        evidences = self.manager.session.query(models.Evidence).all()
        self.assertEqual(3, len(evidences))

        evidences_texts = {'Evidence 1 w extra notes', 'Evidence 2', 'Evidence 3'}
        self.assertEqual(evidences_texts, {
            evidence.text
            for evidence in evidences
        })

    def test_nodes(self):
        nodes = self.manager.session.query(models.Node).all()
        self.assertEqual(4, len(nodes))

    def test_edges(self):
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

        self.assertEqual(
            {network_edge_association.edge_id for network_edge_association in network_edge_associations},
            {edge.id for edge in edges}
        )

    def test_reconstitute(self):
        g2 = self.manager.get_graph_by_name_version(
            expected_test_simple_metadata[METADATA_NAME],
            expected_test_simple_metadata[METADATA_VERSION]
        )
        self.bel_simple_reconstituted(g2)


class TestAddNodeFromData(unittest.TestCase):
    def setUp(self):
        self.graph = BELGraph()

    def test_simple(self):
        node_tuple = PROTEIN, 'HGNC', 'YFG'
        node_data = yfg_data
        self.graph.add_node_from_data(node_data)
        self.assertIn(node_tuple, self.graph)
        self.assertEqual(1, self.graph.number_of_nodes())

    def test_single_variant(self):
        node_tuple = GENE, 'HGNC', 'AKT1', (HGVS, 'p.Phe508del')
        node_data = {
            FUNCTION: GENE,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1',
            VARIANTS: [
                {
                    KIND: HGVS,
                    IDENTIFIER: 'p.Phe508del'
                }
            ]
        }

        node_parent_tuple = GENE, 'HGNC', 'AKT1'
        node_parent_data = {
            FUNCTION: GENE,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1'
        }

        self.graph.add_node_from_data(node_data)
        self.assertIn(node_tuple, self.graph)
        self.assertEqual(node_data, self.graph.node[node_tuple])
        self.assertIn(node_parent_tuple, self.graph)
        self.assertEqual(node_parent_data, self.graph.node[node_parent_tuple])
        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertEqual(1, self.graph.number_of_edges())

    def test_multiple_variants(self):
        node_tuple = GENE, 'HGNC', 'AKT1', (HGVS, 'p.Phe508del'), (HGVS, 'p.Phe509del')
        node_data = {
            FUNCTION: GENE,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1',
            VARIANTS: [
                {
                    KIND: HGVS,
                    IDENTIFIER: 'p.Phe508del'
                }, {
                    KIND: HGVS,
                    IDENTIFIER: 'p.Phe509del'
                }
            ]
        }

        node_parent_tuple = GENE, 'HGNC', 'AKT1'
        node_parent_data = {
            FUNCTION: GENE,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1'
        }

        self.graph.add_node_from_data(node_data)
        self.assertIn(node_tuple, self.graph)
        self.assertEqual(node_data, self.graph.node[node_tuple])
        self.assertIn(node_parent_tuple, self.graph)
        self.assertEqual(node_parent_data, self.graph.node[node_parent_tuple])
        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertEqual(1, self.graph.number_of_edges())

    def test_fusion(self):
        node_tuple = GENE, ('HGNC', 'TMPRSS2'), ('c', 1, 79), ('HGNC', 'ERG'), ('c', 312, 5034)
        node_data = {
            FUNCTION: GENE,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'TMPRSS2'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'ERG'},
                RANGE_5P: {
                    FUSION_REFERENCE: 'c',
                    FUSION_START: 1,
                    FUSION_STOP: 79

                },
                RANGE_3P: {
                    FUSION_REFERENCE: 'c',
                    FUSION_START: 312,
                    FUSION_STOP: 5034
                }
            }
        }

        self.graph.add_node_from_data(node_data)
        self.assertIn(node_tuple, self.graph)
        self.assertEqual(node_data, self.graph.node[node_tuple])
        self.assertEqual(1, self.graph.number_of_nodes())
        self.assertEqual(0, self.graph.number_of_edges())

    def test_composite(self):
        il23 = COMPLEX, 'GOCC', 'interleukin-23 complex'
        il6 = PROTEIN, 'HGNC', 'IL6'
        node_tuple = COMPOSITE, il23, il6
        node_data = {
            FUNCTION: COMPOSITE,
            MEMBERS: [
                {
                    FUNCTION: COMPLEX,
                    NAMESPACE: 'GOCC',
                    NAME: 'interleukin-23 complex'
                },
                {
                    FUNCTION: PROTEIN,
                    NAMESPACE: 'HGNC',
                    NAME: 'IL6'
                }
            ]
        }

        self.graph.add_node_from_data(node_data)
        self.assertIn(node_tuple, self.graph)
        self.assertEqual(3, self.graph.number_of_nodes())
        self.assertIn(il6, self.graph)
        self.assertIn(il23, self.graph)
        self.assertEqual(2, self.graph.number_of_edges())
        self.assertIn(il6, self.graph.edge[node_tuple])
        self.assertIn(has_component_code, self.graph.edge[node_tuple][il6])
        self.assertEqual(HAS_COMPONENT, self.graph.edge[node_tuple][il6][has_component_code][RELATION])
        self.assertIn(il23, self.graph.edge[node_tuple])
        self.assertIn(has_component_code, self.graph.edge[node_tuple][il23])
        self.assertEqual(HAS_COMPONENT, self.graph.edge[node_tuple][il23][has_component_code][RELATION])

    def test_reaction(self):
        superoxide_node = ABUNDANCE, 'CHEBI', 'superoxide'
        hydrogen_peroxide = ABUNDANCE, 'CHEBI', 'hydrogen peroxide'
        oxygen_node = ABUNDANCE, 'CHEBI', 'oxygen'

        node_tuple = REACTION, (superoxide_node,), (hydrogen_peroxide, oxygen_node)
        node_data = {
            FUNCTION: REACTION,
            REACTANTS: [
                {
                    FUNCTION: ABUNDANCE,
                    NAMESPACE: 'CHEBI',
                    NAME: 'superoxide'
                }
            ],
            PRODUCTS: [
                {
                    FUNCTION: ABUNDANCE,
                    NAMESPACE: 'CHEBI',
                    NAME: 'hydrogen peroxide'
                },
                {

                    FUNCTION: ABUNDANCE,
                    NAMESPACE: 'CHEBI',
                    NAME: 'oxygen'
                }
            ]
        }
        self.graph.add_node_from_data(node_data)
        self.assertIn(node_tuple, self.graph)
        self.assertEqual(4, self.graph.number_of_nodes())
        self.assertIn(superoxide_node, self.graph)
        self.assertIn(hydrogen_peroxide, self.graph)
        self.assertIn(oxygen_node, self.graph)
        self.assertEqual(3, self.graph.number_of_edges())
        self.assertIn(superoxide_node, self.graph.edge[node_tuple])
        self.assertIn(has_reactant_code, self.graph.edge[node_tuple][superoxide_node])
        self.assertEqual(HAS_REACTANT, self.graph.edge[node_tuple][superoxide_node][has_reactant_code][RELATION])
        self.assertIn(hydrogen_peroxide, self.graph.edge[node_tuple])
        self.assertIn(has_product_code, self.graph.edge[node_tuple][hydrogen_peroxide])
        self.assertEqual(HAS_PRODUCT, self.graph.edge[node_tuple][hydrogen_peroxide][has_product_code][RELATION])
        self.assertIn(oxygen_node, self.graph.edge[node_tuple])
        self.assertIn(has_product_code, self.graph.edge[node_tuple][oxygen_node])
        self.assertEqual(HAS_PRODUCT, self.graph.edge[node_tuple][oxygen_node][has_product_code][RELATION])

    def test_complex(self):
        has_component_code = unqualified_edge_code[HAS_COMPONENT]
        node_tuple = ap1_complex_tuple
        node_data = {
            FUNCTION: COMPLEX,
            MEMBERS: [
                fos_data,
                jun_data
            ]
        }
        self.graph.add_node_from_data(node_data)
        self.assertIn(node_tuple, self.graph)
        self.assertEqual(3, self.graph.number_of_nodes())
        self.assertIn(fos_tuple, self.graph)
        self.assertIn(jun_tuple, self.graph)
        self.assertEqual(2, self.graph.number_of_edges())
        self.assertIn(fos_tuple, self.graph.edge[node_tuple])
        self.assertIn(has_component_code, self.graph.edge[node_tuple][fos_tuple])
        self.assertEqual(HAS_COMPONENT, self.graph.edge[node_tuple][fos_tuple][has_component_code][RELATION])
        self.assertIn(jun_tuple, self.graph.edge[node_tuple])
        self.assertIn(has_component_code, self.graph.edge[node_tuple][jun_tuple])
        self.assertEqual(HAS_COMPONENT, self.graph.edge[node_tuple][jun_tuple][has_component_code][RELATION])

    def test_dimer_complex(self):
        """Tests what happens if a BEL statement complex(p(X), p(X)) is added"""
        self.graph.add_node_from_data(egfr_dimer_data)

        self.assertIn(egfr_tuple, self.graph)
        self.assertIn(egfr_dimer, self.graph)
        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertEqual(1, self.graph.number_of_edges())

        self.assertIn(egfr_tuple, self.graph.edge[egfr_dimer])
        self.assertIn(has_component_code, self.graph.edge[egfr_dimer][egfr_tuple])
        self.assertEqual(HAS_COMPONENT, self.graph.edge[egfr_dimer][egfr_tuple][has_component_code][RELATION])

    def test_nested_complex(self):
        """Checks what happens if a theoretical BEL statement `complex(p(X), complex(p(Y), p(Z)))` is added"""
        self.graph.add_node_from_data(bound_ap1_e2f4_data)
        self.assertIn(bound_ap1_e2f4_tuple, self.graph)
        self.assertEqual(5, self.graph.number_of_nodes())
        self.assertIn(fos_tuple, self.graph)
        self.assertIn(jun_tuple, self.graph)
        self.assertIn(e2f4_tuple, self.graph)
        self.assertIn(ap1_complex_tuple, self.graph)
        self.assertEqual(4, self.graph.number_of_edges())
        self.assertIn(fos_tuple, self.graph.edge[ap1_complex_tuple])
        self.assertIn(has_component_code, self.graph.edge[ap1_complex_tuple][fos_tuple])
        self.assertEqual(HAS_COMPONENT, self.graph.edge[ap1_complex_tuple][fos_tuple][has_component_code][RELATION])
        self.assertIn(jun_tuple, self.graph.edge[ap1_complex_tuple])
        self.assertIn(has_component_code, self.graph.edge[ap1_complex_tuple][jun_tuple])
        self.assertEqual(HAS_COMPONENT, self.graph.edge[ap1_complex_tuple][jun_tuple][has_component_code][RELATION])

        self.assertIn(has_component_code, self.graph.edge[bound_ap1_e2f4_tuple][ap1_complex_tuple])
        self.assertEqual(HAS_COMPONENT,
                         self.graph.edge[bound_ap1_e2f4_tuple][ap1_complex_tuple][has_component_code][RELATION])

        self.assertIn(has_component_code, self.graph.edge[bound_ap1_e2f4_tuple][e2f4_tuple])
        self.assertEqual(HAS_COMPONENT, self.graph.edge[bound_ap1_e2f4_tuple][e2f4_tuple][has_component_code][RELATION])


class TestReconstituteNodeTuples(TemporaryCacheMixin):
    """Tests the ability to go from PyBEL to relational database"""

    def help_reconstitute(self, node_data, namespace_dict, number_nodes, number_edges):
        """Helps test the round-trip conversion from PyBEL data dictionary to node model, then back to PyBEL node
        data dictionary and PyBEL node tuple.

        :param dict node_data: PyBEL node data dictionary
        """
        graph = BELGraph(name='test', version='0.0.0')
        make_dummy_namespaces(self.manager, graph, namespace_dict)

        node_tuple = graph.add_node_from_data(node_data)

        self.manager.insert_graph(graph, store_parts=True)
        self.assertEqual(number_nodes, self.manager.count_nodes())
        self.assertEqual(number_edges, self.manager.count_edges())

        node = self.manager.get_or_create_node(graph, node_tuple)
        self.manager.session.commit()

        self.assertEqual(node_data, node.to_json())
        self.assertEqual(node_tuple, node.to_tuple())

        self.assertEqual(node, self.manager.get_node_by_tuple(node_tuple))

        node_hash = hash_node(node_tuple)
        self.assertEqual(node_tuple, self.manager.get_node_tuple_by_hash(node_hash))

    @mock_bel_resources
    def test_simple(self, mock):
        namespaces = {'HGNC': ['YFG']}
        self.help_reconstitute(yfg_data, namespaces, 1, 0)

    @mock_bel_resources
    def test_hgvs(self, mock):
        node_data = {
            FUNCTION: GENE,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1',
            VARIANTS: [
                {
                    KIND: HGVS,
                    IDENTIFIER: 'p.Phe508del'
                }
            ]
        }
        namespaces = {'HGNC': ['AKT1']}
        self.help_reconstitute(node_data, namespaces, 2, 1)

    @mock_bel_resources
    def test_fragment_unspecified(self, mock):
        dummy_namespace = n()
        dummy_name = n()
        node_data = protein(namespace=dummy_namespace, name=dummy_name, variants=[fragment()])
        namespaces = {dummy_namespace: [dummy_name]}
        self.help_reconstitute(node_data, namespaces, 2, 1)

    @mock_bel_resources
    def test_fragment_specified(self, mock):
        dummy_namespace = n()
        dummy_name = n()
        node_data = protein(namespace=dummy_namespace, name=dummy_name, variants=[fragment(start=5, stop=8)])
        namespaces = {dummy_namespace: [dummy_name]}
        self.help_reconstitute(node_data, namespaces, 2, 1)

    @mock_bel_resources
    def test_fragment_specified_start_only(self, mock):
        dummy_namespace = n()
        dummy_name = n()
        node_data = protein(namespace=dummy_namespace, name=dummy_name, variants=[fragment(start=5, stop='*')])
        namespaces = {dummy_namespace: [dummy_name]}
        self.help_reconstitute(node_data, namespaces, 2, 1)

    @mock_bel_resources
    def test_fragment_specified_end_only(self, mock):
        dummy_namespace = n()
        dummy_name = n()
        node_data = protein(namespace=dummy_namespace, name=dummy_name, variants=[fragment(start='*', stop=1000)])
        namespaces = {dummy_namespace: [dummy_name]}
        self.help_reconstitute(node_data, namespaces, 2, 1)

    @mock_bel_resources
    def test_gmod_custom(self, mock):
        """Tests a gene modification that uses a non-default namespace"""
        dummy_namespace = n()
        dummy_name = n()
        dummy_mod_namespace = n()
        dummy_mod_name = n()

        node_data = gene(namespace=dummy_namespace, name=dummy_name,
                         variants=[gmod(name=dummy_mod_name, namespace=dummy_mod_namespace)])
        namespaces = {dummy_namespace: [dummy_name], dummy_mod_namespace: [dummy_mod_name]}
        self.help_reconstitute(node_data, namespaces, 2, 1)

    @mock_bel_resources
    def test_gmod_default(self, mock):
        """Tests a gene modification that uses the BEL default namespace"""
        dummy_namespace = n()
        dummy_name = n()

        node_data = gene(namespace=dummy_namespace, name=dummy_name, variants=[gmod('Me')])
        namespaces = {dummy_namespace: [dummy_name]}
        self.help_reconstitute(node_data, namespaces, 2, 1)

    @mock_bel_resources
    def test_pmod_default_simple(self, mock):
        dummy_namespace = n()
        dummy_name = n()

        node_data = protein(namespace=dummy_namespace, name=dummy_name, variants=[pmod('Me')])
        namespaces = {dummy_namespace: [dummy_name]}
        self.help_reconstitute(node_data, namespaces, 2, 1)

    @mock_bel_resources
    def test_pmod_custom_simple(self, mock):
        dummy_namespace = n()
        dummy_name = n()
        dummy_mod_namespace = n()
        dummy_mod_name = n()

        node_data = protein(namespace=dummy_namespace, name=dummy_name,
                            variants=[pmod(name=dummy_mod_name, namespace=dummy_mod_namespace)])
        namespaces = {dummy_namespace: [dummy_name], dummy_mod_namespace: [dummy_mod_name]}
        self.help_reconstitute(node_data, namespaces, 2, 1)

    @mock_bel_resources
    def test_pmod_default_with_residue(self, mock):
        dummy_namespace = n()
        dummy_name = n()

        node_data = protein(namespace=dummy_namespace, name=dummy_name, variants=[pmod('Me', code='Ser')])
        namespaces = {dummy_namespace: [dummy_name]}
        self.help_reconstitute(node_data, namespaces, 2, 1)

    @mock_bel_resources
    def test_pmod_custom_with_residue(self, mock):
        dummy_namespace = n()
        dummy_name = n()
        dummy_mod_namespace = n()
        dummy_mod_name = n()

        node_data = protein(namespace=dummy_namespace, name=dummy_name,
                            variants=[pmod(name=dummy_mod_name, namespace=dummy_mod_namespace, code='Ser')])
        namespaces = {dummy_namespace: [dummy_name], dummy_mod_namespace: [dummy_mod_name]}
        self.help_reconstitute(node_data, namespaces, 2, 1)

    @mock_bel_resources
    def test_pmod_default_full(self, mock):
        dummy_namespace = n()
        dummy_name = n()

        node_data = protein(namespace=dummy_namespace, name=dummy_name, variants=[pmod('Me', code='Ser', position=5)])
        namespaces = {dummy_namespace: [dummy_name]}
        self.help_reconstitute(node_data, namespaces, 2, 1)

    @mock_bel_resources
    def test_pmod_custom_full(self, mock):
        dummy_namespace = n()
        dummy_name = n()
        dummy_mod_namespace = n()
        dummy_mod_name = n()

        node_data = protein(namespace=dummy_namespace, name=dummy_name,
                            variants=[pmod(name=dummy_mod_name, namespace=dummy_mod_namespace, code='Ser', position=5)])
        namespaces = {dummy_namespace: [dummy_name], dummy_mod_namespace: [dummy_mod_name]}
        self.help_reconstitute(node_data, namespaces, 2, 1)

    @mock_bel_resources
    def test_multiple_variants(self, mock):
        node_data = {
            FUNCTION: GENE,
            NAMESPACE: 'HGNC',
            NAME: 'AKT1',
            VARIANTS: [
                {
                    KIND: HGVS,
                    IDENTIFIER: 'p.Phe508del'
                }, {
                    KIND: HGVS,
                    IDENTIFIER: 'p.Phe509del'
                }
            ]
        }
        namespaces = {'HGNC': ['AKT1']}
        self.help_reconstitute(node_data, namespaces, 2, 1)

    @mock_bel_resources
    def test_fusion_specified(self, mock):
        node_data = {
            FUNCTION: GENE,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'TMPRSS2'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'ERG'},
                RANGE_5P: {
                    FUSION_REFERENCE: 'c',
                    FUSION_START: 1,
                    FUSION_STOP: 79

                },
                RANGE_3P: {
                    FUSION_REFERENCE: 'c',
                    FUSION_START: 312,
                    FUSION_STOP: 5034
                }
            }
        }
        namespaces = {'HGNC': ['TMPRSS2', 'ERG']}
        self.help_reconstitute(node_data, namespaces, 1, 0)

    @mock_bel_resources
    def test_fusion_unspecified(self, mock):
        node_data = {
            FUNCTION: GENE,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'TMPRSS2'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'ERG'},
                RANGE_5P: {FUSION_MISSING: '?'},
                RANGE_3P: {FUSION_MISSING: '?'}
            }
        }
        namespaces = {'HGNC': ['TMPRSS2', 'ERG']}
        self.help_reconstitute(node_data, namespaces, 1, 0)

    @mock_bel_resources
    def test_composite(self, mock):
        node_data = {
            FUNCTION: COMPOSITE,
            MEMBERS: [
                {
                    FUNCTION: COMPLEX,
                    NAMESPACE: 'GOCC',
                    NAME: 'interleukin-23 complex'
                },
                {
                    FUNCTION: PROTEIN,
                    NAMESPACE: 'HGNC',
                    NAME: 'IL6'
                }
            ]
        }
        namespaces = {'GOCC': ['interleukin-23 complex'], 'HGNC': ['IL6']}
        self.help_reconstitute(node_data, namespaces, 3, 2)

    @mock_bel_resources
    def test_reaction(self, mock):
        node_data = {
            FUNCTION: REACTION,
            REACTANTS: [
                {
                    FUNCTION: ABUNDANCE,
                    NAMESPACE: 'CHEBI',
                    NAME: 'superoxide'
                }
            ],
            PRODUCTS: [
                {
                    FUNCTION: ABUNDANCE,
                    NAMESPACE: 'CHEBI',
                    NAME: 'hydrogen peroxide'
                },
                {
                    FUNCTION: ABUNDANCE,
                    NAMESPACE: 'CHEBI',
                    NAME: 'oxygen'
                }
            ]
        }
        namespaces = {'CHEBI': ['superoxide', 'hydrogen peroxide', 'oxygen']}
        self.help_reconstitute(node_data, namespaces, 4, 3)

    @mock_bel_resources
    def test_complex(self, mock):
        namespaces = {'HGNC': ['FOS', 'JUN']}
        self.help_reconstitute(ap1_complex_data, namespaces, 3, 2)

    @mock_bel_resources
    def test_nested_complex(self, mock):
        namespaces = {'HGNC': ['FOS', 'JUN', 'E2F4']}
        self.help_reconstitute(bound_ap1_e2f4_data, namespaces, 5, 4)


class TestReconstituteEdges(TemporaryCacheMixin):
    """This class tests that edges with varying properties can be added and extracted losslessly"""

    def setUp(self):
        """Creates a unit test with a manager and graph"""
        super(TestReconstituteEdges, self).setUp()
        self.graph = BELGraph(
            name=n(),
            version=n()
        )

    def help_insert_graph(self):
        # FIXME get d better by getting ALL names from graph

        d = defaultdict(set)

        d = {
            'HGNC': ['F2', 'EDN1'], 'GOCC': ['intracellular', 'cell surface', 'extracellular space']
        }

        make_dummy_namespaces(self.manager, self.graph, d)

        self.manager.insert_graph(self.graph, store_parts=True)

    @mock_bel_resources
    def test_translocation_default(self, mock):
        """This test checks that a translocation gets in the database properly"""
        self.graph.add_increases(
            protein(name='F2', namespace='HGNC'),
            protein(name='EDN1', namespace='HGNC'),
            evidence='In endothelial cells, ET-1 secretion is detectable under basal conditions, whereas thrombin induces its secretion.',
            citation='10473669',
            subject_modifier=secretion()
        )

        make_dummy_namespaces(self.manager, self.graph, {
            'HGNC': ['F2', 'EDN1'], 'GOCC': ['intracellular', 'cell surface', 'extracellular space']
        })

        network = self.manager.insert_graph(self.graph, store_parts=True)
        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        edge = network.edges.first()
        self.assertEqual(2, edge.properties.count())

    @mock_bel_resources
    def test_subject_translocation_custom_to_loc(self, mock):
        self.graph.add_increases(
            protein(name='F2', namespace='HGNC'),
            protein(name='EDN1', namespace='HGNC'),
            evidence='In endothelial cells, ET-1 secretion is detectable under basal conditions, whereas thrombin induces its secretion.',
            citation='10473669',
            subject_modifier=translocation(
                from_loc=entity(namespace='TEST', name='A'),
                to_loc=entity(namespace='GOCC', name='extracellular space'),
            )
        )

        make_dummy_namespaces(self.manager, self.graph, {
            'HGNC': ['F2', 'EDN1'],
            'GOCC': ['extracellular space'], 'TEST': ['A']
        })

        network = self.manager.insert_graph(self.graph, store_parts=True)
        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        edge = network.edges.first()
        self.assertEqual(2, edge.properties.count())

    @mock_bel_resources
    def test_subject_activity_default(self, mock):
        p1_name = n()
        p2_name = n()

        self.graph.add_increases(
            protein(name=p1_name, namespace='HGNC'),
            protein(name=p2_name, namespace='HGNC'),
            evidence=n(),
            citation=n(),
            subject_modifier=activity('kin')
        )

        make_dummy_namespaces(self.manager, self.graph, {
            'HGNC': [p1_name, p2_name],
        })

        network = self.manager.insert_graph(self.graph, store_parts=True)
        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        kin_list = self.manager.session.query(models.NamespaceEntry).filter(models.NamespaceEntry.name == 'kin').all()
        self.assertEqual(1, len(kin_list))

        kin = list(kin_list)[0]
        self.assertEqual('kin', kin.name)

        effects = self.manager.session.query(models.Property).join(models.NamespaceEntry).filter(
            models.Property.effect == kin)
        self.assertEqual(1, effects.count())

    @mock_bel_resources
    def test_subject_activity_custom(self, mock):
        p1_name = n()
        p2_name = n()
        dummy_activity_namespace = n()
        dummy_activity_name = n()

        self.graph.add_increases(
            protein(name=p1_name, namespace='HGNC'),
            protein(name=p2_name, namespace='HGNC'),
            evidence=n(),
            citation=n(),
            subject_modifier=activity(name=dummy_activity_name, namespace=dummy_activity_namespace)
        )

        make_dummy_namespaces(self.manager, self.graph, {
            'HGNC': [p1_name, p2_name], dummy_activity_namespace: [dummy_activity_name]
        })

        network = self.manager.insert_graph(self.graph, store_parts=True)
        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        kin_list = self.manager.session.query(models.NamespaceEntry).filter(
            models.NamespaceEntry.name == dummy_activity_name).all()
        self.assertEqual(1, len(kin_list))

        kin = list(kin_list)[0]
        self.assertEqual(dummy_activity_name, kin.name)

        effects = self.manager.session.query(models.Property).join(models.NamespaceEntry).filter(
            models.Property.effect == kin)
        self.assertEqual(1, effects.count())

    @mock_bel_resources
    def test_object_activity_default(self, mock):
        p1_name = n()
        p2_name = n()

        self.graph.add_increases(
            protein(name=p1_name, namespace='HGNC'),
            protein(name=p2_name, namespace='HGNC'),
            evidence=n(),
            citation=n(),
            object_modifier=activity('kin')
        )

        make_dummy_namespaces(self.manager, self.graph, {
            'HGNC': [p1_name, p2_name],
        })

        network = self.manager.insert_graph(self.graph, store_parts=True)
        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        kin_list = self.manager.session.query(models.NamespaceEntry).filter(models.NamespaceEntry.name == 'kin').all()
        self.assertEqual(1, len(kin_list))

        kin = list(kin_list)[0]
        self.assertEqual('kin', kin.name)

        effects = self.manager.session.query(models.Property).join(models.NamespaceEntry).filter(
            models.Property.effect == kin)
        self.assertEqual(1, effects.count())

    @mock_bel_resources
    def test_object_activity_custom(self, mock):
        p1_name = n()
        p2_name = n()
        dummy_activity_namespace = n()
        dummy_activity_name = n()

        self.graph.add_increases(
            protein(name=p1_name, namespace='HGNC'),
            protein(name=p2_name, namespace='HGNC'),
            evidence=n(),
            citation=n(),
            object_modifier=activity(name=dummy_activity_name, namespace=dummy_activity_namespace)
        )

        make_dummy_namespaces(self.manager, self.graph, {
            'HGNC': [p1_name, p2_name], dummy_activity_namespace: [dummy_activity_name]
        })

        network = self.manager.insert_graph(self.graph, store_parts=True)
        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        kin_list = self.manager.session.query(models.NamespaceEntry).filter(
            models.NamespaceEntry.name == dummy_activity_name).all()
        self.assertEqual(1, len(kin_list))

        kin = list(kin_list)[0]
        self.assertEqual(dummy_activity_name, kin.name)

        effects = self.manager.session.query(models.Property).join(models.NamespaceEntry).filter(
            models.Property.effect == kin)
        self.assertEqual(1, effects.count())

    @mock_bel_resources
    def test_subject_degradation(self, mock):
        self.graph.add_association(
            protein(name='YFG', namespace='HGNC'),
            protein(name='YFG2', namespace='HGNC'),
            evidence=n(),
            citation=n(),
            subject_modifier=degradation(),
        )
        make_dummy_namespaces(self.manager, self.graph, {'HGNC': ['YFG', 'YFG2']})

        network = self.manager.insert_graph(self.graph, store_parts=True)

        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        edge = network.edges.first()
        self.assertEqual(1, edge.properties.count())

    @mock_bel_resources
    def test_object_degradation(self, mock):
        self.graph.add_association(
            protein(name='YFG', namespace='HGNC'),
            protein(name='YFG2', namespace='HGNC'),
            evidence=n(),
            citation=n(),
            object_modifier=degradation(),
        )
        make_dummy_namespaces(self.manager, self.graph, {'HGNC': ['YFG', 'YFG2']})

        network = self.manager.insert_graph(self.graph, store_parts=True)

        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        edge = network.edges.first()
        self.assertEqual(1, edge.properties.count())

    @mock_bel_resources
    def test_subject_location(self, mock):
        self.graph.add_association(
            protein(name='YFG', namespace='HGNC'),
            protein(name='YFG2', namespace='HGNC'),
            evidence=n(),
            citation=n(),
            subject_modifier={
                LOCATION: entity(namespace='GOCC', name='nucleus')
            },
        )
        make_dummy_namespaces(self.manager, self.graph, {'HGNC': ['YFG', 'YFG2'], 'GOCC': ['nucleus']})

        network = self.manager.insert_graph(self.graph, store_parts=True)

        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        edge = network.edges.first()
        self.assertEqual(1, edge.properties.count())

    @mock_bel_resources
    def test_mixed_1(self, mock):
        """Test mixed having location and something else."""

        self.graph.add_increases(
            protein(namespace='HGNC', name='CDC42'),
            protein(namespace='HGNC', name='PAK2'),
            evidence="""Summary: PAK proteins, a family of serine/threonine p21-activating kinases, include PAK1, PAK2,
             PAK3 and PAK4. PAK proteins are critical effectors that link Rho GTPases to cytoskeleton reorganization 
             and nuclear signaling. They serve as targets for the small GTP binding proteins Cdc42 and Rac and have 
             been implicated in a wide range of biological activities. PAK4 interacts specifically with the GTP-bound 
             form of Cdc42Hs and weakly activates the JNK family of MAP kinases. PAK4 is a mediator of filopodia 
             formation and may play a role in the reorganization of the actin cytoskeleton. Multiple alternatively 
             spliced transcript variants encoding distinct isoforms have been found for this gene.""",
            citation={CITATION_TYPE: "Online Resource", CITATION_REFERENCE: "PAK4 Hs ENTREZ Gene Summary"},
            annotations={'Species': '9606'},
            subject_modifier=activity('gtp'),
            object_modifier=activity('kin'),
        )

        make_dummy_namespaces(self.manager, self.graph, {
            'HGNC': ['CDC42', 'PAK2']
        })

        make_dummy_annotations(self.manager, self.graph, {
            'Species': ['9606']
        })

        network = self.manager.insert_graph(self.graph, store_parts=True)
        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        edge = network.edges.first()
        self.assertEqual(2, edge.properties.count())

        subject = edge.properties.filter(models.Property.is_subject).one()
        self.assertTrue(subject.is_subject)
        self.assertEqual('gtp', subject.effect.name)
        self.assertIsNotNone(subject.effect.namespace)
        self.assertEqual(BEL_DEFAULT_NAMESPACE, subject.effect.namespace.keyword)

        object = edge.properties.filter(not_(models.Property.is_subject)).one()
        self.assertFalse(object.is_subject)
        self.assertEqual('kin', object.effect.name)
        self.assertIsNotNone(object.effect.namespace)
        self.assertEqual(BEL_DEFAULT_NAMESPACE, object.effect.namespace.keyword)

    @mock_bel_resources
    def test_mixed_2(self, mock):
        """Tests both subject and object activity with location information as well."""
        self.graph.add_directly_increases(
            protein(namespace='HGNC', name='HDAC4'),
            protein(namespace='HGNC', name='MEF2A'),
            citation='10487761',
            evidence=""""In the nucleus, HDAC4 associates with the myocyte enhancer factor MEF2A. Binding of HDAC4 to 
            MEF2A results in the repression of MEF2A transcriptional activation, a function that requires the 
            deacetylase domain of HDAC4.""",
            annotations={'Species': '9606'},
            subject_modifier=activity('cat', location=entity(namespace='GOCC', name='nucleus')),
            object_modifier=activity('tscript', location=entity(namespace='GOCC', name='nucleus'))
        )

        make_dummy_namespaces(self.manager, self.graph, {
            'HGNC': ['HDAC4', 'MEF2A'],
            'GOCC': ['nucleus']
        })

        make_dummy_annotations(self.manager, self.graph, {
            'Species': ['9606']
        })

        network = self.manager.insert_graph(self.graph, store_parts=True)
        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        edge = network.edges.first()
        self.assertEqual(4, edge.properties.count())
        self.assertEqual(2, edge.properties.filter(models.Property.is_subject).count())
        self.assertEqual(2, edge.properties.filter(not_(models.Property.is_subject)).count())


class TestNoAddNode(TemporaryCacheMixin):
    """Tests scenarios where an instance of :class:`BELGraph` may contain edges that refer to uncached resources, and
    therefore should not be added to the edge store."""

    @mock_bel_resources
    def test_no_node_name(self, mock):
        """Test that a node whose namespace is in the uncached namespaces set can't be added."""
        graph = BELGraph(name='Test No Add Nodes', version='1.0.0')

        dummy_namespace = n()
        dummy_url = n()

        graph.namespace_url[dummy_namespace] = dummy_url
        graph.uncached_namespaces.add(dummy_url)

        node_data = protein(name=n(), namespace=dummy_namespace)
        graph.add_node_from_data(node_data)

        network = self.manager.insert_graph(graph)
        self.assertEqual(0, len(network.nodes.all()))

    @mock_bel_resources
    def test_no_node_fusion_3p(self, mock):
        """Test that a fusion node whose 3P partner's namespace is in the uncached namespaces set can't be added."""
        graph = BELGraph(name='Test No Add Nodes', version='1.0.0')

        dummy_namespace_name = n()
        dummy_url = n()

        graph.namespace_url[dummy_namespace_name] = dummy_url
        graph.uncached_namespaces.add(dummy_url)

        node_data = protein_fusion(
            partner_3p=protein(namespace=dummy_namespace_name, name='AKT1'),
            partner_5p=protein(namespace='HGNC', name='YFG'),
        )
        graph.add_node_from_data(node_data)

        make_dummy_namespaces(self.manager, graph, {'HGNC': ['YFG']})
        network = self.manager.insert_graph(graph)

        self.assertEqual(0, len(network.nodes.all()))

    @mock_bel_resources
    def test_no_node_fusion_5p(self, mock):
        """Test that a node whose namespace is in the uncached namespaces set can't be added."""
        dummy_namespace_name = n()

        node_data = protein_fusion(
            partner_3p=protein(namespace='HGNC', name='YFG'),
            partner_5p=protein(namespace=dummy_namespace_name, name='YFG'),
        )

        graph = BELGraph(name='Test No Add Nodes', version='1.0.0')
        dummy_url = n()
        graph.namespace_url[dummy_namespace_name] = dummy_url
        graph.uncached_namespaces.add(dummy_url)
        graph.add_node_from_data(node_data)
        make_dummy_namespaces(self.manager, graph, {'HGNC': ['YFG']})
        network = self.manager.insert_graph(graph)
        self.assertEqual(0, len(network.nodes.all()))

    @mock_bel_resources
    def test_no_protein_modification(self, mock):
        """Test that a protein node whose pmod variant is in the uncached namespaces set can't be added."""
        graph = BELGraph(name='Test No Add Nodes', version='1.0.0')

        dummy_namespace_name = n()
        dummy_url = n()

        graph.namespace_url[dummy_namespace_name] = dummy_url
        graph.uncached_namespaces.add(dummy_url)

        node_data = protein(namespace='HGNC', name='YFG', variants=[
            pmod(name='dummy', namespace=dummy_namespace_name)
        ])

        graph.add_node_from_data(node_data)

        make_dummy_namespaces(self.manager, graph, {'HGNC': ['YFG']})
        network = self.manager.insert_graph(graph)

        self.assertEqual(1, network.nodes.count())

    @mock_bel_resources
    def test_no_gene_modification(self, mock):
        """Test that a gene node whose gmod variant is in the uncached namespaces set can't be added."""
        graph = BELGraph(name='Test No Add Nodes', version='1.0.0')

        dummy_namespace_name = n()
        dummy_url = n()

        graph.namespace_url[dummy_namespace_name] = dummy_url
        graph.uncached_namespaces.add(dummy_url)

        node_data = gene(namespace='HGNC', name='YFG', variants=[
            gmod(name='dummy', namespace=dummy_namespace_name)
        ])

        graph.add_node_from_data(node_data)

        make_dummy_namespaces(self.manager, graph, {'HGNC': ['YFG']})
        network = self.manager.insert_graph(graph)

        self.assertEqual(1, network.nodes.count())

    @mock_bel_resources
    def test_no_translocation(self, mock):
        """Test that a translocation using custom namespaces doesn't get stored."""
        graph = BELGraph(name='dummy graph', version='0.0.1')

        dummy_namespace_name = n()
        dummy_namespace_url = n()

        graph.namespace_url[dummy_namespace_name] = dummy_namespace_url
        graph.uncached_namespaces.add(dummy_namespace_url)

        graph.add_association(
            protein(name='YFG', namespace='HGNC'),
            protein(name='YFG2', namespace='HGNC'),
            evidence=n(),
            citation=n(),
            subject_modifier=translocation(
                from_loc=entity(namespace=dummy_namespace_name, name='intracellular'),
                to_loc=entity(namespace='GOCC', name='extracellular space')
            ),
        )

        make_dummy_namespaces(self.manager, graph, {'HGNC': ['YFG', 'YFG2'], 'GOCC': ['extracellular space']})

        network = self.manager.insert_graph(graph, store_parts=True)

        self.assertEqual(2, network.nodes.count())
        self.assertEqual(0, network.edges.count())

    @mock_bel_resources
    def test_no_location(self, mock):
        """Test that when using a custom namespace in the location the edge doesn't get stored."""
        graph = BELGraph(name='dummy graph', version='0.0.1')
        dummy_namespace_name = n()
        dummy_url = n()
        graph.namespace_url[dummy_namespace_name] = dummy_url
        graph.uncached_namespaces.add(dummy_url)

        graph.add_association(
            protein(name='YFG', namespace='HGNC'),
            protein(name='YFG2', namespace='HGNC'),
            evidence=n(),
            citation=n(),
            subject_modifier={
                LOCATION: entity(namespace=dummy_namespace_name, name='lysozome')
            },
        )

        make_dummy_namespaces(self.manager, graph, {'HGNC': ['YFG', 'YFG2']})

        network = self.manager.insert_graph(graph, store_parts=True)

        self.assertEqual(2, network.nodes.count())
        self.assertEqual(0, network.edges.count())

    @mock_bel_resources
    def test_no_activity(self, mock):
        """Test that when an uncached custom namespace is used in the activity on an edge, the edge doesn't get
        stored."""
        graph = BELGraph(name='dummy graph', version='0.0.1')
        dummy_namespace_name = n()
        dummy_url = n()
        graph.namespace_url[dummy_namespace_name] = dummy_url
        graph.uncached_namespaces.add(dummy_url)

        graph.add_association(
            protein(name='YFG', namespace='HGNC'),
            protein(name='YFG2', namespace='HGNC'),
            evidence=n(),
            citation=n(),
            subject_modifier=activity(name='dummy', namespace=dummy_namespace_name)
        )

        make_dummy_namespaces(self.manager, graph, {'HGNC': ['YFG', 'YFG2']})

        network = self.manager.insert_graph(graph, store_parts=True)

        self.assertEqual(2, network.nodes.count())
        self.assertEqual(0, network.edges.count())

    @mock_bel_resources
    def test_regex_lookup(self, mock):  # FIXME this test needs to be put somewhere else
        """Test that regular expression nodes get love too."""
        graph = BELGraph(name='Regular Expression Test Graph', description='Help test regular expression namespaces',
                         version='1.0.0')
        dbsnp = 'dbSNP'
        DBSNP_PATTERN = 'rs[0-9]+'
        graph.namespace_pattern[dbsnp] = DBSNP_PATTERN

        rs1234 = gene(namespace=dbsnp, name='rs1234')
        rs1235 = gene(namespace=dbsnp, name='rs1235')

        rs1234_tuple = graph.add_node_from_data(rs1234)
        rs1235_tuple = graph.add_node_from_data(rs1235)

        rs1234_hash = hash_node(rs1234_tuple)
        rs1235_hash = hash_node(rs1235_tuple)

        self.manager.insert_graph(graph, store_parts=True)

        rs1234_lookup = self.manager.get_node_by_hash(rs1234_hash)
        self.assertIsNotNone(rs1234_lookup)
        self.assertEqual('Gene', rs1234_lookup.type)
        self.assertEqual('g(dbSNP:rs1234)', rs1234_lookup.bel)
        self.assertEqual(rs1234_hash, rs1234_lookup.sha512)
        self.assertIsNotNone(rs1234_lookup.namespace_entry)
        self.assertEqual('rs1234', rs1234_lookup.namespace_entry.name)
        self.assertEqual('dbSNP', rs1234_lookup.namespace_entry.namespace.keyword)
        self.assertEqual(DBSNP_PATTERN, rs1234_lookup.namespace_entry.namespace.pattern)

        rs1235_lookup = self.manager.get_node_by_hash(rs1235_hash)
        self.assertIsNotNone(rs1235_lookup)
        self.assertEqual('Gene', rs1235_lookup.type)
        self.assertEqual('g(dbSNP:rs1235)', rs1235_lookup.bel)
        self.assertEqual(rs1235_hash, rs1235_lookup.sha512)
        self.assertIsNotNone(rs1235_lookup.namespace_entry)
        self.assertEqual('rs1235', rs1235_lookup.namespace_entry.name)
        self.assertEqual('dbSNP', rs1235_lookup.namespace_entry.namespace.keyword)
        self.assertEqual(DBSNP_PATTERN, rs1235_lookup.namespace_entry.namespace.pattern)


class TestEquivalentNodes(unittest.TestCase):
    def test_direct_has_namespace(self):
        graph = BELGraph()

        n1 = graph.add_node_from_data(protein(namespace='HGNC', name='CD33', identifier='1659'))
        n2 = graph.add_node_from_data(protein(namespace='NOPE', name='NOPE', identifier='NOPE'))

        graph.add_increases(n1, n2, n(), n())

        self.assertEqual({n1}, graph.get_equivalent_nodes(n1))

        self.assertTrue(graph.node_has_namespace(n1, 'HGNC'))
        self.assertFalse(graph.node_has_namespace(n2, 'HGNC'))

    def test_indirect_has_namespace(self):
        graph = BELGraph()

        a = graph.add_node_from_data(protein(namespace='HGNC', name='CD33'))
        b = graph.add_node_from_data(protein(namespace='HGNCID', identifier='1659'))

        graph.add_equivalence(a, b)

        self.assertEqual({a, b}, graph.get_equivalent_nodes(a))
        self.assertEqual({a, b}, graph.get_equivalent_nodes(b))

        self.assertTrue(graph.node_has_namespace(a, 'HGNC'))
        self.assertTrue(graph.node_has_namespace(b, 'HGNC'))

    def test_triangle_has_namespace(self):
        graph = BELGraph()

        a = graph.add_node_from_data(protein(namespace='A', name='CD33'))
        b = graph.add_node_from_data(protein(namespace='B', identifier='1659'))
        c = graph.add_node_from_data(protein(namespace='C', identifier='1659'))
        d = graph.add_node_from_data(protein(namespace='HGNC', identifier='1659'))

        graph.add_equivalence(a, b)
        graph.add_equivalence(b, c)
        graph.add_equivalence(c, a)
        graph.add_equivalence(c, d)

        self.assertEqual({a, b, c, d}, graph.get_equivalent_nodes(a))
        self.assertEqual({a, b, c, d}, graph.get_equivalent_nodes(b))
        self.assertEqual({a, b, c, d}, graph.get_equivalent_nodes(c))
        self.assertEqual({a, b, c, d}, graph.get_equivalent_nodes(d))

        self.assertTrue(graph.node_has_namespace(a, 'HGNC'))
        self.assertTrue(graph.node_has_namespace(b, 'HGNC'))
        self.assertTrue(graph.node_has_namespace(c, 'HGNC'))
        self.assertTrue(graph.node_has_namespace(d, 'HGNC'))


if __name__ == '__main__':
    unittest.main()
