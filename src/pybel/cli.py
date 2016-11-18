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
import sys
import time

import click
import py2neo

from . import graph
from .constants import PYBEL_DIR
from .manager.namespace_cache import DefinitionCacheManager, DEFAULT_CACHE_LOCATION

log = logging.getLogger('pybel')
log.setLevel(logging.DEBUG)

log_levels = {
    0: logging.INFO,
    1: logging.DEBUG,
}

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)

fh_path = os.path.join(PYBEL_DIR, time.strftime('pybel_%Y_%m_%d_%H_%M_%S.txt'))
fh = logging.FileHandler(fh_path)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh)


@click.group(help="PyBEL Command Line Utilities")
@click.version_option()
def main():
    pass


@main.command()
@click.option('--path', type=click.File('r'), help='Input BEL file file path. Use - for stdin')
@click.option('--url', help='Input BEL file URL')
@click.option('--database', help='Input BEL database')
@click.option('--csv', help='Output path for *.csv')
@click.option('--graphml', help='Output path for GraphML output. Use *.graphml for Cytoscape')
@click.option('--json', type=click.File('w'), help='Output path for Node-link *.json')
@click.option('--pickle', help='Output path for NetworkX *.gpickle')
@click.option('--neo', help="Connection string for neo4j upload")
@click.option('--neo-context', help="Context for neo4j upload")
@click.option('--lenient', is_flag=True, help="Enable lenient parsing")
@click.option('--log-file', type=click.File('w'), help="Optional path for verbose log output")
@click.option('-v', '--verbose', count=True)
def convert(path, url, database, csv, graphml, json, pickle, neo, neo_context, lenient, log_file, verbose):
    """Options for multiple outputs/conversions"""

    ch.setLevel(log_levels.get(verbose, 5))
    log.addHandler(ch)

    if path:
        g = graph.BELGraph(path, lenient=lenient, log_stream=log_file)
    elif url:
        g = graph.from_url(url, lenient=lenient, log_stream=log_file)
    elif database:
        g = graph.from_database(database)
    else:
        raise ValueError('missing BEL file')

    if csv:
        log.info('Outputting csv to %s', csv)
        graph.to_csv(g, csv)

    if graphml:
        log.info('Outputting graphml to %s', graphml)
        graph.to_graphml(g, graphml)

    if json:
        log.info('Outputting json to %s', json)
        graph.to_json(g, json)

    if pickle:
        log.info('Outputting pickle to %s', pickle)
        graph.to_pickle(g, pickle)

    if neo:
        log.info('Uploading to neo4j with context %s', neo_context)
        neo_graph = py2neo.Graph(neo)
        assert neo_graph.data('match (n) return count(n) as count')[0]['count'] is not None
        graph.to_neo4j(g, neo_graph, neo_context)

    sys.exit(0 if g.last_parse_errors == 0 else 1)


@main.group(help="PyBEL Data Manager Utilities")
def manage():
    pass


@manage.command(help='Set up definition cache with default definitions')
@click.option('--path', help='Destination for namespace namspace_cache. Defaults to ~/.pybel/data/namespace_cache.db')
def setup(path):
    DefinitionCacheManager(conn=path, setup_default_cache=True)
    sys.exit(0)


@manage.command(help='Remove definition cache')
def remove():
    os.remove(DEFAULT_CACHE_LOCATION)
    sys.exit(0)


if __name__ == '__main__':
    main()
