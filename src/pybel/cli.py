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

from . import io
from .canonicalize import to_bel
from .constants import PYBEL_DIR
from .graph import BELGraph
from .manager.cache import DEFAULT_CACHE_LOCATION, CacheManager
from .manager.graph_cache import GraphCacheManager, to_database, from_database

log = logging.getLogger('pybel')

formatter = logging.Formatter('%(name)s:%(levelname)s - %(message)s')
logging.basicConfig(format=formatter)

fh_path = os.path.join(PYBEL_DIR, time.strftime('pybel_%Y_%m_%d_%H_%M_%S.txt'))
fh = logging.FileHandler(fh_path)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh)


@click.group(help="PyBEL Command Line Utilities on {}".format(sys.executable))
@click.version_option()
def main():
    pass


@main.command()
@click.option('--path', type=click.File('r'), default=sys.stdin, help='Input BEL file file path')
@click.option('--url', help='Input BEL file URL')
@click.option('--database-name', help='Input graph name from database')
@click.option('--database-connection', help='Input cache location. Defaults to {}'.format(DEFAULT_CACHE_LOCATION))
@click.option('--csv', help='Output path for *.csv')
@click.option('--graphml', help='Output path for GraphML output. Use *.graphml for Cytoscape')
@click.option('--json', type=click.File('w'), help='Output path for Node-link *.json')
@click.option('--pickle', help='Output path for NetworkX *.gpickle')
@click.option('--bel', type=click.File('w'), help='Output canonical BEL')
@click.option('--neo', help="Connection string for neo4j upload")
@click.option('--neo-context', help="Context for neo4j upload")
@click.option('--store-default', is_flag=True, help="Stores to default cache at {}".format(DEFAULT_CACHE_LOCATION))
@click.option('--store', help="Database connection string")
@click.option('--lenient', is_flag=True, help="Enable lenient parsing")
@click.option('--complete-origin', is_flag=True, help="Complete origin from protein to gene")
@click.option('--log-file', type=click.File('w'), help="Optional path for verbose log output")
@click.option('-v', '--verbose', count=True)
def convert(path, url, database_name, database_connection, csv, graphml, json, pickle, bel, neo, neo_context,
            store_default, store, lenient, complete_origin, log_file, verbose):
    """Options for multiple outputs/conversions"""

    log.setLevel(int(5 * verbose ** 2 / 2 - 25 * verbose / 2 + 20))

    if url:
        g = io.from_url(url, lenient=lenient, complete_origin=complete_origin, log_stream=log_file)
    elif database_name:
        g = from_database(database_name, connection=database_connection)
    else:
        g = BELGraph(path, lenient=lenient, complete_origin=complete_origin, log_stream=log_file)

    if csv:
        log.info('Outputting csv to %s', csv)
        io.to_csv(g, csv)

    if graphml:
        log.info('Outputting graphml to %s', graphml)
        io.to_graphml(g, graphml)

    if json:
        log.info('Outputting json to %s', json)
        io.to_json(g, json)

    if pickle:
        log.info('Outputting pickle to %s', pickle)
        io.to_pickle(g, pickle)

    if bel:
        log.info('Outputting BEL to %s', bel)
        to_bel(g, bel)

    if store_default:
        to_database(g)

    if store:
        to_database(g, store)

    if neo:
        log.info('Uploading to neo4j with context %s', neo_context)
        neo_graph = py2neo.Graph(neo)
        assert neo_graph.data('match (n) return count(n) as count')[0]['count'] is not None
        io.to_neo4j(g, neo_graph, neo_context)

    sys.exit(0 if 0 == sum(g.last_parse_errors.values()) else 1)


@main.group(help="PyBEL Data Manager Utilities")
def manage():
    pass


@manage.command(help='Set up definition cache with default definitions')
@click.option('--path', help='Cache location. Defaults to {}'.format(DEFAULT_CACHE_LOCATION))
@click.option('--skip-namespaces', is_flag=True)
@click.option('--skip-annotations', is_flag=True)
@click.option('--skip-owl', is_flag=True)
def setup(path, skip_namespaces, skip_annotations, skip_owl):
    cm = CacheManager(connection=path)
    if not skip_namespaces:
        cm.load_default_namespaces()
    if not skip_annotations:
        cm.load_default_annotations()
    if not skip_owl:
        cm.load_default_owl()


@manage.command(help='Remove default definition cache at {}'.format(DEFAULT_CACHE_LOCATION))
def remove():
    os.remove(DEFAULT_CACHE_LOCATION)


@manage.command(help='Manually add definition by URL')
@click.argument('url')
@click.option('--path', help='Cache location. Defaults to {}'.format(DEFAULT_CACHE_LOCATION))
def insert(url, path):
    dcm = CacheManager(connection=path)

    if url.endswith('.belns'):
        dcm.ensure_namespace(url)
    elif url.endswith('.belanno'):
        dcm.ensure_annotation(url)
    else:
        dcm.ensure_owl(url)


@manage.command(help='List URLs of cached resources, or contents of a specific resource')
@click.option('--url', help='Resource to list')
@click.option('--path', help='Cache location. Defaults to {}'.format(DEFAULT_CACHE_LOCATION))
def ls(url, path):
    dcm = CacheManager(connection=path)

    if not url:
        click.echo_via_pager('\n'.join(sorted(x for x in dcm.ls() if x)))
    else:
        if url.endswith('.belns'):
            res = dcm.get_namespace(url)
        elif url.endswith('.belanno'):
            res = dcm.get_annotation(url)
        else:
            res = dcm.get_owl_terms(url)
        click.echo_via_pager('\n'.join(res))


@manage.command(help='Lists stored graph names and versions')
@click.option('--path', help='Cache location. Defaults to {}'.format(DEFAULT_CACHE_LOCATION))
def ls_graphs(path):
    gcm = GraphCacheManager(connection=path)
    click.echo_via_pager('\n'.join('{} - {}'.format(a, b) for a, b in gcm.ls()))


if __name__ == '__main__':
    main()
