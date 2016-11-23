import networkx as nx
import sqlalchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Sequence, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker, scoped_session

from sqlalchemy.orm.exc import NoResultFound

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
        return "Owl(iri='{}', #entries='{}')>".format(self.iri, list(self.entries))


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
        return 'OwlEntry({})'.format(self.entry)


class OwlCacheManager:
    def __init__(self, conn=None):
        self.connection_url = conn if conn is not None else 'sqlite:///' + DEFAULT_CACHE_LOCATION
        self.engine = sqlalchemy.create_engine(self.connection_url)
        self.session = scoped_session(sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False))

        self.term_cache = {}
        self.edge_cache = {}
        self.graph_cache = {}

    def create_database(self):
        Base.metadata.create_all(self.engine)

    def drop_database(self):
        Base.metadata.drop_all(self.engine)

    def load_default_owl(self):
        for url in default_owl:
            self.insert_by_iri(url)

    def insert_by_iri(self, iri):
        self.insert(graph=parse_owl(iri))

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

    def ensure(self, iri):
        if iri in self.term_cache:
            return
        try:
            results = self.session.query(Owl).filter(Owl.iri == iri).one()
        except NoResultFound:
            raise ValueError('IRI {} missing from cache'.format(iri))

        self.term_cache[iri] = set(entry.entry for entry in results.entries)
        self.edge_cache[iri] = set((sub.entry, sup.entry) for sub in results.entries for sup in sub.children)

        graph = nx.DiGraph()
        graph.add_edges_from(self.edge_cache[iri])
        self.graph_cache[iri] = graph

    def get_terms(self, iri):
        self.ensure(iri)
        return self.term_cache[iri]

    def get_edges(self, iri):
        self.ensure(iri)
        return self.edge_cache[iri]

    def get_graph(self, iri):
        self.ensure(iri)
        return self.graph_cache[iri]
