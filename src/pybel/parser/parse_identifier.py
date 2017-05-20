# -*- coding: utf-8 -*-

import logging
import re

from pyparsing import Suppress

from .baseparser import BaseParser
from .parse_exceptions import UndefinedNamespaceWarning, NakedNameWarning, MissingNamespaceNameWarning, \
    MissingDefaultNameWarning, MissingNamespaceRegexWarning
from .utils import word, quote
from ..constants import DIRTY, NAMESPACE, NAME

__all__ = ['IdentifierParser']

log = logging.getLogger(__name__)


class IdentifierParser(BaseParser):
    """A parser for identifiers in the form of namespace:name. Can be made more lenient when given a default namespace
    or enabling the use of naked names"""

    def __init__(self, namespace_dict=None, namespace_regex=None, default_namespace=None,
                 allow_naked_names=False):
        """
        :param namespace_dict: A dictionary of {namespace: set of names}
        :type namespace_dict: dict
        :param namespace_regex: A dictionary of {namespace: regular expression string} to compile
        :type namespace_regex: dict
        :param default_namespace: A set of strings that can be used without a namespace
        :type default_namespace: set of str
        :param allow_naked_names: If true, turn off naked namespace failures
        :type allow_naked_names: bool
        """
        #: A dictionary of cached {namespace keyword: set of values}
        self.namespace_dict = namespace_dict
        #: A dictionary of {namespace keyword: regular expression string}
        self.namespace_regex = {} if namespace_regex is None else namespace_regex
        #: A dictionary of {namespace keyword: compiled regular expression}
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
            self.identifier_bare.setParseAction(IdentifierParser.handle_namespace_lenient)
        else:
            self.identifier_bare.setParseAction(IdentifierParser.handle_namespace_invalid)

        BaseParser.__init__(self, self.identifier_qualified | self.identifier_bare)

    def has_enumerated_namespace(self, namespace):
        return namespace in self.namespace_dict

    def has_regex_namespace(self, namespace):
        return namespace in self.namespace_regex

    def has_namespace(self, namespace):
        return self.has_enumerated_namespace(namespace) or self.has_regex_namespace(namespace)

    def has_enumerated_namespace_name(self, namespace, name):
        return namespace in self.namespace_dict and name in self.namespace_dict[namespace]

    def has_regex_namespace_name(self, namespace, name):
        return namespace in self.namespace_regex_compiled and self.namespace_regex_compiled[namespace].match(name)

    def has_namespace_name(self, namespace, name):
        if not self.has_namespace(namespace):
            raise UndefinedNamespaceWarning(namespace, name)

        return self.has_enumerated_namespace_name(namespace, name) or self.has_regex_namespace_name(namespace, name)

    def raise_for_missing_namespace(self, namespace, name):
        if not self.has_namespace(namespace):
            raise UndefinedNamespaceWarning(namespace, name)

    def raise_for_missing_name(self, namespace, name):
        self.raise_for_missing_namespace(namespace, name)

        if self.has_enumerated_namespace(namespace) and not self.has_enumerated_namespace_name(namespace, name):
            raise MissingNamespaceNameWarning(name, namespace)

        if self.has_regex_namespace(namespace) and not self.has_regex_namespace_name(namespace, name):
            raise MissingNamespaceRegexWarning(name, namespace)

    def raise_for_missing_default(self, name):
        if not self.default_namespace:
            raise ValueError('Default namespace is not set')

        if name not in self.default_namespace:
            raise MissingDefaultNameWarning(name)

    def handle_identifier_qualified(self, line, position, tokens):
        namespace = tokens[NAMESPACE]
        name = tokens[NAME]

        self.raise_for_missing_namespace(namespace, name)
        self.raise_for_missing_name(namespace, name)

        return tokens

    def handle_identifier_default(self, line, position, tokens):
        name = tokens[NAME]
        self.raise_for_missing_default(name)
        return tokens

    @staticmethod
    def handle_namespace_lenient(line, position, tokens):
        tokens[NAMESPACE] = DIRTY
        log.debug('Naked namespace: %s', line)
        return tokens

    @staticmethod
    def handle_namespace_invalid(line, position, tokens):
        name = tokens[NAME]
        raise NakedNameWarning(line, position, name)
