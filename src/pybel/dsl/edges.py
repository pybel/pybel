# -*- coding: utf-8 -*-

"""Internal DSL functions for edges."""

import warnings
from typing import Dict, Optional, Union

from ..constants import (
    ACTIVITY, CELL_SURFACE, DEGRADATION, EFFECT, EXTRACELLULAR, FROM_LOC, INTRACELLULAR,
    LOCATION, MODIFIER, NAME, NAMESPACE, TO_LOC, TRANSLOCATION,
)
from ..language import Entity, activity_mapping, compartment_mapping

__all__ = [
    'activity',
    'degradation',
    'translocation',
    'secretion',
    'cell_surface_expression',
    'location',
]

ModifierDict = Dict
LocationDict = Dict


def _modifier_helper(
    modifier: str,
    location: Optional[LocationDict] = None,
) -> ModifierDict:
    """Make a modifier dictionary.

    :param modifier: The name of the modifier
    :param location: An entity from :func:`pybel.dsl.entity`
    """
    rv = {
        MODIFIER: modifier,
    }

    if location:
        rv[LOCATION] = location

    return rv


def activity(
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    identifier: Optional[str] = None,
    location: Optional[LocationDict] = None,
) -> ModifierDict:
    """Make a subject/object modifier dictionary.

    :param name: The name of the activity. If no namespace given, uses BEL default namespace
    :param namespace: The namespace of the activity
    :param identifier: The identifier of the name in the database
    :param location: An entity from :func:`pybel.dsl.entity` representing the location of the node
    """
    rv = _modifier_helper(ACTIVITY, location=location)

    if name and not namespace:
        rv[EFFECT] = activity_mapping[name]
    elif not name and not namespace and not identifier:
        rv[EFFECT] = activity_mapping['act']
    else:
        rv[EFFECT] = Entity(
            namespace=namespace,
            name=name,
            identifier=identifier,
        )
    return rv


def degradation(location: Optional[LocationDict] = None) -> ModifierDict:
    """Make a degradation dictionary.

    :param location: An entity from :func:`pybel.dsl.entity` representing the location of the node
    """
    return _modifier_helper(DEGRADATION, location=location)


def translocation(
    from_loc: Union[str, Entity],
    to_loc: Union[str, Entity],
) -> ModifierDict:
    """Make a translocation dictionary.

    :param dict from_loc: An entity dictionary from :func:`pybel.dsl.entity`
    :param dict to_loc: An entity dictionary from :func:`pybel.dsl.entity`
    :rtype: dict
    """
    rv = _modifier_helper(TRANSLOCATION)
    if isinstance(from_loc, str):
        from_loc = compartment_mapping[from_loc]
    if not isinstance(from_loc, Entity):
        raise TypeError
    if isinstance(to_loc, str):
        to_loc = compartment_mapping[to_loc]
    if not isinstance(to_loc, Entity):
        raise TypeError

    rv[EFFECT] = {
        FROM_LOC: from_loc,
        TO_LOC: to_loc,
    }
    return rv


def secretion() -> ModifierDict:
    """Make a secretion translocation dictionary.

    This is a convenient wrapper representing the :func:`translocation` from the intracellular location to the
    extracellular space.
    """
    return translocation(INTRACELLULAR, EXTRACELLULAR)


def cell_surface_expression() -> ModifierDict:
    """Make a cellular surface expression translocation dictionary.

    This is a convenient wrapper representing the :func:`translocation` from the intracellular location to the cell
    surface.
    """
    return translocation(INTRACELLULAR, CELL_SURFACE)


def location(identifier: Entity) -> LocationDict:
    """Make a location object modifier dictionary.

    :param identifier: A namespace/name/identifier pair

    Usage:

    X increases the abundance of Y in the cytoplasm

    .. code-block:: python

        from pybel import BELGraph
        from pybel.dsl import protein, location

        graph = BELGraph()

        source = protein('HGNC', 'IRAK1')
        target = protein('HGNC', 'IRF7, variants=[
            pmod('Ph', 'Ser', 477), pmod('Ph', 'Ser', 479),
        ])
        graph.add_increases(
            source,
            target,
            citation=...,
            evidence=...,
            target_modifier=location(entity(namespace='GO', name='cytosol', identifier='GO:0005829')),
        )

    X increases the kinase activity of Y in the cytoplasm. In this case, the :func:`activity` function takes a location as
    an optional argument.

    .. code-block:: python

        from pybel import BELGraph
        from pybel.dsl import protein, location

        graph = BELGraph()

        source = ...
        target = ...
        graph.add_increases(
            source,
            target,
            citation=...,
            evidence=...,
            target_modifier=activity('kin', location=entity(namespace='GO', name='cytosol', identifier='GO:0005829')),
        )
    """
    return {
        LOCATION: identifier,
    }
