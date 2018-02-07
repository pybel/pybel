# -*- coding: utf-8 -*-

import logging
import re

from pyparsing import Suppress

from .baseparser import BaseParser
from .exc import (
    MissingDefaultNameWarning, MissingNamespaceNameWarning, MissingNamespaceRegexWarning, NakedNameWarning,
    UndefinedNamespaceWarning,
)
from .utils import quote, word
from ..constants import DIRTY, NAME, NAMESPACE

__all__ = ['IdentifierParser']

log = logging.getLogger(__name__)


class IdentifierParser(BaseParser):
    """A parser for identifiers in the form of namespace:name. Can be made more lenient when given a default namespace
    or enabling the use of naked names"""

    def __init__(self, namespace_dict=None, namespace_regex=None, default_namespace=None, allow_naked_names=False):
        """
        :param Optional[dict[str,dict[str,str]]] namespace_dict: A dictionary of {namespace: {name: encoding}}
        :param Optional[dict[str,str]] namespace_regex: A dictionary of {namespace: regular expression string} to compile
        :param Optional[set[str]] default_namespace: A set of strings that can be used without a namespace
        :param bool allow_naked_names: If true, turn off naked namespace failures
        """
        self._namespace_dict = namespace_dict
        self._namespace_regex = {} if namespace_regex is None else namespace_regex
        self._namespace_regex_compiled = {
            keyword: re.compile(pattern)
            for keyword, pattern in self.namespace_regex.items()
        }
        self.default_namespace = set(default_namespace) if default_namespace is not None else None
        self.allow_naked_names = allow_naked_names

        self.identifier_qualified = word(NAMESPACE) + Suppress(':') + (word | quote)(NAME)

        if self.namespace_dict is not None:
            self.identifier_qualified.setParseAction(self.handle_identifier_qualified)

        self.identifier_bare = (word | quote)(NAME)

        self.identifier_bare.setParseAction(
            self.handle_namespace_default if self.default_namespace else
            self.handle_namespace_lenient if self.allow_naked_names else
            self.handle_namespace_invalid
        )

        super(IdentifierParser, self).__init__(self.identifier_qualified | self.identifier_bare)

    @property
    def namespace_dict(self):
        """A dictionary of {namespace: {name: encodings}}

        :rtype: dict[str,dict[str,str]]
        """
        return self._namespace_dict

    @property
    def namespace_regex(self):
        """A dictionary of {namespace keyword: regular expression string}

        :rtype: dict[str,str]
        """
        return self._namespace_regex

    @property
    def namespace_regex_compiled(self):
        """A dictionary of {namespace keyword: compiled regular expression}

        :rtype: dict[str,re]
        """
        return self._namespace_regex_compiled

    def has_enumerated_namespace(self, namespace):
        """Checks that the namespace has been defined by an enumeration"""
        return namespace in self.namespace_dict

    def has_regex_namespace(self, namespace):
        """Checks that the namespace has been defined by a regular expression"""
        return namespace in self.namespace_regex

    def has_namespace(self, namespace):
        """Checks that the namespace has either been defined by an enumeration or a regular expression"""
        return self.has_enumerated_namespace(namespace) or self.has_regex_namespace(namespace)

    def has_enumerated_namespace_name(self, namespace, name):
        """Checks that the namespace is defined by an enumeration and that the name is a member"""
        return self.has_enumerated_namespace(namespace) and name in self.namespace_dict[namespace]

    def has_regex_namespace_name(self, namespace, name):
        """Checks that the namespace is defined as a regular expression and the name matches it"""
        return self.has_regex_namespace(namespace) and self.namespace_regex_compiled[namespace].match(name)

    def has_namespace_name(self, line, position, namespace, name):
        self.raise_for_missing_namespace(line, position, namespace, name)
        return self.has_enumerated_namespace_name(namespace, name) or self.has_regex_namespace_name(namespace, name)

    def raise_for_missing_namespace(self, line, position, namespace, name):
        if not self.has_namespace(namespace):
            raise UndefinedNamespaceWarning(self.line_number, line, position, namespace, name)

    def raise_for_missing_name(self, line, position, namespace, name):
        self.raise_for_missing_namespace(line, position, namespace, name)

        if self.has_enumerated_namespace(namespace) and not self.has_enumerated_namespace_name(namespace, name):
            raise MissingNamespaceNameWarning(self.line_number, line, position, namespace, name)

        if self.has_regex_namespace(namespace) and not self.has_regex_namespace_name(namespace, name):
            raise MissingNamespaceRegexWarning(self.line_number, line, position, namespace, name)

    def raise_for_missing_default(self, line, position, name):
        if not self.default_namespace:
            raise ValueError('Default namespace is not set')

        if name not in self.default_namespace:
            raise MissingDefaultNameWarning(self.line_number, line, position, name)

    def handle_identifier_qualified(self, line, position, tokens):
        namespace = tokens[NAMESPACE]
        name = tokens[NAME]

        self.raise_for_missing_namespace(line, position, namespace, name)
        self.raise_for_missing_name(line, position, namespace, name)

        return tokens

    def handle_namespace_default(self, line, position, tokens):
        name = tokens[NAME]
        self.raise_for_missing_default(line, position, name)
        return tokens

    @staticmethod
    def handle_namespace_lenient(line, position, tokens):
        tokens[NAMESPACE] = DIRTY
        log.debug('Naked namespace: [%d] %s', position, line)
        return tokens

    def handle_namespace_invalid(self, line, position, tokens):
        name = tokens[NAME]
        raise NakedNameWarning(self.line_number, line, position, name)
