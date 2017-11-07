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

import json
import logging
import os
import sys
import time

import click

from .canonicalize import to_bel
from .constants import PYBEL_CONFIG_PATH, PYBEL_CONNECTION, PYBEL_LOG_DIR, config, get_cache_connection
from .io import from_lines, from_url, to_csv, to_cx_file, to_graphml, to_gsea, to_json_file, to_neo4j, to_pickle, to_sif
from .manager import Manager, defaults
from .manager.database_io import from_database, to_database
from .manager.models import Base
from .utils import PYBEL_MYSQL_FMT_NOPASS, PYBEL_MYSQL_FMT_PASS

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
    """PyBEL Command Line """


@main.command()
@click.option('-p', '--path', type=click.File('r'), default=sys.stdin, help='Input BEL file file path')
@click.option('--url', help='Input BEL file URL')
@click.option('-c', '--connection', help='Connection to cache. Defaults to {}'.format(get_cache_connection()))
@click.option('--database-name', help='Input network name from database')
@click.option('--csv', type=click.File('w'), help='Output path for *.csv')
@click.option('--sif', type=click.File('w'), help='Output path for *.sif')
@click.option('--gsea', type=click.File('w'), help='Output path for *.grp for gene set enrichment analysis')
@click.option('--graphml', help='Output path for GraphML output. Use *.graphml for Cytoscape')
@click.option('--json', type=click.File('w'), help='Output path for Node-link *.json')
@click.option('--pickle', help='Output path for NetworkX *.gpickle')
@click.option('--cx', type=click.File('w'), help='Output CX JSON for use with NDEx')
@click.option('--bel', type=click.File('w'), help='Output canonical BEL')
@click.option('--neo', help="Connection string for neo4j upload")
@click.option('--neo-context', help="Optional context for neo4j upload")
@click.option('-s', '--store-default', is_flag=True,
              help="Stores to default cache at {}".format(get_cache_connection()))
@click.option('--store-connection', help="Database connection string")
@click.option('--allow-naked-names', is_flag=True, help="Enable lenient parsing for naked names")
@click.option('--allow-nested', is_flag=True, help="Enable lenient parsing for nested statements")
@click.option('--allow-unqualified-translocations', is_flag=True,
              help="Enable lenient parsing for unqualified translocations")
@click.option('--no-citation-clearing', is_flag=True, help='Turn off citation clearing')
@click.option('-v', '--debug', count=True)
def convert(path, url, connection, database_name, csv, sif, gsea, graphml, json, pickle, cx, bel, neo,
            neo_context, store_default, store_connection, allow_naked_names, allow_nested,
            allow_unqualified_translocations, no_citation_clearing, debug):
    """Convert BEL"""
    if debug == 1:
        log.setLevel(20)
    elif debug == 2:
        log.setLevel(10)

    manager = Manager(connection=connection)

    if database_name:
        g = from_database(database_name, connection=manager)

    elif url:
        g = from_url(
            url,
            manager=manager,
            allow_nested=allow_nested,
            allow_naked_names=allow_naked_names,
            allow_unqualified_translocations=allow_unqualified_translocations,
            citation_clearing=(not no_citation_clearing),
        )

    else:
        g = from_lines(
            path,
            manager=manager,
            allow_nested=allow_nested,
            allow_naked_names=allow_naked_names,
            allow_unqualified_translocations=allow_unqualified_translocations,
            citation_clearing=(not no_citation_clearing),
        )

    if csv:
        log.info('Outputting CSV to %s', csv)
        to_csv(g, csv)

    if sif:
        log.info('Outputting SIF to %s', sif)
        to_sif(g, sif)

    if graphml:
        log.info('Outputting GraphML to %s', graphml)
        to_graphml(g, graphml)

    if gsea:
        log.info('Outputting GRP to %s', gsea)
        to_gsea(g, gsea)

    if json:
        log.info('Outputting JSON to %s', json)
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
        log.info('Storing to database')
        to_database(g, store_parts=True)

    if store_connection:
        log.info('Storing to database: %s', store_connection)
        to_database(g, connection=store_connection, store_parts=True)

    if neo:
        import py2neo
        log.info('Uploading to neo4j with context %s', neo_context)
        neo_graph = py2neo.Graph(neo)
        assert neo_graph.data('match (n) return count(n) as count')[0]['count'] is not None
        to_neo4j(g, neo_graph, neo_context)

    sys.exit(0 if 0 == len(g.warnings) else 1)


def set_default(key, value):
    """Sets the default setting for this key/value pair. Does NOT update the current config.

    :param str key:
    :param str value:
    """
    with open(PYBEL_CONFIG_PATH) as f:
        default_config = json.load(f)

    default_config[key] = value

    with open(PYBEL_CONFIG_PATH, 'w') as f:
        json.dump(f, default_config)


def set_default_connection(value):
    """Sets the default connection string with the given value. See
    http://docs.sqlalchemy.org/en/latest/core/engines.html for examples"""
    set_default(PYBEL_CONNECTION, value)


def set_default_mysql_connection(user=None, password=None, host=None, database=None, charset=None):
    """Sets the default connection string with MySQL settings

    :param host: MySQL database host
    :param user: MySQL database user
    :param password: MySQL database password. Can be None if no password is used.
    :param database: MySQL database name
    :param charset: MySQL database character set
    """
    kwargs = dict(
        user=user or 'pybel',
        host=host or 'localhost',
        password=password,
        database=database or 'pybel',
        charset=charset or 'utf8'
    )

    fmt = PYBEL_MYSQL_FMT_NOPASS if password is None else PYBEL_MYSQL_FMT_PASS

    set_default_connection(fmt.format(**kwargs))


@main.group(help="Edit connection settings. Set to: {}".format(config[PYBEL_CONNECTION]))
def connection():
    pass


@connection.command()
@click.argument('value')
def set(value):
    """Set custom connection string"""
    set_default_connection(value)


@connection.command()
@click.option('--user')
@click.option('--password')
@click.option('--host')
@click.option('--database')
@click.option('--charset')
def set_mysql(user, password, host, database, charset):
    """Sets MySQL connection string"""
    set_default_mysql_connection(
        user=user,
        password=password,
        host=host,
        database=database,
        charset=charset
    )


@main.group()
@click.option('-c', '--connection', help='Cache connection. Defaults to {}'.format(get_cache_connection()))
@click.pass_context
def manage(ctx, connection):
    """Manage database"""
    ctx.obj = Manager(connection)
    Base.metadata.bind = ctx.obj.engine
    Base.query = ctx.obj.session.query_property()


@manage.command()
@click.option('-v', '--debug', count=True)
@click.pass_obj
def setup(manager, debug):
    """Create the cache if it doesn't exist"""
    log.setLevel(int(5 * debug ** 2 / 2 - 25 * debug / 2 + 20))
    manager.create_all()


@manage.command()
@click.option('-y', '--yes', is_flag=True)
@click.pass_obj
def remove(manager, yes):
    """Drops cache"""
    if yes or click.confirm('Drop database?'):
        manager.drop_all()


@manage.group()
def namespaces():
    """Manage definitions"""


@manage.group()
def annotations():
    """Manage definitions"""


@namespaces.command()
@click.option('-v', '--debug', count=True)
@click.pass_obj
def ensure(manager, debug):
    """Set up default cache with default definitions"""
    log.setLevel(int(5 * debug ** 2 / 2 - 25 * debug / 2 + 20))

    for url in defaults.fraunhofer_namespaces:
        manager.ensure_namespace(url)


@annotations.command()
@click.option('-v', '--debug', count=True)
@click.pass_obj
def ensure(manager, debug):
    """Set up default cache with default annotations"""
    log.setLevel(int(5 * debug ** 2 / 2 - 25 * debug / 2 + 20))

    for url in defaults.fraunhofer_annotations:
        manager.ensure_annotation(url)


@namespaces.command()
@click.argument('url')
@click.pass_obj
def insert(manager, url):
    """Manually add namespace by URL"""
    if url.endswith('.belns'):
        manager.ensure_namespace(url)
    else:
        manager.ensure_namespace_owl(url)


@annotations.command()
@click.argument('url')
@click.pass_obj
def insert(manager, url):
    """Manually add annotation by URL"""
    if url.endswith('.belanno'):
        manager.ensure_annotation(url)
    else:
        manager.ensure_annotation_owl(url)


@namespaces.command()
@click.option('--url', help='Specific resource URL to list')
@click.pass_obj
def ls(manager, url):
    """Lists cached namespaces"""
    if not url:
        for namespace, in manager.list_namespaces():
            click.echo(namespace.url)

    else:
        if url.endswith('.belns'):
            res = manager.ensure_namespace(url).to_values()

        else:
            res = manager.get_namespace_owl_terms(url)

        for l in res:
            click.echo(l)


@annotations.command()
@click.option('--url', help='Specific resource URL to list')
@click.pass_obj
def ls(manager, url):
    """Lists cached annotations"""
    if not url:
        for annotation, in manager.list_annotations():
            click.echo(annotation.url)

    else:
        if url.endswith('.belanno'):
            annotation = manager.ensure_annotation(url)
        else:
            annotation = manager.ensure_annotation_owl(url)

        for l in annotation.get_entries():
            click.echo(l)


@namespaces.command()
@click.argument('url')
@click.pass_obj
def drop(manager, url):
    """Drops a namespace by URL"""
    manager.drop_namespace_by_url(url)


@annotations.command()
@click.argument('url')
@click.pass_obj
def drop(manager, url):
    """Drops an annotation by URL"""
    manager.drop_annotation_by_url(url)


@manage.group()
def network():
    """Manage networks"""


@network.command()
@click.pass_obj
def ls(manager):
    """Lists network names, versions, and optionally descriptions"""
    for n in manager.list_networks():
        click.echo('{}\t{}\t{}'.format(n.id, n.name, n.version))


@network.command()
@click.argument('network_id')
@click.pass_obj
def drop(manager, network_id):
    """Drops a network by its database identifier"""
    manager.drop_network_by_id(network_id)


@network.command()
@click.option('-y', '--yes', is_flag=True)
@click.pass_obj
def dropall(manager, yes):
    """Drops all networks"""
    if yes or click.confirm('Drop all networks?'):
        manager.drop_networks()


if __name__ == '__main__':
    main()
