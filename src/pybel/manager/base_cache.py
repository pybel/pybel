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

    def __init__(self, connection=None, echo=False):
        """
        :param str connection: An RFC-1738 database connection string. If ``None``, tries to load from the environment
                                variable ``PYBEL_CONNECTION`` then from the config file ``~/.config/pybel/config.json``
                                whose value for ``PYBEL_CONNECTION`` defaults to 
                                :data:`pybel.constants.DEFAULT_CACHE_LOCATION`
        :param bool echo: Turn on echoing sql
        """
        if connection is not None:
            self.connection = connection
            log.info('connected to user-defined cache: %s', self.connection)
        else:
            self.connection = get_cache_connection()

        self.engine = create_engine(self.connection, echo=echo)

        #: A SQLAlchemy session maker
        self.sessionmaker = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)

        #: A SQLAlchemy session object
        self.session = scoped_session(self.sessionmaker)

        self.create_all()

    def create_all(self, checkfirst=True):
        """Creates the PyBEL cache's database and tables"""
        Base.metadata.create_all(self.engine, checkfirst=checkfirst)

    def drop_database(self):
        """Drops all data, tables, and databases for the PyBEL cache"""
        Base.metadata.drop_all(self.engine)
