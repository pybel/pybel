# -*- coding: utf-8 -*-

"""This module holds the Pipeline class."""

import json
import logging
import types
from functools import wraps

from .decorators import get_transformation, in_place_map, mapped, universe_map
from .exc import MetaValueError, MissingPipelineFunctionError, MissingUniverseError
from ..operations import node_intersection, union

__all__ = [
    'Pipeline',
]

log = logging.getLogger(__name__)

META_UNION = 'union'
META_INTERSECTION = 'intersection'


def _get_protocol_tuple(data):
    """Convert a dictionary to a tuple.

    :param dict data:
    :rtype: tuple[str,list,dict]
    """
    return data['function'], data.get('args', []), data.get('kwargs', {})


class Pipeline(object):
    """Builds and runs analytical pipelines on BEL graphs.

    Example usage:

    >>> from pybel import BELGraph
    >>> from pybel.struct.pipeline import Pipeline
    >>> from pybel.struct.mutation import enrich_protein_and_rna_origins, prune_protein_rna_origins
    >>> graph = BELGraph()
    >>> example = Pipeline()
    >>> example.append(enrich_protein_and_rna_origins)
    >>> example.append(prune_protein_rna_origins)
    >>> result = example.run(graph)
    """

    def __init__(self, protocol=None, universe=None):
        """
        :param iter[dict] protocol: An iterable of dictionaries describing how to transform a network
        :param pybel.BELGraph universe: The entire set of known knowledge to draw from
        """
        self.universe = universe
        self.protocol = [] if protocol is None else protocol

    def __len__(self):
        return len(self.protocol)

    def __iter__(self):
        return iter(self.protocol)

    @staticmethod
    def from_functions(functions):
        """Build a pipeline from a list of functions.

        :param functions: A list of functions or names of functions
        :type functions: iter[((pybel.BELGraph) -> pybel.BELGraph) or ((pybel.BELGraph) -> None) or str]
        :rtype: Pipeline

        Example with function:

        >>> from pybel.struct.pipeline import Pipeline
        >>> from pybel.struct.mutation import remove_associations
        >>> pipeline = Pipeline.from_functions([remove_associations])

        Equivalent example with function names:

        >>> from pybel.struct.pipeline import Pipeline
        >>> pipeline = Pipeline.from_functions(['remove_associations'])

        Lookup by name is possible for built in functions, and those that have been registered correctly using one of
        the four decorators:

        1. :func:`pybel.struct.pipeline.transformation`,
        2. :func:`pybel.struct.pipeline.in_place_transformation`,
        3. :func:`pybel.struct.pipeline.uni_transformation`,
        4. :func:`pybel.struct.pipeline.uni_in_place_transformation`,
        """
        result = Pipeline()

        for func in functions:
            result.append(func)

        return result

    def _get_function(self, name):
        """Wrap a function with the universe and in-place.

        :param str name: The name of the function
        :rtype: types.FunctionType
        :raises MissingPipelineFunctionError: If the functions is not registered
        """
        f = mapped.get(name)

        if f is None:
            raise MissingPipelineFunctionError('{} is not registered as a pipeline function'.format(name))

        if name in universe_map and name in in_place_map:
            return self._wrap_in_place(self._wrap_universe(f))

        if name in universe_map:
            return self._wrap_universe(f)

        if name in in_place_map:
            return self._wrap_in_place(f)

        return f

    def append(self, name, *args, **kwargs):
        """Add a function (either as a reference, or by name) and arguments to the pipeline.

        :param name: The name of the function
        :type name: str or (pybel.BELGraph -> pybel.BELGraph)
        :param args: The positional arguments to call in the function
        :param kwargs: The keyword arguments to call in the function
        :return: This pipeline for fluid query building
        :rtype: Pipeline
        :raises MissingPipelineFunctionError: If the function is not registered
        """
        if isinstance(name, types.FunctionType):
            return self.append(name.__name__, *args, **kwargs)
        elif isinstance(name, str):
            get_transformation(name)
        else:
            raise TypeError('invalid function argument: {}'.format(name))

        av = {
            'function': name,
        }

        if args:
            av['args'] = args

        if kwargs:
            av['kwargs'] = kwargs

        self.protocol.append(av)
        return self

    def extend(self, protocol):
        """Add another pipeline to the end of the current pipeline.

        :param protocol: An iterable of dictionaries (or another Pipeline)
        :type protocol: iter[dict] or Pipeline
        :return: This pipeline for fluid query building
        :rtype: Pipeline

        Example:

        >>> p1 = Pipeline.from_functions(['enrich_protein_and_rna_origins'])
        >>> p2 = Pipeline.from_functions(['remove_pathologies'])
        >>> p1.extend(p2)
        """
        for data in protocol:
            name, args, kwargs = _get_protocol_tuple(data)
            self.append(name, *args, **kwargs)

        return self

    def _run_helper(self, graph, protocol):
        """Help run the protocol.

        :param pybel.BELGraph graph: A BEL graph
        :param list[dict] protocol: The protocol to run, as JSON
        :rtype: pybel.BELGraph
        """
        result = graph

        for entry in protocol:
            meta_entry = entry.get('meta')

            if meta_entry is None:
                name, args, kwargs = _get_protocol_tuple(entry)
                func = self._get_function(name)
                result = func(result, *args, **kwargs)
            else:
                networks = (
                    self._run_helper(graph, subprotocol)
                    for subprotocol in entry['pipelines']
                )

                if meta_entry == META_UNION:
                    result = union(networks)

                elif meta_entry == META_INTERSECTION:
                    result = node_intersection(networks)

                else:
                    raise MetaValueError('invalid meta-command: {}'.format(meta_entry))

        return result

    def _can_be_run_in_place(self):
        """Checks if this pipeline can be run in place.

        Requirements:

        - All functions have the "in place" tag
        - No splitting, unioning, or other exotic things happen.

        :rtype: bool
        """
        raise NotImplementedError  # TODO implement

    def run(self, graph, universe=None, in_place=True):
        """Run the contained protocol on a seed graph.

        :param pybel.BELGraph graph: The seed BEL graph
        :param pybel.BELGraph universe: Allows just-in-time setting of the universe in case it wasn't set before.
                                        Defaults to the given network.
        :param bool in_place: Should the graph be copied before applying the algorithm?
        :return: The new graph is returned if not applied in-place
        :rtype: pybel.BELGraph
        """
        self.universe = graph.copy() if universe is None else universe

        result = graph if in_place else graph.copy()
        result = self._run_helper(result, self.protocol)
        return result

    def __call__(self, graph, universe=None, in_place=True):
        """Call :meth:`Pipeline.run`.

        :param pybel.BELGraph graph: The seed BEL graph
        :param pybel.BELGraph universe: Allows just-in-time setting of the universe in case it wasn't set before.
                                        Defaults to the given network.
        :param bool in_place: Should the graph be copied before applying the algorithm?
        :return: The new graph is returned if not applied in-place
        :rtype: pybel.BELGraph

        Using __call__ allows for methods to be chained together then applied

        >>> from pybel.struct.mutation import remove_associations, remove_pathologies
        >>> from pybel.struct.pipeline.pipeline import Pipeline
        >>> from pybel import BELGraph
        >>> pipe = Pipeline.from_functions([remove_associations, remove_pathologies])
        >>> graph = BELGraph() ...
        >>> new_graph = pipe(graph)
        """
        return self.run(graph=graph, universe=universe, in_place=in_place)

    def _wrap_universe(self, func):
        """Take a function that needs a universe graph as the first argument and returns a wrapped one."""

        @wraps(func)
        def wrapper(graph, *args, **kwargs):
            """Applies the enclosed function with the universe given as the first argument"""
            if self.universe is None:
                raise MissingUniverseError(
                    'Can not run universe function [{}] - No universe is set'.format(func.__name__))

            return func(self.universe, graph, *args, **kwargs)

        return wrapper

    @staticmethod
    def _wrap_in_place(func):
        """Take a function that doesn't return the graph and returns the graph."""

        @wraps(func)
        def wrapper(graph, *args, **kwargs):
            """Applies the enclosed function and returns the graph"""
            func(graph, *args, **kwargs)
            return graph

        return wrapper

    def dumps(self, **kwargs):
        """Give this pipeline as a JSON string.

        :rtype: str
        """
        return json.dumps(self.protocol, **kwargs)

    def dump(self, file):
        """Dump this protocol to a file in JSON.

        :param file: A file or file-like to pass to :func:`json.dump`
        """
        return json.dump(self.protocol, file)

    @staticmethod
    def load(file):
        """Load a protocol from JSON contained in file.

        :param file: A file or file-like
        :return: The pipeline represented by the JSON in the file
        :rtype: Pipeline
        :raises MissingPipelineFunctionError: If any functions are not registered
        """
        return Pipeline(protocol=json.load(file))

    @staticmethod
    def loads(s):
        """Load a protocol from a JSON string.

        :param str s: A JSON string
        :return: The pipeline represented by the JSON in the file
        :rtype: Pipeline
        :raises MissingPipelineFunctionError: If any functions are not registered
        """
        return Pipeline(protocol=json.loads(s))

    def __str__(self):
        return json.dumps(self.protocol, indent=2)

    @staticmethod
    def _build_meta(meta, pipelines):
        """
        :param str meta: either union or intersection
        :param iter[Pipeline] pipelines:
        :rtype: Pipeline
        """
        return Pipeline(protocol=[
            {
                'meta': meta,
                'pipelines': [
                    pipeline.protocol
                    for pipeline in pipelines
                ]
            },
        ])

    @staticmethod
    def union(pipelines):
        """Take the union of multiple pipelines.

        :param iter[Pipeline] pipelines: A list of pipelines
        :return: The union of the results from multiple pipelines
        :rtype: Pipeline
        """
        return Pipeline._build_meta(META_UNION, pipelines)

    @staticmethod
    def intersection(pipelines):
        """Take the intersection of the results from multiple pipelines.

        :param iter[Pipeline] pipelines: A list of pipelines
        :return: The intersection of results from multiple pipelines
        :rtype: Pipeline
        """
        return Pipeline._build_meta(META_INTERSECTION, pipelines)
