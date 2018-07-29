# -*- coding: utf-8 -*-

"""Tests for the command line interface."""

import json
import logging
import os
import traceback
import unittest

import py2neo
import py2neo.database.status
from click.testing import CliRunner

from pybel import Manager, cli
from pybel.constants import METADATA_NAME, PYBEL_CONTEXT_TAG
from pybel.io import from_json, from_path, from_pickle
from pybel.manager.database_io import from_database
from pybel.testing.cases import FleetingTemporaryCacheMixin
from pybel.testing.constants import test_bel_simple, test_bel_thorough
from pybel.testing.mocks import mock_bel_resources
from tests.constants import BelReconstitutionMixin, expected_test_thorough_metadata

log = logging.getLogger(__name__)


@unittest.skip
class TestCli(FleetingTemporaryCacheMixin, BelReconstitutionMixin):
    def setUp(self):
        super(TestCli, self).setUp()
        self.runner = CliRunner()

    @mock_bel_resources
    def test_convert(self, mock_get):

        with self.runner.isolated_filesystem():
            test_csv = os.path.abspath('test.csv')
            test_gpickle = os.path.abspath('test.gpickle')
            test_canon = os.path.abspath('test.bel')

            args = [
                'convert',
                # Input
                '--path', test_bel_thorough,
                '--connection', self.connection,
                # Outputs
                '--csv', test_csv,
                '--pickle', test_gpickle,
                '--bel', test_canon,
                '--store',
                '--allow-nested'
            ]

            result = self.runner.invoke(cli.main, args)
            self.assertEqual(0, result.exit_code, msg='{}\n{}\n{}'.format(
                result.exc_info[0],
                result.exc_info[1],
                traceback.format_tb(result.exc_info[2])
            ))

            self.assertTrue(os.path.exists(test_csv))

            self.bel_thorough_reconstituted(from_pickle(test_gpickle))
            self.bel_thorough_reconstituted(from_path(test_canon))

            manager = Manager(connection=self.connection)
            self.bel_thorough_reconstituted(
                from_database(expected_test_thorough_metadata[METADATA_NAME], manager=manager))

    @mock_bel_resources
    def test_convert_json(self, mock_get):
        with self.runner.isolated_filesystem():
            test_json = os.path.abspath('test.json')

            args = [
                'convert',
                '--path', test_bel_thorough,
                '--json', test_json,
                '--connection', self.connection,
                '--allow-nested'
            ]

            result = self.runner.invoke(cli.main, args)
            self.assertEqual(0, result.exit_code, msg=result.exc_info)

            with open(test_json) as f:
                self.bel_thorough_reconstituted(from_json(json.load(f)))

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
            with self.runner.isolated_filesystem():
                args = [
                    'convert',
                    '--path', test_bel_simple,
                    '--connection', self.connection,
                    '--neo', neo_path,
                    '--neo-context', test_context
                ]
                self.runner.invoke(cli.main, args)

                q = 'match (n)-[r]->() where r.{}="{}" return count(n) as count'.format(PYBEL_CONTEXT_TAG, test_context)
                count = neo.data(q)[0]['count']
                self.assertEqual(14, count)
