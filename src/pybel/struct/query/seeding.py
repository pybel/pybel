# -*- coding: utf-8 -*-

"""Query builder."""

import json
import logging
import random
from collections import UserList
from typing import Any, Dict, List, Set, TextIO, Union

from .constants import SEED_TYPE_ANNOTATION, SEED_TYPE_INDUCTION, SEED_TYPE_NEIGHBORS, SEED_TYPE_SAMPLE
from .selection import get_subgraph
from ...dsl import BaseEntity
from ...struct import union
from ...tokens import parse_result_to_dsl

log = logging.getLogger(__name__)

SEED_METHOD = 'type'
SEED_DATA = 'data'

MaybeNodeList = Union[BaseEntity, List[BaseEntity], List[Dict]]


class Seeding(UserList):
    """Represents a container of seeding methods to apply to a network."""

    def append_induction(self, nodes: MaybeNodeList) -> 'Seeding':
        """Add a seed induction method.

        :param nodes: A node or list of nodes
        :returns: self for fluid API
        """
        return self._append_seed_handle_nodes(SEED_TYPE_INDUCTION, nodes)

    def append_neighbors(self, nodes: MaybeNodeList) -> 'Seeding':
        """Add a seed by neighbors.

        :param nodes: A node or list of nodes
        :returns: self for fluid API
        """
        return self._append_seed_handle_nodes(SEED_TYPE_NEIGHBORS, nodes)

    def append_annotation(self, annotation: str, values: Set[str]) -> 'Seeding':
        """Add a seed induction method for single annotation's values.

        :param annotation: The annotation to filter by
        :param values: The values of the annotation to keep
        :returns: self for fluid API
        """
        return self._append_seed(SEED_TYPE_ANNOTATION, {
            'annotations': {
                annotation: values,
            }
        })

    def append_sample(self, **kwargs) -> 'Seeding':
        """Add seed induction methods.

        Kwargs can have ``number_edges`` or ``number_seed_nodes``.

        :returns: self for fluid API
        """
        data = {
            'seed': random.randint(0, 1000000)
        }
        data.update(kwargs)

        return self._append_seed(SEED_TYPE_SAMPLE, data)

    def _append_seed(self, seed_type: str, data: Any) -> 'Seeding':
        """Add a seeding method and returns self.

        :returns: self for fluid API
        """
        self.append({
            SEED_METHOD: seed_type,
            SEED_DATA: data,
        })
        return self

    def _append_seed_handle_nodes(self, seed_type: str, nodes: MaybeNodeList) -> 'Seeding':
        """Add a seeding method and returns self.

        :param seed_type: The seed type
        :param nodes: A node or list of nodes
        :returns: self for fluid API
        """
        return self._append_seed(seed_type, _handle_nodes(nodes))

    def run(self, graph):
        """Seed the graph or return none if not possible.

        :type graph: pybel.BELGraph
        :rtype: Optional[pybel.BELGraph]
        """
        if not self:
            log.debug('no seeding, returning graph: %s', graph)
            return graph

        subgraphs = []

        for seed in self:
            seed_method, seed_data = seed[SEED_METHOD], seed[SEED_DATA]

            log.debug('seeding with %s: %s', seed_method, seed_data)
            subgraph = get_subgraph(graph, seed_method=seed_method, seed_data=seed_data)

            if subgraph is None:
                log.debug('seed returned empty graph: %s', seed)
                continue

            subgraphs.append(subgraph)

        if not subgraphs:
            log.debug('no subgraphs returned')
            return

        return union(subgraphs)

    def to_json(self) -> List[Dict]:
        """Serialize this seeding container to a JSON object."""
        return list(self)

    def dump(self, file, sort_keys: bool = True, **kwargs) -> None:
        """Dump this seeding container to a file as JSON."""
        json.dump(self.to_json(), file, sort_keys=sort_keys, **kwargs)

    def dumps(self, sort_keys: bool = True, **kwargs) -> str:
        """Dump this query to a string as JSON."""
        return json.dumps(self.to_json(), sort_keys=sort_keys, **kwargs)

    @staticmethod
    def from_json(data) -> 'Seeding':
        """Build a seeding container from a JSON list."""
        return Seeding(data)

    @staticmethod
    def load(file: TextIO) -> 'Seeding':
        """Load a seeding container from a JSON file."""
        return Seeding.from_json(json.load(file))

    @staticmethod
    def loads(s: str) -> 'Seeding':
        """Load a seeding container from a JSON string."""
        return Seeding.from_json(json.loads(s))


def _handle_nodes(nodes: MaybeNodeList) -> List[BaseEntity]:
    """Handle node(s) that might be dictionaries."""
    if isinstance(nodes, BaseEntity):
        return [nodes]

    return [
        (
            parse_result_to_dsl(node)
            if not isinstance(node, BaseEntity) else
            node
        )
        for node in nodes
    ]
