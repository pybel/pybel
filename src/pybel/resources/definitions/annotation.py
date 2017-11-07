# -*- coding: utf-8 -*-

from __future__ import print_function

import time

from .write_utils import DATETIME_FMT, make_author_header, make_properties_header
from ..utils import get_iso_8601_date

__all__ = [
    'write_annotation'
]


def make_annotation_header(keyword, description=None, usage=None, version=None, created=None):
    """Makes the ``[AnnotationDefinition]`` section of a BELANNO file

    :param str keyword: Preferred BEL Keyword, maximum length of 8
    :param str description: A description of this annotation
    :param str usage: How to use this annotation
    :param str version: Namespace version. Defaults to date in ``YYYYMMDD`` format.
    :param str created: Namespace public timestamp, ISO 8601 datetime
    :return: A iterator over the lines for the ``[AnnotationDefinition]`` section
    :rtype: iter[str]
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


def write_annotation(keyword, values, citation_name, description, usage=None, version=None, created=None,
                     author_name=None, author_copyright=None, author_contact=None, case_sensitive=True, delimiter='|',
                     cacheable=True, file=None, value_prefix=''):
    """Writes a BEL annotation (BELANNO) to a file

    :param str keyword: The annotation keyword
    :param dict[str, str] values: A dictionary of {name: label}
    :param str citation_name: The citation name
    :param str description: A description of this annotation
    :param str usage: How to use this annotation
    :param str version: The version of this annotation. Defaults to date in ``YYYYMMDD`` format.
    :param str created: The annotation's public timestamp, ISO 8601 datetime
    :param str author_name: The author's name
    :param str author_copyright: The copyright information for this annotation. Defaults to ``Other/Proprietary``
    :param str author_contact: The contact information for the author of this annotation.
    :param bool case_sensitive: Should this config file be interpreted as case-sensitive?
    :param str delimiter: The delimiter between names and labels in this config file
    :param bool cacheable: Should this config file be cached?
    :param file file: A writable file or file-like
    :param str value_prefix: An optional prefix for all values
    """
    for line in make_annotation_header(keyword, description=description, usage=usage, version=version, created=created):
        print(line, file=file)
    print(file=file)

    for line in make_author_header(name=author_name, contact=author_contact, copyright_str=author_copyright):
        print(line, file=file)
    print(file=file)

    print('[Citation]', file=file)
    print('NameString={}'.format(citation_name), file=file)
    print(file=file)

    for line in make_properties_header(case_sensitive=case_sensitive, delimiter=delimiter, cacheable=cacheable):
        print(line, file=file)
    print(file=file)

    print('[Values]', file=file)
    for key, value in sorted(values.items()):
        if not key.strip():
            continue
        print('{}{}|{}'.format(value_prefix, key.strip(), value.strip().replace('\n', '')), file=file)
