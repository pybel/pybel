# -*- coding: utf-8 -*-

"""Conversion functions for BEL graphs with JGIF JSON.

The JSON Graph Interchange Format (JGIF) is `specified <http://jsongraphformat.info/>`_ similarly to the Node-Link
JSON. Interchange with this format provides compatibilty with other software and repositories, such as the 
`Causal Biological Network Database <http://causalbionet.com/>`_.
"""

import logging
from collections import defaultdict

from pyparsing import ParseException

from ..canonicalize import node_to_bel
from ..constants import (
    ANNOTATIONS, CITATION, CITATION_REFERENCE, CITATION_TYPE, EVIDENCE, FUNCTION, METADATA_AUTHORS, METADATA_CONTACT,
    METADATA_INSERT_KEYS, METADATA_LICENSES, RELATION, UNQUALIFIED_EDGES,
)
from ..parser import BelParser
from ..parser.exc import NakedNameWarning
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


def reformat_citation(citation):
    """Reformat a citation dictionary.

    :type citation: dict[str,str]
    :rtype: dict[str,str]
    """
    return {
        CITATION_TYPE: citation['type'].strip(),
        CITATION_REFERENCE: citation['id'].strip()
    }


def map_cbn(d):
    """Pre-processes the JSON from the CBN.

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
                if not value:
                    log.debug('key %s without value', key)
                    continue

                value = value.strip()

                if not value:
                    log.debug('key %s without value', key)
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
    """Build a BEL graph from CBN JGIF.

    Map the JGIF used by the Causal Biological Network Database to standard namespace and annotations, then
    builds a BEL graph using :func:`pybel.from_jgif`.

    :param dict graph_jgif_dict: The JSON object representing the graph in JGIF format
    :rtype: BELGraph

    Example:

    >>> import requests
    >>> from pybel import from_cbn_jgif
    >>> apoptosis_url = 'http://causalbionet.com/Networks/GetJSONGraphFile?networkId=810385422'
    >>> graph_jgif_dict = requests.get(apoptosis_url).json()
    >>> graph = from_cbn_jgif(graph_jgif_dict)

    .. warning::

        Handling the annotations is not yet supported, since the CBN documents do not refer to the resources used
        to create them. This may be added in the future, but the annotations must be stripped from the graph
        before uploading to the network store using :func:`pybel.struct.mutation.strip_annotations`
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
        """.replace('\n', '\t'),
        METADATA_CONTACT: 'CausalBiologicalNetworks.RD@pmi.com',
    })

    graph = from_jgif(graph_jgif_dict)

    graph.namespace_url.update({
        'HGNC': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/hgnc-human-genes/hgnc-human-genes-20150601.belns',
        'GOBP': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/go-biological-process/go-biological-process-20150601.belns',
        'SFAM': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/selventa-protein-families/selventa-protein-families-20150601.belns',
        'GOCC': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/go-cellular-component/go-cellular-component-20170511.belns',
        'MESHPP': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/mesh-processes/mesh-processes-20150601.belns',
        'MGI': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/mgi-mouse-genes/mgi-mouse-genes-20150601.belns',
        'RGD': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/rgd-rat-genes/rgd-rat-genes-20150601.belns',
        'CHEBI': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/chebi/chebi-20150601.belns',
        'SCHEM': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/selventa-legacy-chemicals/selventa-legacy-chemicals-20150601.belns',
        'EGID': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/entrez-gene-ids/entrez-gene-ids-20150601.belns',
        'MESHD': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/mesh-diseases/mesh-diseases-20150601.belns',
        'SDIS': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/selventa-legacy-diseases/selventa-legacy-diseases-20150601.belns',
        'SCOMP': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/selventa-named-complexes/selventa-named-complexes-20150601.belns',
        'MESHC': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/mesh-chemicals/mesh-chemicals-20170511.belns',
        'GOBPID': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/go-biological-process-ids/go-biological-process-ids-20150601.belns',
        'MESHCS': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/mesh-cell-structures/mesh-cell-structures-20150601.belns',
    })

    graph.annotation_url.update({
        'Cell': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/cell-line/cell-line-20150601.belanno',
        'Disease': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/disease/disease-20150601.belanno',
        'Species': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/species-taxonomy-id/species-taxonomy-id-20170511.belanno',
        'Tissue': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/mesh-anatomy/mesh-anatomy-20150601.belanno',
    })

    return graph


def from_jgif(graph_jgif_dict):
    """Build a BEL graph from a JGIF JSON object.

    :param dict graph_jgif_dict: The JSON object representing the graph in JGIF format
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
        node_label = node.get('label')

        if node_label is None:
            log.warning('node missing label: %s', node)
            continue

        try:
            parser.bel_term.parseString(node_label)
        except NakedNameWarning as e:
            log.info('Naked name: %s', e)
        except ParseException:
            log.info('Parse exception for %s', node_label)

    for i, edge in enumerate(root['edges']):
        relation = edge.get('relation')
        if relation is None:
            log.warning('no relation for edge: %s', edge)

        if relation in {'actsIn', 'translocates'}:
            continue  # don't need legacy BEL format

        edge_metadata = edge.get('metadata')
        if edge_metadata is None:
            log.warning('no metadata for edge: %s', edge)
            continue

        bel_statement = edge.get('label')
        if bel_statement is None:
            log.debug('No BEL statement for edge %s', edge)

        evidences = edge_metadata.get('evidences')

        if relation in UNQUALIFIED_EDGES:
            pass  # FIXME?

        else:
            if not evidences:  # is none or is empty list
                log.debug('No evidence for edge %s', edge)
                continue

            for evidence in evidences:
                citation = evidence.get('citation')

                if not citation:
                    continue

                if 'type' not in citation or 'id' not in citation:
                    continue

                summary_text = evidence['summary_text'].strip()

                if not summary_text or summary_text == placeholder_evidence:
                    continue

                parser.control_parser.clear()
                parser.control_parser.citation = reformat_citation(citation)
                parser.control_parser.evidence = summary_text
                parser.control_parser.annotations.update(evidence[EXPERIMENT_CONTEXT])

                try:
                    parser.parseString(bel_statement, line_number=i)
                except Exception as e:
                    log.warning('JGIF relation parse error: %s for %s', e, bel_statement)

    return graph


def to_jgif(graph):
    """Build a JGIF dictionary from a BEL graph.

    :param pybel.BELGraph graph: A BEL graph
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

    for i, (node, node_data) in enumerate(graph.iter_node_data_pairs()):
        bel = node_to_bel(node_data)
        node_bel[node] = bel

        nodes_entry.append({
            'id': bel,
            'label': bel,
            'nodeId': i,
            'bel_function_type': node_data[FUNCTION],
            'metadata': {}
        })

    for u, v in graph.edges():
        relation_evidences = defaultdict(list)

        for data in graph[u][v].values():

            if (u, v, data[RELATION]) not in u_v_r_bel:
                u_v_r_bel[u, v, data[RELATION]] = graph.edge_to_bel(u, v, data=data)

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
