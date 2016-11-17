import os
import unittest

from pybel.parser.parse_bel import BelParser
from pybel.parser.utils import any_subdict_matches

dir_path = os.path.dirname(os.path.realpath(__file__))

test_ns_1 = os.path.join(dir_path, 'bel', 'test_ns_1.belns')
test_bel_1 = os.path.join(dir_path, 'bel', 'test_bel_1.bel')
test_bel_2 = os.path.join(dir_path, 'bel', 'test_bel_2.bel')
test_bel_3 = os.path.join(dir_path, 'bel', 'test_bel_3.bel')
test_bel_slushy = os.path.join(dir_path, 'bel', 'slushy.bel')

test_citation_bel = 'SET Citation = {"TestType","TestName","TestRef"}'
test_citation_dict = dict(type='TestType', name='TestName', reference='TestRef')


class TestTokenParserBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = BelParser()

    def setUp(self):
        self.parser.clear()

    def assertHasNode(self, member, msg=None, **kwargs):
        self.assertIn(member, self.parser.graph)
        if kwargs:
            self.assertTrue(all(kwarg in self.parser.graph.node[member] for kwarg in kwargs),
                            msg="Missing kwarg in node data")
            self.assertEqual(kwargs, {k: self.parser.graph.node[member][k] for k in kwargs},
                             msg="Wrong values in node data")
            # msg_format = 'Wrong node {} properties. expected {} but got {}'
            # self.assertTrue(subdict_matches(self.parser.graph.node[member], kwargs, ),
            #                msg=msg_format.format(member, kwargs, self.parser.graph.node[member]))

    def assertHasEdge(self, u, v, msg=None, **kwargs):
        self.assertTrue(self.parser.graph.has_edge(u, v), msg='Edge ({}, {}) not in graph'.format(u, v))
        if kwargs:
            msg_format = 'No edge with correct properties. expected {} but got {}'
            self.assertTrue(any_subdict_matches(self.parser.graph.edge[u][v], kwargs),
                            msg=msg_format.format(kwargs, self.parser.graph.edge[u][v]))

def bel_1_reconstituted(self, g):
    nodes = list(g.nodes_iter(namespace='HGNC', name='AKT1'))
    self.assertEqual(3, len(nodes))

    edges = list(g.edges_iter(relation='increases'))
    self.assertEqual(2, len(edges))
