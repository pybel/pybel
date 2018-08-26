# -*- coding: utf-8 -*-

"""Query builder."""

import json
import logging

from .constants import (
    SEED_TYPE_ANNOTATION, SEED_TYPE_INDUCTION, SEED_TYPE_NEIGHBORS, SEED_TYPE_SAMPLE,
)
from .exc import QueryMissingNetworksError
from .selection import get_subgraph
from ...dsl import BaseEntity
from ...manager.models import Node
from ...struct import union
from ...struct.pipeline import Pipeline
from ...tokens import parse_result_to_dsl

__all__ = [
    'Query',
]

log = logging.getLogger(__name__)

SEED_METHOD = 'type'
SEED_DATA = 'data'


def _get_random_int():
    try:
        import numpy as np
        return np.random.randint(0, np.iinfo('i').max)
    except ImportError:
        raise NotImplementedError


class Query:
    """Wraps a query over the network store."""

    def __init__(self, network_ids=None, seeding=None, pipeline=None):
        """Build a query.

        :param iter[int] network_ids: Database network identifiers identifiers
        :type network_ids: None or int or iter[int]
        :param Optional[list[dict]] seeding:
        :param Optional[Pipeline] pipeline: Instance of a pipeline
        """
        if not network_ids:
            self.network_ids = []
        elif isinstance(network_ids, int):
            self.network_ids = [network_ids]
        else:
            self.network_ids = list(network_ids)

        self.seeding = seeding or []
        self.pipeline = pipeline or Pipeline()

    def append_network(self, network_id):
        """Add a network to this query.

        :param int network_id: The database identifier of the network
        """
        self.network_ids.append(network_id)

    def _append_seed(self, seed_type, data):
        """Add a seeding method.

        :param str seed_type:
        :param data:
        """
        self.seeding.append({
            SEED_METHOD: seed_type,
            SEED_DATA: data
        })

    @staticmethod
    def _handle_nodes(nodes):
        return [
            (
                parse_result_to_dsl(node)
                if isinstance(node, dict) else
                node
            )
            for node in nodes
        ]

    def append_seeding_induction(self, nodes):
        """Add a seed induction method.

        :param list[tuple or Node or BaseEntity] nodes: A list of PyBEL node tuples
        """
        self._append_seed(SEED_TYPE_INDUCTION, self._handle_nodes(nodes))

    def append_seeding_neighbors(self, nodes):
        """Add a seed by neighbors.

        :param nodes: A list of PyBEL node tuples
        :type nodes: BaseEntity or iter[BaseEntity]
        """
        self._append_seed(SEED_TYPE_NEIGHBORS, self._handle_nodes(nodes))

    def append_seeding_annotation(self, annotation, values):
        """Add a seed induction method for single annotation's values.

        :param str annotation: The annotation to filter by
        :param set[str] values: The values of the annotation to keep
        """
        log.debug('appending seed by annotation=%s and values=%s', annotation, values)
        self._append_seed(SEED_TYPE_ANNOTATION, {
            'annotations': {
                annotation: values
            }
        })

    def append_seeding_sample(self, **kwargs):
        """Adds seed induction methods.

        Kwargs can have ``number_edges`` or ``number_seed_nodes``.
        """
        data = {
            'seed': _get_random_int
        }
        data.update(kwargs)

        self._append_seed(SEED_TYPE_SAMPLE, data)

    def append_pipeline(self, name, *args, **kwargs):
        """Add an entry to the pipeline. Defers to :meth:`pybel_tools.pipeline.Pipeline.append`.

        :param name: The name of the function
        :type name: str or types.FunctionType
        :return: This pipeline for fluid query building
        :rtype: Pipeline
        """
        return self.pipeline.append(name, *args, **kwargs)

    def __call__(self, manager, in_place=True):
        """Run this query and returns the resulting BEL graph with :meth:`Query.run`.

        :param pybel.manager.Manager manager: A cache manager
        :param bool in_place: Should the graph be copied before applying the algorithm?
        :rtype: Optional[pybel.BELGraph]
        """
        return self.run(manager, in_place=in_place)

    def run(self, manager, in_place=True):
        """Run this query and returns the resulting BEL graph.

        :param pybel.manager.Manager manager: A cache manager
        :param bool in_place: Should the graph be copied before applying the algorithm?
        :rtype: Optional[pybel.BELGraph]
        """
        if not self.network_ids:
            raise QueryMissingNetworksError('can not run query without network identifiers')

        log.debug('query universe consists of networks: %s', self.network_ids)

        universe = manager.get_graph_by_ids(self.network_ids)
        log.debug('query universe has %d nodes/%d edges', universe.number_of_nodes(), universe.number_of_edges())

        # parse seeding stuff

        if not self.seeding:
            return self.pipeline.run(universe, universe=universe, in_place=in_place)

        subgraphs = []

        for seed in self.seeding:
            seed_method, seed_data = seed[SEED_METHOD], seed[SEED_DATA]

            log.debug('seeding with %s: %s', seed_method, seed_data)
            subgraph = get_subgraph(universe, seed_method=seed_method, seed_data=seed_data)

            if subgraph is None:
                log.debug('seed returned empty graph: %s', seed)
                continue

            subgraphs.append(subgraph)

        if not subgraphs:
            log.debug('no subgraphs returned')
            return

        graph = union(subgraphs)

        return self.pipeline.run(graph, universe=universe, in_place=in_place)

    def _seeding_to_json(self):
        return self.seeding

    def seeding_to_jsons(self, indent=None):
        """Return seeding information as a JSON string

        :rtype: str
        """
        return json.dumps(self._seeding_to_json(), sort_keys=True, indent=indent)

    def _pipeline_to_json(self):
        return self.pipeline.protocol

    def to_json(self):
        """Return this query as a JSON object.

        :rtype: dict
        """
        rv = {
            'network_ids': list(self.network_ids),
        }

        if self.seeding:
            rv['seeding'] = self._seeding_to_json()

        if self.pipeline:
            rv['pipeline'] = self._pipeline_to_json()

        return rv

    def to_jsons(self, indent=None):
        """Return this query as a stringified JSON object.

        :rtype: str
        """
        return json.dumps(self.to_json(), indent=indent)

    @staticmethod
    def from_jsons(s):
        """Load a query from a stringified JSON object.

        :param str s: A stringified JSON query
        :rtype: Query
        :raises: QueryMissingNetworks
        """
        return Query.from_json(json.loads(s))

    @staticmethod
    def from_json(data):
        """Load a query from a JSON dictionary.

        :param dict data: A JSON dictionary
        :rtype: Query
        :raises: QueryMissingNetworks
        """
        network_ids = data.get('network_ids')
        if network_ids is None:
            raise QueryMissingNetworksError('query JSON did not have key "network_ids"')

        if 'pipeline' in data:
            pipeline = Pipeline(data['pipeline'])
        else:
            pipeline = None

        return Query(
            network_ids=network_ids,
            seeding=data.get('seeding'),
            pipeline=pipeline
        )
