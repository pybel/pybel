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
from ..struct.filters.edge_predicates import edge_has_pubmed_citation
from ..summary.provenance import get_pubmed_identifiers

__all__ = (
    'get_citations_by_pmids',
)

log = logging.getLogger(__name__)

EUTILS_URL_FMT = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={}"

re1 = re.compile('^[12][0-9]{3} [a-zA-Z]{3} \d{1,2}$')
re2 = re.compile('^[12][0-9]{3} [a-zA-Z]{3}$')
re3 = re.compile('^[12][0-9]{3}$')
re4 = re.compile('^[12][0-9]{3} [a-zA-Z]{3}-[a-zA-Z]{3}$')


# TODO re5 = re.compile('^[12][0-9]{3} Fall|Spring|Winter|Summer$')

def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def get_citations_by_pmids(pmids, group_size=None, sleep_time=None, return_errors=False, manager=None):
    """Gets the citation information for the given list of PubMed identifiers using the NCBI's eutils service

    :param iter[str] or iter[int] pmids: an iterable of PubMed identifiers
    :param int group_size: The number of PubMed identifiers to query at a time. Defaults to 200 identifiers.
    :param int sleep_time: Number of seconds to sleep between queries. Defaults to 1 second.
    :param bool return_errors: Should a set of erroneous PubMed identifiers be returned?
    :param manager: An RFC-1738 database connection string, a pre-built :class:`pybel.manager.Manager`,
                    or ``None`` for default connection
    :type manager: None or str or Manager
    :return: A dictionary of {pmid: pmid data dictionary} or a pair of this dictionary and a set ot erroneous
            pmids if return_errors is :data:`True`
    :rtype: dict[str,dict]
    """
    group_size = group_size if group_size is not None else 200
    sleep_time = sleep_time if sleep_time is not None else 1

    pmids = sorted({str(pmid).strip() for pmid in pmids})
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
        return (result, set()) if return_errors else result

    total_unresolved_count = len(unresolved_pmids)
    log.info('Querying PubMed for %d identifiers', total_unresolved_count)

    errors = set()
    t = time.time()

    for pmid_group_index, pmid_list in enumerate(grouper(group_size, unresolved_pmids), start=1):
        pmid_list = list(pmid_list)
        log.info('Getting group %d having %d PubMed identifiers', pmid_group_index, len(pmid_list))
        url = EUTILS_URL_FMT.format(','.join(pmid for pmid in pmid_list if pmid))
        response_raw = requests.get(url)
        response = response_raw.json()

        for pmid in response['result']['uids']:
            p = response['result'][pmid]

            if 'error' in p:
                log.warning("Error downloading PubMed identifier: %s", pmid)
                errors.add(pmid)
                continue

            result[pmid] = {
                'title': p['title'],
                'last': p['lastauthor'],
                CITATION_NAME: p['fulljournalname'],
                'volume': p['volume'],
                'issue': p['issue'],
                'pages': p['pages'],
                'first': p['sortfirstauthor'],
            }

            citation = unresolved_pmids[pmid]

            citation.name = result[pmid][CITATION_NAME]
            citation.title = result[pmid]['title']
            citation.volume = result[pmid]['volume']
            citation.issue = result[pmid]['issue']
            citation.pages = result[pmid]['pages']
            citation.first = manager.get_or_create_author(result[pmid]['first'])
            citation.last = manager.get_or_create_author(result[pmid]['last'])

            if 'authors' in p:
                result[pmid][CITATION_AUTHORS] = [author['name'] for author in p['authors']]
                for author in result[pmid][CITATION_AUTHORS]:
                    author_model = manager.get_or_create_author(author)
                    if author_model not in citation.authors:
                        citation.authors.append(author_model)

            publication_date = p['pubdate']

            if re1.search(publication_date):
                result[pmid][CITATION_DATE] = datetime.strptime(p['pubdate'], '%Y %b %d').strftime('%Y-%m-%d')
            elif re2.search(publication_date):
                result[pmid][CITATION_DATE] = datetime.strptime(p['pubdate'], '%Y %b').strftime('%Y-%m-01')
            elif re3.search(publication_date):
                result[pmid][CITATION_DATE] = p['pubdate'] + "-01-01"
            elif re4.search(publication_date):
                result[pmid][CITATION_DATE] = datetime.strptime(p['pubdate'][:-4], '%Y %b').strftime('%Y-%m-01')
            else:
                log.info('Date with strange format: %s', p['pubdate'])

            if CITATION_DATE in result[pmid]:
                citation.date = datetime.strptime(result[pmid][CITATION_DATE], '%Y-%m-%d')

            manager.session.add(citation)

        manager.session.commit()  # commit in groups

        # Don't want to hit that rate limit
        time.sleep(sleep_time)

    log.info('retrieved %d PubMed identifiers in %.02f seconds', len(unresolved_pmids), time.time() - t)

    return (result, errors) if return_errors else result


def enrich_pubmed_citations(graph, manager=None, group_size=None, sleep_time=None):
    """Overwrites all PubMed citations with values from NCBI's eUtils lookup service.

    Sets authors as list, so probably a good idea to run :func:`pybel_tools.mutation.serialize_authors` before
    exporting.

    :param pybel.BELGraph graph: A BEL graph
    :param bool stringify_authors: Converts all author lists to author strings using
                                  :func:`pybel_tools.mutation.serialize_authors`. Defaults to ``False``.
    :param manager: An RFC-1738 database connection string, a pre-built :class:`pybel.manager.Manager`,
                    or ``None`` for default connection
    :type manager: None or str or Manager
    :param int group_size: The number of PubMed identifiers to query at a time. Defaults to 200 identifiers.
    :param int sleep_time: Number of seconds to sleep between queries. Defaults to 1 second.
    :return: A set of PMIDs for which the eUtils service crashed
    :rtype: set[str]
    """
    if 'PYBEL_ENRICHED_CITATIONS' in graph.graph:
        log.warning('citations have already been enriched in %s', graph)
        return set()

    pmids = get_pubmed_identifiers(graph)
    pmid_data, errors = get_citations_by_pmids(pmids, group_size=group_size, sleep_time=sleep_time, return_errors=True,
                                               manager=manager)

    for u, v, k, d in filter_edges(graph, edge_has_pubmed_citation):
        pmid = d[CITATION][CITATION_REFERENCE].strip()

        if pmid not in pmid_data:
            log.warning('Missing data for PubMed identifier: %s', pmid)
            errors.add(pmid)
            continue

        graph.edge[u][v][k][CITATION].update(pmid_data[pmid])

    graph.graph['PYBEL_ENRICHED_CITATIONS'] = True

    return errors
