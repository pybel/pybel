import logging
import os
import unittest

import py2neo
import py2neo.database.status
from click.testing import CliRunner

import pybel
from pybel import cli
from pybel.constants import PYBEL_CONTEXT_TAG
from tests.constants import test_bel, test_bel_slushy, BelReconstitutionMixin, expected_test_bel_metadata, mock_bel_resources

log = logging.getLogger(__name__)


class TestCli(BelReconstitutionMixin, unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @mock_bel_resources
    def test_slushy(self, mock_get):
        """Tests that slushy document doesn't even make it to warning counting"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli.main, ['convert', '--path', test_bel_slushy])
            self.assertEqual(-1, result.exit_code, msg=result.exc_info)

    @mock_bel_resources
    def test_convert(self, mock_get):

        with self.runner.isolated_filesystem():
            test_csv = os.path.abspath('test.csv')
            test_gpickle = os.path.abspath('test.gpickle')
            test_graphml = os.path.abspath('test.graphml')
            test_json = os.path.abspath('test.json')
            test_canon = os.path.abspath('test.bel')

            conn = 'sqlite:///' + os.path.abspath('test.db')

            args = [
                'convert',
                '--path', test_bel,
                '--csv', test_csv,
                '--pickle', test_gpickle,
                '--graphml', test_graphml,
                '--json', test_json,
                '--bel', test_canon,
                '--store', conn
            ]

            result = self.runner.invoke(cli.main, args)
            self.assertEqual(0, result.exit_code, msg=result.exc_info)

            self.assertTrue(os.path.exists(test_csv))

            self.bel_1_reconstituted(pybel.from_pickle(test_gpickle))
            self.bel_1_reconstituted(pybel.from_graphml(test_graphml), check_metadata=False)
            self.bel_1_reconstituted(pybel.from_json(test_json))
            self.bel_1_reconstituted(pybel.from_path(test_canon))
            self.bel_1_reconstituted(pybel.from_database(expected_test_bel_metadata['name'], connection=conn))

    @unittest.skipUnless('NEO_PATH' in os.environ, 'Need environmental variable $NEO_PATH')
    @mock_bel_resources
    def test_neo4j_remote(self, mock_get):
        test_context = 'PYBEL_TEST_CTX'
        neo_path = os.environ['NEO_PATH']

        try:
            neo = py2neo.Graph(neo_path)
            neo.data('match (n)-[r]->() where r.{}="{}" detach delete n'.format(PYBEL_CONTEXT_TAG, test_context))
        except py2neo.database.status.GraphError:
            self.skipTest("Can't connect to neo4j")
        else:
            self.runner.invoke(cli.main, ['convert', '--path', test_bel, '--neo',
                                          neo_path, '--neo-context', test_context, '--complete-origin'])

            q = 'match (n)-[r]->() where r.{}="{}" return count(n) as count'.format(PYBEL_CONTEXT_TAG, test_context)
            count = neo.data(q)[0]['count']
            self.assertEqual(14, count)
