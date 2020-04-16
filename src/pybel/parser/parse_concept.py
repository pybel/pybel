# -*- coding: utf-8 -*-

"""A module holding the :class:`IdentifierParser`."""

import logging
from collections import defaultdict
from typing import Mapping, Optional, Pattern, Set

from pyparsing import ParseResults, Suppress

from .baseparser import BaseParser
from .constants import NamespaceTermEncodingMapping
from .exc import (
    MissingDefaultNameWarning, MissingNamespaceNameWarning, MissingNamespaceRegexWarning, NakedNameWarning,
    UndefinedNamespaceWarning,
)
from .utils import quote, word
from ..constants import DIRTY, IDENTIFIER, NAME, NAMESPACE

__all__ = [
    'ConceptParser',
]

logger = logging.getLogger(__name__)


class ConceptParser(BaseParser):
    """A parser for concepts in the form of ``namespace:name`` or ``namespace:identifier!name``.

    Can be made more lenient when given a default namespace or enabling the use of naked names.
    """

    def __init__(
        self,
        namespace_to_term_to_encoding: Optional[NamespaceTermEncodingMapping] = None,
        namespace_to_pattern: Optional[Mapping[str, Pattern]] = None,
        default_namespace: Optional[Set[str]] = None,
        allow_naked_names: bool = False,
    ) -> None:
        """Initialize the concept parser.

        :param namespace_to_term_to_encoding: A dictionary of {namespace: {(identifier, name): encoding}}
        :param namespace_to_pattern: A dictionary of {namespace: regular expression string} to compile
        :param default_namespace: A set of strings that can be used without a namespace
        :param allow_naked_names: If true, turn off naked namespace failures
        """
        self.identifier_fqualified = (
            word(NAMESPACE)
            + Suppress(':')
            + (word | quote)(IDENTIFIER)
            + Suppress('!')
            + (word | quote)(NAME)
        )
        self.identifier_qualified = word(NAMESPACE) + Suppress(':') + (word | quote)(NAME)

        if namespace_to_term_to_encoding is not None:
            self.namespace_to_name_to_encoding = defaultdict(dict)
            self.namespace_to_identifier_to_encoding = defaultdict(dict)
            for namespace, term_mapping in namespace_to_term_to_encoding.items():
                for (identifier, name), encoding in term_mapping.items():
                    self.namespace_to_name_to_encoding[namespace][name] = encoding
                    self.namespace_to_identifier_to_encoding[namespace][identifier] = encoding

            self.namespace_to_name_to_encoding = dict(self.namespace_to_name_to_encoding)
            self.namespace_to_identifier_to_encoding = dict(self.namespace_to_identifier_to_encoding)
        else:
            self.namespace_to_name_to_encoding = {}
            self.namespace_to_identifier_to_encoding = {}

        self.identifier_fqualified.setParseAction(self.handle_identifier_fqualified)
        self.identifier_qualified.setParseAction(self.handle_identifier_qualified)

        self.namespace_to_pattern = namespace_to_pattern or {}
        self.default_namespace = set(default_namespace) if default_namespace is not None else None
        self.allow_naked_names = allow_naked_names

        self.identifier_bare = (word | quote)(NAME)
        self.identifier_bare.setParseAction(
            self.handle_namespace_default if self.default_namespace else
            self.handle_namespace_lenient if self.allow_naked_names else
            self.handle_namespace_invalid,
        )

        super().__init__(
            self.identifier_fqualified | self.identifier_qualified | self.identifier_bare,
        )

    def has_enumerated_namespace(self, namespace: str) -> bool:
        """Check that the namespace has been defined by an enumeration."""
        return namespace in self.namespace_to_name_to_encoding

    def has_regex_namespace(self, namespace: str) -> bool:
        """Check that the namespace has been defined by a regular expression."""
        return namespace in self.namespace_to_pattern

    def raise_for_missing_namespace(self, line: str, position: int, namespace: str, name: str) -> None:
        """Raise an exception if the namespace is not defined."""
        if not self.has_enumerated_namespace(namespace) and not self.has_regex_namespace(namespace):
            raise UndefinedNamespaceWarning(self.get_line_number(), line, position, namespace, name)

    def raise_for_missing_name(self, line: str, position: int, namespace: str, name: str) -> None:
        """Raise an exception if the namespace is not defined or if it does not validate the given name."""
        self.raise_for_missing_namespace(line, position, namespace, name)

        if self.has_enumerated_namespace(namespace) and name not in self.namespace_to_name_to_encoding[namespace]:
            raise MissingNamespaceNameWarning(self.get_line_number(), line, position, namespace, name)

        if self.has_regex_namespace(namespace) and not self.namespace_to_pattern[namespace].match(name):
            raise MissingNamespaceRegexWarning(self.get_line_number(), line, position, namespace, name)

    def handle_identifier_fqualified(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle parsing a qualified OBO-style identifier."""
        return self._handle_identifier(line, position, tokens, key=IDENTIFIER)

    def handle_identifier_qualified(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle parsing a qualified identifier."""
        return self._handle_identifier(line, position, tokens, key=NAME)

    def _handle_identifier(self, line: str, position: int, tokens: ParseResults, key) -> ParseResults:
        """Handle parsing a qualified identifier."""
        namespace, name = tokens[NAMESPACE], tokens[key]

        self.raise_for_missing_namespace(line, position, namespace, name)
        self.raise_for_missing_name(line, position, namespace, name)

        return tokens

    def handle_namespace_default(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle parsing an identifier for the default namespace."""
        name = tokens[NAME]
        if not self.default_namespace:
            raise ValueError('Default namespace is not set')
        if name not in self.default_namespace:
            raise MissingDefaultNameWarning(self.get_line_number(), line, position, name)
        return tokens

    @staticmethod
    def handle_namespace_lenient(line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle parsing an identifier for names missing a namespace that are outside the default namespace."""
        tokens[NAMESPACE] = DIRTY
        logger.debug('Naked namespace: [%d] %s', position, line)
        return tokens

    def handle_namespace_invalid(self, line: str, position: int, tokens: ParseResults) -> None:
        """Raise an exception when parsing a name missing a namespace."""
        name = tokens[NAME]
        raise NakedNameWarning(self.get_line_number(), line, position, name)
