# -*- coding: utf-8 -*-

"""This module contains output functions to BEL scripts."""

from __future__ import print_function

import itertools as itt
import logging
import sys
import time

from operator import itemgetter

from .constants import *
from .parser.language import rev_abundance_labels
from .struct.filters import filter_provenance_edges
from .utils import ensure_quotes, flatten_citation, get_version, hash_edge

__all__ = [
    'to_bel_lines',
    'to_bel',
    'to_bel_path'
]

log = logging.getLogger(__name__)


def postpend_location(bel_string, location_model):
    """Rips off the closing parentheses and adds canonicalized modification.

    I did this because writing a whole new parsing model for the data would be sad and difficult

    :param str bel_string: BEL string representing node
    :param dict location_model: A dictionary containing keys :code:`pybel.constants.TO_LOC` and
                                :code:`pybel.constants.FROM_LOC`
    :return: A part of a BEL string representing the location
    :rtype: str
    """
    if not all(k in location_model for k in {NAMESPACE, NAME}):
        raise ValueError('Location model missing namespace and/or name keys: {}'.format(location_model))

    return "{}, loc({}:{}))".format(
        bel_string[:-1],
        location_model[NAMESPACE],
        ensure_quotes(location_model[NAME])
    )


def variant_to_bel(tokens):
    """

    :param tokens:
    :rtype: str
    """
    if tokens[KIND] == PMOD:
        if tokens[IDENTIFIER][NAMESPACE] == BEL_DEFAULT_NAMESPACE:
            name = tokens[IDENTIFIER][NAME]
        else:
            name = '{}:{}'.format(tokens[IDENTIFIER][NAMESPACE], tokens[IDENTIFIER][NAME])
        return 'pmod({}{})'.format(name, ''.join(', {}'.format(tokens[x]) for x in PMOD_ORDER[2:] if x in tokens))

    elif tokens[KIND] == GMOD:
        if tokens[IDENTIFIER][NAMESPACE] == BEL_DEFAULT_NAMESPACE:
            name = tokens[IDENTIFIER][NAME]
        else:
            name = '{}:{}'.format(tokens[IDENTIFIER][NAMESPACE], tokens[IDENTIFIER][NAME])
        return 'gmod({})'.format(name)

    elif tokens[KIND] == HGVS:
        return 'var({})'.format(tokens[IDENTIFIER])

    elif tokens[KIND] == FRAGMENT:
        if FRAGMENT_MISSING in tokens:
            res = '?'
        else:
            res = '{}_{}'.format(tokens[FRAGMENT_START], tokens[FRAGMENT_STOP])

        if FRAGMENT_DESCRIPTION in tokens:
            res += ', {}'.format(tokens[FRAGMENT_DESCRIPTION])

        return 'frag({})'.format(res)


def fusion_range_to_bel(tokens):
    """

    :param tokens:
    :rtype: str
    """
    if FUSION_REFERENCE in tokens:
        return '{}.{}_{}'.format(tokens[FUSION_REFERENCE], tokens[FUSION_START], tokens[FUSION_STOP])
    return '?'


def get_targets_by_relation(graph, node, relation):
    """Gets the set of neighbors of a given node that have a relation of the given type

    :param BELGraph graph: A BEL network
    :param tuple node: A BEL node
    :param relation: the relation to follow from the given node
    :return: A set of BEL nodes
    :rtype: set[tuple]
    """
    return {
        target
        for _, target, data in graph.out_edges_iter(node, data=True)
        if data[RELATION] == relation
    }


def node_to_bel(graph, node):
    """Returns a node from a graph as a BEL string

    :param BELGraph graph: A BEL Graph
    :param tuple node: a node from the BEL graph
    :rtype: str
    """
    data = graph.node[node]

    if data[FUNCTION] == REACTION:
        reactants = get_targets_by_relation(graph, node, HAS_REACTANT)
        reactants_canon = sorted(map(lambda n: node_to_bel(graph, n), reactants))
        products = get_targets_by_relation(graph, node, HAS_PRODUCT)
        products_canon = sorted(map(lambda n: node_to_bel(graph, n), products))
        return 'rxn(reactants({}), products({}))'.format(', '.join(reactants_canon), ', '.join(products_canon))

    if data[FUNCTION] in {COMPOSITE, COMPLEX} and NAMESPACE not in data:
        members = get_targets_by_relation(graph, node, HAS_COMPONENT)
        members_canon = sorted(map(lambda n: node_to_bel(graph, n), members))
        return '{}({})'.format(rev_abundance_labels[data[FUNCTION]], ', '.join(members_canon))

    if VARIANTS in data:
        variants_canon = sorted(map(variant_to_bel, data[VARIANTS]))
        return "{}({}:{}, {})".format(
            rev_abundance_labels[data[FUNCTION]],
            data[NAMESPACE],
            ensure_quotes(data[NAME]),
            ', '.join(variants_canon)
        )

    if FUSION in data:
        return "{}(fus({}:{}, {}, {}:{}, {}))".format(
            rev_abundance_labels[data[FUNCTION]],
            data[FUSION][PARTNER_5P][NAMESPACE],
            data[FUSION][PARTNER_5P][NAME],
            fusion_range_to_bel(data[FUSION][RANGE_5P]),
            data[FUSION][PARTNER_3P][NAMESPACE],
            data[FUSION][PARTNER_3P][NAME],
            fusion_range_to_bel(data[FUSION][RANGE_3P])
        )

    if data[FUNCTION] in {GENE, RNA, MIRNA, PROTEIN, ABUNDANCE, COMPLEX, PATHOLOGY, BIOPROCESS}:
        return "{}({}:{})".format(
            rev_abundance_labels[data[FUNCTION]],
            data[NAMESPACE],
            ensure_quotes(data[NAME])
        )

    raise ValueError('Unknown node data: {} {}'.format(node, data))


def _decanonicalize_edge_node(graph, node, edge_data, node_position):
    """Writes a node with its modifiers stored in the given edge

    :param BELGraph graph: A BEL graph
    :param tuple node: A PyBEL node tuple
    :param dict edge_data: A PyBEL edge data dictionary
    :param node_position: Either :data:`pybel.constants.SUBJECT` or :data:`pybel.constants.OBJECT`
    :rtype: str
    """
    if node_position not in {SUBJECT, OBJECT}:
        raise ValueError('invalid node position: {}'.format(node_position))

    node_str = node_to_bel(graph, node)

    if node_position not in edge_data:
        return node_str

    node_edge_data = edge_data[node_position]

    if LOCATION in node_edge_data:
        node_str = postpend_location(node_str, node_edge_data[LOCATION])

    if MODIFIER in node_edge_data and DEGRADATION == node_edge_data[MODIFIER]:
        node_str = "deg({})".format(node_str)

    elif MODIFIER in node_edge_data and ACTIVITY == node_edge_data[MODIFIER]:
        node_str = "act({}".format(node_str)
        if EFFECT in node_edge_data and node_edge_data[EFFECT]:  # TODO remove and node_edge_data[EFFECT]
            ma = node_edge_data[EFFECT]

            if ma[NAMESPACE] == BEL_DEFAULT_NAMESPACE:
                node_str = "{}, ma({}))".format(node_str, ma[NAME])
            else:
                node_str = "{}, ma({}:{}))".format(node_str, ma[NAMESPACE], ensure_quotes(ma[NAME]))
        else:
            node_str = "{})".format(node_str)

    elif MODIFIER in node_edge_data and TRANSLOCATION == node_edge_data[MODIFIER]:
        from_loc = "fromLoc({}:{})".format(
            node_edge_data[EFFECT][FROM_LOC][NAMESPACE],
            ensure_quotes(node_edge_data[EFFECT][FROM_LOC][NAME])
        )

        to_loc = "toLoc({}:{})".format(
            node_edge_data[EFFECT][TO_LOC][NAMESPACE],
            ensure_quotes(node_edge_data[EFFECT][TO_LOC][NAME])
        )

        node_str = "tloc({}, {}, {})".format(node_str, from_loc, to_loc)

    return node_str


def edge_to_bel(graph, u, v, k, sep=' '):
    """Takes two nodes and gives back a BEL string representing the statement

    :param BELGraph graph: A BEL graph
    :param tuple u: The edge's source's PyBEL node tuple
    :param tuple v: The edge's target's PyBEL node tuple
    :param int k: The edge's key
    :return: The canonical BEL for this edge
    :rtype: str
    """
    data = graph.edge[u][v][k]

    u_str = _decanonicalize_edge_node(graph, u, data, node_position=SUBJECT)
    v_str = _decanonicalize_edge_node(graph, v, data, node_position=OBJECT)

    return sep.join([u_str, data[RELATION], v_str])


def sort_dict_items(d):
    """Returns the dictionary's items, sorted by their keys

    :param dict d: A dictionary
    :rtype: iter[tuple]
    """
    return sorted(d.items(), key=itemgetter(0))


def to_bel_lines(graph):
    """Returns an iterable over the lines of the BEL graph as a canonical BEL Script (.bel)

    :param BELGraph graph: the BEL Graph to output as a BEL Script
    :return: An iterable over the lines of the representative BEL script
    :rtype: iter[str]
    """
    yield '# Output by PyBEL v{} on {}\n'.format(get_version(), time.asctime())

    for k in sorted(graph.document):
        yield 'SET DOCUMENT {} = "{}"'.format(INVERSE_DOCUMENT_KEYS[k], graph.document[k])

    yield '###############################################\n'

    if GOCC_KEYWORD not in graph.namespace_url:
        graph.namespace_url[GOCC_KEYWORD] = GOCC_LATEST

    for namespace, url in sort_dict_items(graph.namespace_url):
        yield 'DEFINE NAMESPACE {} AS URL "{}"'.format(namespace, url)

    for namespace, url in sort_dict_items(graph.namespace_owl):
        yield 'DEFINE NAMESPACE {} AS OWL "{}"'.format(namespace, url)

    for namespace, pattern in sort_dict_items(graph.namespace_pattern):
        yield 'DEFINE NAMESPACE {} AS PATTERN "{}"'.format(namespace, pattern)

    yield '###############################################\n'

    for annotation, url in sort_dict_items(graph.annotation_url):
        yield 'DEFINE ANNOTATION {} AS URL "{}"'.format(annotation, url)

    for annotation, url in sort_dict_items(graph.annotation_owl):
        yield 'DEFINE ANNOTATION {} AS OWL "{}"'.format(annotation, url)

    for annotation, pattern in sort_dict_items(graph.annotation_pattern):
        yield 'DEFINE ANNOTATION {} AS PATTERN "{}"'.format(annotation, pattern)

    for annotation, values in sort_dict_items(graph.annotation_list):
        yield 'DEFINE ANNOTATION {} AS LIST {{{}}}'.format(annotation, ', '.join('"{}"'.format(e) for e in values))

    yield '###############################################\n'

    # sort by citation, then supporting text
    qualified_edges_iter = filter_provenance_edges(graph)
    qualified_edges = sorted(qualified_edges_iter, key=lambda edge: hash_edge(*edge))

    for citation, citation_edges in itt.groupby(qualified_edges, key=lambda t: flatten_citation(t[3][CITATION])):
        yield 'SET Citation = {{{}}}'.format(citation)

        for evidence, evidence_edges in itt.groupby(citation_edges, key=lambda u_v_k_d: u_v_k_d[3][EVIDENCE]):
            yield 'SET SupportingText = "{}"'.format(evidence)

            for u, v, k, d in evidence_edges:
                dkeys = sorted(d[ANNOTATIONS])
                for dk in dkeys:
                    yield 'SET {} = "{}"'.format(dk, d[ANNOTATIONS][dk])
                yield edge_to_bel(graph, u, v, k)
                if dkeys:
                    yield 'UNSET {{{}}}'.format(', '.join('"{}"'.format(dk) for dk in dkeys))
            yield 'UNSET SupportingText'
        yield 'UNSET Citation\n'

    yield '###############################################\n'
    yield 'SET Citation = {"Other","Added by PyBEL","https://github.com/pybel/pybel/"}'
    yield 'SET SupportingText = "{}"'.format(PYBEL_AUTOEVIDENCE)

    for u, v, d in graph.edges_iter(data=True):
        if d[RELATION] not in unqualified_edge_code:
            continue

        if EVIDENCE in d:
            continue

        yield '{} {} {}'.format(node_to_bel(graph, u), d[RELATION], node_to_bel(graph, v))

    for node in graph.nodes_iter():
        if not graph.pred[node] and not graph.succ[node]:
            yield node_to_bel(graph, node)

    yield 'UNSET SupportingText'
    yield 'UNSET Citation'


def to_bel(graph, file=None):
    """Outputs the BEL graph as canonical BEL to the given file/file-like/stream. Defaults to standard out.

    :param BELGraph graph: the BEL Graph to output as a BEL Script
    :param file file: A writable file-like object. If None, defaults to standard out.
    """
    file = sys.stdout if file is None else file
    for line in to_bel_lines(graph):
        print(line, file=file)


def to_bel_path(graph, path):
    """Writes the BEL graph as a canonical BEL Script to the given path

    :param BELGraph graph: the BEL Graph to output as a BEL Script
    :param str path: A file path
    """
    with open(path, 'w') as f:
        to_bel(graph, f)


def calculate_canonical_name(graph, node):
    """Calculates the canonical name for a given node. If it is a simple node, uses the already given name.
    Otherwise, it uses the BEL string.

    :param BELGraph graph: A BEL Graph
    :param tuple node: A PyBEL node tuple
    :return: Canonical node name
    :rtype: str
    """
    data = graph.node[node]

    if data[FUNCTION] == COMPLEX and NAMESPACE in data:
        return graph.node[node][NAME]

    if VARIANTS in data:
        return node_to_bel(graph, node)

    if FUSION in data:
        return node_to_bel(graph, node)

    if data[FUNCTION] in {REACTION, COMPOSITE, COMPLEX}:
        return node_to_bel(graph, node)

    if VARIANTS not in data and FUSION not in data:  # this is should be a simple node
        return graph.node[node][NAME]

    raise ValueError('Unexpected node data: {}'.format(data))


def _canonicalize_edge_modifications(data):
    """Returns the SUBJECT or OBJECT entry of a PyBEL edge data dictioanry as a canonicalized tuple

    :param dict data: A PyBEL edge data dictionary
    :rtype: tuple
    """
    if MODIFIER not in data:
        raise ValueError('Modifier not in data')

    result = []

    if data[MODIFIER] == ACTIVITY:
        t = (ACTIVITY, data[ACTIVITY])

        if EFFECT in data:
            t += (data[EFFECT][NAMESPACE], data[EFFECT][NAME])

        result.append(t)

    elif data[MODIFIER] == DEGRADATION:
        t = (DEGRADATION,)
        result.append(t)

    elif data[MODIFIER] == TRANSLOCATION:
        t = (
            TRANSLOCATION,
            data[EFFECT][FROM_LOC][NAMESPACE],
            data[EFFECT][FROM_LOC][NAME],
            data[EFFECT][TO_LOC][NAMESPACE],
            data[EFFECT][TO_LOC][NAME],
        )
        result.append(t)

    else:
        raise ValueError('Invalid modifier: {}'.format(data[MODIFIER]))

    if LOCATION in data:
        location_tuple = (LOCATION, data[LOCATION][NAMESPACE], data[LOCATION][NAME])
        result.append(location_tuple)

    return tuple(result)


def canonicalize_edge(data):
    """Canonicalizes the edge to a tuple based on the relation, subject modifications, and object modifications

    :param dict data: A PyBEL edge data dictionary
    :return: A 3-tuple that's specific for the edge (relation, subject, object)
    :rtype: tuple
    """
    subject = data.get(SUBJECT)
    obj = data.get(OBJECT)

    return (
        data[RELATION],
        _canonicalize_edge_modifications(subject) if subject else tuple(),
        _canonicalize_edge_modifications(obj) if obj else tuple(),
    )
