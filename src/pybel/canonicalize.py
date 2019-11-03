# -*- coding: utf-8 -*-

"""This module contains output functions to BEL scripts."""

import itertools as itt
import logging
import time
from typing import Iterable, List, Mapping, Optional, TextIO, Tuple, Union

from networkx.utils import open_file

import bel_resources.constants
from bel_resources import make_knowledge_header
from .constants import (
    ACTIVITY, ANNOTATIONS, BEL_DEFAULT_NAMESPACE, CELL_SURFACE, CITATION, CITATION_DB, CITATION_IDENTIFIER, DEGRADATION,
    EFFECT, EVIDENCE, EXTRACELLULAR, FROM_LOC, INTRACELLULAR, LOCATION, MODIFIER, NAME, NAMESPACE, OBJECT,
    PYBEL_AUTOEVIDENCE, RELATION, SUBJECT, TO_LOC, TRANSLOCATION, UNQUALIFIED_EDGES, VARIANTS,
)
from .dsl import BaseAbundance, BaseEntity, FusionBase, ListAbundance, Reaction
from .typing import EdgeData
from .utils import ensure_quotes
from .version import VERSION

__all__ = [
    'to_bel_script',
    'to_bel_script_lines',
    'edge_to_bel',
    'calculate_canonical_name',
]

logger = logging.getLogger(__name__)

EdgeTuple = Tuple[BaseEntity, BaseEntity, str, EdgeData]


@open_file(1, mode='w')
def to_bel_script(graph, path: Union[str, TextIO]) -> None:
    """Write the BELGraph as a canonical BEL script.

    :param BELGraph graph: the BEL Graph to output as a BEL Script
    :param path: A path or file-like.
    """
    for line in to_bel_script_lines(graph):
        print(line, file=path)


def to_bel_script_lines(graph) -> Iterable[str]:
    """Iterate over the lines of the BEL graph as a canonical BEL script.

    :param pybel.BELGraph graph: A BEL Graph
    """
    return itt.chain(
        _to_bel_lines_header(graph),
        _to_bel_lines_body(graph),
        _to_bel_lines_footer(graph),
    )


def postpend_location(bel_string: str, location_model) -> str:
    """Rip off the closing parentheses and adds canonicalized modification.

    I did this because writing a whole new parsing model for the data would be sad and difficult

    :param bel_string: BEL string representing node
    :param dict location_model: A dictionary containing keys :code:`pybel.constants.TO_LOC` and
                                :code:`pybel.constants.FROM_LOC`
    :return: A part of a BEL string representing the location
    """
    if not all(k in location_model for k in {NAMESPACE, NAME}):
        raise ValueError('Location model missing namespace and/or name keys: {}'.format(location_model))

    return "{}, loc({}:{}))".format(
        bel_string[:-1],
        location_model[NAMESPACE],
        ensure_quotes(location_model[NAME]),
    )


def _decanonicalize_edge_node(node: BaseEntity, edge_data: EdgeData, node_position: str) -> str:
    """Canonicalize a node with its modifiers stored in the given edge to a BEL string.

    :param node: A PyBEL node data dictionary
    :param edge_data: A PyBEL edge data dictionary
    :param node_position: Either :data:`pybel.constants.SUBJECT` or :data:`pybel.constants.OBJECT`
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

        if from_loc_data[NAMESPACE] == BEL_DEFAULT_NAMESPACE and from_loc_data[NAME] == INTRACELLULAR:
            if to_loc_data[NAMESPACE] == BEL_DEFAULT_NAMESPACE and to_loc_data[NAME] == EXTRACELLULAR:
                return 'sec({})'.format(node_str)
            if to_loc_data[NAMESPACE] == BEL_DEFAULT_NAMESPACE and to_loc_data[NAME] == CELL_SURFACE:
                return 'surf({})'.format(node_str)

        from_loc = _get_tloc_terminal('fromLoc', from_loc_data)
        to_loc = _get_tloc_terminal('toLoc', to_loc_data)

        return "tloc({}, {}, {})".format(node_str, from_loc, to_loc)

    raise ValueError('invalid modifier: {}'.format(modifier))


def _get_tloc_terminal(side, data):
    return "{}({}:{})".format(
        side,
        data[NAMESPACE],
        ensure_quotes(data[NAME]),
    )


def edge_to_tuple(u: BaseEntity, v: BaseEntity, data: EdgeData) -> Tuple[str, str, str]:
    """Take two nodes and gives back a BEL string representing the statement.

    :param u: The edge's source's PyBEL node data dictionary
    :param v: The edge's target's PyBEL node data dictionary
    :param data: The edge's data dictionary
    """
    u_str = _decanonicalize_edge_node(u, data, node_position=SUBJECT)
    v_str = _decanonicalize_edge_node(v, data, node_position=OBJECT)
    return u_str, data[RELATION], v_str


def edge_to_bel(u: BaseEntity, v: BaseEntity, data: EdgeData, sep: Optional[str] = None) -> str:
    """Take two nodes and gives back a BEL string representing the statement.

    :param u: The edge's source's PyBEL node data dictionary
    :param v: The edge's target's PyBEL node data dictionary
    :param data: The edge's data dictionary
    :param sep: The separator between the source, relation, and target. Defaults to ' '
    """
    sep = sep or ' '
    return sep.join(edge_to_tuple(u=u, v=v, data=data))


def _sort_qualified_edges_helper(t: EdgeTuple) -> Tuple[str, str, str]:
    return (
        t[3][CITATION][CITATION_DB],
        t[3][CITATION][CITATION_IDENTIFIER],
        t[3][EVIDENCE],
    )


def sort_qualified_edges(graph) -> Iterable[EdgeTuple]:
    """Return the qualified edges, sorted first by citation, then by evidence, then by annotations.

    :param BELGraph graph: A BEL graph
    """
    qualified_edges = (
        (u, v, k, d)
        for u, v, k, d in graph.edges(keys=True, data=True)
        if graph.has_edge_citation(u, v, k) and graph.has_edge_evidence(u, v, k)
    )
    return sorted(qualified_edges, key=_sort_qualified_edges_helper)


def _citation_sort_key(t: EdgeTuple) -> str:
    """Make a confusing 4 tuple sortable by citation."""
    return '"{}", "{}"'.format(t[3][CITATION][CITATION_DB], t[3][CITATION][CITATION_IDENTIFIER])


def _evidence_sort_key(t: EdgeTuple) -> str:
    """Make a confusing 4 tuple sortable by citation."""
    return t[3][EVIDENCE]


def _set_annotation_to_str(annotation_data: Mapping[str, Mapping[str, bool]], key: str) -> str:
    """Return a set annotation string."""
    value = annotation_data[key]

    if len(value) == 1:
        return 'SET {} = "{}"'.format(key, list(value)[0])

    x = ('"{}"'.format(v) for v in sorted(value))

    return 'SET {} = {{{}}}'.format(key, ', '.join(x))


def _unset_annotation_to_str(keys: List[str]) -> str:
    """Return an unset annotation string."""
    if len(keys) == 1:
        return 'UNSET {}'.format(list(keys)[0])

    return 'UNSET {{{}}}'.format(', '.join('{}'.format(key) for key in keys))


def _to_bel_lines_header(graph) -> Iterable[str]:
    """Iterate the lines of a BEL graph's corresponding BEL script's header.

    :param pybel.BELGraph graph: A BEL graph
    """
    yield '# This document was created by PyBEL v{} and bel-resources v{} on {}\n'.format(
        VERSION, bel_resources.constants.VERSION, time.asctime(),
    )
    yield from make_knowledge_header(
        namespace_url=graph.namespace_url,
        namespace_patterns=graph.namespace_pattern,
        annotation_url=graph.annotation_url,
        annotation_patterns=graph.annotation_pattern,
        annotation_list=graph.annotation_list,
        **graph.document,
    )


def group_citation_edges(edges: Iterable[EdgeTuple]) -> Iterable[Tuple[str, Iterable[EdgeTuple]]]:
    """Return an iterator over pairs of citation values and their corresponding edge iterators."""
    return itt.groupby(edges, key=_citation_sort_key)


def group_evidence_edges(edges: Iterable[EdgeTuple]) -> Iterable[Tuple[str, Iterable[EdgeTuple]]]:
    """Return an iterator over pairs of evidence values and their corresponding edge iterators."""
    return itt.groupby(edges, key=_evidence_sort_key)


def _to_bel_lines_body(graph) -> Iterable[str]:
    """Iterate the lines of a BEL graph's corresponding BEL script's body.

    :param pybel.BELGraph graph: A BEL graph
    """
    qualified_edges = sort_qualified_edges(graph)

    for citation, citation_edges in group_citation_edges(qualified_edges):
        yield 'SET Citation = {{{}}}\n'.format(citation)

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
        yield 'UNSET Citation\n'
        yield '#' * 80


def _to_bel_lines_footer(graph) -> Iterable[str]:
    """Iterate the lines of a BEL graph's corresponding BEL script's footer.

    :param pybel.BELGraph graph: A BEL graph
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


def calculate_canonical_name(node: BaseEntity, use_curie: bool = False) -> str:
    """Calculate the canonical name for a given node.

    If it is a simple node, uses the already given name. Otherwise, it uses the BEL string.
    """
    if isinstance(node, (Reaction, ListAbundance, FusionBase)):
        return node.as_bel(use_identifiers=True)

    elif isinstance(node, BaseAbundance):
        if VARIANTS in node:
            return node.as_bel(use_identifiers=True)
        elif use_curie:
            return node.curie
        else:
            return node.obo

    else:
        raise TypeError('Unhandled node: {}'.format(node))
