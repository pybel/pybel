import os

import sqlalchemy
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

from .defaults import default_owl
from ..constants import PYBEL_DATA
from ..parser.utils import parse_owl

Base = declarative_base()
OWL_CACHE_LOCATION = os.path.join(PYBEL_DATA, 'owl_cache.db')


class Owl(Base):
    __tablename__ = 'owl'

    id = Column(Integer, primary_key=True)
    iri = Column(String(255))

    entries = relationship("OwlEntry", order_by="owl_entry.id", backref="owl")


class OwlEntry(Base):
    __tablename__ = 'owl_entry'

    id = Column(Integer, primary_key=True)
    owl_id = Column(Integer, ForeignKey('owl.id'), index=True)
    entry = Column(String(255))


class OwlRelationship(Base):
    __tablename__ = 'owl_relationship'

    child = Column(Integer, ForeignKey('owl_entry.id'), index=True, primary_key=True)
    parent = Column(Integer, ForeignKey('owl_entry.id'), index=True, primary_key=True)


class OwlCacheManager:
    def __init__(self, conn=None):
        self.connection_url = conn if conn is not None else 'sqlite://' + OWL_CACHE_LOCATION
        self.engine = sqlalchemy.create_engine(self.connection_url)
        self.session = sessionmaker(bind=self.engine)

        self.cache = {}

    def create_database(self):
        Base.metadata.create_all(self.engine)

    def ensure_cache(self):
        for url in default_owl:
            graph = parse_owl(url)
            self.insert(graph.iri, graph)

    def insert(self, graph, iri=None):
        iri = iri if iri is not None else graph.iri

        owl = Owl(iri=iri)
        owl.entries = [OwlEntry(entry=node) for node in graph.nodes_iter()]

        self.session.add(owl)

    def get(self, iri):
        if iri not in self.cache:
            self.cache[iri] = set(self.session.query(Owl).join(OwlEntry).filter(Owl.iri == iri).all())
        return self.cache[iri]
