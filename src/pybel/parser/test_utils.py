import unittest

from .parse_bel import BelParser
from .utils import subdict_matches, any_subdict_matches


class TestTokenParserBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = BelParser()

    def setUp(self):
        self.parser.graph.clear()
        self.parser.clear_annotations()
        self.parser.node_to_id.clear()
        self.parser.id_to_node.clear()
        self.parser.node_count = 0

    def assertHasNode(self, member, msg=None, **kwargs):
        self.assertIn(member, self.parser.graph)
        if kwargs:
            msg_format = 'Wrong node {} properties. expected {} but got {}'
            self.assertTrue(subdict_matches(self.parser.graph.node[member], kwargs, ),
                            msg=msg_format.format(member, kwargs, self.parser.graph.node[member]))

    def assertHasEdge(self, u, v, msg=None, **kwargs):
        self.assertTrue(self.parser.graph.has_edge(u, v), msg='Edge ({}, {}) not in graph'.format(u, v))
        if kwargs:
            msg_format = 'No edge with correct properties. expected {} but got {}'
            self.assertTrue(any_subdict_matches(self.parser.graph.edge[u][v], kwargs),
                            msg=msg_format.format(kwargs, self.parser.graph.edge[u][v]))
