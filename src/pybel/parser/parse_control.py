# -*- coding: utf-8 -*-

"""
Control Parser
~~~~~~~~~~~~~~
This module handles parsing control statement, which add annotations and namespaces to the document.

See: https://wiki.openbel.org/display/BLD/Control+Records
"""

import logging
import re

from pyparsing import Suppress, MatchFirst
from pyparsing import pyparsing_common as ppc

from .baseparser import BaseParser, quote, delimitedSet, And, oneOf
from .parse_exceptions import *
from .utils import is_int
from ..constants import BEL_KEYWORD_STATEMENT_GROUP, BEL_KEYWORD_CITATION, BEL_KEYWORD_EVIDENCE, BEL_KEYWORD_SUPPORT, \
    BEL_KEYWORD_ALL, ANNOTATIONS
from ..constants import CITATION_ENTRIES, EVIDENCE, CITATION_TYPES, BEL_KEYWORD_SET, BEL_KEYWORD_UNSET, CITATION

log = logging.getLogger('pybel')


class ControlParser(BaseParser):
    def __init__(self, annotation_dicts=None, annotation_expressions=None, citation_clearing=True):
        """Builds parser for BEL valid_annotations statements

        :param annotation_dicts: A dictionary of {annotation: set of valid values} for parsing
        :type annotation_dicts: dict
        :param annotation_expressions: A dictionary of {annotation: regular expression string}
        :type annotation_expressions: dict
        :param citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
        :type citation_clearing: bool
        """

        self.citation_clearing = citation_clearing

        self.valid_annotations = {} if annotation_dicts is None else annotation_dicts
        self.annotations_re = {} if annotation_expressions is None else annotation_expressions
        self.annotations_re_compiled = {k: re.compile(v) for k, v in self.annotations_re.items()}

        self.statement_group = None
        self.citation = {}
        self.evidence = None
        self.annotations = {}

        annotation_key = ppc.identifier('key').setParseAction(self.handle_annotation_key)

        self.set_statement_group = And([Suppress(BEL_KEYWORD_STATEMENT_GROUP), Suppress('='), quote('group')])
        self.set_statement_group.setParseAction(self.handle_set_statement_group)

        self.set_citation = And([Suppress(BEL_KEYWORD_CITATION), Suppress('='), delimitedSet('values')])
        self.set_citation.setParseAction(self.handle_set_citation)

        supporting_text_tags = oneOf([BEL_KEYWORD_EVIDENCE, BEL_KEYWORD_SUPPORT])
        self.set_evidence = And([Suppress(supporting_text_tags), Suppress('='), quote('value')])
        self.set_evidence.setParseAction(self.handle_set_evidence)

        set_command_prefix = And([annotation_key('key'), Suppress('=')])
        self.set_command = set_command_prefix + quote('value')
        self.set_command.setParseAction(self.handle_set_command)

        self.set_command_list = set_command_prefix + delimitedSet('values')
        self.set_command_list.setParseAction(self.handle_set_command_list)

        self.unset_command = annotation_key('key')
        self.unset_command.addParseAction(self.handle_unset_command)

        self.unset_evidence = supporting_text_tags(EVIDENCE)
        self.unset_evidence.setParseAction(self.handle_unset_evidence)

        self.unset_citation = Suppress(BEL_KEYWORD_CITATION)
        self.unset_citation.setParseAction(self.handle_unset_citation)

        self.unset_statement_group = Suppress(BEL_KEYWORD_STATEMENT_GROUP)
        self.unset_statement_group.setParseAction(self.handle_unset_statement_group)

        self.unset_list = delimitedSet('values')
        self.unset_list.setParseAction(self.handle_unset_list)

        self.unset_all = Suppress(BEL_KEYWORD_ALL)
        self.unset_all.setParseAction(self.handle_unset_all)

        set_tag = Suppress(BEL_KEYWORD_SET)
        unset_tag = Suppress(BEL_KEYWORD_UNSET)

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

        BaseParser.__init__(self, self.language)

    def validate_annotation_key(self, key):
        if key not in self.valid_annotations and key not in self.annotations_re_compiled:
            raise UndefinedAnnotationWarning(key)

    def validate_value(self, key, value):
        if key in self.valid_annotations and value not in self.valid_annotations[key]:
            raise IllegalAnnotationValueWarning(value, key)
        elif key in self.annotations_re_compiled and not self.annotations_re_compiled[key].match(value):
            raise MissingAnnotationRegexWarning(value, key)

    def handle_annotation_key(self, s, l, tokens):
        """Called on all annotation keys before parsing to validate that it's either enumerated or as a regex"""
        key = tokens['key']

        if self.citation_clearing and not self.citation:
            raise MissingCitationException(s)

        self.validate_annotation_key(key)
        return tokens

    def handle_set_statement_group(self, s, l, tokens):
        self.statement_group = tokens['group']
        return tokens

    def handle_set_citation(self, s, l, tokens):
        self.clear_citation()

        values = tokens['values']

        if not (3 <= len(values) <= 6):
            raise InvalidCitationException(s)

        if values[0] not in CITATION_TYPES:
            raise InvalidCitationType(values[0])

        if values[0] == 'PubMed' and not is_int(values[2]):
            raise InvalidPubMedIdentifierWarning(values[2])

        self.citation = dict(zip(CITATION_ENTRIES, values))

        return tokens

    def handle_set_evidence(self, s, l, tokens):
        self.evidence = tokens['value']
        return tokens

    def handle_set_command(self, s, l, tokens):
        key = tokens['key']
        value = tokens['value']

        self.validate_value(key, value)

        self.annotations[key] = value
        return tokens

    def handle_set_command_list(self, s, l, tokens):
        key = tokens['key']
        values = tokens['values']

        for value in values:
            self.validate_value(key, value)

        self.annotations[key] = set(values)
        return tokens

    def handle_unset_statement_group(self, s, l, tokens):
        if self.statement_group is None:
            raise MissingAnnotationKeyWarning(BEL_KEYWORD_STATEMENT_GROUP)
        self.statement_group = None
        return tokens

    def handle_unset_citation(self, s, l, tokens):
        if not self.citation:
            raise MissingAnnotationKeyWarning(BEL_KEYWORD_CITATION)

        self.clear_citation()

        return tokens

    def handle_unset_evidence(self, s, l, tokens):
        if self.evidence is None:
            raise MissingAnnotationKeyWarning(tokens[EVIDENCE])
        self.evidence = None
        return tokens

    def validate_unset_command(self, key):
        if key not in self.annotations:
            raise MissingAnnotationKeyWarning(key)

    def handle_unset_command(self, s, l, tokens):
        key = tokens['key']
        self.validate_unset_command(key)
        del self.annotations[key]
        return tokens

    def handle_unset_list(self, s, l, tokens):
        for key in tokens['values']:
            if key in {BEL_KEYWORD_EVIDENCE, BEL_KEYWORD_SUPPORT}:
                self.evidence = None
            else:
                self.validate_unset_command(key)
                del self.annotations[key]

        return tokens

    def handle_unset_all(self, s, l, tokens):
        self.clear()
        return tokens

    def get_annotations(self):
        """

        :return: The currently stored BEL annotations
        :rtype: dict
        """
        return {
            EVIDENCE: self.evidence,
            CITATION: self.citation.copy(),
            ANNOTATIONS: self.annotations.copy()
        }

    def clear_citation(self):
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
