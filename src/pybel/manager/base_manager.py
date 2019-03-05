# -*- coding: utf-8 -*-

"""This module contains the base class for connection managers in SQLAlchemy."""

import logging
from typing import List, Optional, Tuple, Type, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .models import Base
from ..config import config

__all__ = [
    'BaseManager',
    'build_engine_session',
]

log = logging.getLogger(__name__)

X = TypeVar('X')


def build_engine_session(connection: str,
                         echo: bool = False,
                         autoflush: Optional[bool] = None,
                         autocommit: Optional[bool] = None,
                         expire_on_commit: Optional[bool] = None,
                         scopefunc=None) -> Tuple:
    """Build an engine and a session.

    :param connection: An RFC-1738 database connection string
    :param echo: Turn on echoing SQL
    :param autoflush: Defaults to True if not specified in kwargs or configuration.
    :param autocommit: Defaults to False if not specified in kwargs or configuration.
    :param expire_on_commit: Defaults to False if not specified in kwargs or configuration.
    :param scopefunc: Scoped function to pass to :func:`sqlalchemy.orm.scoped_session`
    :rtype: tuple[Engine,Session]

    From the Flask-SQLAlchemy documentation:

    An extra key ``'scopefunc'`` can be set on the ``options`` dict to
    specify a custom scope function.  If it's not provided, Flask's app
    context stack identity is used. This will ensure that sessions are
    created and removed with the request/response cycle, and should be fine
    in most cases.
    """
    if connection is None:
        raise ValueError('can not build engine when connection is None')

    engine = create_engine(connection, echo=echo)

    if autoflush is None:
        autoflush = config.get('PYBEL_MANAGER_AUTOFLUSH', False)

    if autocommit is None:
        autocommit = config.get('PYBEL_MANAGER_AUTOCOMMIT', False)

    if expire_on_commit is None:
        expire_on_commit = config.get('PYBEL_MANAGER_AUTOEXPIRE', True)

    log.debug('auto flush: %s, auto commit: %s, expire on commmit: %s', autoflush, autocommit, expire_on_commit)

    #: A SQLAlchemy session maker
    session_maker = sessionmaker(
        bind=engine,
        autoflush=autoflush,
        autocommit=autocommit,
        expire_on_commit=expire_on_commit,
    )

    #: A SQLAlchemy session object
    session = scoped_session(
        session_maker,
        scopefunc=scopefunc,
    )

    return engine, session


class BaseManager(object):
    """A wrapper around a SQLAlchemy engine and session."""

    #: The declarative base for this manager
    base = Base

    def __init__(self, engine, session) -> None:
        """Instantiate a manager from an engine and session."""
        self.engine = engine
        self.session = session

    def create_all(self, checkfirst: bool = True) -> None:
        """Create the PyBEL cache's database and tables.

        :param checkfirst: Check if the database exists before trying to re-make it
        """
        self.base.metadata.create_all(bind=self.engine, checkfirst=checkfirst)

    def drop_all(self, checkfirst: bool = True) -> None:
        """Drop all data, tables, and databases for the PyBEL cache.

        :param checkfirst: Check if the database exists before trying to drop it
        """
        self.session.close()
        self.base.metadata.drop_all(bind=self.engine, checkfirst=checkfirst)

    def bind(self) -> None:
        """Bind the metadata to the engine and session."""
        self.base.metadata.bind = self.engine
        self.base.query = self.session.query_property()

    def _list_model(self, model_cls: Type[X]) -> List[X]:
        """List the models in this class."""
        return self.session.query(model_cls).all()

    def _count_model(self, model_cls) -> int:
        """Count the number of models in the database."""
        return self.session.query(model_cls).count()

    def __repr__(self):
        return '<{} connection={}>'.format(self.__class__.__name__, self.engine.url)
