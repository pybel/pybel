# -*- coding: utf-8 -*-

"""This module contains the base class for connection managers in SQLAlchemy"""

import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from .models import Base
from ..constants import PYBEL_CONNECTION_ENV, DEFAULT_CACHE_LOCATION

__all__ = ['BaseCacheManager']

log = logging.getLogger(__name__)


class BaseCacheManager:
    """Creates a connection to database and a persistent session using SQLAlchemy"""

    def __init__(self, connection=None, echo=False):
        """
        :param connection: A custom database connection string can be given explicitly, loaded from a 
                            :data:`pybel.constants.PYBEL_CONNECTION` in the environment, or will default to 
                            :data`pybel.constants.DEFAULT_CACHE_LOCATION`
        :type connection: str or None
        :param echo: Turn on echoing sql
        :type echo: bool
        """
        if connection is not None:
            self.connection = connection
            log.info('Connected to user-defined cache: %s', self.connection)
        elif PYBEL_CONNECTION_ENV in os.environ:
            self.connection = os.environ[PYBEL_CONNECTION_ENV]
            log.info('Connected to environment-defined cache: %s', self.connection)
        else:
            self.connection = 'sqlite:///' + DEFAULT_CACHE_LOCATION
            log.info('Connected to default cache: %s', self.connection)

        self.engine = create_engine(self.connection, echo=echo)
        self.sessionmaker = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        self.session = scoped_session(self.sessionmaker)()
        self.create_database()

    def create_database(self, checkfirst=True):
        """Creates the PyBEL cache's database and tables"""
        Base.metadata.create_all(self.engine, checkfirst=checkfirst)

    def drop_database(self):
        """Drops all data, tables, and databases for the PyBEL cache"""
        Base.metadata.drop_all(self.engine)
