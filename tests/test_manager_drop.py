# -*- coding: utf-8 -*-

from pybel import BELGraph
from pybel.constants import *
from pybel.dsl import protein
from tests.constants import TemporaryCacheMixin, test_citation_dict, test_evidence_text
from tests.mocks import mock_bel_resources
from tests.utils import make_dummy_annotations, make_dummy_namespaces

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

        node_1 = graph.add_node_from_data(yfg1)
        node_2 = graph.add_node_from_data(yfg2)

        graph.add_qualified_edge(
            node_1,
            node_2,
            relation=INCREASES,
            evidence=test_evidence_text,
            citation=test_citation_dict,
            annotations={
                'Disease': 'Disease1',
                'Cell': 'Cell1'
            }
        )

        network = self.manager.insert_graph(graph, store_parts=True)

        self.manager.drop_network_by_id(network.id)
