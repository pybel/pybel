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
import logging
import sys

import click
import networkx as nx
import py2neo
from networkx.readwrite import json_graph

from . import graph
from .parser.utils import flatten_edges

log = logging.getLogger(__name__)


@click.group(help="PyBEL Command Line Utilities")
@click.version_option()
def main():
    pass


@main.command()
@click.option('--path', help='BEL file file path')
@click.option('--url', help='BEL file URL')
@click.option('--database', help='BEL database')
@click.option('--neo', help='URL of neo4j database')
def to_neo(path, url, database, neo):
    """Parses BEL file and uploads to Neo4J"""
    if path:
        g = graph.from_path(path)
    elif url:
        g = graph.from_url(url)
    elif database:
        g = graph.from_database(database)
    else:
        raise ValueError('missing BEL file')

    p2n = py2neo.Graph(neo)
    g.to_neo4j(p2n)


# FIXME
@main.command()
@click.option('--path', help='BEL file file path')
@click.option('--url', help='BEL file URL')
@click.option('--database', help='BEL database')
@click.option('--edge-path', help='File path to output edge file')
def to_csv(path, url, database, edge_path):
    """Parses BEL file and exports as edge list files"""
    if path:
        g = graph.from_path(path)
    elif url:
        g = graph.from_url(url)
    elif database:
        g = graph.from_database(database)
    else:
        raise ValueError('missing BEL file')

    h = flatten_edges(g)
    nx.write_edgelist(h, edge_path, data=True)


@main.command()
@click.option('--path', help='BEL file file path')
@click.option('--url', help='BEL file URL')
@click.option('--database', help='BEL database')
@click.option('--output', default=sys.stdout)
def to_graphml(path, url, database, output):
    """Parses BEL file and exports as GraphML file"""
    if path:
        g = graph.from_path(path)
    elif url:
        g = graph.from_url(url)
    elif database:
        g = graph.from_database(database)
    else:
        raise ValueError('missing BEL file')

    nx.write_graphml(flatten_edges(g), output)


@main.command()
@click.option('--path', help='BEL file file path')
@click.option('--url', help='BEL file URL')
@click.option('--database', help='BEL database')
@click.option('--output', default=sys.stdout)
def to_pickle(path, url, database, output):
    """Parses BEL file and exports as pickled python object"""
    if path:
        log.info('loading graph from path for picking')
        g = graph.from_path(path)
    elif url:
        g = graph.from_url(path)
    elif database:
        g = graph.from_database(path)
    else:
        raise ValueError('missing BEL file')

    nx.write_gpickle(flatten_edges(g), output)


@main.command()
@click.option('--path', help='BEL file file path')
@click.option('--url', help='BEL file URL')
@click.option('--database', help='BEL database')
@click.option('--output', type=click.File('w'), default=sys.stdout)
def to_json(path, url, database, output):
    """Parses BEL file and exports as node-link json"""
    if path:
        g = graph.from_path(path)
    elif url:
        g = graph.from_url(path)
    elif database:
        g = graph.from_database(path)
    else:
        raise ValueError('missing BEL file')

    data = json_graph.node_link_data(flatten_edges(g))
    json.dump(data, output, ensure_ascii=False)


if __name__ == '__main__':
    main()
