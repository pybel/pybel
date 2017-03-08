import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from .models import Base
from ..constants import PYBEL_CONNECTION_ENV, DEFAULT_CACHE_LOCATION


class BaseCacheManager:
    """Creates a connection to database and a persistent session using SQLAlchemy"""

    def __init__(self, connection=None, echo=False):
        """

        :param connection: custom database connection string can be given explicitly, loaded from a 'PYBEL_CONNECTION'
                           in the environment, or will default to ~/.pybel/data/pybel_cache.db
        :type connection: str or None
        :param echo: Whether or not echo the running sql code.
        :type echo: bool
        """

        if connection is not None:
            self.connection = connection
        elif connection is None and PYBEL_CONNECTION_ENV in os.environ:
            self.connection = os.environ[PYBEL_CONNECTION_ENV]
        else:
            self.connection = 'sqlite:///' + DEFAULT_CACHE_LOCATION

        self.engine = create_engine(self.connection, echo=echo)
        self.sessionmaker = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        self.session = scoped_session(self.sessionmaker)()
        self.create_database()

    def create_database(self, checkfirst=True):
        Base.metadata.create_all(self.engine, checkfirst=checkfirst)

    def drop_database(self):
        Base.metadata.drop_all(self.engine)
