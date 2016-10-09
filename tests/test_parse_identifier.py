import unittest

from pybel.parser.parse_identifier import IdentifierParser


class TestIdentifierParser(unittest.TestCase):
    def setUp(self):
        nsd = {
            'A': {'1', '2', '3'},
            'B': {'4', '5', '6'}
        }

        self.parser = IdentifierParser(namespace_dict=nsd)

    def test_valid_1(self):
        s = 'A:3'
        result = self.parser.parseString(s)

        self.assertIn('namespace', result)
        self.assertIn('name', result)
        self.assertEqual('A', result['namespace'])
        self.assertEqual('3', result['name'])

    def test_valid_2(self):
        s = 'A:"3"'
        result = self.parser.parseString(s)

        self.assertIn('namespace', result)
        self.assertIn('name', result)
        self.assertEqual('A', result['namespace'])
        self.assertEqual('3', result['name'])

    def test_invalid_1(self):
        s = 'C:4'
        with self.assertRaises(Exception):
            self.parser.parseString(s)

    def test_invalid_2(self):
        s = 'A:4'
        with self.assertRaises(Exception):
            self.parser.parseString(s)

    def test_invalid_3(self):
        s = 'bare'
        with self.assertRaises(Exception):
            self.parser.parseString(s)

    def test_invalid_4(self):
        s = '"quoted"'
        with self.assertRaises(Exception):
            self.parser.parseString(s)


class TestNamespaceParserDefault(unittest.TestCase):
    def setUp(self):
        nsd = {
            'A': {'1', '2', '3'},
            'B': {'4', '5', '6'}
        }

        dns = {'X', 'Y', 'W Z'}

        self.parser = IdentifierParser(namespace_dict=nsd, default_namespace=dns)

    def test_valid_1(self):
        s = 'A:3'
        result = self.parser.parseString(s)

        self.assertIn('namespace', result)
        self.assertIn('name', result)
        self.assertEqual('A', result['namespace'])
        self.assertEqual('3', result['name'])

    def test_valid_2(self):
        s = 'X'
        result = self.parser.parseString(s)

        self.assertIn('name', result)
        self.assertEqual('X', result['name'])

    def test_valid_3(self):
        s = '"W Z"'
        result = self.parser.parseString(s)

        self.assertIn('name', result)
        self.assertEqual('W Z', result['name'])



