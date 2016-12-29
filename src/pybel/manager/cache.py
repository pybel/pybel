import itertools as itt
import logging
import os
from datetime import datetime

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound

from . import defaults
from . import models
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
    """Creates a connection to database and a persistient session using SQLAlchemy"""

    def __init__(self, connection=None, echo=False):
        connection = connection if connection is not None else 'sqlite:///' + DEFAULT_CACHE_LOCATION
        self.engine = create_engine(connection, echo=echo)
        self.session = scoped_session(sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False))
        self.create_database()

    def create_database(self, checkfirst=True):
        models.Base.metadata.create_all(self.engine, checkfirst=checkfirst)

    def drop_database(self):
        models.Base.metadata.drop_all(self.engine)


def extract_shared_required(config, definition_header='Namespace'):
    """

    :param config:
    :param definition_header: 'Namespace' or 'AnnotationDefinition'
    :return:
    """
    return {
        'keyword': config[definition_header]['Keyword'],
        'created': parse_datetime(config[definition_header]['CreatedDateTime']),
        'author': config['Author']['NameString'],
        'citation': config['Citation']['NameString']
    }


def extract_shared_optional(config, definition_header='Namespace'):
    s = {
        'description': (definition_header, 'DescriptionString'),
        'version': (definition_header, 'VersionString'),
        'license': ('Author', 'CopyrightString'),
        'contact': ('Author', 'ContactInfoString'),
        'citation_description': ('Citation', 'DescriptionString'),
        'citation_version': ('Citation', 'PublishedVersionString'),
        'citation_url': ('Citation', 'ReferenceURL')
    }

    x = {}

    for database_column, (section, key) in s.items():
        if section in config and key in config[section]:
            x[database_column] = config[section][key]

    if 'PublishedDate' in config['Citation']:
        x['citation_published'] = parse_datetime(config['Citation']['PublishedDate'])

    return x


class CacheManager(BaseCacheManager):
    def __init__(self, connection=None, echo=False):
        """The definition cache manager takes care of storing BEL namespace and annotation files for later use.
        It uses SQLite by default for speed and lightness, but any database can be used wiht its SQLAlchemy interface.

        :param connection: custom database connection string
        :type connection: str
        :param echo: Whether or not echo the running sql code.
        :type echo: bool
        """

        BaseCacheManager.__init__(self, connection=connection, echo=echo)

        self.namespace_cache = {}
        self.annotation_cache = {}

        self.term_cache = {}
        self.edge_cache = {}
        self.graph_cache = {}

        self.create_database()

    def insert_namespace(self, url):
        """Inserts the namespace file at the given location to the cache

        :param url: the location of the namespace file
        :type url: str
        :return: SQL Alchemy model instance, populated with data from URL
        :rtype: :class:`models.Namespace`
        """
        config = download_url(url)

        namespace_insert_values = {
            'name': config['Namespace']['NameString'],
            'url': url,
            'domain': config['Namespace']['DomainString']
        }

        namespace_insert_values.update(extract_shared_required(config, 'Namespace'))
        namespace_insert_values.update(extract_shared_optional(config, 'Namespace'))

        namespace_mapping = {
            'species': ('Namespace', 'SpeciesString'),
            'query_url': ('Namespace', 'QueryValueURL')
        }

        for database_column, (section, key) in namespace_mapping.items():
            if section in config and key in config[section]:
                namespace_insert_values[database_column] = config[section][key]

        namespace = models.Namespace(**namespace_insert_values)

        values = {c: e if e else DEFAULT_BELNS_ENCODING for c, e in config['Values'].items() if c}

        namespace.entries = [models.NamespaceEntry(name=c, encoding=e) for c, e in values.items()]

        self.session.add(namespace)
        self.session.commit()

        return namespace

    def insert_annotation(self, url):
        config = download_url(url)
        annotation_insert_values = {
            'type': config['AnnotationDefinition']['TypeString']
        }
        annotation_insert_values.update(extract_shared_required(config, 'AnnotationDefinition'))
        annotation_insert_values.update(extract_shared_optional(config, 'AnnotationDefinition'))

        annotation_mapping = {
            'name': ('Citation', 'NameString')
        }

        for database_column, (section, key) in annotation_mapping.items():
            if section in config and key in config[section]:
                annotation_insert_values[database_column] = config[section][key]

        annotation = models.Annotation(**annotation_insert_values)
        annotation.entries = [models.AnnotationEntry(name=c, label=l) for c, l in config['Values'].items() if c]

        self.session.add(annotation)
        self.session.commit()

        return annotation

    def ensure_namespace(self, url):
        """Caches a namespace file if not already in the cache

        :param url: the location of the namespace file
        :type url: str
        """
        if url in self.namespace_cache:
            return

        try:
            results = self.session.query(models.Namespace).filter(models.Namespace.url == url).one()
        except NoResultFound:
            results = self.insert_namespace(url)

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
            results = self.session.query(models.Annotation).filter(models.Annotation.url == url).one()
        except NoResultFound:
            results = self.insert_annotation(url)

        self.annotation_cache[url] = {entry.name: entry.label for entry in results.entries}

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
        return itt.chain(self.ls_namespaces(), self.ls_annotations())

    def ls_namespaces(self):
        """Returns a list of the locations of the stored namespaces and annotations"""
        return [definition.url for definition in self.session.query(models.Namespace).all()]

    def ls_annotations(self):
        """Returns a list of the locations of the stored namespaces and annotations"""
        return [definition.url for definition in self.session.query(models.Annotation).all()]

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

    def load_default_namespaces(self):
        """Caches the default set of namespaces"""
        for url in defaults.default_namespaces:
            self.ensure_namespace(url)

    def load_default_annotations(self):
        """Caches the default set of annotations"""
        for url in defaults.default_annotations:
            self.ensure_annotation(url)

    def load_default_owl(self):
        """Caches the default set of ontologies"""
        for url in defaults.default_owl:
            self.ensure_owl(url)

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
        """Caches an ontology represented by a graph

        :param iri: the location of the ontology
        :type iri: str
        :param graph: the graph representation of the ontology's subclass and instanceof relationships
        :type graph: :class:`networkx.DiGraph`
        """
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
