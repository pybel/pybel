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
import os

import click
import networkx as nx
from py2neo import authenticate, Graph

from .graph import from_url, from_file


@click.group(help="PyBEL Command Line Utilities")
@click.version_option()
def main():
    pass


def get_from_url_or_path(url=None, path=None):
    if url is not None:
        return from_url(url)
    elif path is not None:
        with open(os.path.expanduser(path)) as f:
            return from_file(f)
    raise ValueError('Missing both url and path arguments')


@main.command()
@click.option('--url', help='URL of BEL file')
@click.option('--path', help='File path of BEL file')
@click.option('--neo-url', default='localhost', help='URL of neo4j database')
@click.option('--neo-port', type=int, default=7474, help='Port of neo4j database')
@click.option('--neo-user', default='neo4j', help='User for neo4j database')
@click.option('--neo-pass', default='neo4j', help='Password for neo4j database')
def to_neo(url, path, neo_url, neo_port, neo_user, neo_pass):
    """Parses BEL file and uploads to Neo4J"""
    g = get_from_url_or_path(url, path)

    authenticate('{}:{}'.format(neo_url, neo_port), neo_user, neo_pass)
    p2n = Graph()

    g.to_neo4j(p2n)


@main.command()
@click.option('--url', help='URL of BEL file')
@click.option('--path', help='File path of BEL file')
@click.option('--node-path', help='File path to output node file')
@click.option('--edge-path', help='File path to output edge file')
def to_csv(url, path, node_path, edge_path):
    """Parses BEL file and exports as node/edge list files"""
    g = get_from_url_or_path(url, path)
    nx.write_edgelist(g, edge_path, data=True)

    with open(node_path, 'w') as f:
        json.dump(g.nodes(data=True), f)


if __name__ == '__main__':
    main()
