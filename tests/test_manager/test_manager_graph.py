# -*- coding: utf-8 -*-

"""Tests for manager functions handling BEL networks."""

import time
import unittest
from collections import Counter
from random import randint

from sqlalchemy import not_

from pybel import BELGraph, from_bel_script, from_database, to_database
from pybel.constants import (
    ABUNDANCE, BEL_DEFAULT_NAMESPACE, BIOPROCESS, CITATION_AUTHORS, CITATION_DATE, CITATION_DB, CITATION_IDENTIFIER,
    CITATION_JOURNAL, CITATION_TYPE_OTHER, CITATION_TYPE_PUBMED, DECREASES, HAS_PRODUCT, HAS_REACTANT, INCREASES,
    METADATA_NAME, METADATA_VERSION, MIRNA, PART_OF, PATHOLOGY, PROTEIN, RELATION, CITATION_DB_NAME
)
from pybel.dsl import (
    BaseEntity, ComplexAbundance, CompositeAbundance, EnumeratedFusionRange, Fragment, Gene, GeneFusion,
    GeneModification, Hgvs, NamedComplexAbundance, Pathology, Protein, ProteinModification, Reaction, activity,
    degradation, location, secretion, translocation,
)
from pybel.dsl.namespaces import chebi, hgnc, mirbase
from pybel.examples import ras_tloc_graph, sialic_acid_graph
from pybel.language import Entity
from pybel.manager import models
from pybel.manager.models import Author, Citation, Edge, Evidence, NamespaceEntry, Node, Property
from pybel.testing.cases import FleetingTemporaryCacheMixin, TemporaryCacheClsMixin, TemporaryCacheMixin
from pybel.testing.constants import test_bel_simple
from pybel.testing.mocks import mock_bel_resources
from pybel.testing.utils import make_dummy_annotations, make_dummy_namespaces, n
from tests.constants import (
    BelReconstitutionMixin, akt1, casp8, egfr, expected_test_simple_metadata, fadd, test_citation_dict,
    test_evidence_text,
)

fos = hgnc('FOS')
jun = hgnc('JUN')
mirna_1 = mirbase(n())
mirna_2 = mirbase(n())
pathology_1 = Pathology('DO', n())
ap1_complex = ComplexAbundance([fos, jun])

egfr_dimer = ComplexAbundance([egfr, egfr])

yfg_data = hgnc('YFG')
e2f4_data = hgnc('E2F4')
bound_ap1_e2f4 = ComplexAbundance([ap1_complex, e2f4_data])

superoxide = chebi('superoxide')
hydrogen_peroxide = chebi('hydrogen peroxide')
oxygen = chebi('oxygen')
superoxide_decomposition = Reaction(reactants=[superoxide], products=[hydrogen_peroxide, oxygen])


def assert_unqualified_edge(test_case, u: BaseEntity, v: BaseEntity, rel: str) -> None:
    """Assert there's only one edge and get the data for it"""
    test_case.assertIn(u, test_case.graph)
    test_case.assertIn(v, test_case.graph[u])
    edges = list(test_case.graph[u][v].values())
    test_case.assertEqual(1, len(edges))
    data = edges[0]
    test_case.assertEqual(rel, data[RELATION])


class TestNetworkCache(BelReconstitutionMixin, FleetingTemporaryCacheMixin):

    def test_get_network_missing(self):
        network = self.manager.get_most_recent_network_by_name('This network is not here')
        self.assertIsNone(network)

    def test_get_graph_missing(self):
        network = self.manager.get_graph_by_most_recent('This network is not here')
        self.assertIsNone(network)

    @mock_bel_resources
    def test_reload(self, mock_get):
        """Test that a graph with the same name and version can't be added twice."""
        graph = sialic_acid_graph.copy()
        self.assertEqual('1.0.0', graph.version)

        to_database(graph, manager=self.manager)
        time.sleep(1)

        self.assertEqual(1, self.manager.count_networks())

        networks = self.manager.list_networks()
        self.assertEqual(1, len(networks))

        network = networks[0]
        self.assertEqual(graph.name, network.name)
        self.assertEqual(graph.version, network.version)
        self.assertEqual(graph.description, network.description)

        reconstituted = self.manager.get_graph_by_name_version(graph.name, graph.version)

        self.assertIsInstance(reconstituted, BELGraph)
        self.assertEqual(graph.nodes(data=True), reconstituted.nodes(data=True))
        # self.bel_thorough_reconstituted(reconstituted)

        self.assertEqual(1, self.manager.count_networks())

        graph_copy = graph.copy()
        graph_copy.version = '1.0.1'
        network_copy = self.manager.insert_graph(graph_copy)

        time.sleep(1)  # Sleep so the first graph always definitely goes in first

        self.assertNotEqual(network.id, network_copy.id)

        self.assertTrue(self.manager.has_name_version(graph_copy.name, graph_copy.version))
        self.assertFalse(self.manager.has_name_version('wrong name', '0.1.2'))
        self.assertFalse(self.manager.has_name_version(graph_copy.name, '0.1.2'))
        self.assertFalse(self.manager.has_name_version('wrong name', graph_copy.version))

        self.assertEqual(2, self.manager.count_networks())

        self.assertEqual('1.0.1', self.manager.get_most_recent_network_by_name(graph.name).version)

        query_ids = {-1, network.id, network_copy.id}
        query_networks_result = self.manager.get_networks_by_ids(query_ids)
        self.assertEqual(2, len(query_networks_result))
        self.assertEqual({network.id, network_copy.id}, {network.id for network in query_networks_result})

        expected_versions = {'1.0.1', '1.0.0'}
        self.assertEqual(expected_versions, set(self.manager.get_network_versions(graph.name)))

        exact_name_version = from_database(graph.name, graph.version, manager=self.manager)
        self.assertEqual(graph.name, exact_name_version.name)
        self.assertEqual(graph.version, exact_name_version.version)

        exact_name_version = from_database(graph.name, '1.0.1', manager=self.manager)
        self.assertEqual(graph.name, exact_name_version.name)
        self.assertEqual('1.0.1', exact_name_version.version)

        most_recent_version = from_database(graph.name, manager=self.manager)
        self.assertEqual(graph.name, most_recent_version.name)
        self.assertEqual('1.0.1', exact_name_version.version)

        recent_networks = list(self.manager.list_recent_networks())  # just try it to see if it fails
        self.assertIsNotNone(recent_networks)
        self.assertEqual([(network.name, '1.0.1')], [(n.name, n.version) for n in recent_networks])
        self.assertEqual('1.0.1', recent_networks[0].version)

    @mock_bel_resources
    def test_upload_with_tloc(self, mock_get):
        """Test that the RAS translocation example graph can be uploaded."""
        make_dummy_namespaces(self.manager, ras_tloc_graph)
        to_database(ras_tloc_graph, manager=self.manager)


class TestTemporaryInsertNetwork(TemporaryCacheMixin):
    def test_insert_with_list_annotations(self):
        """This test checks that graphs that contain list annotations, which aren't cached, can be loaded properly
        into the database."""
        graph = BELGraph(name='test', version='0.0.0')
        graph.annotation_list['TEST'] = {'a', 'b', 'c'}

        graph.add_increases(
            fos,
            jun,
            evidence=test_evidence_text,
            citation=test_citation_dict,
            annotations={'TEST': 'a'}
        )

        make_dummy_namespaces(self.manager, graph)

        with mock_bel_resources:
            self.manager.insert_graph(graph)

        # TODO check that the database doesn't have anything for TEST in it


class TestTypedQuery(TemporaryCacheMixin):
    def setUp(self):
        super().setUp()

        graph = BELGraph(name='test', version='0.0.0')
        graph.annotation_list['TEST'] = {'a', 'b', 'c'}

        graph.add_positive_correlation(
            mirna_1,
            pathology_1,
            evidence=n(),
            citation=n(),
        )

        graph.add_negative_correlation(
            mirna_2,
            pathology_1,
            evidence=n(),
            citation=n(),
        )

        make_dummy_namespaces(self.manager, graph)
        make_dummy_annotations(self.manager, graph)

        with mock_bel_resources:
            self.manager.insert_graph(graph)

    def test_query_edge_source_type(self):
        rv = self.manager.query_edges(source_function=MIRNA).all()
        self.assertEqual(2, len(rv))

        rv = self.manager.query_edges(target_function=PATHOLOGY).all()
        self.assertEqual(2, len(rv))


class TestQuery(TemporaryCacheMixin):
    def setUp(self):
        super(TestQuery, self).setUp()

        graph = BELGraph(name='test', version='0.0.0')
        graph.annotation_list['TEST'] = {'a', 'b', 'c'}

        graph.add_increases(
            fos,
            jun,
            evidence=test_evidence_text,
            citation=test_citation_dict,
            annotations={
                'TEST': 'a'
            }
        )

        make_dummy_namespaces(self.manager, graph)
        make_dummy_annotations(self.manager, graph)

        with mock_bel_resources:
            self.manager.insert_graph(graph)

    def test_query_node_bel_1(self):
        rv = self.manager.query_nodes(bel='p(HGNC:FOS)').all()
        self.assertEqual(1, len(rv))
        self.assertEqual(fos, rv[0].to_json())

    def test_query_node_bel_2(self):
        rv = self.manager.query_nodes(bel='p(HGNC:JUN)').all()
        self.assertEqual(1, len(rv))
        self.assertEqual(jun, rv[0].to_json())

    def test_query_node_namespace_wildcard(self):
        rv = self.manager.query_nodes(namespace='HG%').all()
        self.assertEqual(2, len(rv))
        self.assertTrue(any(x.to_json() == fos for x in rv))
        self.assertTrue(any(x.to_json() == jun for x in rv))

    def test_query_node_name_wildcard(self):
        rv = self.manager.query_nodes(name='%J%').all()
        self.assertEqual(1, len(rv), 1)
        self.assertEqual(jun, rv[0].to_json())

    def test_query_node_type(self):
        rv = self.manager.query_nodes(type=PROTEIN).all()
        self.assertEqual(2, len(rv))

    def test_query_node_type_missing(self):
        rv = self.manager.query_nodes(type=ABUNDANCE).all()
        self.assertEqual(0, len(rv))

    def test_query_edge_by_bel(self):
        rv = self.manager.query_edges(bel="p(HGNC:FOS) increases p(HGNC:JUN)").all()
        self.assertEqual(1, len(rv))

    def test_query_edge_by_relation_wildcard(self):
        # relation like, data
        increased_list = self.manager.query_edges(relation='increase%').all()
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
        # FIXME what should this return
        empty_list = self.manager.query_edges(source='p(HGNC:FADD)', relation=DECREASES)
        self.assertEqual(len(empty_list), 0)

    def test_query_edge_by_mixed(self):
        # source, relation, data
        source_list = self.manager.query_edges(source='p(HGNC:FOS)', relation=INCREASES).all()
        self.assertEqual(len(source_list), 1)

    def test_query_edge_by_source_function(self):
        edges = self.manager.query_edges(source_function=PROTEIN).all()
        self.assertEqual(1, len(edges), msg='Wrong number of edges: {}'.format(edges))

        edges = self.manager.query_edges(source_function=BIOPROCESS).all()
        self.assertEqual(0, len(edges), msg='Wrong number of edges: {}'.format(edges))

    def test_query_edge_by_target_function(self):
        edges = self.manager.query_edges(target_function=PROTEIN).all()
        self.assertEqual(1, len(edges), msg='Wrong number of edges: {}'.format(edges))

        edges = self.manager.query_edges(target_function=PATHOLOGY).all()
        self.assertEqual(0, len(edges), msg='Wrong number of edges: {}'.format(edges))

    def test_query_citation_by_type(self):
        rv = self.manager.query_citations(db=CITATION_TYPE_PUBMED)
        self.assertEqual(1, len(rv))
        self.assertTrue(rv[0].is_pubmed)
        self.assertFalse(rv[0].is_enriched)

    def test_query_citaiton_by_reference(self):
        rv = self.manager.query_citations(db=CITATION_TYPE_PUBMED, db_id=test_citation_dict[CITATION_IDENTIFIER])
        self.assertEqual(1, len(rv))
        self.assertTrue(rv[0].is_pubmed)
        self.assertFalse(rv[0].is_enriched)
        self.assertEqual(test_citation_dict, rv[0].to_json())

    @unittest.skip
    def test_query_by_author_wildcard(self):
        author_list = self.manager.query_citations(author="Example%")
        self.assertEqual(len(author_list), 1)

    @unittest.skip
    def test_query_by_name(self):
        # type, name, data
        name_dict_list = self.manager.query_citations(
            db=CITATION_TYPE_PUBMED,
            name="That other article from last week",
        )
        self.assertEqual(len(name_dict_list), 1)
        # self.assertIn(..., name_dict_list)

    @unittest.skip
    def test_query_by_name_wildcard(self):
        # type, name like, data
        name_dict_list2 = self.manager.query_citations(db=CITATION_TYPE_PUBMED, name="%article from%")
        self.assertEqual(len(name_dict_list2), 2)
        # self.assertIn(..., name_dict_list2)
        # self.assertIn(..., name_dict_list2)


class TestEnsure(TemporaryCacheMixin):
    def test_get_or_create_citation(self):
        reference = str(randint(1, 1000000))
        citation_dict = {
            CITATION_DB: CITATION_TYPE_PUBMED,
            CITATION_IDENTIFIER: reference,
        }

        citation = self.manager.get_or_create_citation(**citation_dict)
        self.manager.session.commit()

        self.assertIsInstance(citation, Citation)
        self.assertEqual(citation_dict, citation.to_json())

        citation_reloaded_from_reference = self.manager.get_citation_by_pmid(reference)
        self.assertIsNotNone(citation_reloaded_from_reference)
        self.assertEqual(citation_dict, citation_reloaded_from_reference.to_json())

        citation_reloaded_from_dict = self.manager.get_or_create_citation(**citation_dict)
        self.assertIsNotNone(citation_reloaded_from_dict)
        self.assertEqual(citation_dict, citation_reloaded_from_dict.to_json())

        citation_reloaded_from_reference = self.manager.get_citation_by_reference(
            citation_dict[CITATION_DB], citation_dict[CITATION_IDENTIFIER],
        )
        self.assertIsNotNone(citation_reloaded_from_reference)
        self.assertEqual(citation_dict, citation_reloaded_from_reference.to_json())

    def test_get_or_create_evidence(self):
        citation_db, citation_ref = CITATION_TYPE_PUBMED, str(randint(1, 1000000))
        basic_citation = self.manager.get_or_create_citation(db=citation_db, db_id=citation_ref)
        utf8_test_evidence = u"Yes, all the information is true! This contains a unicode alpha: α"

        evidence = self.manager.get_or_create_evidence(basic_citation, utf8_test_evidence)
        self.assertIsInstance(evidence, Evidence)
        self.assertIn(evidence, self.manager.object_cache_evidence.values())

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
        super().setUpClass()

        with mock_bel_resources:
            cls.graph = from_bel_script(test_bel_simple, manager=cls.manager, disallow_nested=False)
            cls.network = cls.manager.insert_graph(cls.graph)

    def test_citations(self):
        citations = self.manager.session.query(Citation).all()
        self.assertEqual(2, len(citations), msg='Citations: {}'.format(citations))

        citation_db_ids = {'123455', '123456'}
        self.assertEqual(citation_db_ids, {
            citation.db_id
            for citation in citations
        })

    def test_evidences(self):
        evidences = self.manager.session.query(Evidence).all()
        self.assertEqual(3, len(evidences))

        evidences_texts = {'Evidence 1 w extra notes', 'Evidence 2', 'Evidence 3'}
        self.assertEqual(evidences_texts, {
            evidence.text
            for evidence in evidences
        })

    def test_nodes(self):
        nodes = self.manager.session.query(Node).all()
        self.assertEqual(4, len(nodes))

    def test_edges(self):
        edges = self.manager.session.query(Edge).all()

        x = Counter((e.source.bel, e.target.bel) for e in edges)

        d = {
            (akt1.as_bel(), egfr.as_bel()): 1,
            (egfr.as_bel(), fadd.as_bel()): 1,
            (egfr.as_bel(), casp8.as_bel()): 1,
            (fadd.as_bel(), casp8.as_bel()): 1,
            (akt1.as_bel(), casp8.as_bel()): 1,  # two way association
            (casp8.as_bel(), akt1.as_bel()): 1  # two way association
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
        self.graph.add_node_from_data(yfg_data)
        self.assertIn(yfg_data, self.graph)
        self.assertEqual(1, self.graph.number_of_nodes())

    def test_single_variant(self):
        node_data = Gene('HGNC', 'AKT1', variants=Hgvs('p.Phe508del'))
        node_parent_data = node_data.get_parent()

        self.graph.add_node_from_data(node_data)
        self.assertIn(node_data, self.graph)
        self.assertIn(node_parent_data, self.graph)
        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertEqual(1, self.graph.number_of_edges())

    def test_multiple_variants(self):
        node_data = Gene('HGNC', 'AKT1', variants=[
            Hgvs('p.Phe508del'), Hgvs('p.Phe509del')
        ])
        node_parent_data = node_data.get_parent()
        node_parent_tuple = node_parent_data

        self.graph.add_node_from_data(node_data)
        self.assertIn(node_data, self.graph)
        self.assertIn(node_parent_tuple, self.graph)
        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertEqual(1, self.graph.number_of_edges())

    def test_fusion(self):
        node_data = GeneFusion(
            partner_5p=Gene('HGNC', 'TMPRSS2'),
            partner_3p=Gene('HGNC', 'ERG'),
            range_5p=EnumeratedFusionRange('c', 1, 79),
            range_3p=EnumeratedFusionRange('c', 312, 5034)
        )
        node_data = node_data

        self.graph.add_node_from_data(node_data)
        self.assertIn(node_data, self.graph)
        self.assertEqual(1, self.graph.number_of_nodes())
        self.assertEqual(0, self.graph.number_of_edges())

    def test_composite(self):
        il23 = NamedComplexAbundance(namespace='GO', name='interleukin-23 complex')
        il6 = Protein(namespace='HGNC', name='IL6')
        node_data = CompositeAbundance([il23, il6])

        self.graph.add_node_from_data(node_data)
        self.assertIn(node_data, self.graph)
        self.assertEqual(3, self.graph.number_of_nodes())
        self.assertIn(il6, self.graph, msg='Nodes:\n'.format('\n'.join(map(str, self.graph))))
        self.assertIn(il23, self.graph)
        self.assertEqual(2, self.graph.number_of_edges())

        self.assertIn(node_data, self.graph[il6])
        edges = list(self.graph[il6][node_data].values())
        self.assertEqual(1, len(edges))
        data = edges[0]
        self.assertEqual(PART_OF, data[RELATION])

        self.assertIn(node_data, self.graph[il23])
        edges = list(self.graph[il23][node_data].values())
        self.assertEqual(1, len(edges))
        data = edges[0]
        self.assertEqual(PART_OF, data[RELATION])

    def test_reaction(self):
        self.graph.add_node_from_data(superoxide_decomposition)
        self.assertIn(superoxide_decomposition, self.graph)
        self.assertEqual(4, self.graph.number_of_nodes())
        self.assertEqual(3, self.graph.number_of_edges())

        assert_unqualified_edge(self, superoxide_decomposition, superoxide, HAS_REACTANT)
        assert_unqualified_edge(self, superoxide_decomposition, hydrogen_peroxide, HAS_PRODUCT)
        assert_unqualified_edge(self, superoxide_decomposition, oxygen, HAS_PRODUCT)

    def test_complex(self):
        node = ComplexAbundance(members=[fos, jun])

        self.graph.add_node_from_data(node)
        self.assertIn(node, self.graph)
        self.assertEqual(3, self.graph.number_of_nodes())
        self.assertEqual(2, self.graph.number_of_edges())

        assert_unqualified_edge(self, fos, node, PART_OF)
        assert_unqualified_edge(self, jun, node, PART_OF)

    def test_dimer_complex(self):
        """Tests what happens if a BEL statement complex(p(X), p(X)) is added"""
        self.graph.add_node_from_data(egfr_dimer)

        self.assertIn(egfr, self.graph)
        self.assertIn(egfr_dimer, self.graph)
        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertEqual(1, self.graph.number_of_edges())

        assert_unqualified_edge(self, egfr, egfr_dimer, PART_OF)

    def test_nested_complex(self):
        """Checks what happens if a theoretical BEL statement `complex(p(X), complex(p(Y), p(Z)))` is added"""
        self.graph.add_node_from_data(bound_ap1_e2f4)
        self.assertIn(bound_ap1_e2f4, self.graph)
        self.assertEqual(5, self.graph.number_of_nodes())
        self.assertIn(fos, self.graph)
        self.assertIn(jun, self.graph)
        self.assertIn(e2f4_data, self.graph)
        self.assertIn(ap1_complex, self.graph)
        self.assertEqual(4, self.graph.number_of_edges())

        assert_unqualified_edge(self, fos, ap1_complex, PART_OF)
        assert_unqualified_edge(self, jun, ap1_complex, PART_OF)
        assert_unqualified_edge(self, ap1_complex, bound_ap1_e2f4, PART_OF)
        assert_unqualified_edge(self, e2f4_data, bound_ap1_e2f4, PART_OF)


class TestReconstituteNodeTuples(TemporaryCacheMixin):
    """Tests the ability to go from PyBEL to relational database"""

    def _help_reconstitute(self, node: BaseEntity, number_nodes: int, number_edges: int):
        """Help test the round-trip conversion from PyBEL data dictionary to node model."""
        self.assertIsInstance(node, BaseEntity)

        graph = BELGraph(name='test', version='0.0.0')
        graph.add_node_from_data(node)

        make_dummy_namespaces(self.manager, graph)

        self.manager.insert_graph(graph)
        self.assertEqual(number_nodes, self.manager.count_nodes())
        self.assertEqual(number_edges, self.manager.count_edges())

        node_model = self.manager.get_or_create_node(graph, node)
        self.assertEqual(node.md5, node_model.md5)
        self.manager.session.commit()

        self.assertEqual(node, node_model.to_json())
        self.assertEqual(node, self.manager.get_dsl_by_hash(node.md5))

    @mock_bel_resources
    def test_simple(self, mock):
        self._help_reconstitute(yfg_data, 1, 0)

    @mock_bel_resources
    def test_Hgvs(self, mock):
        node_data = Gene(namespace='HGNC', name='AKT1', variants=Hgvs('p.Phe508del'))
        self._help_reconstitute(node_data, 2, 1)

    @mock_bel_resources
    def test_fragment_unspecified(self, mock):
        dummy_namespace = n()
        dummy_name = n()
        node_data = Protein(namespace=dummy_namespace, name=dummy_name, variants=[Fragment()])
        self._help_reconstitute(node_data, 2, 1)

    @mock_bel_resources
    def test_fragment_specified(self, mock):
        dummy_namespace = n()
        dummy_name = n()
        node_data = Protein(namespace=dummy_namespace, name=dummy_name, variants=[Fragment(start=5, stop=8)])
        self._help_reconstitute(node_data, 2, 1)

    @mock_bel_resources
    def test_fragment_specified_start_only(self, mock):
        dummy_namespace = n()
        dummy_name = n()
        node_data = Protein(namespace=dummy_namespace, name=dummy_name, variants=[Fragment(start=5, stop='*')])
        self._help_reconstitute(node_data, 2, 1)

    @mock_bel_resources
    def test_fragment_specified_end_only(self, mock):
        dummy_namespace = n()
        dummy_name = n()
        node_data = Protein(namespace=dummy_namespace, name=dummy_name, variants=[Fragment(start='*', stop=1000)])
        self._help_reconstitute(node_data, 2, 1)

    @mock_bel_resources
    def test_gmod_custom(self, mock):
        """Tests a gene modification that uses a non-default namespace"""
        dummy_namespace = 'HGNC'
        dummy_name = 'AKT1'
        dummy_mod_namespace = 'GO'
        dummy_mod_name = 'DNA Methylation'

        node_data = Gene(namespace=dummy_namespace, name=dummy_name,
                         variants=[GeneModification(name=dummy_mod_name, namespace=dummy_mod_namespace)])
        self._help_reconstitute(node_data, 2, 1)

    @mock_bel_resources
    def test_gmod_default(self, mock):
        """Test a gene modification that uses the BEL default namespace."""
        dummy_namespace = n()
        dummy_name = n()

        node_data = Gene(namespace=dummy_namespace, name=dummy_name, variants=[GeneModification('Me')])
        self._help_reconstitute(node_data, 2, 1)

    @mock_bel_resources
    def test_pmod_default_simple(self, mock):
        dummy_namespace = n()
        dummy_name = n()

        node_data = Protein(namespace=dummy_namespace, name=dummy_name, variants=[ProteinModification('Me')])
        self._help_reconstitute(node_data, 2, 1)

    @mock_bel_resources
    def test_pmod_custom_simple(self, mock):
        dummy_namespace = 'HGNC'
        dummy_name = 'AKT1'
        dummy_mod_namespace = 'GO'
        dummy_mod_name = 'Protein phosphorylation'

        node_data = Protein(namespace=dummy_namespace, name=dummy_name,
                            variants=[ProteinModification(name=dummy_mod_name, namespace=dummy_mod_namespace)])
        self._help_reconstitute(node_data, 2, 1)

    @mock_bel_resources
    def test_pmod_default_with_residue(self, mock):
        dummy_namespace = n()
        dummy_name = n()

        node_data = Protein(namespace=dummy_namespace, name=dummy_name,
                            variants=[ProteinModification('Me', code='Ser')])
        self._help_reconstitute(node_data, 2, 1)

    @mock_bel_resources
    def test_pmod_custom_with_residue(self, mock):
        dummy_namespace = 'HGNC'
        dummy_name = 'AKT1'
        dummy_mod_namespace = 'GO'
        dummy_mod_name = 'Protein phosphorylation'

        node_data = Protein(
            namespace=dummy_namespace,
            name=dummy_name,
            variants=[ProteinModification(name=dummy_mod_name, namespace=dummy_mod_namespace, code='Ser')]
        )
        self._help_reconstitute(node_data, 2, 1)

    @mock_bel_resources
    def test_pmod_default_full(self, mock):
        dummy_namespace = n()
        dummy_name = n()

        node_data = Protein(namespace=dummy_namespace, name=dummy_name,
                            variants=[ProteinModification('Me', code='Ser', position=5)])
        self._help_reconstitute(node_data, 2, 1)

    @mock_bel_resources
    def test_pmod_custom_full(self, mock):
        dummy_namespace = 'HGNC'
        dummy_name = 'AKT1'
        dummy_mod_namespace = 'GO'
        dummy_mod_name = 'Protein phosphorylation'

        node_data = Protein(
            namespace=dummy_namespace,
            name=dummy_name,
            variants=[ProteinModification(name=dummy_mod_name, namespace=dummy_mod_namespace, code='Ser', position=5)]
        )
        self._help_reconstitute(node_data, 2, 1)

    @mock_bel_resources
    def test_multiple_variants(self, mock):
        node_data = Gene(namespace='HGNC', name='AKT1', variants=[
            Hgvs('p.Phe508del'),
            Hgvs('p.Phe509del')
        ])
        self._help_reconstitute(node_data, 2, 1)

    @mock_bel_resources
    def test_fusion_specified(self, mock):
        node_data = GeneFusion(
            Gene('HGNC', 'TMPRSS2'),
            Gene('HGNC', 'ERG'),
            EnumeratedFusionRange('c', 1, 79),
            EnumeratedFusionRange('c', 312, 5034),
        )
        self._help_reconstitute(node_data, 1, 0)

    @mock_bel_resources
    def test_fusion_unspecified(self, mock):
        node_data = GeneFusion(
            Gene('HGNC', 'TMPRSS2'),
            Gene('HGNC', 'ERG'),
        )
        self._help_reconstitute(node_data, 1, 0)

    @mock_bel_resources
    def test_composite(self, mock):
        interleukin_23_complex = NamedComplexAbundance('GO', 'interleukin-23 complex')
        il6 = hgnc('IL6')
        interleukin_23_and_il6 = CompositeAbundance([interleukin_23_complex, il6])

        self._help_reconstitute(interleukin_23_and_il6, 3, 2)

    @mock_bel_resources
    def test_reaction(self, mock):
        self._help_reconstitute(superoxide_decomposition, 4, 3)

    @mock_bel_resources
    def test_complex(self, mock):
        self._help_reconstitute(ap1_complex, 3, 2)

    @mock_bel_resources
    def test_nested_complex(self, mock):
        self._help_reconstitute(bound_ap1_e2f4, 5, 4)


class TestReconstituteEdges(TemporaryCacheMixin):
    """This class tests that edges with varying properties can be added and extracted losslessly"""

    def setUp(self):
        """Creates a unit test with a manager and graph"""
        super().setUp()
        self.graph = BELGraph(name=n(), version=n())

    @mock_bel_resources
    def test_translocation_default(self, mock):
        """This test checks that a translocation gets in the database properly"""
        self.graph.add_increases(
            Protein(name='F2', namespace='HGNC'),
            Protein(name='EDN1', namespace='HGNC'),
            evidence='In endothelial cells, ET-1 secretion is detectable under basal conditions, whereas thrombin '
                     'induces its secretion.',
            citation='10473669',
            subject_modifier=secretion()
        )

        make_dummy_namespaces(self.manager, self.graph)

        network = self.manager.insert_graph(self.graph)
        self.assertEqual(2, network.nodes.count(), msg='Missing one or both of the nodes.')
        self.assertEqual(1, network.edges.count(), msg='Missing the edge')

        edge = network.edges.first()
        self.assertEqual(2, edge.properties.count())

    @mock_bel_resources
    def test_subject_translocation_custom_to_loc(self, mock):
        self.graph.add_increases(
            Protein(name='F2', namespace='HGNC'),
            Protein(name='EDN1', namespace='HGNC'),
            evidence='In endothelial cells, ET-1 secretion is detectable under basal conditions, whereas thrombin induces its secretion.',
            citation='10473669',
            subject_modifier=translocation(
                from_loc=Entity(namespace='TEST', name='A'),
                to_loc=Entity(namespace='GO', name='extracellular space'),
            )
        )

        make_dummy_namespaces(self.manager, self.graph)

        network = self.manager.insert_graph(self.graph)
        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        edge = network.edges.first()
        self.assertEqual(2, edge.properties.count())

    @mock_bel_resources
    def test_subject_activity_default(self, mock):
        p1_name = n()
        p2_name = n()

        self.graph.add_increases(
            Protein(name=p1_name, namespace='HGNC'),
            Protein(name=p2_name, namespace='HGNC'),
            evidence=n(),
            citation=n(),
            subject_modifier=activity('kin')
        )

        make_dummy_namespaces(self.manager, self.graph)

        network = self.manager.insert_graph(self.graph)
        self.assertEqual(2, network.nodes.count(), msg='number of nodes')
        self.assertEqual(1, network.edges.count(), msg='number of edges')

        kin_list = self.manager.session.query(NamespaceEntry).filter(NamespaceEntry.name == 'kin').all()
        self.assertEqual(1, len(kin_list), msg='number of kinase NamespaceEntrys')

        kin = list(kin_list)[0]
        self.assertEqual('kin', kin.name)

        effects = self.manager.session.query(Property).join(NamespaceEntry).filter(Property.effect == kin)
        self.assertEqual(1, effects.count(), msg='number of effects')

    @mock_bel_resources
    def test_subject_activity_custom(self, mock):
        p1_name = n()
        p2_name = n()
        dummy_activity_namespace = n()
        dummy_activity_name = n()

        self.graph.add_increases(
            Protein(name=p1_name, namespace='HGNC'),
            Protein(name=p2_name, namespace='HGNC'),
            evidence=n(),
            citation=n(),
            subject_modifier=activity(name=dummy_activity_name, namespace=dummy_activity_namespace)
        )

        make_dummy_namespaces(self.manager, self.graph)

        network = self.manager.insert_graph(self.graph)
        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        kin_list = self.manager.session.query(NamespaceEntry).filter(NamespaceEntry.name == dummy_activity_name).all()
        self.assertEqual(1, len(kin_list))

        kin = list(kin_list)[0]
        self.assertEqual(dummy_activity_name, kin.name)

        effects = self.manager.session.query(Property).join(NamespaceEntry).filter(Property.effect == kin)
        self.assertEqual(1, effects.count())

    @mock_bel_resources
    def test_object_activity_default(self, mock):
        p1_name = n()
        p2_name = n()

        self.graph.add_increases(
            Protein(name=p1_name, namespace='HGNC'),
            Protein(name=p2_name, namespace='HGNC'),
            evidence=n(),
            citation=n(),
            object_modifier=activity('kin')
        )

        make_dummy_namespaces(self.manager, self.graph)

        network = self.manager.insert_graph(self.graph)
        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        kin_list = self.manager.session.query(NamespaceEntry).filter(NamespaceEntry.name == 'kin').all()
        self.assertEqual(1, len(kin_list))

        kin = list(kin_list)[0]
        self.assertEqual('kin', kin.name)

        effects = self.manager.session.query(Property).join(NamespaceEntry).filter(Property.effect == kin)
        self.assertEqual(1, effects.count())

    @mock_bel_resources
    def test_object_activity_custom(self, mock):
        p1_name = n()
        p2_name = n()
        dummy_activity_namespace = n()
        dummy_activity_name = n()

        self.graph.add_increases(
            Protein(name=p1_name, namespace='HGNC'),
            Protein(name=p2_name, namespace='HGNC'),
            evidence=n(),
            citation=n(),
            object_modifier=activity(name=dummy_activity_name, namespace=dummy_activity_namespace)
        )

        make_dummy_namespaces(self.manager, self.graph)

        network = self.manager.insert_graph(self.graph)
        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        kin_list = self.manager.session.query(NamespaceEntry).filter(NamespaceEntry.name == dummy_activity_name).all()
        self.assertEqual(1, len(kin_list))

        kin = list(kin_list)[0]
        self.assertEqual(dummy_activity_name, kin.name)

        effects = self.manager.session.query(Property).join(NamespaceEntry).filter(Property.effect == kin)
        self.assertEqual(1, effects.count())

    def test_subject_degradation(self):
        self.graph.add_increases(
            Protein(name='YFG', namespace='HGNC'),
            Protein(name='YFG2', namespace='HGNC'),
            evidence=n(),
            citation=n(),
            subject_modifier=degradation(),
        )
        make_dummy_namespaces(self.manager, self.graph)

        network = self.manager.insert_graph(self.graph)

        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        edge = network.edges.first()
        self.assertEqual(1, edge.properties.count())

    def test_object_degradation(self):
        self.graph.add_increases(
            Protein(name='YFG', namespace='HGNC'),
            Protein(name='YFG2', namespace='HGNC'),
            evidence=n(),
            citation=n(),
            object_modifier=degradation(),
        )
        make_dummy_namespaces(self.manager, self.graph)

        network = self.manager.insert_graph(self.graph)

        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        edge = network.edges.first()
        self.assertEqual(1, edge.properties.count())

    def test_subject_location(self):
        self.graph.add_increases(
            Protein(name='YFG', namespace='HGNC'),
            Protein(name='YFG2', namespace='HGNC'),
            evidence=n(),
            citation=n(),
            subject_modifier=location(Entity(namespace='GO', name='nucleus', identifier='GO:0005634'))
        )
        make_dummy_namespaces(self.manager, self.graph)

        network = self.manager.insert_graph(self.graph)

        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        edge = network.edges.first()
        self.assertEqual(1, edge.properties.count())

    def test_mixed_1(self):
        """Test mixed having location and something else."""
        self.graph.add_increases(
            Protein(namespace='HGNC', name='CDC42'),
            Protein(namespace='HGNC', name='PAK2'),
            evidence="""Summary: PAK proteins, a family of serine/threonine p21-activating kinases, include PAK1, PAK2,
         PAK3 and PAK4. PAK proteins are critical effectors that link Rho GTPases to cytoskeleton reorganization
         and nuclear signaling. They serve as targets for the small GTP binding proteins Cdc42 and Rac and have
         been implicated in a wide range of biological activities. PAK4 interacts specifically with the GTP-bound
         form of Cdc42Hs and weakly activates the JNK family of MAP kinases. PAK4 is a mediator of filopodia
         formation and may play a role in the reorganization of the actin cytoskeleton. Multiple alternatively
         spliced transcript variants encoding distinct isoforms have been found for this gene.""",
            citation={CITATION_DB: "Online Resource", CITATION_IDENTIFIER: "PAK4 Hs ENTREZ Gene Summary"},
            annotations={'Species': '9606'},
            subject_modifier=activity('gtp'),
            object_modifier=activity('kin'),
        )

        make_dummy_namespaces(self.manager, self.graph)
        make_dummy_annotations(self.manager, self.graph)

        network = self.manager.insert_graph(self.graph)
        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        edge = network.edges.first()
        self.assertEqual(2, edge.properties.count())

        subject = edge.properties.filter(Property.is_subject).one()
        self.assertTrue(subject.is_subject)
        self.assertEqual('gtp', subject.effect.name)
        self.assertIsNotNone(subject.effect.namespace)
        self.assertEqual(BEL_DEFAULT_NAMESPACE, subject.effect.namespace.keyword)

        object = edge.properties.filter(not_(Property.is_subject)).one()
        self.assertFalse(object.is_subject)
        self.assertEqual('kin', object.effect.name)
        self.assertIsNotNone(object.effect.namespace)
        self.assertEqual(BEL_DEFAULT_NAMESPACE, object.effect.namespace.keyword)

    def test_mixed_2(self):
        """Tests both subject and object activity with location information as well."""
        self.graph.add_directly_increases(
            Protein(namespace='HGNC', name='HDAC4'),
            Protein(namespace='HGNC', name='MEF2A'),
            citation='10487761',
            evidence=""""In the nucleus, HDAC4 associates with the myocyte enhancer factor MEF2A. Binding of HDAC4 to
        MEF2A results in the repression of MEF2A transcriptional activation, a function that requires the
        deacetylase domain of HDAC4.""",
            annotations={'Species': '9606'},
            subject_modifier=activity('cat', location=Entity(namespace='GO', name='nucleus')),
            object_modifier=activity('tscript', location=Entity(namespace='GO', name='nucleus'))
        )

        make_dummy_namespaces(self.manager, self.graph)
        make_dummy_annotations(self.manager, self.graph)

        network = self.manager.insert_graph(self.graph)
        self.assertEqual(2, network.nodes.count())
        self.assertEqual(1, network.edges.count())

        edge = network.edges.first()
        self.assertEqual(4, edge.properties.count())
        self.assertEqual(2, edge.properties.filter(Property.is_subject).count())
        self.assertEqual(2, edge.properties.filter(not_(Property.is_subject)).count())


class TestNoAddNode(TemporaryCacheMixin):
    """Tests scenarios where an instance of :class:`BELGraph` may contain edges that refer to uncached resources, and
    therefore should not be added to the edge store."""

    @mock_bel_resources
    def test_regex_lookup(self, mock):  # FIXME this test needs to be put somewhere else
        """Test that regular expression nodes get love too."""
        graph = BELGraph(
            name='Regular Expression Test Graph',
            description='Help test regular expression namespaces',
            version='1.0.0',
        )
        dbsnp = 'dbSNP'
        DBSNP_PATTERN = 'rs[0-9]+'
        graph.namespace_pattern[dbsnp] = DBSNP_PATTERN

        rs1234 = Gene(namespace=dbsnp, name='rs1234')
        rs1235 = Gene(namespace=dbsnp, name='rs1235')

        graph.add_node_from_data(rs1234)
        graph.add_node_from_data(rs1235)

        rs1234_hash = rs1234.md5
        rs1235_hash = rs1235.md5

        self.manager.insert_graph(graph)

        rs1234_lookup = self.manager.get_node_by_hash(rs1234_hash)
        self.assertIsNotNone(rs1234_lookup)
        self.assertEqual('Gene', rs1234_lookup.type)
        self.assertEqual('g(dbSNP:rs1234)', rs1234_lookup.bel)
        self.assertEqual(rs1234_hash, rs1234_lookup.md5)
        self.assertIsNotNone(rs1234_lookup.namespace_entry)
        self.assertEqual('rs1234', rs1234_lookup.namespace_entry.name)
        self.assertEqual('dbSNP', rs1234_lookup.namespace_entry.namespace.keyword)
        self.assertEqual(DBSNP_PATTERN, rs1234_lookup.namespace_entry.namespace.pattern)

        rs1235_lookup = self.manager.get_node_by_hash(rs1235_hash)
        self.assertIsNotNone(rs1235_lookup)
        self.assertEqual('Gene', rs1235_lookup.type)
        self.assertEqual('g(dbSNP:rs1235)', rs1235_lookup.bel)
        self.assertEqual(rs1235_hash, rs1235_lookup.md5)
        self.assertIsNotNone(rs1235_lookup.namespace_entry)
        self.assertEqual('rs1235', rs1235_lookup.namespace_entry.name)
        self.assertEqual('dbSNP', rs1235_lookup.namespace_entry.namespace.keyword)
        self.assertEqual(DBSNP_PATTERN, rs1235_lookup.namespace_entry.namespace.pattern)


class TestEquivalentNodes(unittest.TestCase):
    def test_direct_has_namespace(self):
        graph = BELGraph()

        n1 = Protein(namespace='HGNC', name='CD33', identifier='1659')
        n2 = Protein(namespace='NOPE', name='NOPE', identifier='NOPE')

        graph.add_increases(n1, n2, citation=n(), evidence=n())

        self.assertEqual({n1}, graph.get_equivalent_nodes(n1))

        self.assertTrue(graph.node_has_namespace(n1, 'HGNC'))
        self.assertFalse(graph.node_has_namespace(n2, 'HGNC'))

    def test_indirect_has_namespace(self):
        graph = BELGraph()

        a = Protein(namespace='HGNC', name='CD33')
        b = Protein(namespace='HGNCID', identifier='1659')

        graph.add_equivalence(a, b)

        self.assertEqual({a, b}, graph.get_equivalent_nodes(a))
        self.assertEqual({a, b}, graph.get_equivalent_nodes(b))

        self.assertTrue(graph.node_has_namespace(a, 'HGNC'))
        self.assertTrue(graph.node_has_namespace(b, 'HGNC'))

    def test_triangle_has_namespace(self):
        graph = BELGraph()

        a = Protein(namespace='A', name='CD33')
        b = Protein(namespace='B', identifier='1659')
        c = Protein(namespace='C', identifier='1659')
        d = Protein(namespace='HGNC', identifier='1659')

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
