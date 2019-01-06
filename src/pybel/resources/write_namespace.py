# -*- coding: utf-8 -*-

"""Utilities for writing BEL namespace files."""

import time
from itertools import chain
from typing import Iterable, Mapping, Optional, TextIO

from .utils import get_iso_8601_date
from .write_utils import DATETIME_FMT, iter_author_header, iter_body, iter_citation_header, iter_properties_header
from ..constants import NAMESPACE_DOMAIN_OTHER, NAMESPACE_DOMAIN_TYPES

__all__ = [
    'write_namespace',
]


def write_namespace(values: Mapping[str, str],
                    namespace_name: str,
                    namespace_keyword: str,
                    namespace_domain: Optional[str] = None,
                    author_name: Optional[str] = None,
                    citation_name: Optional[str] = None,
                    namespace_description: Optional[str] = None,
                    namespace_species: Optional[str] = None,
                    namespace_version: Optional[str] = None,
                    namespace_query_url: Optional[str] = None,
                    namespace_created: Optional[str] = None,
                    author_contact: Optional[str] = None,
                    author_copyright: Optional[str] = None,
                    citation_description: Optional[str] = None,
                    citation_url: Optional[str] = None,
                    citation_version: Optional[str] = None,
                    citation_date: Optional[str] = None,
                    case_sensitive: bool = True,
                    delimiter: str = '|',
                    cacheable: bool = True,
                    file: Optional[TextIO] = None,
                    ) -> None:
    """Write a BEL namespace (BELNS) to a file.

    :param values: A dictionary of values to their encodings
    :param namespace_name: The namespace nam
    :param namespace_keyword: Preferred BEL Keyword, maximum length of 8 (corresponds to MIRIAM namespace)
    :param namespace_domain: One of: :data:`pybel.constants.NAMESPACE_DOMAIN_BIOPROCESS`,
     :data:`pybel.constants.NAMESPACE_DOMAIN_CHEMICAL`, :data:`pybel.constants.NAMESPACE_DOMAIN_GENE`, or
     :data:`pybel.constants.NAMESPACE_DOMAIN_OTHER`
    :param author_name: The namespace's authors
    :param citation_name: The name of the citation
    :param namespace_query_url: HTTP URL to query for details on namespace values (must be valid URL)
    :param namespace_description: Namespace description
    :param namespace_species: Comma-separated list of species taxonomy id's
    :param namespace_version: Namespace version
    :param namespace_created: Namespace public timestamp, ISO 8601 datetime
    :param author_contact: Namespace author's contact info/email address
    :param author_copyright: Namespace's copyright/license information
    :param citation_description: Citation description
    :param citation_url: URL to more citation information
    :param citation_version: Citation version
    :param citation_date: Citation publish timestamp, ISO 8601 Date
    :param case_sensitive: Should this config file be interpreted as case-sensitive?
    :param delimiter: The delimiter between names and labels in this config file
    :param cacheable: Should this config file be cached?
    :param file: A writable file or file-like
    """
    header_lines = iter_namespace_nominal(
        namespace_name,
        namespace_keyword,
        namespace_domain=namespace_domain,
        query_url=namespace_query_url,
        description=namespace_description,
        species=namespace_species,
        version=namespace_version,
        created=namespace_created,
    )
    author_lines = iter_author_header(
        author_name,
        contact=author_contact,
        copyright_str=author_copyright,
    )
    citation_lines = iter_citation_header(
        citation_name,
        description=citation_description,
        url=citation_url,
        version=citation_version,
        date=citation_date,
    )
    property_lines = iter_properties_header(
        case_sensitive=case_sensitive,
        delimiter=delimiter,
        cacheable=cacheable,
    )
    body_lines = iter_body(
        values,
        delimiter=delimiter,
    )
    for line in chain(header_lines, author_lines, citation_lines, property_lines, body_lines):
        print(line, file=file)


def iter_namespace_nominal(name: str,
                           keyword: str,
                           namespace_domain: Optional[str] = None,
                           query_url: Optional[str] = None,
                           description: Optional[str] = None,
                           species: Optional[str] = None,
                           version: Optional[str] = None,
                           created: Optional[str] = None,
                           ) -> Iterable[str]:
    """Iterate over the lines of the ``[Namespace]`` section of a BELNS file.

    :param name: The namespace name
    :param keyword: Preferred BEL Keyword, maximum length of 8
    :param namespace_domain: One of: :data:`pybel.constants.NAMESPACE_DOMAIN_BIOPROCESS`,
     :data:`pybel.constants.NAMESPACE_DOMAIN_CHEMICAL`, :data:`pybel.constants.NAMESPACE_DOMAIN_GENE`, or
     :data:`pybel.constants.NAMESPACE_DOMAIN_OTHER`
    :param query_url: HTTP URL to query for details on namespace values (must be valid URL)
    :param description: Namespace description
    :param species: Comma-separated list of species taxonomy id's
    :param version: Namespace version. Defaults to current date in ``YYYYMMDD`` format.
    :param created: Namespace public timestamp, ISO 8601 datetime. Defaults to current time.
    """
    if namespace_domain is None:
        namespace_domain = NAMESPACE_DOMAIN_OTHER
    elif namespace_domain not in NAMESPACE_DOMAIN_TYPES:
        raise ValueError('Invalid domain: {}. Should be one of: {}'.format(namespace_domain, NAMESPACE_DOMAIN_TYPES))

    yield '[Namespace]'
    yield 'Keyword={}'.format(keyword)
    yield 'NameString={}'.format(name)
    yield 'DomainString={}'.format(namespace_domain)
    yield 'VersionString={}'.format(version if version else get_iso_8601_date())
    yield 'CreatedDateTime={}'.format(created if created else time.strftime(DATETIME_FMT))

    if description:
        yield 'DescriptionString={}'.format(description.strip().replace('\n', ''))

    if species is not None:
        yield 'SpeciesString={}'.format(species)

    if query_url is not None:
        yield 'QueryValueURL={}'.format(query_url)
