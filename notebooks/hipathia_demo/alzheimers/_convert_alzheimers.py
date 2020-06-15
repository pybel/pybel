# -*- coding: utf-8 -*-

"""Convert the AD graph for Hipathia."""

import os

import click
from pyobo.cli_utils import verbose_option

import pybel
import pybel.grounding
from pybel.struct import get_subgraphs_by_annotation

HERE = os.path.dirname(__file__)
OUTPUT = os.path.join(HERE, 'output')
os.makedirs(OUTPUT, exist_ok=True)
PATH = os.path.join(HERE, 'alzheimers.bel.nodelink.json')


@click.command()
@verbose_option
def main():
    """Convert the AD graph to Hipathia."""
    graph = pybel.load(PATH)
    graph = pybel.grounding.ground(graph)

    graphs = get_subgraphs_by_annotation(graph, annotation='Subgraph')
    for name, graph in graphs.items():
        graph.name = name
        pybel.to_hipathia(graph, OUTPUT)


if __name__ == '__main__':
    main()
