# -*- coding: utf-8 -*-

"""
Module that contains the command line app

Why does this file exist, and why not put this in __main__?
You might be tempted to import things from __main__ later, but that will cause
problems--the code will get executed twice:
 - When you run `python3 -m pybel` python will execute
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

from .canonicalize import to_bel
from .constants import PYBEL_LOG_DIR, get_cache_connection
from .io import from_lines, from_url, to_json_file, to_csv, to_graphml, to_neo4j, to_cx_file, to_pickle
from .manager.cache import CacheManager
from .manager.database_io import to_database, from_database

log = logging.getLogger('pybel')

formatter = logging.Formatter('%(name)s:%(levelname)s - %(message)s')
logging.basicConfig(format=formatter)

fh_path = os.path.join(PYBEL_LOG_DIR, time.strftime('pybel_%Y_%m_%d_%H_%M_%S.txt'))
fh = logging.FileHandler(fh_path)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh)


@click.group(help="PyBEL Command Line Utilities on {}".format(sys.executable))
@click.version_option()
def main():
    pass


@main.command()
@click.option('-p', '--path', type=click.File('r'), default=sys.stdin, help='Input BEL file file path')
@click.option('--url', help='Input BEL file URL')
@click.option('-c', '--connection', help='Connection to cache. Defaults to {}'.format(get_cache_connection()))
@click.option('--database-name', help='Input graph name from database')
@click.option('--csv', help='Output path for *.csv')
@click.option('--graphml', help='Output path for GraphML output. Use *.graphml for Cytoscape')
@click.option('--json', type=click.File('w'), help='Output path for Node-link *.json')
@click.option('--pickle', help='Output path for NetworkX *.gpickle')
@click.option('--cx', type=click.File('w'), help='Output CX JSON for use with NDEx')
@click.option('--bel', type=click.File('w'), help='Output canonical BEL')
@click.option('--neo', help="Connection string for neo4j upload")
@click.option('--neo-context', help="Optional context for neo4j upload")
@click.option('--store-default', is_flag=True, help="Stores to default cache at {}".format(get_cache_connection()))
@click.option('--store-connection', help="Database connection string")
@click.option('--allow-naked-names', is_flag=True, help="Enable lenient parsing for naked names")
@click.option('--allow-nested', is_flag=True, help="Enable lenient parsing for nested statements")
@click.option('--allow-unqualified-translocations', is_flag=True,
              help="Enable lenient parsing for unqualified translocations")
@click.option('--no-citation-clearing', is_flag=True, help='Turn off citation clearing')
@click.option('-v', '--debug', count=True)
def convert(path, url, connection, database_name, csv, graphml, json, pickle, cx, bel, neo,
            neo_context, store_default, store_connection, allow_naked_names, allow_nested,
            allow_unqualified_translocations, no_citation_clearing, debug):
    """Options for multiple outputs/conversions"""
    if debug == 1:
        log.setLevel(20)
    elif debug == 2:
        log.setLevel(10)

    manager = CacheManager(connection=connection)

    if database_name:
        g = from_database(database_name, connection=manager)
    elif url:
        g = from_url(
            url,
            manager=manager,
            allow_nested=allow_nested,
            allow_naked_names=allow_naked_names,
            allow_unqualified_translocations=allow_unqualified_translocations,
            citation_clearing=(not no_citation_clearing)
        )

    else:
        g = from_lines(
            path,
            manager=manager,
            allow_nested=allow_nested,
            allow_naked_names=allow_naked_names,
            allow_unqualified_translocations=allow_unqualified_translocations,
            citation_clearing=(not no_citation_clearing)
        )

    if csv:
        log.info('Outputting csv to %s', csv)
        to_csv(g, csv)

    if graphml:
        log.info('Outputting graphml to %s', graphml)
        to_graphml(g, graphml)

    if json:
        log.info('Outputting json to %s', json)
        to_json_file(g, json)

    if pickle:
        log.info('Outputting pickle to %s', pickle)
        to_pickle(g, pickle)

    if cx:
        log.info('Outputting CX to %s', cx)
        to_cx_file(g, cx)

    if bel:
        log.info('Outputting BEL to %s', bel)
        to_bel(g, bel)

    if store_default:
        to_database(g)

    if store_connection:
        to_database(g, connection=store_connection)

    if neo:
        import py2neo
        log.info('Uploading to neo4j with context %s', neo_context)
        neo_graph = py2neo.Graph(neo)
        assert neo_graph.data('match (n) return count(n) as count')[0]['count'] is not None
        to_neo4j(g, neo_graph, neo_context)

    sys.exit(0 if 0 == len(g.warnings) else 1)


@main.group(help="PyBEL Data Manager Utilities")
def manage():
    pass


@manage.command(help="Create the cache if it doesn't exist")
@click.option('-c', '--connection', help='Cache connection string. Defaults to {}'.format(get_cache_connection()))
@click.option('-v', '--debug', count=True)
def setup(connection, debug):
    log.setLevel(int(5 * debug ** 2 / 2 - 25 * debug / 2 + 20))
    manager = CacheManager(connection=connection, echo=True)
    manager.create_all()


@manage.command(help='Drops database in cache')
@click.option('-c', '--connection', help='Cache connection string. Defaults to {}'.format(get_cache_connection()))
def remove(connection):
    manager = CacheManager(connection=connection, echo=True)
    manager.drop_database()


@manage.group(help="Manage definitions")
def definitions():
    pass


@definitions.command(help='Set up default cache with default definitions')
@click.option('-c', '--connection', help='Cache connection string. Defaults to {}'.format(get_cache_connection()))
@click.option('--skip-namespaces', is_flag=True)
@click.option('--skip-annotations', is_flag=True)
@click.option('--owl', is_flag=True)
@click.option('--fraunhofer', is_flag=True, help='Use Fraunhofer resources instead of OpenBEL')
@click.option('-v', '--debug', count=True)
def ensure(connection, skip_namespaces, skip_annotations, owl, fraunhofer, debug):
    log.setLevel(int(5 * debug ** 2 / 2 - 25 * debug / 2 + 20))

    manager = CacheManager(connection=connection)

    if not skip_namespaces:
        manager.ensure_default_namespaces(use_fraunhofer=fraunhofer)
    if not skip_annotations:
        manager.ensure_default_annotations(use_fraunhofer=fraunhofer)
    if owl:
        manager.ensure_default_owl_namespaces()


@definitions.command(help='Manually add definition by URL')
@click.argument('url')
@click.option('-c', '--connection', help='Cache connection string. Defaults to {}'.format(get_cache_connection()))
def insert(url, connection):
    manager = CacheManager(connection=connection)

    if url.endswith('.belns'):
        manager.ensure_namespace(url)
    elif url.endswith('.belanno'):
        manager.ensure_annotation(url)
    else:
        manager.ensure_namespace_owl(url)


@definitions.command(help='List URLs of cached resources, or contents of a specific resource')
@click.option('--url', help='Resource to list')
@click.option('-c', '--connection', help='Cache connection string. Defaults to {}'.format(get_cache_connection()))
def ls(url, connection):
    manager = CacheManager(connection=connection)

    if not url:
        for line in manager.get_definition_urls():
            if not line:
                continue
            click.echo(line)

    else:
        if url.endswith('.belns'):
            res = manager.get_namespace(url)
        elif url.endswith('.belanno'):
            res = manager.get_annotation(url)
        else:
            res = manager.get_namespace_owl_terms(url)

        for l in res:
            click.echo(l)


@definitions.command(help='Drop namespace by url')
@click.argument('url')
@click.option('-c', '--connection', help='Cache connection string. Defaults to {}'.format(get_cache_connection()))
def drop_namespace(url, connection):
    manager = CacheManager(connection=connection)
    manager.drop_namespace(url)


@manage.group(help="Manage graphs")
def graph():
    pass


@graph.command(help='Lists stored graph names and versions')
@click.option('-c', '--connection', help='Cache connection string. Defaults to {}'.format(get_cache_connection()))
@click.option('-d', '--include-description', help="Include graph descriptions")
def ls(connection, include_description):
    manager = CacheManager(connection=connection)

    for row in manager.list_graphs(include_description=include_description):
        click.echo('\t'.join(map(str, row)))


@graph.command(help='Drops a graph by ID')
@click.argument('gid')
@click.option('-c', '--connection', help='Cache connection string. Defaults to {}'.format(get_cache_connection()))
def drop(gid, connection):
    manager = CacheManager(connection=connection)
    manager.drop_graph(gid)


@graph.command(help='Drops all graphs')
@click.option('-c', '--connection', help='Cache connection string. Defaults to {}'.format(get_cache_connection()))
def dropall(connection):
    manager = CacheManager(connection=connection)
    manager.drop_graphs()


if __name__ == '__main__':
    main()
