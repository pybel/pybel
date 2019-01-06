# -*- coding: utf-8 -*-

"""Utilities for writing BEL annotation files."""

import time
from itertools import chain
from typing import Iterable, Mapping, Optional, TextIO

from .utils import get_iso_8601_date
from .write_utils import DATETIME_FMT, iter_author_header, iter_body, iter_citation_header, iter_properties_header

__all__ = [
    'write_annotation',
]


def write_annotation(keyword: str,
                     values: Mapping[str, str],
                     citation_name: str,
                     description: str,
                     usage: Optional[str] = None,
                     version: Optional[str] = None,
                     created: Optional[str] = None,
                     author_name: Optional[str] = None,
                     author_copyright: Optional[str] = None,
                     author_contact: Optional[str] = None,
                     case_sensitive: bool = True,
                     delimiter: str = '|',
                     cacheable: bool = True,
                     file: Optional[TextIO] = None,
                     ) -> None:
    """Write a BEL annotation (BELANNO) to a file.

    :param keyword: The annotation keyword
    :param values: A dictionary of {name: label}
    :param citation_name: The citation name
    :param description: A description of this annotation
    :param usage: How to use this annotation
    :param version: The version of this annotation. Defaults to date in ``YYYYMMDD`` format.
    :param created: The annotation's public timestamp, ISO 8601 datetime
    :param author_name: The author's name
    :param author_copyright: The copyright information for this annotation. Defaults to ``Other/Proprietary``
    :param author_contact: The contact information for the author of this annotation.
    :param case_sensitive: Should this config file be interpreted as case-sensitive?
    :param delimiter: The delimiter between names and labels in this config file
    :param cacheable: Should this config file be cached?
    :param file: A writable file or file-like
    """
    values = {
        key.strip(): value.strip().replace('\n', '')
        for key, value in values.items()
    }

    nominal_lines = iter_annotation_nominal(
        keyword,
        description=description,
        usage=usage,
        version=version,
        created=created,
    )
    header_lines = iter_author_header(
        name=author_name,
        contact=author_contact,
        copyright_str=author_copyright,
    )
    citation_lines = iter_citation_header(
        name=citation_name,
    )
    property_lines = iter_properties_header(
        case_sensitive=case_sensitive,
        delimiter=delimiter,
        cacheable=cacheable,
    )
    body_lines = iter_body(
        values=values,
        delimiter=delimiter,
    )
    for line in chain(nominal_lines, header_lines, citation_lines, property_lines, body_lines):
        print(line, file=file)


def iter_annotation_nominal(keyword: str,
                            description: Optional[str] = None,
                            usage: Optional[str] = None,
                            version: Optional[str] = None,
                            created: Optional[str] = None,
                            ) -> Iterable[str]:
    """Iterate over the lines of the ``[AnnotationDefinition]`` section of a BELANNO file.

    :param keyword: Preferred BEL Keyword, maximum length of 8
    :param description: A description of this annotation
    :param usage: How to use this annotation
    :param version: Namespace version. Defaults to date in ``YYYYMMDD`` format.
    :param created: Namespace public timestamp, ISO 8601 datetime
    :return: A iterator over the lines for the ``[AnnotationDefinition]`` section
    """
    yield '[AnnotationDefinition]'
    yield 'Keyword={}'.format(keyword)
    yield 'TypeString={}'.format('list')
    yield 'VersionString={}'.format(version if version else get_iso_8601_date())
    yield 'CreatedDateTime={}'.format(created if created else time.strftime(DATETIME_FMT))

    if description is not None:
        yield 'DescriptionString={}'.format(description.strip().replace('\n', ''))

    if usage is not None:
        yield 'UsageString={}'.format(usage.strip().replace('\n', ''))
