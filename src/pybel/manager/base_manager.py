# -*- coding: utf-8 -*-

"""This module contains the base class for connection managers in SQLAlchemy"""

from __future__ import unicode_literals

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .models import Base
from ..constants import config, get_cache_connection

__all__ = [
    'BaseManager'
]

log = logging.getLogger(__name__)


class BaseManager(object):
    """Creates a connection to database and a persistent session using SQLAlchemy
    
    A custom default can be set as an environment variable with the name :data:`pybel.constants.PYBEL_CONNECTION`,  
    using an `RFC-1738 <http://rfc.net/rfc1738.html>`_ string. For example, a MySQL string can be given with the 
    following form:  
    
    :code:`mysql+pymysql://<username>:<password>@<host>/<dbname>?charset=utf8[&<options>]`
    
    A SQLite connection string can be given in the form:
    
    ``sqlite:///~/Desktop/cache.db``
    
    Further options and examples can be found on the SQLAlchemy documentation on 
    `engine configuration <http://docs.sqlalchemy.org/en/latest/core/engines.html>`_.
    """

    def __init__(self, connection=None, echo=False, autoflush=None, autocommit=None, expire_on_commit=None,
                 scopefunc=None):
        """
        :param str connection: An RFC-1738 database connection string. If ``None``, tries to load from the environment
                                variable ``PYBEL_CONNECTION`` then from the config file ``~/.config/pybel/config.json``
                                whose value for ``PYBEL_CONNECTION`` defaults to 
                                :data:`pybel.constants.DEFAULT_CACHE_LOCATION`

        :param bool echo: Turn on echoing sql
        :param bool autoflush: Defaults to True if not specified in kwargs or configuration.
        :param bool autocommit: Defaults to False if not specified in kwargs or configuration.
        :param bool expire_on_commit: Defaults to False if not specified in kwargs or configuration.
        :param scopefunc: Scoped function to pass to :func:`sqlalchemy.orm.scoped_session`


        From the Flask-SQLAlchemy documentation:

        An extra key ``'scopefunc'`` can be set on the ``options`` dict to
        specify a custom scope function.  If it's not provided, Flask's app
        context stack identity is used. This will ensure that sessions are
        created and removed with the request/response cycle, and should be fine
        in most cases.
        """
        self.connection = get_cache_connection(connection)
        self.engine = create_engine(self.connection, echo=echo)
        self.autoflush = autoflush if autoflush is not None else config.get('PYBEL_MANAGER_AUTOFLUSH', False)
        self.autocommit = autocommit if autocommit is not None else config.get('PYBEL_MANAGER_AUTOCOMMIT', False)

        if expire_on_commit is not None:
            self.expire_on_commit = expire_on_commit
        else:
            self.expire_on_commit = config.get('PYBEL_MANAGER_AUTOEXPIRE', True)

        log.info(
            'auto flush: %s, auto commit: %s, expire on commmit: %s',
            self.autoflush,
            self.autoflush,
            self.expire_on_commit
        )

        #: A SQLAlchemy session maker
        self.session_maker = sessionmaker(
            bind=self.engine,
            autoflush=self.autoflush,
            autocommit=self.autocommit,
            expire_on_commit=self.expire_on_commit,
        )

        self.scopefunc = scopefunc

        #: A SQLAlchemy session object
        self.session = scoped_session(self.session_maker, scopefunc=self.scopefunc)

        self.create_all()

    def create_all(self, checkfirst=True):
        """Creates the PyBEL cache's database and tables

        :param bool checkfirst: Check if the database is made before trying to re-make it
        """
        Base.metadata.create_all(bind=self.engine, checkfirst=checkfirst)

    def drop_all(self, checkfirst=True):
        """Drops all data, tables, and databases for the PyBEL cache"""
        Base.metadata.drop_all(bind=self.engine, checkfirst=checkfirst)
