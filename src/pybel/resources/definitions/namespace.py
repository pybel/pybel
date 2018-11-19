# -*- coding: utf-8 -*-

from __future__ import print_function

import time
from collections import Iterable, Mapping

from pybel.constants import NAMESPACE_DOMAIN_OTHER, NAMESPACE_DOMAIN_TYPES, belns_encodings
from pybel.resources.utils import get_iso_8601_date
from .write_utils import DATETIME_FMT, make_author_header, make_citation_header, make_properties_header

__all__ = [
    'write_namespace',
]


def write_namespace(values, namespace_name, namespace_keyword, namespace_domain=None, author_name=None,
                    citation_name=None, namespace_description=None, namespace_species=None, namespace_version=None,
                    namespace_query_url=None, namespace_created=None, author_contact=None, author_copyright=None,
                    citation_description=None, citation_url=None, citation_version=None, citation_date=None,
                    case_sensitive=True, delimiter='|', cacheable=True, functions=None, file=None, value_prefix='',
                    sort_key=None):
    """Write a BEL namespace (BELNS) to a file.

    :param values: An iterable of values (strings) or dictionary of values to their encodings
    :type values: iter[str] or dict[str,str]
    :param str namespace_name: The namespace nam
    :param str namespace_keyword: Preferred BEL Keyword, maximum length of 8 (corresponds to MIRIAM namespace)
    :param Optional[str] namespace_domain: One of: :data:`pybel.constants.NAMESPACE_DOMAIN_BIOPROCESS`,
     :data:`pybel.constants.NAMESPACE_DOMAIN_CHEMICAL`, :data:`pybel.constants.NAMESPACE_DOMAIN_GENE`, or
     :data:`pybel.constants.NAMESPACE_DOMAIN_OTHER`
    :param Optional[str] author_name: The namespace's authors
    :param Optional[str] citation_name: The name of the citation
    :param Optional[str] namespace_query_url: HTTP URL to query for details on namespace values (must be valid URL)
    :param Optional[str] namespace_description: Namespace description
    :param Optional[str] namespace_species: Comma-separated list of species taxonomy id's
    :param Optional[str] namespace_version: Namespace version
    :param Optional[str] namespace_created: Namespace public timestamp, ISO 8601 datetime
    :param Optional[str] author_contact: Namespace author's contact info/email address
    :param Optional[str] author_copyright: Namespace's copyright/license information
    :param Optional[str] citation_description: Citation description
    :param Optional[str] citation_url: URL to more citation information
    :param Optional[str] citation_version: Citation version
    :param Optional[str] citation_date: Citation publish timestamp, ISO 8601 Date
    :param bool case_sensitive: Should this config file be interpreted as case-sensitive?
    :param str delimiter: The delimiter between names and labels in this config file
    :param bool cacheable: Should this config file be cached?
    :param Optional[str] functions: The encoding for the elements in this namespace. See :data:`pybel.constants.belns_encodings`
    :param Optional[file] file: A writable file or file-like
    :param str value_prefix: a prefix for each name
    :param sort_key: A function to sort the values with :func:`sorted`. Give ``False`` to not sort
    """
    write_namespace_header(
        namespace_name=namespace_name,
        namespace_keyword=namespace_keyword,
        namespace_domain=namespace_domain,
        author_name=author_name,
        citation_name=citation_name,
        namespace_description=namespace_description,
        namespace_species=namespace_species,
        namespace_version=namespace_version,
        namespace_query_url=namespace_query_url,
        namespace_created=namespace_created,
        author_contact=author_contact,
        author_copyright=author_copyright,
        citation_description=citation_description,
        citation_url=citation_url,
        citation_version=citation_version,
        citation_date=citation_date,
        case_sensitive=case_sensitive,
        delimiter=delimiter,
        cacheable=cacheable,
        file=file,
    )
    write_namespace_body(
        values,
        delimiter=delimiter,
        functions=functions,
        file=file,
        value_prefix=value_prefix,
        sort_key=sort_key,
    )


def write_namespace_body(values, delimiter='|', functions=None, file=None, value_prefix='', sort_key=None):
    """Writes the [Values] section of a BEL namespace file

    :param values: An iterable of values (strings) or dictionary of {label:encodings}
    :type values: iter[str] or dict[str,str]
    :param str delimiter: The delimiter between names and labels in this config file
    :param Optional[str] functions: The encoding for the elements in this namespace. See :data:`pybel.constants.belns_encodings`
    :param Optional[file] file: A writable file or file-like
    :param str value_prefix: a prefix for each name
    :param sort_key: A function to sort the values with :func:`sorted`. Give ``False`` to not sort
    """
    if isinstance(values, Mapping):
        entries = sorted(
            (k, ''.join(sorted(v if v is not None else belns_encodings)))
            for k, v in values.items()
        )

    elif isinstance(values, Iterable):
        function_values = ''.join(sorted(functions if functions is not None else belns_encodings.keys()))
        entries = [(k, function_values) for k in sorted(set(values), key=sort_key)]

    else:
        raise TypeError

    print('[Values]', file=file)

    for label, encodings in entries:
        if not label:
            continue

        label = str(label).strip()

        if not label:
            continue

        print('{}{}{}{}'.format(value_prefix, label, delimiter, encodings), file=file)


def write_namespace_header(namespace_name, namespace_keyword, namespace_domain=None, author_name=None,
                           citation_name=None, namespace_description=None, namespace_species=None,
                           namespace_version=None, namespace_query_url=None, namespace_created=None,
                           author_contact=None, author_copyright=None, citation_description=None, citation_url=None,
                           citation_version=None, citation_date=None, case_sensitive=True, delimiter='|',
                           cacheable=True, file=None):
    """Write a BEL namespace (BELNS) to a file.

    :param str namespace_name: The namespace name
    :param str namespace_keyword: Preferred BEL Keyword, maximum length of 8
    :param Optional[str] namespace_domain: One of: :data:`pybel.constants.NAMESPACE_DOMAIN_BIOPROCESS`,
     :data:`pybel.constants.NAMESPACE_DOMAIN_CHEMICAL`, :data:`pybel.constants.NAMESPACE_DOMAIN_GENE`, or
     :data:`pybel.constants.NAMESPACE_DOMAIN_OTHER`
    :param Optional[str] author_name: The namespace's authors
    :param Optional[str] citation_name: The name of the citation
    :param Optional[str] namespace_query_url: HTTP URL to query for details on namespace values (must be valid URL)
    :param Optional[str] namespace_description: Namespace description
    :param Optional[str] namespace_species: Comma-separated list of species taxonomy id's
    :param Optional[str] namespace_version: Namespace version
    :param Optional[str] namespace_created: Namespace public timestamp, ISO 8601 datetime
    :param Optional[str] author_contact: Namespace author's contact info/email address
    :param Optional[str] author_copyright: Namespace's copyright/license information
    :param Optional[str] citation_description: Citation description
    :param Optional[str] citation_url: URL to more citation information
    :param Optional[str] citation_version: Citation version
    :param Optional[str] citation_date: Citation publish timestamp, ISO 8601 Date
    :param bool case_sensitive: Should this config file be interpreted as case-sensitive?
    :param str delimiter: The delimiter between names and labels in this config file
    :param bool cacheable: Should this config file be cached?
    :param Optional[file] file: A writable file or file-like
    """
    namespace_header_lines = make_namespace_header(
        namespace_name,
        namespace_keyword,
        namespace_domain=namespace_domain,
        query_url=namespace_query_url,
        description=namespace_description,
        species=namespace_species,
        version=namespace_version,
        created=namespace_created
    )

    for line in namespace_header_lines:
        print(line, file=file)

    print(file=file)

    author_header_lines = make_author_header(
        author_name,
        contact=author_contact,
        copyright_str=author_copyright
    )

    for line in author_header_lines:
        print(line, file=file)

    print(file=file)

    citation_header_lines = make_citation_header(
        citation_name,
        description=citation_description,
        url=citation_url,
        version=citation_version,
        date=citation_date
    )

    for line in citation_header_lines:
        print(line, file=file)

    print(file=file)

    properties_header_lines = make_properties_header(
        case_sensitive=case_sensitive,
        delimiter=delimiter,
        cacheable=cacheable
    )

    for line in properties_header_lines:
        print(line, file=file)

    print(file=file)


def make_namespace_header(name, keyword, namespace_domain=None, query_url=None, description=None, species=None,
                          version=None, created=None):
    """Make the ``[Namespace]`` section of a BELNS file.

    :param str name: The namespace name
    :param str keyword: Preferred BEL Keyword, maximum length of 8
    :param Optional[str] namespace_domain: One of: :data:`pybel.constants.NAMESPACE_DOMAIN_BIOPROCESS`,
     :data:`pybel.constants.NAMESPACE_DOMAIN_CHEMICAL`, :data:`pybel.constants.NAMESPACE_DOMAIN_GENE`, or
     :data:`pybel.constants.NAMESPACE_DOMAIN_OTHER`
    :param Optional[str] query_url: HTTP URL to query for details on namespace values (must be valid URL)
    :param Optional[str] description: Namespace description
    :param Optional[str] species: Comma-separated list of species taxonomy id's
    :param Optional[str] version: Namespace version. Defaults to current date in ``YYYYMMDD`` format.
    :param Optional[str] created: Namespace public timestamp, ISO 8601 datetime
    :return: An iterator over the lines of the ``[Namespace]`` section of a BELNS file
    :rtype: iter[str]
    """
    if namespace_domain is None:
        namespace_domain = NAMESPACE_DOMAIN_OTHER

    if namespace_domain is not None and namespace_domain not in NAMESPACE_DOMAIN_TYPES:
        raise ValueError('Invalid domain: {}. Should be one of: {}'.format(namespace_domain, NAMESPACE_DOMAIN_TYPES))

    yield '[Namespace]'
    yield 'Keyword={}'.format(keyword)
    yield 'NameString={}'.format(name)

    if namespace_domain:
        yield 'DomainString={}'.format(namespace_domain)

    yield 'VersionString={}'.format(version if version else get_iso_8601_date())
    yield 'CreatedDateTime={}'.format(created if created else time.strftime(DATETIME_FMT))

    if description:
        yield 'DescriptionString={}'.format(description.strip().replace('\n', ''))

    if species is not None:
        yield 'SpeciesString={}'.format(species)

    if query_url is not None:
        yield 'QueryValueURL={}'.format(query_url)
