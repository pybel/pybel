import logging

from sqlalchemy.exc import IntegrityError

from .graph_cache import GraphCacheManager

__all__ = [
    'to_database',
    'from_database'
]

log = logging.getLogger(__name__)


def build_graph_cache_manager(connection=None):
    if isinstance(connection, GraphCacheManager):
        return connection
    return GraphCacheManager(connection=connection)


def to_database(graph, connection=None):
    """Stores a graph in a database

    :param graph: a BEL graph
    :type graph: BELGraph
    :param connection: The string form of the URL is :code:`dialect[+driver]://user:password@host/dbname[?key=value..]`,
                       where dialect is a database name such as mysql, oracle, postgresql, etc., and driver the name
                       of a DBAPI, such as psycopg2, pyodbc, cx_oracle, etc. Alternatively, the URL can be an instance
                       of URL
    :type connection: None or str or GraphCacheManager
    """
    try:
        build_graph_cache_manager(connection).insert_graph(graph)
    except IntegrityError:
        log.exception('Error storing graph - other graph with same metadata'
                      ' already present. Consider incrementing the version')


def from_database(name, version=None, connection=None):
    """Loads a BEL graph from a database


    :param name: The name of the graph
    :type name: str
    :param version: The version string of the graph. If not specified, loads most recent graph added with this name
    :type version: str
    :param connection: The string form of the URL is :code:`dialect[+driver]://user:password@host/dbname[?key=value..]`,
                       where dialect is a database name such as mysql, oracle, postgresql, etc., and driver the name
                       of a DBAPI, such as psycopg2, pyodbc, cx_oracle, etc. Alternatively, the URL can be an instance
                       of URL.
    :type connection: None or str or GraphCacheManager
    :return: a BEL graph loaded from the database
    :rtype: BELGraph
    """
    return build_graph_cache_manager(connection).get_graph(name, version)
