# -*- coding: utf-8 -*-

"""Control parser.

This module handles parsing control statement, which add annotations and namespaces to the document.

.. see also::

    https://wiki.openbel.org/display/BLD/Control+Records
"""

import logging
from typing import Dict, List, Mapping, Optional, Pattern, Set

from pyparsing import And, MatchFirst, ParseResults, Suppress, oneOf, pyparsing_common as ppc

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

        BEL 1.0 specification on `control records
        <http://openbel.org/language/version_1.0/bel_specification_version_1.0.html#_control_records>`_
    """

    def __init__(self,
                 annotation_to_term: Optional[Mapping[str, Set[str]]] = None,
                 annotation_to_pattern: Optional[Mapping[str, Pattern]] = None,
                 annotation_to_local: Optional[Mapping[str, Set[str]]] = None,
                 citation_clearing: bool = True,
                 required_annotations: Optional[List[str]] = None
                 ) -> None:
        """Initialize the control statement parser.

        :param annotation_to_term: A dictionary of {annotation: set of valid values} defined with URL for parsing
        :param annotation_to_pattern: A dictionary of {annotation: regular expression string}
        :param annotation_to_local: A dictionary of {annotation: set of valid values} for parsing defined with LIST
        :param citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
        :param required_annotations: Annotations that are required
        """
        self.citation_clearing = citation_clearing

        self.annotation_to_term = annotation_to_term or {}
        self.annotation_to_pattern = annotation_to_pattern or {}
        self.annotation_to_local = annotation_to_local or {}

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
    def _in_debug_mode(self) -> bool:
        return not self.annotation_to_term and not self.annotation_to_pattern

    def has_enumerated_annotation(self, annotation: str) -> bool:
        """Check if the annotation is defined as an enumeration."""
        return annotation in self.annotation_to_term

    def has_regex_annotation(self, annotation: str) -> bool:
        """Check if the annotation is defined as a regular expression."""
        return annotation in self.annotation_to_pattern

    def has_local_annotation(self, annotation: str) -> bool:
        """Check if the annotation is defined locally."""
        return annotation in self.annotation_to_local

    def has_annotation(self, annotation: str) -> bool:
        """Check if the annotation is defined."""
        return (
            self.has_enumerated_annotation(annotation) or
            self.has_regex_annotation(annotation) or
            self.has_local_annotation(annotation)
        )

    def raise_for_undefined_annotation(self, line: str, position: int, annotation: str) -> None:
        """Raise an exception if the annotation is not defined.

        :raises: UndefinedAnnotationWarning
        """
        if self._in_debug_mode:
            return

        if not self.has_annotation(annotation):
            raise UndefinedAnnotationWarning(self.get_line_number(), line, position, annotation)

    def raise_for_invalid_annotation_value(self, line: str, position: int, key: str, value: str) -> None:
        """Raise an exception if the annotation is not defined.

        :raises: IllegalAnnotationValueWarning or MissingAnnotationRegexWarning
        """
        if self._in_debug_mode:
            return

        if self.has_enumerated_annotation(key) and value not in self.annotation_to_term[key]:
            raise IllegalAnnotationValueWarning(self.get_line_number(), line, position, key, value)

        elif self.has_regex_annotation(key) and not self.annotation_to_pattern[key].match(value):
            raise MissingAnnotationRegexWarning(self.get_line_number(), line, position, key, value)

        elif self.has_local_annotation(key) and value not in self.annotation_to_local[key]:  # TODO condense
            raise IllegalAnnotationValueWarning(self.get_line_number(), line, position, key, value)

    def raise_for_missing_citation(self, line: str, position: int) -> None:
        """Raise an exception if there is no citation present in the parser.

        :raises: MissingCitationException
        """
        if self.citation_clearing and not self.citation:
            raise MissingCitationException(self.get_line_number(), line, position)

    def handle_annotation_key(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle an annotation key before parsing to validate that it's either enumerated or as a regex.

        :raise: MissingCitationException or UndefinedAnnotationWarning
        """
        key = tokens['key']
        self.raise_for_missing_citation(line, position)
        self.raise_for_undefined_annotation(line, position, key)
        return tokens

    def handle_set_statement_group(self, _, __, tokens: ParseResults) -> ParseResults:
        """Handle a ``SET STATEMENT_GROUP = "X"`` statement."""
        self.statement_group = tokens['group']
        return tokens

    def handle_set_citation(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle a ``SET Citation = {"X", "Y", "Z", ...}`` statement."""
        self.clear_citation()

        values = tokens['values']

        if len(values) < 2:
            raise CitationTooShortException(self.get_line_number(), line, position)

        citation_type = values[0]

        if citation_type not in CITATION_TYPES:
            raise InvalidCitationType(self.get_line_number(), line, position, citation_type)

        if 2 == len(values):
            return self.handle_set_citation_double(line, position, tokens)

        citation_reference = values[2]

        if citation_type == CITATION_TYPE_PUBMED and not is_int(citation_reference):
            raise InvalidPubMedIdentifierWarning(self.get_line_number(), line, position, citation_reference)

        if 4 <= len(values) and not valid_date(values[3]):
            log.debug('Invalid date: %s. Truncating entry.', values[3])
            self.citation = dict(zip(CITATION_ENTRIES, values[:3]))
            return tokens

        if 5 <= len(values):
            values[4] = [value.strip() for value in values[4].split('|')]

        if 6 < len(values):
            raise CitationTooLongException(self.get_line_number(), line, position)

        self.citation = dict(zip(CITATION_ENTRIES, values))

        return tokens

    def handle_set_citation_double(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle a ``SET Citation = {"X", "Y"}`` statement."""
        values = tokens['values']

        if values[0] == CITATION_TYPE_PUBMED and not is_int(values[1]):
            raise InvalidPubMedIdentifierWarning(self.get_line_number(), line, position, values[1])

        self.citation = dict(zip((CITATION_TYPE, CITATION_REFERENCE), values))
        return tokens

    def handle_set_evidence(self, _, __, tokens: ParseResults) -> ParseResults:
        """Handle a ``SET Evidence = ""`` statement."""
        self.evidence = tokens['value']
        return tokens

    def handle_set_command(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle a ``SET X = "Y"`` statement."""
        key, value = tokens['key'], tokens['value']
        self.raise_for_invalid_annotation_value(line, position, key, value)
        self.annotations[key] = value
        return tokens

    def handle_set_command_list(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle a ``SET X = {"Y", "Z", ...}`` statement."""
        key, values = tokens['key'], tokens['values']
        for value in values:
            self.raise_for_invalid_annotation_value(line, position, key, value)
        self.annotations[key] = set(values)
        return tokens

    def handle_unset_statement_group(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Unset the statement group, or raises an exception if it is not set.

        :raises: MissingAnnotationKeyWarning
        """
        if self.statement_group is None:
            raise MissingAnnotationKeyWarning(self.get_line_number(), line, position, BEL_KEYWORD_STATEMENT_GROUP)
        self.statement_group = None
        return tokens

    def handle_unset_citation(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Unset the citation, or raise an exception if it is not set.

        :raises: MissingAnnotationKeyWarning
        """
        if not self.citation:
            raise MissingAnnotationKeyWarning(self.get_line_number(), line, position, BEL_KEYWORD_CITATION)

        self.clear_citation()
        return tokens

    def handle_unset_evidence(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Unset the evidence, or throws an exception if it is not already set.

        The value for ``tokens[EVIDENCE]`` corresponds to which alternate of SupportingText or Evidence was used in
        the BEL script.

        :raises: MissingAnnotationKeyWarning
        """
        if self.evidence is None:
            raise MissingAnnotationKeyWarning(self.get_line_number(), line, position, tokens[EVIDENCE])
        self.evidence = None
        return tokens

    def validate_unset_command(self, line: str, position: int, annotation: str) -> None:
        """Raise an exception when trying to ``UNSET X`` if ``X`` is not already set.

        :raises: MissingAnnotationKeyWarning
        """
        if annotation not in self.annotations:
            raise MissingAnnotationKeyWarning(self.get_line_number(), line, position, annotation)

    def handle_unset_command(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle an ``UNSET X`` statement or raises an exception if it is not already set.

        :raises: MissingAnnotationKeyWarning
        """
        key = tokens['key']
        self.validate_unset_command(line, position, key)
        del self.annotations[key]
        return tokens

    def handle_unset_list(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle ``UNSET {A, B, ...}`` or raises an exception of any of them are not present.

        Consider that all unsets are in peril if just one of them is wrong!

        :raises: MissingAnnotationKeyWarning
        """
        for key in tokens['values']:
            if key in {BEL_KEYWORD_EVIDENCE, BEL_KEYWORD_SUPPORT}:
                self.evidence = None
            else:
                self.validate_unset_command(line, position, key)
                del self.annotations[key]

        return tokens

    def handle_unset_all(self, _, __, tokens) -> ParseResults:
        """Handle an ``UNSET_ALL`` statement."""
        self.clear()
        return tokens

    def get_annotations(self) -> Dict:
        """Get the current annotations."""
        return {
            EVIDENCE: self.evidence,
            CITATION: self.citation.copy(),
            ANNOTATIONS: self.annotations.copy()
        }

    def get_missing_required_annotations(self) -> List[str]:
        """Return missing required annotations."""
        return [
            required_annotation
            for required_annotation in self.required_annotations
            if required_annotation not in self.annotations
        ]

    def clear_citation(self):
        """Clear the citation and if citation clearing is enabled, clear the evidence and annotations."""
        self.citation.clear()

        if self.citation_clearing:
            self.evidence = None
            self.annotations.clear()

    def clear(self):
        """Clear the statement_group, citation, evidence, and annotations."""
        self.statement_group = None
        self.citation.clear()
        self.evidence = None
        self.annotations.clear()
