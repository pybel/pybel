import logging
import os
from datetime import datetime

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound

from . import models
from .defaults import default_owl
from .models import DEFINITION_ANNOTATION, DEFINITION_NAMESPACE
from .utils import parse_owl
from ..constants import PYBEL_DATA
from ..parser import language
from ..utils import download_url

log = logging.getLogger('pybel')

DEFAULT_DEFINITION_CACHE_NAME = 'definitions.db'
DEFAULT_CACHE_LOCATION = os.path.join(PYBEL_DATA, DEFAULT_DEFINITION_CACHE_NAME)

DEFAULT_BELNS_ENCODING = ''.join(sorted(language.value_map))

CREATION_DATE_FMT = '%Y-%m-%dT%H:%M:%S'
PUBLISHED_DATE_FMT = '%Y-%m-%d'

# TODO make Enum
definition_headers = {
    DEFINITION_NAMESPACE: 'Namespace',
    DEFINITION_ANNOTATION: 'AnnotationDefinition'
}

VALID_NAMESPACE_DOMAINSTRING = {"BiologicalProcess", "Chemical", "Gene and Gene Products", "Other"}


def parse_datetime(s):
    """Tries to parse a datetime object from a standard datetime format or date format"""
    try:
        dt = datetime.strptime(s, CREATION_DATE_FMT)
        return dt
    except:
        try:
            dt = datetime.strptime(s, PUBLISHED_DATE_FMT)
            return dt
        except:
            raise ValueError('Incorrect datetime format for {}'.format(s))


class BaseCacheManager:
    def __init__(self, connection=None, echo=False, create_all=False):
        connection = connection if connection is not None else 'sqlite:///' + DEFAULT_CACHE_LOCATION
        self.engine = create_engine(connection, echo=echo)
        self.session = scoped_session(sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False))

        if create_all:
            self.create_database()

    def create_database(self, checkfirst=True):
        models.Base.metadata.create_all(self.engine, checkfirst=checkfirst)

    def drop_database(self):
        models.Base.metadata.drop_all(self.engine)


class CacheManager(BaseCacheManager):
    def __init__(self, connection=None, create_all=False, echo=False):
        """The definition cache manager takes care of storing BEL namespace and annotation files for later use.
        It uses SQLite by default for speed and lightness, but any database can be used wiht its SQLAlchemy interface.

        :param: connection: custom database connection string
        :type connection: str
        :param create_all: create database?
        :type create_all: bool
        :param: echo: Whether or not echo the running sql code.
        :type echo: bool
        """

        BaseCacheManager.__init__(self, connection=connection, echo=echo, create_all=create_all)

        self.namespace_cache = {}
        self.annotation_cache = {}

        # TODO harmonize term cache with namespace cache
        self.term_cache = {}
        self.edge_cache = {}
        self.graph_cache = {}

        self.create_database()

    def insert_definition(self, url, definition_type):
        """Inserts the definition file at the given location to the cache

        :param url: the location of the definition file
        :type url: str
        :param definition_type: either DEFINITION_NAMESPACE or DEFINITION_ANNOTATION
        :return: SQL Alchemy model instance, populated with data from URL
        """
        config = download_url(url)

        header = definition_headers[definition_type]

        definition_insert_values = {
            'url': url,
            'definitionType': definition_type,
            'author': config['Author']['NameString'],
            'keyword': config[header]['Keyword'],
            'createdDateTime': parse_datetime(config[header]['CreatedDateTime']),
            'copyright': config['Author']['CopyrightString'],
            'version': config[header]['VersionString'],
            'contact': config['Author']['ContactInfoString']
        }

        if 'PublishedDate' in config['Citation']:
            definition_insert_values['pubDate'] = parse_datetime(config['Citation']['PublishedDate'])

        definition = models.Definition(**definition_insert_values)

        if definition_type == DEFINITION_ANNOTATION:
            values = {c: e for c, e in config['Values'].items() if c}
        else:
            values = {c: e if e else DEFAULT_BELNS_ENCODING for c, e in config['Values'].items() if c}

        definition.entries = [models.Entry(name=c, encoding=e) for c, e in values.items() if c]

        self.session.add(definition)
        self.session.commit()

        return definition

    def ensure_namespace(self, url):
        """Caches a namespace file if not already in the cache

        :param url: the location of the namespace file
        :type url: str
        """
        if url in self.namespace_cache:
            return

        try:
            results = self.session.query(models.Definition).filter(models.Definition.url == url).one()
        except NoResultFound:

            # TODO split namespace and annotation handling
            # if config[header]['DomainString'] not in VALID_NAMESPACE_DOMAINSTRING:
            #    raise ValueError("Invalid DomainString {}".format(config[header]['DomainString']))

            results = self.insert_definition(url, DEFINITION_NAMESPACE)

        if results is None:
            raise ValueError('No results for {}'.format(url))
        elif not results.entries:
            raise ValueError('No entries for {}'.format(url))

        self.namespace_cache[url] = {entry.name: set(entry.encoding) for entry in results.entries}

    def ensure_annotation(self, url):
        """Caches an annotation file if not already in the cache

        :param url: the location of the annotation file
        :type url: str
        """
        if url in self.annotation_cache:
            return

        try:
            results = self.session.query(models.Definition).filter(models.Definition.url == url).one()
        except NoResultFound:
            results = self.insert_definition(url, DEFINITION_ANNOTATION)

        self.annotation_cache[url] = {entry.name: entry.encoding for entry in results.entries}

    def get_namespace(self, url):
        """Returns a dict of names and their encodings for the given namespace file

        :param url: the location of the namespace file
        :type url: str
        """
        self.ensure_namespace(url)
        return self.namespace_cache[url]

    def get_annotation(self, url):
        """Returns a dict of annotations and their labels for the given annotation file

        :param url: the location of the annotation file
        :type url: str
        """
        self.ensure_annotation(url)
        return self.annotation_cache[url]

    def ls(self):
        """Returns a list of the locations of the stored namespaces and annotations"""
        return [definition.url for definition in self.session.query(models.Definition).all()]

    def ls_definition(self, definition_url):
        """Returns a list of the entries for the given definition file

        :param url: the location of the annotation file
        :type url: str
        """
        definition = self.session.query(models.Definition).filter_by(url=definition_url).first()
        return [context.context for context in definition.entries]

    def ensure_owl(self, iri):
        """Caches an ontology at the given IRI if it is not already in the cache

        :param iri: the location of the ontology
        :type iri: str
        """

        if iri in self.term_cache:
            return
        try:
            results = self.session.query(models.Owl).filter(models.Owl.iri == iri).one()
        except NoResultFound:
            results = self.insert_by_iri(iri)

        self.term_cache[iri] = set(entry.entry for entry in results.entries)
        self.edge_cache[iri] = set((sub.entry, sup.entry) for sub in results.entries for sup in sub.children)

        graph = nx.DiGraph()
        graph.add_edges_from(self.edge_cache[iri])
        self.graph_cache[iri] = graph

    def load_default_owl(self):
        """Caches the default set of ontologies"""
        for url in default_owl:
            self.insert_by_iri(url)

    def ls_owl(self):
        """Returns a list of the locations of the stored ontologies"""

        return [owl.iri for owl in self.session.query(models.Owl).all()]

    def insert_by_iri(self, iri):
        """Caches an ontology at the given IRI

        :param iri: the location of the ontology
        :type iri: str
        """
        return self.insert_by_graph(iri, parse_owl(iri))

    def insert_by_graph(self, iri, graph):
        """"""
        if 0 < self.session.query(models.Owl).filter(models.Owl.iri == iri).count():
            log.debug('%s already cached', iri)
            return

        owl = models.Owl(iri=iri)

        entries = {node: models.OwlEntry(entry=node) for node in graph.nodes_iter()}

        owl.entries = list(entries.values())

        for u, v in graph.edges_iter():
            entries[u].children.append(entries[v])

        self.session.add(owl)
        self.session.commit()

        return owl

    def get_owl_terms(self, iri):
        """Gets a set of classes and individuals in the ontology at the given IRI

        :param iri: the location of the ontology
        :type iri: str
        """
        self.ensure_owl(iri)
        return self.term_cache[iri]

    def get_edges(self, iri):
        """Gets a set of directed edge pairs from the graph representing the ontology at the given IRI

        :param iri: the location of the ontology
        :type iri: str
        """
        self.ensure_owl(iri)
        return self.edge_cache[iri]

    def get_graph(self, iri):
        """Gets the graph representing the ontology at the given IRI

        :param iri: the location of the ontology
        :type iri: str
        """
        self.ensure_owl(iri)
        return self.graph_cache[iri]
