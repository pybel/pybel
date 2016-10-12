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

import logging
import sys

import click
import py2neo

from . import graph

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
@click.option('--context', help='Context tag for multiple simultaneous neo4j graphs')
def to_neo(path, url, database, neo, context):
    """Parses BEL file and uploads to Neo4J"""

    p2n = py2neo.Graph(neo)
    assert p2n.data('match (n) return count(n) as count')[0]['count'] is not None

    if path:
        g = graph.from_path(path)
    elif url:
        g = graph.from_url(url)
    elif database:
        g = graph.from_database(database)
    else:
        raise ValueError('missing BEL file')

    g.to_neo4j(p2n, context)


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

    g.to_csv(edge_path)


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

    g.to_graphml(output)


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

    g.to_pickle(output)


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

    g.to_json(output)


if __name__ == '__main__':
    main()
