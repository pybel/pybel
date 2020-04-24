# -*- coding: utf-8 -*-

"""Transport functions for `Franhofer SCAI's OrientDB <http://graphstore.scai.fraunhofer.de>`_.

Fraunhofer SCAI hosts an OrientDB instance that contains BEL in a schema similar to Umbrella
Node-Link. However, they include custom relations that do not come from a controlled vocabulary,
and have not made the schema, ETL scripts, or documentation available.

Unlike BioDati and BEL Commons, the Fraunhofer OrientDB does not allow for uploads, so only
a single function :func:`from_fraunhofer_orientdb` is provided by PyBEL.
"""

import logging
from typing import Any, List, Mapping, Optional

import requests

from pybel.parser import BELParser
from pybel.struct import BELGraph

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
    """Get a BEL graph.

    :param database: The OrientDB database to connect to
    :param user: The user to connect to OrientDB
    :param password: The password to connect to OrientDB
    :param query: The query to run. Defaults to the URL encoded version of ``select from E``,
     where ``E`` is all edges in the OrientDB edge database. Likely does not need to be changed,
     except in the case of selecting specific subsets of edges. Make sure you URL encode it
     properly, because OrientDB's RESTful API puts it in the URL's path.
    """
    graph = BELGraph()
    parser = BELParser(graph, skip_validation=True)

    # FIXME this does not page through results, so it only
    #  gets the first set of 20 or so. Needs updating

    results = _request_graphstore(database, user, password, query=query)
    for result in results:
        _parse_result(parser, result)
    return graph


def _parse_result(parser: BELParser, result: Mapping[str, Any]) -> None:
    parser.control_parser.clear()
    parser.control_parser.citation_db = 'PubMed'
    parser.control_parser.citation_db_id = result['pmid']
    parser.control_parser.evidence = result['evidence']
    parser.control_parser.annotations.update(result['annotation'])

    source = result['in']['bel']
    relation = result['@class']
    target = result['out']['bel']
    statement = ' '.join([source, relation, target])
    parser.parseString(statement)


def _request_graphstore(
    database: str,
    user: str,
    password: str,
    query: Optional[str] = None,
    limit='5',
) -> List[Mapping[str, Any]]:
    if query is None:
        query = 'select%20from%20E'
    url = 'http://graphstore.scai.fraunhofer.de/query/{}/sql/{}/{}/*:1'.format(database, query, limit)
    res = requests.get(url, auth=(user, password))
    res_json = res.json()
    for k, v in res_json.items():
        if k != 'result':
            logger.debug('%s: %s', k, v)
    return res_json['result']


def _main():
    graph = from_fraunhofer_orientdb()
    print('NODES\n')
    for node in graph:
        print(node)

    print('\n\nEDGES\n')
    for u, v, d in graph.edges(data=True):
        print(graph.edge_to_bel(u, v, d))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _main()
