# -*- coding: utf-8 -*-

"""This module contains IO functions for import of BEL graphs stored in JSON Graph Interchange Format"""

import logging

from ..constants import CITATION_NAME, CITATION_TYPE, CITATION_REFERENCE, unqualified_edges
from ..graph import BELGraph
from ..parser import BelParser

__all__ = [
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

annotation_value_map = {
    'Species': species_map
}


def get_citation(evidence):
    return {
        CITATION_NAME: evidence['citation']['name'].strip(),
        CITATION_TYPE: evidence['citation']['type'].strip(),
        CITATION_REFERENCE: evidence['citation']['id'].strip()
    }


# TODO add metadata
def from_jgif(graph_jgif_dict):
    """Builds a BEL graph from a JGIF JSON object (tested on data from CausalBioNet)
    
    :param dict graph_jgif_dict: The JSON object representing the graph in JGIF format
    :return: A BEL graph
    :rtype: BELGraph
    """

    label = graph_jgif_dict['graph'].get('label')
    metadata = graph_jgif_dict['graph']['metadata']

    graph = BELGraph()
    parser = BelParser(graph)

    for edge in graph_jgif_dict['graph']['edges']:

        if edge['relation'] in {'actsIn'}:
            continue  # don't need legacy BEL format

        if edge['relation'] in unqualified_edges:
            pass


        if not edge['relation'] in unqualified_edges and ('evidences' not in edge['metadata'] or not edge['metadata']['evidences']):
            log.debug('No evidence for edge %s', edge['label'])
            continue

        for evidence in edge['metadata']['evidences']:
            if 'citation' not in evidence or not evidence['citation']:
                continue

            parser.control_parser.clear()
            parser.control_parser.citation = get_citation(evidence)
            parser.control_parser.evidence = evidence['summary_text'].strip()

            d = {}

            if 'biological_context' in evidence:
                annotations = evidence['biological_context'].strip()

                if 'tissue' in annotations and annotations['tissue'].strip():
                    d['Tissue'] = annotations['tissue']

                if 'disease' in annotations and annotations['disease'].strip():
                    d['Disease'] = annotations['disease'].strip()

                if 'species_common_name' in annotations and annotations['species_common_name'].strip():
                    d['Species'] = species_map[annotations['species_common_name'].strip().lower()]

                if 'cell' in annotations and annotations['cell'].strip():
                    d['Cell'] = annotations['cell'].strip()

            parser.control_parser.annotations.update(d)

            try:
                parser.parseString(edge['label'])
            except Exception as e:
                log.warning('Error %s for %s', e, edge['label'])

    return graph
