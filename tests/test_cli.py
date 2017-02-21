# -*- coding: utf-8 -*-

import logging
import os
import unittest

import py2neo
import py2neo.database.status
from click.testing import CliRunner

from pybel import cli
from pybel.constants import PYBEL_CONTEXT_TAG, METADATA_NAME
from pybel.io import from_pickle, from_json, from_path
from pybel.manager.database_io import from_database
from .constants import test_bel_simple, BelReconstitutionMixin, mock_bel_resources, test_bel_thorough, \
    expected_test_thorough_metadata

log = logging.getLogger(__name__)


class TestCli(BelReconstitutionMixin, unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @mock_bel_resources
    def test_convert(self, mock_get):

        with self.runner.isolated_filesystem():
            test_csv = os.path.abspath('test.csv')
            test_gpickle = os.path.abspath('test.gpickle')
            test_canon = os.path.abspath('test.bel')

            conn = 'sqlite:///' + os.path.abspath('test.db')

            args = [
                'convert',
                # Input
                '--path', test_bel_thorough,
                # Outputs
                '--csv', test_csv,
                '--pickle', test_gpickle,
                '--bel', test_canon,
                '--store', conn,
                '--allow-nested'
            ]

            result = self.runner.invoke(cli.main, args)
            self.assertEqual(0, result.exit_code, msg=result.exc_info)

            self.assertTrue(os.path.exists(test_csv))

            self.bel_thorough_reconstituted(from_pickle(test_gpickle))
            self.bel_thorough_reconstituted(from_path(test_canon))
            self.bel_thorough_reconstituted(from_database(expected_test_thorough_metadata[METADATA_NAME],
                                                          connection=conn))

    @mock_bel_resources
    def test_convert_json(self, mock_get):
        with self.runner.isolated_filesystem():
            test_json = os.path.abspath('test.json')

            args = [
                'convert',
                '--path', test_bel_thorough,
                '--json', test_json,
                '--allow-nested'
            ]

            result = self.runner.invoke(cli.main, args)
            self.assertEqual(0, result.exit_code, msg=result.exc_info)

            self.bel_thorough_reconstituted(from_json(test_json))

    @unittest.skipUnless('NEO_PATH' in os.environ, 'Need environmental variable $NEO_PATH')
    @mock_bel_resources
    def test_neo4j_remote(self, mock_get):
        test_context = 'PYBEL_TEST_CTX'
        neo_path = os.environ['NEO_PATH']

        try:
            neo = py2neo.Graph(neo_path)
            neo.data('match (n)-[r]->() where r.{}="{}" detach delete n'.format(PYBEL_CONTEXT_TAG, test_context))
        except py2neo.database.status.GraphError:
            self.skipTest("Can't query Neo4J ")
        except:
            self.skipTest("Can't connect to Neo4J server")
        else:
            self.runner.invoke(cli.main, ['convert', '--path', test_bel_simple, '--neo',
                                          neo_path, '--neo-context', test_context, '--complete-origin'])

            q = 'match (n)-[r]->() where r.{}="{}" return count(n) as count'.format(PYBEL_CONTEXT_TAG, test_context)
            count = neo.data(q)[0]['count']
            self.assertEqual(14, count)
