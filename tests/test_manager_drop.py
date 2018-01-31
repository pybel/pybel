# -*- coding: utf-8 -*-

from pybel import BELGraph
from pybel.constants import *
from pybel.dsl import protein
from pybel.manager.models import Edge, Network, Node
from tests.constants import TemporaryCacheMixin, test_citation_dict, test_evidence_text
from tests.mocks import mock_bel_resources
from tests.utils import make_dummy_annotations, make_dummy_namespaces, n

yfg1 = protein(name='YFG1', namespace='HGNC')
yfg2 = protein(name='YFG1', namespace='HGNC')


class TestReconstituteNodeTuples(TemporaryCacheMixin):
    @mock_bel_resources
    def test_simple(self, mock):
        """This test checks that the network can be added and dropped"""
        graph = BELGraph(name='test', version='0.0.0')

        namespaces = {
            'HGNC': ['YFG1', 'YFG2']
        }
        annotations = {
            'Disease': ['Disease1', 'Disease2'],
            'Cell': ['Cell1']
        }

        make_dummy_namespaces(self.manager, graph, namespaces)
        make_dummy_annotations(self.manager, graph, annotations)

        graph.add_qualified_edge(
            yfg1,
            yfg2,
            relation=INCREASES,
            evidence=test_evidence_text,
            citation=test_citation_dict,
            annotations={
                'Disease': {'Disease1': True},
                'Cell': {'Cell1': True}
            }
        )

        network = self.manager.insert_graph(graph, store_parts=True)

        self.manager.drop_network_by_id(network.id)


class TestCascades(TemporaryCacheMixin):
    def setUp(self):
        super(TestCascades, self).setUp()

        self.n1 = Node(type=PROTEIN, bel='p(HGNC:A)')
        self.n2 = Node(type=PROTEIN, bel='p(HGNC:B)')
        self.n3 = Node(type=PROTEIN, bel='p(HGNC:C)')
        self.e1 = Edge(source=self.n1, target=self.n2, relation=INCREASES, bel='p(HGNC:A) increases p(HGNC:B)')
        self.e2 = Edge(source=self.n2, target=self.n3, relation=INCREASES, bel='p(HGNC:B) increases p(HGNC:C)')
        self.e3 = Edge(source=self.n1, target=self.n3, relation=INCREASES, bel='p(HGNC:A) increases p(HGNC:C)')
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
        edges = list(self.manager.iterate_singleton_edges_from_network(self.g1))
        self.assertEqual(2, len(edges))
        self.assertIn(self.e2, edges)
        self.assertIn(self.e3, edges)

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

    def test_drop_modification(self):
        """Don't let this happen"""

    def test_drop_property(self):
        """Don't let this happen"""
