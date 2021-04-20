# -*- coding: utf-8 -*-

"""Utilities for BEL repositories."""

import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from itertools import chain
from typing import Any, Iterable, Mapping, Optional, Set, TextIO, Tuple, Union

import click
import pandas as pd
from tqdm.autonotebook import tqdm

from .cli import connection_option, host_option, password_option, user_option, verbose_option
from .constants import CITATION
from .io import from_bel_script, to_bel_commons, to_indra_statements
from .io.api import dump, load
from .manager import Manager
from .manager.citation_utils import enrich_pubmed_citations
from .struct import BELGraph
from .struct.operations import union
from .version import get_version

__all__ = [
    'BELMetadata',
    'BELRepository',
    'append_click_group',
]

logger = logging.getLogger(__name__)

private_option = click.option('--private', is_flag=True)

OUTPUT_KWARGS = {
    'nodelink.json': dict(indent=2, sort_keys=True),
    'cx.json': dict(indent=2, sort_keys=True),
    'jgif.json': dict(indent=2, sort_keys=True),
}


@dataclass
class BELMetadata:
    """A container for BEL document metadata."""

    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    authors: Optional[str] = None
    contact: Optional[str] = None
    license: Optional[str] = None
    copyright: Optional[str] = None
    disclaimer: Optional[str] = None

    def new(self) -> BELGraph:
        """Generate a new BEL graph with the given metadata."""
        graph = BELGraph()
        self.update(graph)
        return graph

    def update(self, graph: BELGraph) -> None:
        """Update the BEL graph's metadata."""
        if self.name:
            graph.name = self.name
        if self.version:
            graph.version = self.version
        if self.authors:
            graph.authors = self.authors
        if self.description:
            graph.description = self.description
        if self.contact:
            graph.contact = self.contact
        if self.license:
            graph.licenses = self.license
        if self.copyright:
            graph.copyright = self.copyright
        if self.disclaimer:
            graph.disclaimer = self.disclaimer


@dataclass
class BELRepository:
    """A container for a BEL repository."""

    directory: str
    output_directory: Optional[str] = None

    bel_cache_name: str = '_cache.bel'
    metadata: Optional[BELMetadata] = None
    formats: Tuple[str, ...] = ('pickle', 'nodelink.json')

    #: Must include {file_name} and {extension}
    cache_fmt: str = '{file_name}.{extension}'
    global_summary_ext: str = 'summary.tsv'
    warnings_ext: str = 'warnings.tsv'

    #: Arguments passed to :func:`pybel.from_path` during compilation
    from_path_kwargs: Mapping[str, Any] = field(default_factory=dict)

    #: The location where the summary DataFrame will be output as a TSV.
    bel_summary_path: str = field(init=False)

    def __post_init__(self) -> None:  # noqa: D105
        if self.output_directory is None:
            self.output_directory = self.directory

        self.bel_summary_path = self._build_cache_ext_path(
            root=self.output_directory,
            file_name=self.bel_cache_name,
            extension=self.global_summary_ext.lstrip('.'),
        )

    def _get_global_cache_path_by_extension(self, extension: str) -> str:
        return self._build_cache_ext_path(self.output_directory, self.bel_cache_name, extension)

    def _build_warnings_path(self, root: str, file_name: str) -> str:
        return self._build_cache_ext_path(root, file_name, self.warnings_ext.lstrip('.'))

    def _build_summary_path(self, root: str, file_name: str) -> str:
        return self._build_cache_ext_path(root, file_name, 'summary.json')

    def _build_cache_ext_path(self, root: str, file_name: str, extension: str) -> str:
        return os.path.join(root, self.cache_fmt.format(file_name=file_name, extension=extension.lstrip('.')))

    def walk(self) -> Iterable[Tuple[str, Iterable[str], Iterable[str]]]:
        """Recursively walk this directory."""
        return os.walk(self.directory)

    def iterate_bel(self) -> Iterable[Tuple[str, str]]:
        """Yield all paths to BEL documents."""
        for root, _dirs, file_names in self.walk():
            for file_name in sorted(file_names):
                if not file_name.startswith('_') and file_name.endswith('.bel'):
                    yield root, file_name

    def clear_global_cache(self) -> None:
        """Clear the global cache."""
        self._remove_root_file_name(self.output_directory, self.bel_cache_name)

    def clear_local_caches(self) -> None:
        """Clear all caches of BEL documents in the repository."""
        for root, file_name in self.iterate_bel():
            self._remove_root_file_name(root, file_name)

    def clear_local_warned(self) -> None:
        """Clear caches for BEL documents with errors."""
        for root, file_name in self.iterate_bel():
            if self._has_warnings(root, file_name):
                self._remove_root_file_name(root, file_name)

    def _has_warnings(self, root: str, file_name: str) -> bool:
        return os.path.exists(self._build_warnings_path(root, file_name))

    def _remove_root_file_name(self, root: str, file_name: str) -> None:
        for _, path in self._iterate_extension_path(root, file_name):
            if os.path.exists(path):
                os.remove(path)

    def _iterate_extension_path(self, root: str, file_name: str) -> Iterable[Tuple[str, str]]:
        for extension in self.formats:
            yield extension, self._build_cache_ext_path(root, file_name, extension)

    def _import_local(self, root: str, file_name: str) -> Optional[BELGraph]:
        for _, path in self._iterate_extension_path(root, file_name):
            if os.path.exists(path):
                return load(path)

        return None

    def _import_global(self) -> Optional[BELGraph]:
        return self._import_local(self.output_directory, self.bel_cache_name)

    def _export_local(self, graph: BELGraph, root: str, file_name: str) -> None:
        for extension, path in self._iterate_extension_path(root, file_name):
            kwargs = OUTPUT_KWARGS.get(extension, {})
            dump(graph, path, **kwargs)

        with open(self._build_summary_path(root, file_name), 'w') as file:
            json.dump(graph.summarize.dict(), file, indent=2)

        if graph.warnings:
            logger.info(f' - {graph.number_of_warnings()} warnings')
            warnings_path = self._build_warnings_path(root, file_name)
            warnings_df = pd.DataFrame([
                (exc.line_number, exc.position, exc.line, exc.__class__.__name__, str(exc))
                for _, exc, _ in graph.warnings
            ], columns=['Line Number', 'Position', 'Line', 'Error', 'Message'])
            warnings_df.to_csv(warnings_path, sep='\t', index=False)

    def _export_global(self, graph: BELGraph) -> None:
        self._export_local(graph, self.output_directory, self.bel_cache_name)

    def get_graph(
        self,
        manager: Optional[Manager] = None,
        use_cached: bool = True,
        use_tqdm: bool = False,
        tqdm_kwargs: Optional[Mapping[str, Any]] = None,
        from_path_kwargs: Optional[Mapping[str, Any]] = None,
    ) -> BELGraph:
        """Get a combine graph."""
        if use_cached:
            graph = self._import_global()
            if graph is not None:
                return graph

        graphs = self.get_graphs(
            manager=manager,
            use_tqdm=use_tqdm,
            tqdm_kwargs=tqdm_kwargs,
            from_path_kwargs=from_path_kwargs,
        )
        graph = union(graphs.values())

        if self.metadata is not None:
            self.metadata.update(graph)

        self._get_summary_df_from_graphs(graphs)
        self._export_global(graph)

        return graph

    def get_indra_statements(self, **kwargs):
        """Get INDRA statements for all graphs.

        :rtype: List[indra.statements.Statement]
        """
        return list(chain.from_iterable(
            to_indra_statements(graph)
            for graph in self.get_graphs(**kwargs).values()
        ))

    def get_graphs(
        self,
        manager: Optional[Manager] = None,
        use_cached: bool = True,
        use_tqdm: bool = False,
        tqdm_kwargs: Optional[Mapping[str, Any]] = None,
        from_path_kwargs: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, BELGraph]:
        """Get a mapping of all graphs' paths to their compiled BEL graphs."""
        if manager is None:
            manager = Manager()

        paths = self.iterate_bel()
        if use_tqdm:
            paths = tqdm(list(paths), **(tqdm_kwargs or {}))

        rv = {}
        for root, file_name in paths:
            path = os.path.join(root, file_name)

            if use_cached:
                graph = self._import_local(root, file_name)
                if graph is not None:
                    rv[path] = graph
                    continue

            _from_path_kwargs = from_path_kwargs or {}
            _from_path_kwargs.update(self.from_path_kwargs)

            try:
                graph = rv[path] = from_bel_script(path, manager=manager, **_from_path_kwargs)
                graph.path = os.path.relpath(os.path.join(root, file_name), self.directory)
            except Exception as exc:
                logger.warning(f'problem with {path}: {exc}')
                continue

            enrich_pubmed_citations(graph=graph, manager=manager)
            self._export_local(graph, root, file_name)

        return rv

    def get_summary_df(
        self,
        manager: Optional[Manager] = None,
        use_cached: bool = False,
        use_tqdm: bool = False,
        tqdm_kwargs: Optional[Mapping[str, Any]] = None,
        from_path_kwargs: Optional[Mapping[str, Any]] = None,
        save: Union[bool, str, TextIO] = True,
    ) -> pd.DataFrame:
        """Get a pandas DataFrame summarizing the contents of all graphs in the repository."""
        graphs = self.get_graphs(
            manager=manager,
            use_cached=use_cached,
            use_tqdm=use_tqdm,
            tqdm_kwargs=tqdm_kwargs,
            from_path_kwargs=from_path_kwargs,
        )
        return self._get_summary_df_from_graphs(graphs, save=save)

    def _get_summary_df_from_graphs(self, graphs, save: Union[str, bool, TextIO] = True):
        summary_dicts = {
            os.path.relpath(path, self.directory): graph.summarize.dict()
            for path, graph in graphs.items()
        }

        df = pd.DataFrame.from_dict(summary_dicts, orient='index')

        if isinstance(save, str):
            df.to_csv(save, sep='\t')
        elif save:
            df.to_csv(self.bel_summary_path, sep='\t')

        return df

    def build_cli(self):  # noqa: D202
        """Build a command line interface."""

        @click.group(help=f'Tools for the BEL repository at {self.directory} using PyBEL v{get_version()}')
        @click.pass_context
        def main(ctx):
            """Group the commands."""
            ctx.obj = self

        append_click_group(main)
        return main

    def get_extensions(self, root: str, file_name: str) -> Set[str]:
        """Get all compiled files for the given BEL."""
        # TODO check that this is a valid BEL path!
        return {
            extension
            for extension, path in self._iterate_extension_path(root, file_name)
            if os.path.exists(path)
        }

    def _get_global_caches(self):
        return self.get_extensions(self.output_directory, self.bel_cache_name)

    def _iterate_citations(self, **kwargs) -> Iterable[Tuple[str, str]]:
        """List all citations in documents in this repository."""
        for _, _, data in self.get_graph(**kwargs).edges(data=True):
            citation = data.get(CITATION)
            if citation is not None:
                yield citation.namespace, citation.identifier


def _write_caches(bel_repository: BELRepository, root: str, file_name: str):
    extensions = ', '.join(sorted(bel_repository.get_extensions(root, file_name)))
    has_warnings = os.path.exists(bel_repository._build_warnings_path(root, file_name))

    try:
        with open(bel_repository._build_summary_path(root, file_name)) as file:
            summary = json.load(file)
    except FileNotFoundError:
        summary = None

    if extensions and has_warnings:
        s = click.style('✘️ ', fg='red')
    elif extensions and not has_warnings:
        s = click.style('✔︎ ', fg='green')
    else:
        s = click.style('? ', fg='yellow', bold=True)

    path = os.path.join(root, file_name)
    s += os.path.relpath(path, bel_repository.directory)

    if extensions:
        s += click.style(f' ({extensions})', fg='green')

    if summary:
        s += click.style(f' ({summary["Number of Nodes"]} nodes, {summary["Number of Edges"]} edges)', fg='blue')

    click.echo(s)


def append_click_group(group: click.Group) -> None:  # noqa: D202, C901
    """Append a :py:class:`click.Group`."""

    @group.command()
    @click.pass_obj
    def ls(bel_repository: BELRepository):
        """List the contents of the repository."""
        global_caches = bel_repository._get_global_caches()
        if global_caches:
            click.secho('Global Cache', fg='red', bold=True)
            _write_caches(bel_repository, bel_repository.output_directory, bel_repository.bel_cache_name)
            click.secho('Local Caches', fg='red', bold=True)

        for root, file_name in bel_repository.iterate_bel():
            _write_caches(bel_repository, root, file_name)

    @group.command()
    @click.pass_obj
    def citations(repository: BELRepository):
        """List citations in the repository."""
        for database, reference in sorted(set(repository._iterate_citations(use_tqdm=True)), key=lambda x: int(x[1])):
            click.echo(f'{database}\t{reference}')

    @group.command()
    @host_option
    @user_option
    @password_option
    @click.option('-s', '--sleep', type=int, default=3, help='Seconds to sleep between sending')
    @private_option
    @click.pass_obj
    def upload_separate(repository: BELRepository, host: str, user: str, password: str, sleep: int, private: bool):
        """Upload all to BEL Commons."""
        it = tqdm(repository.get_graphs().items())
        for name, graph in it:
            res = to_bel_commons(graph, host=host, user=user, password=password, public=not private)
            res_json = res.json()
            task_id = res_json.get('task_id')
            if task_id is not None:
                it.write(f'task:{task_id} - {name}')
                it.write(f'see: {host.rstrip("/")}/api/task/{task_id}')
                time.sleep(sleep)
            else:
                it.write(f'problem with {name}: {res_json}')

    @group.command()
    @host_option
    @user_option
    @password_option
    @private_option
    @click.pass_obj
    def upload_combine(repository: BELRepository, host: str, user: str, password: str, private: bool):
        """Upload the combine graph."""
        graph = repository.get_graph()
        res = to_bel_commons(graph, host=host, user=user, password=password, public=not private)
        res_json = res.json()
        task_id = res_json.get('task_id')
        if task_id is not None:
            click.echo(f'task:{task_id} - {graph}')
            click.echo(f'see: {host.rstrip("/")}/api/task/{task_id}')
        else:
            click.echo(f'problem with {graph.name}: {res_json}')

    @group.command()
    @click.confirmation_option()
    @click.pass_obj
    def uncache(bel_repository: BELRepository):
        """Clear the cached data for the repository."""
        bel_repository.clear_global_cache()
        bel_repository.clear_local_caches()

    @group.command()
    @click.confirmation_option()
    @click.pass_obj
    def uncache_global(bel_repository: BELRepository):
        """Clear the cached data for the repository."""
        bel_repository.clear_global_cache()

    @group.command()
    @click.confirmation_option()
    @click.pass_obj
    def uncache_local(bel_repository: BELRepository):
        """Clear the cached data for the repository."""
        bel_repository.clear_local_caches()

    @group.command()
    @click.confirmation_option()
    @click.pass_obj
    def uncache_warned(bel_repository: BELRepository):
        """Clear the cached data for the documents that have warnings."""
        bel_repository.clear_local_warned()

    @group.command()
    @connection_option
    @click.option('-r', '--reload', is_flag=True)
    @click.option('--no-tqdm', is_flag=True)
    @verbose_option
    @click.pass_obj
    def compile(bel_repository: BELRepository, connection: str, reload: bool, no_tqdm: bool):
        """Summarize the repository."""
        if reload:
            bel_repository.clear_global_cache()
            bel_repository.clear_local_caches()

        manager = Manager(connection=connection)
        graph = bel_repository.get_graph(
            manager=manager,
            use_cached=(not reload),
            use_tqdm=(not no_tqdm),
            tqdm_kwargs=dict(
                desc='Loading BEL',
                leave=False,
            ),
            from_path_kwargs=dict(
                use_tqdm=(not no_tqdm),
                tqdm_kwargs=dict(
                    leave=False,
                ),
            ),
        )
        click.echo(graph.summarize.str())

    @group.command()
    @click.argument('file', type=click.File('w'))
    @click.pass_obj
    def html(bel_repository: BELRepository, file: TextIO):
        """Output an HTML summary."""
        graph = bel_repository.get_graph()
        try:
            from pybel_tools.assembler.html import to_html_file
        except ImportError:
            click.secho('pybel_tools.assembler.html is not available', fg='red')
            sys.exit(1)
        else:
            to_html_file(graph, file)


@click.group()
@click.version_option()
@click.option(
    '-d', '--directory',
    default=os.getcwd(), type=click.Path(file_okay=False, dir_okay=True, exists=True),
    help='Defaults to current working directory',
)
@click.pass_context
def main(ctx, directory: str):
    """Command line interface for bel-repository."""
    ctx.obj = BELRepository(directory=directory)


append_click_group(main)

if __name__ == '__main__':
    main()
