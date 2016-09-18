import os
import sys

import click
import py2neo

from .graph import from_url, from_file


@click.group(help="PyBEL Command Line Utilities")
def cli():
    pass


@cli.command()
@click.option('--url')
@click.option('--path')
@click.option('--neo-url', default='localhost')
@click.option('--neo-port', type=int, default=7474)
@click.option('--neo-user', default='neo4j')
@click.option('--neo-pass', default='neo4j')
def to_neo(url, path, neo_url, neo_port, neo_user, neo_pass):
    """Parses BEL file and uploads to Neo4J"""
    if url:
        g = from_url(url)
    elif path:
        with open(os.path.expanduser(path)) as f:
            g = from_file(f)
    else:
        sys.exit(-1)

    py2neo.authenticate('{}:{}'.format(neo_url, neo_port), neo_user, neo_pass)
    p2n = py2neo.Graph()

    g.to_neo4j(p2n)


if __name__ == '__main__':
    cli()
