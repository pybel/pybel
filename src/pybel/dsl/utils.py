# -*- coding: utf-8 -*-

from ..constants import *


def add_identifier(rv, namespace, name, identifier=None):
    """Adds identifier information to the given dict"""
    rv[NAMESPACE] = namespace
    rv[NAME] = name

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
