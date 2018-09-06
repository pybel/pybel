# -*- coding: utf-8 -*-

"""Exceptions for the manager."""

from ..constants import LINE
from ..exceptions import PyBELWarning

MSG = "Error adding edge {line_s} to database. Check this line in the file and make sure the citation, " \
      "evidence, and annotations all use valid UTF-8 characters: {source} {target} {key} {data} with " \
      "original error:\n {error}"


class EdgeAddError(PyBELWarning):
    """When there's a problem inserting an edge."""

    def __init__(self, e, u, v, key, data):  # noqa: D107
        super(EdgeAddError, self).__init__(e, u, v, key, data)
        self.error = e
        self.source = u
        self.target = v
        self.key = key
        self.data = data

    def __str__(self):
        line_s = 'from line {} '.format(self.line) if LINE in self.data else ''
        return MSG.format(
            line_s=line_s,
            source=self.source,
            target=self.target,
            key=self.key,
            data=self.data,
            error=self.error,
        )

    @property
    def line(self):
        """Return the BEL script's line on which this error occurred.

        :rtype: str
        """
        return self.data.get(LINE)
