import json
import logging
import os
import unittest

import networkx as nx
import py2neo
from click.testing import CliRunner

import pybel
from pybel import cli
from pybel.graph import PYBEL_CONTEXT_TAG
from tests.constants import test_bel_1

log = logging.getLogger(__name__)


class TestCli(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @unittest.skipUnless('NEO_PATH' in os.environ, 'Need environmental variable $NEO_PATH')
    def test_neo4j(self):
        test_context = 'PYBEL_TEST_CTX'

        neo = py2neo.Graph(os.environ['NEO_PATH'])
        neo.data('match (n)-[r]->() where r.{}="{}" detach delete n'.format(PYBEL_CONTEXT_TAG, test_context))

        self.runner.invoke(cli.main, ['to_neo', '--path', test_bel_1, '--neo', os.environ['NEO_PATH'], '--context',
                                      test_context])

        q = 'match (n)-[r]->() where r.{}="{}" return count(n) as count'.format(PYBEL_CONTEXT_TAG, test_context)
        count = neo.data(q)[0]['count']
        self.assertEqual(14, count)

    @unittest.skip
    def test_csv(self):
        test_edge_file = 'myedges.csv'

        with self.runner.isolated_filesystem():
            abs_test_edge_file = os.path.abspath(test_edge_file)
            result = self.runner.invoke(cli.main, ['convert', '--path', test_bel_1, '--csv', abs_test_edge_file])
            log.info('File paths: {}'.format(abs_test_edge_file))
            self.assertEqual(0, result.exit_code, msg=result.exc_info)
            self.assertTrue(os.path.exists(abs_test_edge_file))

            with open(abs_test_edge_file) as f:
                loaded = json.load(f)
                self.assertIsNotNone(loaded)

    def test_pickle(self):
        test_file = 'mygraph.gpickle'

        with self.runner.isolated_filesystem():
            abs_test_file = os.path.abspath(test_file)
            result = self.runner.invoke(cli.main, ['convert', '--path', test_bel_1, '--pickle', abs_test_file])
            log.info('File path: {}'.format(abs_test_file))
            self.assertEqual(0, result.exit_code)
            self.assertTrue(os.path.exists(abs_test_file))
            g = pybel.from_pickle(abs_test_file)
            self.assertTrue(isinstance(g, nx.MultiDiGraph))

    def test_graphml(self):
        test_file = 'mygraph.graphml'

        with self.runner.isolated_filesystem():
            abs_test_file = os.path.abspath(test_file)
            result = self.runner.invoke(cli.main, ['convert', '--path', test_bel_1, '--graphml', abs_test_file])
            log.info('File path: {}'.format(abs_test_file))
            self.assertEqual(0, result.exit_code)
            self.assertTrue(os.path.exists(abs_test_file))
            g = nx.read_graphml(abs_test_file)
            self.assertTrue(isinstance(g, (nx.MultiDiGraph, nx.DiGraph)))

    def test_json(self):
        test_file = 'mygraph.json'

        with self.runner.isolated_filesystem():
            abs_test_file = os.path.abspath(test_file)
            result = self.runner.invoke(cli.main, ['convert', '--path', test_bel_1, '--json', abs_test_file])
            log.info('File path: {}'.format(abs_test_file))
            self.assertEqual(0, result.exit_code, msg=result.exc_info)
            self.assertTrue(os.path.exists(abs_test_file))

            with open(abs_test_file) as f:
                loaded = json.load(f)
                self.assertIsNotNone(loaded)
