# -*- coding: utf-8 -*-

from ...constants import MODIFIER

__all__ = ['part_has_modifier']


def part_has_modifier(data, part, modifier):
    """Returns true if the modifier is in the given subject/object part

    :param dict data: A PyBEL edge data dictionary
    :param str part: either :data:`pybel.constants.SUBJECT` or :data:`pybel.constants.OBJECT`
    :param modifier: The modifier to look for
    :rtype: bool
    """
    part_data = data.get(part)

    if part_data is None:
        return False

    found_modifier = part_data.get(MODIFIER)

    if found_modifier is None:
        return False

    return found_modifier == modifier
