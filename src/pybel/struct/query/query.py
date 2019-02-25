# -*- coding: utf-8 -*-

"""Query builder."""

import json
import logging
from typing import Dict, Iterable, List, Mapping, Optional, Set, TextIO, Union

from .exc import QueryMissingNetworksError
from .seeding import Seeding
from ..pipeline import Pipeline
from ...dsl import BaseEntity

__all__ = [
    'Query',
]

log = logging.getLogger(__name__)


class Query:
    """Represents a query over a network store."""

    def __init__(self,
                 network_ids: Union[None, int, Iterable[int]] = None,
                 seeding: Optional[Seeding] = None,
                 pipeline: Optional[Pipeline] = None,
                 ) -> None:
        """Build a query.

        :param network_ids: Database network identifiers identifiers
        """
        if not network_ids:
            self.network_ids = []
        elif isinstance(network_ids, int):
            self.network_ids = [network_ids]
        elif isinstance(network_ids, Iterable):
            network_ids = list(network_ids)

            for network_id in network_ids:
                if not isinstance(network_id, int):
                    raise TypeError(network_ids)

            self.network_ids = network_ids
        else:
            raise TypeError(network_ids)

        if seeding is not None and not isinstance(seeding, Seeding):
            raise TypeError('Not a Seeding: {}'.format(seeding))
        self.seeding = seeding or Seeding()

        if pipeline is not None and not isinstance(pipeline, Pipeline):
            raise TypeError('Not a pipeline: {}'.format(pipeline))
        self.pipeline = pipeline or Pipeline()

    def append_network(self, network_id: int) -> 'Query':
        """Add a network to this query.

        :param network_id: The database identifier of the network
        :returns: self for fluid API
        """
        self.network_ids.append(network_id)
        return self

    def append_seeding_induction(self, nodes: Union[BaseEntity, List[BaseEntity], List[Dict]]) -> Seeding:
        """Add a seed induction method.

        :returns: seeding container for fluid API
        """
        return self.seeding.append_induction(nodes)

    def append_seeding_neighbors(self, nodes: Union[BaseEntity, List[BaseEntity], List[Dict]]) -> Seeding:
        """Add a seed by neighbors.

        :returns: seeding container for fluid API
        """
        return self.seeding.append_neighbors(nodes)

    def append_seeding_annotation(self, annotation: str, values: Set[str]) -> Seeding:
        """Add a seed induction method for single annotation's values.

        :param annotation: The annotation to filter by
        :param values: The values of the annotation to keep
        """
        return self.seeding.append_annotation(annotation, values)

    def append_seeding_sample(self, **kwargs) -> Seeding:
        """Add seed induction methods.

        Kwargs can have ``number_edges`` or ``number_seed_nodes``.
        """
        return self.seeding.append_sample(**kwargs)

    def append_pipeline(self, name, *args, **kwargs) -> Pipeline:
        """Add an entry to the pipeline. Defers to :meth:`pybel_tools.pipeline.Pipeline.append`.

        :param name: The name of the function
        :type name: str or types.FunctionType
        :return: This pipeline for fluid query building
        """
        return self.pipeline.append(name, *args, **kwargs)

    def __call__(self, manager):
        """Run this query and returns the resulting BEL graph with :meth:`Query.run`.

        :param pybel.manager.Manager manager: A cache manager
        :rtype: Optional[pybel.BELGraph]
        """
        return self.run(manager)

    def run(self, manager):
        """Run this query and returns the resulting BEL graph.

        :param manager: A cache manager
        :rtype: Optional[pybel.BELGraph]
        """
        universe = self._get_universe(manager)
        graph = self.seeding.run(universe)
        return self.pipeline.run(graph, universe=universe)

    def _get_universe(self, manager):
        if not self.network_ids:
            raise QueryMissingNetworksError('can not run query without network identifiers')

        log.debug('query universe consists of networks: %s', self.network_ids)

        universe = manager.get_graph_by_ids(self.network_ids)
        log.debug('query universe has %d nodes/%d edges', universe.number_of_nodes(), universe.number_of_edges())

        return universe

    def to_json(self) -> Dict:
        """Return this query as a JSON object."""
        rv = {
            'network_ids': self.network_ids,
        }

        if self.seeding:
            rv['seeding'] = self.seeding.to_json()

        if self.pipeline:
            rv['pipeline'] = self.pipeline.to_json()

        return rv

    def dump(self, file: TextIO, **kwargs) -> None:
        """Dump this query to a file as JSON."""
        json.dump(self.to_json(), file, **kwargs)

    def dumps(self, **kwargs) -> str:
        """Dump this query to a string as JSON."""
        return json.dumps(self.to_json(), **kwargs)

    @staticmethod
    def from_json(data: Mapping) -> 'Query':
        """Load a query from a JSON dictionary.

        :param data: A JSON dictionary
        :raises: QueryMissingNetworksError
        """
        network_ids = data.get('network_ids')
        if network_ids is None:
            raise QueryMissingNetworksError('query JSON did not have key "network_ids"')

        seeding_data = data.get('seeding')
        seeding = (
            Seeding.from_json(seeding_data)
            if seeding_data is not None else
            None
        )

        pipeline_data = data.get('pipeline')
        pipeline = (
            Pipeline.from_json(pipeline_data)
            if pipeline_data is not None else
            None
        )

        return Query(
            network_ids=network_ids,
            seeding=seeding,
            pipeline=pipeline,
        )

    @staticmethod
    def load(file: TextIO) -> 'Query':
        """Load a query from a JSON file.

        :raises: QueryMissingNetworksError
        """
        return Query.from_json(json.load(file))

    @staticmethod
    def loads(s: str) -> 'Query':
        """Load a query from a JSON string.

        :param s: A stringified JSON query
        :raises: QueryMissingNetworksError
        """
        return Query.from_json(json.loads(s))

    def __str__(self):
        return 'Query(networks={}, seeding={}, pipeline={})'.format(self.network_ids, self.seeding, self.pipeline)
