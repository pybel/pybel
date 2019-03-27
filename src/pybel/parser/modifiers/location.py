# -*- coding: utf-8 -*-

"""Locations.

Location data also is added into the information in the edge for the node (subject or object) for which it was
annotated. :code:`p(HGNC:GSK3B, pmod(P, S, 9), loc(GO:lysozome)) pos act(p(HGNC:GSK3B), ma(kin))` becomes:

.. code-block:: python

    from pybel.constants import *

    {
        SUBJECT: {
            LOCATION: {
                NAMESPACE: 'GO',
                NAME: 'lysozome',
            }
        },
        RELATION: POSITIVE_CORRELATION,
        OBJECT: {
            MODIFIER: ACTIVITY,
            EFFECT: {
                NAMESPACE: BEL_DEFAULT_NAMESPACE
                NAME: 'kin',
            }
        },
        EVIDENCE: ...,
        CITATION: { ... },
    }


The addition of the :code:`location()` element in BEL 2.0 allows for the unambiguous expression of the differences
between the process of hypothetical :code:`HGNC:A` moving from one place to another and the existence of
hypothetical :code:`HGNC:A` in a specific location having different effects. In BEL 1.0, this action had its own node,
but this introduced unnecessary complexity to the network and made querying more difficult.
This calls for thoughtful consideration of the following two statements:

- :code:`tloc(p(HGNC:A), fromLoc(GO:intracellular), toLoc(GO:"cell membrane")) -> p(HGNC:B)`
- :code:`p(HGNC:A, location(GO:"cell membrane")) -> p(HGNC:B)`

.. seealso::

    - BEL 2.0 specification on `cellular location (2.2.4) <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_cellular_location>`_
    - PyBEL module :py:class:`pybel.parser.modifiers.get_location_language`
"""

from pyparsing import Group, ParserElement, Suppress, oneOf

from ..utils import nest
from ...constants import LOCATION

__all__ = [
    'get_location_language',
]

location_tag = Suppress(oneOf(['loc', 'location']))


def get_location_language(identifier: ParserElement) -> ParserElement:
    """Build a location parser."""
    return Group(
        location_tag +
        nest(identifier)
    )(LOCATION)
