# -*- coding: utf-8 -*-

"""A module holding the :class:`IdentifierParser`."""

import logging
import re
from typing import Mapping, Optional, Set

from pyparsing import ParseResults, Suppress

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
    """A parser for identifiers in the form of ``namespace:name``.

    Can be made more lenient when given a default namespace or enabling the use of naked names.
    """

    def __init__(self,
                 namespace_dict: Optional[Mapping[str, Mapping[str, str]]] = None,
                 namespace_regex: Optional[Mapping[str, str]] = None,
                 default_namespace: Optional[Set[str]] = None,
                 allow_naked_names: bool = False,
                 ) -> None:
        """Initialize the identifier parser.

        :param namespace_dict: A dictionary of {namespace: {name: encoding}}
        :param namespace_regex: A dictionary of {namespace: regular expression string} to compile
        :param default_namespace: A set of strings that can be used without a namespace
        :param allow_naked_names: If true, turn off naked namespace failures
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
    def namespace_dict(self) -> Mapping[str, Mapping[str, str]]:
        """Get the dictionary of {namespace: {name: encodings}}."""
        return self._namespace_dict

    @property
    def namespace_regex(self) -> Mapping[str, str]:
        """Get the dictionary of {namespace keyword: regular expression string}."""
        return self._namespace_regex

    @property
    def namespace_regex_compiled(self):
        """Get the dictionary of {namespace keyword: compiled regular expression}."""
        return self._namespace_regex_compiled

    def has_enumerated_namespace(self, namespace: str) -> bool:
        """Check that the namespace has been defined by an enumeration."""
        return namespace in self.namespace_dict

    def has_regex_namespace(self, namespace: str) -> bool:
        """Check that the namespace has been defined by a regular expression."""
        return namespace in self.namespace_regex

    def has_namespace(self, namespace: str) -> bool:
        """Check that the namespace has either been defined by an enumeration or a regular expression."""
        return self.has_enumerated_namespace(namespace) or self.has_regex_namespace(namespace)

    def has_enumerated_namespace_name(self, namespace: str, name: str) -> bool:
        """Check that the namespace is defined by an enumeration and that the name is a member."""
        return self.has_enumerated_namespace(namespace) and name in self.namespace_dict[namespace]

    def has_regex_namespace_name(self, namespace: str, name: str) -> bool:
        """Check that the namespace is defined as a regular expression and the name matches it."""
        return self.has_regex_namespace(namespace) and self.namespace_regex_compiled[namespace].match(name)

    def has_namespace_name(self, line: str, position: int, namespace: str, name: str) -> bool:
        """Check that the namespace is defined and has the given name."""
        self.raise_for_missing_namespace(line, position, namespace, name)
        return self.has_enumerated_namespace_name(namespace, name) or self.has_regex_namespace_name(namespace, name)

    def raise_for_missing_namespace(self, line: str, position: int, namespace: str, name: str) -> None:
        """Raise an exception if the namespace is not defined."""
        if not self.has_namespace(namespace):
            raise UndefinedNamespaceWarning(self.get_line_number(), line, position, namespace, name)

    def raise_for_missing_name(self, line: str, position: int, namespace: str, name: str) -> None:
        """Raise an exception if the namespace is not defined or if it does not validate the given name."""
        self.raise_for_missing_namespace(line, position, namespace, name)

        if self.has_enumerated_namespace(namespace) and not self.has_enumerated_namespace_name(namespace, name):
            raise MissingNamespaceNameWarning(self.get_line_number(), line, position, namespace, name)

        if self.has_regex_namespace(namespace) and not self.has_regex_namespace_name(namespace, name):
            raise MissingNamespaceRegexWarning(self.get_line_number(), line, position, namespace, name)

    def raise_for_missing_default(self, line: str, position: int, name: str) -> None:
        """Raise an exeception if the name does not belong to the default namespace."""
        if not self.default_namespace:
            raise ValueError('Default namespace is not set')

        if name not in self.default_namespace:
            raise MissingDefaultNameWarning(self.get_line_number(), line, position, name)

    def handle_identifier_qualified(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle parsing a qualified identifier."""
        namespace, name = tokens[NAMESPACE], tokens[NAME]

        self.raise_for_missing_namespace(line, position, namespace, name)
        self.raise_for_missing_name(line, position, namespace, name)

        return tokens

    def handle_namespace_default(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle parsing an identifier for the default namespace."""
        name = tokens[NAME]
        self.raise_for_missing_default(line, position, name)
        return tokens

    @staticmethod
    def handle_namespace_lenient(line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle parsing an identifier for name missing a namespac ethat are outside the default namespace."""
        tokens[NAMESPACE] = DIRTY
        log.debug('Naked namespace: [%d] %s', position, line)
        return tokens

    def handle_namespace_invalid(self, line: str, position: int, tokens: ParseResults) -> None:
        """Raise an exception when parsing a name missing a namespace."""
        name = tokens[NAME]
        raise NakedNameWarning(self.get_line_number(), line, position, name)
