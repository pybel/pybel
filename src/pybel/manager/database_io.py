# -*- coding: utf-8 -*-

"""This module provides IO functions to the relational edge store"""

import logging

from sqlalchemy.exc import IntegrityError, OperationalError

from .cache import build_manager

__all__ = [
    'to_database',
    'from_database'
]

log = logging.getLogger(__name__)


def to_database(graph, connection=None, store_parts=False):
    """Stores a graph in a database

    :param graph: A BEL graph
    :type graph: BELGraph
    :param connection: The string form of the URL is :code:`dialect[+driver]://user:password@host/dbname[?key=value..]`,
                       where dialect is a database name such as mysql, oracle, postgresql, etc., and driver the name
                       of a DBAPI, such as psycopg2, pyodbc, cx_oracle, etc. Alternatively, the URL can be an instance
                       of URL
    :type connection: None or str or pybel.manager.cache.CacheManager
    :param store_parts: Should the graph be stored in the edge store?
    :type store_parts: bool
    """
    manager = build_manager(connection=connection)

    try:
        manager.insert_graph(graph, store_parts=store_parts)
    except IntegrityError:
        manager.rollback()
        log.exception('Error storing graph - other graph with same metadata'
                      ' already present. Consider incrementing the version')
    except OperationalError:
        manager.rollback()
        log.exception('Error storing graph - operational exception')
    except Exception as e:
        manager.rollback()
        raise e


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
    :type connection: None or str or pybel.manager.cache.CacheManager
    :return: A BEL graph loaded from the database
    :rtype: BELGraph
    """
    manager = build_manager(connection=connection)
    return manager.get_graph(name, version)
