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
from .utils import ensure_quotes, flatten_citation, sort_edges, get_version

__all__ = [
    'to_bel_lines',
    'to_bel',
    'to_bel_path'
]

log = logging.getLogger(__name__)


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


def postpend_location(bel_string, location_model):
    """Rips off the closing parentheses and adds canonicalized modification.

    I did this because writing a whole new parsing model for the data would be sad and difficult

    :param bel_string: BEL string representing node
    :type bel_string: str
    :param location_model: A dictionary containing keys :code:`pybel.constants.TO_LOC` and
                            :code:`pybel.constants.FROM_LOC`
    :type location_model: dict
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


def decanonicalize_variant(tokens):
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
            res = 'frag(?'
        else:
            res = 'frag({}_{}'.format(tokens[FRAGMENT_START], tokens[FRAGMENT_STOP])

        if FRAGMENT_DESCRIPTION in tokens:
            res += ', {}'.format(tokens[FRAGMENT_DESCRIPTION])

        return res + ')'


def decanonicalize_fusion_range(tokens):
    if FUSION_REFERENCE in tokens:
        return '{}.{}_{}'.format(tokens[FUSION_REFERENCE], tokens[FUSION_START], tokens[FUSION_STOP])
    return '?'


def decanonicalize_node(graph, node):
    """Returns a node from a graph as a BEL string

    :param graph: A BEL Graph
    :type graph: BELGraph
    :param node: a node from the BEL graph
    :type node: tuple
    """
    data = graph.node[node]

    if data[FUNCTION] == REACTION:
        reactants = get_targets_by_relation(graph, node, HAS_REACTANT)
        reactants_canon = sorted(map(lambda n: decanonicalize_node(graph, n), reactants))
        products = get_targets_by_relation(graph, node, HAS_PRODUCT)
        products_canon = sorted(map(lambda n: decanonicalize_node(graph, n), products))
        return 'rxn(reactants({}), products({}))'.format(', '.join(reactants_canon), ', '.join(products_canon))

    if data[FUNCTION] in {COMPOSITE, COMPLEX} and NAMESPACE not in data:
        members = get_targets_by_relation(graph, node, HAS_COMPONENT)
        members_canon = sorted(map(lambda n: decanonicalize_node(graph, n), members))
        return '{}({})'.format(rev_abundance_labels[data[FUNCTION]], ', '.join(members_canon))

    if VARIANTS in data:
        variants_canon = sorted(map(decanonicalize_variant, data[VARIANTS]))
        return "{}({}:{}, {})".format(rev_abundance_labels[data[FUNCTION]],
                                      data[NAMESPACE],
                                      ensure_quotes(data[NAME]),
                                      ', '.join(variants_canon))

    if FUSION in data:
        return "{}(fus({}:{}, {}, {}:{}, {}))".format(
            rev_abundance_labels[data[FUNCTION]],
            data[FUSION][PARTNER_5P][NAMESPACE],
            data[FUSION][PARTNER_5P][NAME],
            decanonicalize_fusion_range(data[FUSION][RANGE_5P]),
            data[FUSION][PARTNER_3P][NAMESPACE],
            data[FUSION][PARTNER_3P][NAME],
            decanonicalize_fusion_range(data[FUSION][RANGE_3P])
        )

    if data[FUNCTION] in {GENE, RNA, MIRNA, PROTEIN, ABUNDANCE, COMPLEX, PATHOLOGY, BIOPROCESS}:
        return "{}({}:{})".format(rev_abundance_labels[data[FUNCTION]],
                                  data[NAMESPACE],
                                  ensure_quotes(data[NAME]))

    raise ValueError('Unknown node data: {} {}'.format(node, data))


def decanonicalize_edge_node(g, node, edge_data, node_position):
    node_str = decanonicalize_node(g, node)

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

        from_loc = "fromLoc({}:{})".format(node_edge_data[EFFECT][FROM_LOC][NAMESPACE],
                                           ensure_quotes(node_edge_data[EFFECT][FROM_LOC][NAME]))

        to_loc = "toLoc({}:{})".format(node_edge_data[EFFECT][TO_LOC][NAMESPACE],
                                       ensure_quotes(node_edge_data[EFFECT][TO_LOC][NAME]))

        node_str = "tloc({}, {}, {})".format(node_str, from_loc, to_loc)

    return node_str


def decanonicalize_edge(g, u, v, k):
    """Takes two nodes and gives back a BEL string representing the statement

    :param BELGraph g: A BEL graph
    :param tuple u: The edge's source node
    :param tuple v: The edge's target node
    :param int k: The edge's key
    :return: The canonical BEL for this edge
    :rtype: str
    """

    ed = g.edge[u][v][k]

    u_str = decanonicalize_edge_node(g, u, ed, node_position=SUBJECT)
    v_str = decanonicalize_edge_node(g, v, ed, node_position=OBJECT)

    return "{} {} {}".format(u_str, ed[RELATION], v_str)


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

    for namespace, url in sorted(graph.namespace_url.items(), key=itemgetter(0)):
        yield 'DEFINE NAMESPACE {} AS URL "{}"'.format(namespace, url)

    for namespace, url in sorted(graph.namespace_owl.items(), key=itemgetter(0)):
        yield 'DEFINE NAMESPACE {} AS OWL "{}"'.format(namespace, url)

    for namespace, pattern in sorted(graph.namespace_pattern.items(), key=itemgetter(0)):
        yield 'DEFINE NAMESPACE {} AS PATTERN "{}"'.format(namespace, pattern)

    yield '###############################################\n'

    for annotation, url in sorted(graph.annotation_url.items(), key=itemgetter(0)):
        yield 'DEFINE ANNOTATION {} AS URL "{}"'.format(annotation, url)

    for annotation, url in sorted(graph.annotation_owl.items(), key=itemgetter(0)):
        yield 'DEFINE ANNOTATION {} AS OWL "{}"'.format(annotation, url)

    for annotation, pattern in sorted(graph.annotation_pattern.items(), key=itemgetter(0)):
        yield 'DEFINE ANNOTATION {} AS PATTERN "{}"'.format(annotation, pattern)

    for annotation, values in sorted(graph.annotation_list.items(), key=itemgetter(0)):
        yield 'DEFINE ANNOTATION {} AS LIST {{{}}}'.format(annotation, ', '.join('"{}"'.format(e) for e in values))

    yield '###############################################\n'

    # sort by citation, then supporting text
    qualified_edges_iter = filter_provenance_edges(graph)
    qualified_edges = sorted(qualified_edges_iter, key=lambda u_v_k_d: sort_edges(u_v_k_d[3]))

    for citation, citation_edges in itt.groupby(qualified_edges, key=lambda t: flatten_citation(t[3][CITATION])):
        yield 'SET Citation = {{{}}}'.format(citation)

        for evidence, evidence_edges in itt.groupby(citation_edges, key=lambda u_v_k_d: u_v_k_d[3][EVIDENCE]):
            yield 'SET SupportingText = "{}"'.format(evidence)

            for u, v, k, d in evidence_edges:
                dkeys = sorted(d[ANNOTATIONS])
                for dk in dkeys:
                    yield 'SET {} = "{}"'.format(dk, d[ANNOTATIONS][dk])
                yield decanonicalize_edge(graph, u, v, k)
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

        yield '{} {} {}'.format(decanonicalize_node(graph, u), d[RELATION], decanonicalize_node(graph, v))

    for node in graph.nodes_iter():
        if not graph.pred[node] and not graph.succ[node]:
            yield decanonicalize_node(graph, node)

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
    :param tuple node: A BEL node
    :return: Canonical node name
    :rtype: str
    """
    data = graph.node[node]

    if data[FUNCTION] == COMPLEX and NAMESPACE in data:
        return graph.node[node][NAME]

    if VARIANTS in data:
        return decanonicalize_node(graph, node)

    if FUSION in data:
        return decanonicalize_node(graph, node)

    if data[FUNCTION] in {REACTION, COMPOSITE, COMPLEX}:
        return decanonicalize_node(graph, node)

    if VARIANTS not in data and FUSION not in data:  # this is should be a simple node
        return graph.node[node][NAME]

    raise ValueError('Unexpected node data: {}'.format(data))
