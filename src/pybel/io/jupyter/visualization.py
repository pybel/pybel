# -*- coding: utf-8 -*-

"""Convert BEL graphs to HTML.

This module provides functions for making HTML visualizations of BEL Graphs. Because the :class:`pybel.BELGraph`
inherits from :class:`networkx.MultiDiGraph`, it can also be visualized using :mod:`networkx`
`library <https://networkx.github.io/documentation/latest/reference/drawing.html>`_.
"""

import json
from typing import Mapping, Optional, TextIO, Union

from networkx.utils import open_file

from .constants import DEFAULT_COLOR_MAP
from ..jinja_utils import build_template_renderer
from ..nodelink import to_nodelink_jsons
from ...struct import BELGraph

__all__ = [
    'to_html',
    'to_html_file',
]

#: Renders templates from pybel.io.jupyter.templates folder
render_template = build_template_renderer(__file__)


def to_html(graph: BELGraph, color_map: Optional[Mapping[str, str]] = None) -> str:
    """Create an HTML visualization for the given JSON representation of a BEL graph.

    :param graph: A BEL graph
    :param color_map: A dictionary from PyBEL internal node functions to CSS color strings like #FFEE00.
                    Defaults to :data:`default_color_map`
    :return: HTML string representing the graph
    """
    color_map = DEFAULT_COLOR_MAP if color_map is None else color_map
    return render_template(
        'graph_template.html',
        graph=to_nodelink_jsons(graph),
        color_map=json.dumps(color_map),
        number_nodes=graph.number_of_nodes(),
        number_edges=graph.number_of_edges(),
    )


@open_file(1, mode='w')
def to_html_file(
    graph: BELGraph,
    file: Union[str, TextIO],
    color_map: Optional[Mapping[str, str]] = None,
) -> None:
    """Write the HTML visualization to a file or file-like.

    :param graph: A BEL graph
    :param color_map: A dictionary from PyBEL internal node functions to CSS color strings like #FFEE00.
                    Defaults to :data:`default_color_map`
    :param file file: A writable file or file-like or file path
    """
    print(to_html(graph, color_map=color_map), file=file)
