# -*- coding: utf-8 -*-

__all__ = [
    'get_syntax_errors',
]


def get_syntax_errors(graph):
    """Gets a list of the syntax errors from the BEL script underlying the graph. Uses SyntaxError as a
    stand-in for :exc:`pybel.parser.parse_exceptions.BelSyntaxError`

    :param pybel.BELGraph graph: A BEL graph
    :return: A list of 4-tuples of line number, line text, exception, and annotations present in the parser
    :rtype: list[tuple]
    """
    return [
        (number, line, exc, an)
        for number, line, exc, an in graph.warnings
        if isinstance(exc, SyntaxError)
    ]
