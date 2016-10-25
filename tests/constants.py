import os
import unittest

from pybel.parser.parse_bel import BelParser
from pybel.parser.utils import subdict_matches, any_subdict_matches

dir_path = os.path.dirname(os.path.realpath(__file__))

PYBEL_TEST_ALL = False  # getpass.getuser() in ('cthoyt',) or int(os.environ.get('PYBEL_ALLTESTS', '0')) == 3

test_ns_1 = os.path.join(dir_path, 'bel', 'test_ns_1.belns')
test_bel_1 = os.path.join(dir_path, 'bel', 'test_bel_1.bel')
test_bel_2 = os.path.join(dir_path, 'bel', 'test_bel_2.bel')
test_bel_3 = os.path.join(dir_path, 'bel', 'test_bel_3.bel')


class TestTokenParserBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = BelParser()

    def setUp(self):
        self.parser.clear()

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
