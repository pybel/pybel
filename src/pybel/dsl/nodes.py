# -*- coding: utf-8 -*-

from .utils import add_identifier
from ..constants import *

__all__ = [
    'protein',
    'protein_complex',
]


def protein(name, namespace, identifier=None):
    """Returns the node data dictionary for a protein

    :param str name: The database's preferred name or label for this protein
    :param str namespace: The name of the database used to identify this protein
    :param str identifier: The database's identifier for this protein
    :rtype: dict
    """
    rv = {
        FUNCTION: PROTEIN,
    }

    add_identifier(rv, namespace, name, identifier=identifier)

    return rv


def protein_complex(proteins, name=None, namespace=None, identifier=None):
    """Returns the node data dictionary for a protein complex

    :param list[dict] proteins:
    :param str name: The name of the complex
    :param str namespace: The namespace from which the name originates
    :param str identifier: The identifier in the namespace in which the name originates
    :rtype: dict
    """
    rv = {
        FUNCTION: COMPLEX,
        MEMBERS: proteins
    }

    if namespace and name:
        add_identifier(rv, namespace, name, identifier=identifier)

    return rv
