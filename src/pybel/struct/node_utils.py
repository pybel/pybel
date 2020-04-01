# -*- coding: utf-8 -*-

"""Utilities for handling nodes."""

import itertools as itt
import logging
from itertools import chain
from typing import Set, Tuple, Type, Union

from networkx import relabel_nodes

from ..constants import ANNOTATIONS, CITATION, EVIDENCE, INCREASES, RELATION
from ..dsl import BaseAbundance, BaseEntity, ListAbundance, Reaction

__all__ = [
    'flatten_list_abundance',
    'list_abundance_cartesian_expansion',
    'reaction_cartesian_expansion',
]

logger = logging.getLogger(__name__)


def flatten_list_abundance(node: ListAbundance) -> ListAbundance:
    """Flattens the complex or composite abundance."""
    return node.__class__(list(chain.from_iterable(
        (
            flatten_list_abundance(member).members
            if isinstance(member, ListAbundance) else
            [member]
        )
        for member in node.members
    )))


def list_abundance_expansion(graph) -> None:
    """Flatten list abundances."""
    mapping = {
        node: flatten_list_abundance(node)
        for node in graph
        if isinstance(node, ListAbundance)
    }
    relabel_nodes(graph, mapping, copy=False)


def list_abundance_cartesian_expansion(graph) -> None:
    """Expand all list abundances to simple subject-predicate-object networks."""
    for u, v, d in list(graph.edges(data=True)):
        if CITATION not in d:
            continue

        if isinstance(u, ListAbundance) and isinstance(v, ListAbundance):
            for u_member, v_member in itt.product(u.members, v.members):
                graph.add_qualified_edge(
                    u_member, v_member,
                    relation=d[RELATION],
                    citation=d.get(CITATION),
                    evidence=d.get(EVIDENCE),
                    annotations=d.get(ANNOTATIONS),
                )

        elif isinstance(u, ListAbundance):
            for member in u.members:
                graph.add_qualified_edge(
                    member, v,
                    relation=d[RELATION],
                    citation=d.get(CITATION),
                    evidence=d.get(EVIDENCE),
                    annotations=d.get(ANNOTATIONS),
                )

        elif isinstance(v, ListAbundance):
            for member in v.members:
                graph.add_qualified_edge(
                    u, member,
                    relation=d[RELATION],
                    citation=d.get(CITATION),
                    evidence=d.get(EVIDENCE),
                    annotations=d.get(ANNOTATIONS),
                )

    _remove_list_abundance_nodes(graph)


def _reaction_cartesian_expansion_unqualified_helper(
    graph,
    u: BaseEntity,
    v: BaseEntity,
    d: dict,
) -> None:
    """Help deal with cartesian expansion in unqualified edges."""
    if isinstance(u, Reaction) and isinstance(v, Reaction):
        enzymes = _get_catalysts_in_reaction(u) | _get_catalysts_in_reaction(v)

        for reactant, product in chain(itt.product(u.reactants, u.products),
                                       itt.product(v.reactants, v.products)):
            if reactant in enzymes or product in enzymes:
                continue

            graph.add_unqualified_edge(
                reactant, product, INCREASES
            )

        for product, reactant in itt.product(u.products, u.reactants):
            if reactant in enzymes or product in enzymes:
                continue

            graph.add_unqualified_edge(
                product, reactant, d[RELATION],
            )

    elif isinstance(u, Reaction):
        enzymes = _get_catalysts_in_reaction(u)

        for product in u.products:
            # Skip create increases edges between enzymes
            if product in enzymes:
                continue

            # Only add edge between v and reaction if the node is not part of the reaction
            # In practice skips hasReactant, hasProduct edges
            if v not in u.products and v not in u.reactants:
                graph.add_unqualified_edge(
                    product, v, INCREASES
                )
            for reactant in u.reactants:
                graph.add_unqualified_edge(
                    reactant, product, INCREASES
                )

    elif isinstance(v, Reaction):
        enzymes = _get_catalysts_in_reaction(v)

        for reactant in v.reactants:
            # Skip create increases edges between enzymes
            if reactant in enzymes:
                continue

            # Only add edge between v and reaction if the node is not part of the reaction
            # In practice skips hasReactant, hasProduct edges
            if u not in v.products and u not in v.reactants:
                graph.add_unqualified_edge(
                    u, reactant, INCREASES
                )
            for product in v.products:
                graph.add_unqualified_edge(
                    reactant, product, INCREASES
                )


def _get_catalysts_in_reaction(reaction: Reaction) -> Set[BaseAbundance]:
    """Return nodes that are both in reactants and reactions in a reaction."""
    # TODO replace with reaction.get_catalysts()
    return set(reaction.reactants).intersection(reaction.products)


def reaction_cartesian_expansion(graph, accept_unqualified_edges: bool = True) -> None:
    """Expand all reactions to simple subject-predicate-object networks."""
    for u, v, d in list(graph.edges(data=True)):
        # Deal with unqualified edges
        if CITATION not in d and accept_unqualified_edges:
            _reaction_cartesian_expansion_unqualified_helper(graph, u, v, d)
            continue

        if isinstance(u, Reaction) and isinstance(v, Reaction):
            catalysts = _get_catalysts_in_reaction(u) | _get_catalysts_in_reaction(v)

            for reactant, product in chain(itt.product(u.reactants, u.products), itt.product(v.reactants, v.products)):
                if reactant in catalysts or product in catalysts:
                    continue
                graph.add_increases(
                    reactant, product,
                    citation=d.get(CITATION),
                    evidence=d.get(EVIDENCE),
                    annotations=d.get(ANNOTATIONS),
                )

            for product, reactant in itt.product(u.products, u.reactants):
                if reactant in catalysts or product in catalysts:
                    continue

                graph.add_qualified_edge(
                    product, reactant,
                    relation=d[RELATION],
                    citation=d.get(CITATION),
                    evidence=d.get(EVIDENCE),
                    annotations=d.get(ANNOTATIONS),
                )

        elif isinstance(u, Reaction):
            catalysts = _get_catalysts_in_reaction(u)

            for product in u.products:
                # Skip create increases edges between enzymes
                if product in catalysts:
                    continue

                # Only add edge between v and reaction if the node is not part of the reaction
                # In practice skips hasReactant, hasProduct edges
                if v not in u.products and v not in u.reactants:
                    graph.add_increases(
                        product, v,
                        citation=d.get(CITATION),
                        evidence=d.get(EVIDENCE),
                        annotations=d.get(ANNOTATIONS),
                    )

                for reactant in u.reactants:
                    graph.add_increases(
                        reactant, product,
                        citation=d.get(CITATION),
                        evidence=d.get(EVIDENCE),
                        annotations=d.get(ANNOTATIONS),
                    )

        elif isinstance(v, Reaction):
            catalysts = _get_catalysts_in_reaction(v)

            for reactant in v.reactants:
                # Skip create increases edges between enzymes
                if reactant in catalysts:
                    continue

                # Only add edge between v and reaction if the node is not part of the reaction
                # In practice skips hasReactant, hasProduct edges
                if u not in v.products and u not in v.reactants:
                    graph.add_increases(
                        u, reactant,
                        citation=d.get(CITATION),
                        evidence=d.get(EVIDENCE),
                        annotations=d.get(ANNOTATIONS),
                    )
                for product in v.products:
                    graph.add_increases(
                        reactant, product,
                        citation=d.get(CITATION),
                        evidence=d.get(EVIDENCE),
                        annotations=d.get(ANNOTATIONS),
                    )

    _remove_reaction_nodes(graph)


def remove_reified_nodes(graph) -> None:
    """Remove complex nodes."""
    _remove_list_abundance_nodes(graph)
    _remove_reaction_nodes(graph)


def _remove_list_abundance_nodes(graph):
    _remove_typed_nodes(graph, ListAbundance)


def _remove_reaction_nodes(graph):
    _remove_typed_nodes(graph, Reaction)


def _remove_typed_nodes(
    graph,
    cls: Union[Type[BaseEntity], Tuple[Type[BaseEntity], ...]],
) -> None:
    graph.remove_nodes_from({
        node
        for node in graph
        if isinstance(node, cls)
    })
