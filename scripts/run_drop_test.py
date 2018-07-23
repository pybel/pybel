# -*- coding: utf-8 -*-

"""Test loading and dropping a network."""

import os
import time
from contextlib import contextmanager

import click

import pybel

DEFAULT_CONNECTION = 'mysql+mysqldb://root@localhost/pbt?charset=utf8'
PICKLE = 'small_corpus.bel.gpickle'
SMALL_CORPUS_URL = 'https://arty.scai.fraunhofer.de/artifactory/bel/knowledge/selventa-small-corpus/selventa-small-corpus-20150611.bel'


@contextmanager
def time_me(start_string):
    """Wrap statements with time logging."""
    print(start_string)
    parse_start_time = time.time()
    yield
    print(f'ran in {time.time() - parse_start_time:.2f} seconds')


def get_numbers(graph, connection=None):
    manager = pybel.Manager.from_connection(connection if connection else DEFAULT_CONNECTION)
    print('inserting')
    parse_start_time = time.time()
    network = manager.insert_graph(graph)
    print(f'inserted in {time.time() - parse_start_time:.2f} seconds')

    print('dropping')
    drop_start_time = time.time()
    manager.drop_network(network)
    drop_time = time.time() - drop_start_time
    print(f'dropped in {drop_time:.2f} seconds')

    return drop_time


@click.command()
@click.option('--connection', help=f'SQLAlchemy connection. Defaults to {DEFAULT_CONNECTION}')
def main(connection):
    """Parse a network, load it to the database, then test how fast it drops."""

    if os.path.exists(PICKLE):
        print(f'opening from {PICKLE}')
        graph = pybel.from_pickle(PICKLE)
    else:
        with time_me(f'opening from {SMALL_CORPUS_URL}'):
            manager = pybel.Manager.from_connection(connection if connection else DEFAULT_CONNECTION)
            graph = pybel.from_url(SMALL_CORPUS_URL, manager=manager, use_tqdm=True, citation_clearing=False)

        pybel.to_pickle(graph, PICKLE)

    n = 1
    # FIXME this fails if you do it with the same manager

    times = [
        get_numbers(graph, connection)
        for _ in range(n)
    ]

    print(times)
    print(sum(times) / n)


if __name__ == '__main__':
    main()
