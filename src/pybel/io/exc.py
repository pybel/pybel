# -*- coding: utf-8 -*-

"""Exceptions for input/output."""

from ..exceptions import PyBelWarning

import_version_message_fmt = 'Tried importing from PyBEL v{}. Need at least v{}'


class ImportVersionWarning(PyBelWarning, ValueError):
    """Raised when trying to import data from an old version of PyBEL."""

    def __init__(self, actual_version_tuple, minimum_version_tuple):
        """Build an import version warning.

        :type actual_version_tuple: str
        :type minimum_version_tuple: str
        """
        super(ImportVersionWarning, self).__init__(actual_version_tuple, minimum_version_tuple)
        self.actual_tuple = actual_version_tuple
        self.minimum_tuple = minimum_version_tuple

    def __str__(self):
        actual_s = '.'.join(map(str, self.actual_tuple))
        minimum_s = '.'.join(map(str, self.minimum_tuple))
        return import_version_message_fmt.format(actual_s, minimum_s)
