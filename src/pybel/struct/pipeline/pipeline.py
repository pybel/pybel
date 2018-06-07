# -*- coding: utf-8 -*-

"""This module holds the Pipeline class."""

import json
import logging
import types
from functools import wraps

from .decorators import get_transformation, in_place_map, mapped, universe_map
from .exc import MissingPipelineFunctionError
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
    >>> from pybel.struct.mutation import infer_central_dogma, prune_central_dogma
    >>> graph = BELGraph()
    >>> example = Pipeline()
    >>> example.append(infer_central_dogma)
    >>> example.append(prune_central_dogma)
    >>> result = example.run(graph)
    """

    def __init__(self, protocol=None, universe=None):
        """
        :param list[dict] protocol: The list of dictionaries describing how to transform a network
        :param pybel.BELGraph universe: The entire set of known knowledge to draw from
        """
        self.universe = universe
        self.protocol = []

        if protocol is not None:
            self._extend_helper(protocol)

    def __nonzero__(self):
        return self.protocol

    def __len__(self):
        return len(self.protocol)

    @staticmethod
    def from_functions(functions):
        """Build a pipeline from a list of functions.

        :param iter[(pybel.BELGraph) -> pybel.BELGraph or (pybel.BELGraph) -> None] functions: A list of functions
        :rtype: Pipeline
        """
        result = Pipeline()

        for func in functions:
            result.append(func)

        return result

    def get_function(self, name):
        """Wrap a function with the universe and in-place.

        :param str name: The name of the function
        :rtype: types.FunctionType
        :raises: MissingPipelineFunctionError
        """
        f = mapped.get(name)

        if f is None:
            raise MissingPipelineFunctionError('{} is not registered as a pipeline function'.format(name))

        if name in universe_map and name in in_place_map:
            return self.wrap_in_place(self.wrap_universe(f))

        if name in universe_map:
            return self.wrap_universe(f)

        if name in in_place_map:
            return self.wrap_in_place(f)

        return f

    def append(self, name, *args, **kwargs):
        """Add a function (either as a reference, or by name) and arguments to the pipeline.

        :param name: The name of the function
        :type name: str or (pybel.BELGraph -> pybel.BELGraph)
        :param args: The positional arguments to call in the function
        :param kwargs: The keyword arguments to call in the function
        :return: This pipeline for fluid query building
        :rtype: Pipeline
        :raises: MissingPipelineFunctionError
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

    def _extend_helper(self, protocol):
        """Extend this pipeline's protocol with another protocol.

        :param list[dict] protocol:
        """
        if protocol:
            for data in protocol:
                name, args, kwargs = _get_protocol_tuple(data)
                self.append(name, *args, **kwargs)

    def extend(self, pipeline):
        """Add another pipeline to the end of the current pipeline.

        :param Pipeline pipeline: Another pipeline
        :return: This pipeline for fluid query building
        :rtype: Pipeline

        Example:

        >>> p1 = Pipeline.from_functions(['infer_central_dogma'])
        >>> p2 = Pipeline.from_functions(['remove_pathologies'])
        >>> p1.extend(p2)
         """
        self._extend_helper(pipeline.protocol)
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
                func = self.get_function(name)
                result = func(result, *args, **kwargs)
            else:
                networks = (
                    self._run_helper(graph, subprotocol)
                    for subprotocol in entry['pipeline']
                )

                if meta_entry == META_UNION:
                    result = union(networks)

                elif meta_entry == META_INTERSECTION:
                    result = node_intersection(networks)

                else:
                    raise ValueError('invalid meta-command: {}'.format(meta_entry))

        return result

    def run(self, graph, universe=None, in_place=True):
        """Run the contained protocol on a seed graph.

        :param pybel.BELGraph graph: The seed BEL graph
        :param pybel.BELGraph universe: Allows just-in-time setting of the universe in case it wasn't set before.
                                        Defaults to the given network.
        :param bool in_place: Should the graph be copied before applying the algorithm?
        :return: The new graph is returned if not applied in-place
        :rtype: pybel.BELGraph
        """
        self.universe = graph if universe is None else universe

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

    def wrap_universe(self, f):
        """Take a function that needs a universe graph as the first argument and returns a wrapped one."""

        @wraps(f)
        def wrapper(graph, *args, **kwargs):
            """Applies the enclosed function with the universe given as the first argument"""
            if self.universe is None:
                raise ValueError('Can not run universe function [{}] - No universe is set'.format(f.__name__))

            return f(self.universe, graph, *args, **kwargs)

        return wrapper

    @staticmethod
    def wrap_in_place(f):
        """Take a function that doesn't return the graph and returns the graph."""

        @wraps(f)
        def wrapper(graph, *args, **kwargs):
            """Applies the enclosed function and returns the graph"""
            f(graph, *args, **kwargs)
            return graph

        return wrapper

    def to_json(self):
        """Give this pipeline as JSON.

        :rtype: list[dict]
        """
        return self.protocol

    def to_jsons(self):
        """Give this pipeline as a JSON string.

        :rtype: str
        """
        return json.dumps(self.to_json())

    def dump_json(self, file):
        """Dump this protocol to a file in JSON.

        :param file: A file or file-like to pass to :func:`json.dump`
        """
        return json.dump(self.protocol, file)

    @staticmethod
    def from_json(protocol):
        """Load a pipeline from a JSON object.

        :param list[dict] protocol:
        :return: The pipeline represented by the JSON
        :rtype: Pipeline
        :raises: MissingPipelineFunctionError
        """
        return Pipeline(protocol=protocol)

    @staticmethod
    def from_json_file(file):
        """Load a protocol from JSON contained in file using :meth:`Pipeline.from_json`.

        :return: The pipeline represented by the JSON in the file
        :rtype: Pipeline
        :raises: MissingPipelineFunctionError
        """
        return Pipeline.from_json(json.load(file))

    def __str__(self):
        return json.dumps(self.protocol, indent=2)

    @staticmethod
    def _build_meta(meta, pipelines):
        """
        :param str meta: either union or intersection
        :param iter[Pipeline] pipelines:
        :rtype: Pipeline
        """
        return Pipeline.from_json([{
            'meta': meta,
            'pipelines': [
                pipeline.to_json()
                for pipeline in pipelines
            ]
        }])

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
