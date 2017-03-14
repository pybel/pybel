# -*- coding: utf-8 -*-

import logging
import re

from pyparsing import Suppress, Group

from .baseparser import BaseParser, word, quote
from .parse_exceptions import UndefinedNamespaceWarning, NakedNameWarning, MissingNamespaceNameWarning, \
    MissingDefaultNameWarning, MissingNamespaceRegexWarning
from ..constants import DIRTY, NAMESPACE, NAME, IDENTIFIER

log = logging.getLogger(__name__)


class IdentifierParser(BaseParser):
    def __init__(self, namespace_dicts=None, default_namespace=None, namespace_expressions=None,
                 namespace_mappings=None, allow_naked_names=False):
        """Builds a namespace parser.

        :param namespace_dicts: dictionary of {namespace: set of names}
        :type namespace_dicts: dict
        :param namespace_expressions: dictionary of {namespace: regular expression string} to compile
        :type namespace_expressions: dict
        :param default_namespace: set of strings that can be used without a namespace
        :type default_namespace: set of str
        :param namespace_mappings: dictionary of {namespace: {name: (mapped_ns, mapped_name)}}
        :type namespace_mappings: dict
        :param allow_naked_names: if true, turn off naked namespace failures
        :type allow_naked_names: bool
        """

        self.namespace_dict = namespace_dicts
        self.namespace_regex = {} if namespace_expressions is None else namespace_expressions
        self.namespace_regex_compiled = {k: re.compile(v) for k, v in self.namespace_regex.items()}
        self.default_namespace = set(default_namespace) if default_namespace is not None else None
        self.allow_naked_names = allow_naked_names

        self.identifier_qualified = word(NAMESPACE) + Suppress(':') + (word | quote)(NAME)

        if self.namespace_dict is not None:
            self.identifier_qualified.setParseAction(self.handle_identifier_qualified)

        self.identifier_bare = (word | quote)(NAME)

        if self.default_namespace is not None:
            self.identifier_bare.setParseAction(self.handle_identifier_default)
        elif self.allow_naked_names:
            self.identifier_bare.setParseAction(handle_namespace_lenient)
        else:
            self.identifier_bare.setParseAction(handle_namespace_invalid)

        if namespace_mappings is not None:
            # TODO implement
            raise NotImplementedError('Mapping not yet implemented')

        BaseParser.__init__(self, self.identifier_qualified | self.identifier_bare)

    def handle_identifier_qualified(self, s, l, tokens):
        namespace = tokens[NAMESPACE]

        if namespace not in self.namespace_dict and namespace not in self.namespace_regex_compiled:
            raise UndefinedNamespaceWarning(namespace)

        name = tokens[NAME]
        if namespace in self.namespace_dict and name not in self.namespace_dict[namespace]:
            raise MissingNamespaceNameWarning(name, namespace)
        elif namespace in self.namespace_regex_compiled and not self.namespace_regex_compiled[namespace].match(name):
            raise MissingNamespaceRegexWarning(name, namespace)

        return tokens

    def handle_identifier_default(self, s, l, tokens):
        name = tokens[NAME]
        if name not in self.default_namespace:
            raise MissingDefaultNameWarning(name)
        return tokens

    def as_group(self):
        return Group(self.language)(IDENTIFIER)


def handle_namespace_lenient(s, l, tokens):
    tokens[NAMESPACE] = DIRTY
    log.debug('Naked namespace: %s', s)
    return tokens


def handle_namespace_invalid(s, l, tokens):
    raise NakedNameWarning(tokens[NAME])
