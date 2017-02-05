# -*- coding: utf-8 -*-

"""
Locations
~~~~~~~~~

Location data also is added into the information in the edge for the node (subject or object) for which it was
annotated. :code:`p(HGNC:GSK3B, pmod(P, S, 9), loc(GOCC:lysozome)) pos act(p(HGNC:GSK3B), ma(kin))` becomes:

.. code::

    {
        'subject': {
            'function': 'Protein',
            'identifier': 'identifier': {
                    'namespace': 'HGNC',
                    'name': 'GSK3B'
            },
            'variants': [
                {
                    'kind': 'pmod',
                    'code': 'Ser',
                    'identifier': {
                        'name': 'Ph',
                        'namespace': 'PYBEL'
                    },
                    'pos': 9
                }
            ],
            'location': {
                'namespace': 'GOCC',
                'name': 'lysozome'
            }
        },
        'relation': 'positiveCorrelation',
        'object': {
            'modifier': 'Activity',
            'target': {
                'function': 'Protein',
                'identifier': {
                    'namespace': 'HGNC',
                    'name': 'GSK3B'
                }
            },
            'effect': {
                'name': 'kin',
                'namespace': 'PYBEL'
            }
        },
    }

.. seealso:: 2.2.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_cellular_location
"""

from pyparsing import Suppress, oneOf, Group

from ..baseparser import BaseParser, nest
from ..parse_identifier import IdentifierParser
from ...constants import LOCATION


class LocationParser(BaseParser):
    def __init__(self, identifier_parser=None):
        """
        :param identifier_parser:
        :type identifier_parser: IdentifierParser
        :return:
        """
        self.identifier_parser = identifier_parser if identifier_parser is not None else IdentifierParser()
        identifier = self.identifier_parser.get_language()
        location_tag = Suppress(oneOf(['loc', 'location']))
        self.language = Group(location_tag + nest(identifier))(LOCATION)

    def get_language(self):
        return self.language
