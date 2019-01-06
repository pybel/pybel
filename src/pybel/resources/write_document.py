# -*- coding: utf-8 -*-

"""Utilities for reading BEL Script."""

import time
from typing import Iterable, Mapping, Optional, Set

from .constants import (
    ANNOTATION_PATTERN_FMT, ANNOTATION_URL_FMT, NAMESPACE_PATTERN_FMT, NAMESPACE_URL_FMT, format_annotation_list,
)
from ..constants import VERSION

__all__ = [
    'make_knowledge_header',
]


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
    yield from make_document_metadata(
        name=name,
        contact=contact,
        description=description,
        authors=authors,
        version=version,
        copyright=copyright,
        licenses=licenses,
        disclaimer=disclaimer,
    )

    yield from make_document_namespaces(
        namespace_url=namespace_url,
        namespace_patterns=namespace_patterns,
    )

    yield from make_document_annotations(
        annotation_url=annotation_url,
        annotation_patterns=annotation_patterns,
        annotation_list=annotation_list,
    )

    yield '#' * 80
    yield '#| Statements'
    yield '#' * 80 + '\n'


def make_document_metadata(name: str,
                           version: Optional[str] = None,
                           contact: Optional[str] = None,
                           description: Optional[str] = None,
                           authors: Optional[str] = None,
                           copyright: Optional[str] = None,
                           licenses: Optional[str] = None,
                           disclaimer: Optional[str] = None,
                           ) -> Iterable[str]:
    """Iterate over the lines for the document metadata section of a BEL document.

    :param name: The unique name for this BEL document
    :param version: The version. Defaults to the current date in ``YYYYMMDD`` format.
    :param description: A description of the contents of this document
    :param authors: The authors of this document
    :param contact: The email address of the maintainer
    :param copyright: Copyright information about this document
    :param licenses: The license applied to this document
    :param disclaimer: The disclaimer for this document
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
    """
    yield '#' * 80
    yield '#| Namespaces'
    yield '#' * 80 + '\n'

    if namespace_url:
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
    """
    if annotation_url or annotation_patterns or annotation_list:
        yield '#' * 80
        yield '#| Annotations'
        yield '#' * 80 + '\n'

    if annotation_url:
        yield '# Enumerated Annotations\n'
        for name, url in sorted(annotation_url.items()):
            yield ANNOTATION_URL_FMT.format(name, url)

    if annotation_patterns:
        yield '# Regular Expression Annotations\n'
        for name, pattern in sorted(annotation_patterns.items()):
            yield ANNOTATION_PATTERN_FMT.format(name, pattern)

    if annotation_list:
        yield '# Locally Defined Annotations\n'
        for annotation, values in sorted(annotation_list.items()):
            yield format_annotation_list(annotation, values)

    yield ''
