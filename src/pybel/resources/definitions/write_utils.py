# -*- coding: utf-8 -*-

import getpass

DATETIME_FMT = '%Y-%m-%dT%H:%M:%S'


def make_author_header(name=None, contact=None, copyright_str=None):
    """Makes the ``[Author]`` section of a BELNS file

    :param str name: Namespace's authors
    :param str contact: Namespace author's contact info/email address
    :param str copyright_str: Namespace's copyright/license information. Defaults to ``Other/Proprietary``
    :return: An iterable over the lines of the ``[Author]`` section of a BELNS file
    :rtype: iter[str]
    """
    yield '[Author]'
    yield 'NameString={}'.format(name if name is not None else getpass.getuser())
    yield 'CopyrightString={}'.format('Other/Proprietary' if copyright_str is None else copyright_str)

    if contact is not None:
        yield 'ContactInfoString={}'.format(contact)


def make_citation_header(name, description=None, url=None, version=None, date=None):
    """Makes the ``[Citation]`` section of a BEL config file.

    :param str name: Citation name
    :param str description: Citation description
    :param str url: URL to more citation information
    :param str version: Citation version
    :param str date: Citation publish timestamp, ISO 8601 Date
    :return: An iterable over the lines of the ``[Citation]`` section of a BEL config file
    :rtype: iter[str]
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


def make_properties_header(case_sensitive=True, delimiter='|', cacheable=True):
    """Makes the ``[Processing]`` section of a BEL config file.

    :param bool case_sensitive: Should this config file be interpreted as case-sensitive?
    :param str delimiter: The delimiter between names and labels in this config file
    :param bool cacheable: Should this config file be cached?
    :return: An iterable over the lines of the ``[Processing]`` section of a BEL config file
    :rtype: iter[str]
    """
    yield '[Processing]'
    yield 'CaseSensitiveFlag={}'.format('yes' if case_sensitive else 'no')
    yield 'DelimiterString={}'.format(delimiter)
    yield 'CacheableFlag={}'.format('yes' if cacheable else 'no')
