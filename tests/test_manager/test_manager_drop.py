# -*- coding: utf-8 -*-

import json

from pybel import BELGraph
from pybel.constants import INCREASES, RELATION
from pybel.dsl import protein
from pybel.manager.models import Edge, Namespace, NamespaceEntry, Network, Node
from pybel.testing.cases import TemporaryCacheMixin
from pybel.testing.mocks import mock_bel_resources
from pybel.testing.utils import make_dummy_annotations, make_dummy_namespaces, n
from tests.constants import test_citation_dict, test_evidence_text

yfg1 = protein(name='YFG1', namespace='HGNC')
yfg2 = protein(name='YFG1', namespace='HGNC')
yfg3 = protein(name='YFG3', namespace='HGNC')


def make_increase_edge(u, v):
    bel = '{} {} {}'.format(u.as_bel(), INCREASES, v.as_bel())
    data = json.dumps({
        RELATION: INCREASES
    })
    assert data
    return Edge(source=u, target=v, relation=INCREASES, bel=bel, data=data)


class TestReconstituteNodeTuples(TemporaryCacheMixin):
    @mock_bel_resources
    def test_simple(self, mock):
        """This test checks that the network can be added and dropped"""
        graph = BELGraph(name='test', version='0.0.0')
        graph.add_increases(
            yfg1,
            yfg2,
            evidence=test_evidence_text,
            citation=test_citation_dict,
            annotations={
                'Disease': {'Disease1': True},
                'Cell': {'Cell1': True}
            }
        )

        make_dummy_namespaces(self.manager, graph)
        make_dummy_annotations(self.manager, graph)

        network = self.manager.insert_graph(graph, store_parts=True)

        self.manager.drop_network_by_id(network.id)


class TestCascades(TemporaryCacheMixin):
    def setUp(self):
        super(TestCascades, self).setUp()

        self.n1 = Node._start_from_base_entity(yfg1)
        self.n2 = Node._start_from_base_entity(yfg2)
        self.n3 = Node._start_from_base_entity(yfg3)
        self.e1 = make_increase_edge(self.n1, self.n2)
        self.e2 = make_increase_edge(self.n2, self.n3)
        self.e3 = make_increase_edge(self.n1, self.n3)
        self.g1 = Network(name=n(), version=n(), edges=[self.e1, self.e2, self.e3])
        self.g2 = Network(name=n(), version=n(), edges=[self.e1])

        self.manager.session.add_all([self.n1, self.n2, self.n3, self.e1, self.e2, self.e3, self.g1, self.g2])
        self.manager.session.commit()

        self.assertEqual(3, self.manager.count_nodes())
        self.assertEqual(3, self.manager.count_edges())
        self.assertEqual(2, self.manager.count_networks())

    def test_drop_node(self):
        """Makes sure that when a node gets dropped, its in-edges AND out-edges also do"""
        self.manager.session.delete(self.n2)
        self.manager.session.commit()

        self.assertEqual(2, self.manager.count_nodes())
        self.assertEqual(1, self.manager.count_edges())
        self.assertEqual(2, self.manager.count_networks())
        self.assertEqual(1, self.g1.edges.count())
        self.assertEqual(0, self.g2.edges.count())

    def test_drop_edge(self):
        """When an edge gets dropped, make sure the network doesn't have as many edges, but nodes get to stay"""
        self.manager.session.delete(self.e1)
        self.manager.session.commit()

        self.assertEqual(3, self.manager.count_nodes())
        self.assertEqual(2, self.manager.count_edges())
        self.assertEqual(2, self.manager.count_networks())
        self.assertEqual(2, self.g1.edges.count())
        self.assertEqual(0, self.g2.edges.count())

    def test_get_orphan_edges(self):
        edges = [result.edge_id for result in self.manager.query_singleton_edges_from_network(self.g1)]
        self.assertEqual(2, len(edges))
        self.assertIn(self.e2.id, edges)
        self.assertIn(self.e3.id, edges)

    def test_drop_network_1(self):
        """When a network gets dropped, drop all of the edges if they don't appear in other networks"""
        self.manager.drop_network(self.g1)

        self.assertEqual(3, self.manager.count_nodes())
        self.assertEqual(1, self.manager.count_edges())
        self.assertEqual(1, self.manager.count_networks())
        self.assertEqual(1, self.g2.edges.count())

    def test_drop_network_2(self):
        """When a network gets dropped, drop all of the edges if they don't appear in other networks"""
        self.manager.drop_network(self.g2)

        self.assertEqual(3, self.manager.count_nodes())
        self.assertEqual(3, self.manager.count_edges())
        self.assertEqual(1, self.manager.count_networks())
        self.assertEqual(3, self.g1.edges.count())

    def test_drop_all_networks(self):
        """When all networks are dropped, make sure all the edges and network_edge mappings are gone too"""
        self.manager.drop_networks()

        self.assertEqual(0, self.manager.count_edges())
        self.assertEqual(0, self.manager.count_networks())

    def test_drop_modification(self):
        """Don't let this happen"""

    def test_drop_property(self):
        """Don't let this happen"""

    def test_drop_namespace(self):
        keyword, url = n(), n()

        namespace = Namespace(keyword=keyword, url=url)
        self.manager.session.add(namespace)

        n_entries = 5

        for _ in range(n_entries):
            entry = NamespaceEntry(name=n(), namespace=namespace)
            self.manager.session.add(entry)

        self.manager.session.commit()

        self.assertEqual(1, self.manager.count_namespaces(), msg='Should have one namespace')
        self.assertEqual(n_entries, self.manager.count_namespace_entries(),
                         msg='Should have {} entries'.format(n_entries))

        self.manager.drop_namespace_by_url(url)

        self.assertEqual(0, self.manager.count_namespaces(), msg='Should have no namespaces')
        self.assertEqual(0, self.manager.count_namespace_entries(), msg='Entries should have been dropped')
