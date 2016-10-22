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
import os
import time

import click
import py2neo

from . import graph
from .manager.namespace_cache import NamespaceCache

log = logging.getLogger('pybel')

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)


@click.group(help="PyBEL Command Line Utilities")
@click.version_option()
def main():
    pass


@main.command()
@click.option('--path', help='BEL file file path')
@click.option('--url', help='BEL file URL')
@click.option('--database', help='BEL database')
@click.option('--csv', help='Path for CSV output')
@click.option('--graphml', help='Path for GraphML output. Use .graphml for Cytoscale')
@click.option('--json', type=click.File('w'), help='Path for Node-Link JSON output')
@click.option('--pickle', help='Path for NetworkX gpickle output')
@click.option('--lenient', is_flag=True, help="Enable lenient parsing")
@click.option('--log-file', help="Optional path for verbose log output")
@click.option('-v', '--verbose', count=True)
def convert(path, url, database, csv, graphml, json, pickle, lenient, log_file, verbose):
    """Options for multiple outputs/conversions"""

    if verbose == 1:
        ch.setLevel(logging.DEBUG)
    elif verbose >= 2:
        ch.setLevel(5)
    else:
        ch.setLevel(logging.INFO)

    log.addHandler(ch)

    if log_file:
        log_path = os.path.expanduser(log_file)
        log.info('Logging output to {}'.format(log_path))
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        log.addHandler(fh)

    if path:
        g = graph.from_path(path, lenient=lenient)
    elif url:
        g = graph.from_url(url, lenient=lenient)
    elif database:
        g = graph.from_database(database)
    else:
        raise ValueError('missing BEL file')

    log.info('Done loading BEL')

    if csv:
        log.info('Outputting csv to {}'.format(csv))
        graph.to_csv(g, csv)

    if graphml:
        log.info('Outputting graphml to {}'.format(graphml))
        graph.to_graphml(g, graphml)

    if json:
        log.info('Outputting json to {}'.format(json))
        graph.to_json(g, json)

    if pickle:
        log.info('Outputting pickle to {}'.format(pickle))
        graph.to_pickle(g, pickle)


@main.command()
@click.option('--path', help='BEL file file path')
@click.option('--url', help='BEL file URL')
@click.option('--database', help='BEL database')
@click.option('--neo', help='URL of neo4j database')
@click.option('--context', help='Context tag for multiple simultaneous neo4j graphs')
@click.option('-v', '--verbose', count=True)
def to_neo(path, url, database, neo, context, verbose):
    """Parses BEL file and uploads to Neo4J"""

    if verbose == 1:
        ch.setLevel(logging.DEBUG)
    elif verbose >= 2:
        ch.setLevel(5)
    else:
        ch.setLevel(logging.INFO)

    log.addHandler(ch)

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

    t = time.time()
    graph.to_neo4j(g, p2n, context)
    log.info('Upload to neo4j done in {:.02f} seconds'.format(time.time() - t))


@main.command()
@click.option('--path', help='Destination for namespace cache. Defaults to ~/.pybel/data/namespace_cache.db')
def setup_nscache(conn):
    NamespaceCache(conn=conn, setup_default_cache=True)


if __name__ == '__main__':
    main()
