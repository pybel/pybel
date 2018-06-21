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
import sys
import time

import click

from .canonicalize import to_bel
from .constants import get_cache_connection
from .io import from_lines, from_url, to_csv, to_cx_file, to_graphml, to_gsea, to_json_file, to_neo4j, to_pickle, to_sif
from .manager import Manager, defaults
from .manager.database_io import from_database, to_database
from .manager.models import Base, Edge, Namespace

log = logging.getLogger(__name__)


def _page(it):
    click.echo_via_pager('\n'.join(map(str, it)))


@click.group(
    help="PyBEL Command Line Utilities on {} using default connection {}".format(sys.executable,
                                                                                 get_cache_connection()))
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
@click.option('--no-identifier-validation', is_flag=True, help='Turn off identifier validation')
@click.option('--no-citation-clearing', is_flag=True, help='Turn off citation clearing')
@click.option('-v', '--debug', count=True)
def convert(path, url, connection, database_name, csv, sif, gsea, graphml, json, pickle, cx, bel, neo,
            neo_context, store_default, store_connection, allow_naked_names, allow_nested,
            allow_unqualified_translocations, no_identifier_validation, no_citation_clearing, debug):
    """Convert BEL"""
    if debug == 1:
        log.setLevel(logging.INFO)
        logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s - %(message)s')
    elif debug == 2:
        log.setLevel(logging.DEBUG)
        logging.basicConfig(level=logging.DEBUG, format='%(name)s:%(levelname)s - %(message)s')

    manager = Manager.from_connection(connection)

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
            no_identifier_validation=no_identifier_validation,
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


@main.command()
@click.argument('agents', nargs=-1)
@click.option('--host')
def machine(agents, host):
    """Get content from the INDRA machine and upload to BEL Commons."""
    from indra.sources import indra_db_rest
    from pybel import from_indra_statements, to_web

    statements = indra_db_rest.get_statements(agents=agents)
    click.echo('got {} statements from INDRA'.format(len(statements)))

    graph = from_indra_statements(
        statements,
        name='INDRA Machine for {}'.format(', '.join(sorted(agents))),
        version=time.strftime('%Y%m%d'),
    )
    click.echo('built BEL graph with {} nodes and {} edges'.format(graph.number_of_nodes(), graph.number_of_edges()))

    resp = to_web(graph, host=host)
    resp.raise_for_status()


@main.group()
@click.option('-c', '--connection', help='Cache connection. Defaults to {}'.format(get_cache_connection()))
@click.pass_context
def manage(ctx, connection):
    """Manage database"""
    ctx.obj = Manager.from_connection(connection)
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
def drop(manager, yes):
    """Drops cache"""
    if yes or click.confirm('Drop database?'):
        manager.drop_all()


@manage.group()
def namespace():
    """Manage namespaces"""


@manage.group()
def annotations():
    """Manage annotations"""


@namespace.command()
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


@namespace.command()
@click.argument('url')
@click.pass_obj
def insert(manager, url):
    """Manually add namespace by URL"""
    manager.ensure_namespace(url)


@annotations.command()
@click.argument('url')
@click.pass_obj
def insert(manager, url):
    """Manually add annotation by URL"""
    manager.ensure_annotation(url)


@namespace.command()
@click.option('--url', help='Specific resource URL to list')
@click.option('-i', '--namespace-id', help='Specific resource URL to list')
@click.pass_obj
def ls(manager, url, namespace_id):
    """Lists cached namespaces."""
    if url:
        n = manager.ensure_namespace(url)
        _page(n.entries)

    elif namespace_id:
        n = manager.session.query(Namespace).get(namespace_id)
        _page(n.entries)

    else:
        for n in manager.session.query(Namespace).order_by(Namespace.uploaded.desc()):
            click.echo('\t'.join(map(str, (n.id, n.keyword, n.version, n.url))))


@annotations.command()
@click.option('--url', help='Specific resource URL to list')
@click.pass_obj
def ls(manager, url):
    """Lists cached annotations"""
    if not url:
        for annotation, in manager.list_annotations():
            click.echo(annotation.url)

    else:
        annotation = manager.ensure_annotation(url)
        for l in annotation.get_entries():
            click.echo(l)


@namespace.command()
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
@click.option('-n', '--network-id', type=int, help='Identifier of network to drop')
@click.option('-y', '--yes', is_flag=True, help='Drop all networks without confirmation if no identifier is given')
@click.pass_obj
def drop(manager, network_id, yes):
    """Drops a network by its identifier or drops all networks"""
    if network_id:
        manager.drop_network_by_id(network_id)

    if yes or click.confirm('Drop all networks?'):
        manager.drop_networks()


@manage.group()
def edge():
    """Manage edges"""


@edge.command()
@click.option('--offset', type=int)
@click.option('--limit', type=int, default=10)
@click.pass_obj
def ls(manager, offset, limit):
    """Lists edges"""
    q = manager.session.query(Edge)

    if offset:
        q = q.offset(offset)

    if limit > 0:
        q = q.limit(limit)

    for e in q:
        click.echo(e.bel)


@manage.command()
@click.pass_obj
def summarize(manager):
    """Summarizes the contents of the database"""
    click.echo('Networks: {}'.format(manager.count_networks()))
    click.echo('Edges: {}'.format(manager.count_edges()))
    click.echo('Nodes: {}'.format(manager.count_nodes()))
    click.echo('Namespaces: {}'.format(manager.count_namespaces()))
    click.echo('Namespaces entries: {}'.format(manager.count_namespace_entries()))
    click.echo('Annotations: {}'.format(manager.count_annotations()))
    click.echo('Annotation entries: {}'.format(manager.count_annotation_entries()))


if __name__ == '__main__':
    main()
