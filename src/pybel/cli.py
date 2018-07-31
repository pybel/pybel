# -*- coding: utf-8 -*-

"""Command line interface for PyBEL.

Why does this file exist, and why not put this in __main__?
You might be tempted to import things from __main__ later, but that will cause
problems--the code will get executed twice:
 - When you run ``python3 -m pybel`` python will execute
   ``__main__.py`` as a script. That means there won't be any
   ``pybel.__main__`` in ``sys.modules``.
 - When you import __main__ it will get executed again (as a module) because
   there's no ``pybel.__main__`` in ``sys.modules``.
Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

import logging
from pkg_resources import iter_entry_points
import sys
import time

import click
from click_plugins import with_plugins

from .canonicalize import to_bel
from .constants import get_cache_connection
from .io import from_lines, to_csv, to_graphml, to_gsea, to_json_file, to_neo4j, to_pickle, to_sif
from .io.web import _get_host
from .manager import Manager
from .manager.database_io import to_database
from .manager.models import Annotation, Base, Edge, Namespace

log = logging.getLogger(__name__)


def _page(it):
    click.echo_via_pager('\n'.join(map(str, it)))


connection_option = click.option(
    '-c',
    '--connection',
    default=get_cache_connection(),
    help='Connection to cache. Defaults to {}'.format(get_cache_connection()),
)


@with_plugins(iter_entry_points('pybel.cli_plugins'))
@click.group(help="PyBEL Command Line Utilities on {} using default "
                  "connection {}".format(sys.executable, get_cache_connection()))
@click.version_option()
def main():
    """PyBEL Command Line."""


@main.command()
@click.option('-p', '--path', type=click.File('r'), default=sys.stdin, help='Input BEL file file path')
@connection_option
@click.option('--csv', type=click.File('w'), help='Path to output a CSV file.')
@click.option('--sif', type=click.File('w'), help='Path to output an SIF file.')
@click.option('--gsea', type=click.File('w'), help='Path to output a GRP file for gene set enrichment analysis')
@click.option('--graphml', help='Path to output a GraphML file. Use .graphml for Cytoscape')
@click.option('--json', type=click.File('w'), help='Path to output a node-link JSON file.')
@click.option('--pickle', help='Path to output a pickle file.')
@click.option('--bel', type=click.File('w'), help='Output canonical BEL')
@click.option('--neo', help="Connection string for neo4j upload")
@click.option('--neo-context', help="Optional context for neo4j upload")
@click.option('-s', '--store', is_flag=True, help='Stores to database specified by -c')
@click.option('--allow-naked-names', is_flag=True, help="Enable lenient parsing for naked names")
@click.option('--allow-nested', is_flag=True, help="Enable lenient parsing for nested statements")
@click.option('--allow-unqualified-translocations', is_flag=True,
              help="Enable lenient parsing for unqualified translocations")
@click.option('--no-identifier-validation', is_flag=True, help='Turn off identifier validation')
@click.option('--no-citation-clearing', is_flag=True, help='Turn off citation clearing')
@click.option('-r', '--required-annotations', multiple=True, help='Specify multiple required annotations')
def convert(path, connection, csv, sif, gsea, graphml, json, pickle, bel, neo, neo_context, store, allow_naked_names,
            allow_nested, allow_unqualified_translocations, no_identifier_validation, no_citation_clearing,
            required_annotations):
    """Convert BEL."""
    manager = Manager(connection=connection)

    g = from_lines(
        path,
        manager=manager,
        allow_nested=allow_nested,
        allow_naked_names=allow_naked_names,
        allow_unqualified_translocations=allow_unqualified_translocations,
        citation_clearing=(not no_citation_clearing),
        required_annotations=required_annotations,
        no_identifier_validation=no_identifier_validation,
        use_tqdm=True,
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

    if bel:
        log.info('Outputting BEL to %s', bel)
        to_bel(g, bel)

    if store:
        log.info('Storing to database')
        to_database(g, manager=manager, store_parts=True)

    if neo:
        import py2neo
        log.info('Uploading to neo4j with context %s', neo_context)
        neo_graph = py2neo.Graph(neo)
        assert neo_graph.data('match (n) return count(n) as count')[0]['count'] is not None
        to_neo4j(g, neo_graph, neo_context)

    sys.exit(0 if 0 == len(g.warnings) else 1)


@main.command()
@click.argument('agents', nargs=-1)
@click.option('--local', is_flag=True, help='Upload to local database.')
@connection_option
@click.option('--host', help='URL of BEL Commons. Defaults to {}'.format(_get_host()))
def machine(agents, local, connection, host):
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

    if 0 == len(graph):
        click.echo('not uploading empty graph')
        sys.exit(-1)

    if local:
        manager = Manager(connection=connection)
        to_database(graph, manager=manager)
    else:
        resp = to_web(graph, host=host)
        resp.raise_for_status()


@main.group()
@connection_option
@click.pass_context
def manage(ctx, connection):
    """Manage the database."""
    ctx.obj = Manager(connection=connection)
    Base.metadata.bind = ctx.obj.engine
    Base.query = ctx.obj.session.query_property()


@manage.command()
@click.pass_obj
def setup(manager):
    """Create the database, if it doesn't exist."""
    manager.create_all()


@manage.command()
@click.option('-y', '--yes', is_flag=True)
@click.pass_obj
def drop(manager, yes):
    """Drop the database."""
    if yes or click.confirm('Drop database?'):
        manager.drop_all()


@manage.group()
def namespaces():
    """Manage namespaces."""


@manage.group()
def annotations():
    """Manage annotations."""


@namespaces.command()
@click.argument('url')
@click.pass_obj
def insert(manager, url):
    """Add a namespace by URL."""
    manager.ensure_namespace(url)


@annotations.command()
@click.argument('url')
@click.pass_obj
def insert(manager, url):
    """Add an annotation by URL."""
    manager.ensure_annotation(url)


def _ls(manager, model_cls, model_id):
    if model_id:
        n = manager.session.query(model_cls).get(model_id)
        _page(n.entries)

    else:
        for n in manager.session.query(model_cls).order_by(model_cls.uploaded.desc()):
            click.echo('\t'.join(map(str, (n.id, n.keyword, n.version, n.url))))


@namespaces.command()
@click.option('--url', help='Specific resource URL to list')
@click.option('-i', '--namespace-id', help='Specific resource URL to list')
@click.pass_obj
def ls(manager, url, namespace_id):
    """List cached namespaces."""
    if url:
        n = manager.ensure_namespace(url)
        _page(n.entries)
    else:
        _ls(manager, Namespace, namespace_id)


@annotations.command()
@click.option('--url', help='Specific resource URL to list')
@click.option('-i', '--annotation-id', help='Specific resource URL to list')
@click.pass_obj
def ls(manager, url, annotation_id):
    """List cached annotations."""
    if url:
        n = manager.ensure_annotation(url)
        _page(n.entries)
    else:
        _ls(manager, Annotation, annotation_id)


@namespaces.command()
@click.argument('url')
@click.pass_obj
def drop(manager, url):
    """Drop a namespace by URL."""
    manager.drop_namespace_by_url(url)


@annotations.command()
@click.argument('url')
@click.pass_obj
def drop(manager, url):
    """Drop an annotation by URL."""
    manager.drop_annotation_by_url(url)


@manage.group()
def networks():
    """Manage networks."""


@networks.command()
@click.pass_obj
def ls(manager):
    """List network names, versions, and optionally, descriptions."""
    for n in manager.list_networks():
        click.echo('{}\t{}\t{}'.format(n.id, n.name, n.version))


@networks.command()
@click.option('-n', '--network-id', type=int, help='Identifier of network to drop')
@click.option('-y', '--yes', is_flag=True, help='Drop all networks without confirmation if no identifier is given')
@click.pass_obj
def drop(manager, network_id, yes):
    """Drop a network by its identifier or drop all networks."""
    if network_id:
        manager.drop_network_by_id(network_id)

    elif yes or click.confirm('Drop all networks?'):
        manager.drop_networks()


@manage.group()
def edges():
    """Manage edges."""


@edges.command()
@click.option('--offset', type=int)
@click.option('--limit', type=int, default=10)
@click.pass_obj
def ls(manager, offset, limit):
    """List edges."""
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
    """Summarize the contents of the database."""
    click.echo('Networks: {}'.format(manager.count_networks()))
    click.echo('Edges: {}'.format(manager.count_edges()))
    click.echo('Nodes: {}'.format(manager.count_nodes()))
    click.echo('Namespaces: {}'.format(manager.count_namespaces()))
    click.echo('Namespaces entries: {}'.format(manager.count_namespace_entries()))
    click.echo('Annotations: {}'.format(manager.count_annotations()))
    click.echo('Annotation entries: {}'.format(manager.count_annotation_entries()))


if __name__ == '__main__':
    main()
