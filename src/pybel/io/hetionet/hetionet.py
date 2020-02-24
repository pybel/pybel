# -*- coding: utf-8 -*-

"""Importer for Hetionet JSON."""

import bz2
import json
import logging
import os
from typing import Any, Mapping, Set, Union
from urllib.request import urlretrieve

from tqdm import tqdm

from .constants import (
    ACTIVATES_ACTIONS, BINDS_ACTIONS, COMPOUND, DSL_MAP, GENE, HETIONET_PUBMED, INHIBITS_ACTIONS, PHARMACOLOGICAL_CLASS,
    QUALIFIED_MAPPING, REGULATES_ACTIONS, UNQUALIFIED_MAPPING,
)
from ...config import CACHE_DIRECTORY
from ...dsl import Abundance, Protein
from ...struct import BELGraph

__all__ = [
    'get_hetionet',
    'from_hetionet_json',
    'from_hetionet_gz',
    'from_hetionet_file',
]

logger = logging.getLogger(__name__)

JSON_BZ2_URL = 'https://github.com/hetio/hetionet/raw/master/hetnet/json/hetionet-v1.0.json.bz2'
PATH = os.path.join(CACHE_DIRECTORY, 'hetionet-v1.0.json.bz2')


def get_hetionet() -> BELGraph:
    """Get Hetionet from GitHub, cache, and convert to BEL."""
    if not os.path.exists(PATH):
        logger.warning('downloading hetionet from %s to %s', JSON_BZ2_URL, PATH)
        urlretrieve(JSON_BZ2_URL, PATH)  # noqa: S310
    return from_hetionet_gz(PATH)


def from_hetionet_gz(path: str) -> BELGraph:
    """Get Hetionet from its JSON GZ file."""
    logger.info('opening %s', path)
    with bz2.open(path) as file:
        return from_hetionet_file(file)


def from_hetionet_file(file) -> BELGraph:
    """Get Hetionet from a JSON file."""
    logger.info('parsing json from %s', file)
    j = json.load(file)
    logger.info('converting hetionet dict to BEL')
    return from_hetionet_json(j)


def from_hetionet_json(
    hetionet_dict: Mapping[str, Any],
    use_tqdm: bool = True,
) -> BELGraph:
    """Convert a Hetionet dictionary to a BEL graph."""
    graph = BELGraph(  # FIXME what metadata is appropriate?
        name='Hetionet',
        version='1.0',
        authors='Daniel Himmelstein',
    )
    # FIXME add namespaces
    # graph.namespace_pattern.update({})

    kind_identifier_to_name = {
        (x['kind'], x['identifier']): x['name']
        for x in hetionet_dict['nodes']
    }

    edges = hetionet_dict['edges']

    if use_tqdm:
        edges = tqdm(edges, desc='Converting Hetionet')
        it_logger = edges.write
    else:
        it_logger = logger.info

    for edge in edges:
        _add_edge(graph, edge, kind_identifier_to_name, it_logger)

    return graph


def _get_node(edge, key, kind_identifier_to_name):
    node_type, node_identifier = edge[key]
    if node_type not in DSL_MAP:
        return None, None, None
    node_name = kind_identifier_to_name[node_type, node_identifier]
    node_identifier = str(node_identifier)
    return node_type, node_identifier, node_name


def _add_edge(  # noqa: C901
    graph,
    edge,
    kind_identifier_to_name,
    it_logger,
) -> Union[None, str, Set[str]]:
    source_type, source_identifier, source_name = _get_node(edge, 'source_id', kind_identifier_to_name)
    target_type, target_identifier, target_name = _get_node(edge, 'target_id', kind_identifier_to_name)
    if source_type is None or target_type is None:
        return

    kind = edge['kind']

    # direction = e['direction']
    data = edge['data']
    if 'unbiased' in data:
        del data['unbiased']

    annotations = {}
    if 'source' in data:
        source = data.pop('source')
        annotations['source'] = {source: True}
    elif 'sources' in data:
        annotations['source'] = {
            source: True
            for source in data.pop('sources')
        }
    else:
        pass
        # it_logger(f'Missing source for {source_identifier}-{kind}-{target_identifier}\n{e}')

    if 'pubmed_ids' in data:
        citations = list(data.pop('pubmed_ids'))
    else:
        citations = [HETIONET_PUBMED]

    for k, v in data.items():
        if k in {'actions', 'urls', 'subtypes'}:
            continue  # handled explicitly later
        if not isinstance(v, (str, int, bool, float)):
            it_logger('Unhandled: {source_identifier}-{kind}-{target_identifier} {k}: {v}'.format(
                source_identifier=source_identifier, kind=kind, target_identifier=target_identifier,
                k=k, v=v,
            ))
            continue
        annotations[k] = {v: True}

    for _h_type, h_dsl, _r, _t_type, t_dsl, f in QUALIFIED_MAPPING:
        if source_type != _h_type or kind != _r or target_type != _t_type:
            continue
        rv = set()
        for citation in citations:
            key = f(
                graph,
                h_dsl(namespace=DSL_MAP[_h_type], identifier=source_identifier, name=source_name),
                t_dsl(namespace=DSL_MAP[_t_type], identifier=target_identifier, name=target_name),
                citation=citation, evidence='', annotations=annotations,
            )
            rv.add(key)
        return rv

    for _h_type, h_dsl, _r, _t_type, t_dsl, f in UNQUALIFIED_MAPPING:
        if source_type == _h_type and kind == _r and target_type == _t_type:
            return f(
                graph,
                h_dsl(namespace=DSL_MAP[_h_type], identifier=source_identifier, name=source_name),
                t_dsl(namespace=DSL_MAP[_t_type], identifier=target_identifier, name=target_name),
            )

    def _check(_source_type: str, _kind: str, _target_type: str) -> bool:
        """Check the metaedge."""
        return kind == _kind and source_type == _source_type and target_type == _target_type

    if _check(COMPOUND, 'binds', GENE):
        drug = Abundance(namespace='drugbank', name=source_name, identifier=source_identifier)
        protein = Protein(namespace='ncbigene', name=target_name, identifier=target_identifier)

        rv = set()
        for action in data.get('actions', []):
            action = action.lower()
            if action in ACTIVATES_ACTIONS:
                key = graph.add_directly_activates(
                    drug, protein, citation=HETIONET_PUBMED, evidence='', annotations=annotations,
                )
            elif action in INHIBITS_ACTIONS:
                key = graph.add_directly_inhibits(
                    drug, protein, citation=HETIONET_PUBMED, evidence='', annotations=annotations,
                )
            elif action in REGULATES_ACTIONS:
                key = graph.add_regulates(drug, protein, citation=HETIONET_PUBMED, evidence='', annotations=annotations)
            elif action in BINDS_ACTIONS:
                key = graph.add_binds(drug, protein, citation=HETIONET_PUBMED, evidence='', annotations=annotations)
            else:
                key = graph.add_binds(drug, protein, citation=HETIONET_PUBMED, evidence='', annotations=annotations)
                it_logger('Unhandled action for {source_identifier}-{kind}-{target_identifier}: {action}'.format(
                    source_identifier=source_identifier, kind=kind, target_identifier=target_identifier, action=action,
                ))
            rv.add(key)
        return rv

    if _check(PHARMACOLOGICAL_CLASS, 'includes', COMPOUND):
        return graph.add_is_a(
            Abundance(namespace='drugbank', name=target_name, identifier=target_identifier),
            Abundance(namespace='drugcentral', name=source_name, identifier=source_identifier),
        )

    it_logger('missed: {edge}'.format(edge=edge))
