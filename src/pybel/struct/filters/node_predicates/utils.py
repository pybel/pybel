# -*- coding: utf-8 -*-

"""Pre-defined predicates for nodes."""

from functools import wraps
from typing import Callable, Iterable

from ..typing import NodePredicate, NodePredicates
from ...graph import BELGraph
from ....dsl import BaseEntity

__all__ = [
    'node_predicate',
    'invert_node_predicate',
    'concatenate_node_predicates',
    'true_node_predicate',
    'false_node_predicate',
]


def node_predicate(f: Callable[[BaseEntity], bool]) -> NodePredicate:  # noqa: D202
    """Tag a node predicate that takes a dictionary to also accept a pair of (BELGraph, node).

    Apply this as a decorator to a function that takes a single argument, a PyBEL node, to make
    sure that it can also accept a pair of arguments, a BELGraph and a PyBEL node as well.
    """

    @wraps(f)
    def wrapped(*args):
        x = args[0]

        if isinstance(x, BELGraph):
            return f(args[1], *args[2:])
        elif isinstance(x, BaseEntity):
            return f(*args)
        else:
            raise TypeError

    return wrapped


def invert_node_predicate(f: NodePredicate) -> NodePredicate:  # noqa: D202
    """Build a node predicate that is the inverse of the given node predicate."""

    def inverse_predicate(graph: BELGraph, node: BaseEntity) -> bool:
        """Return the inverse of the enclosed node predicate applied to the graph and node."""
        return not f(graph, node)

    return inverse_predicate


def concatenate_node_predicates(node_predicates: NodePredicates) -> NodePredicate:
    """Concatenate multiple node predicates to a new predicate that requires all predicates to be met.

    Example usage:

    >>> from pybel import BELGraph
    >>> from pybel.dsl import Protein
    >>> from pybel.struct.filters import not_gene, not_rna
    >>> app_protein = Protein(name='APP', namespace='hgnc', identifier='620')
    >>> app_rna = app_protein.get_rna()
    >>> app_gene = app_rna.get_gene()
    >>> graph = BELGraph()
    >>> _ = graph.add_transcription(app_gene, app_rna)
    >>> _ = graph.add_translation(app_rna, app_protein)
    >>> node_predicate = concatenate_node_predicates([not_rna, not_gene])
    >>> assert node_predicate(graph, app_protein)
    >>> assert not node_predicate(graph, app_rna)
    >>> assert not node_predicate(graph, app_gene)
    """
    # If a predicate outside a list is given, just return it
    if not isinstance(node_predicates, Iterable):
        return node_predicates

    node_predicates = tuple(node_predicates)

    # If only one predicate is given, don't bother wrapping it
    if 1 == len(node_predicates):
        return node_predicates[0]

    def concatenated_node_predicate(graph: BELGraph, node: BaseEntity) -> bool:
        """Pass only for a nodes that pass all enclosed predicates."""
        return all(
            node_predicate(graph, node)
            for node_predicate in node_predicates
        )

    return concatenated_node_predicate


@node_predicate
def true_node_predicate(_: BaseEntity) -> bool:
    """Return true for all nodes.

    Given BEL graph :code:`graph`, applying :func:`true_predicate` with a predicate on the nodes iterable
    as in :code:`filter(keep_node_permissive, graph)` will result in the same iterable as iterating directly over a
    :class:`BELGraph`
    """
    return True


@node_predicate
def false_node_predicate(_: BaseEntity) -> bool:
    """Return false for all nodes."""
    return False
