import sqlalchemy
from sqlalchemy.orm import sessionmaker

from .database_models import Base, Owl, OwlEntry
from .defaults import default_owl
from .namespace_cache import DEFAULT_CACHE_LOCATION
from ..parser.utils import parse_owl


class OwlCacheManager:
    def __init__(self, conn=None):
        self.connection_url = conn if conn is not None else 'sqlite:///' + DEFAULT_CACHE_LOCATION
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