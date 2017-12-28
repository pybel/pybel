# -*- coding: utf-8 -*-

"""This module contains output functions to BEL scripts."""

from __future__ import print_function

import itertools as itt
import logging
import sys

from .constants import *
from .parser.language import rev_abundance_labels
from .resources.document import make_knowledge_header
from .struct.filters import filter_qualified_edges
from .utils import ensure_quotes, flatten_citation, hash_edge

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


def node_data_to_bel(data):
    """Returns a node data dictionary as a BEL string

    :param dict data: A PyBEL node data dictionary
    :rtype: str
    """
    if data[FUNCTION] == REACTION:
        return 'rxn(reactants({}), products({}))'.format(
            ', '.join(node_data_to_bel(reactant_data) for reactant_data in data[REACTANTS]),
            ', '.join(node_data_to_bel(product_data) for product_data in data[PRODUCTS])
        )

    if data[FUNCTION] in {COMPOSITE, COMPLEX} and NAMESPACE not in data:
        return '{}({})'.format(
            rev_abundance_labels[data[FUNCTION]],
            ', '.join(node_data_to_bel(member_data) for member_data in data[MEMBERS])
        )

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

    raise ValueError('Unknown values in node data: {}'.format(data))


def node_to_bel(graph, node):
    """Returns a node from a graph as a BEL string

    :param BELGraph graph: A BEL Graph
    :param tuple node: a node from the BEL graph
    :rtype: str
    """
    return node_data_to_bel(graph.node[node])


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


def edge_to_bel(graph, u, v, data, sep=' '):
    """Takes two nodes and gives back a BEL string representing the statement

    :param BELGraph graph: A BEL graph
    :param tuple u: The edge's source's PyBEL node tuple
    :param tuple v: The edge's target's PyBEL node tuple
    :param dict data: The edge's data dictionary
    :param str sep: The separator between the source, relation, and target
    :return: The canonical BEL for this edge
    :rtype: str
    """
    u_str = _decanonicalize_edge_node(graph, u, data, node_position=SUBJECT)
    v_str = _decanonicalize_edge_node(graph, v, data, node_position=OBJECT)

    return sep.join((u_str, data[RELATION], v_str))


def _sort_qualified_edges_helper(edge_tuple):
    u, v, k, d = edge_tuple
    return (
        d[CITATION][CITATION_TYPE],
        d[CITATION][CITATION_REFERENCE],
        d[EVIDENCE],
        hash_edge(u, v, k, d)
    )


def sort_qualified_edges(graph):
    """Returns the qualified edges, sorted first by citation, then by evidence, then by annotations

    :param BELGraph graph: A BEL graph
    :rtype: tuple[tuple,tuple,dict]
    """
    qualified_edges_iter = filter_qualified_edges(graph)
    qualified_edges = sorted(qualified_edges_iter, key=_sort_qualified_edges_helper)
    return qualified_edges


def to_bel_lines(graph):
    """Returns an iterable over the lines of the BEL graph as a canonical BEL Script (.bel)

    :param pybel.BELGraph graph: the BEL Graph to output as a BEL Script
    :return: An iterable over the lines of the representative BEL script
    :rtype: iter[str]
    """
    if GOCC_KEYWORD not in graph.namespace_url:
        graph.namespace_url[GOCC_KEYWORD] = GOCC_LATEST

    header_lines = make_knowledge_header(
        namespace_url=graph.namespace_url,
        namespace_owl=graph.namespace_owl,
        namespace_patterns=graph.namespace_pattern,
        annotation_url=graph.annotation_url,
        annotation_owl=graph.annotation_owl,
        annotation_patterns=graph.annotation_pattern,
        annotation_list=graph.annotation_list,
        **graph.document
    )

    for line in header_lines:
        yield line

    qualified_edges = sort_qualified_edges(graph)

    for citation, citation_edges in itt.groupby(qualified_edges, key=lambda t: flatten_citation(t[3][CITATION])):
        yield 'SET Citation = {{{}}}'.format(citation)

        for evidence, evidence_edges in itt.groupby(citation_edges, key=lambda u_v_k_d: u_v_k_d[3][EVIDENCE]):
            yield 'SET SupportingText = "{}"'.format(evidence)

            for u, v, _, data in evidence_edges:
                keys = sorted(data[ANNOTATIONS]) if ANNOTATIONS in data else tuple()
                for key in keys:
                    yield 'SET {} = "{}"'.format(key, data[ANNOTATIONS][key])
                yield edge_to_bel(graph, u, v, data=data)
                if keys:
                    yield 'UNSET {{{}}}'.format(', '.join('{}'.format(key) for key in keys))
            yield 'UNSET SupportingText'
        yield 'UNSET Citation\n'

    unqualified_edges_to_serialize = [
        (u, v, d)
        for u, v, d in graph.edges_iter(data=True)
        if d[RELATION] in unqualified_edge_code and EVIDENCE not in d
    ]

    isolated_nodes_to_serialize = [
        node
        for node in graph
        if not graph.pred[node] and not graph.succ[node]
    ]

    if unqualified_edges_to_serialize or isolated_nodes_to_serialize:
        yield '###############################################\n'
        yield 'SET Citation = {"PubMed","Added by PyBEL","29048466"}'
        yield 'SET SupportingText = "{}"'.format(PYBEL_AUTOEVIDENCE)

        for u, v, data in unqualified_edges_to_serialize:
            yield '{} {} {}'.format(node_to_bel(graph, u), data[RELATION], node_to_bel(graph, v))

        for node in isolated_nodes_to_serialize:
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
        return node_data_to_bel(data)

    if FUSION in data:
        return node_data_to_bel(data)

    if data[FUNCTION] in {REACTION, COMPOSITE, COMPLEX}:
        return node_data_to_bel(data)

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
