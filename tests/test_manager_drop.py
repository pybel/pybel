from pybel import BELGraph
from pybel.constants import *
from tests.constants import TemporaryCacheMixin, test_citation_dict, test_evidence_text
from tests.utils import make_dummy_namespaces, make_dummy_annotations


class TestReconstituteNodeTuples(TemporaryCacheMixin):
    def test_simple(self):
        """This test checks that the network can be added and dropped"""
        graph = BELGraph(name='test', version='0.0.0')

        node_1 = graph.add_node_from_data({
            FUNCTION: PROTEIN,
            NAMESPACE: 'HGNC',
            NAME: 'YFG1'
        })

        node_2 = graph.add_node_from_data({
            FUNCTION: PROTEIN,
            NAMESPACE: 'HGNC',
            NAME: 'YFG2'
        })

        namespaces = {
            'HGNC': ['YFG1', 'YFG2']
        }
        annotations = {
            'Disease': ['Disease1', 'Disease2'],
            'Cell': ['Cell1']
        }

        make_dummy_namespaces(self.manager, graph, namespaces)
        make_dummy_annotations(self.manager, graph, annotations)

        graph.add_edge(node_1, node_2, **{
            RELATION: INCREASES,
            EVIDENCE: test_evidence_text,
            CITATION: test_citation_dict,
            ANNOTATIONS: {
                'Disease': 'Disease1',
                'Cell': 'Cell1'
            }
        })

        network = self.manager.insert_graph(graph, store_parts=True)

        self.manager.drop_network_by_id(network.id)
