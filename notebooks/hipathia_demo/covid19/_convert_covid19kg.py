# -*- coding: utf-8 -*-

"""Convert the COVID-19 graph for Hipathia."""

import os
from urllib.request import urlretrieve

import pybel
import pybel.ground

HERE = os.path.dirname(__file__)
URL = 'https://github.com/covid19kg/covid19kg/raw/master/covid19kg/_cache.bel.nodelink.json'
PATH = os.path.join(HERE, 'covid19.bel.nodelink.json')


def main():
    """Convert the COVID-19 graph to Hipathia."""
    if not os.path.exists(PATH):
        urlretrieve(URL, PATH)

    graph = pybel.load(PATH)
    graph = pybel.ground.ground_graph(graph)
    pybel.to_hipathia(graph, os.path.dirname(__file__))


if __name__ == '__main__':
    main()
