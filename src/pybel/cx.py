import logging
import time

from .canonicalize import decanonicalize_node
from .constants import *
from .utils import expand_dict

log = logging.getLogger(__name__)


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

    for node_id, (node, data) in enumerate(graph.nodes_iter(data=True)):
        node_nid[node] = node_id
        nid_data[node_id] = data

        nodes_entry.append({
            '@id': node_id,
            'n': data[NAME] if NAME in data else decanonicalize_node(graph, node),
        })

        for k, v in expand_dict(data).items():
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

        if EVIDENCE not in d:
            continue

        edges_entry.append({
            '@id': eid,
            's': uid,
            't': vid,
            'i': d[RELATION],
        })

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
            for k, v in expand_dict(d[SUBJECT]).items():
                edge_attributes_entry.append({
                    'po': eid,
                    'n': k,
                    'v': v
                })

        if OBJECT in d:
            for k, v in expand_dict(d[OBJECT]).items():
                edge_attributes_entry.append({
                    'po': eid,
                    'n': k,
                    'v': v
                })

    context_entry = [dict(graph.namespace_url)]

    network_attributes_entry = [{
        "n": "ndex:sourceFormat",
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
    """Rebuilds a BELGraph from CX JSON

    :param cx: The CX JSON for this graph
    :type cx: list
    :return: A BEL Graph
    :rtype: pybel.BELGraph
    """
    raise NotImplementedError
