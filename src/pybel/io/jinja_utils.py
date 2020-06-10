# -*- coding: utf-8 -*-

"""Utilities for Jinja2 templating."""

import os

__all__ = [
    'build_template_environment',
    'build_template_renderer',
]


def build_template_environment(here: str):
    """Build a custom templating environment so Flask apps can get data from lots of different places.

    :param here: Give this the result of :code:`os.path.dirname(os.path.abspath(__file__))`
    :rtype: jinja2.Environment
    """
    from jinja2 import Environment, FileSystemLoader

    loader = FileSystemLoader(os.path.join(here, 'templates'))
    environment = Environment(
        autoescape=True,
        loader=loader,
        trim_blocks=False,
    )
    environment.globals['STATIC_PREFIX'] = here + '/static/'
    return environment


def build_template_renderer(path: str):
    """Build a render template function.

    :param path: The location of the current file. Pass it :code:`__file__` like in the example below.

    >>> render_template = build_template_renderer(__file__)
    """
    here = os.path.dirname(os.path.abspath(path))
    template_environment = build_template_environment(here)

    def render_template_enclosure(template_filename: str, **context) -> str:
        """Render a template as a unicode string.

        :param template_filename: The name of the file to render in the template directory
        :param dict context: The variables to template
        """
        return template_environment.get_template(template_filename).render(context)

    render_template_enclosure.environment = template_environment
    return render_template_enclosure
