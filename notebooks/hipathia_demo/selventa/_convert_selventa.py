# -*- coding: utf-8 -*-

"""Convert the Selventa graph for Hipathia."""

import os
from urllib.request import urlretrieve

import click
from pyobo.cli_utils import verbose_option

import pybel
import pybel.grounding

HERE = os.path.dirname(__file__)
URL = 'https://github.com/cthoyt/selventa-knowledge/raw/master/selventa_knowledge/small_corpus.bel.nodelink.json.gz'
PATH = os.path.join(HERE, 'small_corpus.bel.nodelink.json.gz')
GROUNDED_PATH = os.path.join(HERE, 'small_corpus-grounded.bel.nodelink.json.gz')


@click.command()
@verbose_option
def main():
    """Convert the Selventa graph to Hipathia."""
    if not os.path.exists(PATH):
        urlretrieve(URL, PATH)
    if not os.path.exists(GROUNDED_PATH):
        graph = pybel.load(PATH)
        graph = pybel.grounding.ground(graph)
        pybel.dump(graph, GROUNDED_PATH)
    else:
        graph = pybel.load(GROUNDED_PATH)
    pybel.to_hipathia(graph, HERE)


if __name__ == '__main__':
    main()
