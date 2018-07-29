# -*- coding: utf-8 -*-

"""Conversion functions for BEL graphs with a SQL database."""

import logging

from sqlalchemy.exc import IntegrityError, OperationalError

from .cache_manager import Manager

__all__ = [
    'to_database',
    'from_database'
]

log = logging.getLogger(__name__)


def to_database(graph, manager=None, store_parts=True):
    """Store a graph in a database.

    :param BELGraph graph: A BEL graph
    :type manager: Optional[pybel.manager.Manager]
    :param bool store_parts: Should the graph be stored in the edge store?
    :return: If successful, returns the network object from the database.
    :rtype: Optional[Network]
    """
    if manager is None:
        manager = Manager()

    try:
        return manager.insert_graph(graph, store_parts=store_parts)
    except (IntegrityError, OperationalError):
        manager.session.rollback()
        log.exception('Error storing graph')
    except Exception as e:
        manager.session.rollback()
        raise e


def from_database(name, version=None, manager=None):
    """Load a BEL graph from a database.

    If name and version are given, finds it exactly with
    :meth:`pybel.manager.Manager.get_network_by_name_version`. If just the name is given, finds most recent
    with :meth:`pybel.manager.Manager.get_network_by_name_version`

    :param str name: The name of the graph
    :param Optional[str] version: The version string of the graph. If not specified, loads most recent graph added
     with this name
    :type manager: Optional[pybel.manager.Manager]
    :return: A BEL graph loaded from the database
    :rtype: Optional[BELGraph]
    """
    if manager is None:
        manager = Manager()

    if version is None:
        return manager.get_graph_by_most_recent(name)

    return manager.get_graph_by_name_version(name, version)
