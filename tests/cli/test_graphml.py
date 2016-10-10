import logging
import os

import networkx as nx

from pybel import cli
from tests.constants import TestCliBase

log = logging.getLogger(__name__)
dir_path = os.path.dirname(os.path.realpath(__file__))


class TestCliGraphML(TestCliBase):
    def test_graphml(self):
        test_file = 'mygraph.graphml'

        with self.runner.isolated_filesystem():
            abs_test_file = os.path.abspath(test_file)
            result = self.runner.invoke(cli.main, ['to_graphml', '--path', self.test_path, '--output', abs_test_file])
            log.info('File path: {}'.format(abs_test_file))
            self.assertEqual(0, result.exit_code)
            self.assertTrue(os.path.exists(abs_test_file))
            g = nx.read_graphml(abs_test_file)
            self.assertTrue(isinstance(g, (nx.MultiDiGraph, nx.DiGraph)))
