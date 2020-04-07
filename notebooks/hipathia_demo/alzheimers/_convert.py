# -*- coding: utf-8 -*-

"""Convert the AD graph for Hipathia."""

import os

import pybel
import pybel.ground

HERE = os.path.dirname(__file__)
PATH = os.path.join(HERE, 'alzheimers.bel.nodelink.json')


def main():
    """Convert the AD graph to Hipathia."""
    graph = pybel.load(PATH)
    graph = pybel.ground.ground_graph(graph)
    pybel.to_hipathia(graph, os.path.dirname(__file__))


if __name__ == '__main__':
    main()
