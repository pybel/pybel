# -*- coding: utf-8 -*-

"""Conversion functions for BEL graphs with GraphDati.

Note that these are not exact I/O - you can't currently use them as a round trip because
the input functions expect the GraphDati format that's output by BioDati.
"""

import gzip
import json
import logging
from collections import defaultdict
from typing import Any, Iterable, List, Mapping, TextIO, Tuple, Union

import pyparsing
from networkx.utils import open_file
from tqdm import tqdm

from .jgif import NAMESPACE_TO_PATTERN
from ..canonicalize import edge_to_tuple
from ..constants import CITATION, CITATION_DB, CITATION_IDENTIFIER, CITATION_TYPE_PUBMED, CITATION_TYPE_URL, EVIDENCE
from ..parser import BELParser
from ..struct import BELGraph

__all__ = [
    'to_graphdati',
    'from_graphdati',
    'to_graphdati_file',
    'from_graphdati_file',
    'to_graphdati_gz',
    'from_graphdati_gz',
    'to_graphdati_jsons',
    'from_graphdati_jsons',
    'to_graphdati_jsonl',
    'to_graphdati_jsonl_gz',
]

logger = logging.getLogger(__name__)

NanopubMapping = Mapping[str, Mapping[str, Any]]

SCHEMA_URI = 'https://github.com/belbio/schemas/blob/master/schemas/nanopub_bel-1.0.0.yaml'
GRAPHDATI_PUBLICATION_TYPES = {
    'PMID': CITATION_TYPE_PUBMED,
    'http': CITATION_TYPE_URL,
    'https': CITATION_TYPE_URL,
}


@open_file(1, mode='w')
def to_graphdati_file(graph: BELGraph, path: Union[str, TextIO], use_identifiers: bool = True, **kwargs) -> None:
    """Write this graph as GraphDati JSON to a file.

    :param graph: A BEL graph
    :param path: A path or file-like
    """
    json.dump(to_graphdati(graph, use_identifiers=use_identifiers), path, ensure_ascii=False, **kwargs)


def from_graphdati_file(path: Union[str, TextIO]) -> BELGraph:
    """Load a file containing GraphDati JSON.

    :param path: A path or file-like
    """
    return from_graphdati(json.load(path))


def to_graphdati_gz(graph: BELGraph, path: str, **kwargs) -> None:
    """Write a graph as GraphDati JSON to a gzip file."""
    with gzip.open(path, 'wt') as file:
        to_graphdati_file(graph, file, **kwargs)


def from_graphdati_gz(path: str) -> BELGraph:
    """Read a graph as GraphDati JSON from a gzip file."""
    with gzip.open(path, 'rt') as file:
        return from_graphdati(json.load(file))


def to_graphdati_jsons(graph: BELGraph, **kwargs) -> str:
    """Dump this graph as a GraphDati JSON object to a string.

    :param graph: A BEL graph
    """
    return json.dumps(to_graphdati(graph), ensure_ascii=False, **kwargs)


def from_graphdati_jsons(s: str) -> BELGraph:
    """Load a graph from a GraphDati JSON string."""
    return from_graphdati(json.loads(s))


@open_file(1, mode='w')
def to_graphdati_jsonl(graph, file, use_identifiers: bool = True, use_tqdm: bool = True):
    """Write this graph as a GraphDati JSON lines file."""
    for nanopub in _iter_graphdati(graph, use_identifiers=use_identifiers, use_tqdm=use_tqdm):
        print(json.dumps(nanopub), file=file)


def to_graphdati_jsonl_gz(graph: BELGraph, path: str, **kwargs) -> None:
    """Write a graph as GraphDati JSONL to a gzip file."""
    with gzip.open(path, 'wt') as file:
        to_graphdati_jsonl(graph, file, **kwargs)


def to_graphdati(graph, use_identifiers: bool = True) -> List[NanopubMapping]:
    """Export a GraphDati list using the nanopub.

    :param graph: A BEL graph
    :param use_identifiers: use OBO-style identifiers
    """
    return list(_iter_graphdati(graph, use_identifiers=use_identifiers))


def _iter_graphdati(graph, *, use_identifiers: bool = True, use_tqdm: bool = False) -> Iterable[NanopubMapping]:
    it = graph.edges(keys=True, data=True)
    if use_tqdm:
        it = tqdm(it, total=graph.number_of_edges(), desc='iterating as nanopubs')
    for u, v, k, d in it:
        yield _make_nanopub(graph, u, v, k, d, use_identifiers)


def _make_nanopub(graph: BELGraph, u, v, k, d, use_identifiers) -> NanopubMapping:
    return dict(
        nanopub=dict(
            schema_uri=SCHEMA_URI,
            type=dict(name='BEL', version='2.1.0'),
            annotations=_get_annotations(d),
            citation=_get_citation(d),
            assertions=_get_assertions(u, v, d, use_identifiers),
            evidence=_get_evidence(d),
            metadata=_get_metadata(graph, d),
            id='pybel_{}'.format(k),
        ),
    )


def _get_assertions(u, v, d, use_identifiers):
    return [
        dict(zip(
            ('subject', 'relation', 'object'),
            edge_to_tuple(u, v, d, use_identifiers=use_identifiers),
        )),
    ]


def _get_evidence(d):
    return d.get(EVIDENCE, 'Not Available')


def _get_citation(d):
    citation = d.get(CITATION)
    rv = {}
    if citation is None:
        rv['reference'] = 'Not Available'
    else:
        rv['database'] = dict(name=citation[CITATION_DB], id=citation[CITATION_IDENTIFIER])
    return rv


def _get_metadata(graph: BELGraph, _):
    return dict(
        gd_creator=graph.authors,
        version=graph.version,
    )  # TODO later


def _get_annotations(d):
    return []  # TODO later


def from_graphdati(j, use_tqdm: bool = True) -> BELGraph:
    """Convert data from the "normal" network format.

    .. warning:: BioDati crashes when requesting the ``full`` network format, so this isn't yet explicitly supported
    """
    root = j['graph']
    graph = BELGraph(
        name=root.get('label'),
        version=root['metadata'].get('gd_rev'),
        authors=root['metadata'].get('gd_creator'),
        description=root.get('gd_description'),
    )
    # Just in case you want to find it again
    graph.graph['biodati_network_id'] = root['metadata']['id']

    parser = BELParser(
        graph=graph,
        namespace_to_pattern=NAMESPACE_TO_PATTERN,  # To be updated manually depending on what William is up to
    )

    it = root['edges']
    if use_tqdm:
        it = tqdm(it, desc='iterating edges')

    for i, edge in enumerate(it):
        relation = edge.get('relation')
        if relation is None:
            logger.warning('no relation for edge: %s', edge)

        if relation in {'actsIn', 'translocates'}:
            continue  # don't need legacy BEL format

        bel_statement = edge.get('label')  # this is actually the BEL statement
        if bel_statement is None:
            logger.debug('No BEL statement for edge %s', edge)
            continue

        # Fill up that sweet, sweet metadata
        metadata_entries = edge['metadata']['nanopub_data']
        for metadata in metadata_entries:
            parser.control_parser.clear()

            citation = metadata['citation_id']  # as CURIE
            citation_db, citation_id = _parse_biodati_citation(citation)
            if citation_db is None:
                continue
            parser.control_parser.citation_db = citation_db
            parser.control_parser.citation_db_id = citation_id

            # FIXME where is the evidence/support/summary text?
            parser.control_parser.evidence = 'No evidence available from BioDai'

            nanopub_id = metadata['nanopub_id']
            parser.control_parser.annotations['biodati_nanopub_id'] = [nanopub_id]

            annotations = metadata['annotations']
            parser.control_parser.annotations.update(_parse_biodati_annotations(annotations))

            # Finally, parse the BEL statement (once to go with each set of metadata)
            # TODO change parser to give back pre-compiled info so this doesn't need to be repeated
            try:
                parser.parseString(bel_statement, line_number=i)
            except pyparsing.ParseException as e:
                logger.warning('parse error for %s: %s', bel_statement, e)

    return graph


def _parse_biodati_citation(citation: str) -> Union[Tuple[None, None], Tuple[str, str]]:
    try:
        citation_db, citation_id = citation.split(':')
    except ValueError:
        logger.warning('structured citation not available for %s', citation)
        return None, None

    try:
        citation_db = GRAPHDATI_PUBLICATION_TYPES[citation_db]
    except KeyError:
        logger.warning('invalid citation structure: %s', citation)
        return None, None

    return citation_db, citation_id


def _parse_biodati_annotations(annotations: List[Mapping[str, str]]) -> Mapping[str, Mapping[str, bool]]:
    rv = defaultdict(set)
    for annotation in annotations:
        annotation_curie = annotation['id']
        annotation_prefix, annotation_id = annotation_curie.split(':', 1)
        rv[annotation_prefix].add(annotation_id)
    return dict(rv)
