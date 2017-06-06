# -*- coding: utf-8 -*-

"""

JSON Graph Interchange Format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The JSON Graph Interchange Format (JGIF) is `specified <http://jsongraphformat.info/>`_ similarly to the Node-Link
JSON. Interchange with this format provides compatibilty with other software and repositories, such as the 
`Causal Biological Network Database <http://causalbionet.com/>`_.

"""

import logging
from collections import defaultdict

from ..canonicalize import decanonicalize_node, decanonicalize_edge
from ..constants import CITATION_TYPE, CITATION_REFERENCE, CITATION_NAME, unqualified_edges
from ..constants import RELATION, FUNCTION, EVIDENCE, CITATION, ANNOTATIONS, METADATA_NAME
from ..parser import BelParser
from ..struct import BELGraph

__all__ = [
    'from_cbn_jgif',
    'from_jgif',
    'to_jgif',
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
    citation = {
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
    """Maps the JGIF used by the Causal Biological Network Database to standard namespace and annotations, then
    builds a BEL graph using :func:`pybel.from_jgif`.

    :param dict graph_jgif_dict: The JSON object representing the graph in JGIF format
    :return: A BEL graph
    :rtype: BELGraph

    Example:

    >>> import requests
    >>> from pybel import from_cbn_jgif
    >>> apoptosis_url = 'http://causalbionet.com/Networks/GetJSONGraphFile?networkId=810385422'
    >>> graph_jgif_dict = requests.get(apoptosis_url).json()
    >>> graph = from_cbn_jgif(graph_jgif_dict)
    """
    return from_jgif(map_cbn(graph_jgif_dict))


# TODO add metadata
def from_jgif(graph_jgif_dict):
    """Builds a BEL graph from a JGIF JSON object.
    
    :param dict graph_jgif_dict: The JSON object representing the graph in JGIF format
    :return: A BEL graph
    :rtype: BELGraph
    """
    root = graph_jgif_dict['graph']

    metadata = {
        METADATA_NAME: root.get('label')
    }
    metadata.update(root['metadata'])

    graph = BELGraph(**metadata)
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

            if 'type' not in evidence['citation'] and 'id' not in evidence['citation']:
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


def to_jgif(graph):
    """Builds a JGIF dictionary from a BEL graph.
    
    :param BELGraph graph: A BEL graph
    :return: A JGIF dictionary
    :rtype: dict
    
    .. warning:: Untested! This format is not general purpose and is therefore time is not heavily invested
    
    """
    node_to_bel = {}
    u_v_r_bel = {}

    nodes_entry = []
    edges_entry = []

    for i, node in enumerate(graph.nodes_iter()):
        bel = decanonicalize_node(graph, node)
        node_to_bel[node] = bel

        nodes_entry.append({
            'id': bel,
            'label': bel,
            'nodeId': i,
            'bel_function_type': graph.node[node][FUNCTION],
            'metadata': {}
        })

    for u, v in graph.edges_iter():
        relation_evidences = defaultdict(list)

        for k, d in graph.edge[u][v].items():

            if (u, v, d[RELATION]) not in u_v_r_bel:
                u_v_r_bel[u, v, d[RELATION]] = decanonicalize_edge(graph, u, v, k)

            bel = u_v_r_bel[u, v, d[RELATION]]

            evidence_dict = {
                'bel_statement': bel,
                'experiment_context': d[ANNOTATIONS],
            }

            if EVIDENCE in d:
                evidence_dict['summary_text'] = d[EVIDENCE]

            if CITATION in d:
                evidence_dict['citation'] = d[CITATION]

            relation_evidences[d[RELATION]].append(evidence_dict)

        for relation, evidences in relation_evidences.items():
            edges_entry.append({
                'source': node_to_bel[u],
                'target': node_to_bel[v],
                'relation': relation,
                'label': u_v_r_bel[u, v, relation],
                'metadata': {
                    'evidences': evidences
                }
            })

    return {
        'graph': {
            'metadata': graph.document,
            'nodes': nodes_entry,
            'edges': edges_entry
        }
    }
