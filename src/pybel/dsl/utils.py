# -*- coding: utf-8 -*-

from .exc import PyBELDSLException
from ..constants import IDENTIFIER, NAME, NAMESPACE


def entity(namespace, name=None, identifier=None):
    """Creates a dictionary representing a reference to an entity

    :param str namespace: The namespace to which the entity belongs
    :param str name: The name of the entity
    :param str identifier: The identifier of the entity in the namespace
    :rtype: dict
    """
    if name is None and identifier is None:
        raise PyBELDSLException('cannot create an entity with neither a name nor identifier')

    rv = {
        NAMESPACE: namespace,
    }

    if name is not None:
        rv[NAME] = name

    if identifier is not None:
        rv[IDENTIFIER] = identifier

    return rv
