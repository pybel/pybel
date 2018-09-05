# -*- coding: utf-8 -*-

"""Query builder."""

import json
import logging
import random

from six.moves import UserList

from .constants import (
    SEED_TYPE_ANNOTATION, SEED_TYPE_INDUCTION, SEED_TYPE_NEIGHBORS, SEED_TYPE_SAMPLE,
)
from .selection import get_subgraph
from ...dsl import BaseEntity
from ...manager.models import Node
from ...struct import union
from ...tokens import parse_result_to_dsl

log = logging.getLogger(__name__)

SEED_METHOD = 'type'
SEED_DATA = 'data'


class Seeding(UserList):
    """Represents a container of seeding methods to apply to a network."""

    def append_induction(self, nodes):
        """Add a seed induction method.

        :param list[tuple or Node or BaseEntity] nodes: A list of PyBEL node tuples
        :returns: self for fluid API
        :rtype: Seeding
        """
        return self._append_seed(SEED_TYPE_INDUCTION, _handle_nodes(nodes))

    def append_neighbors(self, nodes):
        """Add a seed by neighbors.

        :param nodes: A list of PyBEL node tuples
        :type nodes: BaseEntity or iter[BaseEntity]
        :returns: self for fluid API
        :rtype: Seeding
        """
        return self._append_seed(SEED_TYPE_NEIGHBORS, _handle_nodes(nodes))

    def append_annotation(self, annotation, values):
        """Add a seed induction method for single annotation's values.

        :param str annotation: The annotation to filter by
        :param set[str] values: The values of the annotation to keep
        :returns: self for fluid API
        :rtype: Seeding
        """
        return self._append_seed(SEED_TYPE_ANNOTATION, {
            'annotations': {
                annotation: values
            }
        })

    def append_sample(self, **kwargs):
        """Add seed induction methods.

        Kwargs can have ``number_edges`` or ``number_seed_nodes``.
        :returns: self for fluid API
        :rtype: Seeding
        """
        data = {
            'seed': random.randint(0, 1000000)
        }
        data.update(kwargs)

        return self._append_seed(SEED_TYPE_SAMPLE, data)

    def _append_seed(self, seed_type, data):
        """Add a seeding method.

        :param str seed_type:
        :param data:
        :returns: self for fluid API
        :rtype: Seeding
        """
        self.append({
            SEED_METHOD: seed_type,
            SEED_DATA: data,
        })
        return self

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

    def to_json(self):
        """Serialize this seeding container to a JSON object.

        :rtype: list
        """
        return list(self)

    def dump(self, file, sort_keys=True, **kwargs):
        """Dump this seeding container to a file as JSON."""
        json.dump(self.to_json(), file, sort_keys=sort_keys, **kwargs)

    def dumps(self, sort_keys=True, **kwargs):
        """Dump this query to a string as JSON.

        :rtype: str
        """
        return json.dumps(self.to_json(), sort_keys=sort_keys, **kwargs)

    @staticmethod
    def from_json(data):
        """Build a seeding container from a JSON list.

        :param dict data:
        :rtype: Seeding
        """
        return Seeding(data)

    @staticmethod
    def load(file):
        """Load a seeding container from a JSON file.

        :rtype: Seeding
        """
        return Seeding.from_json(json.load(file))

    @staticmethod
    def loads(s):
        """Load a seeding container from a JSON string.

        :rtype: Seeding
        """
        return Seeding.from_json(json.loads(s))


def _handle_nodes(nodes):
    """Handle nodes that might be dictionaries.

    :type nodes: BaseEntity or list[dict] or list[BaseEntity]
    :rtype: list[BaseEntity]
    """
    if isinstance(nodes, BaseEntity):
        return [nodes]

    return [
        (
            parse_result_to_dsl(node)
            if isinstance(node, dict) else
            node
        )
        for node in nodes
    ]
