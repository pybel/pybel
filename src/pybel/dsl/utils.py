# -*- coding: utf-8 -*-

from ..constants import *


def entity(name, namespace, identifier=None):
    """Creates a dictionary representing a reference to an entity

    :param str name: The name of the entity
    :param str namespace: The namespace to which the entity belongs
    :param str identifier: The identifier of the entity in the namespace
    :rtype: dict
    """
    rv = {
        NAME: name,
        NAMESPACE: namespace,
    }

    if identifier is not None:
        rv[ID] = identifier

    return rv


def add_identifier(rv, name, namespace, identifier=None):
    """Adds identifier information to the given dict"""
    rv[NAME] = name
    rv[NAMESPACE] = namespace

    if identifier:
        rv[ID] = identifier


def make_translocation_modifier_dict(from_loc, to_loc):
    """Makes a translocation dict

    :param dict from_loc:
    :param dict to_loc:
    :rtype: dict
    """
    return {
        MODIFIER: TRANSLOCATION,
        EFFECT: {
            FROM_LOC: from_loc,
            TO_LOC: to_loc
        }
    }
