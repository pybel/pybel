# -*- coding: utf-8 -*-

"""Shared utilities for writing BEL namespace and annotation files."""

import getpass
from typing import Iterable, Mapping, Optional

DATETIME_FMT = '%Y-%m-%dT%H:%M:%S'


def iter_author_header(name: Optional[str] = None,
                       contact: Optional[str] = None,
                       copyright_str: Optional[str] = None,
                       ) -> Iterable[str]:
    """Iterate over the lines of the ``[Author]`` section of a BELNS file.

    :param name: Namespace's authors
    :param contact: Namespace author's contact info/email address
    :param copyright_str: Namespace's copyright/license information. Defaults to ``Other/Proprietary``
    """
    yield '[Author]'
    yield 'NameString={}'.format(name if name is not None else getpass.getuser())
    yield 'CopyrightString={}'.format('Other/Proprietary' if copyright_str is None else copyright_str)

    if contact is not None:
        yield 'ContactInfoString={}'.format(contact)


def iter_citation_header(name: str,
                         description: Optional[str] = None,
                         url: Optional[str] = None,
                         version: Optional[str] = None,
                         date: Optional[str] = None,
                         ) -> Iterable[str]:
    """Iterate over the lines of the ``[Citation]`` section of a BEL config file.

    :param name: Citation name
    :param description: Citation description
    :param url: URL to more citation information
    :param version: Citation version
    :param date: Citation publish timestamp, ISO 8601 Date
    """
    yield '[Citation]'
    yield 'NameString={}'.format(name)

    if date is not None:
        yield 'PublishedDate={}'.format(date)

    if version is not None:
        yield 'PublishedVersionString={}'.format(version)

    if description is not None:
        yield 'DescriptionString={}'.format(description)

    if url is not None:
        yield 'ReferenceURL={}'.format(url)


def iter_properties_header(case_sensitive: bool = True,
                           delimiter: str = '|',
                           cacheable: bool = True,
                           ) -> Iterable[str]:
    """Iterate over the lines of the ``[Processing]`` section of a BEL config file.

    :param case_sensitive: Should this config file be interpreted as case-sensitive?
    :param delimiter: The delimiter between names and labels in this config file
    :param cacheable: Should this config file be cached?
    """
    yield '[Processing]'
    yield 'CaseSensitiveFlag={}'.format('yes' if case_sensitive else 'no')
    yield 'DelimiterString={}'.format(delimiter)
    yield 'CacheableFlag={}'.format('yes' if cacheable else 'no')


def iter_body(values: Mapping[str, str],
              delimiter: str = '|',
              ) -> Iterable[str]:
    """Iterate over the lines of the ``[Values]`` section of a BEL resource file.

    :param values: A dictionary of labels to their encodings
    :param delimiter: The delimiter between names and labels in this config file
    """
    if not isinstance(values, Mapping):
        raise TypeError('values must be a Mapping ')

    yield '[Values]'

    for key, value in sorted(values.items()):
        if not key:
            continue

        key = str(key).strip()

        if not key:
            continue

        yield '{}{}{}'.format(key, delimiter, value)
