# -*- coding: utf-8 -*-

"""Convert the Selventa graph for Hipathia."""

import os
from urllib.request import urlretrieve

import pybel
import pybel.grounding

HERE = os.path.dirname(__file__)
URL = 'https://github.com/cthoyt/selventa-knowledge/raw/master/selventa_knowledge/small_corpus.bel.nodelink.json.gz'
PATH = os.path.join(HERE, 'small_corpus.bel.nodelink.json.gz')


def main():
    """Convert the Selventa graph to Hipathia."""
    if not os.path.exists(PATH):
        urlretrieve(URL, PATH)

    graph = pybel.load(PATH)
    graph = pybel.grounding.ground(graph)
    pybel.to_hipathia(graph, HERE)


if __name__ == '__main__':
    main()
