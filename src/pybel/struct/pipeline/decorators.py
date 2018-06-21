# -*- coding: utf-8 -*-

"""This module contains the functions for decorating transformation functions.

A transformation function takes in a :class:`pybel.BELGraph` and either returns None (in-place) or a new
:class:`pybel.BELGraph` (out-of-place).
"""

from .exc import MissingPipelineFunctionError

try:
    from inspect import signature
except ImportError:
    from funcsigs import signature

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

mapped = {}
universe_map = {}
in_place_map = {}
has_arguments_map = {}
no_arguments_map = {}


def _has_arguments(func, universe):
    sig = signature(func)
    return (
            (universe and 3 <= len(sig.parameters)) or
            (not universe and 2 <= len(sig.parameters))
    )


def _register(universe, in_place):
    """Build a decorator function to tag transformation functions.

    :param bool universe: Does the first positional argument of this function correspond to a universe graph?
    :param bool in_place: Does this function return a new graph, or just modify it in-place?
    """

    def decorator(func):
        """Tag a transformation function.

        :param func: A function
        :return: The same function, with additional properties added
        """
        mapped[func.__name__] = func

        if universe:
            universe_map[func.__name__] = func

        if in_place:
            in_place_map[func.__name__] = func

        if _has_arguments(func, universe):
            has_arguments_map[func.__name__] = func
        else:
            no_arguments_map[func.__name__] = func

        return func

    return decorator


#: A function decorator to inform the Pipeline how to handle a function
in_place_transformation = _register(universe=False, in_place=True)
#: A function decorator to inform the Pipeline how to handle a function
uni_in_place_transformation = _register(universe=True, in_place=True)
#: A function decorator to inform the Pipeline how to handle a function
uni_transformation = _register(universe=True, in_place=False)
#: A function decorator to inform the Pipeline how to handle a function
transformation = _register(universe=False, in_place=False)


def get_transformation(name):
    """Get a transformation function and error if its name is not registered.

    :param str name:
    :return: A transformation function
    :raises: MissingPipelineFunctionError
    """
    func = mapped.get(name)

    if func is None:
        raise MissingPipelineFunctionError('{} is not registered as a pipeline function'.format(name))

    return func
