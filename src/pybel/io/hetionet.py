# -*- coding: utf-8 -*-

"""Importer for Hetionet JSON."""

import bz2
import json
import logging
import os
from typing import Any, Mapping, Optional
from urllib.request import urlretrieve

from tqdm import tqdm

from ..config import CACHE_DIRECTORY
from ..dsl import Abundance, BiologicalProcess, Pathology, Population, Protein, Rna
from ..struct import BELGraph

__all__ = [
    'get_hetionet',
    'from_hetionet_json',
    'from_hetionet_gz',
    'from_hetnetio_file',
]

logger = logging.getLogger(__name__)

JSON_BZ2_URL = 'https://github.com/hetio/hetionet/raw/master/hetnet/json/hetionet-v1.0.json.bz2'
PATH = os.path.join(CACHE_DIRECTORY, 'hetionet-v1.0.json.bz2')

TYPE_BLACKLIST = {'Molecular Function', 'Cellular Component'}
ANATOMY = 'Anatomy'
GENE = 'Gene'
PATHWAY = 'Pathway'
BIOPROCESS = 'Biological Process'
COMPOUND = 'Compound'
SIDE_EFFECT = 'Side Effect'
DISEASE = 'Disease'
PHARMACOLOGICAL_CLASS = 'Pharmacologic Class'
SYMPTOM = 'Symptom'
DSL_MAP = {
    ANATOMY: 'uberon',
    GENE: 'ncbigene',
    PATHWAY: 'reactome',
    BIOPROCESS: 'go',
    COMPOUND: 'drugbank',
    SIDE_EFFECT: 'umls',
    DISEASE: 'doid',
    PHARMACOLOGICAL_CLASS: 'drugcentral',
    SYMPTOM: 'mesh',
}


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
        return from_hetnetio_file(file)


def from_hetnetio_file(file) -> BELGraph:
    """Get Hetnetio from a JSON file."""
    logger.info('parsing json from %s', file)
    j = json.load(file)
    logger.info('converting hetionet dict to BEL')
    return from_hetionet_json(j)


qualified_mapping = {
    (ANATOMY, Population, 'upregulates', GENE, Rna, BELGraph.add_positive_correlation),
    (ANATOMY, Population, 'downregulates', GENE, Rna, BELGraph.add_negative_correlation),
    (ANATOMY, Population, 'expresses', GENE, Rna, BELGraph.add_association),  # FIXME add "correlates" relationship
    (COMPOUND, Abundance, 'resembles', COMPOUND, Abundance, BELGraph.add_association),
    (COMPOUND, Abundance, 'upregulates', GENE, Protein, BELGraph.add_activates),
    (COMPOUND, Abundance, 'downregulates', GENE, Protein, BELGraph.add_inhibits),
    (COMPOUND, Abundance, 'treats', DISEASE, Pathology, BELGraph.add_decreases),
    (COMPOUND, Abundance, 'palliates', DISEASE, Pathology, BELGraph.add_decreases),
    (COMPOUND, Abundance, 'causes', SIDE_EFFECT, Pathology, BELGraph.add_increases),
    (GENE, Protein, 'interacts', GENE, Protein, BELGraph.add_binds),
    (GENE, Protein, 'regulates', GENE, Protein, BELGraph.add_regulates),
    (GENE, Rna, 'covaries', GENE, Rna, BELGraph.add_association),
    (DISEASE, Pathology, 'localizes', ANATOMY, Population, BELGraph.add_association),
    (DISEASE, Pathology, 'associates', GENE, Protein, BELGraph.add_association),
    (DISEASE, Pathology, 'upregulates', GENE, Rna, BELGraph.add_positive_correlation),
    (DISEASE, Pathology, 'downregulates', GENE, Rna, BELGraph.add_negative_correlation),
    (DISEASE, Pathology, 'presents', SYMPTOM, Pathology, BELGraph.add_association),
    (DISEASE, Pathology, 'resembles', DISEASE, Pathology, BELGraph.add_association),
}

unqualified_mapping = {
    (GENE, Protein, 'participates', PATHWAY, BiologicalProcess, BELGraph.add_part_of),
    (GENE, Protein, 'participates', BIOPROCESS, BiologicalProcess, BELGraph.add_part_of),
}


def from_hetionet_json(
    hetionet_dict: Mapping[str, Any],
    use_tqdm: bool = True,
) -> BELGraph:
    """Convert a Hetionet dictionary to a BEL graph."""
    graph = BELGraph(name='Hetionet', version='1.0', authors='Daniel Himmelstein')

    kind_identifier_to_name = {
        (x['kind'], x['identifier']): x['name']
        for x in hetionet_dict['nodes']
    }

    edges = hetionet_dict['edges']

    if use_tqdm:
        edges = tqdm(edges)
        it_logger = edges.write
    else:
        it_logger = logger.info

    for edge in edges:
        _add_edge(graph, edge, kind_identifier_to_name, it_logger)

    return graph


ACTIVATES_ACTIONS = {
    'agonist', 'potentiator', 'inducer', 'positive modulator', 'partial agonist',
    'positive allosteric modulator', 'activator', 'stimulator',
}

INHIBITS_ACTIONS = {'inhibitor', 'antagonist', 'blocker', 'partial antagonist',
                    'inhibitor, competitive', 'negative modulator', 'negative allosteric modulator'}

REGULATES_ACTIONS = {'modulator', 'allosteric modulator'}

BINDS_ACTIONS = {'substrate', 'binder', 'other/unknown', 'ligand', 'cofactor', 'product of', 'opener',
                 'desensitize the target', 'other', 'unknown', 'antibody', 'binding', 'adduct'}

# These actions aren't yet obvious how to interpret
TBH_ACTIONS = {}

ACTIVATES_ACTION_PAIRS = {
    ('activator', 'substrate'),
    ('agonist', 'binder'),
    ('agonist', 'partial agonist'), ('inducer', 'substrate'),
    ('agonist', 'positive allosteric modulator'),
    ('positive allosteric modulator', 'potentiator'),
}

INHIBITS_ACTION_PAIR = {
    ('agonist', 'positive modulator'),
    ('allosteric antagonist', 'antagonist'),
    ('antagonist', 'blocker'),
    ('antagonist', 'inhibitor'),
    ('antagonist', 'multitarget'),
    ('antagonist', 'substrate'),
    ('blocker', 'inhibitor'),
    ('blocker', 'modulator'),
    ('inhibitor', 'modulator'),
    ('inhibitor', 'multitarget'),
    ('inhibitor', 'negative modulator'),
    ('inhibitor', 'other'),
    ('inhibitor', 'substrate'),
    ('negative modulator', 'releasing agent'),
}

CONFLICTING_ACTION_PAIR = {
    ('inducer', 'inhibitor', 'substrate'),
    ('inducer', 'inhibitor'),
    ('agonist', 'antagonist'),
    ('antagonist', 'partial agonist'),
    ('adduct', 'inhibitor'),
    ('agonist', 'antagonist', 'modulator'),
}

UNINTERPRETABLE_ACTION_PAIR = {
    ('binder', 'opener'),
}


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
) -> Optional[str]:
    source_type, source_identifier, source_name = _get_node(edge, kind_identifier_to_name, 'source_id')
    target_type, target_identifier, target_name = _get_node(edge, kind_identifier_to_name, 'target_id')
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

    for k, v in data.items():
        if k in {'actions', 'pubmed_ids', 'urls', 'subtypes'}:
            continue  # handled explicitly later
        if not isinstance(v, (str, int, bool, float)):
            it_logger('Unhandled: {source_identifier}-{kind}-{target_identifier} {k}: {v}'.format(
                source_identifier=source_identifier, kind=kind, target_identifier=target_identifier,
                k=k, v=v,
            ))
            continue
        annotations[k] = {v: True}

    for _h_type, h_dsl, _r, _t_type, t_dsl, f in qualified_mapping:
        if source_type == _h_type and kind == _r and target_type == _t_type:
            return f(
                graph,
                h_dsl(namespace=DSL_MAP[_h_type], identifier=source_identifier, name=source_name),
                t_dsl(namespace=DSL_MAP[_t_type], identifier=target_identifier, name=target_name),
                citation='', evidence='', annotations=annotations,
            )

    for _h_type, h_dsl, _r, _t_type, t_dsl, f in unqualified_mapping:
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

        for action in data.get('actions', []):
            action = action.lower()
            if action in ACTIVATES_ACTIONS:
                # FIXME change to add_directly_activates
                graph.add_activates(drug, protein, citation='', evidence='', annotations=annotations)
            elif action in INHIBITS_ACTIONS:
                # FIXME change to add_directly_inhibits
                graph.add_inhibits(drug, protein, citation='', evidence='', annotations=annotations)
            elif action in REGULATES_ACTIONS:
                graph.add_regulates(drug, protein, citation='', evidence='', annotations=annotations)
            elif action in BINDS_ACTIONS:
                graph.add_binds(drug, protein, citation='', evidence='', annotations=annotations)
            else:
                it_logger('Unhandled action for {source_identifier}-{kind}-{target_identifier}: {action}'.format(
                    source_identifier=source_identifier, kind=kind, target_identifier=target_identifier, action=action,
                ))

    if _check(PHARMACOLOGICAL_CLASS, 'includes', COMPOUND):
        return graph.add_is_a(
            Abundance(namespace='drugbank', name=target_name, identifier=target_identifier),
            Abundance(namespace='drugcentral', name=source_name, identifier=source_identifier),
        )

    it_logger('missed: {edge}'.format(edge=edge))
