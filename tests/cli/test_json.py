import json
import logging
import os
import unittest

from pybel import cli
from tests.constants import TestCliBase

log = logging.getLogger(__name__)


@unittest.skipIf('TRAVIS_SKIP' in os.environ, 'not enough memory on Travis-CI for this test')
class TestCliJson(TestCliBase):
    def test_json(self):
        test_file = 'mygraph.json'

        with self.runner.isolated_filesystem():
            abs_test_file = os.path.abspath(test_file)
            result = self.runner.invoke(cli.main, ['to_json', '--path', self.test_path, '--output', abs_test_file])
            log.info('File path: {}'.format(abs_test_file))
            self.assertEqual(0, result.exit_code, msg=result.exc_info)
            self.assertTrue(os.path.exists(abs_test_file))

            with open(abs_test_file) as f:
                loaded = json.load(f)
                self.assertIsNotNone(loaded)
