# -*- coding: utf-8 -*-

"""This module contains output functions to BEL scripts."""

from __future__ import print_function

import logging

import itertools as itt

from .constants import (
    ACTIVITY, ANNOTATIONS, BEL_DEFAULT_NAMESPACE, CITATION, CITATION_REFERENCE, CITATION_TYPE, COMPLEX, COMPOSITE,
    DEGRADATION, EFFECT, EVIDENCE, FROM_LOC, FUNCTION, FUSION, GOCC_KEYWORD, GOCC_LATEST, IDENTIFIER, LOCATION,
    MODIFIER, NAME, NAMESPACE, OBJECT, PYBEL_AUTOEVIDENCE, REACTION, RELATION, SUBJECT, TO_LOC, TRANSLOCATION,
    UNQUALIFIED_EDGES, VARIANTS,
)
from .dsl import BaseEntity
from .resources.document import make_knowledge_header
from .utils import ensure_quotes

__all__ = [
    'to_bel_lines',
    'to_bel',
    'to_bel_path',
    'edge_to_bel',
]

log = logging.getLogger(__name__)


def postpend_location(bel_string, location_model):
    """Rip off the closing parentheses and adds canonicalized modification.

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


def _decanonicalize_edge_node(node, edge_data, node_position):
    """Canonicalize a node with its modifiers stored in the given edge to a BEL string.

    :param BaseEntity node: A PyBEL node data dictionary
    :param dict edge_data: A PyBEL edge data dictionary
    :param node_position: Either :data:`pybel.constants.SUBJECT` or :data:`pybel.constants.OBJECT`
    :rtype: str
    """
    node_str = node.as_bel()

    if node_position not in edge_data:
        return node_str

    node_edge_data = edge_data[node_position]

    if LOCATION in node_edge_data:
        node_str = postpend_location(node_str, node_edge_data[LOCATION])

    modifier = node_edge_data.get(MODIFIER)

    if modifier is None:
        return node_str

    if DEGRADATION == modifier:
        return "deg({})".format(node_str)

    effect = node_edge_data.get(EFFECT)

    if ACTIVITY == modifier:
        if effect is None:
            return "act({})".format(node_str)

        if effect[NAMESPACE] == BEL_DEFAULT_NAMESPACE:
            return "act({}, ma({}))".format(node_str, effect[NAME])

        return "act({}, ma({}:{}))".format(node_str, effect[NAMESPACE], ensure_quotes(effect[NAME]))

    if TRANSLOCATION == modifier:
        if effect is None:
            return 'tloc({})'.format(node_str)

        to_loc_data = effect[TO_LOC]
        from_loc_data = effect[FROM_LOC]

        from_loc = "fromLoc({}:{})".format(
            from_loc_data[NAMESPACE],
            ensure_quotes(from_loc_data[NAME])
        )

        to_loc = "toLoc({}:{})".format(
            to_loc_data[NAMESPACE],
            ensure_quotes(to_loc_data[NAME])
        )

        return "tloc({}, {}, {})".format(node_str, from_loc, to_loc)

    raise ValueError('invalid modifier: {}'.format(modifier))


def edge_to_bel(u, v, data, sep=None):
    """Take two nodes and gives back a BEL string representing the statement.

    :param BaseEntity u: The edge's source's PyBEL node data dictionary
    :param BaseEntity v: The edge's target's PyBEL node data dictionary
    :param dict data: The edge's data dictionary
    :param str sep: The separator between the source, relation, and target. Defaults to ' '
    :return: The canonical BEL for this edge
    :rtype: str
    """
    sep = sep or ' '
    u_str = _decanonicalize_edge_node(u, data, node_position=SUBJECT)
    v_str = _decanonicalize_edge_node(v, data, node_position=OBJECT)

    return sep.join((u_str, data[RELATION], v_str))


def _sort_qualified_edges_helper(edge_tuple):
    u, v, k, d = edge_tuple
    return (
        d[CITATION][CITATION_TYPE],
        d[CITATION][CITATION_REFERENCE],
        d[EVIDENCE],
    )


def sort_qualified_edges(graph):
    """Return the qualified edges, sorted first by citation, then by evidence, then by annotations.

    :param BELGraph graph: A BEL graph
    :rtype: tuple[tuple,tuple,int,dict]
    """
    qualified_edges = (
        (u, v, k, d)
        for u, v, k, d in graph.edges(keys=True, data=True)
        if graph.has_edge_citation(u, v, k) and graph.has_edge_evidence(u, v, k)
    )
    return sorted(qualified_edges, key=_sort_qualified_edges_helper)


def _citation_sort_key(t):
    """Make a confusing 4 tuple sortable by citation.

    :param tuple t: A 4-tuple of source node, target node, key, and data
    :rtype: tuple[str,str]
    """
    return '"{}", "{}"'.format(t[3][CITATION][CITATION_TYPE], t[3][CITATION][CITATION_REFERENCE])


def _evidence_sort_key(t):
    """Make a confusing 4 tuple sortable by citation.

    :param tuple t: A 4-tuple of source node, target node, key, and data
    :rtype: str
    """
    return t[3][EVIDENCE]


def _set_annotation_to_str(annotation_data, key):
    """Return a set annotation string.

    :param dict[str,dict[str,bool] annotation_data:
    :param key:
    :return:
    """
    value = annotation_data[key]

    if len(value) == 1:
        return 'SET {} = "{}"'.format(key, list(value)[0])

    x = ('"{}"'.format(v) for v in sorted(value))

    return 'SET {} = {{{}}}'.format(key, ', '.join(x))


def _unset_annotation_to_str(keys):
    """Return an unset annotation string.

    :rtype: str
    """
    if len(keys) == 1:
        return 'UNSET {}'.format(list(keys)[0])

    return 'UNSET {{{}}}'.format(', '.join('{}'.format(key) for key in keys))


def _to_bel_lines_header(graph):
    """Iterate the lines of a BEL graph's corresponding BEL script's header.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: iter[str]
    """
    if GOCC_KEYWORD not in graph.namespace_url:
        graph.namespace_url[GOCC_KEYWORD] = GOCC_LATEST

    return make_knowledge_header(
        namespace_url=graph.namespace_url,
        namespace_patterns=graph.namespace_pattern,
        annotation_url=graph.annotation_url,
        annotation_patterns=graph.annotation_pattern,
        annotation_list=graph.annotation_list,
        **graph.document
    )


def group_citation_edges(edges):
    """Return an iterator over pairs of citation values and their corresponding edge iterators.

    :param iter[tuple,tuple,int,dict] edges: An iterator over the 4-tuples of edges
    :rtype: tuple[str,tuple[tuple,tuple,int,dict]]
    """
    return itt.groupby(edges, key=_citation_sort_key)


def group_evidence_edges(edges):
    """Return an iterator over pairs of evidence values and their corresponding edge iterators.

    :param iter[tuple,tuple,int,dict] edges: An iterator over the 4-tuples of edges
    :rtype: tuple[str,tuple[tuple,tuple,int,dict]]
    """
    return itt.groupby(edges, key=_evidence_sort_key)


def _to_bel_lines_body(graph):
    """Iterate the lines of a BEL graph's corresponding BEL script's body.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: iter[str]
    """
    qualified_edges = sort_qualified_edges(graph)

    for citation, citation_edges in group_citation_edges(qualified_edges):
        yield '#' * 80
        yield 'SET Citation = {{{}}}'.format(citation)

        for evidence, evidence_edges in group_evidence_edges(citation_edges):
            yield 'SET SupportingText = "{}"'.format(evidence)

            for u, v, _, data in evidence_edges:
                annotations_data = data.get(ANNOTATIONS)

                keys = sorted(annotations_data) if annotations_data is not None else tuple()
                for key in keys:
                    yield _set_annotation_to_str(annotations_data, key)

                yield graph.edge_to_bel(u, v, data)

                if keys:
                    yield _unset_annotation_to_str(keys)

            yield 'UNSET SupportingText'
        yield 'UNSET Citation'


def _to_bel_lines_footer(graph):
    """Iterate the lines of a BEL graph's corresponding BEL script's footer.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: iter[str]
    """
    unqualified_edges_to_serialize = [
        (u, v, d)
        for u, v, d in graph.edges(data=True)
        if d[RELATION] in UNQUALIFIED_EDGES and EVIDENCE not in d
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
            yield '{} {} {}'.format(u.as_bel(), data[RELATION], v.as_bel())

        for node in isolated_nodes_to_serialize:
            yield node.as_bel()

        yield 'UNSET SupportingText'
        yield 'UNSET Citation'


def to_bel_lines(graph):
    """Return an iterable over the lines of the BEL graph as a canonical BEL Script (.bel).

    :param pybel.BELGraph graph: the BEL Graph to output as a BEL Script
    :return: An iterable over the lines of the representative BEL script
    :rtype: iter[str]
    """
    return itt.chain(
        _to_bel_lines_header(graph),
        _to_bel_lines_body(graph),
        _to_bel_lines_footer(graph)
    )


def to_bel(graph, file=None):
    """Output the BEL graph as canonical BEL to the given file/file-like/stream.

    :param BELGraph graph: the BEL Graph to output as a BEL Script
    :param file file: A writable file-like object. If None, defaults to standard out.
    """
    for line in to_bel_lines(graph):
        print(line, file=file)


def to_bel_path(graph, path, mode='w', **kwargs):
    """Write the BEL graph as a canonical BEL Script to the given path.

    :param BELGraph graph: the BEL Graph to output as a BEL Script
    :param str path: A file path
    :param str mode: The file opening mode. Defaults to 'w'
    """
    with open(path, mode=mode, **kwargs) as bel_file:
        to_bel(graph, bel_file)


def calculate_canonical_name(data):
    """Calculate the canonical name for a given node.

    If it is a simple node, uses the already given name. Otherwise, it uses the BEL string.

    :type data: BaseEntity
    :return: Canonical node name
    :rtype: str
    """
    if data[FUNCTION] == COMPLEX and NAMESPACE in data:
        return data[NAME]

    if VARIANTS in data:
        return data.as_bel()

    if FUSION in data:
        return data.as_bel()

    if data[FUNCTION] in {REACTION, COMPOSITE, COMPLEX}:
        return data.as_bel()

    if VARIANTS not in data and FUSION not in data:  # this is should be a simple node
        if IDENTIFIER in data and NAME in data:
            return '{namespace}:{identifier} ({name})'.format(**data)

        if IDENTIFIER in data:
            return '{namespace}:{identifier}'.format(namespace=data[NAMESPACE], identifier=data[IDENTIFIER])

        return data[NAME]

    raise ValueError('Unexpected node data: {}'.format(data))
