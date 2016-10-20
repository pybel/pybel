import logging
import os
import unittest

from pybel.exceptions import NamespaceMismatch, AnnotationMismatch
from pybel.parser import ControlParser, MetadataParser
from pybel.parser.parse_exceptions import *
from pybel.parser.utils import sanitize_file_lines, split_file_to_annotations_and_definitions

logging.getLogger("requests").setLevel(logging.WARNING)

dir_path = os.path.dirname(os.path.realpath(__file__))





class TestSplitLines(unittest.TestCase):
    def test_parts(self):
        path = os.path.join(dir_path, 'bel', 'test_bel_1.bel')

        with open(path) as f:
            docs, defs, states = split_file_to_annotations_and_definitions(f)

        self.assertEqual(7, len(docs))
        self.assertEqual(5, len(defs))
        self.assertEqual(14, len(states))


class TestParseMetadata(unittest.TestCase):
    def setUp(self):
        self.parser = MetadataParser()

    def test_control_1(self):
        s = 'DEFINE NAMESPACE MGI AS URL "http://resource.belframework.org/belframework/1.0/namespace/mgi-approved-symbols.belns"'

        self.parser.parseString(s)
        self.assertIn('MGI', self.parser.namespace_dict)
        self.assertIn('MGI', self.parser.namespace_metadata)

        # Test doesn't overwrite
        s = 'DEFINE NAMESPACE MGI AS LIST {"A","B","C"}'
        self.parser.parseString(s)
        self.assertIn('MGI', self.parser.namespace_dict)
        self.assertIn('MGI', self.parser.namespace_metadata)
        self.assertNotIn('A', self.parser.namespace_dict['MGI'])

    def test_control_2(self):
        s = 'DEFINE NAMESPACE Custom1 AS LIST {"A","B","C"}'
        self.parser.parseString(s)
        self.assertIn('Custom1', self.parser.namespace_dict)

        s = 'DEFINE NAMESPACE Custom1 AS URL "http://resource.belframework.org/belframework/1.0/namespace/mgi-approved-symbols.belns"'
        self.parser.parseString(s)
        self.assertIn('Custom1', self.parser.namespace_dict)
        self.assertIn('A', self.parser.namespace_dict['Custom1'])

    @unittest.skip('Future versions may not be so relaxed')
    def test_control_annotation_lexicographyException(self):
        s = 'DEFINE ANNOTATION CELLSTRUCTURE AS URL "http://resource.belframework.org/belframework/1.0/annotation/mesh-cell-structure.belanno"'
        with self.assertRaises(LexicographyException):
            self.parser.parseString(s)

    @unittest.skip('Future versions may not be so relaxed')
    def test_control_namespace_lexicographyException(self):
        s = 'DEFINE NAMESPACE mgi AS URL "http://resource.belframework.org/belframework/1.0/namespace/mgi-approved-symbols.belns"'
        with self.assertRaises(LexicographyException):
            self.parser.parseString(s)

    def test_control_3(self):
        s = 'DEFINE ANNOTATION CellStructure AS URL "http://resource.belframework.org/belframework/1.0/annotation/mesh-cell-structure.belanno"'
        self.parser.parseString(s)
        self.assertIn('CellStructure', self.parser.annotations_dict)
        self.assertIn('CellStructure', self.parser.annotations_metadata)

        s = 'DEFINE ANNOTATION CellStructure AS LIST {"A","B","C"}'
        self.parser.parseString(s)
        self.assertIn('CellStructure', self.parser.annotations_dict)
        self.assertIn('CellStructure', self.parser.annotations_metadata)
        self.assertNotIn('A', self.parser.annotations_dict['CellStructure'])

    def test_control_4(self):
        s = 'DEFINE ANNOTATION TextLocation AS LIST {"Abstract","Results","Legend","Review"}'
        self.parser.parseString(s)
        self.assertIn('TextLocation', self.parser.annotations_dict)
        self.assertIn('TextLocation', self.parser.annotations_metadata)

        s = 'DEFINE ANNOTATION TextLocation AS URL "http://resource.belframework.org/belframework/1.0/annotation/mesh-cell-structure.belanno"'
        self.parser.parseString(s)
        self.assertIn('TextLocation', self.parser.annotations_dict)
        self.assertIn('TextLocation', self.parser.annotations_metadata)
        self.assertIn('Abstract', self.parser.annotations_dict['TextLocation'])

    def test_underscore(self):
        s = 'DEFINE ANNOTATION Text_Location AS LIST {"Abstract","Results","Legend","Review"}'
        self.parser.parseString(s)
        self.assertIn('Text_Location', self.parser.annotations_dict)
        self.assertIn('Text_Location', self.parser.annotations_metadata)

    def test_control_compound_1(self):
        s1 = 'DEFINE NAMESPACE MGI AS URL "http://resource.belframework.org/belframework/1.0/namespace/mgi-approved-symbols.belns"'
        s2 = 'DEFINE NAMESPACE CHEBI AS URL "http://resource.belframework.org/belframework/1.0/namespace/chebi-names.belns"'

        self.parser.parse_lines([s1, s2])

        self.assertIn('MGI', self.parser.namespace_dict)
        self.assertIn('CHEBI', self.parser.namespace_dict)

    def test_control_compound_2(self):
        s1 = 'DEFINE ANNOTATION CellStructure AS  URL "http://resource.belframework.org/belframework/1.0/annotation/mesh-cell-structure.belanno"'
        s2 = 'DEFINE ANNOTATION CellLine AS  URL "http://resource.belframework.org/belframework/1.0/annotation/atcc-cell-line.belanno"'
        s3 = 'DEFINE ANNOTATION TextLocation AS  LIST {"Abstract","Results","Legend","Review"}'
        self.parser.parse_lines([s1, s2, s3])

        self.assertIn('CellStructure', self.parser.annotations_dict)
        self.assertIn('CellLine', self.parser.annotations_dict)
        self.assertIn('TextLocation', self.parser.annotations_dict)

    def test_parse_document(self):
        s = '''SET DOCUMENT Name = "Alzheimer's Disease Model"'''

        self.parser.parseString(s)

        self.assertIn('Name', self.parser.document_metadata)
        self.assertEqual("Alzheimer's Disease Model", self.parser.document_metadata['Name'])

    def test_parse_namespace_list_1(self):
        s = '''DEFINE NAMESPACE BRCO AS LIST {"Hippocampus", "Parietal Lobe"}'''

        self.parser.parseString(s)

        expected_namespace_dict = {
            'BRCO': {'Hippocampus', 'Parietal Lobe'}
        }

        self.assertIn('BRCO', self.parser.namespace_dict)
        self.assertEqual(2, len(self.parser.namespace_dict['BRCO']))
        self.assertEqual(expected_namespace_dict, self.parser.namespace_dict)

    def test_parse_namespace_list_2(self):
        s1 = '''SET DOCUMENT Name = "Alzheimer's Disease Model"'''
        s2 = '''DEFINE NAMESPACE BRCO AS LIST {"Hippocampus", "Parietal Lobe"}'''

        self.parser.parseString(s1)
        self.parser.parseString(s2)

        expected_namespace_dict = {
            'BRCO': {'Hippocampus', 'Parietal Lobe'}
        }

        expected_namespace_annoations = {
        }

        self.assertIn('BRCO', self.parser.namespace_dict)
        self.assertEqual(2, len(self.parser.namespace_dict['BRCO']))
        self.assertEqual(expected_namespace_dict, self.parser.namespace_dict)
        self.assertEqual(expected_namespace_annoations, self.parser.namespace_metadata)

    @unittest.skip('Future versions may not be so relaxed')
    def test_parse_namespace_url_mismatch(self):
        path = os.path.join(dir_path, 'bel', 'test_ns_1.belns')
        s = '''DEFINE NAMESPACE TEST AS URL "file://{}"'''.format(path)

        with self.assertRaises(NamespaceMismatch):
            self.parser.parseString(s)

    def test_parse_namespace_url_1(self):
        path = os.path.join(dir_path, 'bel', 'test_ns_1.belns')
        s = '''DEFINE NAMESPACE TESTNS1 AS URL "file://{}"'''.format(path)
        self.parser.parseString(s)

        expected_values = {
            'TestValue1': 'O',
            'TestValue2': 'O',
            'TestValue3': 'O',
            'TestValue4': 'O',
            'TestValue5': 'O'
        }

        self.assertIn('TESTNS1', self.parser.namespace_dict)
        self.assertEqual(expected_values, self.parser.namespace_dict['TESTNS1'])

    def test_parse_annotation_url_1(self):
        path = os.path.join(dir_path, 'bel', 'test_an_1.belanno')
        s = '''DEFINE ANNOTATION TESTAN1 AS URL "file://{}"'''.format(path)
        self.parser.parseString(s)

        expected_values = {
            'TestAnnot1': 'O',
            'TestAnnot2': 'O',
            'TestAnnot3': 'O',
            'TestAnnot4': 'O',
            'TestAnnot5': 'O'
        }

        self.assertIn('TESTAN1', self.parser.annotations_dict)
        self.assertEqual(expected_values, self.parser.annotations_dict['TESTAN1'])

    @unittest.skip('Future versions may not be so relaxed')
    def test_parse_annotation_url_failure(self):
        path = os.path.join(dir_path, 'bel', 'test_an_1.belanno')
        s = '''DEFINE ANNOTATION Test AS URL "file://{}"'''.format(path)

        with self.assertRaises(AnnotationMismatch):
            self.parser.parseString(s)

    def test_parse_pattern(self):
        s = 'DEFINE ANNOTATION Test AS PATTERN "\w+"'
        with self.assertRaises(NotImplementedError):
            self.parser.parseString(s)


class TestParseControl(unittest.TestCase):
    def setUp(self):
        custom_annotations = {
            'Custom1': {'Custom1_A', 'Custom1_B'},
            'Custom2': {'Custom2_A', 'Custom2_B'}
        }

        self.parser = ControlParser(valid_annotations=custom_annotations)

    def test_set_statement_group(self):
        s = 'SET STATEMENT_GROUP = "my group"'

        self.assertIsNotNone(self.parser.set_statement_group.parseString(s))

        self.parser.parseString(s)
        self.assertEqual('my group', self.parser.statement_group)

        s = 'UNSET STATEMENT_GROUP'
        self.parser.parseString(s)
        self.assertIsNone(self.parser.statement_group)

    def test_unset_missing_evidence(self):
        s = 'UNSET Evidence'
        self.parser.parseString(s)

    def test_unset_missing_command(self):
        s = 'UNSET Custom1'
        with self.assertRaises(MissingAnnotationKeyException):
            self.parser.parseString(s)

    def test_unset_invalid_command(self):
        s = 'UNSET Custom3'
        with self.assertRaises(InvalidAnnotationKeyException):
            self.parser.parseString(s)

    def test_unset_missing_citation(self):
        s = 'UNSET Citation'
        self.parser.parseString(s)

    def test_set_missing_statement(self):
        s = 'SET MissingKey = "lol"'
        with self.assertRaises(InvalidAnnotationKeyException):
            self.parser.parseString(s)

    def test_citation_short(self):
        s = 'SET Citation = {"PubMed","Trends in molecular medicine","12928037"}'

        self.parser.parseString(s)

        expected_citation = {
            'type': 'PubMed',
            'name': 'Trends in molecular medicine',
            'reference': '12928037',
        }

        self.assertEqual(expected_citation, self.parser.citation)

        annotations = self.parser.get_annotations()
        expected_annotations = {
            'citation_type': 'PubMed',
            'citation_name': 'Trends in molecular medicine',
            'citation_reference': '12928037'
        }
        self.assertEqual(expected_annotations, annotations)

        self.parser.parseString('UNSET Citation')
        self.assertEqual(0, len(self.parser.citation))

    def test_citation_long(self):
        s = 'SET Citation = {"PubMed","Trends in molecular medicine","12928037","","de Nigris|Lerman A|Ignarro LJ",""}'

        self.parser.parseString(s)

        expected_citation = {
            'type': 'PubMed',
            'name': 'Trends in molecular medicine',
            'reference': '12928037',
            'date': '',
            'authors': 'de Nigris|Lerman A|Ignarro LJ',
            'comments': ''
        }

        self.assertEqual(expected_citation, self.parser.citation)

    def test_citation_error(self):
        s = 'SET Citation = {"PubMed","Trends in molecular medicine"}'
        with self.assertRaises(Exception):
            self.parser.parseString(s)

    def test_evidence(self):
        s = 'SET Evidence = "For instance, during 7-ketocholesterol-induced apoptosis of U937 cells"'
        self.parser.parseString(s)

        expected_annotation = {
            'Evidence': 'For instance, during 7-ketocholesterol-induced apoptosis of U937 cells'
        }

        self.assertEqual(expected_annotation, self.parser.annotations)

    def test_custom_annotation(self):
        s = 'SET Custom1 = "Custom1_A"'
        self.parser.parseString(s)

        expected_annotation = {
            'Custom1': 'Custom1_A'
        }

        self.assertEqual(expected_annotation, self.parser.annotations)

    def test_custom_annotation_list(self):
        s = 'SET Custom1 = {"Custom1_A","Custom1_B"}'
        self.parser.parseString(s)

        expected_annotation = {
            'Custom1': {'Custom1_A', 'Custom1_B'}
        }

        self.assertEqual(expected_annotation, self.parser.annotations)

    def test_custom_annotation_list_withInvalid(self):
        s = 'SET Custom1 = {"Custom1_A","Custom1_B","Evil invalid!!!"}'

        with self.assertRaises(IllegalAnnotationValueExeption):
            self.parser.parseString(s)

    def test_custom_key_failure(self):
        s = 'SET FAILURE = "never gonna happen"'
        with self.assertRaises(Exception):
            self.parser.parseString(s)

    def test_custom_value_failure(self):
        s = 'SET Custom1 = "Custom1_C"'
        with self.assertRaises(Exception):
            self.parser.parseString(s)

    def test_reset_annotation(self):
        s1 = 'SET Evidence = "a"'
        s2 = 'SET Evidence = "b"'

        self.parser.parseString(s1)
        self.parser.parseString(s2)

        self.assertEqual('b', self.parser.annotations['Evidence'])

    def test_unset_evidence(self):
        s1 = 'SET Evidence = "a"'
        s2 = 'UNSET Evidence'

        self.parser.parseString(s1)
        self.parser.parseString(s2)

        self.assertEqual({}, self.parser.annotations)

    def test_unset_custom(self):
        s1 = 'SET Custom1 = "Custom1_A"'
        s2 = 'UNSET Custom1'

        self.parser.parseString(s1)
        self.parser.parseString(s2)

        self.assertEqual({}, self.parser.annotations)

    def test_reset_citation(self):
        s1 = 'SET Citation = {"a","b","c"}'
        s2 = 'SET Evidence = "d"'

        s3 = 'SET Citation = {"e","f","g"}'
        s4 = 'SET Evidence = "h"'

        self.parser.parseString(s1)
        self.parser.parseString(s2)
        self.parser.parseString(s3)
        self.parser.parseString(s4)

        self.assertEqual('h', self.parser.annotations['Evidence'])
        self.assertEqual('e', self.parser.citation['type'])
        self.assertEqual('f', self.parser.citation['name'])
        self.assertEqual('g', self.parser.citation['reference'])


class TestParseEvidence(unittest.TestCase):
    def test_111(self):
        statement = '''SET Evidence = "1.1.1 Easy case"'''
        expect = '''SET Evidence = "1.1.1 Easy case'''
        lines = list(sanitize_file_lines(statement.split('\n')))
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertTrue(expect, line)

    def test_131(self):
        statement = '''SET Evidence = "3.1 Backward slash break test \\
second line"'''
        expect = '''SET Evidence = "3.1 Backward slash break test second line"'''
        lines = [line for i, line in sanitize_file_lines(statement.split('\n'))]
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)

    def test_132(self):
        statement = '''SET Evidence = "3.2 Backward slash break test with whitespace \\
second line"'''
        expect = '''SET Evidence = "3.2 Backward slash break test with whitespace second line"'''
        lines = [line for i, line in sanitize_file_lines(statement.split('\n'))]
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)

    def test_133(self):
        statement = '''SET Evidence = "3.3 Backward slash break test \\
second line \\
third line"'''
        expect = '''SET Evidence = "3.3 Backward slash break test second line third line"'''
        lines = [line for i, line in sanitize_file_lines(statement.split('\n'))]
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)

    def test_141(self):
        statement = '''SET Evidence = "4.1 Malformed line breakcase
second line"'''
        expect = '''SET Evidence = "4.1 Malformed line breakcase second line"'''
        lines = [line for i, line in sanitize_file_lines(statement.split('\n'))]
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)

    def test_142(self):
        statement = '''SET Evidence = "4.2 Malformed line breakcase
second line
third line"'''
        expect = '''SET Evidence = "4.2 Malformed line breakcase second line third line"'''
        lines = [line for i, line in sanitize_file_lines(statement.split('\n'))]
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)
