# -*- coding: utf-8 -*-

"""Convert the AD graph for Hipathia."""

import os

import pybel
import pybel.ground
from pybel.struct import get_subgraphs_by_annotation

HERE = os.path.dirname(__file__)
PATH = os.path.join(HERE, 'alzheimers.bel.nodelink.json')


def main():
    """Convert the AD graph to Hipathia."""
    graph = pybel.load(PATH)
    graph = pybel.ground.ground_graph(graph)

    graphs = get_subgraphs_by_annotation(graph, annotation='Subgraph')
    for name, graph in graphs.items():
        graph.name = name
        pybel.to_hipathia(graph, HERE)


if __name__ == '__main__':
    main()
