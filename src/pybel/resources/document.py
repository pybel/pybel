# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import itertools as itt

import logging
import time

from .constants import (
    ANNOTATION_PATTERN_FMT, ANNOTATION_URL_FMT, METADATA_LINE_RE, NAMESPACE_PATTERN_FMT, NAMESPACE_URL_FMT,
    format_annotation_list,
)
from ..constants import VERSION

log = logging.getLogger(__name__)


def sanitize_file_line_iter(f, note_char=':'):
    """Enumerates the given lines and removes empty lines/comments

    :param iter[str] f: An iterable over strings
    :param str note_char: The character sequence denoting a special note
    :rtype: iter[tuple[int,str]]
    """
    for line_number, line in enumerate(f, start=1):
        line = line.strip()

        if not line:
            continue

        if line[0] == '#':
            if len(line) > 1 and line[1] == note_char:
                log.info('NOTE: Line %d: %s', line_number, line)
            continue

        yield line_number, line


def sanitize_file_lines(f):
    """Enumerates a line iterator and returns the pairs of (line number, line) that are cleaned

    :param iter[str] f: An iterable of strings
    :rtype: iter[tuple[int,str]]
    """
    it = sanitize_file_line_iter(f)

    for line_number, line in it:
        if line.endswith('\\'):
            log.log(4, 'Multiline quote starting on line: %d', line_number)
            line = line.strip('\\').strip()
            next_line_number, next_line = next(it)
            while next_line.endswith('\\'):
                log.log(3, 'Extending line: %s', next_line)
                line += " " + next_line.strip('\\').strip()
                next_line_number, next_line = next(it)
            line += " " + next_line.strip()
            log.log(3, 'Final line: %s', line)

        elif 1 == line.count('"'):
            log.log(4, 'PyBEL013 Missing new line escapes [line: %d]', line_number)
            next_line_number, next_line = next(it)
            next_line = next_line.strip()
            while not next_line.endswith('"'):
                log.log(3, 'Extending line: %s', next_line)
                line = '{} {}'.format(line.strip(), next_line)
                next_line_number, next_line = next(it)
                next_line = next_line.strip()
            line = '{} {}'.format(line, next_line)
            log.log(3, 'Final line: %s', line)

        comment_loc = line.rfind(' //')
        if 0 <= comment_loc:
            line = line[:comment_loc]

        yield line_number, line


def split_file_to_annotations_and_definitions(file):
    """Enumerates a line iterable and splits into 3 parts

    :param iter[str] file:
    :rtype: tuple[list[str],list[str],list[str]]
    """
    content = list(sanitize_file_lines(file))

    end_document_section_index = 1 + max(
        index
        for index, (_, line) in enumerate(content)
        if line.startswith('SET DOCUMENT')
    )

    end_definitions_section_index = 1 + max(
        index
        for index, (_, line)
        in enumerate(content)
        if METADATA_LINE_RE.match(line)
    )

    log.info('File length: %d lines', len(content))
    documents = content[:end_document_section_index]
    definitions = content[end_document_section_index:end_definitions_section_index]
    statements = content[end_definitions_section_index:]

    return documents, definitions, statements


def make_document_metadata(name, version=None, contact=None, description=None, authors=None, copyright=None,
                           licenses=None, disclaimer=None):
    """Builds a list of lines for the document metadata section of a BEL document

    :param str name: The unique name for this BEL document
    :param Optional[str] version: The version. Defaults to the current date in ``YYYYMMDD`` format.
    :param Optional[str] description: A description of the contents of this document
    :param Optional[str] authors: The authors of this document
    :param Optional[str] contact: The email address of the maintainer
    :param Optional[str] copyright: Copyright information about this document
    :param Optional[str] licenses: The license applied to this document
    :param Optional[str] disclaimer: The disclaimer for this document
    :return: An iterator over the lines for the document metadata section
    :rtype: iter[str]
    """
    yield '# This document was created by PyBEL v{} on {}\n'.format(VERSION, time.asctime())

    yield '#' * 80
    yield '#| Metadata'
    yield '#' * 80 + '\n'

    yield 'SET DOCUMENT Name = "{}"'.format(name)
    yield 'SET DOCUMENT Version = "{}"'.format(version if version else time.strftime('%Y%m%d'))

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


def make_document_namespaces(namespace_url=None, namespace_patterns=None):
    """Builds a list of lines for the namespace definitions

    :param Optional[dict[str,str]] namespace_url: dictionary of {str name: str URL} of namespaces
    :param Optional[dict[str,str]] namespace_owl: dictionary of {str name: str URL} of namespaces
    :param Optional[dict[str,str]] namespace_patterns: A dictionary of {str name: str regex}
    :return: An iterator over the lines for the namespace definitions
    :rtype: iter[str]
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


def make_document_annotations(annotation_url=None, annotation_patterns=None, annotation_list=None):
    """Builds a list of lines for the annotation definitions

    :param Optional[dict[str,str]] annotation_url: A dictionary of {str name: str URL} of annotations
    :param Optional[dict[str,str]] annotation_owl: A dictionary of {str name: str URL} of annotations from OWL
    :param Optional[dict[str,str]] annotation_patterns: A dictionary of {str name: str regex}
    :param Optional[dict[str,set[str]]] annotation_list: A dictionary of {str name: set of name str}
    :return: An iterator over the lines for the annotation definitions
    :rtype: iter[str]
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


def make_knowledge_header(name, version=None, description=None, authors=None, contact=None, copyright=None,
                          licenses=None, disclaimer=None, namespace_url=None, namespace_patterns=None,
                          annotation_url=None, annotation_patterns=None, annotation_list=None, ):
    """Iterates over the strings for the header of a BEL document, with standard document metadata, definitions.

    :param str name: The unique name for this BEL document
    :param str contact: The email address of the maintainer
    :param str description: A description of the contents of this document
    :param str authors: The authors of this document
    :param str version: The version. Defaults to current date in format ``YYYYMMDD``.
    :param str copyright: Copyright information about this document
    :param str licenses: The license applied to this document
    :param str disclaimer: The disclaimer for this document
    :param Optional[dict[str,str]] namespace_url: an optional dictionary of {str name: str URL} of namespaces
    :param Optional[dict[str,str]] namespace_owl: an optional dictionary of {str name: str URL} of namespaces
    :param Optional[dict[str,str]] namespace_patterns: An optional dictionary of {str name: str regex} namespaces
    :param Optional[dict[str,str]] annotation_url: An optional dictionary of {str name: str URL} of annotations
    :param Optional[dict[str,str]] annotation_owl: An optional dictionary of {str name: str URL} of OWL annotations
    :param Optional[dict[str,str]] annotation_patterns: An optional dictionary of {str name: str regex} of regex
     annotations
    :param Optional[dict[str,set[str]]] annotation_list: An optional dictionary of {str name: set of names} of list
     annotations
    :rtype: iter[str]
    """
    metadata_iter = make_document_metadata(
        name=name,
        contact=contact,
        description=description,
        authors=authors,
        version=version,
        copyright=copyright,
        licenses=licenses,
        disclaimer=disclaimer
    )

    namespaces_iter = make_document_namespaces(
        namespace_url=namespace_url,
        namespace_patterns=namespace_patterns
    )

    annotations_iter = make_document_annotations(
        annotation_url=annotation_url,
        annotation_patterns=annotation_patterns,
        annotation_list=annotation_list
    )

    for line in itt.chain(metadata_iter, namespaces_iter, annotations_iter):
        yield line

    yield '#' * 80
    yield '#| Statements'
    yield '#' * 80 + '\n'
