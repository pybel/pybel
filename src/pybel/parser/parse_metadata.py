# -*- coding: utf-8 -*-

"""This module supports the relation parser by handling statements."""

import logging
import re
from typing import Mapping, Optional, Pattern, Set

from pyparsing import And, MatchFirst, ParseResults, Suppress, Word, pyparsing_common as ppc

from .baseparser import BaseParser
from .exc import InvalidMetadataException, RedefinedAnnotationError, RedefinedNamespaceError, VersionFormatWarning
from .utils import delimited_quoted_list, qid, quote, word
from ..constants import (
    BEL_KEYWORD_ANNOTATION, BEL_KEYWORD_AS, BEL_KEYWORD_DEFINE, BEL_KEYWORD_DOCUMENT, BEL_KEYWORD_LIST,
    BEL_KEYWORD_NAMESPACE, BEL_KEYWORD_PATTERN, BEL_KEYWORD_SET, BEL_KEYWORD_URL, DOCUMENT_KEYS, METADATA_VERSION,
    belns_encodings,
)
from ..utils import valid_date_version

__all__ = ['MetadataParser']

log = logging.getLogger(__name__)

as_tag = Suppress(BEL_KEYWORD_AS)
url_tag = Suppress(BEL_KEYWORD_URL)
list_tag = Suppress(BEL_KEYWORD_LIST)
set_tag = Suppress(BEL_KEYWORD_SET)
define_tag = Suppress(BEL_KEYWORD_DEFINE)

function_tags = Word(''.join(belns_encodings))

SEMANTIC_VERSION_STRING_RE = re.compile(
    r'(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:-(?P<release>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?')

MALFORMED_VERSION_STRING_RE = re.compile(r'(?P<major>\d+)(\.(?P<minor>\d+)(\.(?P<patch>\d+))?)?')


class MetadataParser(BaseParser):
    """A parser for the document and definitions section of a BEL document.

    .. seealso::

        BEL 1.0 Specification for the `DEFINE <http://openbel.org/language/web/version_1.0/bel_specification_version_1.0.html#_define>`_ keyword
    """

    def __init__(self,
                 manager,
                 namespace_to_term: Optional[Mapping[str, Mapping[str, str]]] = None,
                 namespace_to_pattern: Optional[Mapping[str, Pattern]] = None,
                 annotation_to_term: Optional[Mapping[str, Set[str]]] = None,
                 annotation_to_pattern: Optional[Mapping[str, Pattern]] = None,
                 annotation_to_local: Optional[Mapping[str, Set[str]]] = None,
                 default_namespace: Optional[Set[str]] = None,
                 allow_redefinition: bool = False,
                 skip_validation: bool = False,
                 ) -> None:
        """Build a metadata parser.

        :param manager: A cache manager
        :param namespace_to_term: Enumerated namespace mapping from {namespace keyword: {name: encoding}}
        :param namespace_to_pattern: Regular expression namespace mapping from {namespace keyword: regex string}
        :param annotation_to_term: Enumerated annotation mapping from {annotation keyword: set of valid values}
        :param annotation_to_pattern: Regular expression annotation mapping from {annotation keyword: regex string}
        :param default_namespace: A set of strings that can be used without a namespace
        :param skip_validation: If true, don't download and cache namespaces/annotations
        """
        #: This metadata parser's internal definition cache manager
        self.manager = manager
        self.disallow_redefinition = not allow_redefinition
        self.skip_validation = skip_validation

        #: A dictionary of cached {namespace keyword: {name: encoding}}
        self.namespace_to_term = namespace_to_term or {}
        #: A set of namespaces's URLs that can't be cached
        self.uncachable_namespaces = set()
        #: A dictionary of {namespace keyword: regular expression string}
        self.namespace_to_pattern = namespace_to_pattern or {}
        #: A set of names that can be used without a namespace
        self.default_namespace = set(default_namespace) if default_namespace is not None else None

        #: A dictionary of cached {annotation keyword: set of values}
        self.annotation_to_term = annotation_to_term or {}
        #: A dictionary of {annotation keyword: regular expression string}
        self.annotation_to_pattern = annotation_to_pattern or {}
        #: A dictionary of cached {annotation keyword: set of values}
        self.annotation_to_local = annotation_to_local or {}

        #: A dictionary containing the document metadata
        self.document_metadata = {}

        #: A dictionary from {namespace keyword: BEL namespace URL}
        self.namespace_url_dict = {}
        #: A dictionary from {annotation keyword: BEL annotation URL}
        self.annotation_url_dict = {}

        self.document = And([
            set_tag,
            Suppress(BEL_KEYWORD_DOCUMENT),
            word('key'),
            Suppress('='),
            qid('value')
        ])

        namespace_tag = And([define_tag, Suppress(BEL_KEYWORD_NAMESPACE), ppc.identifier('name'), as_tag])
        self.namespace_url = And([namespace_tag, url_tag, quote('url')])
        self.namespace_pattern = And([namespace_tag, Suppress(BEL_KEYWORD_PATTERN), quote('value')])

        annotation_tag = And([define_tag, Suppress(BEL_KEYWORD_ANNOTATION), ppc.identifier('name'), as_tag])
        self.annotation_url = And([annotation_tag, url_tag, quote('url')])
        self.annotation_list = And([annotation_tag, list_tag, delimited_quoted_list('values')])
        self.annotation_pattern = And([annotation_tag, Suppress(BEL_KEYWORD_PATTERN), quote('value')])

        self.document.setParseAction(self.handle_document)
        self.namespace_url.setParseAction(self.handle_namespace_url)
        self.namespace_pattern.setParseAction(self.handle_namespace_pattern)
        self.annotation_url.setParseAction(self.handle_annotations_url)
        self.annotation_list.setParseAction(self.handle_annotation_list)
        self.annotation_pattern.setParseAction(self.handle_annotation_pattern)

        self.language = MatchFirst([
            self.document,
            self.namespace_url,
            self.annotation_url,
            self.annotation_list,
            self.annotation_pattern,
            self.namespace_pattern
        ]).setName('BEL Metadata')

        super(MetadataParser, self).__init__(self.language)

    def handle_document(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle statements like ``SET DOCUMENT X = "Y"``.

        :raises: InvalidMetadataException
        :raises: VersionFormatWarning
        """
        key = tokens['key']
        value = tokens['value']

        if key not in DOCUMENT_KEYS:
            raise InvalidMetadataException(self.get_line_number(), line, position, key, value)

        norm_key = DOCUMENT_KEYS[key]

        if norm_key in self.document_metadata:
            log.warning('Tried to overwrite metadata: %s', key)
            return tokens

        self.document_metadata[norm_key] = value

        if norm_key == METADATA_VERSION:
            self.raise_for_version(line, position, value)

        return tokens

    def raise_for_redefined_namespace(self, line: str, position: int, namespace: str) -> None:
        """Raise an exception if a namespace is already defined.

        :raises: RedefinedNamespaceError
        """
        if self.disallow_redefinition and self.has_namespace(namespace):
            raise RedefinedNamespaceError(self.get_line_number(), line, position, namespace)

    def handle_namespace_url(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle statements like ``DEFINE NAMESPACE X AS URL "Y"``.

        :raises: RedefinedNamespaceError
        :raises: pybel.resources.exc.ResourceError
        """
        namespace = tokens['name']
        self.raise_for_redefined_namespace(line, position, namespace)

        url = tokens['url']
        self.namespace_url_dict[namespace] = url

        if self.skip_validation:
            return tokens

        namespace_result = self.manager.get_or_create_namespace(url)

        if isinstance(namespace_result, dict):
            self.namespace_to_term[namespace] = namespace_result
            self.uncachable_namespaces.add(url)
        else:
            self.namespace_to_term[namespace] = self.manager.get_namespace_encoding(url)

        return tokens

    def handle_namespace_pattern(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle statements like ``DEFINE NAMESPACE X AS PATTERN "Y"``.

        :raises: RedefinedNamespaceError
        """
        namespace = tokens['name']
        self.raise_for_redefined_namespace(line, position, namespace)
        self.namespace_to_pattern[namespace] = re.compile(tokens['value'])
        return tokens

    def raise_for_redefined_annotation(self, line: str, position: int, annotation: str) -> None:
        """Raise an exception if the given annotation is already defined.

        :raises: RedefinedAnnotationError
        """
        if self.disallow_redefinition and self.has_annotation(annotation):
            raise RedefinedAnnotationError(self.get_line_number(), line, position, annotation)

    def handle_annotations_url(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle statements like ``DEFINE ANNOTATION X AS URL "Y"``.

        :raises: RedefinedAnnotationError
        """
        keyword = tokens['name']
        self.raise_for_redefined_annotation(line, position, keyword)

        url = tokens['url']
        self.annotation_url_dict[keyword] = url

        if self.skip_validation:
            return tokens

        self.annotation_to_term[keyword] = self.manager.get_annotation_entry_names(url)

        return tokens

    def handle_annotation_list(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle statements like ``DEFINE ANNOTATION X AS LIST {"Y","Z", ...}``.

        :raises: RedefinedAnnotationError
        """
        annotation = tokens['name']
        self.raise_for_redefined_annotation(line, position, annotation)
        self.annotation_to_local[annotation] = set(tokens['values'])
        return tokens

    def handle_annotation_pattern(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Handle statements like ``DEFINE ANNOTATION X AS PATTERN "Y"``.

        :raises: RedefinedAnnotationError
        """
        annotation = tokens['name']
        self.raise_for_redefined_annotation(line, position, annotation)
        self.annotation_to_pattern[annotation] = re.compile(tokens['value'])
        return tokens

    def has_enumerated_annotation(self, annotation: str) -> bool:
        """Check if this annotation is defined by an enumeration."""
        return annotation in self.annotation_to_term

    def has_regex_annotation(self, annotation: str) -> bool:
        """Check if this annotation is defined by a regular expression."""
        return annotation in self.annotation_to_pattern

    def has_local_annotation(self, annotation: str) -> bool:
        """Check if this annotation is defined by an locally."""
        return annotation in self.annotation_to_local

    def has_annotation(self, annotation: str) -> bool:
        """Check if this annotation is defined."""
        return (
            self.has_enumerated_annotation(annotation) or
            self.has_regex_annotation(annotation) or
            self.has_local_annotation(annotation)
        )

    def has_enumerated_namespace(self, namespace: str) -> bool:
        """Check if this namespace is defined by an enumeration."""
        return namespace in self.namespace_to_term

    def has_regex_namespace(self, namespace: str) -> bool:
        """Check if this namespace is defined by a regular expression."""
        return namespace in self.namespace_to_pattern

    def has_namespace(self, namespace: str) -> bool:
        """Check if this namespace is defined."""
        return self.has_enumerated_namespace(namespace) or self.has_regex_namespace(namespace)

    def raise_for_version(self, line: str, position: int, version: str) -> None:
        """Check that a version string is valid for BEL documents.

        This means it's either in the YYYYMMDD or semantic version format.

        :param line: The line being parsed
        :param position: The position in the line being parsed
        :param str version: A version string
        :raises: VersionFormatWarning
        """
        if valid_date_version(version):
            return

        if not SEMANTIC_VERSION_STRING_RE.match(version):
            raise VersionFormatWarning(self.get_line_number(), line, position, version)
