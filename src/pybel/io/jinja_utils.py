# -*- coding: utf-8 -*-

"""Utilities for Jinja2 templating."""

import os

from jinja2 import Environment, FileSystemLoader

__all__ = [
    'render_template',
]


def build_template_environment(here: str) -> Environment:
    """Build a custom templating environment so Flask apps can get data from lots of different places.

    :param here: Give this the result of :code:`os.path.dirname(os.path.abspath(__file__))`
    """
    template_environment = Environment(
        autoescape=True,
        loader=FileSystemLoader(os.path.join(here, 'templates')),
        trim_blocks=False
    )

    template_environment.globals['STATIC_PREFIX'] = here + '/static/'

    return template_environment


def build_template_renderer(file):
    """Build a render template function.

    :param file: The location of the current file. Pass it :code:`__file__` like in the example below.

    >>> render_template = build_template_renderer(__file__)
    """
    here = os.path.dirname(os.path.abspath(file))
    template_environment = build_template_environment(here)

    def render_template_enclosure(template_filename: str, **context) -> str:
        """Render a template as a unicode string.

        :param template_filename: The name of the file to render in the template directory
        :param dict context: The variables to template
        """
        return template_environment.get_template(template_filename).render(context)

    return render_template_enclosure


#: Renders templates from pybel_tools.visualization.templates folder
render_template = build_template_renderer(__file__)
