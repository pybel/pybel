# -*- coding: utf-8 -*-

"""Utilities for the internal DSL."""

from .exc import PyBELDSLException
from ..constants import BEL_DEFAULT_NAMESPACE, IDENTIFIER, NAME, NAMESPACE
from ..utils import ensure_quotes


class entity(dict):
    """Represents a named entity with a namespace and name/identifier."""

    def __init__(self, namespace, name=None, identifier=None):
        """Create a dictionary representing a reference to an entity.

        :param str namespace: The namespace to which the entity belongs
        :param str name: The name of the entity
        :param str identifier: The identifier of the entity in the namespace
        :rtype: dict
        """
        if name is None and identifier is None:
            raise PyBELDSLException('cannot create an entity with neither a name nor identifier')

        super(entity, self).__init__({
            NAMESPACE: namespace,
        })

        if name is not None:
            self[NAME] = name

        if identifier is not None:
            self[IDENTIFIER] = identifier

    def __str__(self):
        if self[NAMESPACE] == BEL_DEFAULT_NAMESPACE:
            return self[NAME]

        return '{}:{}'.format(self[NAMESPACE], ensure_quotes(self[NAME]))
