# -*- coding: utf-8 -*-

"""Importer for Hetionet JSON."""

import bz2
import json
import os
from urllib.request import urlretrieve

from tqdm.notebook import tqdm

from .. import dsl
from ..config import CACHE_DIRECTORY
from ..struct import BELGraph

__all__ = [
    'from_hetionet_github',
    'from_hetionet_json',
]

JSON_BZ2_URL = 'https://github.com/hetio/hetionet/raw/master/hetnet/json/hetionet-v1.0.json.bz2'
PATH = os.path.join(CACHE_DIRECTORY, 'hetionet-v1.0.json.bz2')
DSL_MAP = {
    'Anatomy': dsl.Population,
    'Gene': dsl.Protein,
    'Pathway': dsl.BiologicalProcess,
    'Biological Process': dsl.BiologicalProcess,
    'Compound': dsl.Abundance,
    'Side Effect': dsl.Pathology,
    'Disease': dsl.Pathology,
    'Pharmacologic Class': dsl.Abundance,
    'Symptom': dsl.Pathology,
}


def from_hetionet_github() -> BELGraph:
    """Get Hetionet from GitHub."""
    if not os.path.exists(PATH):
        urlretrieve(JSON_BZ2_URL, PATH)  # noqa: S310
    with bz2.open(PATH) as file:
        return from_hetionet_json(file)


def from_hetionet_json(file) -> BELGraph:  # noqa: C901
    """Convert a hetionet JSON file to a BEL graph."""
    j = json.load(file)

    kind_identifier_to_name = {}
    for x in tqdm(j['nodes']):
        kind_identifier_to_name[x['kind'], x['identifier']] = x['name']

    graph = BELGraph(name='Hetionet')

    type_blacklist = {'Molecular Function', 'Cellular Component'}

    it = tqdm(j['edges'])
    for e in it:
        # it.write(str(e))

        source_type, source_identifier = e['source_id']
        if source_type in type_blacklist:
            continue
        source_name = kind_identifier_to_name[source_type, source_identifier]

        target_type, target_identifier = e['target_id']
        if target_type in type_blacklist:
            continue
        target_name = kind_identifier_to_name[target_type, target_identifier]

        source_identifier = str(source_identifier)
        target_identifier = str(target_identifier)

        kind = e['kind']

        def _check(_source_type: str, _kind: str, _target_type: str) -> bool:
            """Check the metaedge."""
            return kind == _kind and source_type == _source_type and target_type == _target_type

        # direction = e['direction']
        data = e['data']
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
            # it.write(f'Missing source for {source_identifier}-{kind}-{target_identifier}\n{e}')

        for k, v in data.items():
            if k in {'actions', 'pubmed_ids', 'urls', 'subtypes'}:
                continue  # handled explicitly later
            if not isinstance(v, (str, int, bool, float)):
                it.write(f'Unhandled: {source_identifier}-{kind}-{target_identifier} {k}: {v}')
                continue
            annotations[k] = {v: True}

        if _check('Anatomy', 'upregulates', 'Gene'):
            graph.add_positive_correlation(
                dsl.Abundance(namespace='uberon', name=source_name, identifier=source_identifier),
                dsl.Rna(namespace='ncbigene', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Anatomy', 'downregulates', 'Gene'):
            graph.add_negative_correlation(
                dsl.Abundance(namespace='uberon', name=source_name, identifier=source_identifier),
                dsl.Rna(namespace='ncbigene', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Anatomy', 'expresses', 'Gene'):
            graph.add_association(  # FIXME add "correlates" relationship
                dsl.Abundance(namespace='uberon', name=source_name, identifier=source_identifier),
                dsl.Rna(namespace='ncbigene', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Compound', 'resembles', 'Compound'):
            graph.add_association(  # FIXME add "similar" relationship
                dsl.Abundance(namespace='drugbank', name=source_name, identifier=source_identifier),
                dsl.Abundance(namespace='drugbank', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Compound', 'binds', 'Gene'):
            actions = data.get('actions', [])
            drug = dsl.Abundance(namespace='drugbank', name=source_name, identifier=source_identifier)
            protein = dsl.Protein(namespace='ncbigene', name=target_name, identifier=target_identifier)
            graph.add_binds(drug, protein, citation='', evidence='', annotations=annotations)

            if len(actions) == 0:
                pass
            elif len(actions) == 1:
                action = actions[0].lower()
                if action in {'agonist', 'potentiator', 'inducer', 'positive modulator', 'partial agonist',
                              'positive allosteric modulator', 'activator', 'stimulator'}:
                    graph.add_activates(drug, protein, citation='', evidence='', annotations=annotations)
                elif action in {'inhibitor', 'antagonist', 'blocker', 'partial antagonist',
                                'inhibitor, competitive', 'negative modulator', 'negative allosteric modulator'}:
                    graph.add_inhibits(drug, protein, citation='', evidence='', annotations=annotations)
                elif action in {'modulator', 'allosteric modulator'}:
                    graph.add_regulates(drug, protein, citation='', evidence='', annotations=annotations)
                elif action in {'substrate', 'binder', 'other/unknown', 'ligand', 'cofactor', 'product of', 'opener',
                                'desensitize the target', 'other', 'unknown', 'antibody', 'binding', 'adduct'}:
                    pass
                else:
                    it.write(f'Unhandled action for {source_identifier}-{kind}-{target_identifier}: {action}')
            else:
                actions = tuple(sorted(actions))
                if actions in {}:
                    graph.add_activates(drug, protein, citation='', evidence='', annotations=annotations)
                if actions in {('inhibitor', 'substrate'), ('inhibitor', 'blocker')}:
                    graph.add_inhibits(drug, protein, citation='', evidence='', annotations=annotations)
                elif actions in {}:
                    graph.add_regulates(drug, protein, citation='', evidence='', annotations=annotations)
                else:
                    it.write(f'Unhandled actions for {source_identifier}-{kind}-{target_identifier}: {actions}')

        elif _check('Compound', 'upregulates', 'Gene'):
            graph.add_activates(
                dsl.Abundance(namespace='drugbank', name=source_name, identifier=source_identifier),
                dsl.Protein(namespace='ncbigene', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Compound', 'downregulates', 'Gene'):
            graph.add_inhibits(
                dsl.Abundance(namespace='drugbank', name=source_name, identifier=source_identifier),
                dsl.Protein(namespace='ncbigene', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Compound', 'treats', 'Disease'):
            graph.add_decreases(
                dsl.Abundance(namespace='drugbank', name=source_name, identifier=source_identifier),
                dsl.Pathology(namespace='doid', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Gene', 'interacts', 'Gene'):
            graph.add_binds(
                dsl.Protein(namespace='ncbigene', name=source_name, identifier=source_identifier),
                dsl.Protein(namespace='ncbigene', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Gene', 'regulates', 'Gene'):
            graph.add_regulates(
                dsl.Protein(namespace='ncbigene', name=source_name, identifier=source_identifier),
                dsl.Protein(namespace='ncbigene', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Gene', 'covaries', 'Gene'):
            graph.add_association(
                dsl.Rna(namespace='ncbigene', name=source_name, identifier=source_identifier),
                dsl.Rna(namespace='ncbigene', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Gene', 'participates', 'Pathway'):
            graph.add_part_of(
                dsl.Protein(namespace='ncbigene', name=source_name, identifier=source_identifier),
                dsl.BiologicalProcess(namespace='reactome', name=target_name, identifier=target_identifier),
            )
        elif _check('Gene', 'participates', 'Biological Process'):
            graph.add_part_of(
                dsl.Protein(namespace='ncbigene', name=source_name, identifier=source_identifier),
                dsl.BiologicalProcess(namespace='go', name=target_name, identifier=target_identifier),
            )
        elif _check('Compound', 'causes', 'Side Effect'):
            graph.add_increases(
                dsl.Abundance(namespace='drugbank', name=source_name, identifier=source_identifier),
                dsl.Pathology(namespace='umls', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Disease', 'localizes', 'Anatomy'):
            graph.add_association(
                dsl.Pathology(namespace='doid', name=source_name, identifier=source_identifier),
                dsl.Abundance(namespace='uberon', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Disease', 'associates', 'Gene'):
            graph.add_association(
                dsl.Pathology(namespace='doid', name=source_name, identifier=source_identifier),
                dsl.Protein(namespace='ncbigene', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Disease', 'upregulates', 'Gene'):
            graph.add_positive_correlation(
                dsl.Pathology(namespace='doid', name=source_name, identifier=source_identifier),
                dsl.Rna(namespace='ncbigene', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Disease', 'downregulates', 'Gene'):
            graph.add_negative_correlation(
                dsl.Pathology(namespace='doid', name=source_name, identifier=source_identifier),
                dsl.Rna(namespace='ncbigene', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Pharmacologic Class', 'includes', 'Compound'):
            graph.add_is_a(
                dsl.Abundance(namespace='drugbank', name=target_name, identifier=target_identifier),
                dsl.Abundance(namespace='drucentralclass', name=source_name, identifier=source_identifier),
                # FIXME namespace
            )
        elif _check('Disease', 'presents', 'Symptom'):
            graph.add_association(
                dsl.Pathology(namespace='doid', name=source_name, identifier=source_identifier),
                dsl.Pathology(namespace='mesh', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Disease', 'resembles', 'Disease'):
            graph.add_association(
                dsl.Pathology(namespace='doid', name=source_name, identifier=source_identifier),
                dsl.Pathology(namespace='doid', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        elif _check('Compound', 'palliates', 'Disease'):
            graph.add_decreases(
                dsl.Abundance(namespace='drugbank', name=source_name, identifier=source_identifier),
                dsl.Pathology(namespace='doid', name=target_name, identifier=target_identifier),
                citation='', evidence='', annotations=annotations,
            )
        else:
            it.write(f'missed: {e}')

    return graph
