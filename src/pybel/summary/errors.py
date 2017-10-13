# -*- coding: utf-8 -*-

from ..parser.parse_exceptions import BelSyntaxError

__all__ = [
    'get_syntax_errors',
]


def get_syntax_errors(graph):
    """Gets only the syntax errors from the graph

    :param pybel.BELGraph graph:
    :rtype: list[tuple]
    """
    return [
        (number, line, exc, an)
        for number, line, exc, an in graph.warnings
        if isinstance(exc, BelSyntaxError)
    ]
