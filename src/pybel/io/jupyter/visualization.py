# -*- coding: utf-8 -*-

"""Convert BEL graphs to HTML.

This module provides functions for making HTML visualizations of BEL Graphs. Because the :class:`pybel.BELGraph`
inherits from :class:`networkx.MultiDiGraph`, it can also be visualized using :mod:`networkx`
`library <https://networkx.github.io/documentation/latest/reference/drawing.html>`_.
"""

import json
import os
from typing import Mapping, Optional

from .constants import DEFAULT_COLOR_MAP
from ..jinja_utils import build_template_renderer
from ..nodelink import to_nodelink_jsons
from ...struct import BELGraph

__all__ = [
    'to_html',
    'to_html_file',
    'to_html_path',
]

#: Renders templates from pybel.io.jupyter.templates folder
render_template = build_template_renderer(__file__)


def build_graph_context(graph: BELGraph, color_map: Optional[Mapping[str, str]] = None) -> Mapping:
    """Build the data dictionary to be used by the Jinja templating engine in :py:func:`to_html`.

    :param graph: A BEL graph
    :param color_map: A dictionary from PyBEL internal node functions to CSS color strings like #FFEE00.
                    Defaults to :data:`default_color_map`
    :return: JSON context for rendering
    """
    color_map = DEFAULT_COLOR_MAP if color_map is None else color_map

    return {
        'json': to_nodelink_jsons(graph),
        'cmap': json.dumps(color_map),
        'number_nodes': graph.number_of_nodes(),
        'number_edges': graph.number_of_edges(),
    }


def to_html(graph: BELGraph, color_map: Optional[Mapping[str, str]] = None) -> str:
    """Create an HTML visualization for the given JSON representation of a BEL graph.

    :param graph: A BEL graph
    :param color_map: A dictionary from PyBEL internal node functions to CSS color strings like #FFEE00.
                    Defaults to :data:`default_color_map`
    :return: HTML string representing the graph
    """
    context = build_graph_context(graph, color_map=color_map)
    return render_template('graph_template.html', context=context)


def to_html_file(graph: BELGraph, file, color_map: Optional[Mapping[str, str]] = None) -> None:
    """Write the HTML visualization to a file or file-like.

    :param graph: A BEL graph
    :param color_map: A dictionary from PyBEL internal node functions to CSS color strings like #FFEE00.
                    Defaults to :data:`default_color_map`
    :param file file: A writable file or file-like
    """
    print(to_html(graph, color_map=color_map), file=file)


def to_html_path(graph: BELGraph, path: str, color_map: Optional[Mapping[str, str]] = None) -> None:
    """Write the HTML visualization to a file specified by the file path.

    :param graph: A BEL graph
    :param color_map: A dictionary from PyBEL internal node functions to CSS color strings like #FFEE00.
                    Defaults to :data:`default_color_map`
    :param path: The file path
    """
    with open(os.path.expanduser(path), 'w') as file:
        to_html_file(graph, file, color_map=color_map)
