import logging

from pyparsing import Suppress, oneOf

from .baseparser import BaseParser, W, quote, delimitedSet
from .parse_exceptions import *

log = logging.getLogger(__name__)


class ControlParser(BaseParser):
    def __init__(self, citation=None, annotations=None, custom_annotations=None):
        """Builds parser for BEL custom_annotations statements

        :param custom_annotations: A dictionary from {annotation: set of valid values} for parsing
        :type custom_annotations: dict
        :return:
        """

        self.citation = {} if citation is None else citation
        self.annotations = {} if annotations is None else annotations
        self.custom_annotations = dict() if custom_annotations is None else custom_annotations
        self.statement_group = None

        custom_annotations = oneOf(self.custom_annotations.keys())

        set_tag = Suppress('SET')
        unset_tag = Suppress('UNSET')

        self.set_statement_group = set_tag + W + Suppress('STATEMENT_GROUP') + W + Suppress('=') + W + quote(
            'group')
        self.set_statement_group.setParseAction(self.handle_statement_group)

        self.set_citation = set_tag + W + Suppress('Citation') + W + Suppress('=') + W + delimitedSet('values')
        self.set_citation.setParseAction(self.handle_citation)

        self.set_evidence = set_tag + W + Suppress('Evidence') + W + Suppress('=') + W + quote('value')
        self.set_evidence.setParseAction(self.handle_evidence)

        self.set_command = set_tag + W + custom_annotations('key') + W + Suppress('=') + W + quote('value')
        self.set_command.setParseAction(self.handle_set_command)

        self.set_command_list = set_tag + W + custom_annotations('key') + W + Suppress('=') + W + delimitedSet(
            'values')
        self.set_command_list.setParseAction(self.handle_set_command_list)

        self.unset_command = unset_tag + W + (custom_annotations | 'Evidence')('key')
        self.unset_command.setParseAction(self.handle_unset_command)

        self.unset_statement_group = unset_tag + W + Suppress('STATEMENT_GROUP')
        self.unset_statement_group.setParseAction(self.handle_unset_statement_group)

        self.commands = (self.set_citation | self.unset_command | self.unset_statement_group |
                         self.set_statement_group | self.set_evidence | self.set_command | self.set_command_list)

    def handle_citation(self, s, l, tokens):
        self.citation.clear()
        self.annotations.clear()

        values = tokens['values']

        if len(values) not in (3, 6):
            raise InvalidCitationException('PyBEL011 invalid citation: {}'.format(s))

        self.citation = dict(zip(('type', 'name', 'reference', 'date', 'authors', 'comments'), values))

        return tokens

    def handle_evidence(self, s, l, tokens):
        if 'value' not in tokens:
            log.error('ERROR {} {} {}'.format(s, l, tokens))
        value = tokens['value']
        self.annotations['Evidence'] = value
        return tokens

    def handle_statement_group(self, s, l, tokens):
        self.statement_group = tokens['group']
        return tokens

    def handle_set_command(self, s, l, tokens):
        key = tokens['key']
        value = tokens['value']

        if value not in self.custom_annotations[key]:
            raise IllegalAnnotationValueExeption('PyBEL012 illegal annotation value')

        self.annotations[key] = value
        return tokens

    def handle_set_command_list(self, s, l, tokens):
        key = tokens['key']
        values = tokens['values']

        for value in values:
            if value not in self.custom_annotations[key]:
                raise IllegalAnnotationValueExeption('PyBEL012 illegal annotation value: {}'.format(value))

        self.annotations[key] = set(values)
        return tokens

    def handle_unset_statement_group(self):
        self.statement_group = None

    def handle_unset_command(self, s, l, tokens):
        key = tokens['key']

        if key not in self.annotations:
            log.warning("PyBEL020 Can't unset missing key")
            return tokens

        del self.annotations[key]
        return tokens

    def get_language(self):
        return self.commands

    def get_annotations(self):
        annot = self.annotations.copy()
        for key, value in self.citation.items():
            annot['citation_{}'.format(key)] = value
        return annot

    def clear_annotations(self):
        self.annotations.clear()
