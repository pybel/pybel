# -*- coding: utf-8 -*-

"""Convert the HemeKG for Hipathia."""

import os
from urllib.request import urlretrieve

import click
from pyobo.cli_utils import verbose_option

import pybel
import pybel.grounding

HERE = os.path.dirname(__file__)
URL = 'https://github.com/hemekg/hemekg/raw/master/hemekg/_cache.bel.nodelink.json'
PATH = os.path.join(HERE, 'hemekg.bel.nodelink.json')


@click.command()
@verbose_option
def main():
    """Convert the HemeKG graph to Hipathia."""
    if not os.path.exists(PATH):
        urlretrieve(URL, PATH)

    graph = pybel.load(PATH)
    graph = pybel.grounding.ground(graph)
    pybel.to_hipathia(graph, HERE)


if __name__ == '__main__':
    main()
