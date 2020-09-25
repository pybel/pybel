# -*- coding: utf-8 -*-

"""Conversion functions for BEL graphs with JGIF JSON.

The JSON Graph Interchange Format (JGIF) is `specified <http://jsongraphformat.info/>`_ similarly to the Node-Link
JSON. Interchange with this format provides compatibilty with other software and repositories, such as the
`Causal Biological Network Database <http://causalbionet.com/>`_.
"""

import gzip
import json
import logging
import re
from collections import defaultdict
from operator import methodcaller
from typing import Any, Mapping, Optional, TextIO, Union

import requests
from networkx.utils import open_file
from pyparsing import ParseException

from .. import constants as pc
from ..constants import (
    ANNOTATIONS, CITATION, EVIDENCE, GRAPH_ANNOTATION_URL, GRAPH_NAMESPACE_URL, METADATA_AUTHORS, METADATA_CONTACT,
    METADATA_INSERT_KEYS, METADATA_LICENSES, RELATION, UNQUALIFIED_EDGES,
)
from ..exceptions import NakedNameWarning, UndefinedNamespaceWarning
from ..parser import BELParser
from ..struct import BELGraph
from ..version import get_version

__all__ = [
    'from_cbn_jgif',
    'from_cbn_jgif_file',
    'from_jgif',
    'from_jgif_file',
    'from_jgif_gz',
    'from_jgif_jsons',
    'to_jgif',
    'to_jgif_file',
    'to_jgif_gz',
    'to_jgif_jsons',
    'post_jgif',
]

logger = logging.getLogger(__name__)

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


def map_cbn(d):
    """Pre-processes the JSON from the CBN.

    - removes statements without evidence, or with placeholder evidence

    :param dict d: Raw JGIF from the CBN
    :return: Preprocessed JGIF
    :rtype: dict
    """
    for i, edge in enumerate(d['graph']['edges']):
        if 'metadata' not in edge:
            continue

        if 'evidences' not in edge['metadata']:
            continue

        for j, evidence in enumerate(edge['metadata']['evidences']):
            if EXPERIMENT_CONTEXT not in evidence:
                continue

            # ctx = {k.strip().lower(): v.strip() for k, v in evidence[EXPERIMENT_CONTEXT].items() if v.strip()}

            new_context = {}

            for key, value in evidence[EXPERIMENT_CONTEXT].items():
                if not value:
                    logger.debug('key %s without value', key)
                    continue

                value = value.strip()

                if not value:
                    logger.debug('key %s without value', key)
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

            # TODO can this be replaced with edge as well?
            d['graph']['edges'][i]['metadata']['evidences'][j][EXPERIMENT_CONTEXT] = new_context

    return d


NAMESPACE_URLS = {
    "TAX": "https://arty.scai.fraunhofer.de/artifactory/bel/namespace/ncbi-taxonomy/ncbi-taxonomy-20200322.belns",
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
    'GOCCID': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/go-cellular-component-ids/go-cellular-component-ids-20150601.belns',
    'MESHCS': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/mesh-cell-structures/mesh-cell-structures-20150601.belns',
}

ANNOTATION_URLS = {
    'Cell': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/cell-line/cell-line-20150601.belanno',
    'Disease': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/disease/disease-20150601.belanno',
    'Species': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/species-taxonomy-id/species-taxonomy-id-20170511.belanno',
    'Tissue': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/mesh-anatomy/mesh-anatomy-20150601.belanno',
}

NAMESPACE_TO_PATTERN = {
    namespace: re.compile(r'.*')  # don't validate anything
    for namespace in (set(NAMESPACE_URLS) | {'GO', 'MESH'})
}


@open_file(0, mode='r')
def from_cbn_jgif_file(path: Union[str, TextIO]) -> BELGraph:
    """Build a graph from a file containing the CBN variant of JGIF.

    :param path: A path or file-like
    """
    return from_cbn_jgif(json.load(path))


def from_cbn_jgif(graph_jgif_dict):
    """Build a BEL graph from CBN JGIF.

    Map the JGIF used by the Causal Biological Network Database to standard namespace and annotations, then
    builds a BEL graph using :func:`pybel.from_jgif`.

    :param dict graph_jgif_dict: The JSON object representing the graph in JGIF format
    :rtype: BELGraph

    Example:
    .. code-block:: python

        import requests
        from pybel import from_cbn_jgif
        apoptosis_url = 'http://causalbionet.com/Networks/GetJSONGraphFile?networkId=810385422'
        graph_jgif_dict = requests.get(apoptosis_url).json()
        graph = from_cbn_jgif(graph_jgif_dict)

    .. warning::

        Handling the annotations is not yet supported, since the CBN documents do not refer to the resources used
        to create them. This may be added in the future, but the annotations must be stripped from the graph
        before uploading to the network store using :func:`pybel.struct.mutation.strip_annotations`.

    """
    graph_jgif_dict = map_cbn(graph_jgif_dict)

    graph_jgif_dict['graph'][GRAPH_NAMESPACE_URL] = NAMESPACE_URLS
    graph_jgif_dict['graph'][GRAPH_ANNOTATION_URL] = ANNOTATION_URLS
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
    return graph


def from_jgif(graph_jgif_dict, parser_kwargs: Optional[Mapping[str, Any]] = None):  # noqa:C901
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

    for k in (GRAPH_ANNOTATION_URL, GRAPH_NAMESPACE_URL):
        if k in root:
            graph.graph[k] = root[k]

    parser = BELParser(graph, namespace_to_pattern=NAMESPACE_TO_PATTERN)
    parser.bel_term.addParseAction(parser.handle_term)

    for node in root['nodes']:
        node_label = node.get('label')

        if node_label is None:
            logger.warning('node missing label: %s', node)
            continue

        try:
            parser.bel_term.parseString(node_label)
        except NakedNameWarning as e:
            logger.info('Naked name: %s', e)
        except UndefinedNamespaceWarning as e:
            logger.info('Undefined namespace: %s', e)
        except ParseException:
            logger.info('Parse exception for %s', node_label)

    for i, edge in enumerate(root['edges']):
        relation = edge.get('relation')
        if relation is None:
            logger.warning('no relation for edge: %s', edge)

        if relation in {'actsIn', 'translocates'}:
            continue  # don't need legacy BEL format

        edge_metadata = edge.get('metadata')
        if edge_metadata is None:
            logger.warning('no metadata for edge: %s', edge)
            continue

        bel_statement = edge.get('label')
        if bel_statement is None:
            logger.debug('No BEL statement for edge %s', edge)

        evidences = edge_metadata.get('evidences')

        if relation in UNQUALIFIED_EDGES:
            pass  # FIXME?

        else:
            if not evidences:  # is none or is empty list
                logger.debug('No evidence for edge %s', edge)
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
                citation_namespace = citation['type'].lower().strip()
                citation_namespace = pc.CITATION_NORMALIZER.get(citation_namespace, citation_namespace)
                parser.control_parser.citation_db = citation_namespace
                parser.control_parser.citation_db_id = citation['id'].strip()
                parser.control_parser.evidence = summary_text
                annotations = parser.graph._clean_annotations(evidence[EXPERIMENT_CONTEXT])
                parser.control_parser.annotations.update(annotations)

                try:
                    parser.parseString(bel_statement, line_number=i)
                except Exception as e:
                    logger.warning('JGIF relation parse error: %s for %s', e, bel_statement)

    return graph


@open_file(0, mode='r')
def from_jgif_file(path: Union[str, TextIO]) -> BELGraph:
    """Build a graph from the JGIF JSON contained in the given file.

    :param path: A path or file-like
    """
    return from_jgif(json.load(path))


def from_jgif_gz(path: str) -> BELGraph:
    """Read a graph as JGIF JSON from a gzip file."""
    with gzip.open(path, 'rt') as file:
        return from_jgif(json.load(file))


def from_jgif_jsons(graph_json_str: str) -> BELGraph:
    """Read a BEL graph from a JGIF JSON string."""
    return from_jgif(json.loads(graph_json_str))


def to_jgif(graph):
    """Build a JGIF dictionary from a BEL graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: A JGIF dictionary
    :rtype: dict

    .. warning::

        Untested! This format is not general purpose and is therefore time is not heavily invested. If you want to
        use Cytoscape.js, we suggest using :func:`pybel.to_cx` instead.

    The example below shows how to output a BEL graph as a JGIF dictionary.

    .. code-block:: python

        import os
        from pybel.examples import sialic_acid_graph
        graph_jgif_json = pybel.to_jgif(sialic_acid_graph)

    If you want to write the graph directly to a file as JGIF, see func:`to_jgif_file`.
    """
    u_v_r_bel = {}

    nodes_entry = []
    edges_entry = []

    for node in sorted(graph, key=methodcaller('as_bel')):
        nodes_entry.append({
            'id': node.md5,
            'label': node.as_bel(),
            'bel_function_type': node.function,
        })

    for u, v in graph.edges():
        relation_evidences = defaultdict(list)

        for key, data in graph[u][v].items():
            if (u, v, data[RELATION]) not in u_v_r_bel:
                u_v_r_bel[u, v, data[RELATION]] = graph.edge_to_bel(u, v, edge_data=data)

            bel = u_v_r_bel[u, v, data[RELATION]]

            evidence_dict = {
                'bel_statement': bel,
                'key': key,
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
                'source': u.md5,
                'target': v.md5,
                'relation': relation,
                'label': u_v_r_bel[u, v, relation],
                'metadata': {
                    'evidences': evidences,
                },
            })

    return {
        'graph': {
            'metadata': dict(
                origin=dict(name='pybel', version=get_version()),
                **graph.document,
            ),
            'nodes': nodes_entry,
            'edges': edges_entry,
        },
    }


@open_file(1, mode='w')
def to_jgif_file(graph: BELGraph, file: Union[str, TextIO], **kwargs) -> None:
    """Write JGIF to a file.

    :param graph: A BEL graph
    :param file: A writable file or file-like

    The example below shows how to output a BEL graph as JGIF to an open file.

    .. code-block:: python

       from pybel.examples import sialic_acid_graph
       from pybel import to_jgif_file
       with open('graph.bel.jgif.json', 'w') as file:
           to_jgif_file(sialic_acid_graph, file)

    The example below shows how to output a BEL graph as JGIF to a file at a given path.

    .. code-block:: python

        from pybel.examples import sialic_acid_graph
        from pybel import to_jgif_file
        to_jgif_file(sialic_acid_graph, 'graph.bel.jgif.json')

    If you have a big graph, you might consider storing it as a gzipped JGIF file
    by using :func:`to_jgif_gz`.
    """
    json.dump(to_jgif(graph), file, ensure_ascii=False, **kwargs)


def to_jgif_gz(graph, path: str, **kwargs) -> None:
    """Write a graph as JGIF JSON to a gzip file."""
    with gzip.open(path, 'wt') as file:
        json.dump(to_jgif(graph), file, ensure_ascii=False, **kwargs)


def to_jgif_jsons(graph: BELGraph, **kwargs) -> str:
    """Dump this graph as a JGIF JSON object to a string."""
    return json.dumps(to_jgif(graph), ensure_ascii=False, **kwargs)


def post_jgif(graph: BELGraph, url: str, **kwargs) -> requests.Response:
    """Post the JGIF to a given URL."""
    return requests.post(url, json=to_jgif(graph), **kwargs)
