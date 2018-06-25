# -*- coding: utf-8 -*-

"""This module contains the base class for connection managers in SQLAlchemy"""

from __future__ import unicode_literals

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .models import Base
from ..constants import config

__all__ = [
    'BaseManager',
    'build_engine_session',
]

log = logging.getLogger(__name__)


def build_engine_session(connection, echo=False, autoflush=None, autocommit=None, expire_on_commit=None,
                         scopefunc=None):
    """Build an engine and a session.

    :param str connection: An RFC-1738 database connection string
    :param bool echo: Turn on echoing SQL
    :param Optional[bool] autoflush: Defaults to True if not specified in kwargs or configuration.
    :param Optional[bool] autocommit: Defaults to False if not specified in kwargs or configuration.
    :param Optional[bool] expire_on_commit: Defaults to False if not specified in kwargs or configuration.
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
        scopefunc=scopefunc
    )

    return engine, session


class BaseManager(object):
    """A wrapper around a SQLAlchemy engine and session."""

    def __init__(self, engine, session):
        """Instantiate a manager from an engine and session."""
        self.engine = engine
        self.session = session

    @classmethod
    def from_connection(cls, connection, echo=True, autoflush=None, autocommit=None, expire_on_commit=None,
                        scopefunc=None):
        """Create a connection to database and a persistent session using SQLAlchemy.

        A custom default can be set as an environment variable with the name :data:`pybel.constants.PYBEL_CONNECTION`,
        using an `RFC-1738 <http://rfc.net/rfc1738.html>`_ string. For example, a MySQL string can be given with the
        following form:

        :code:`mysql+pymysql://<username>:<password>@<host>/<dbname>?charset=utf8[&<options>]`

        A SQLite connection string can be given in the form:

        ``sqlite:///~/Desktop/cache.db``

        Further options and examples can be found on the SQLAlchemy documentation on
        `engine configuration <http://docs.sqlalchemy.org/en/latest/core/engines.html>`_.

        :param str connection: An RFC-1738 database connection string.
        :param bool echo: Turn on echoing sql
        :param Optional[bool] autoflush: Defaults to True if not specified in kwargs or configuration.
        :param Optional[bool] autocommit: Defaults to False if not specified in kwargs or configuration.
        :param Optional[bool] expire_on_commit: Defaults to False if not specified in kwargs or configuration.
        :param scopefunc: Scoped function to pass to :func:`sqlalchemy.orm.scoped_session`

        From the Flask-SQLAlchemy documentation:

        An extra key ``'scopefunc'`` can be set on the ``options`` dict to
        specify a custom scope function.  If it's not provided, Flask's app
        context stack identity is used. This will ensure that sessions are
        created and removed with the request/response cycle, and should be fine
        in most cases.
        """
        engine, session = build_engine_session(
            connection,
            echo=echo,
            autoflush=autoflush,
            autocommit=autocommit,
            expire_on_commit=expire_on_commit,
            scopefunc=scopefunc,
        )
        return cls(engine=engine, session=session)

    def create_all(self, checkfirst=True):
        """Create the PyBEL cache's database and tables.

        :param bool checkfirst: Check if the database exists before trying to re-make it
        """
        Base.metadata.create_all(bind=self.engine, checkfirst=checkfirst)

    def drop_all(self, checkfirst=True):
        """Drop all data, tables, and databases for the PyBEL cache.

        :param bool checkfirst: Check if the database exists before trying to drop it
        """
        Base.metadata.drop_all(bind=self.engine, checkfirst=checkfirst)

    def __repr__(self):
        return '<{} connection={}>'.format(self.__class__.__name__, self.engine.url)
