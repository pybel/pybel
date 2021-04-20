# -*- coding: utf-8 -*-

"""Citation utilities for the database manager."""

import logging
import re
from datetime import date, datetime
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

import ratelimit
import requests
from more_itertools import chunked
from sqlalchemy import and_
from tqdm.autonotebook import tqdm

from . import models
from ..constants import CITATION
from ..struct.filters import filter_edges
from ..struct.filters.edge_predicates import CITATION_PREDIACATES
from ..struct.summary.provenance import get_citation_identifiers

__all__ = [
    '_get_citations_by_identifiers',
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


def clean_pubmed_identifiers(identifiers: Iterable[str]) -> List[str]:
    """Clean a list of identifiers with string strips, deduplicates, and sorting."""
    _identifiers = (str(identifier).strip() for identifier in identifiers if identifier)
    return sorted({i for i in _identifiers if i})


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
    return _get_citations_by_identifiers(
        manager=manager, identifiers=pmids, group_size=group_size, offline=offline, prefix='pubmed',
    )


def _get_citations_by_identifiers(
    manager,
    identifiers: Iterable[Union[str, int]],
    *,
    group_size: Optional[int] = None,
    offline: bool = False,
    prefix: Optional[str] = None,
) -> Tuple[Dict[str, Dict], Set[str]]:
    """Get citation information for the given list of PubMed identifiers using the NCBI's eUtils service.

    :type manager: pybel.Manager
    :param identifiers: an iterable of PubMed identifiers
    :param group_size: The number of PubMed identifiers to query at a time. Defaults to 200 identifiers.
    :return: A dictionary of {identifier: data dictionary} or a pair of this dictionary and a set ot erroneous
             identifiers.
    """
    if prefix is None:
        prefix = 'pubmed'

    helper = _HELPERS.get(prefix)
    if helper is None:
        raise ValueError(f'can not work on prefix: {prefix}')

    group_size = group_size if group_size is not None else 200

    identifiers = clean_pubmed_identifiers(identifiers)
    logger.info('ensuring %d %s identifiers', len(identifiers), prefix)

    enriched_models = {}
    unenriched_models = {}

    id_to_model = {
        citation_model.db_id: citation_model
        for citation_model in _get_citation_models(identifiers, prefix=prefix, manager=manager)
    }
    logger.info('%d of %d %s identifiers are already cached', len(id_to_model), len(identifiers), prefix)
    for identifier in tqdm(identifiers, desc=f'creating {prefix} models'):
        model = id_to_model.get(identifier)
        if model is None:
            model = id_to_model[identifier] = manager.get_or_create_citation(identifier=identifier, namespace=prefix)
        if model.is_enriched:
            enriched_models[identifier] = model.to_json()
        else:
            unenriched_models[identifier] = model

    logger.info('%d of %d %s are identifiers already enriched', len(enriched_models), len(identifiers), prefix)
    manager.session.commit()

    errors = set()
    if not unenriched_models or offline:
        return enriched_models, errors

    it = tqdm(unenriched_models, desc=f'getting {prefix} data in chunks of {group_size}')
    for identifier_chunk in chunked(it, n=group_size):
        helper(
            identifier_chunk,
            manager=manager,
            enriched_models=enriched_models,
            unenriched_models=unenriched_models,
            errors=errors,
        )

    return enriched_models, errors


def _help_enrich_pmids(identifiers: Iterable[str], *, manager, unenriched_models, enriched_models, errors):
    response = get_pubmed_citation_response(identifiers)
    response_pmids = response['result']['uids']

    for pmid in response_pmids:
        p = response['result'][pmid]
        citation = unenriched_models.get(pmid)
        if citation is None:
            tqdm.write(f'problem looking up pubmed:{pmid}')
            continue

        successful_enrichment = enrich_citation_model(manager, citation, p)

        if not successful_enrichment:
            tqdm.write(f"Error downloading pubmed:{pmid}")
            errors.add(pmid)
            continue

        enriched_models[pmid] = citation.to_json()
        manager.session.add(citation)

    manager.session.commit()  # commit in groups


def _help_enrich_pmc_identifiers(identifiers: Iterable[str], *, manager, unenriched_models, enriched_models, errors):
    for pmcid in identifiers:
        try:
            csl = get_pmc_csl_item(pmcid)
        except Exception:
            tqdm.write(f"Error downloading pmc:{pmcid}")
            errors.add(pmcid)
            continue

        model = unenriched_models[pmcid]
        enrich_citation_model_from_pmc(manager=manager, citation=model, csl=csl)
        manager.session.add(model)
        enriched_models[pmcid] = model.to_json()

    manager.session.commit()  # commit in groups


_HELPERS = {
    'pubmed': _help_enrich_pmids,
    'pmc': _help_enrich_pmc_identifiers,
}


def _get_citation_models(identifiers: Iterable[str], *, prefix: str, manager, chunksize: int = 200):
    for identifiers_chunk in chunked(identifiers, chunksize):
        citation_filter = and_(
            models.Citation.db == prefix,
            models.Citation.db_id.in_(identifiers_chunk),
        )
        yield from manager.session.query(models.Citation).filter(citation_filter).all()


def enrich_pubmed_citations(
    manager,
    graph,
    group_size: Optional[int] = None,
    offline: bool = False,
) -> Set[str]:
    """Overwrite all PubMed citations with values from NCBI's eUtils lookup service.

    :type manager: pybel.manager.Manager
    :type graph: pybel.BELGraph
    :param group_size: The number of PubMed identifiers to query at a time. Defaults to 200 identifiers.
    :param offline: An override for when you don't want to hit the eUtils
    :return: A set of PMIDs for which the eUtils service crashed
    """
    return _enrich_citations(
        manager=manager, graph=graph, group_size=group_size, offline=offline, prefix='pubmed',
    )


def _enrich_citations(
    manager,
    graph,
    group_size: Optional[int] = None,
    offline: bool = False,
    prefix: Optional[str] = None,
) -> Set[str]:
    """Overwrite all citations of the given prefix using the predefined lookup functions.

    :type manager: pybel.manager.Manager
    :type graph: pybel.BELGraph
    :param group_size: The number of identifiers to query at a time. Defaults to 200 identifiers.
    :return: A set of identifiers for which lookup was not possible
    """
    if prefix is None:
        prefix = 'pubmed'

    identifiers = {identifier for identifier in get_citation_identifiers(graph, prefix) if identifier}
    identifier_map, errors = _get_citations_by_identifiers(
        manager,
        identifiers=identifiers,
        group_size=group_size,
        offline=offline,
        prefix=prefix,
    )

    for u, v, k in filter_edges(graph, CITATION_PREDIACATES[prefix]):
        identifier = graph[u][v][k][CITATION].identifier

        identifier_data = identifier_map.get(identifier)
        if identifier_data is None:
            logger.warning('Missing data for %s:%s', prefix, identifier)
            errors.add(identifier)
            continue

        graph[u][v][k][CITATION].update(identifier_data)

    return errors


@lru_cache()
def get_pmc_csl_item(pmcid: str):
    """Get the CSL Item for a PubMed Central record by its PMID, PMCID, or DOI, using the NCBI Citation Exporter API."""
    if not pmcid.startswith("PMC"):
        raise ValueError(f'not a valid pmd id: {pmcid}')

    from manubot.cite.pubmed import get_pmc_csl_item
    csl_item = get_pmc_csl_item(pmcid)
    if "URL" not in csl_item:
        csl_item["URL"] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{csl_item.get('PMCID', pmcid)}/"
    return csl_item


def enrich_citation_model_from_pmc(manager, citation, csl) -> bool:
    """Enrich a citation model with the information from PubMed Central.

    :param pybel.manager.Manager manager:
    :param Citation citation: A citation model
    :param dict csl: The dictionary from PMC
    """
    citation.title = csl.get('title')
    citation.journal = csl.get('container-title')
    citation.volume = csl.get('volume')
    # citation.issue = csl['issue']
    citation.pages = csl.get('page')
    citation.article_type = csl.get('type')

    for author in csl.get('author', []):
        try:
            author_name = f'{author["given"]} {author["family"]}'
        except KeyError:
            print(f'problem with author in pmc:{citation.db_id}', author)
            continue
        author_model = manager.get_or_create_author(author_name)
        if author_model not in citation.authors:
            citation.authors.append(author_model)

    if citation.authors:
        citation.first = citation.authors[0]
        citation.last = citation.authors[-1]

    issued = csl.get('issued')
    if issued is not None:
        date_parts = issued['date-parts'][0]
        if len(date_parts) == 3:
            citation.date = date(year=date_parts[0], month=date_parts[1], day=date_parts[2])
        elif len(date_parts) == 2:
            citation.date = date(year=date_parts[0], month=date_parts[1], day=1)
        elif len(date_parts) == 1:
            citation.date = date(year=date_parts[0], month=1, day=1)
        else:
            logger.warning('not sure about date parts: %s', date_parts)

    return True
