import logging
import os
import unittest

import py2neo
from click.testing import CliRunner

import pybel
from pybel import cli
from pybel.graph import PYBEL_CONTEXT_TAG
from tests.constants import test_bel_1, test_bel_slushy, bel_1_reconstituted

log = logging.getLogger(__name__)


class TestCli(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @unittest.skipUnless('NEO_PATH' in os.environ, 'Need environmental variable $NEO_PATH')
    def test_neo4j_remote(self):
        test_context = 'PYBEL_TEST_CTX'
        neo_path = os.environ['NEO_PATH']
        neo = py2neo.Graph(neo_path)
        neo.data('match (n)-[r]->() where r.{}="{}" detach delete n'.format(PYBEL_CONTEXT_TAG, test_context))

        self.runner.invoke(cli.main, ['convert', '--path', test_bel_1, '--neo',
                                      neo_path, '--neo-context', test_context, '--complete-origin'])

        q = 'match (n)-[r]->() where r.{}="{}" return count(n) as count'.format(PYBEL_CONTEXT_TAG, test_context)
        count = neo.data(q)[0]['count']
        self.assertEqual(14, count)

    def test_csv(self):
        test_edge_file = 'myedges.csv'

        with self.runner.isolated_filesystem():
            abs_test_edge_file = os.path.abspath(test_edge_file)
            result = self.runner.invoke(cli.main, ['convert', '--path', test_bel_1, '--csv', abs_test_edge_file])
            self.assertEqual(0, result.exit_code, msg=result.exc_info)
            self.assertTrue(os.path.exists(abs_test_edge_file))

    def test_slushy(self):
        """Tests that slushy document doesn't even make it to warning counting"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli.main, ['convert', '--path', test_bel_slushy])
            self.assertEqual(-1, result.exit_code, msg=result.exc_info)

    def test_pickle(self):
        test_file = 'mygraph.gpickle'

        with self.runner.isolated_filesystem():
            abs_test_file = os.path.abspath(test_file)
            result = self.runner.invoke(cli.main, ['convert', '--path', test_bel_1, '--pickle', abs_test_file,
                                                   '--complete-origin'])
            self.assertEqual(0, result.exit_code)
            self.assertTrue(os.path.exists(abs_test_file))
            g = pybel.from_pickle(abs_test_file)
            bel_1_reconstituted(self, g)

    def test_graphml(self):
        test_file = 'mygraph.graphml'

        with self.runner.isolated_filesystem():
            abs_test_file = os.path.abspath(test_file)
            result = self.runner.invoke(cli.main, ['convert', '--path', test_bel_1, '--graphml', abs_test_file,
                                                   '--complete-origin'])
            self.assertEqual(0, result.exit_code)
            self.assertTrue(os.path.exists(abs_test_file))
            g = pybel.from_graphml(abs_test_file)
            bel_1_reconstituted(self, g)

    def test_json(self):
        test_file = 'mygraph.json'

        with self.runner.isolated_filesystem():
            abs_test_file = os.path.abspath(test_file)
            result = self.runner.invoke(cli.main, ['convert', '--path', test_bel_1, '--json', abs_test_file,
                                                   '--complete-origin'])
            self.assertEqual(0, result.exit_code, msg=result.exc_info)
            self.assertTrue(os.path.exists(abs_test_file))
            g = pybel.from_json(abs_test_file)
            bel_1_reconstituted(self, g)

    def test_bel(self):
        test_file = 'mygraph.bel'

        with self.runner.isolated_filesystem():
            abs_test_file = os.path.abspath(test_file)
            result = self.runner.invoke(cli.main, ['convert', '--path', test_bel_1, '--bel', abs_test_file,
                                                   '--complete-origin'])
            self.assertEqual(0, result.exit_code, msg=result.exc_info)
            g = pybel.from_path(abs_test_file)
            bel_1_reconstituted(self, g)
