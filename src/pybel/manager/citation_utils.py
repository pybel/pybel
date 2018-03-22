# -*- coding: utf-8 -*-

import logging
import re
import time
from datetime import datetime

import requests
from six.moves import zip_longest

from .cache_manager import Manager
from ..constants import *
from ..struct.filters import filter_edges
from ..struct.filters.edge_predicates import has_pubmed
from ..struct.summary.provenance import get_pubmed_identifiers

__all__ = (
    'get_citations_by_pmids',
)

log = logging.getLogger(__name__)

EUTILS_URL_FMT = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={}"

re1 = re.compile('^[12][0-9]{3} [a-zA-Z]{3} \d{1,2}$')
re2 = re.compile('^[12][0-9]{3} [a-zA-Z]{3}$')
re3 = re.compile('^[12][0-9]{3}$')
re4 = re.compile('^[12][0-9]{3} [a-zA-Z]{3}-[a-zA-Z]{3}$')
re5 = re.compile('^([12][0-9]{3}) (Spring|Fall|Winter|Summer)$')
re6 = re.compile('^[12][0-9]{3} [a-zA-Z]{3} \d{1,2}-(\d{1,2})$')
re7 = re.compile('^[12][0-9]{3} [a-zA-Z]{3} \d{1,2}-([a-zA-Z]{3} \d{1,2})$')

season_map = {'Spring': '03', 'Summer': '06', 'Fall': '09', 'Winter': '12'}


def sanitize_date(publication_date):
    """Sanitizes lots of different date strings into ISO 8601

    :param str publication_date:
    :rtype: str
    """
    if re1.search(publication_date):
        return datetime.strptime(publication_date, '%Y %b %d').strftime('%Y-%m-%d')

    if re2.search(publication_date):
        return datetime.strptime(publication_date, '%Y %b').strftime('%Y-%m-01')

    if re3.search(publication_date):
        return publication_date + "-01-01"

    if re4.search(publication_date):
        return datetime.strptime(publication_date[:-4], '%Y %b').strftime('%Y-%m-01')

    s = re5.search(publication_date)

    if s:
        year, season = s.groups()
        return '{}-{}-01'.format(year, season_map[season])

    s = re6.search(publication_date)

    if s:
        return datetime.strptime(publication_date, '%Y %b %d-{}'.format(s.groups()[0])).strftime('%Y-%m-%d')

    s = re7.search(publication_date)

    if s:
        return datetime.strptime(publication_date, '%Y %b %d-{}'.format(s.groups()[0])).strftime('%Y-%m-%d')


def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def clean_pubmed_identifiers(pmids):
    """String strips, deduplicates, and sorts a list of PubMed identifiers

    :param iter[str] pmids: An iterable of PubMed identifiers
    :return:
    """
    return sorted({str(pmid).strip() for pmid in pmids})


def get_pubmed_citation_response(pubmed_identifiers):
    """Gets the response from PubMed E-Utils for a given list of PubMed identifiers

    :param list[str] pubmed_identifiers:
    :rtype: dict
    """
    pubmed_identifiers = list(pubmed_identifiers)
    url = EUTILS_URL_FMT.format(','.join(
        pubmed_identifier
        for pubmed_identifier in pubmed_identifiers
        if pubmed_identifier
    ))
    response = requests.get(url)
    return response.json()


def enrich_citation_model(manager, citation, p):
    """

    :param pybel.manager.Manager manager:
    :param Citation citation:
    :param dict p:
    :rtype: bool
    """
    if 'error' in p:
        log.warning('Error downloading PubMed')
        return

    citation.name = p['fulljournalname']
    citation.title = p['title']
    citation.volume = p['volume']
    citation.issue = p['issue']
    citation.pages = p['pages']
    citation.first = manager.get_or_create_author(p['sortfirstauthor'])
    citation.last = manager.get_or_create_author(p['lastauthor'])

    if 'authors' in p:
        for author in p['authors']:
            author_model = manager.get_or_create_author(author['name'])
            if author_model not in citation.authors:
                citation.authors.append(author_model)

    publication_date = p['pubdate']

    sanitized_publication_date = sanitize_date(publication_date)
    if sanitized_publication_date:
        citation.date = datetime.strptime(sanitized_publication_date, '%Y-%m-%d')
    else:
        log.info('result had date with strange format: %s', publication_date)

    return True


def get_citations_by_pmids(manager, pmids, group_size=None, sleep_time=None):
    """Gets the citation information for the given list of PubMed identifiers using the NCBI's eutils service

    :type manager: Manager
    :param pmids: an iterable of PubMed identifiers
    :type pmids: iter[str] or iter[int]
    :param int group_size: The number of PubMed identifiers to query at a time. Defaults to 200 identifiers.
    :param int sleep_time: Number of seconds to sleep between queries. Defaults to 1 second.
    :return: A dictionary of {pmid: pmid data dictionary} or a pair of this dictionary and a set ot erroneous
            pmids if return_errors is :data:`True`
    :rtype: tuple[dict[str,dict],set[str]]
    """
    group_size = group_size if group_size is not None else 200
    sleep_time = sleep_time if sleep_time is not None else 1

    pmids = clean_pubmed_identifiers(pmids)
    log.info('Ensuring %d PubMed identifiers', len(pmids))

    manager = Manager.ensure(manager)

    result = {}
    unresolved_pmids = {}

    for pmid in pmids:
        citation = manager.get_or_create_citation(type=CITATION_TYPE_PUBMED, reference=pmid)

        if not citation.date or not citation.name or not citation.authors:
            unresolved_pmids[pmid] = citation
            continue

        result[pmid] = citation.to_json()

    manager.session.commit()

    log.debug('Found %d PubMed identifiers in database', len(pmids) - len(unresolved_pmids))

    if not unresolved_pmids:
        return result, set()

    total_unresolved_count = len(unresolved_pmids)
    log.info('Querying PubMed for %d identifiers', total_unresolved_count)

    errors = set()
    t = time.time()

    for pmid_group_index, pmid_list in enumerate(grouper(group_size, unresolved_pmids), start=1):
        pmid_list = list(pmid_list)
        log.info('Getting group %d having %d PubMed identifiers', pmid_group_index, len(pmid_list))
        response = get_pubmed_citation_response(pmid_list)

        for pmid in response['result']['uids']:
            p = response['result'][pmid]
            citation = unresolved_pmids[pmid]

            successful_enrichment = enrich_citation_model(manager, citation, p)

            if not successful_enrichment:
                log.warning("Error downloading PubMed identifier: %s", pmid)
                errors.add(pmid)
                continue

            result[pmid] = citation.to_json()
            manager.session.add(citation)

        manager.session.commit()  # commit in groups

        # Don't want to hit that rate limit
        time.sleep(sleep_time)

    log.info('retrieved %d PubMed identifiers in %.02f seconds', len(unresolved_pmids), time.time() - t)

    return result, errors


def enrich_pubmed_citations(manager, graph, group_size=None, sleep_time=None):
    """Overwrites all PubMed citations with values from NCBI's eUtils lookup service.

    Sets authors as list, so probably a good idea to run :func:`pybel_tools.mutation.serialize_authors` before
    exporting.

    :type manager: pybel.manager.Manager
    :type graph: pybel.BELGraph
    :param Optional[int] group_size: The number of PubMed identifiers to query at a time. Defaults to 200 identifiers.
    :param Optional[int] sleep_time: Number of seconds to sleep between queries. Defaults to 1 second.
    :return: A set of PMIDs for which the eUtils service crashed
    :rtype: set[str]
    """
    if 'PYBEL_ENRICHED_CITATIONS' in graph.graph:
        log.warning('citations have already been enriched in %s', graph)
        return set()

    pmids = get_pubmed_identifiers(graph)
    pmid_data, errors = get_citations_by_pmids(manager=manager, pmids=pmids, group_size=group_size,
                                               sleep_time=sleep_time)

    for u, v, k in filter_edges(graph, has_pubmed):
        pmid = graph.edges[u, v, k][CITATION][CITATION_REFERENCE].strip()

        if pmid not in pmid_data:
            log.warning('Missing data for PubMed identifier: %s', pmid)
            errors.add(pmid)
            continue

        graph.edges[u, v, k][CITATION].update(pmid_data[pmid])

    graph.graph['PYBEL_ENRICHED_CITATIONS'] = True

    return errors
