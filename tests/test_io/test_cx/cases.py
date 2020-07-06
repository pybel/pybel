# -*- coding: utf-8 -*-

"""Test cases for PyBEL-CX."""

import json
import unittest
from typing import Mapping, Tuple

from pybel import BELGraph, BaseEntity
from pybel.constants import ANNOTATIONS, CITATION, EVIDENCE, IDENTIFIER, NAMESPACE, TARGET_MODIFIER, RELATION, SOURCE_MODIFIER
from pybel.typing import EdgeData

__all__ = [
    'TestCase',
]


def _edge_to_tuple(u: BaseEntity, v: BaseEntity, edge_data: EdgeData):
    """Convert an edge to tuple.

    :return: A tuple that can be hashed representing this edge. Makes no promises to its structure.
    """
    citation = edge_data.get(CITATION)
    if citation is None:
        citation_hashable = None
    else:
        citation_hashable = (citation[NAMESPACE], citation[IDENTIFIER])

    evidence_hashable = edge_data.get(EVIDENCE)

    annotations = edge_data.get(ANNOTATIONS)
    if annotations is None:
        annotations_hashable = None
    else:
        annotations_hashable = tuple(
            (key, tuple(sorted(values)))
            for key, values in sorted(annotations.items())
        )

    source_modifier = edge_data.get(SOURCE_MODIFIER)
    if source_modifier is None:
        subject_hashable = None
    else:
        subject_hashable = json.dumps(source_modifier, ensure_ascii=True, sort_keys=True, indent=0)

    target_modifier = edge_data.get(TARGET_MODIFIER)
    if target_modifier is None:
        object_hashable = None
    else:
        object_hashable = json.dumps(target_modifier, ensure_ascii=True, sort_keys=True, indent=0)

    return (
        u,
        v,
        edge_data[RELATION],
        citation_hashable,
        evidence_hashable,
        annotations_hashable,
        subject_hashable,
        object_hashable,
    )


def _hash_edge(u: BaseEntity, v: BaseEntity, data: EdgeData) -> int:
    """Convert an edge tuple to a hash.

    :return: A hashed version of the edge tuple using md5 hash of the binary pickle dump of u, v, and the json dump of d
    """
    return hash(_edge_to_tuple(u, v, data))


def _get_edge_dict(graph: BELGraph) -> Mapping[int, Tuple[BaseEntity, BaseEntity, EdgeData]]:
    return {
        _hash_edge(u, v, data): (u, v, data)
        for u, v, k, data in graph.edges(keys=True, data=True)
    }


class TestCase(unittest.TestCase):
    """Extension to base :class:`unittest.TestCase` with :class:`pybel.BELGraph` comparison."""

    def assert_graph_equal(self, g1: BELGraph, g2: BELGraph) -> None:
        """Assert two BEL graphs are the same."""
        self.assertEqual(g1.graph, g2.graph, msg='Metadata were not the same')

        # self.assertEqual(g1.number_of_nodes(), g2.number_of_nodes())
        self.assertEqual(set(g1), set(g2), msg='Nodes were not the same')

        # self.assertEqual(g1.number_of_edges(), g2.number_of_edges())
        self.assertEqual(set(g1.edges()), set(g2.edges()))

        g1_edge_hashes = _get_edge_dict(g1)
        g2_edge_hashes = _get_edge_dict(g2)

        g1k = g1_edge_hashes.keys()
        g2k = g2_edge_hashes.keys()

        g1ng2 = g1k - g2k
        g2ng1 = g2k - g1k

        if g1ng2 and not g2ng1:
            for k in g1ng2:
                print(k[:6], g1_edge_hashes[k])
            self.fail()

        elif not g1ng2 and g2ng1:
            for k in g2ng1:
                print(k[:6], g2_edge_hashes[k])
            self.fail()

        elif g1ng2 and g2ng1:
            print('in g1 but not g2:')
            for k in g1ng2:
                print(k[:6], g1_edge_hashes[k])

            print('in g2 but not g1:')
            for k in g2ng1:
                print(k[:6], g2_edge_hashes[k])
            self.fail()
