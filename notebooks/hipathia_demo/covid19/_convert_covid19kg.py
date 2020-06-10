# -*- coding: utf-8 -*-

"""Convert the COVID-19 graph for Hipathia."""

import os
from urllib.request import urlretrieve

import click
from pyobo.cli_utils import verbose_option

import pybel
import pybel.grounding

HERE = os.path.dirname(__file__)
URL = 'https://github.com/covid19kg/covid19kg/raw/master/covid19kg/_cache.bel.nodelink.json'
PATH = os.path.join(HERE, 'covid19.bel.nodelink.json')
GROUNDED_PATH = os.path.join(HERE, 'covid19-grounded.bel.nodelink.json')


@click.command()
@verbose_option
def main():
    """Convert the COVID-19 graph to Hipathia."""
    if not os.path.exists(PATH):
        urlretrieve(URL, PATH)
    if not os.path.exists(GROUNDED_PATH):
        graph = pybel.load(PATH)
        graph = pybel.grounding.ground(graph)
        pybel.dump(graph, GROUNDED_PATH, indent=2)
    else:
        graph = pybel.load(GROUNDED_PATH)
    pybel.to_hipathia(graph, HERE)


if __name__ == '__main__':
    main()
