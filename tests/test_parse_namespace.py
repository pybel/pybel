import unittest

from pybel.parsers.parse_namespace import NamespaceParser


class TestNamespaceParser(unittest.TestCase):
    def setUp(self):
        nsd = {
            'A': {'1', '2', '3'},
            'B': {'4', '5', '6'}
        }

        self.parser = NamespaceParser(namespace_dict=nsd)

    def test_valid_1(self):
        s = 'A:3'
        result = self.parser.parse(s)

        self.assertIn('namespace', result)
        self.assertIn('value', result)
        self.assertEqual('A', result['namespace'])
        self.assertEqual('3', result['value'])

    def test_valid_2(self):
        s = 'A:"3"'
        result = self.parser.parse(s)

        self.assertIn('namespace', result)
        self.assertIn('value', result)
        self.assertEqual('A', result['namespace'])
        self.assertEqual('3', result['value'])

    def test_invalid_1(self):
        s = 'C:4'
        with self.assertRaises(Exception):
            self.parser.parse(s)

    def test_invalid_2(self):
        s = 'A:4'
        with self.assertRaises(Exception):
            self.parser.parse(s)

    def test_invalid_3(self):
        s = 'bare'
        with self.assertRaises(Exception):
            self.parser.parse(s)

    def test_invalid_4(self):
        s = '"quoted"'
        with self.assertRaises(Exception):
            self.parser.parse(s)


class TestNamespaceParserDefault(unittest.TestCase):
    def setUp(self):
        nsd = {
            'A': {'1', '2', '3'},
            'B': {'4', '5', '6'}
        }

        dns = {'X', 'Y', 'W Z'}

        self.parser = NamespaceParser(namespace_dict=nsd, default_namespace=dns)

    def test_valid_1(self):
        s = 'A:3'
        result = self.parser.parse(s)

        self.assertIn('namespace', result)
        self.assertIn('value', result)
        self.assertEqual('A', result['namespace'])
        self.assertEqual('3', result['value'])

    def test_valid_2(self):
        s = 'X'
        result = self.parser.parse(s)

        self.assertIn('value', result)
        self.assertEqual('X', result['value'])

    def test_valid_2(self):
        s = '"W Z"'
        result = self.parser.parse(s)

        self.assertIn('value', result)
        self.assertEqual('W Z', result['value'])



