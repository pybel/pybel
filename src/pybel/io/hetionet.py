# -*- coding: utf-8 -*-

"""Importer for Hetionet JSON."""

import bz2
import json
import logging
import os
from typing import Any, Mapping, Optional
from urllib.request import urlretrieve

from tqdm.notebook import tqdm

from ..config import CACHE_DIRECTORY
from ..dsl import Abundance, BiologicalProcess, Pathology, Population, Protein, Rna
from ..struct import BELGraph

__all__ = [
    'from_hetionet',
    'get_hetionet_dict',
    'from_hetionet_dict',
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


def from_hetionet() -> BELGraph:
    """Get Hetionet from GitHub."""
    hetionet_dict = get_hetionet_dict()
    return from_hetionet_dict(hetionet_dict)


def get_hetionet_dict() -> Mapping[str, Any]:
    """Get the Hetionet dictionary."""
    if not os.path.exists(PATH):
        urlretrieve(JSON_BZ2_URL, PATH)  # noqa: S310
    with bz2.open(PATH) as file:
        return json.load(file)


def from_hetionet_dict(
    hetionet_dict: Mapping[str, Any],
    use_tqdm: bool = False,
) -> BELGraph:
    """Convert a Hetionet dictionary to a BEL graph."""
    g = BELGraph(name='Hetionet', version='1.0')

    kind_identifier_to_name = {
        (x['kind'], x['identifier']): x['name']
        for x in hetionet_dict['nodes']
    }

    qualified_mapping = {
        (ANATOMY, Population, 'upregulates', GENE, Rna, g.add_positive_correlation),
        (ANATOMY, Population, 'downregulates', GENE, Rna, g.add_negative_correlation),
        (ANATOMY, Population, 'expresses', GENE, Rna, g.add_association),  # FIXME add "correlates" relationship
        (COMPOUND, Abundance, 'resembles', COMPOUND, Abundance, g.add_association),
        (COMPOUND, Abundance, 'upregulates', GENE, Protein, g.add_activates),
        (COMPOUND, Abundance, 'downregulates', GENE, Protein, g.add_inhibits),
        (COMPOUND, Abundance, 'treats', DISEASE, Pathology, g.add_decreases),
        (COMPOUND, Abundance, 'palliates', DISEASE, Pathology, g.add_decreases),
        (COMPOUND, Abundance, 'causes', SIDE_EFFECT, Pathology, g.add_increases),
        (GENE, Protein, 'interacts', GENE, Protein, g.add_binds),
        (GENE, Protein, 'regulates', GENE, Protein, g.add_regulates),
        (GENE, Rna, 'covaries', GENE, Rna, g.add_association),
        (DISEASE, Pathology, 'localizes', ANATOMY, Population, g.add_association),
        (DISEASE, Pathology, 'associates', GENE, Protein, g.add_association),
        (DISEASE, Pathology, 'upregulates', GENE, Rna, g.add_positive_correlation),
        (DISEASE, Pathology, 'downregulates', GENE, Rna, g.add_negative_correlation),
        (DISEASE, Pathology, 'presents', SYMPTOM, Pathology, g.add_association),
        (DISEASE, Pathology, 'resembles', DISEASE, Pathology, g.add_association),
    }

    unqualified_mapping = {
        (GENE, Protein, 'participates', PATHWAY, BiologicalProcess, g.add_part_of),
        (GENE, Protein, 'participates', BIOPROCESS, BiologicalProcess, g.add_part_of),
    }

    edges = hetionet_dict['edges']

    if use_tqdm:
        edges = tqdm(edges)
        it_logger = edges.write
    else:
        it_logger = logger.info

    for edge in edges:
        _add_edge(g, edge, kind_identifier_to_name, it_logger, qualified_mapping, unqualified_mapping)

    return g


def _add_edge(
    g,
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
            it_logger(f'Unhandled: {source_identifier}-{kind}-{target_identifier} {k}: {v}')
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
        actions = data.get('actions', [])
        drug = Abundance(namespace='drugbank', name=source_name, identifier=source_identifier)
        protein = Protein(namespace='ncbigene', name=target_name, identifier=target_identifier)
        g.add_binds(drug, protein, citation='', evidence='', annotations=annotations)

        if len(actions) == 0:
            return
        if len(actions) == 1:
            action = actions[0].lower()
            if action in {'agonist', 'potentiator', 'inducer', 'positive modulator', 'partial agonist',
                          'positive allosteric modulator', 'activator', 'stimulator'}:
                return g.add_activates(drug, protein, citation='', evidence='', annotations=annotations)
            elif action in {'inhibitor', 'antagonist', 'blocker', 'partial antagonist',
                            'inhibitor, competitive', 'negative modulator', 'negative allosteric modulator'}:
                return g.add_inhibits(drug, protein, citation='', evidence='', annotations=annotations)
            elif action in {'modulator', 'allosteric modulator'}:
                return g.add_regulates(drug, protein, citation='', evidence='', annotations=annotations)
            elif action in {'substrate', 'binder', 'other/unknown', 'ligand', 'cofactor', 'product of', 'opener',
                            'desensitize the target', 'other', 'unknown', 'antibody', 'binding', 'adduct'}:
                return
            else:
                it_logger(f'Unhandled action for {source_identifier}-{kind}-{target_identifier}: {action}')
                return
        else:
            actions = tuple(sorted(actions))
            if actions in {}:
                return g.add_activates(drug, protein, citation='', evidence='', annotations=annotations)
            if actions in {('inhibitor', 'substrate'), ('inhibitor', 'blocker')}:
                return g.add_inhibits(drug, protein, citation='', evidence='', annotations=annotations)
            elif actions in {}:
                return g.add_regulates(drug, protein, citation='', evidence='', annotations=annotations)
            else:
                it_logger(f'Unhandled actions for {source_identifier}-{kind}-{target_identifier}: {actions}')
                return

    if _check(PHARMACOLOGICAL_CLASS, 'includes', COMPOUND):
        return g.add_is_a(
            Abundance(namespace='drugbank', name=target_name, identifier=target_identifier),
            Abundance(namespace='drucentralclass', name=source_name, identifier=source_identifier),
            # FIXME namespace
        )

    it_logger(f'missed: {edge}')
