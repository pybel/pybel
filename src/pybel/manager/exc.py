# -*- coding: utf-8 -*-

from ..constants import LINE
from ..exceptions import PyBelWarning


class EdgeAddError(PyBelWarning):
    """When there's a problem inserting an edge"""

    def __init__(self, e, u, v, data):
        super(EdgeAddError, self).__init__(e, u, v, data)
        self.error = e
        self.source = u
        self.target = v
        self.data = data

    def __str__(self):
        line_s = 'from line {} '.format(self.line) if LINE in self.data else ''

        return ("Error adding edge {}to database. Check this line in the file and make sure the citation, "
                "evidence, and annotations all use valid UTF-8 characters: {} {} {} with original error:\n "
                "{}".format(line_s, self.source, self.target, self.data, self.error))

    @property
    def line(self):
        return self.data.get(LINE)
