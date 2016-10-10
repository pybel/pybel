import json
import logging
import os
import unittest

from pybel import cli
from tests.constants import TestCliBase

log = logging.getLogger(__name__)


class TestCliNeo(TestCliBase):
    @unittest.skip
    def test_neo4j(self):
        pass

    @unittest.skip
    def test_csv(self):
        test_edge_file = 'myedges.csv'

        with self.runner.isolated_filesystem():
            abs_test_edge_file = os.path.abspath(test_edge_file)
            result = self.runner.invoke(cli.main,
                                        ['to_csv', '--path', self.test_path, '--edge-path', abs_test_edge_file])
            log.info('File paths: {}'.format(abs_test_edge_file))
            self.assertEqual(0, result.exit_code, msg=result.exc_info)
            self.assertTrue(os.path.exists(abs_test_edge_file))

            with open(abs_test_edge_file) as f:
                loaded = json.load(f)
                self.assertIsNotNone(loaded)
