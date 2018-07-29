# -*- coding: utf-8 -*-

"""This module supports the relation parser by handling statements."""

import logging
import re

from pyparsing import And, MatchFirst, Suppress, Word, pyparsing_common as ppc

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
    '(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:-(?P<release>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?')

MALFORMED_VERSION_STRING_RE = re.compile('(?P<major>\d+)(\.(?P<minor>\d+)(\.(?P<patch>\d+))?)?')


class MetadataParser(BaseParser):
    """A parser for the document and definitions section of a BEL document.

    .. seealso::

        BEL 1.0 Specification for the `DEFINE <http://openbel.org/language/web/version_1.0/bel_specification_version_1.0.html#_define>`_ keyword
    """

    def __init__(self, manager, namespace_dict=None, annotation_dict=None, namespace_regex=None,
                 annotation_regex=None, default_namespace=None, allow_redefinition=False):
        """Build a metadata parser.

        :param pybel.manager.Manager manager: A cache manager
        :param dict[str,dict[str,str]] namespace_dict: A dictionary of pre-loaded, enumerated namespaces from
                                {namespace keyword: {name: encoding}}
        :param dict[str,set[str] annotation_dict: A dictionary of pre-loaded, enumerated annotations from
                                {annotation keyword: set of valid values}
        :param dict[str,str] namespace_regex: A dictionary of pre-loaded, regular expression namespaces from
                                {namespace keyword: regex string}
        :param dict[str,str] annotation_regex: A dictionary of pre-loaded, regular expression annotations from
                                {annotation keyword: regex string}
        :param set[str] default_namespace: A set of strings that can be used without a namespace
        """
        #: This metadata parser's internal definition cache manager
        self.manager = manager

        self.disallow_redefinition = not allow_redefinition

        #: A dictionary of cached {namespace keyword: {name: encoding}}
        self.namespace_dict = {} if namespace_dict is None else namespace_dict
        #: A dictionary of cached {annotation keyword: set of values}
        self.annotation_dict = {} if annotation_dict is None else annotation_dict
        #: A dictionary of {namespace keyword: regular expression string}
        self.namespace_regex = {} if namespace_regex is None else namespace_regex
        #: A set of names that can be used without a namespace
        self.default_namespace = set(default_namespace) if default_namespace is not None else None
        #: A dictionary of {annotation keyword: regular expression string}
        self.annotation_regex = {} if annotation_regex is None else annotation_regex

        #: A set of namespaces's URLs that can't be cached
        self.uncachable_namespaces = set()

        #: A dictionary containing the document metadata
        self.document_metadata = {}

        #: A dictionary from {namespace keyword: BEL namespace URL}
        self.namespace_url_dict = {}
        #: A dictionary from {annotation keyword: BEL annotation URL}
        self.annotation_url_dict = {}
        #: A set of annotation keywords that are defined ad-hoc in the BEL script
        self.annotation_lists = set()

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

    def handle_document(self, line, position, tokens):
        """Handle statements like ``SET DOCUMENT X = "Y"``.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        """
        key = tokens['key']
        value = tokens['value']

        if key not in DOCUMENT_KEYS:
            raise InvalidMetadataException(self.line_number, line, position, key, value)

        norm_key = DOCUMENT_KEYS[key]

        if norm_key in self.document_metadata:
            log.warning('Tried to overwrite metadata: %s', key)
            return tokens

        self.document_metadata[norm_key] = value

        if norm_key == METADATA_VERSION:
            self.raise_for_version(line, position, value)

        return tokens

    def raise_for_redefined_namespace(self, line, position, namespace):
        """Raise an exception if a namespace is already defined.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param str namespace: The namespace being parsed
        :raises: RedefinedNamespaceError
        """
        if self.disallow_redefinition and self.has_namespace(namespace):
            raise RedefinedNamespaceError(self.line_number, line, position, namespace)

    def handle_namespace_url(self, line, position, tokens):
        """Handle statements like ``DEFINE NAMESPACE X AS URL "Y"``.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        :raises: RedefinedNamespaceError
        :raises: pybel.resources.exc.ResourceError
        """
        namespace = tokens['name']
        self.raise_for_redefined_namespace(line, position, namespace)

        url = tokens['url']

        namespace_result = self.manager.ensure_namespace(url)

        if isinstance(namespace_result, dict):
            self.namespace_dict[namespace] = namespace_result
            self.uncachable_namespaces.add(url)
        else:
            self.namespace_dict[namespace] = namespace_result.to_values()

        self.namespace_url_dict[namespace] = url

        return tokens

    def handle_namespace_pattern(self, line, position, tokens):
        """Handle statements like ``DEFINE NAMESPACE X AS PATTERN "Y"``.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        :raises: RedefinedNamespaceError
        """
        namespace = tokens['name']
        self.raise_for_redefined_namespace(line, position, namespace)

        self.namespace_regex[namespace] = tokens['value']

        return tokens

    def raise_for_redefined_annotation(self, line, position, annotation):
        """Raise an exception if the given annotation is already defined.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param str annotation: The annotation being parsed
        :raises: RedefinedAnnotationError
        """
        if self.disallow_redefinition and self.has_annotation(annotation):
            raise RedefinedAnnotationError(self.line_number, line, position, annotation)

    def handle_annotations_url(self, line, position, tokens):
        """Handle statements like ``DEFINE ANNOTATION X AS URL "Y"``.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        :raises: RedefinedAnnotationError
        """
        keyword = tokens['name']
        self.raise_for_redefined_annotation(line, position, keyword)

        url = tokens['url']
        self.annotation_dict[keyword] = self.manager.get_annotation_entry_names(url)
        self.annotation_url_dict[keyword] = url

        return tokens

    def handle_annotation_list(self, line, position, tokens):
        """Handle statements like ``DEFINE ANNOTATION X AS LIST {"Y","Z", ...}``.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        :raises: RedefinedAnnotationError
        """
        annotation = tokens['name']
        self.raise_for_redefined_annotation(line, position, annotation)

        values = set(tokens['values'])

        self.annotation_dict[annotation] = values
        self.annotation_lists.add(annotation)

        return tokens

    def handle_annotation_pattern(self, line, position, tokens):
        """Handle statements like ``DEFINE ANNOTATION X AS PATTERN "Y"``.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        :raises: RedefinedAnnotationError
        """
        annotation = tokens['name']
        self.raise_for_redefined_annotation(line, position, annotation)
        self.annotation_regex[annotation] = tokens['value']
        return tokens

    def has_enumerated_annotation(self, annotation):
        """Check if this annotation is defined by an enumeration.

        :param str annotation: The keyword of a annotation
        :rtype: bool
        """
        return annotation in self.annotation_dict

    def has_regex_annotation(self, annotation):
        """Check if this annotation is defined by a regular expression.

        :param str annotation: The keyword of a annotation
        :rtype: bool
        """
        return annotation in self.annotation_regex

    def has_annotation(self, annotation):
        """Check if this annotation is defined.

        :param str annotation: The keyword of a annotation
        :rtype: bool
        """
        return self.has_enumerated_annotation(annotation) or self.has_regex_annotation(annotation)

    def has_enumerated_namespace(self, namespace):
        """Check if this namespace is defined by an enumeration.

        :param str namespace: The keyword of a namespace
        :rtype: bool
        """
        return namespace in self.namespace_dict

    def has_regex_namespace(self, namespace):
        """Check if this namespace is defined by a regular expression.

        :param str namespace: The keyword of a namespace
        :rtype: bool
        """
        return namespace in self.namespace_regex

    def has_namespace(self, namespace):
        """Check if this namespace is defined.

        :param str namespace: The keyword of a namespace
        :rtype: bool
        """
        return self.has_enumerated_namespace(namespace) or self.has_regex_namespace(namespace)

    def raise_for_version(self, line, position, version):
        """Check that a version string is valid for BEL documents.

        This means it's either in the YYYYMMDD or semantic version format.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param str version: A version string
        :raises: VersionFormatWarning
        """
        if valid_date_version(version):
            return

        if not SEMANTIC_VERSION_STRING_RE.match(version):
            raise VersionFormatWarning(self.line_number, line, position, version)
