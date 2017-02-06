# -*- coding: utf-8 -*-

"""
Control Parser
~~~~~~~~~~~~~~
This module handles parsing control statement, which add annotations and namespaces to the document.

See: https://wiki.openbel.org/display/BLD/Control+Records
"""

import logging

from pyparsing import Suppress, pyparsing_common, MatchFirst

from .baseparser import BaseParser, quote, delimitedSet, And, oneOf
from .parse_exceptions import *
from .utils import is_int
from ..constants import CITATION_ENTRIES, EVIDENCE, CITATION_TYPES

log = logging.getLogger('pybel')

BEL_KEYWORD_SET = 'SET'
BEL_KEYWORD_UNSET = 'UNSET'
BEL_KEYWORD_STATEMENT_GROUP = 'STATEMENT_GROUP'
BEL_KEYWORD_CITATION = 'Citation'
BEL_KEYWORD_EVIDENCE = 'Evidence'
BEL_KEYWORD_SUPPORT = 'SupportingText'
BEL_KEYWORD_ALL = 'ALL'


class ControlParser(BaseParser):
    def __init__(self, valid_annotations=None):
        """Builds parser for BEL valid_annotations statements

        :param valid_annotations: A dictionary from {annotation: set of valid values} for parsing
        :type valid_annotations: dict
        """

        self.valid_annotations = dict() if valid_annotations is None else valid_annotations

        self.citation = {}
        self.annotations = {}
        self.statement_group = None

        annotation_key = pyparsing_common.identifier.setResultsName('key')
        annotation_key.setParseAction(self.handle_annotation_key)

        set_tag = Suppress(BEL_KEYWORD_SET)
        unset_tag = Suppress(BEL_KEYWORD_UNSET)

        self.set_statement_group = And([set_tag, Suppress(BEL_KEYWORD_STATEMENT_GROUP), Suppress('='), quote('group')])
        self.set_statement_group.setParseAction(self.handle_statement_group)

        self.set_citation = And([set_tag, Suppress(BEL_KEYWORD_CITATION), Suppress('='), delimitedSet('values')])
        self.set_citation.setParseAction(self.handle_citation)

        supporting_text_tags = oneOf([BEL_KEYWORD_EVIDENCE, BEL_KEYWORD_SUPPORT])
        self.set_evidence = And([set_tag, Suppress(supporting_text_tags), Suppress('='), quote('value')])
        self.set_evidence.setParseAction(self.handle_supporting_text)

        set_command_prefix = And([set_tag, annotation_key, Suppress('=')])
        self.set_command = set_command_prefix + quote('value')
        self.set_command.setParseAction(self.handle_set_command)

        self.set_command_list = set_command_prefix + delimitedSet('values')
        self.set_command_list.setParseAction(self.handle_set_command_list)

        self.unset_command = unset_tag + annotation_key
        self.unset_command.setParseAction(self.handle_unset_command)

        self.unset_evidence = unset_tag + Suppress(supporting_text_tags)
        self.unset_evidence.setParseAction(self.handle_unset_supporting_text)

        self.unset_citation = unset_tag + Suppress(BEL_KEYWORD_CITATION)
        self.unset_citation.setParseAction(self.handle_unset_citation)

        self.unset_statement_group = unset_tag + Suppress(BEL_KEYWORD_STATEMENT_GROUP)
        self.unset_statement_group.setParseAction(self.handle_unset_statement_group)

        self.unset_list = unset_tag + delimitedSet('values')
        self.unset_list.setParseAction(self.handle_unset_list)

        self.unset_all = unset_tag + Suppress(BEL_KEYWORD_ALL)
        self.unset_all.setParseAction(self.handle_unset_all)

        self.unset_statements = MatchFirst([
            self.unset_all, self.unset_citation, self.unset_evidence,
            self.unset_statement_group, self.unset_command, self.unset_list
        ])

        self.commands = MatchFirst([self.set_statement_group, self.set_citation, self.set_evidence,
                                    self.set_command, self.set_command_list, self.unset_statements])

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

    def handle_supporting_text(self, s, l, tokens):
        value = tokens['value']
        self.annotations[EVIDENCE] = value
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

    def handle_unset_supporting_text(self, s, l, tokens):
        if EVIDENCE not in self.annotations:
            raise MissingAnnotationKeyWarning(EVIDENCE)
        else:
            del self.annotations[EVIDENCE]
        return tokens

    def handle_unset_citation(self, s, l, tokens):
        if 0 == len(self.citation):
            raise MissingAnnotationKeyWarning(BEL_KEYWORD_CITATION)
        else:
            self.citation.clear()
        return tokens

    def handle_unset_statement_group(self, s, l, tokens):
        self.statement_group = None
        return tokens

    def handle_unset_command(self, s, l, tokens):
        key = tokens['key']

        if key not in self.annotations:
            raise MissingAnnotationKeyWarning(key)

        del self.annotations[key]
        return tokens

    def handle_unset_all(self, s, l, tokens):
        self.clear()
        return tokens

    def handle_unset_list(self, s, l, tokens):
        for key in tokens['values']:
            self.handle_unset(key)
        return tokens

    def handle_unset(self, key):
        if key == BEL_KEYWORD_CITATION:
            self.citation.clear()
            self.annotations.clear()
        elif key == BEL_KEYWORD_STATEMENT_GROUP:
            self.statement_group = None
        elif key in {BEL_KEYWORD_EVIDENCE, BEL_KEYWORD_SUPPORT}:
            del self.annotations[EVIDENCE]
        elif key not in self.annotations:
            raise MissingAnnotationKeyWarning(key)
        else:
            del self.annotations[key]

    def get_language(self):
        return self.commands

    def get_annotations(self):
        """

        :return: The currently stored BEL annotations
        :rtype: dict
        """
        annotations = self.annotations.copy()
        annotations['citation'] = self.citation.copy()
        return annotations

    def clear(self):
        """Clears the annotations, citation, and statement group"""
        self.annotations.clear()
        self.citation.clear()
        self.statement_group = None
