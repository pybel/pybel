# -*- coding: utf-8 -*-

"""Convert the HemeKG for Hipathia."""

import os
from urllib.request import urlretrieve

import pybel
import pybel.ground

HERE = os.path.dirname(__file__)
URL = 'https://github.com/hemekg/hemekg/raw/master/hemekg/_cache.bel.nodelink.json'
PATH = os.path.join(HERE, 'hemekg.bel.nodelink.json')


def main():
    """Convert the HemeKG graph to Hipathia."""
    if not os.path.exists(PATH):
        urlretrieve(URL, PATH)

    graph = pybel.load(PATH)
    graph = pybel.ground.ground_graph(graph)
    pybel.to_hipathia(graph, os.path.dirname(__file__))


if __name__ == '__main__':
    main()
