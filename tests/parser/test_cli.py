import unittest

from click.testing import CliRunner


# from pybel.cli import main
# TODO add CLI tests

class TestCli(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
