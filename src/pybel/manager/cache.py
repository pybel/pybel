# -*- coding: utf-8 -*-

"""

This module contains the Definitions Cache Manager.

Under the hood, PyBEL caches namespace and annotation files for quick recall on later use. The user doesn't need to
enable this option, but can specify a database location if they choose.

"""

import itertools as itt
import logging

import networkx as nx
from sqlalchemy.orm.exc import NoResultFound

from . import defaults
from . import models
from .base_cache import BaseCacheManager
from .utils import parse_owl, extract_shared_required, extract_shared_optional
from ..parser.language import belns_encodings
from ..utils import download_url

log = logging.getLogger(__name__)

DEFAULT_BELNS_ENCODING = ''.join(sorted(belns_encodings))


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

        self.namespace_term_cache = {}
        self.namespace_edge_cache = {}
        self.namespace_graph_cache = {}

        self.annotation_term_cache = {}
        self.annotation_edge_cache = {}
        self.annotation_graph_cache = {}

    # NAMESPACE MANAGEMENT

    def insert_namespace(self, url):
        """Inserts the namespace file at the given location to the cache

        :param url: the location of the namespace file
        :type url: str
        :return: SQL Alchemy model instance, populated with data from URL
        :rtype: :class:`pybel.manager.models.Namespace`
        """
        log.info('Caching namespace %s', url)

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

    def ensure_namespace(self, url):
        """Caches a namespace file if not already in the cache

        :param url: the location of the namespace file
        :type url: str
        """
        if url in self.namespace_cache:
            log.info('Already cached %s', url)
            return

        try:
            results = self.session.query(models.Namespace).filter(models.Namespace.url == url).one()
            log.info('Loaded namespace from %s (%d)', url, len(results.entries))
        except NoResultFound:
            results = self.insert_namespace(url)

        if results is None:
            raise ValueError('No results for {}'.format(url))
        elif not results.entries:
            raise ValueError('No entries for {}'.format(url))

        self.namespace_cache[url] = {entry.name: set(entry.encoding) for entry in results.entries}

    def get_namespace(self, url):
        """Returns a dict of names and their encodings for the given namespace file

        :param url: the location of the namespace file
        :type url: str
        """
        self.ensure_namespace(url)
        return self.namespace_cache[url]

    def ls_namespaces(self):
        """Returns a list of the locations of the stored namespaces and annotations"""
        return [definition.url for definition in self.session.query(models.Namespace).all()]

    def load_default_namespaces(self):
        """Caches the default set of namespaces"""
        for url in defaults.default_namespaces:
            self.ensure_namespace(url)

    # ANNOTATION MANAGEMENT

    def insert_annotation(self, url):
        """Inserts the namespace file at the given location to the cache

        :param url: the location of the namespace file
        :type url: str
        :return: SQL Alchemy model instance, populated with data from URL
        :rtype: :class:`models.Namespace`
        """
        log.info('Caching annotation %s', url)

        config = download_url(url)

        annotation_insert_values = {
            'type': config['AnnotationDefinition']['TypeString'],
            'url': url
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

    def ensure_annotation(self, url):
        """Caches an annotation file if not already in the cache

        :param url: the location of the annotation file
        :type url: str
        """
        if url in self.annotation_cache:
            log.info('Already cached %s', url)
            return

        try:
            results = self.session.query(models.Annotation).filter(models.Annotation.url == url).one()
            log.info('Loaded annotation from %s (%d)', url, len(results.entries))
        except NoResultFound:
            results = self.insert_annotation(url)

        self.annotation_cache[url] = {entry.name: entry.label for entry in results.entries}

    def get_annotation(self, url):
        """Returns a dict of annotations and their labels for the given annotation file

        :param url: the location of the annotation file
        :type url: str
        """
        self.ensure_annotation(url)
        return self.annotation_cache[url]

    def ls_annotations(self):
        """Returns a list of the locations of the stored namespaces and annotations"""
        return [definition.url for definition in self.session.query(models.Annotation).all()]

    def load_default_annotations(self):
        """Caches the default set of annotations"""
        for url in defaults.default_annotations:
            self.ensure_annotation(url)

    # NAMESPACE OWL MANAGEMENT

    def insert_owl(self, iri, owl_model, owl_entry_model):
        """Caches an ontology at the given IRI

        :param iri: the location of the ontology
        :type iri: str
        """
        log.info('Caching owl %s', iri)

        graph = parse_owl(iri)

        if 0 == len(graph):
            raise ValueError('Empty owl document: {}'.format(iri))

        owl = owl_model(iri=iri)

        entries = {node: owl_entry_model(entry=node) for node in graph.nodes_iter()}

        owl.entries = list(entries.values())

        for u, v in graph.edges_iter():
            entries[u].children.append(entries[v])

        self.session.add(owl)
        self.session.commit()

        return owl

    def insert_namespace_owl(self, iri):
        """Caches an ontology at the given IRI

        :param iri: the location of the ontology
        :type iri: str
        """
        return self.insert_owl(iri, models.OwlNamespace, models.OwlNamespaceEntry)

    def insert_annotation_owl(self, iri):
        """Caches an ontology at the given IRI

        :param iri: the location of the ontology
        :type iri: str
        """
        return self.insert_owl(iri, models.OwlAnnotation, models.OwlAnnotationEntry)

    def ensure_namespace_owl(self, iri):
        """Caches an ontology at the given IRI if it is not already in the cache

        :param iri: the location of the ontology
        :type iri: str
        """
        if iri in self.namespace_term_cache:
            return
        try:
            results = self.session.query(models.OwlNamespace).filter(models.OwlNamespace.iri == iri).one()
        except NoResultFound:
            results = self.insert_namespace_owl(iri)

        self.namespace_term_cache[iri] = set(entry.entry for entry in results.entries)
        self.namespace_edge_cache[iri] = set((sub.entry, sup.entry) for sub in results.entries for sup in sub.children)

        graph = nx.DiGraph()
        graph.add_edges_from(self.namespace_edge_cache[iri])
        self.namespace_graph_cache[iri] = graph

    def ensure_annotation_owl(self, iri):
        if iri in self.annotation_term_cache:
            return
        try:
            results = self.session.query(models.OwlAnnotation).filter(models.OwlAnnotation.iri == iri).one()
        except NoResultFound:
            results = self.insert_annotation_owl(iri)

        self.annotation_term_cache[iri] = set(entry.entry for entry in results.entries)
        self.annotation_edge_cache[iri] = set((sub.entry, sup.entry) for sub in results.entries for sup in sub.children)

        graph = nx.DiGraph()
        graph.add_edges_from(self.annotation_edge_cache[iri])
        self.annotation_graph_cache[iri] = graph

    def get_namespace_owl_terms(self, iri):
        """Gets a set of classes and individuals in the ontology at the given IRI

        :param iri: the location of the ontology
        :type iri: str
        """
        self.ensure_namespace_owl(iri)
        return self.namespace_term_cache[iri]

    def get_annotation_owl_terms(self, iri):
        """Gets a set of classes and individuals in the ontology at the given IRI

        :param iri: the location of the ontology
        :type iri: str
        """
        self.ensure_annotation_owl(iri)
        return self.annotation_term_cache[iri]

    def get_namespace_owl_edges(self, iri):
        """Gets a set of directed edge pairs from the graph representing the ontology at the given IRI

        :param iri: the location of the ontology
        :type iri: str
        """
        self.ensure_namespace_owl(iri)
        return self.namespace_edge_cache[iri]

    def get_annotation_owl_edges(self, iri):
        """Gets a set of classes and individuals in the ontology at the given IRI

        :param iri: the location of the ontology
        :type iri: str
        """
        self.ensure_annotation_owl(iri)
        return self.annotation_edge_cache[iri]

    def get_namespace_owl_graph(self, iri):
        """Gets the graph representing the ontology at the given IRI

        :param iri: the location of the ontology
        :type iri: str
        """
        self.ensure_namespace_owl(iri)
        return self.namespace_graph_cache[iri]

    def get_annotation_owl_graph(self, iri):
        """Gets the graph representing the ontology at the given IRI

        :param iri: the location of the ontology
        :type iri: str
        """
        self.ensure_annotation_owl(iri)
        return self.annotation_graph_cache[iri]

    def ls_namespace_owl(self):
        """Returns a list of the locations of the stored ontologies"""
        return [owl.iri for owl in self.session.query(models.OwlNamespace).all()]

    def load_default_namespace_owl(self):
        """Caches the default set of ontologies"""
        for url in defaults.default_owl:
            self.ensure_namespace_owl(url)

    def ls(self):
        return itt.chain(self.ls_namespaces(), self.ls_annotations(), self.ls_namespace_owl())

    # Manage Equivalences

    def ensure_equivalence_class(self, label):
        try:
            result = self.session.query(models.NamespaceEntryEquivalence).filter_by(label=label).one()
        except NoResultFound:
            result = models.NamespaceEntryEquivalence(label=label)
            self.session.add(result)
            self.session.commit()
        return result

    def insert_equivalences(self, url, namespace_url):
        """Given a url to a .beleq file and its accompanying namespace url, populate the database"""
        self.ensure_namespace(namespace_url)

        log.info('Caching equivalences: %s', url)

        config = download_url(url)
        values = config['Values']

        ns = self.session.query(models.Namespace).filter_by(url=namespace_url).one()

        for entry in ns.entries:
            equivalence_label = values[entry.name]
            equivalence = self.ensure_equivalence_class(equivalence_label)
            entry.equivalence_id = equivalence.id

        ns.has_equivalences = True

        self.session.commit()

    def ensure_equivalences(self, url, namespace_url):
        """Check if the equivalence file is already loaded, and if not, load it"""
        self.ensure_namespace(namespace_url)

        ns = self.session.query(models.Namespace).filter_by(url=namespace_url).one()

        if not ns.has_equivalences:
            self.insert_equivalences(url, namespace_url)

    def get_equivalence_by_entry(self, namespace_url, name):
        """Gets the equivalence class

        :param namespace_url: the URL of the namespace
        :param name: the name of the entry in the namespace
        :return: the equivalence class of the entry in the given namespace
        """
        ns = self.session.query(models.Namespace).filter_by(url=namespace_url).one()
        ns_entry = self.session.query(models.NamespaceEntry).filter(models.NamespaceEntry.namespace_id == ns.id,
                                                                    models.NamespaceEntry.name == name).one()
        return ns_entry.equivalence

    def get_equivalence_members(self, equivalence_class):
        """Gets all members of the given equivalence class

        :param equivalence_class: the label of the equivalence class. example: '0b20937b-5eb4-4c04-8033-63b981decce7'
                                    for Alzheimer's Disease
        :return: a list of members of the class
        """
        eq = self.session.query(models.NamespaceEntryEquivalence).filter_by(label=equivalence_class).one()
        return eq.members
