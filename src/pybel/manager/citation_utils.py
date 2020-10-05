# -*- coding: utf-8 -*-

"""Citation utilities for the database manager."""

import logging
import re
import time
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

import ratelimit
import requests
from more_itertools import chunked
from sqlalchemy import and_
from tqdm import tqdm

from . import models
from ..constants import CITATION
from ..struct.filters import filter_edges
from ..struct.filters.edge_predicates import has_pubmed
from ..struct.summary.provenance import get_pubmed_identifiers

__all__ = [
    'get_citations_by_pmids',
    'enrich_pubmed_citations',
]

logger = logging.getLogger(__name__)

EUTILS_URL_FMT = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={}"

re1 = re.compile(r'^[12][0-9]{3} [a-zA-Z]{3} \d{1,2}$')
re2 = re.compile(r'^[12][0-9]{3} [a-zA-Z]{3}$')
re3 = re.compile(r'^[12][0-9]{3}$')
re4 = re.compile(r'^[12][0-9]{3} [a-zA-Z]{3}-[a-zA-Z]{3}$')
re5 = re.compile(r'^([12][0-9]{3}) (Spring|Fall|Winter|Summer)$')
re6 = re.compile(r'^[12][0-9]{3} [a-zA-Z]{3} \d{1,2}-(\d{1,2})$')
re7 = re.compile(r'^[12][0-9]{3} [a-zA-Z]{3} \d{1,2}-([a-zA-Z]{3} \d{1,2})$')

# TODO "Winter 2016" probably with re.compile(r'^(Spring|Fall|Winter|Summer) ([12][0-9]{3})$')
# TODO "YYYY Oct - Dec" update re4 to allow spaces before and after the dash

season_map = {'Spring': '03', 'Summer': '06', 'Fall': '09', 'Winter': '12'}


def sanitize_date(publication_date: str) -> str:
    """Sanitize lots of different date strings into ISO-8601."""
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


def clean_pubmed_identifiers(pmids: Iterable[str]) -> List[str]:
    """Clean a list of PubMed identifiers with string strips, deduplicates, and sorting."""
    return sorted({str(pmid).strip() for pmid in pmids})


@ratelimit.limits(calls=3, period=1)
def get_pubmed_citation_response(pubmed_identifiers: Iterable[str]):
    """Get the response from PubMed E-Utils for a given list of PubMed identifiers.

    Rate limit of 3 requests per second is from:
    https://ncbiinsights.ncbi.nlm.nih.gov/2018/08/14/release-plan-for-e-utility-api-keys/

    :param pubmed_identifiers:
    :rtype: dict
    """
    pubmed_identifiers = list(pubmed_identifiers)
    url = EUTILS_URL_FMT.format(
        ','.join(
            pubmed_identifier
            for pubmed_identifier in pubmed_identifiers
            if pubmed_identifier
        ),
    )
    response = requests.get(url)
    return response.json()


def enrich_citation_model(manager, citation, p) -> bool:
    """Enrich a citation model with the information from PubMed.

    :param pybel.manager.Manager manager:
    :param Citation citation: A citation model
    :param dict p: The dictionary from PubMed E-Utils corresponding to d["result"][pmid]
    """
    if 'error' in p:
        logger.warning('Error downloading PubMed')
        return False

    citation.title = p['title']
    citation.journal = p['fulljournalname']
    citation.volume = p['volume']
    citation.issue = p['issue']
    citation.pages = p['pages']
    citation.first = manager.get_or_create_author(p['sortfirstauthor'])
    citation.last = manager.get_or_create_author(p['lastauthor'])
    pubtypes = p['pubtype']
    if pubtypes:
        citation.article_type = pubtypes[0]

    if 'authors' in p:
        for author in p['authors']:
            author_model = manager.get_or_create_author(author['name'])
            if author_model not in citation.authors:
                citation.authors.append(author_model)

    publication_date = p['pubdate']
    try:
        sanitized_publication_date = sanitize_date(publication_date)
    except ValueError:
        logger.warning('could not parse publication date %s for pubmed:%s', publication_date, citation.db_id)
        sanitized_publication_date = None

    if sanitized_publication_date:
        citation.date = datetime.strptime(sanitized_publication_date, '%Y-%m-%d')
    else:
        logger.info('result had date with strange format: %s', publication_date)

    return True


def get_citations_by_pmids(
    manager,
    pmids: Iterable[Union[str, int]],
    *,
    group_size: Optional[int] = None,
    offline: bool = False,
) -> Tuple[Dict[str, Dict], Set[str]]:
    """Get citation information for the given list of PubMed identifiers using the NCBI's eUtils service.

    :type manager: pybel.Manager
    :param pmids: an iterable of PubMed identifiers
    :param group_size: The number of PubMed identifiers to query at a time. Defaults to 200 identifiers.
    :return: A dictionary of {pmid: pmid data dictionary} or a pair of this dictionary and a set ot erroneous
            pmids if return_errors is :data:`True`
    """
    group_size = group_size if group_size is not None else 200

    pmids = clean_pubmed_identifiers(pmids)
    logger.info('ensuring %d PubMed identifiers', len(pmids))

    enriched_pmids = {}
    unenriched_pmids = {}

    citation_models = []
    for pmid_chunk in chunked(pmids, 200):
        citation_filter = and_(
            models.Citation.db == 'pubmed',
            models.Citation.db_id.in_(pmid_chunk),
        )
        citation_model_chunk = manager.session.query(models.Citation).filter(citation_filter).all()
        citation_models.extend(citation_model_chunk)

    pmid_to_model = {
        citation_model.db_id: citation_model
        for citation_model in citation_models
    }
    logger.info('%d of %d are already cached', len(pmid_to_model), len(pmids))
    for pmid in tqdm(pmids, desc='creating database models'):
        citation = pmid_to_model.get(pmid)
        if citation is None:
            citation = pmid_to_model[pmid] = manager.get_or_create_citation(identifier=pmid)
        if citation.is_enriched:
            enriched_pmids[pmid] = citation.to_json()
        else:
            unenriched_pmids[pmid] = citation

    logger.info('%d of %d are already enriched', len(enriched_pmids), len(pmids))
    manager.session.commit()

    errors = set()
    if not unenriched_pmids or offline:
        return enriched_pmids, errors

    it = tqdm(unenriched_pmids, desc=f'getting PubMed data in chunks of {group_size}')
    for pmid_list in chunked(it, n=group_size):
        response = get_pubmed_citation_response(pmid_list)
        response_pmids = response['result']['uids']

        for pmid in response_pmids:
            p = response['result'][pmid]
            citation = unenriched_pmids.get(pmid)
            if citation is None:
                it.write(f'problem looking up pubmed:{pmid}')
                continue

            successful_enrichment = enrich_citation_model(manager, citation, p)

            if not successful_enrichment:
                it.write(f"Error downloading PubMed identifier: {pmid}")
                errors.add(pmid)
                continue

            enriched_pmids[pmid] = citation.to_json()
            manager.session.add(citation)

        manager.session.commit()  # commit in groups

    return enriched_pmids, errors


def enrich_pubmed_citations(
    manager,
    graph,
    group_size: Optional[int] = None,
    offline: bool = False,
) -> Set[str]:
    """Overwrite all PubMed citations with values from NCBI's eUtils lookup service.

    Sets authors as list, so probably a good idea to run :func:`pybel_tools.mutation.serialize_authors` before
    exporting.

    :type manager: pybel.manager.Manager
    :type graph: pybel.BELGraph
    :param group_size: The number of PubMed identifiers to query at a time. Defaults to 200 identifiers.
    :return: A set of PMIDs for which the eUtils service crashed
    """
    pmids = {x for x in get_pubmed_identifiers(graph) if x}
    pmid_data, errors = get_citations_by_pmids(manager, pmids=pmids, group_size=group_size, offline=offline)

    for u, v, k in filter_edges(graph, has_pubmed):
        pmid = graph[u][v][k][CITATION].identifier

        if pmid not in pmid_data:
            logger.warning('Missing data for PubMed identifier: %s', pmid)
            errors.add(pmid)
            continue

        graph[u][v][k][CITATION].update(pmid_data[pmid])

    return errors
