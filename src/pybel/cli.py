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
from .io import from_lines, from_url, to_json_file, to_csv, to_graphml, to_neo4j, to_cx_file, to_pickle, to_sif, to_gsea
from .manager import defaults
from .manager.cache import CacheManager
from .manager.database_io import to_database, from_database
from .manager.models import Network

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
@click.option('--store-default', is_flag=True, help="Stores to default cache at {}".format(get_cache_connection()))
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

    if sif:
        log.info('Outputting sif to %s', sif)
        to_sif(g, sif)

    if graphml:
        log.info('Outputting graphml to %s', graphml)
        to_graphml(g, graphml)

    if gsea:
        log.info('Outputting grp to %s', gsea)
        to_gsea(g, gsea)

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


@main.group()
@click.option('-c', '--connection', help='Cache connection. Defaults to {}'.format(get_cache_connection()))
@click.pass_context
def manage(ctx, connection):
    """Manage database"""
    ctx.obj = CacheManager(connection)


@manage.command()
@click.option('-c', '--connection', help='Cache connection string. Defaults to {}'.format(get_cache_connection()))
@click.option('-v', '--debug', count=True)
def setup(connection, debug):
    """Create the cache if it doesn't exist"""
    log.setLevel(int(5 * debug ** 2 / 2 - 25 * debug / 2 + 20))
    manager = CacheManager(connection=connection, echo=True)
    manager.create_all()


@manage.command()
@click.option('-c', '--connection', help='Cache connection string. Defaults to {}'.format(get_cache_connection()))
@click.option('-y', '--yes', is_flag=True)
def remove(connection, yes):
    """Drops cache"""
    if yes or click.confirm('Drop database?'):
        manager = CacheManager(connection=connection, echo=True)
        manager.drop_database()


@manage.group()
def definitions():
    """Manage definitions"""


@definitions.command()
@click.option('--skip-namespaces', is_flag=True)
@click.option('--skip-annotations', is_flag=True)
@click.option('--owl', is_flag=True)
@click.option('--fraunhofer', is_flag=True, help='Use Fraunhofer resources instead of OpenBEL')
@click.option('-v', '--debug', count=True)
@click.pass_context
def ensure(ctx, skip_namespaces, skip_annotations, owl, fraunhofer, debug):
    """Set up default cache with default definitions"""
    log.setLevel(int(5 * debug ** 2 / 2 - 25 * debug / 2 + 20))

    if not skip_namespaces:
        for url in defaults.fraunhofer_namespaces if fraunhofer else defaults.default_namespaces:
            ctx.obj.ensure_namespace(url)
    if not skip_annotations:
        for url in defaults.fraunhofer_annotations if fraunhofer else defaults.default_annotations:
            ctx.obj.ensure_annotation(url)
    if owl:
        for url in defaults.default_owl:
            ctx.obj.ensure_namespace_owl(url)


@definitions.command()
@click.argument('url')
@click.pass_context
def insert(ctx, url):
    """Manually add definition by URL"""
    if url.endswith('.belns'):
        ctx.obj.ensure_namespace(url)
    elif url.endswith('.belanno'):
        ctx.obj.ensure_annotation(url)
    else:
        ctx.obj.ensure_namespace_owl(url)


@definitions.command()
@click.option('--url', help='Specific resource URL to list')
@click.pass_context
def ls(ctx, url):
    """Lists cached definitions"""
    if not url:
        for line in ctx.obj.get_definition_urls():
            if not line:
                continue
            click.echo(line)

    else:
        if url.endswith('.belns'):
            res = ctx.obj.get_namespace(url)
        elif url.endswith('.belanno'):
            res = ctx.obj.get_annotation(url)
        else:
            res = ctx.obj.get_namespace_owl_terms(url)

        for l in res:
            click.echo(l)


@definitions.command()
@click.argument('url')
@click.pass_context
def drop_namespace(ctx, url):
    """Drops a namespace by url"""
    ctx.obj.drop_namespace_by_url(url)


@manage.group()
def network():
    """Manage networks"""


@network.command()
@click.option('-d', '--include-description', help="Include network descriptions")
@click.pass_context
def ls(ctx, include_description):
    """Lists network names, versions, and optionally descriptions"""

    if include_description:
        l = ctx.obj.session.query(Network.id, Network.name, Network.version, Network.description).all()
    else:
        l = ctx.obj.session.query(Network.id, Network.name, Network.version).all()

    for row in l:
        click.echo('\t'.join(map(str, row)))


@network.command()
@click.argument('network_id')
@click.pass_context
def drop(ctx, network_id):
    """Drops a network by its database identifier"""
    ctx.obj.drop_network_by_id(network_id)


@network.command()
@click.option('-y', '--yes', is_flag=True)
@click.pass_context
def dropall(ctx, yes):
    """Drops all networks"""
    if yes or click.confirm('Drop all networks?'):
        ctx.obj.drop_networks()


if __name__ == '__main__':
    main()
