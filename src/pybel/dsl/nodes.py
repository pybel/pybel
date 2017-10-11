# -*- coding: utf-8 -*-

from ..constants import *

__all__ = [
    'protein',
    'protein_complex',
]


def _add_identifier(rv, namespace, name, identifier=None):
    rv[NAMESPACE] = namespace
    rv[NAME] = name

    if identifier:
        rv[ID] = identifier


def protein(namespace, name, identifier=None): # TODO make name first, and namespace default to HGNC
    """Returns the node data dictionary for a protein

    :param str namespace: The name of the database used to identify this protein
    :param str name: The database's preferred name or label for this protein
    :param str identifier: The database's identifier for this protein
    :rtype: dict
    """
    rv = {
        FUNCTION: PROTEIN,
    }

    _add_identifier(rv, namespace, name, identifier=identifier)

    return rv


def protein_complex(proteins, namespace=None, name=None, identifier=None):
    """Returns the node data dictionary for a protein complex

    :param list[dict] proteins:
    :param str namespace:
    :param str name:
    :param str identifier:
    :rtype: dict
    """
    rv = {
        FUNCTION: COMPLEX,
        MEMBERS: proteins
    }

    if namespace and name:
        _add_identifier(rv, namespace, name, identifier=identifier)

    return rv
