import logging
import time
from collections import defaultdict

from .canonicalize import calculate_canonical_name
from .constants import *
from .graph import BELGraph
from .utils import flatten_dict, expand_dict

__all__ = [
    'to_cx_json',
    'from_cx_json'
]

log = logging.getLogger(__name__)

NDEX_SOURCE_FORMAT = "ndex:sourceFormat"


def hash_tuple(x):
    h = 0
    for i in x:
        if isinstance(i, tuple):
            h += hash_tuple(i)
        else:
            h += hash(i)
    return h


def to_cx_json(graph):
    """Converts BEL Graph to CX data format (as in-memory JSON) for use with `NDEx <http://www.ndexbio.org/>`_

    :param graph: A BEL Graph
    :type graph: pybel.BELGraph
    :return: The CX JSON for this graph
    :rtype: list

    .. seealso::

        - `NDEx Python Client <https://github.com/ndexbio/ndex-python>`_
        - `PyBEL / NDEx Python Client Wrapper <https://github.com/cthoyt/pybel2cx>`_

    """
    node_nid = {}
    nid_data = {}
    nodes_entry = []
    node_attributes_entry = []

    for node_id, node in enumerate(sorted(graph.nodes_iter(), key=hash_tuple)):
        data = graph.node[node]
        node_nid[node] = node_id
        nid_data[node_id] = data

        nodes_entry.append({
            '@id': node_id,
            'n': calculate_canonical_name(graph, node)
        })

        for k, v in data.items():
            if k == VARIANTS:
                for i, el in enumerate(v):
                    for a, b in flatten_dict(el).items():
                        node_attributes_entry.append({
                            'po': node_id,
                            'n': '{}_{}_{}'.format(k, i, a),
                            'v': b
                        })
            elif k == FUSION:
                for a, b in flatten_dict(v).items():
                    node_attributes_entry.append({
                        'po': node_id,
                        'n': '{}_{}'.format(k, a),
                        'v': b

                    })

            elif k == NAME:
                node_attributes_entry.append({
                    'po': node_id,
                    'n': 'identifier',
                    'v': v
                })
            else:
                node_attributes_entry.append({
                    'po': node_id,
                    'n': k,
                    'v': v
                })

    edges_entry = []
    edge_attributes_entry = []

    for eid, (source, target, d) in enumerate(graph.edges_iter(data=True)):
        uid = node_nid[source]
        vid = node_nid[target]

        edges_entry.append({
            '@id': eid,
            's': uid,
            't': vid,
            'i': d[RELATION],
        })

        if EVIDENCE in d:
            edge_attributes_entry.append({
                'po': eid,
                'n': EVIDENCE,
                'v': d[EVIDENCE]
            })

            for k, v in d[CITATION].items():
                edge_attributes_entry.append({
                    'po': eid,
                    'n': '{}_{}'.format(CITATION, k),
                    'v': v
                })

        for k, v in d[ANNOTATIONS].items():
            edge_attributes_entry.append({
                'po': eid,
                'n': k,
                'v': v
            })

        if SUBJECT in d:
            for k, v in flatten_dict(d[SUBJECT]).items():
                edge_attributes_entry.append({
                    'po': eid,
                    'n': '{}_{}'.format(SUBJECT, k),
                    'v': v
                })

        if OBJECT in d:
            for k, v in flatten_dict(d[OBJECT]).items():
                edge_attributes_entry.append({
                    'po': eid,
                    'n': '{}_{}'.format(OBJECT, k),
                    'v': v
                })

    context_entry = [dict(graph.namespace_url)]

    network_attributes_entry = [{
        "n": NDEX_SOURCE_FORMAT,
        "v": "PyBEL"
    }]
    for k, v in graph.document.items():
        network_attributes_entry.append({
            'n': k,
            'v': v
        })

    # Coalesce to cx
    # cx = create_aspect.number_verification()
    cx = [{'numberVerification': [{'longNumber': 281474976710655}]}]

    cx_pairs = [
        ('@context', context_entry),
        ('networkAttributes', network_attributes_entry),
        ('nodes', nodes_entry),
        ('nodeAttributes', node_attributes_entry),
        ('edges', edges_entry),
        ('edgeAttributes', edge_attributes_entry),
    ]

    cx_metadata = []

    for key, aspect in cx_pairs:
        aspect_dict = {
            "name": key,
            "elementCount": len(aspect),
            "lastUpdate": time.time(),
            "consistencyGroup": 1,
            "properties": [],
            "version": "1.0"
        }

        if key in {'citations', 'supports', 'nodes', 'edges'}:
            aspect_dict['idCounter'] = len(aspect)

        cx_metadata.append(aspect_dict)

    cx.append({
        'metaData': cx_metadata
    })

    for key, aspect in cx_pairs:
        cx.append({
            key: aspect
        })

    return cx


def from_cx_json(cx):
    """Rebuilds a BELGraph from CX JSON output from PyBEL

    :param cx: The CX JSON for this graph
    :type cx: list
    :return: A BEL Graph
    :rtype: pybel.BELGraph
    """

    graph = BELGraph()
    graph.graph[GRAPH_METADATA] = {}

    context_entry = cx[2]
    for d in context_entry['@context']:
        for k, v in d.items():
            if v.endswith('.belns'):
                pass
            elif v.endswith('.belanno'):
                pass
            elif v.endswith('.owl'):
                pass
            else:
                pass

    network_attributes_entry = cx[3]
    for d in network_attributes_entry['networkAttributes']:
        if d['n'] == NDEX_SOURCE_FORMAT:
            continue
        graph.graph[GRAPH_METADATA][d['n']] = d['v']

    node_entries = cx[4]
    node_name = {}
    for d in node_entries['nodes']:
        node_name[d['@id']] = d['n']

    node_attributes_entries = cx[5]
    node_data = defaultdict(dict)
    for d in node_attributes_entries['nodeAttributes']:
        node_data[d['po']][d['n']] = d['v']

    node_data_pp = defaultdict(dict)
    node_data_fusion = defaultdict(dict)
    node_data_variants = defaultdict(lambda: defaultdict(dict))

    for nid, d in node_data.items():
        for k, v in d.items():
            if k.startswith(FUSION):
                node_data_fusion[nid][k] = v
            elif k.startswith(VARIANTS):
                _, i, vls = k.split('_', 2)
                node_data_variants[nid][i][vls] = v
            else:
                node_data_pp[nid][k] = v

    for nid, d in node_data_fusion.items():
        node_data_pp[nid][FUSION] = expand_dict(d)

    for nid, d in node_data_variants.items():
        node_data_pp[nid][VARIANTS] = [expand_dict(d[i]) for i in sorted(d)]

    for nid, d in node_data_pp.items():
        if 'identifier' in d:
            d[NAME] = d.pop('identifier')
        graph.add_node(nid, attr_dict=d)

    edges_entries = cx[6]
    edge_relation = {}
    edge_source = {}
    edge_target = {}
    for d in edges_entries['edges']:
        eid = d['@id']
        edge_relation[eid] = d['i']
        edge_source[eid] = d['s']
        edge_target[eid] = d['t']

    edge_annotations_entries = cx[7]
    edge_data = defaultdict(dict)
    for d in edge_annotations_entries['edgeAttributes']:
        edge_data[d['po']][d['n']] = d['v']

    edge_citation = defaultdict(dict)
    edge_subject = defaultdict(dict)
    edge_object = defaultdict(dict)
    edge_annotations = defaultdict(dict)

    edge_data_pp = defaultdict(dict)

    for eid, d in edge_data.items():
        for k, v in d.items():
            if k.startswith(CITATION):
                _, vl = k.split('_', 1)
                edge_citation[eid][vl] = v
            elif k.startswith(SUBJECT):
                _, vl = k.split('_', 1)
                edge_subject[eid][vl] = v
            elif k.startswith(OBJECT):
                _, vl = k.split('_', 1)
                edge_object[eid][vl] = v
            elif k == EVIDENCE:
                edge_data_pp[eid][EVIDENCE] = v
            else:
                edge_annotations[eid][k] = v

    for eid, d in edge_citation.items():
        edge_data_pp[eid][CITATION] = d

    for eid, d in edge_subject.items():
        edge_data_pp[eid][SUBJECT] = expand_dict(d)

    for eid, d in edge_object.items():
        edge_data_pp[eid][OBJECT] = expand_dict(d)

    for eid in edge_relation:
        edge_data_pp[eid][ANNOTATIONS] = edge_annotations[eid] if eid in edge_annotations else {}

        if eid in edge_citation:
            graph.add_edge(
                edge_source[eid],
                edge_target[eid],
                attr_dict=edge_data_pp[eid],
                **{RELATION: edge_relation[eid]}
            )
        elif edge_relation[eid] in unqualified_edges:
            graph.add_edge(
                edge_source[eid],
                edge_target[eid],
                key=unqualified_edge_code[edge_relation[eid]],
                **{RELATION: edge_relation[eid], ANNOTATIONS: {}}
            )
        else:
            raise ValueError('problem adding edge: {}'.format(eid))

    return graph
