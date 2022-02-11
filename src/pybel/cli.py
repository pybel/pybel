# -*- coding: utf-8 -*-

"""Command line interface for PyBEL.

Why does this file exist, and why not put this in ``__main__``? You might be tempted to import things from ``__main__``
later, but that will cause problems--the code will get executed twice:

- When you run ``python3 -m pybel`` python will execute``__main__.py`` as a script. That means there won't be any
  ``pybel.__main__`` in ``sys.modules``.
- When you import __main__ it will get executed again (as a module) because
  there's no ``pybel.__main__`` in ``sys.modules``.

.. seealso:: http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

import json
import logging
import os
import sys
import time
from typing import List, Optional

import click
from click_plugins import with_plugins
from pkg_resources import iter_entry_points
from tqdm.autonotebook import tqdm

from .canonicalize import to_bel_script
from .constants import get_cache_connection
from .examples import (
    braf_graph,
    egf_graph,
    homology_graph,
    sialic_acid_graph,
    statin_graph,
)
from .exceptions import BELParserWarning
from .io import (
    from_bel_script,
    from_pickle,
    load,
    to_bel_commons,
    to_edgelist,
    to_graphml,
    to_gsea,
    to_neo4j,
    to_nodelink_file,
    to_pickle,
    to_sif,
    to_triples_file,
)
from .io.bel_commons_client import _get_host, _get_password, _get_user
from .manager import Manager
from .manager.database_io import to_database
from .manager.models import Edge, Namespace, Node
from .struct import (
    get_unused_annotations,
    get_unused_list_annotation_values,
    get_unused_namespaces,
)
from .struct.graph import BELGraph, WarningTuple
from .utils import get_corresponding_pickle_path

logger = logging.getLogger(__name__)


def _page(it):
    click.echo_via_pager("\n".join(map(str, it)))


connection_option = click.option(
    "-c",
    "--connection",
    default=get_cache_connection(),
    show_default=True,
    help="Database connection string.",
)

host_option = click.option(
    "--host",
    default=_get_host(),
    show_default=True,
    help="URL of BEL Commons.",
)
user_option = click.option(
    "--user",
    default=_get_user,
    show_default=True,
    prompt=True,
    help="User for BEL Commons",
)
password_option = click.option(
    "--password",
    default=_get_password,
    show_default=True,
    prompt=True,
    hide_input=True,
    help="Password for BEL Commons",
)


def _from_pickle_callback(ctx, param, file):
    path = file.name

    if not path.endswith(".bel"):
        return from_pickle(file)

    cache_path = get_corresponding_pickle_path(path)

    if not os.path.exists(cache_path):
        click.echo(
            "The BEL script {path} has not yet been compiled. First, try running the following command:\n\n "
            "pybel compile {path}\n".format(path=path),
        )
        sys.exit(1)

    return from_pickle(cache_path)


graph_pickle_argument = click.argument(
    "graph",
    metavar="path",
    type=click.File("rb"),
    callback=_from_pickle_callback,
)

graph_argument = click.argument(
    "graph",
    metavar="path",
    callback=lambda _, __, path: load(path),
)

LOG_FMT = "%(asctime)s %(levelname)-8s %(message)s"
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"


def _debug_callback(_ctx, _param, value):
    if not value:
        logging.basicConfig(level=logging.WARNING, format=LOG_FMT, datefmt=LOG_DATEFMT)
    elif value == 1:
        logging.basicConfig(level=logging.INFO, format=LOG_FMT, datefmt=LOG_DATEFMT)
    else:
        logging.basicConfig(level=logging.DEBUG, format=LOG_FMT, datefmt=LOG_DATEFMT)


verbose_option = click.option(
    "-v",
    "--verbose",
    count=True,
    callback=_debug_callback,
    expose_value=False,
)


@with_plugins(iter_entry_points("pybel.cli_plugins"))
@click.group(help="PyBEL CLI on {}".format(sys.executable))
@click.version_option()
@connection_option
@click.pass_context
def main(ctx, connection):
    """Command line interface for PyBEL."""
    ctx.obj = Manager(connection=connection)
    ctx.obj.bind()  # add the engine to the metadata and query property to the session


@main.command()
@click.argument("text")
@click.option("--pprint", is_flag=True)
def parse(text: str, pprint: bool):
    """Parse a single BEL statement and pring JSON output."""
    from .parser.parse_bel import parse as _parse

    click.echo(json.dumps(_parse(text), indent=2 if pprint else None))


@main.command()
@click.argument("path")
@click.option("--allow-naked-names", is_flag=True, help="Enable lenient parsing for naked names")
@click.option(
    "--disallow-nested",
    is_flag=True,
    help="Disable lenient parsing for nested statements",
)
@click.option(
    "--disallow-unqualified-translocations",
    is_flag=True,
    help="Disallow unqualified translocations",
)
@click.option("--no-identifier-validation", is_flag=True, help="Turn off identifier validation")
@click.option("--no-citation-clearing", is_flag=True, help="Turn off citation clearing")
@click.option(
    "-r",
    "--required-annotations",
    multiple=True,
    help="Specify multiple required annotations",
)
@click.option("--upgrade-urls", is_flag=True)
@click.option("--skip-tqdm", is_flag=True)
@verbose_option
@click.pass_obj
def compile(
    manager,
    path,
    allow_naked_names,
    disallow_nested,
    disallow_unqualified_translocations,
    no_identifier_validation,
    no_citation_clearing,
    required_annotations,
    upgrade_urls,
    skip_tqdm,
):
    """Compile a BEL script to a graph."""
    logger.debug("using connection: %s", manager.engine.url)

    click.secho("Compilation", fg="red", bold=True)
    if skip_tqdm:
        click.echo("```")
    graph = from_bel_script(
        path,
        manager=manager,
        use_tqdm=(not skip_tqdm),
        disallow_nested=disallow_nested,
        allow_naked_names=allow_naked_names,
        disallow_unqualified_translocations=disallow_unqualified_translocations,
        citation_clearing=(not no_citation_clearing),
        required_annotations=required_annotations,
        no_identifier_validation=no_identifier_validation,
        allow_definition_failures=True,
        upgrade_urls=upgrade_urls,
    )
    if skip_tqdm:
        click.echo("```")
    to_pickle(graph, get_corresponding_pickle_path(path))

    click.echo("")
    _print_summary(graph, ticks=skip_tqdm)

    sys.exit(0 if 0 == graph.number_of_warnings() else 1)


@main.command()
@graph_pickle_argument
def summarize(graph: BELGraph):
    """Summarize a graph."""
    _print_summary(graph)


def _print_summary(graph: BELGraph, ticks: bool = False):
    if not ticks:
        click.secho("Summary", fg="red", bold=True)
        graph.summarize()

    unused_namespaces = get_unused_namespaces(graph)
    if unused_namespaces:
        click.secho(
            "\nUnused Namespaces ({}/{})".format(len(unused_namespaces), len(graph.defined_namespace_keywords)),
            fg="red",
            bold=True,
        )
        if ticks:
            click.echo("```")
        for namespace in sorted(unused_namespaces):
            click.echo(namespace)
        if ticks:
            click.echo("```")

    unused_annotations = get_unused_annotations(graph)
    if unused_annotations:
        click.secho(
            "\nUnused Annotations ({}/{})".format(len(unused_annotations), len(graph.defined_annotation_keywords)),
            fg="red",
            bold=True,
        )
        if ticks:
            click.echo("```")
        for annotation in sorted(unused_annotations):
            click.echo(annotation)
        if ticks:
            click.echo("```")

    unused_annotation_list_values = get_unused_list_annotation_values(graph)
    if unused_annotation_list_values:
        click.secho("\nUnused List Annotation Values", fg="red", bold=True)
        if ticks:
            click.echo("```")
        for annotation, values in sorted(unused_annotation_list_values.items()):
            click.echo("{} ({}/{})".format(annotation, len(values), len(graph.annotation_list[annotation])))
            for value in sorted(values):
                click.echo("  {}".format(value))
        if ticks:
            click.echo("```")


@main.command()
@graph_pickle_argument
def warnings(graph: BELGraph):
    """List warnings from a graph."""
    echo_warnings_via_pager(graph.warnings)


@main.command()
@graph_pickle_argument
@click.pass_obj
def insert(manager, graph: BELGraph):
    """Insert a graph to the database."""
    to_database(graph, manager=manager, use_tqdm=True)


@main.command()
@graph_argument
@host_option
@user_option
@password_option
def upload(graph: BELGraph, host: str, user: str, password: str):
    """Upload a graph to BEL Commons."""
    resp = to_bel_commons(graph, host=host, user=user, password=password)
    resp.raise_for_status()
    click.echo(json.dumps(resp.json()))


@main.command()
@graph_pickle_argument
@click.option("--tsv", type=click.File("w"), help="Path to output a TSV file.")
@click.option("--edgelist", type=click.File("w"), help="Path to output a edgelist file.")
@click.option("--sif", type=click.File("w"), help="Path to output an SIF file.")
@click.option(
    "--gsea",
    type=click.File("w"),
    help="Path to output a GRP file for gene set enrichment analysis.",
)
@click.option("--graphml", help="Path to output a GraphML file. Use .graphml for Cytoscape.")
@click.option("--nodelink", type=click.File("w"), help="Path to output a node-link JSON file.")
@click.option("--bel", type=click.File("w"), help="Output canonical BEL.")
def serialize(graph: BELGraph, tsv, edgelist, sif, gsea, graphml, nodelink, bel):
    """Serialize a graph to various formats."""
    if tsv:
        logger.info("Outputting TSV to %s", tsv)
        to_triples_file(graph, tsv)

    if edgelist:
        logger.info("Outputting edgelist to %s", edgelist)
        to_edgelist(graph, edgelist)

    if sif:
        logger.info("Outputting SIF to %s", sif)
        to_sif(graph, sif)

    if graphml:
        logger.info("Outputting GraphML to %s", graphml)
        to_graphml(graph, graphml)

    if gsea:
        logger.info("Outputting GRP to %s", gsea)
        to_gsea(graph, gsea)

    if nodelink:
        logger.info("Outputting Nodelink JSON to %s", nodelink)
        to_nodelink_file(graph, nodelink)

    if bel:
        logger.info("Outputting BEL script to %s", bel)
        to_bel_script(graph, bel)


@main.command()
@graph_pickle_argument
@click.option(
    "--connection",
    default="http://localhost:7474/db/data/",
    help="Connection string for neo4j upload.",
)
@click.password_option()
def neo(graph: BELGraph, connection: str, password: str):
    """Upload to neo4j."""
    import py2neo

    neo_graph = py2neo.Graph(connection, password=password)
    to_neo4j(graph, neo_graph)


@main.command()
@click.pass_obj
@click.argument("agents", nargs=-1)
@click.option("--local", is_flag=True, help="Upload to local database.")
@host_option
def machine(manager: Manager, agents: List[str], local: bool, host: str):
    """Get content from the INDRA machine and upload to BEL Commons."""
    from indra.sources import indra_db_rest

    from pybel import from_indra_statements

    statements = indra_db_rest.get_statements(agents=agents)
    click.echo("got {} statements from INDRA".format(len(statements)))

    graph = from_indra_statements(
        statements,
        name="INDRA Machine for {}".format(", ".join(sorted(agents))),
        version=time.strftime("%Y%m%d"),
    )
    click.echo("built BEL graph with {} nodes and {} edges".format(graph.number_of_nodes(), graph.number_of_edges()))

    if 0 == len(graph):
        click.echo("not uploading empty graph")
        sys.exit(-1)

    if local:
        to_database(graph, manager=manager)
    else:
        resp = to_bel_commons(graph, host=host)
        resp.raise_for_status()


@main.group()
def manage():
    """Manage the database."""


@manage.command()
@click.confirmation_option()
@click.pass_obj
def drop(manager: Manager):
    """Drop the database."""
    manager.drop_all()


@manage.command()
@click.option("-v", "--debug", is_flag=True)
@click.pass_obj
def examples(manager: Manager, debug: bool):
    """Load examples to the database."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level)
    logging.getLogger("pybel").setLevel(level)

    for graph in (
        sialic_acid_graph,
        statin_graph,
        homology_graph,
        braf_graph,
        egf_graph,
    ):
        if manager.has_name_version(graph.name, graph.version):
            click.echo("already inserted {}".format(graph))
            continue
        click.echo("inserting {}".format(graph))
        manager.insert_graph(graph, use_tqdm=True)


@manage.group()
def namespaces():
    """Manage namespaces."""


@namespaces.command()  # noqa:F811
@click.argument("url")
@click.pass_obj
def insert(manager: Manager, url: str):
    """Add a namespace by URL."""
    manager.get_or_create_namespace(url)


def _ls(manager: Manager, model_cls, model_id: int):
    if model_id:
        n = manager.session.query(model_cls).get(model_id)
        _page(n.entries)

    else:
        for n in manager.session.query(model_cls).order_by(model_cls.uploaded.desc()):
            click.echo("\t".join(map(str, (n.id, n.keyword, n.version, n.url))))


@namespaces.command()
@click.option("-u", "--url", help="Specific resource URL to list")
@click.option("-i", "--namespace-id", type=int, help="Specific resource URL to list")
@click.pass_obj
def ls(manager: Manager, url: Optional[str], namespace_id: Optional[int]):
    """List cached namespaces."""
    if url:
        n = manager.get_or_create_namespace(url)
        _page(n.entries)
    elif namespace_id is not None:
        _ls(manager, Namespace, namespace_id)
    else:
        click.echo_via_pager(
            "\n".join("{}\t{}\t{}".format(n.id, n.name, n.url) for n in manager.session.query(Namespace)),
        )


@namespaces.command()  # noqa:F811
@click.argument("url")
@click.pass_obj
def drop(manager: Manager, url: str):
    """Drop a namespace by URL."""
    manager.drop_namespace_by_url(url)


@manage.group()
def networks():
    """Manage networks."""


@networks.command()  # noqa:F811
@click.pass_obj
def ls(manager: Manager):
    """List network names, versions, and optionally, descriptions."""
    for n in manager.list_networks():
        click.echo("{}\t{}\t{}".format(n.id, n.name, n.version))


@networks.command()  # noqa:F811
@click.option("-n", "--network-id", type=int, help="Identifier of network to drop")
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Drop all networks without confirmation if no identifier is given",
)
@click.pass_obj
def drop(manager: Manager, network_id: Optional[int], yes):
    """Drop a network by its identifier or drop all networks."""
    if network_id:
        manager.drop_network_by_id(network_id)

    elif yes or click.confirm("Drop all networks?"):
        manager.drop_networks()


@manage.group()
def edges():
    """Manage edges."""


@edges.command()  # noqa:F811
@click.option("--offset", type=int)
@click.option("--limit", type=int, default=10)
@click.pass_obj
def ls(manager: Manager, offset: Optional[int], limit: Optional[int]):
    """List edges."""
    q = manager.session.query(Edge)

    if offset:
        q = q.offset(offset)

    if limit > 0:
        q = q.limit(limit)

    for e in q:
        click.echo(e.bel)


@manage.group()
def nodes():
    """Manage nodes."""


@nodes.command()
@click.pass_obj
def prune(manager: Manager):
    """Prune nodes not belonging to any edges."""
    nodes_to_delete = [
        node for node in tqdm(manager.session.query(Node), total=manager.count_nodes()) if not node.networks
    ]
    manager.session.delete(nodes_to_delete)
    manager.session.commit()


@manage.command()  # noqa:F811
@click.pass_obj
def summarize(manager: Manager):
    """Summarize the contents of the database."""
    click.echo("Networks: {}".format(manager.count_networks()))
    click.echo("Edges: {}".format(manager.count_edges()))
    click.echo("Nodes: {}".format(manager.count_nodes()))
    click.echo("Namespaces: {}".format(manager.count_namespaces()))
    click.echo("Namespaces entries: {}".format(manager.count_namespace_entries()))
    click.echo("Annotations: {}".format(manager.count_annotations()))
    click.echo("Annotation entries: {}".format(manager.count_annotation_entries()))


def echo_warnings_via_pager(warnings: List[WarningTuple], sep: str = "\t") -> None:
    """Output the warnings from a BEL graph with Click and the system's pager."""
    # Exit if no warnings
    if not warnings:
        click.echo("Congratulations! No warnings.")
        sys.exit(0)

    max_line_width = max(len(str(exc.line_number)) for _, exc, _ in warnings)

    max_warning_width = max(len(exc.__class__.__name__) for _, exc, _ in warnings)

    s1 = "{:>" + str(max_line_width) + "}" + sep
    s2 = "{:>" + str(max_warning_width) + "}" + sep

    def _make_line(path: str, exc: BELParserWarning):
        s = click.style(path, fg="cyan") + sep
        s += click.style(s1.format(exc.line_number), fg="blue", bold=True)
        s += click.style(
            s2.format(exc.__class__.__name__),
            fg=("red" if exc.__class__.__name__.endswith("Error") else "yellow"),
        )
        s += click.style(exc.line, bold=True) + sep
        s += click.style(str(exc))
        return s

    click.echo_via_pager(
        "\n".join(_make_line(path, exc) for path, exc, _ in warnings),
    )


if __name__ == "__main__":
    main()
