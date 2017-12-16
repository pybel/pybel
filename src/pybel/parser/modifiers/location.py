# -*- coding: utf-8 -*-

"""

Location data also is added into the information in the edge for the node (subject or object) for which it was
annotated. :code:`p(HGNC:GSK3B, pmod(P, S, 9), loc(GOCC:lysozome)) pos act(p(HGNC:GSK3B), ma(kin))` becomes:

.. code::

    {
        SUBJECT: {
            LOCATION: {
                NAMESPACE: 'GOCC',
                NAME: 'lysozome'
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
        EVIDENCE: '...',
        CITATION: { ... }
    }


The addition of the :code:`location()` element in BEL 2.0 allows for the unambiguous expression of the differences
between the process of hypothetical :code:`HGNC:A` moving from one place to another and the existence of
hypothetical :code:`HGNC:A` in a specific location having different effects. In BEL 1.0, this action had its own node,
but this introduced unnecessary complexity to the network and made querying more difficult.
This calls for thoughtful consideration of the following two statements:

- :code:`tloc(p(HGNC:A), fromLoc(GOCC:intracellular), toLoc(GOCC:"cell membrane")) -> p(HGNC:B)`
- :code:`p(HGNC:A, location(GOCC:"cell membrane")) -> p(HGNC:B)`

.. seealso::

    - BEL 2.0 specification on `cellular location (2.2.4) <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_cellular_location>`_
    - PyBEL module :py:class:`pybel.parser.modifiers.LocationParser`
"""

from pyparsing import Group, Suppress, oneOf

from ..baseparser import BaseParser
from ..parse_identifier import IdentifierParser
from ..utils import nest
from ...constants import LOCATION

__all__ = [
    'location_tag',
    'LocationParser',
]

location_tag = Suppress(oneOf(['loc', 'location']))


class LocationParser(BaseParser):
    def __init__(self, identifier_parser=None):
        """
        :param IdentifierParser identifier_parser: An identifier parser for checking the 3P and 5P partners
        """
        identifier_parser = identifier_parser if identifier_parser is not None else IdentifierParser()
        super(LocationParser, self).__init__(Group(location_tag + nest(identifier_parser.language))(LOCATION))
