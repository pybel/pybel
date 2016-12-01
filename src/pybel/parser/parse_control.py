# -*- coding: utf-8 -*-

import logging

from pyparsing import Suppress, pyparsing_common, MatchFirst

from .baseparser import BaseParser, quote, delimitedSet, And, oneOf
from .parse_exceptions import *

log = logging.getLogger('pybel')


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

        set_tag = Suppress('SET')
        unset_tag = Suppress('UNSET')

        self.set_statement_group = And([set_tag, Suppress('STATEMENT_GROUP'), Suppress('='), quote('group')])
        self.set_statement_group.setParseAction(self.handle_statement_group)

        self.set_citation = And([set_tag, Suppress('Citation'), Suppress('='), delimitedSet('values')])
        self.set_citation.setParseAction(self.handle_citation)

        supporting_text_tags = oneOf(['Evidence', 'SupportingText'])
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

        self.unset_citation = unset_tag + Suppress('Citation')
        self.unset_citation.setParseAction(self.handle_unset_citation)

        self.unset_statement_group = unset_tag + Suppress('STATEMENT_GROUP')
        self.unset_statement_group.setParseAction(self.handle_unset_statement_group)

        self.unset_list = unset_tag + delimitedSet('values')
        self.unset_list.setParseAction(self.handle_unset_list)

        self.unset_all = unset_tag + Suppress("ALL")
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
            raise InvalidAnnotationKeyException("Illegal annotation: {}".format(key))
        return tokens

    def handle_citation(self, s, l, tokens):
        self.citation.clear()
        self.annotations.clear()

        values = tokens['values']

        if not (3 <= len(values) <= 6):
            raise InvalidCitationException('Invalid citation: {}'.format(s))

        self.citation = dict(zip(('type', 'name', 'reference', 'date', 'authors', 'comments'), values))

        return tokens

    def handle_supporting_text(self, s, l, tokens):
        value = tokens['value']
        self.annotations['SupportingText'] = value
        return tokens

    def handle_statement_group(self, s, l, tokens):
        self.statement_group = tokens['group']
        return tokens

    def handle_set_command(self, s, l, tokens):
        key = tokens['key']
        value = tokens['value']

        if value not in self.valid_annotations[key]:
            raise IllegalAnnotationValueExeption('Illegal annotation value for {}: {}'.format(key, value))

        self.annotations[key] = value
        return tokens

    def handle_set_command_list(self, s, l, tokens):
        key = tokens['key']
        values = tokens['values']

        for value in values:
            if value not in self.valid_annotations[key]:
                raise IllegalAnnotationValueExeption('Illegal annotation value for {}: {}'.format(key, value))

        self.annotations[key] = set(values)
        return tokens

    def handle_unset_supporting_text(self, s, l, tokens):
        if 'SupportingText' not in self.annotations:
            log.debug("PyBEL024 Can't unset missing key: %s", 'SupportingText')
        else:
            del self.annotations['SupportingText']
        return tokens

    def handle_unset_citation(self, s, l, tokens):
        if 0 == len(self.citation):
            log.debug("PyBEL024 Can't unset missing key: %s", 'Citation')
        else:
            self.citation.clear()
        return tokens

    def handle_unset_statement_group(self, s, l, tokens):
        self.statement_group = None
        return tokens

    def handle_unset_command(self, s, l, tokens):
        key = tokens['key']

        # TODO refactor to own function
        if key not in self.annotations:
            raise MissingAnnotationKeyException("Can't unset missing key: {}".format(key))

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
        if key == 'Citation':
            self.citation.clear()
            self.annotations.clear()
        elif key == 'STATEMENT_GROUP':
            self.statement_group = None
        elif key in {'SupportingText', 'Evidence'}:
            del self.annotations['SupportingText']
        elif key not in self.annotations:
            raise MissingAnnotationKeyException("Can't unset missing key: {}".format(key))
        else:
            del self.annotations[key]

    def get_language(self):
        return self.commands

    def get_annotations(self):
        annotations = self.annotations.copy()
        annotations['citation'] = self.citation.copy()
        return annotations

    def clear(self):
        self.annotations.clear()
        self.citation.clear()
        self.statement_group = None
