"""
Module that contains the command line app

Why does this file exist, and why not put this in __main__?
You might be tempted to import things from __main__ later, but that will cause
problems--the code will get executed twice:
 - When you run `python -m pybel` python will execute
   ``__main__.py`` as a script. That means there won't be any
   ``pybel.__main__`` in ``sys.modules``.
 - When you import __main__ it will get executed again (as a module) because
   there's no ``pybel.__main__`` in ``sys.modules``.
Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

import json

import click
import networkx as nx
import py2neo

from .graph import from_bel


@click.group(help="PyBEL Command Line Utilities")
@click.version_option()
def main():
    pass


@main.command()
@click.option('--path', help='BEL file')
@click.option('--neo', help='URL of neo4j database')
def to_neo(path, neo):
    """Parses BEL file and uploads to Neo4J"""
    print(neo)
    p2n = py2neo.Graph(neo)

    g = from_bel(path)
    g.to_neo4j(p2n)


@main.command()
@click.option('--path', help='Path of BEL file (url or local)')
@click.option('--node-path', help='File path to output node file')
@click.option('--edge-path', help='File path to output edge file')
def to_csv(url, path, node_path, edge_path):
    """Parses BEL file and exports as node/edge list files"""
    g = from_bel(path)

    nx.write_edgelist(g, edge_path, data=True)

    with open(node_path, 'w') as f:
        json.dump(g.nodes(data=True), f)


if __name__ == '__main__':
    main()
