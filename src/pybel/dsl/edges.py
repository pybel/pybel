# -*- coding: utf-8 -*-

"""Internal DSL functions for edges."""

from typing import Dict, Optional, Union

from ..constants import (
    ACTIVITY, BEL_DEFAULT_NAMESPACE, CELL_SURFACE, DEGRADATION, EFFECT, EXTRACELLULAR, FROM_LOC, INTRACELLULAR,
    LOCATION, MODIFIER, TO_LOC, TRANSLOCATION,
)
from ..language import Entity

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
    :param Optional[dict] location: An entity from :func:`pybel.dsl.entity`
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

    :param str name: The name of the activity. If no namespace given, uses BEL default namespace
    :param Optional[str] namespace: The namespace of the activity
    :param Optional[str] identifier: The identifier of the name in the database
    :param Optional[dict] location: An entity from :func:`pybel.dsl.entity` representing the location of the node
    """
    rv = _modifier_helper(ACTIVITY, location=location)

    if name or (namespace and identifier):
        rv[EFFECT] = Entity(
            namespace=(namespace or BEL_DEFAULT_NAMESPACE),
            name=name,
            identifier=identifier,
        )

    return rv


def degradation(location: Optional[LocationDict] = None) -> ModifierDict:
    """Make a degradation dictionary.

    :param Optional[dict] location: An entity from :func:`pybel.dsl.entity` representing the location of the node
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
    rv[EFFECT] = {
        FROM_LOC: Entity(namespace=BEL_DEFAULT_NAMESPACE, name=from_loc) if isinstance(from_loc, str) else from_loc,
        TO_LOC: Entity(namespace=BEL_DEFAULT_NAMESPACE, name=to_loc) if isinstance(to_loc, str) else to_loc,
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
            object_modifier=location(entity(namespace='GO', name='cytosol', identifier='GO:0005829')),
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
            object_modifier=activity('kin', location=entity(namespace='GO', name='cytosol', identifier='GO:0005829')),
        )
    """
    return {
        LOCATION: identifier,
    }
