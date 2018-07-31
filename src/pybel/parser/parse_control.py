# -*- coding: utf-8 -*-

"""
Control Parser
~~~~~~~~~~~~~~
This module handles parsing control statement, which add annotations and namespaces to the document.

.. see also::

    https://wiki.openbel.org/display/BLD/Control+Records
"""

import logging
import re

from pyparsing import And, MatchFirst, Suppress, oneOf, pyparsing_common as ppc

from .baseparser import BaseParser
from .exc import (
    CitationTooLongException, CitationTooShortException, IllegalAnnotationValueWarning, InvalidCitationType,
    InvalidPubMedIdentifierWarning, MissingAnnotationKeyWarning, MissingAnnotationRegexWarning,
    MissingCitationException, UndefinedAnnotationWarning,
)
from .utils import delimited_quoted_list, delimited_unquoted_list, is_int, qid, quote
from ..constants import (
    ANNOTATIONS, BEL_KEYWORD_ALL, BEL_KEYWORD_CITATION, BEL_KEYWORD_EVIDENCE, BEL_KEYWORD_SET,
    BEL_KEYWORD_STATEMENT_GROUP, BEL_KEYWORD_SUPPORT, BEL_KEYWORD_UNSET, CITATION, CITATION_ENTRIES, CITATION_REFERENCE,
    CITATION_TYPE, CITATION_TYPES, CITATION_TYPE_PUBMED, EVIDENCE,
)
from ..utils import valid_date

__all__ = ['ControlParser']

log = logging.getLogger(__name__)

set_tag = Suppress(BEL_KEYWORD_SET)
unset_tag = Suppress(BEL_KEYWORD_UNSET)
unset_all = Suppress(BEL_KEYWORD_ALL)

supporting_text_tags = oneOf([BEL_KEYWORD_EVIDENCE, BEL_KEYWORD_SUPPORT])

set_statement_group_stub = And([Suppress(BEL_KEYWORD_STATEMENT_GROUP), Suppress('='), qid('group')])
set_citation_stub = And([Suppress(BEL_KEYWORD_CITATION), Suppress('='), delimited_quoted_list('values')])
set_evidence_stub = And([Suppress(supporting_text_tags), Suppress('='), quote('value')])


class ControlParser(BaseParser):
    """A parser for BEL control statements.

    .. seealso::

        BEL 1.0 specification on `control records <http://openbel.org/language/version_1.0/bel_specification_version_1.0.html#_control_records>`_
    """

    def __init__(self, annotation_dict=None, annotation_regex=None, citation_clearing=True, required_annotations=None):
        """
        :param annotation_dict: A dictionary of {annotation: set of valid values} for parsing
        :type annotation_dict: Optional[dict[str,set[str]]]
        :param annotation_regex: A dictionary of {annotation: regular expression string}
        :type annotation_regex: Optional[dict[str,str]]
        :param bool citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
        :param Optional[list[str]] required_annotations: Annotations that are required
        """
        self.citation_clearing = citation_clearing

        self._annotation_dict = {} if annotation_dict is None else annotation_dict
        self._annotation_regex = {} if annotation_regex is None else annotation_regex
        self._annotation_regex_compiled = {
            keyword: re.compile(value)
            for keyword, value in self.annotation_regex.items()
        }

        self.statement_group = None
        self.citation = {}
        self.evidence = None
        self.annotations = {}
        self.required_annotations = required_annotations or []

        annotation_key = ppc.identifier('key').setParseAction(self.handle_annotation_key)

        self.set_statement_group = set_statement_group_stub().setParseAction(self.handle_set_statement_group)
        self.set_citation = set_citation_stub().setParseAction(self.handle_set_citation)
        self.set_evidence = set_evidence_stub().setParseAction(self.handle_set_evidence)

        set_command_prefix = And([annotation_key('key'), Suppress('=')])
        self.set_command = set_command_prefix + qid('value')
        self.set_command.setParseAction(self.handle_set_command)

        self.set_command_list = set_command_prefix + delimited_quoted_list('values')
        self.set_command_list.setParseAction(self.handle_set_command_list)

        self.unset_command = annotation_key('key')
        self.unset_command.addParseAction(self.handle_unset_command)

        self.unset_evidence = supporting_text_tags(EVIDENCE)
        self.unset_evidence.setParseAction(self.handle_unset_evidence)

        self.unset_citation = Suppress(BEL_KEYWORD_CITATION)
        self.unset_citation.setParseAction(self.handle_unset_citation)

        self.unset_statement_group = Suppress(BEL_KEYWORD_STATEMENT_GROUP)
        self.unset_statement_group.setParseAction(self.handle_unset_statement_group)

        self.unset_list = delimited_unquoted_list('values')
        self.unset_list.setParseAction(self.handle_unset_list)

        self.unset_all = unset_all.setParseAction(self.handle_unset_all)

        self.set_statements = set_tag + MatchFirst([
            self.set_statement_group,
            self.set_citation,
            self.set_evidence,
            self.set_command,
            self.set_command_list,
        ])

        self.unset_statements = unset_tag + MatchFirst([
            self.unset_all,
            self.unset_citation,
            self.unset_evidence,
            self.unset_statement_group,
            self.unset_command,
            self.unset_list
        ])

        self.language = self.set_statements | self.unset_statements

        super(ControlParser, self).__init__(self.language)

    @property
    def annotation_dict(self):
        """A dictionary of annotaions to their set of values

        :rtype: dict[str,set[str]]
        """
        return self._annotation_dict

    @property
    def annotation_regex(self):
        """A dictioary of annotations defined by regular expressions {annotation keyword: string regular expression}

        :return: dict[str,str]
        """
        return self._annotation_regex

    @property
    def annotation_regex_compiled(self):
        """A dictionary of annotations defined by regular expressions {annotation keyword: compiled regular expression}

        :rtype: dict[str,re]
        """
        return self._annotation_regex_compiled

    @property
    def _in_debug_mode(self):
        return not self.annotation_dict and not self.annotation_regex

    def has_enumerated_annotation(self, annotation):
        return annotation in self.annotation_dict

    def has_regex_annotation(self, annotation):
        return annotation in self.annotation_regex

    def raise_for_undefined_annotation(self, line, position, annotation):
        """Raises is an annotation is not defined

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param str annotation: The annotation to check
        :raises: UndefinedAnnotationWarning
        """
        if self._in_debug_mode:
            return

        if not self.has_enumerated_annotation(annotation) and not self.has_regex_annotation(annotation):
            raise UndefinedAnnotationWarning(self.line_number, line, position, annotation)

    def raise_for_invalid_annotation_value(self, line, position, key, value):
        """Raises is an annotation is not defined

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param str key: The annotation to check
        :param str value: The entry in the annotation to check
        :raises: IllegalAnnotationValueWarning or MissingAnnotationRegexWarning
        """
        if self._in_debug_mode:
            return

        if self.has_enumerated_annotation(key) and value not in self.annotation_dict[key]:
            raise IllegalAnnotationValueWarning(self.line_number, line, position, key, value)

        elif self.has_regex_annotation(key) and not self.annotation_regex_compiled[key].match(value):
            raise MissingAnnotationRegexWarning(self.line_number, line, position, key, value)

    def raise_for_missing_citation(self, line, position):
        """Raises if there is no citation present in the parser

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :raises: MissingCitationException
        """
        if self.citation_clearing and not self.citation:
            raise MissingCitationException(self.line_number, line, position)

    def handle_annotation_key(self, line, position, tokens):
        """Called on all annotation keys before parsing to validate that it's either enumerated or as a regex

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        :raise: MissingCitationException or UndefinedAnnotationWarning
        """
        key = tokens['key']
        self.raise_for_missing_citation(line, position)
        self.raise_for_undefined_annotation(line, position, key)
        return tokens

    def handle_set_statement_group(self, line, position, tokens):
        self.statement_group = tokens['group']
        return tokens

    def handle_set_citation(self, line, position, tokens):
        self.clear_citation()

        values = tokens['values']

        if len(values) < 2:
            raise CitationTooShortException(self.line_number, line, position)

        citation_type = values[0]

        if citation_type not in CITATION_TYPES:
            raise InvalidCitationType(self.line_number, line, position, citation_type)

        if 2 == len(values):
            return self.handle_set_citation_double(line, position, tokens)

        citation_reference = values[2]

        if citation_type == CITATION_TYPE_PUBMED and not is_int(citation_reference):
            raise InvalidPubMedIdentifierWarning(self.line_number, line, position, citation_reference)

        if 4 <= len(values) and not valid_date(values[3]):
            log.debug('Invalid date: %s. Truncating entry.', values[3])
            self.citation = dict(zip(CITATION_ENTRIES, values[:3]))
            return tokens

        # TODO consider parsing up authors list

        if 6 < len(values):
            raise CitationTooLongException(self.line_number, line, position)

        self.citation = dict(zip(CITATION_ENTRIES, values))

        return tokens

    def handle_set_citation_double(self, line, position, tokens):
        values = tokens['values']

        if values[0] == CITATION_TYPE_PUBMED and not is_int(values[1]):
            raise InvalidPubMedIdentifierWarning(self.line_number, line, position, values[1])

        self.citation = dict(zip((CITATION_TYPE, CITATION_REFERENCE), values))

        return tokens

    def handle_set_evidence(self, line, position, tokens):
        self.evidence = tokens['value']
        return tokens

    def handle_set_command(self, line, position, tokens):
        key = tokens['key']
        value = tokens['value']

        self.raise_for_invalid_annotation_value(line, position, key, value)

        self.annotations[key] = value
        return tokens

    def handle_set_command_list(self, line, position, tokens):
        key = tokens['key']
        values = tokens['values']

        for value in values:
            self.raise_for_invalid_annotation_value(line, position, key, value)

        self.annotations[key] = set(values)
        return tokens

    def handle_unset_statement_group(self, line, position, tokens):
        """Unsets the statement group, or raises an exception if it is not set.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        :raises: MissingAnnotationKeyWarning
        """
        if self.statement_group is None:
            raise MissingAnnotationKeyWarning(self.line_number, line, position, BEL_KEYWORD_STATEMENT_GROUP)
        self.statement_group = None
        return tokens

    def handle_unset_citation(self, line, position, tokens):
        """Unsets the citation, or raises an exception if it is not set

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        :raises: MissingAnnotationKeyWarning
        """
        if not self.citation:
            raise MissingAnnotationKeyWarning(self.line_number, line, position, BEL_KEYWORD_CITATION)

        self.clear_citation()

        return tokens

    def handle_unset_evidence(self, line, position, tokens):
        """Unsets the evidence, or throws an exception if it is not already set. The value for ``tokens[EVIDENCE]``
        corresponds to which alternate of SupportingText or Evidence was used in the BEL script.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        :raises: MissingAnnotationKeyWarning
        """
        if self.evidence is None:
            raise MissingAnnotationKeyWarning(self.line_number, line, position, tokens[EVIDENCE])
        self.evidence = None
        return tokens

    def validate_unset_command(self, line, position, key):
        """Raises an exception when trying to ``UNSET X`` if ``X`` is not already set.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param str key: The annotation to check
        :raises: MissingAnnotationKeyWarning
        """
        if key not in self.annotations:
            raise MissingAnnotationKeyWarning(self.line_number, line, position, key)

    def handle_unset_command(self, line, position, tokens):
        """Handles ``UNSET X`` or raises an exception if it is not already set.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        :raises: MissingAnnotationKeyWarning
        """
        key = tokens['key']
        self.validate_unset_command(line, position, key)
        del self.annotations[key]
        return tokens

    def handle_unset_list(self, line, position, tokens):
        """Handles ``UNSET {A, B, ...}`` or raises an exception of any of them are not present. Consider that all
        unsets are in peril if just one of them is wrong!

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        :raises: MissingAnnotationKeyWarning
        """
        for key in tokens['values']:
            if key in {BEL_KEYWORD_EVIDENCE, BEL_KEYWORD_SUPPORT}:
                self.evidence = None
            else:
                self.validate_unset_command(line, position, key)
                del self.annotations[key]

        return tokens

    def handle_unset_all(self, line, position, tokens):
        """Handles ``UNSET_ALL``"""
        self.clear()
        return tokens

    def get_annotations(self):
        """Gets the current annotations

        :return: The currently stored BEL annotations
        :rtype: dict
        """
        return {
            EVIDENCE: self.evidence,
            CITATION: self.citation.copy(),
            ANNOTATIONS: self.annotations.copy()
        }

    def get_missing_required_annotations(self):
        """Return missing required annotations.

        :rtype: list[str]
        """
        return [
            required_annotation
            for required_annotation in self.required_annotations
            if required_annotation not in self.annotations
        ]

    def clear_citation(self):
        """Clears the citation. Additionally, if citation clearing is enabled, clears the evidence and annotations."""
        self.citation.clear()

        if self.citation_clearing:
            self.evidence = None
            self.annotations.clear()

    def clear(self):
        """Clears the statement_group, citation, evidence, and annotations"""
        self.statement_group = None
        self.citation.clear()
        self.evidence = None
        self.annotations.clear()
