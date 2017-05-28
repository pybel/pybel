# -*- coding: utf-8 -*-

"""This module contains IO functions for import of BEL graphs stored in JSON Graph Interchange Format"""

import logging

from ..constants import CITATION_NAME, CITATION_TYPE, CITATION_REFERENCE, unqualified_edges
from ..graph import BELGraph
from ..parser import BelParser

__all__ = [
    'from_cbn_jgif',
    'from_jgif'
]

log = logging.getLogger(__name__)

annotation_map = {
    'tissue': 'Tissue',
    'disease': 'Disease',
    'species_common_name': 'Species',
    'cell': 'Cell',
}

species_map = {
    'human': '9606',
    'rat': '10116',
    'mouse': '10090',
}

placeholder_evidence = "This Network edge has no supporting evidence.  Please add real evidence to this edge prior to deleting."

EXPERIMENT_CONTEXT = 'experiment_context'


def get_citation(evidence):
    citation= {
        CITATION_TYPE: evidence['citation']['type'].strip(),
        CITATION_REFERENCE: evidence['citation']['id'].strip()
    }

    if 'name' in evidence['citation']:
        citation[CITATION_NAME] = evidence['citation']['name'].strip()

    return citation


def map_cbn(d):
    """Pre-processes the JSON from the CBN
    
    - removes statements without evidence, or with placeholder evidence
    
    :param dict d: Raw JGIF from the CBN
    :return: Preprocessed JGIF
    :rtype: dict
    """
    for i, edge in enumerate(d['graph']['edges']):
        if 'metadata' not in d['graph']['edges'][i]:
            continue

        if 'evidences' not in d['graph']['edges'][i]['metadata']:
            continue

        for j, evidence in enumerate(d['graph']['edges'][i]['metadata']['evidences']):
            if EXPERIMENT_CONTEXT not in evidence:
                continue

            # ctx = {k.strip().lower(): v.strip() for k, v in evidence[EXPERIMENT_CONTEXT].items() if v.strip()}

            new_context = {}

            for key, value in evidence[EXPERIMENT_CONTEXT].items():
                value = value.strip()

                if not value:
                    continue

                key = key.strip().lower()

                if key == 'species_common_name':
                    new_context['Species'] = species_map[value.lower()]
                elif key in annotation_map:
                    new_context[annotation_map[key]] = value
                else:
                    new_context[key] = value

            '''
            for k, v in annotation_map.items():
                if k not in ctx:
                    continue

                d['graph']['edges'][i]['metadata']['evidences'][j][EXPERIMENT_CONTEXT][v] = ctx[k]
                del d['graph']['edges'][i]['metadata']['evidences'][j][EXPERIMENT_CONTEXT][k]

            if 'species_common_name' in ctx:
                species_name = ctx['species_common_name'].strip().lower()
                d['graph']['edges'][i]['metadata']['evidences'][j][EXPERIMENT_CONTEXT]['Species'] = species_map[
                    species_name]
                del d['graph']['edges'][i]['metadata']['evidences'][j][EXPERIMENT_CONTEXT][
                    'species_common_name']
            '''

            d['graph']['edges'][i]['metadata']['evidences'][j][EXPERIMENT_CONTEXT] = new_context
    return d


def from_cbn_jgif(graph_jgif_dict):
    """Maps CBN JGIF then builds a BEL graph."""
    return from_jgif(map_cbn(graph_jgif_dict))


# TODO add metadata
def from_jgif(graph_jgif_dict):
    """Builds a BEL graph from a JGIF JSON object.
    
    :param dict graph_jgif_dict: The JSON object representing the graph in JGIF format
    :return: A BEL graph
    :rtype: BELGraph
    """
    root = graph_jgif_dict['graph']

    label = root.get('label')
    metadata = root['metadata']

    graph = BELGraph()
    parser = BelParser(graph)
    parser.bel_term.addParseAction(parser.handle_term)

    for node in root['nodes']:
        if 'label' not in node:
            log.warning('node missing label: %s', node)
        node_label = node['label']
        parser.bel_term.parseString(node_label)

    for i, edge in enumerate(root['edges']):

        if edge['relation'] in {'actsIn'}:
            continue  # don't need legacy BEL format

        if edge['relation'] in unqualified_edges:
            pass

        if not edge['relation'] in unqualified_edges and (
                        'evidences' not in edge['metadata'] or not edge['metadata']['evidences']):
            log.debug('No evidence for edge %s', edge['label'])
            continue

        for evidence in edge['metadata']['evidences']:
            if 'citation' not in evidence or not evidence['citation']:
                continue

            if not 'type' in evidence['citation'] and not 'id' in evidence['citation']:
                continue

            summary_text = evidence['summary_text'].strip()

            if not summary_text or summary_text == placeholder_evidence:
                continue

            parser.control_parser.clear()
            parser.control_parser.citation = get_citation(evidence)
            parser.control_parser.evidence = summary_text
            parser.control_parser.annotations.update(evidence[EXPERIMENT_CONTEXT])

            bel_statement = edge['label']

            try:
                parser.parseString(bel_statement, i)
            except Exception as e:
                log.warning('Error %s for %s', e, bel_statement)

    return graph
