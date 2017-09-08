# -*- coding: utf-8 -*-

"""This module contains the base class for connection managers in SQLAlchemy"""

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from .models import Base
from ..constants import get_cache_connection

__all__ = ['BaseCacheManager']

log = logging.getLogger(__name__)


class BaseCacheManager(object):
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

    def __init__(self, connection=None, echo=False, autoflush=True, autocommit=False, expire_on_commit=False):
        """
        :param str connection: An RFC-1738 database connection string. If ``None``, tries to load from the environment
                                variable ``PYBEL_CONNECTION`` then from the config file ``~/.config/pybel/config.json``
                                whose value for ``PYBEL_CONNECTION`` defaults to 
                                :data:`pybel.constants.DEFAULT_CACHE_LOCATION`
        :param bool echo: Turn on echoing sql
        """
        self.connection = get_cache_connection(connection)
        self.engine = create_engine(self.connection, echo=echo)
        self.autoflush = autoflush
        self.autocommit = autocommit
        self.expire_on_commit = expire_on_commit

        #: A SQLAlchemy session maker
        self.session_maker = sessionmaker(
            bind=self.engine,
            autoflush=self.autoflush,
            autocommit=self.autocommit,
            expire_on_commit=self.expire_on_commit,
        )

        #: A SQLAlchemy session object
        self.session = scoped_session(self.session_maker)

        self.create_all()

    def create_all(self, checkfirst=True):
        """Creates the PyBEL cache's database and tables"""
        Base.metadata.create_all(self.engine, checkfirst=checkfirst)

    def drop_all(self):
        """Drops all data, tables, and databases for the PyBEL cache"""
        Base.metadata.drop_all(self.engine)
