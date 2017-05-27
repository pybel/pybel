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
    'species_common_name': 'Species'
}

species_map = {
    'human': '9606',
    'rat': '10116',
    'mouse': '10090'
}


def get_citation(evidence):
    return {
        CITATION_NAME: evidence['citation']['name'].strip(),
        CITATION_TYPE: evidence['citation']['type'].strip(),
        CITATION_REFERENCE: evidence['citation']['id'].strip()
    }


def map_cbn(d):
    """Pre-processes the JSON from the CBN"""
    for i, edge in enumerate(d['graph']['edges']):
        if 'metadata' not in d['graph']['edges'][i]:
            continue

        if 'evidences' not in d['graph']['edges'][i]['metadata']:
            continue

        for j, evidence in enumerate(d['graph']['edges'][i]['metadata']['evidences']):
            if 'biological_context' not in evidence:
                continue

            ctx = evidence['biological_context']

            for k, v in annotation_map.items():
                if k in ctx and ctx[k].strip():
                    d['graph']['edges'][i]['metadata']['evidences'][j]['biological_context'][v] = ctx[k]
                    del d['graph']['edges'][i]['metadata']['evidences'][j]['biological_context'][k]

            if 'species_common_name' in ctx and ctx['species_common_name'].strip():
                d['graph']['edges'][i]['metadata']['evidences'][j]['biological_context']['Species'] = species_map[
                    ctx['species_common_name']]
                del d['graph']['edges'][i]['metadata']['evidences'][j]['biological_context'][
                    'species_common_name']
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

            parser.control_parser.clear()
            parser.control_parser.citation = get_citation(evidence)
            parser.control_parser.evidence = evidence['summary_text'].strip()
            parser.control_parser.annotations.update(evidence['biological_context'])

            edge_label = edge['label']

            try:
                parser.parseString(edge_label, i)
            except Exception as e:
                log.warning('Error %s for %s', e, edge_label)

    return graph
