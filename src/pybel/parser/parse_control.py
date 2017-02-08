# -*- coding: utf-8 -*-

"""
Control Parser
~~~~~~~~~~~~~~
This module handles parsing control statement, which add annotations and namespaces to the document.

See: https://wiki.openbel.org/display/BLD/Control+Records
"""

import logging

from pyparsing import Suppress, MatchFirst
from pyparsing import pyparsing_common as ppc

from .baseparser import BaseParser, quote, delimitedSet, And, oneOf
from .parse_exceptions import *
from .utils import is_int
from ..constants import BEL_KEYWORD_STATEMENT_GROUP, BEL_KEYWORD_CITATION, BEL_KEYWORD_EVIDENCE, BEL_KEYWORD_SUPPORT, \
    BEL_KEYWORD_ALL
from ..constants import CITATION_ENTRIES, EVIDENCE, CITATION_TYPES, BEL_KEYWORD_SET, BEL_KEYWORD_UNSET, CITATION

log = logging.getLogger('pybel')


class ControlParser(BaseParser):
    def __init__(self, valid_annotations=None):
        """Builds parser for BEL valid_annotations statements

        :param valid_annotations: A dictionary from {annotation: set of valid values} for parsing
        :type valid_annotations: dict
        """

        self.valid_annotations = dict() if valid_annotations is None else valid_annotations

        self.statement_group = None
        self.citation = {}
        self.evidence = None
        self.annotations = {}

        annotation_key = ppc.identifier('key').setParseAction(self.handle_annotation_key)

        self.set_statement_group = And([Suppress(BEL_KEYWORD_STATEMENT_GROUP), Suppress('='), quote('group')])
        self.set_statement_group.setParseAction(self.handle_statement_group)

        self.set_citation = And([Suppress(BEL_KEYWORD_CITATION), Suppress('='), delimitedSet('values')])
        self.set_citation.setParseAction(self.handle_citation)

        supporting_text_tags = oneOf([BEL_KEYWORD_EVIDENCE, BEL_KEYWORD_SUPPORT])
        self.set_evidence = And([Suppress(supporting_text_tags), Suppress('='), quote('value')])
        self.set_evidence.setParseAction(self.handle_evidence)

        set_command_prefix = And([annotation_key('key'), Suppress('=')])
        self.set_command = set_command_prefix + quote('value')
        self.set_command.setParseAction(self.handle_set_command)

        self.set_command_list = set_command_prefix + delimitedSet('values')
        self.set_command_list.setParseAction(self.handle_set_command_list)

        self.unset_command = annotation_key('key')
        self.unset_command.addParseAction(self.handle_unset_command)

        self.unset_evidence = Suppress(supporting_text_tags)
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

    def handle_annotation_key(self, s, l, tokens):
        key = tokens['key']
        if key not in self.valid_annotations:
            raise UndefinedAnnotationWarning(key)
        return tokens

    def handle_citation(self, s, l, tokens):
        self.citation.clear()
        self.annotations.clear()

        values = tokens['values']

        if not (3 <= len(values) <= 6):
            raise InvalidCitationException(s)

        if values[0] not in CITATION_TYPES:
            raise InvalidCitationType(values[0])

        if values[0] == 'PubMed' and not is_int(values[2]):
            raise InvalidPubMedIdentifierWarning(values[2])

        self.citation = dict(zip(CITATION_ENTRIES, values))

        return tokens

    def handle_evidence(self, s, l, tokens):
        self.evidence = tokens['value']
        return tokens

    def handle_statement_group(self, s, l, tokens):
        self.statement_group = tokens['group']
        return tokens

    def handle_set_command(self, s, l, tokens):
        key = tokens['key']
        value = tokens['value']

        if value not in self.valid_annotations[key]:
            raise IllegalAnnotationValueWarning(value, key)

        self.annotations[key] = value
        return tokens

    def handle_set_command_list(self, s, l, tokens):
        key = tokens['key']
        values = tokens['values']

        for value in values:
            if value not in self.valid_annotations[key]:
                raise IllegalAnnotationValueWarning(value, key)

        self.annotations[key] = set(values)
        return tokens

    def handle_unset_statement_group(self, s, l, tokens):
        self.statement_group = None
        return tokens

    def handle_unset_citation(self, s, l, tokens):
        if not self.citation:
            raise MissingAnnotationKeyWarning(BEL_KEYWORD_CITATION)
        self.citation.clear()
        return tokens

    def handle_unset_evidence(self, s, l, tokens):
        if self.evidence is None:
            raise MissingAnnotationKeyWarning(EVIDENCE)
        self.evidence = None
        return tokens

    def validate_command(self, key):
        if key not in self.valid_annotations:
            raise UndefinedAnnotationWarning(key)

        if key not in self.annotations:
            raise MissingAnnotationKeyWarning(key)

    def handle_unset_command(self, s, l, tokens):
        key = tokens['key']
        self.validate_command(key)

        del self.annotations[key]
        return tokens

    def handle_unset_list(self, s, l, tokens):
        for key in tokens['values']:
            if key in {BEL_KEYWORD_EVIDENCE, BEL_KEYWORD_SUPPORT}:
                self.evidence = None
            elif key not in self.annotations:
                raise MissingAnnotationKeyWarning(key)
            else:
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
        annotations = {
            EVIDENCE: self.evidence,
            CITATION: self.citation.copy()
        }
        annotations.update(self.annotations.copy())
        return annotations

    def clear(self):
        """Clears the annotations, citation, and statement group"""
        self.statement_group = None
        self.citation.clear()
        self.evidence = None
        self.annotations.clear()
