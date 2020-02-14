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

    qualified_mapping = {
        (ANATOMY, Population, 'upregulates', GENE, Rna, graph.add_positive_correlation),
        (ANATOMY, Population, 'downregulates', GENE, Rna, graph.add_negative_correlation),
        (ANATOMY, Population, 'expresses', GENE, Rna, graph.add_association),  # FIXME add "correlates" relationship
        (COMPOUND, Abundance, 'resembles', COMPOUND, Abundance, graph.add_association),
        (COMPOUND, Abundance, 'upregulates', GENE, Protein, graph.add_activates),
        (COMPOUND, Abundance, 'downregulates', GENE, Protein, graph.add_inhibits),
        (COMPOUND, Abundance, 'treats', DISEASE, Pathology, graph.add_decreases),
        (COMPOUND, Abundance, 'palliates', DISEASE, Pathology, graph.add_decreases),
        (COMPOUND, Abundance, 'causes', SIDE_EFFECT, Pathology, graph.add_increases),
        (GENE, Protein, 'interacts', GENE, Protein, graph.add_binds),
        (GENE, Protein, 'regulates', GENE, Protein, graph.add_regulates),
        (GENE, Rna, 'covaries', GENE, Rna, graph.add_association),
        (DISEASE, Pathology, 'localizes', ANATOMY, Population, graph.add_association),
        (DISEASE, Pathology, 'associates', GENE, Protein, graph.add_association),
        (DISEASE, Pathology, 'upregulates', GENE, Rna, graph.add_positive_correlation),
        (DISEASE, Pathology, 'downregulates', GENE, Rna, graph.add_negative_correlation),
        (DISEASE, Pathology, 'presents', SYMPTOM, Pathology, graph.add_association),
        (DISEASE, Pathology, 'resembles', DISEASE, Pathology, graph.add_association),
    }

    unqualified_mapping = {
        (GENE, Protein, 'participates', PATHWAY, BiologicalProcess, graph.add_part_of),
        (GENE, Protein, 'participates', BIOPROCESS, BiologicalProcess, graph.add_part_of),
    }

    edges = hetionet_dict['edges']

    if use_tqdm:
        edges = tqdm(edges)
        it_logger = edges.write
    else:
        it_logger = logger.info

    for edge in edges:
        _add_edge(graph, edge, kind_identifier_to_name, it_logger, qualified_mapping, unqualified_mapping)

    return graph


def _add_edge(
    graph,
    edge,
    kind_identifier_to_name,
    it_logger,
    qualified_mapping,
    unqualified_mapping,
) -> Optional[str]:
    source_type, source_identifier = edge['source_id']
    if source_type not in DSL_MAP:
        return
    source_name = kind_identifier_to_name[source_type, source_identifier]
    source_identifier = str(source_identifier)

    kind = edge['kind']

    target_type, target_identifier = edge['target_id']
    if target_type not in DSL_MAP:
        return
    target_name = kind_identifier_to_name[target_type, target_identifier]
    target_identifier = str(target_identifier)

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
                h_dsl(namespace=DSL_MAP[_h_type], identifier=source_identifier, name=source_name),
                t_dsl(namespace=DSL_MAP[_t_type], identifier=target_identifier, name=target_name),
                citation='', evidence='', annotations=annotations,
            )

    for _h_type, h_dsl, _r, _t_type, t_dsl, f in unqualified_mapping:
        if source_type == _h_type and kind == _r and target_type == _t_type:
            return f(
                h_dsl(namespace=DSL_MAP[_h_type], identifier=source_identifier, name=source_name),
                t_dsl(namespace=DSL_MAP[_t_type], identifier=target_identifier, name=target_name),
            )

    def _check(_source_type: str, _kind: str, _target_type: str) -> bool:
        """Check the metaedge."""
        return kind == _kind and source_type == _source_type and target_type == _target_type

    if _check(COMPOUND, 'binds', GENE):
        drug = Abundance(namespace='drugbank', name=source_name, identifier=source_identifier)
        protein = Protein(namespace='ncbigene', name=target_name, identifier=target_identifier)
        graph.add_binds(drug, protein, citation='', evidence='', annotations=annotations)

        actions = data.get('actions', [])
        if len(actions) == 0:
            return
        if len(actions) == 1:
            action = actions[0].lower()
            if action in {'agonist', 'potentiator', 'inducer', 'positive modulator', 'partial agonist',
                          'positive allosteric modulator', 'activator', 'stimulator'}:
                return graph.add_activates(drug, protein, citation='', evidence='', annotations=annotations)
            elif action in {'inhibitor', 'antagonist', 'blocker', 'partial antagonist',
                            'inhibitor, competitive', 'negative modulator', 'negative allosteric modulator'}:
                return graph.add_inhibits(drug, protein, citation='', evidence='', annotations=annotations)
            elif action in {'modulator', 'allosteric modulator'}:
                return graph.add_regulates(drug, protein, citation='', evidence='', annotations=annotations)
            elif action in {'substrate', 'binder', 'other/unknown', 'ligand', 'cofactor', 'product of', 'opener',
                            'desensitize the target', 'other', 'unknown', 'antibody', 'binding', 'adduct'}:
                return
            else:
                it_logger('Unhandled action for {source_identifier}-{kind}-{target_identifier}: {action}'.format(
                    source_identifier=source_identifier, kind=kind, target_identifier=target_identifier, action=action
                ))
                return
        else:
            actions = tuple(sorted(actions))
            if actions in {
                ('activator', 'substrate'),
                ('agonist', 'binder'),
                ('agonist', 'partial agonist'), ('inducer', 'substrate'),
                ('agonist', 'positive allosteric modulator'),
                ('positive allosteric modulator', 'potentiator'),
            }:
                return graph.add_activates(drug, protein, citation='', evidence='', annotations=annotations)
            if actions in {
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
            }:
                return graph.add_inhibits(drug, protein, citation='', evidence='', annotations=annotations)
            elif actions in {
                ('inducer', 'inhibitor', 'substrate'),
                ('inducer', 'inhibitor'),
                ('agonist', 'antagonist'),
                ('antagonist', 'partial agonist'),
                ('adduct', 'inhibitor'),
                ('agonist', 'antagonist', 'modulator'),
            }:
                return graph.add_regulates(drug, protein, citation='', evidence='', annotations=annotations)
            elif actions in {
                ('binder', 'opener'),
            }:
                pass
            else:
                it_logger('Unhandled actions for {source_identifier}-{kind}-{target_identifier}: {actions}'.format(
                    source_identifier=source_identifier, kind=kind, target_identifier=target_identifier, actions=actions
                ))
                return

    if _check(PHARMACOLOGICAL_CLASS, 'includes', COMPOUND):
        return graph.add_is_a(
            Abundance(namespace='drugbank', name=target_name, identifier=target_identifier),
            Abundance(namespace='drucentralclass', name=source_name, identifier=source_identifier),
            # FIXME namespace
        )

    it_logger('missed: {edge}'.format(edge=edge))
