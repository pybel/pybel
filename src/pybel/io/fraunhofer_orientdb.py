# -*- coding: utf-8 -*-

"""Transport functions for `Fraunhofer's OrientDB <http://graphstore.scai.fraunhofer.de>`_.

`Fraunhofer <https://www.scai.fraunhofer.de/en/business-research-areas/bioinformatics.html>`_ hosts
an instance of `OrientDB <https://orientdb.com/>`_ that contains BEL in a schema similar to
:mod:`pybel.io.umbrella_nodelink`. However, they include custom relations that do not come
from a controlled vocabulary, and have not made the schema, ETL scripts, or documentation available.

Unlike BioDati and BEL Commons, the Fraunhofer OrientDB does not allow for uploads, so only
a single function :func:`pybel.from_fraunhofer_orientdb` is provided by PyBEL.
"""

import logging
from typing import Any, Iterable, Mapping, Optional
from urllib.parse import quote_plus

import requests
from pyparsing import ParseException

from .. import constants as pc
from ..parser import BELParser
from ..struct import BELGraph

__all__ = [
    'from_fraunhofer_orientdb',
]

logger = logging.getLogger(__name__)


def from_fraunhofer_orientdb(  # noqa:S107
    database: str = 'covid',
    user: str = 'covid_user',
    password: str = 'covid',
    query: Optional[str] = None
) -> BELGraph:
    """Get a BEL graph from the Fraunhofer OrientDB.

    :param database: The OrientDB database to connect to
    :param user: The user to connect to OrientDB
    :param password: The password to connect to OrientDB
    :param query: The query to run. Defaults to the URL encoded version of ``select from E``,
     where ``E`` is all edges in the OrientDB edge database. Likely does not need to be changed,
     except in the case of selecting specific subsets of edges. Make sure you URL encode it
     properly, because OrientDB's RESTful API puts it in the URL's path.

    By default, this function connects to the ``covid`` database, that corresponds to the
    COVID-19 Knowledge Graph [0]_. If other databases in the Fraunhofer OrientDB are
    published and demo username/password combinations are given, the following table will
    be updated.

    +----------+------------+----------+
    | Database | Username   | Password |
    +==========+============+==========+
    | covid    | covid_user | covid    |
    +----------+------------+----------+

    The ``covid`` database can be downloaded and converted to a BEL graph like this:

    .. code-block:: python

        import pybel
        graph = pybel.from_fraunhofer_orientdb(
            database='covid',
            user='covid_user',
            password='covid',
        )
        graph.summarize()

    However, because the source BEL scripts for the COVID-19 Knowledge Graph are available on
    `GitHub <https://github.com/covid19kg/covid19kg>`_ and the authors pre-enabled it for PyBEL, it can
    be downloaded with ``pip install git+https://github.com/covid19kg/covid19kg.git`` and used
    with the following python code:

    .. code-block:: python

       import covid19kg
       graph = covid19kg.get_graph()
       graph.summarize()

    .. warning::

        It was initially planned to handle some of the non-standard relationships listed in the
        Fraunhofer OrientDB's `schema <http://graphstore.scai.fraunhofer.de/studio/index.html#/database/covid/schema>`_
        in their OrientDB Studio instance, but none of them actually appear in the only network that is accessible.
        If this changes, please leave an issue at https://github.com/pybel/pybel/issues so it can be addressed.

    .. [0] Domingo-Fernández, D., *et al.* (2020). `COVID-19 Knowledge Graph: a computable, multi-modal,
           cause-and-effect knowledge model of COVID-19 pathophysiology
           <https://doi.org/10.1101/2020.04.14.040667>`_. *bioRxiv* 2020.04.14.040667.
    """
    graph = BELGraph(name='Fraunhofer OrientDB: {}'.format(database))
    parser = BELParser(graph, skip_validation=True)
    results = _request_graphstore(database, user, password, select_query_template=query)
    for result in results:
        _parse_result(parser, result)
    return graph


def _parse_result(parser: BELParser, result: Mapping[str, Any]) -> None:
    citation_db, citation_id = pc.CITATION_TYPE_PUBMED, result.get('pmid')
    if citation_id is None:
        citation_db, citation_id = pc.CITATION_TYPE_PMC, result.get('pmc')
    if citation_id is None:
        if 'citation' in result:
            logger.warning('incorrect citation information for %s: %s', result['@rid'], result['citation'])
        else:
            logger.debug('no citation information for %s', result['@rid'])
        return

    parser.control_parser.clear()
    parser.control_parser.citation_db = citation_db
    parser.control_parser.citation_db_id = citation_id
    parser.control_parser.evidence = result['evidence']
    parser.control_parser.annotations.update(result['annotation'])

    source = result['in']['bel']
    relation = result['@class']
    relation = RELATION_MAP.get(relation, relation)
    target = result['out']['bel']
    statement = ' '.join([source, relation, target])

    try:
        parser.parseString(statement)
    except ParseException:
        logger.warning('could not parse %s', statement)


RELATION_MAP = {
    'causes_no_change': pc.CAUSES_NO_CHANGE,
    'positive_correlation': pc.POSITIVE_CORRELATION,
    'negative_correlation': pc.NEGATIVE_CORRELATION,
    'is_a': pc.IS_A,
    'has_member': 'hasMember',
    'has_members': 'hasMembers',
    'has_component': 'hasComponent',
    'has_components': 'hasComponents',
}


def _request_graphstore(
    database: str,
    user: str,
    password: str,
    count_query: Optional[str] = None,
    select_query_template: Optional[str] = None,
    page_size: int = 500,
    base: str = 'http://graphstore.scai.fraunhofer.de/query'
) -> Iterable[Mapping[str, Any]]:
    """Make an API call to the OrientDB."""
    if count_query is None:
        count_query = 'select count(@rid) from E'
    count_query = quote_plus(count_query)
    count_url = '{base}/{database}/sql/{count_query}'.format(base=base, database=database, count_query=count_query)
    count_res = requests.get(count_url, auth=(user, password))
    count = count_res.json()['result'][0]['count']
    logging.debug('fraunhofer orientdb has %d edges', count)

    if select_query_template is None:
        select_query_template = 'select from E order by @rid limit {limit} offset {offset}'

    offsets = count // page_size
    for offset in range(offsets + 1):
        select_query = select_query_template.format(limit=page_size, offset=offset * page_size)
        logger.debug('query: %s', select_query)
        select_query = quote_plus(select_query)
        select_url = '{base}/{database}/sql/{select_query}/{page_size}/*:1'.format(
            base=base, database=database, select_query=select_query, page_size=page_size,
        )
        res = requests.get(select_url, auth=(user, password))
        res_json = res.json()
        result = res_json['result']
        yield from result
