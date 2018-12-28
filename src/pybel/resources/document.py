# -*- coding: utf-8 -*-

"""Utilities for reading BEL Script."""

import itertools as itt
import logging
import time
from typing import Iterable, Mapping, Optional, Set, Tuple

from .constants import (
    ANNOTATION_PATTERN_FMT, ANNOTATION_URL_FMT, METADATA_LINE_RE, NAMESPACE_PATTERN_FMT, NAMESPACE_URL_FMT,
    format_annotation_list,
)
from ..constants import VERSION

log = logging.getLogger(__name__)

EnumLines = Iterable[Tuple[int, str]]


def sanitize_file_line_iter(file: Iterable[str], note_char: str = ':') -> EnumLines:
    """Clean a line iterator by removing extra whitespace, blank lines, comment lines, and log nodes.

    :param file: An iterable over the lines in a BEL Script
    :param note_char: The character sequence denoting a special note
    :returns: An iterator over the line number and the lines that should be processed
    """
    for line_number, line in enumerate(file, start=1):
        line = line.strip()

        if not line:
            continue

        if line[0] == '#':
            if len(line) > 1 and line[1] == note_char:
                log.info('NOTE: Line %d: %s', line_number, line)
            continue

        yield line_number, line


def sanitize_file_lines(file: Iterable[str]) -> EnumLines:
    """Enumerate a line iterator and returns the pairs of (line number, line) that are cleaned."""
    line_iterator = sanitize_file_line_iter(file)

    for line_number, line in line_iterator:
        if line.endswith('\\'):
            log.log(4, 'Multiline quote starting on line: %d', line_number)
            line = line.strip('\\').strip()
            next_line_number, next_line = next(line_iterator)
            while next_line.endswith('\\'):
                log.log(3, 'Extending line: %s', next_line)
                line += " " + next_line.strip('\\').strip()
                next_line_number, next_line = next(line_iterator)
            line += " " + next_line.strip()
            log.log(3, 'Final line: %s', line)

        elif 1 == line.count('"'):
            log.log(4, 'PyBEL013 Missing new line escapes [line: %d]', line_number)
            next_line_number, next_line = next(line_iterator)
            next_line = next_line.strip()
            while not next_line.endswith('"'):
                log.log(3, 'Extending line: %s', next_line)
                line = '{} {}'.format(line.strip(), next_line)
                next_line_number, next_line = next(line_iterator)
                next_line = next_line.strip()
            line = '{} {}'.format(line, next_line)
            log.log(3, 'Final line: %s', line)

        comment_loc = line.rfind(' //')
        if 0 <= comment_loc:
            line = line[:comment_loc]

        yield line_number, line


def split_file_to_annotations_and_definitions(file: Iterable[str]) -> Tuple[EnumLines, EnumLines, EnumLines]:
    """Enumerate a line iterable and splits into 3 parts."""
    line_number_line_pairs = iter(sanitize_file_lines(file))

    last_value = {0: (None, None)}  # just do this because python2 doesn't allow nonlocal variables

    def document_metadata() -> EnumLines:
        """Iterate over the document metadata lines."""
        for i, line in line_number_line_pairs:
            if not line.startswith('SET DOCUMENT'):
                last_value[0] = i, line
                return
            yield i, line

    def definitions() -> EnumLines:
        """Iterate over the resource definition lines."""
        yield last_value[0]
        for i, line in line_number_line_pairs:
            if not METADATA_LINE_RE.match(line):
                last_value[0] = i, line
                return
            yield i, line

    def statements() -> EnumLines:
        """Iterate over the statement lines."""
        yield last_value[0]
        for line_number_line_pari in line_number_line_pairs:
            yield line_number_line_pari

    return document_metadata(), definitions(), statements()


def make_document_metadata(name: str,
                           version: Optional[str] = None,
                           contact: Optional[str] = None,
                           description: Optional[str] = None,
                           authors: Optional[str] = None,
                           copyright: Optional[str] = None,
                           licenses: Optional[str] = None,
                           disclaimer: Optional[str] = None,
                           ) -> Iterable[str]:
    """Build a list of lines for the document metadata section of a BEL document.

    :param name: The unique name for this BEL document
    :param version: The version. Defaults to the current date in ``YYYYMMDD`` format.
    :param description: A description of the contents of this document
    :param authors: The authors of this document
    :param contact: The email address of the maintainer
    :param copyright: Copyright information about this document
    :param licenses: The license applied to this document
    :param disclaimer: The disclaimer for this document
    :return: An iterator over the lines for the document metadata section
    """
    yield '# This document was created by PyBEL v{} on {}\n'.format(VERSION, time.asctime())

    yield '#' * 80
    yield '#| Metadata'
    yield '#' * 80 + '\n'

    yield 'SET DOCUMENT Name = "{}"'.format(name)
    yield 'SET DOCUMENT Version = "{}"'.format(version or time.strftime('%Y%m%d'))

    if description:
        yield 'SET DOCUMENT Description = "{}"'.format(description.replace('\n', ''))

    if authors:
        yield 'SET DOCUMENT Authors = "{}"'.format(authors)

    if contact:
        yield 'SET DOCUMENT ContactInfo = "{}"'.format(contact)

    if licenses:
        yield 'SET DOCUMENT Licenses = "{}"'.format(licenses)

    if copyright:
        yield 'SET DOCUMENT Copyright = "{}"'.format(copyright)

    if disclaimer:
        yield 'SET DOCUMENT Disclaimer = "{}"'.format(disclaimer)

    yield ''


def make_document_namespaces(namespace_url: Optional[Mapping[str, str]] = None,
                             namespace_patterns: Optional[Mapping[str, str]] = None,
                             ) -> Iterable[str]:
    """Iterate over lines for the namespace definitions.

    :param namespace_url: dictionary of {str name: str URL} of namespaces
    :param namespace_patterns: A dictionary of {str name: str regex}
    :return: An iterator over the lines for the namespace definitions
    """
    yield '#' * 80
    yield '#| Namespaces'
    yield '#' * 80 + '\n'

    yield '# Enumerated Namespaces\n'

    for name, url in sorted(namespace_url.items()):
        yield NAMESPACE_URL_FMT.format(name, url)

    if namespace_patterns:
        yield '\n# Regular Expression Namespaces\n'

        for name, pattern in sorted(namespace_patterns.items()):
            yield NAMESPACE_PATTERN_FMT.format(name, pattern)

    yield ''


def make_document_annotations(annotation_url: Optional[Mapping[str, str]] = None,
                              annotation_patterns: Optional[Mapping[str, str]] = None,
                              annotation_list: Optional[Mapping[str, Set[str]]] = None,
                              ) -> Iterable[str]:
    """Iterate over lines for the annotation definitions.

    :param annotation_url: A dictionary of {str name: str URL} of annotations
    :param annotation_patterns: A dictionary of {str name: str regex}
    :param annotation_list: A dictionary of {str name: set of name str}
    :return: An iterator over the lines for the annotation definitions
    """
    if annotation_url or annotation_patterns or annotation_list:
        yield '#' * 80
        yield '#| Annotations'
        yield '#' * 80 + '\n'

    if annotation_url:
        for name, url in sorted(annotation_url.items()):
            yield ANNOTATION_URL_FMT.format(name, url)

    if annotation_patterns:
        for name, pattern in sorted(annotation_patterns.items()):
            yield ANNOTATION_PATTERN_FMT.format(name, pattern)

    if annotation_list:
        for annotation, values in sorted(annotation_list.items()):
            yield format_annotation_list(annotation, sorted(values))

    yield ''


def make_knowledge_header(name: str,
                          version: Optional[str] = None,
                          description: Optional[str] = None,
                          authors: Optional[str] = None,
                          contact: Optional[str] = None,
                          copyright: Optional[str] = None,
                          licenses: Optional[str] = None,
                          disclaimer: Optional[str] = None,
                          namespace_url: Optional[Mapping[str, str]] = None,
                          namespace_patterns: Optional[Mapping[str, str]] = None,
                          annotation_url: Optional[Mapping[str, str]] = None,
                          annotation_patterns: Optional[Mapping[str, str]] = None,
                          annotation_list: Optional[Mapping[str, Set[str]]] = None,
                          ) -> Iterable[str]:
    """Iterate over lines for the header of a BEL document, with standard document metadata and definitions.

    :param name: The unique name for this BEL document
    :param version: The version. Defaults to current date in format ``YYYYMMDD``.
    :param description: A description of the contents of this document
    :param authors: The authors of this document
    :param contact: The email address of the maintainer
    :param copyright: Copyright information about this document
    :param licenses: The license applied to this document
    :param disclaimer: The disclaimer for this document
    :param namespace_url: an optional dictionary of {str name: str URL} of namespaces
    :param namespace_patterns: An optional dictionary of {str name: str regex} namespaces
    :param annotation_url: An optional dictionary of {str name: str URL} of annotations
    :param annotation_patterns: An optional dictionary of {str name: str regex} of regex annotations
    :param annotation_list: An optional dictionary of {str name: set of names} of list annotations
    """
    metadata_iter = make_document_metadata(
        name=name,
        contact=contact,
        description=description,
        authors=authors,
        version=version,
        copyright=copyright,
        licenses=licenses,
        disclaimer=disclaimer,
    )

    namespaces_iter = make_document_namespaces(
        namespace_url=namespace_url,
        namespace_patterns=namespace_patterns,
    )

    annotations_iter = make_document_annotations(
        annotation_url=annotation_url,
        annotation_patterns=annotation_patterns,
        annotation_list=annotation_list,
    )

    for line in itt.chain(metadata_iter, namespaces_iter, annotations_iter):
        yield line

    yield '#' * 80
    yield '#| Statements'
    yield '#' * 80 + '\n'
