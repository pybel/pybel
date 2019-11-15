# -*- coding: utf-8 -*-

"""Utilities for displaying graphs with inline HTML in Jupyter Notebooks."""

from random import sample
from typing import Mapping, Optional

from IPython.display import Javascript

from .constants import DEFAULT_COLOR_MAP
from ..jinja_utils import build_template_renderer
from ..nodelink import to_nodelink_jsons
from ...struct import BELGraph

__all__ = [
    'to_jupyter',
    'to_jupyter_str'
]

DEFAULT_WIDTH = 1000
DEFAULT_HEIGHT = 650

#: Renders templates from pybel.io.jupyter.templates folder
render_template = build_template_renderer(__file__)


def _generate_id() -> str:
    """Generate a random string of letters."""
    return "".join(sample('abcdefghjkmopqrstuvqxyz', 16))


def to_jupyter(
    graph: BELGraph,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    color_map: Optional[Mapping[str, str]] = None,
) -> Javascript:
    """Display a BEL graph inline in a Jupyter notebook.

    To use successfully, make run as the last statement in a cell inside a Jupyter notebook.

    :param graph: A BEL graph
    :param width: The width of the visualization window to render
    :param height: The height of the visualization window to render
    :param color_map: A dictionary from PyBEL internal node functions to CSS color strings like #FFEE00. Defaults
                    to :data:`default_color_map`
    :return: An IPython notebook Javascript object
    :rtype: :class:`IPython.display.Javascript`
    """
    return Javascript(to_jupyter_str(
        graph,
        width=width,
        height=height,
        color_map=color_map,
    ))


def to_jupyter_str(
    graph: BELGraph,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    color_map: Optional[Mapping[str, str]] = None,
) -> str:
    """Return the string to be javascript-ified by the Jupyter notebook function :class:`IPython.display.Javascript`.

    :param graph: A BEL graph
    :param width: The width of the visualization window to render
    :param height: The height of the visualization window to render
    :param color_map: A dictionary from PyBEL internal node functions to CSS color strings like #FFEE00. Defaults
                    to :data:`default_color_map`
    :return: The javascript string to turn into magic
    """
    gjson = to_nodelink_jsons(graph)
    chart_id = _generate_id()

    return render_template(
        'pybel_jupyter.js',
        graph=gjson,
        chart=chart_id,
        width=width,
        height=height,
        color_map=(color_map or DEFAULT_COLOR_MAP),
    )
