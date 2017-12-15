"""
Add stuff to edges
"""

from .utils import entity
from ..constants import ACTIVITY, BEL_DEFAULT_NAMESPACE, DEGRADATION, EFFECT, FROM_LOC, MODIFIER, TO_LOC, TRANSLOCATION

__all__ = [
    'activity',
    'degradation',
    'translocation',
    'secretion',
    'cell_surface_expression',
]


def activity(name=None, namespace=None, identifier=None):
    """Makes a subject/object modifier dictionary

    :param str name: The name of the activity. If no namespace given, uses BEL default namespace
    :param Optional[str] namespace: The namespace of the activity
    :param Optional[str] identifier: The identifier of the name in the database
    :rtype: dict
    """
    rv = {MODIFIER: ACTIVITY}

    if name or (namespace and identifier):
        rv[EFFECT] = entity(
            namespace=(namespace or BEL_DEFAULT_NAMESPACE),
            name=name,
            identifier=identifier
        )

    return rv


def degradation():
    """Adds the degradation

    :rtype: dict
    """
    return {MODIFIER: DEGRADATION}


def translocation(from_loc, to_loc):
    """Makes a translocation dict

    :param dict from_loc: An entity dictionary from :func:`pybel.dsl.entity`
    :param dict to_loc: An entity dictionary from :func:`pybel.dsl.entity`
    :rtype: dict
    """
    return {
        MODIFIER: TRANSLOCATION,
        EFFECT: {
            FROM_LOC: from_loc,
            TO_LOC: to_loc
        }
    }


def secretion():
    raise NotImplementedError


def cell_surface_expression():
    raise NotImplementedError
