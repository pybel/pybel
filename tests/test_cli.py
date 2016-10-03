import unittest

from click.testing import CliRunner

from pybel.cli import main


class TestCli(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    # FIXME
    @unittest.skip('Test not ready')
    def test_to_neo(self):
        result = self.runner.invoke(main, ['to_neo', '--path', 'bel/test.bel'])
        self.assertEqual(0, result.exit_code)
