import sqlalchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Sequence, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker, scoped_session

from .database_models import Base
from .defaults import default_owl
from .namespace_cache import DEFAULT_CACHE_LOCATION
from ..parser.utils import parse_owl

owl_relationship = Table(
    'owl_relationship', Base.metadata,
    Column('left_id', Integer, ForeignKey('OwlEntry.id'), primary_key=True),
    Column('right_id', Integer, ForeignKey('OwlEntry.id'), primary_key=True)
)

class Owl(Base):
    __tablename__ = 'Owl'

    id = Column(Integer, Sequence('owl_id_seq'), primary_key=True)
    iri = Column(Text, unique=True)
    entries = relationship("OwlEntry", order_by="OwlEntry.id", backref="owl")

    def __repr__(self):
        return "<Owl(iri='{}', #entries='{}')>".format(self.iri, list(self.entries))


class OwlEntry(Base):
    __tablename__ = 'OwlEntry'

    id = Column(Integer, Sequence('OwlEntry_id_seq'), primary_key=True)
    owl_id = Column(Integer, ForeignKey('Owl.id'), index=True)
    entry = Column(String(255))

    children = relationship('OwlEntry',
                            secondary=owl_relationship,
                            primaryjoin=id == owl_relationship.c.left_id,
                            secondaryjoin=id == owl_relationship.c.right_id)

    def __repr__(self):
        return '<OwlEntry({})>'.format(self.entry)


class OwlCacheManager:
    def __init__(self, conn=None):
        self.connection_url = conn if conn is not None else 'sqlite:///' + DEFAULT_CACHE_LOCATION
        self.engine = sqlalchemy.create_engine(self.connection_url)
        self.session = scoped_session(sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False))

        self.term_cache = {}
        self.edge_cache = {}

    def create_database(self):
        Base.metadata.create_all(self.engine)

    def drop_database(self):
        Base.metadata.drop_all(self.engine)

    def ensure_cache(self):
        for url in default_owl:
            graph = parse_owl(url)
            self.insert(graph.iri, graph)

    def insert(self, graph, iri=None):
        iri = iri if iri is not None else graph.iri

        if 0 < self.session.query(Owl).filter(Owl.iri == iri).count():
            return

        owl = Owl(iri=iri)

        entries = {node: OwlEntry(entry=node) for node in graph.nodes_iter()}

        owl.entries = list(entries.values())

        for u, v in graph.edges_iter():
            entries[u].children.append(entries[v])

        self.session.add(owl)
        self.session.commit()

    def get_terms(self, iri):
        if iri not in self.term_cache:
            results = self.session.query(Owl).filter(Owl.iri == iri).one()
            self.term_cache[iri] = set(entry.entry for entry in results.entries)
        return self.term_cache[iri]

    def get_edges_iter(self, iri):
        result = self.session.query(Owl).filter(Owl.iri == iri).one()
        for entry in result.entries:
            for child in entry.children:
                yield (entry.entry, child.entry)
