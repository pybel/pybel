# -*- coding: utf-8 -*-

from .utils import add_identifier
from ..constants import *

__all__ = [
    'protein',
    'complex_abundance',
]


def _make_abundance(func, name, namespace, identifier=None):
    rv = {FUNCTION: func}
    add_identifier(rv, name=name, namespace=namespace, identifier=identifier)
    return rv


def protein(name, namespace, identifier=None):
    """Returns the node data dictionary for a protein

    :param str name: The database's preferred name or label for this protein
    :param str namespace: The name of the database used to identify this protein
    :param str identifier: The database's identifier for this protein
    :rtype: dict
    """
    return _make_abundance(PROTEIN, name=name, namespace=namespace, identifier=identifier)


def abundance(name, namespace, identifier=None):
    """Returns the node data dictionary for an abundance

    :param str name: The database's preferred name or label for this abundance
    :param str namespace: The name of the database used to identify this abundance
    :param str identifier: The database's identifier for this abundance
    :rtype: dict
    """
    return _make_abundance(ABUNDANCE, name=name, namespace=namespace, identifier=identifier)


def complex_abundance(members, name=None, namespace=None, identifier=None):
    """Returns the node data dictionary for a protein complex

    :param list[dict] members: A list of PyBEL node data dictionaries
    :param str name: The name of the complex
    :param str namespace: The namespace from which the name originates
    :param str identifier: The identifier in the namespace in which the name originates
    :rtype: dict
    """
    rv = {
        FUNCTION: COMPLEX,
        MEMBERS: members
    }

    if namespace and name:
        add_identifier(rv, name=name, namespace=namespace, identifier=identifier)

    return rv


def fusion_range(reference, start, stop):
    return {
        FUSION_REFERENCE: reference,
        FUSION_START: start,
        FUSION_STOP: stop

    }


def fusion(func, partner_5p, range_5p, partner_3p, range_3p):
    """

    :param str func: A PyBEL function
    :param dict partner_5p: A PyBEL node data dictionary
    :param dict range_5p:
    :param dict partner_3p: A fusion range produced by :func:`fusion_range`
    :param dict range_3p: A fusion range produced by :func:`fusion_range`
    :return:
    """
    return {
        FUNCTION: func,
        FUSION: {
            PARTNER_5P: partner_5p,
            PARTNER_3P: partner_3p,
            RANGE_5P: range_5p,
            RANGE_3P: range_3p
        }
    }
