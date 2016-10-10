import logging
import os

import networkx as nx

from pybel import cli
from tests.constants import TestCliBase

log = logging.getLogger(__name__)


class TestCliPickle(TestCliBase):
    def test_pickle(self):
        test_file = 'mygraph.gpickle'

        with self.runner.isolated_filesystem():
            abs_test_file = os.path.abspath(test_file)
            result = self.runner.invoke(cli.main, ['to_pickle', '--path', self.test_path, '--output', abs_test_file])
            log.info('File path: {}'.format(abs_test_file))
            self.assertEqual(0, result.exit_code)
            self.assertTrue(os.path.exists(abs_test_file))
            g = nx.read_gpickle(abs_test_file)
            self.assertTrue(isinstance(g, nx.MultiDiGraph))
