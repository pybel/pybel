# -*- coding: utf-8 -*-

"""Utilities for node filters."""

from ...constants import MODIFIER
from ...typing import EdgeData

__all__ = [
    'part_has_modifier',
]


def part_has_modifier(edge_data: EdgeData, part: str, modifier: str) -> bool:
    """Return true if the modifier is in the given subject/object part.

    :param edge_data: PyBEL edge data dictionary
    :param part: either :data:`pybel.constants.SUBJECT` or :data:`pybel.constants.OBJECT`
    :param modifier: The modifier to look for
    """
    part_data = edge_data.get(part)

    if part_data is None:
        return False

    found_modifier = part_data.get(MODIFIER)

    if found_modifier is None:
        return False

    return found_modifier == modifier
