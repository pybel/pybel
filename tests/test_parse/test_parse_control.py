# -*- coding: utf-8 -*-

import logging
import re
import unittest

from pybel.constants import (
    ANNOTATIONS, CITATION, CITATION_AUTHORS, CITATION_COMMENTS, CITATION_DATE, CITATION_NAME,
    CITATION_REFERENCE, CITATION_TYPE, EVIDENCE,
)
from pybel.parser import ControlParser
from pybel.parser.exc import (
    CitationTooLongException, CitationTooShortException, IllegalAnnotationValueWarning, InvalidCitationType,
    InvalidPubMedIdentifierWarning, MissingAnnotationKeyWarning, MissingAnnotationRegexWarning,
    UndefinedAnnotationWarning,
)
from pybel.parser.parse_control import set_citation_stub
from tests.constants import SET_CITATION_TEST, test_citation_dict

logging.getLogger("requests").setLevel(logging.WARNING)


class TestParseControl(unittest.TestCase):
    def setUp(self):
        self.annotation_to_term = {
            'Custom1': {'Custom1_A', 'Custom1_B'},
            'Custom2': {'Custom2_A', 'Custom2_B'}
        }

        self.annotation_to_pattern = {
            'CustomRegex': re.compile('[0-9]+')
        }

        self.parser = ControlParser(
            annotation_to_term=self.annotation_to_term,
            annotation_to_pattern=self.annotation_to_pattern,
        )


class TestParseControlUnsetStatementErrors(TestParseControl):
    def test_unset_missing_evidence(self):
        with self.assertRaises(MissingAnnotationKeyWarning):
            self.parser.parseString('UNSET Evidence')

    def test_unset_missing_citation(self):
        with self.assertRaises(MissingAnnotationKeyWarning):
            self.parser.parseString('UNSET Citation')

    def test_unset_missing_evidence_with_citation(self):
        """Tests that an evidence can't be unset without a citation"""
        s = [SET_CITATION_TEST, 'UNSET Evidence']
        with self.assertRaises(MissingAnnotationKeyWarning):
            self.parser.parse_lines(s)

    def test_unset_missing_statement_group(self):
        with self.assertRaises(MissingAnnotationKeyWarning):
            self.parser.parseString('UNSET STATEMENT_GROUP')

    def test_unset_missing_command(self):
        s = [
            SET_CITATION_TEST,
            'UNSET Custom1'
        ]
        with self.assertRaises(MissingAnnotationKeyWarning):
            self.parser.parse_lines(s)

    def test_unset_invalid_command(self):
        s = [
            SET_CITATION_TEST,
            'UNSET MISSING'
        ]
        with self.assertRaises(UndefinedAnnotationWarning):
            self.parser.parse_lines(s)

    def test_unset_list_compact(self):
        """Tests unsetting an annotation list, without spaces in it"""
        s = [
            SET_CITATION_TEST,
            'SET Custom1 = "Custom1_A"',
            'SET Custom2 = "Custom2_A"',
        ]
        self.parser.parse_lines(s)
        self.assertIn('Custom1', self.parser.annotations)
        self.assertIn('Custom2', self.parser.annotations)
        self.parser.parseString('UNSET {Custom1,Custom2}')
        self.assertFalse(self.parser.annotations)

    def test_unset_list_spaced(self):
        """Tests unsetting an annotation list, with spaces in it"""
        s = [
            SET_CITATION_TEST,
            'SET Custom1 = "Custom1_A"',
            'SET Custom2 = "Custom2_A"',
        ]
        self.parser.parse_lines(s)
        self.assertIn('Custom1', self.parser.annotations)
        self.assertIn('Custom2', self.parser.annotations)
        self.parser.parseString('UNSET {Custom1, Custom2}')
        self.assertFalse(self.parser.annotations)


class TestSetCitation(unittest.TestCase):
    def test_parser_double(self):
        set_citation_stub.parseString('Citation = {"PubMed","12928037"}')

    def test_parser_double_spaced(self):
        set_citation_stub.parseString('Citation = {"PubMed", "12928037"}')

    def test_parser_triple(self):
        set_citation_stub.parseString('Citation = {"PubMedCentral","Trends in molecular medicine","12928037"}')

    def test_parser_triple_spaced(self):
        set_citation_stub.parseString('Citation = {"PubMedCentral", "Trends in molecular medicine", "12928037"}')


class TestParseControlSetStatementErrors(TestParseControl):
    def test_invalid_citation_type(self):
        with self.assertRaises(InvalidCitationType):
            self.parser.parseString('SET Citation = {"PubMedCentral","Trends in molecular medicine","12928037"}')

    def test_invalid_pmid(self):
        with self.assertRaises(InvalidPubMedIdentifierWarning):
            self.parser.parseString('SET Citation = {"PubMed","Trends in molecular medicine","NOT VALID NUMBER"}')

    def test_invalid_pmid_short(self):
        with self.assertRaises(InvalidPubMedIdentifierWarning):
            self.parser.parseString('SET Citation = {"PubMed","NOT VALID NUMBER"}')

    def test_set_missing_statement(self):
        statements = [
            SET_CITATION_TEST,
            'SET MissingKey = "lol"'
        ]
        with self.assertRaises(UndefinedAnnotationWarning):
            self.parser.parse_lines(statements)

    def test_custom_annotation_list_withInvalid(self):
        statements = [
            SET_CITATION_TEST,
            'SET Custom1 = {"Custom1_A","Custom1_B","Evil invalid!!!"}'
        ]

        with self.assertRaises(IllegalAnnotationValueWarning):
            self.parser.parse_lines(statements)

    def test_custom_value_failure(self):
        """Tests what happens for a valid annotation key, but an invalid value"""
        s = [
            SET_CITATION_TEST,
            'SET Custom1 = "Custom1_C"'
        ]
        with self.assertRaises(IllegalAnnotationValueWarning):
            self.parser.parse_lines(s)

    def test_regex_failure(self):
        s = [
            SET_CITATION_TEST,
            'SET CustomRegex = "abce13"'
        ]
        with self.assertRaises(MissingAnnotationRegexWarning):
            self.parser.parse_lines(s)


class TestParseControl2(TestParseControl):
    def test_set_statement_group(self):
        """Tests a statement group gets set properly"""
        s1 = 'SET STATEMENT_GROUP = "my group"'

        self.assertIsNone(self.parser.statement_group)

        self.parser.parseString(s1)
        self.assertEqual('my group', self.parser.statement_group, msg='problem with integration')

        s2 = 'UNSET STATEMENT_GROUP'
        self.parser.parseString(s2)
        self.assertIsNone(self.parser.statement_group, msg='problem with unset')

    def test_citation_short(self):
        self.parser.parseString(SET_CITATION_TEST)
        self.assertEqual(test_citation_dict, self.parser.citation)

        expected_annotations = {
            EVIDENCE: None,
            ANNOTATIONS: {},
            CITATION: test_citation_dict
        }
        self.assertEqual(expected_annotations, self.parser.get_annotations())

        self.parser.parseString('UNSET Citation')
        self.assertEqual(0, len(self.parser.citation))

    def test_citation_invalid_date(self):
        s = 'SET Citation = {"PubMed","Trends in molecular medicine","12928037","01-12-1999","de Nigris"}'

        self.parser.parseString(s)

        expected_citation = {
            CITATION_TYPE: 'PubMed',
            CITATION_NAME: 'Trends in molecular medicine',
            CITATION_REFERENCE: '12928037',
        }

        self.assertEqual(expected_citation, self.parser.citation)

        expected_dict = {
            EVIDENCE: None,
            ANNOTATIONS: {},
            CITATION: expected_citation
        }

        self.assertEqual(expected_dict, self.parser.get_annotations())

    def test_citation_with_empty_comment(self):
        s = 'SET Citation = {"PubMed","Test Name","12928037","1999-01-01","de Nigris|Lerman A|Ignarro LJ",""}'

        self.parser.parseString(s)

        expected_citation = {
            CITATION_TYPE: 'PubMed',
            CITATION_NAME: 'Test Name',
            CITATION_REFERENCE: '12928037',
            CITATION_DATE: '1999-01-01',
            CITATION_AUTHORS: ['de Nigris', 'Lerman A', 'Ignarro LJ'],
            CITATION_COMMENTS: ''
        }

        self.assertEqual(expected_citation, self.parser.citation)

        expected_dict = {
            EVIDENCE: None,
            ANNOTATIONS: {},
            CITATION: expected_citation
        }

        self.assertEqual(expected_dict, self.parser.get_annotations())

    def test_double(self):
        s = 'SET Citation = {"PubMed","12928037"}'
        self.parser.parseString(s)

        expected_citation = {
            CITATION_TYPE: 'PubMed',
            CITATION_REFERENCE: '12928037',
        }
        self.assertEqual(expected_citation, self.parser.citation)

    def test_double_with_space(self):
        """Same as test_double, but has a space between the comma and next entry"""
        s = 'SET Citation = {"PubMed", "12928037"}'
        self.parser.parseString(s)

        expected_citation = {
            CITATION_TYPE: 'PubMed',
            CITATION_REFERENCE: '12928037',
        }
        self.assertEqual(expected_citation, self.parser.citation)

    def test_citation_too_short(self):
        s = 'SET Citation = {"PubMed"}'
        with self.assertRaises(CitationTooShortException):
            self.parser.parseString(s)

    def test_citation_too_long(self):
        s = 'SET Citation = {"PubMed","Name","1234","1999-01-01","Nope|Noper","Nope", "nope nope"}'
        with self.assertRaises(CitationTooLongException):
            self.parser.parseString(s)

    def test_evidence(self):
        s = 'SET Evidence = "For instance, during 7-ketocholesterol-induced apoptosis of U937 cells"'
        self.parser.parseString(s)

        self.assertIsNotNone(self.parser.evidence)

        expected_annotation = {
            CITATION: {},
            ANNOTATIONS: {},
            EVIDENCE: 'For instance, during 7-ketocholesterol-induced apoptosis of U937 cells'
        }

        self.assertEqual(expected_annotation, self.parser.get_annotations())

    def test_custom_annotation(self):
        s = [
            SET_CITATION_TEST,
            'SET Custom1 = "Custom1_A"'
        ]
        self.parser.parse_lines(s)

        expected_annotation = {
            'Custom1': 'Custom1_A'
        }

        self.assertEqual(expected_annotation, self.parser.annotations)

    def test_custom_annotation_list(self):
        s = [
            SET_CITATION_TEST,
            'SET Custom1 = {"Custom1_A","Custom1_B"}'
        ]
        self.parser.parse_lines(s)

        expected_annotation = {
            'Custom1': {'Custom1_A', 'Custom1_B'}
        }

        self.assertEqual(expected_annotation, self.parser.annotations)

        expected_dict = {
            ANNOTATIONS: expected_annotation,
            CITATION: test_citation_dict,
            EVIDENCE: None
        }

        self.assertEqual(expected_dict, self.parser.get_annotations())

    def test_overwrite_evidence(self):
        s1 = 'SET Evidence = "a"'
        s2 = 'SET Evidence = "b"'

        self.parser.parseString(s1)
        self.parser.parseString(s2)

        self.assertEqual('b', self.parser.evidence)

    def test_unset_evidence(self):
        s1 = 'SET Evidence = "a"'
        s2 = 'UNSET Evidence'

        self.parser.parseString(s1)
        self.parser.parseString(s2)

        self.assertEqual({}, self.parser.annotations)

    def test_unset_custom(self):
        statements = [
            SET_CITATION_TEST,
            'SET Custom1 = "Custom1_A"',
            'UNSET Custom1'
        ]

        self.parser.parse_lines(statements)

        self.assertEqual({}, self.parser.annotations)

    def test_reset_citation(self):
        s1 = 'SET Citation = {"PubMed","Test Reference 1","11111"}'
        s2 = 'SET Evidence = "d"'

        s3 = 'SET Citation = {"PubMed","Test Reference 2","22222"}'
        s4 = 'SET Evidence = "h"'
        s5 = 'SET Custom1 = "Custom1_A"'
        s6 = 'SET Custom2 = "Custom2_A"'

        statements = [s1, s2, s3, s4, s5, s6]

        self.parser.parse_lines(statements)

        self.assertEqual('h', self.parser.evidence)
        self.assertEqual('PubMed', self.parser.citation[CITATION_TYPE])
        self.assertEqual('Test Reference 2', self.parser.citation[CITATION_NAME])
        self.assertEqual('22222', self.parser.citation[CITATION_REFERENCE])

        self.parser.parseString('UNSET {Custom1,Evidence}')
        self.assertNotIn('Custom1', self.parser.annotations)
        self.assertIsNone(self.parser.evidence)
        self.assertIn('Custom2', self.parser.annotations)
        self.assertNotEqual(0, len(self.parser.citation))

        self.parser.parseString('UNSET ALL')
        self.assertEqual(0, len(self.parser.annotations))
        self.assertEqual(0, len(self.parser.citation))

    def test_set_regex(self):
        s = [
            SET_CITATION_TEST,
            'SET CustomRegex = "1234"'
        ]
        self.parser.parse_lines(s)

        self.assertEqual('1234', self.parser.annotations['CustomRegex'])
