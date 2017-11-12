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

from ..canonicalize import edge_to_bel, node_data_to_bel
from ..constants import *
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
    graph_jgif_dict = map_cbn(graph_jgif_dict)

    graph_jgif_dict['graph']['metadata'].update({
        METADATA_AUTHORS: 'Causal Biological Networks Database',
        METADATA_LICENSES: """
        Please cite:
        
        - www.causalbionet.com
        - https://bionet.sbvimprover.com 

        as well as any relevant publications.
        
        The sbv IMPROVER project, the website and the Symposia are part of a collaborative project 
        designed to enable scientists to learn about and contribute to the development of a new crowd 
        sourcing method for verification of scientific data and results. The current challenges, website 
        and biological network models were developed and are maintained as part of a collaboration among 
        Selventa, OrangeBus and ADS. The project is led and funded by Philip Morris International. For more
        information on the focus of Philip Morris International’s research, please visit www.pmi.com.
        """.replace('\n', '\t')
    })

    graph = from_jgif(graph_jgif_dict)

    graph.namespace_url.update({
        'HGNC': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/hgnc-human-genes/hgnc-human-genes-20150601.belns',
        'GOBP': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/go-biological-process/go-biological-process-20150601.belns',
        'SFAM': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/selventa-protein-families/selventa-protein-families-20150601.belns',
    })

    graph.annotation_url.update({
        'Cell': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/cell-line/cell-line-20150601.belanno',
        'Disease': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/disease/disease-20150601.belanno',
        'Species': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/species-taxonomy-id/species-taxonomy-id-20170511.belanno',
        'Tissue': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/mesh-anatomy/mesh-anatomy-20150601.belanno',
    })

    return graph


def from_jgif(graph_jgif_dict):
    """Builds a BEL graph from a JGIF JSON object.
    
    :param dict graph_jgif_dict: The JSON object representing the graph in JGIF format
    :return: A BEL graph
    :rtype: BELGraph
    """
    graph = BELGraph()

    root = graph_jgif_dict['graph']

    if 'label' in root:
        graph.name = root['label']

    if 'metadata' in root:
        metadata = root['metadata']

        for key in METADATA_INSERT_KEYS:
            if key in metadata:
                graph.document[key] = metadata[key]

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

        if edge['relation'] in UNQUALIFIED_EDGES:
            pass

        if not edge['relation'] in UNQUALIFIED_EDGES and (
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
    
    .. warning::

        Untested! This format is not general purpose and is therefore time is not heavily invested. If you want to
        use Cytoscape.js, we suggest using :func:`pybel.to_cx` instead.

    Example:

    >>> import pybel, os, json
    >>> graph_url = 'https://arty.scai.fraunhofer.de/artifactory/bel/knowledge/selventa-small-corpus/selventa-small-corpus-20150611.bel'
    >>> graph = pybel.from_url(graph_url)
    >>> graph_jgif_json = pybel.to_jgif(graph)
    >>> with open(os.path.expanduser('~/Desktop/small_corpus.json'), 'w') as f:
    ...     json.dump(graph_jgif_json, f)
    """
    node_bel = {}
    u_v_r_bel = {}

    nodes_entry = []
    edges_entry = []

    for i, (node, node_data) in enumerate(graph.nodes_iter(data=True)):
        bel = node_data_to_bel(node_data)
        node_bel[node] = bel

        nodes_entry.append({
            'id': bel,
            'label': bel,
            'nodeId': i,
            'bel_function_type': node_data[FUNCTION],
            'metadata': {}
        })

    for u, v in graph.edges_iter():
        relation_evidences = defaultdict(list)

        for data in graph.edge[u][v].values():

            if (u, v, data[RELATION]) not in u_v_r_bel:
                u_v_r_bel[u, v, data[RELATION]] = edge_to_bel(graph, u, v, data=data)

            bel = u_v_r_bel[u, v, data[RELATION]]

            evidence_dict = {
                'bel_statement': bel,
            }

            if ANNOTATIONS in data:
                evidence_dict['experiment_context'] = data[ANNOTATIONS]

            if EVIDENCE in data:
                evidence_dict['summary_text'] = data[EVIDENCE]

            if CITATION in data:
                evidence_dict['citation'] = data[CITATION]

            relation_evidences[data[RELATION]].append(evidence_dict)

        for relation, evidences in relation_evidences.items():
            edges_entry.append({
                'source': node_bel[u],
                'target': node_bel[v],
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
