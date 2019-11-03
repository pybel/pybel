# -*- coding: utf-8 -*-

"""This module contains the functions for decorating transformation functions.

A transformation function takes in a :class:`pybel.BELGraph` and either returns None (in-place) or a new
:class:`pybel.BELGraph` (out-of-place).
"""

import logging
from inspect import signature

from .exc import MissingPipelineFunctionError, PipelineNameError

__all__ = [
    'in_place_transformation',
    'uni_in_place_transformation',
    'uni_transformation',
    'transformation',
    'get_transformation',
    'mapped',
    'has_arguments_map',
    'no_arguments_map',
]

logger = logging.getLogger(__name__)

mapped = {}
universe_map = {}
in_place_map = {}
has_arguments_map = {}
no_arguments_map = {}


def _has_arguments(func, universe):
    sig = signature(func)
    return (
        (universe and 3 <= len(sig.parameters))
        or (not universe and 2 <= len(sig.parameters))
    )


def _register_function(name: str, func, universe: bool, in_place: bool):
    """Register a transformation function under the given name.

    :param name: Name to register the function under
    :param func: A function
    :param universe:
    :param in_place:
    :return: The same function, with additional properties added
    """
    if name in mapped:
        mapped_func = mapped[name]
        raise PipelineNameError(
            '{name} is already registered with {func_mod}.{func_name}'.format(
                name=name,
                func_mod=mapped_func.__module__,
                func_name=mapped_func.__name__,
            ),
        )

    mapped[name] = func

    if universe:
        universe_map[name] = func

    if in_place:
        in_place_map[name] = func

    if _has_arguments(func, universe):
        has_arguments_map[name] = func
    else:
        no_arguments_map[name] = func

    return func


def _build_register_function(universe: bool, in_place: bool):  # noqa: D202
    """Build a decorator function to tag transformation functions.

    :param universe: Does the first positional argument of this function correspond to a universe graph?
    :param in_place: Does this function return a new graph, or just modify it in-place?
    """

    def register(func):
        """Tag a transformation function.

        :param func: A function
        :return: The same function, with additional properties added
        """
        return _register_function(func.__name__, func, universe, in_place)

    return register


#: A decorator for functions that modify BEL graphs in-place
in_place_transformation = _build_register_function(universe=False, in_place=True)
#: A decorator for functions that require a "universe" graph and modify BEL graphs in-place
uni_in_place_transformation = _build_register_function(universe=True, in_place=True)
#: A decorator for functions that require a "universe" graph and create new BEL graphs from old BEL graphs
uni_transformation = _build_register_function(universe=True, in_place=False)
#: A decorator for functions that create new BEL graphs from old BEL graphs
transformation = _build_register_function(universe=False, in_place=False)


def get_transformation(name: str):
    """Get a transformation function and error if its name is not registered.

    :param name: The name of a function to look up
    :return: A transformation function
    :raises MissingPipelineFunctionError: If the given function name is not registered
    """
    func = mapped.get(name)

    if func is None:
        raise MissingPipelineFunctionError('{} is not registered as a pipeline function'.format(name))

    return func
