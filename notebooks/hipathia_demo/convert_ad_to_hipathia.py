import os

import pybel


def main():
    graph = pybel.load('alzheimers_grounded.bel.nodelink.json')
    graph.name = 'alzheimers'
    pybel.to_hipathia(graph, os.path.dirname(__file__))


if __name__ == '__main__':
    main()
