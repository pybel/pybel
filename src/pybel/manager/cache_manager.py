# -*- coding: utf-8 -*-

"""
Definition Cache Manager
------------------------
Under the hood, PyBEL caches namespace and annotation files for quick recall on later use. The user doesn't need to
enable this option, but can specify a database location if they choose.
"""

from __future__ import unicode_literals

import logging
import time
from collections import defaultdict
from copy import deepcopy
from itertools import chain, groupby

import six
from six import string_types
from sqlalchemy import and_, exists, func

from .base_manager import BaseManager
from .exc import EdgeAddError
from .lookup_manager import LookupManager
from .models import (
    Annotation, AnnotationEntry, Author, Citation, Edge, Evidence, Modification, Namespace,
    NamespaceEntry, NamespaceEntryEquivalence, Network, Node, Property,
)
from .query_manager import QueryManager
from .utils import extract_shared_optional, extract_shared_required, parse_owl, update_insert_values
from ..canonicalize import node_to_bel
from ..constants import *
from ..language import (
    BEL_DEFAULT_NAMESPACE_URL, BEL_DEFAULT_NAMESPACE_VERSION, activity_mapping, gmod_mappings,
    pmod_mappings,
)
from ..resources.definitions import get_bel_resource
from ..struct import BELGraph, union
from ..utils import hash_citation, hash_dump, hash_edge, hash_evidence, hash_node, parse_datetime

__all__ = [
    'Manager',
    'NetworkManager',
]

log = logging.getLogger(__name__)

DEFAULT_BELNS_ENCODING = ''.join(sorted(belns_encodings))

_namespace_mapping = {
    'species': ('Namespace', 'SpeciesString'),
    'query_url': ('Namespace', 'QueryValueURL')
}


def _get_namespace_insert_values(bel_resource):
    namespace_insert_values = {
        'name': bel_resource['Namespace']['NameString'],
        'domain': bel_resource['Namespace']['DomainString']
    }

    namespace_insert_values.update(extract_shared_required(bel_resource, 'Namespace'))
    namespace_insert_values.update(extract_shared_optional(bel_resource, 'Namespace'))

    update_insert_values(bel_resource, _namespace_mapping, namespace_insert_values)

    return namespace_insert_values


_annotation_mapping = {
    'name': ('Citation', 'NameString')
}


def _get_annotation_insert_values(bel_resource):
    annotation_insert_values = {
        'type': bel_resource['AnnotationDefinition']['TypeString'],
    }
    annotation_insert_values.update(extract_shared_required(bel_resource, 'AnnotationDefinition'))
    annotation_insert_values.update(extract_shared_optional(bel_resource, 'AnnotationDefinition'))

    update_insert_values(bel_resource, _annotation_mapping, annotation_insert_values)

    return annotation_insert_values


def not_resource_cachable(bel_resource):
    """Checks if the BEL resource is cachable. Takes in a dictionary from :func:`get_bel_resource`"""
    return bel_resource['Processing'].get('CacheableFlag') not in {'yes', 'Yes', 'True', 'true'}


def _clean_bel_namespace_values(bel_resource):
    bel_resource['Values'] = {
        name: (encoding if encoding else DEFAULT_BELNS_ENCODING)
        for name, encoding in bel_resource['Values'].items()
        if name
    }


class NamespaceManager(BaseManager):
    """Manages BEL namespaces"""

    def __init__(self, use_namespace_cache=False, *args, **kwargs):
        """
        :param use_namespace_cache: Should namespaces be cached in-memory?
        """
        super(NamespaceManager, self).__init__(*args, **kwargs)

        self.use_namespace_cache = (
            use_namespace_cache
            if use_namespace_cache is not None
            else config.get('PYBEL_IN_MEMORY_NAMESPACE_CACHE', False)
        )
        self._namespace_model = {}
        self._namespace_object_cache = defaultdict(dict)

        log.debug('namespace manager caching: %s', self.use_namespace_cache)

    @property
    def namespace_model(self):
        """A dictionary from {namespace URL: Namespace}

        :rtype: dict[str,Namespace]
        """
        return self._namespace_model

    @property
    def namespace_object_cache(self):
        """A dictionary from {namespace URL: {entry name: NamespaceEntry}}

        :rtype: dict[str,dict[str,NamespaceEntry]]
        """
        return self._namespace_object_cache

    def list_namespaces(self):
        """Returns a list of all namespaces

        :rtype: list[Namespace]
        """
        return self.session.query(Namespace).all()

    def count_namespaces(self):
        """Count the number of namespaces in the database

        :rtype: int
        """
        return self.session.query(Namespace).count()

    def count_namespace_entries(self):
        """Count the number of namespace entries in the database

        :rtype: int
        """
        return self.session.query(NamespaceEntry).count()

    def drop_namespaces(self):
        """Drops all namespaces"""
        self.namespace_object_cache.clear()
        self.namespace_model.clear()

        for namespace in self.session.query(NamespaceEntry).all():
            namespace.children[:] = []
            self.session.commit()

        self.session.query(NamespaceEntry).delete()
        self.session.query(Namespace).delete()
        self.session.commit()

    def drop_namespace_by_url(self, url):
        """Drops the namespace at the given URL. Won't work if the edge store is in use.

        :param str url: The URL of the namespace to drop
        """
        self.session.query(Namespace).filter(Namespace.url == url).delete()
        self.session.commit()

    def get_namespace_by_url(self, url):
        """Looks up a namespace by url. Fails if not inserted already into database.

        :param str url: The URL of the namespace
        :rtype: Namespace
        """
        return self.session.query(Namespace).filter(Namespace.url == url).one_or_none()

    def get_namespace_by_keyword_version(self, keyword, version):
        """Gets a namespace with a given keyword and version

        :param str keyword: The keyword to search
        :param str version: The version to search
        :rtype: Optional[Namespace]
        """
        filt = and_(Namespace.keyword == keyword, Namespace.version == version)
        return self.session.query(Namespace).filter(filt).one_or_none()

    def ensure_default_namespace(self):
        """Creates or gets the BEL default namespace

        :rtype: Namespace
        """
        namespace = self.get_namespace_by_keyword_version(BEL_DEFAULT_NAMESPACE, BEL_DEFAULT_NAMESPACE_VERSION)

        if namespace is None:
            namespace = Namespace(
                name='BEL Default Namespace',
                contact='charles.hoyt@scai.fraunhofer.de',
                keyword=BEL_DEFAULT_NAMESPACE,
                version=BEL_DEFAULT_NAMESPACE_VERSION,
                url=BEL_DEFAULT_NAMESPACE_URL,
            )

            for name in set(chain(pmod_mappings, gmod_mappings, activity_mapping)):
                entry = NamespaceEntry(name=name, namespace=namespace)
                self.session.add(entry)

            self.session.add(namespace)
            self.session.commit()

        return namespace

    def get_or_create_namespace(self, url):
        """Inserts the namespace file at the given location to the cache. If not cachable, returns the dict of
        the values of this namespace.

        :param str url: the location of the namespace file
        :return: SQL Alchemy model instance, populated with data from URL
        :rtype: Namespace or dict
        :raises: pybel.resources.exc.ResourceError
        """
        result = self.get_namespace_by_url(url)

        if result is not None:
            return result

        t = time.time()

        bel_resource = get_bel_resource(url)

        _clean_bel_namespace_values(bel_resource)

        values = bel_resource['Values']

        if not_resource_cachable(bel_resource):
            log.info('not caching namespace: %s (%d terms in %.2f seconds)', url, len(values), time.time() - t)
            return values

        namespace_insert_values = _get_namespace_insert_values(bel_resource)

        namespace = Namespace(
            url=url,
            **namespace_insert_values
        )
        namespace.entries = [
            NamespaceEntry(name=name, encoding=encoding)
            for name, encoding in values.items()
        ]

        log.info('inserted namespace: %s (%d terms in %.2f seconds)', url, len(values), time.time() - t)

        self.session.add(namespace)
        self.session.commit()

        return namespace

    def _cache_namespace(self, namespace):
        """Caches a namespace's model

        :param Namespace namespace:
        """
        self.namespace_model[namespace.url] = namespace

    def _cache_namespace_entries(self, namespace):
        """Caches a namespace's entries' models

        :param Namespace namespace:
        """
        for entry in namespace.entries:
            self.namespace_object_cache[namespace.url][entry.name] = entry

    def ensure_namespace(self, url):
        """Gets or creates a namespace by its URL. Stores in the database and cache if it's cachable, otherwise
        returns a dictionary of {names: encodings}

        :param str url: the location of the namespace file
        :rtype: Namespace or dict[str,str]
        :raises: pybel.resources.exc.ResourceError
        """
        if self.use_namespace_cache and url in self.namespace_model:
            log.debug('already in memory: %s', url)
            return self.namespace_model[url]

        namespace = self.get_or_create_namespace(url)

        if isinstance(namespace, dict):
            log.debug('loaded uncached namespace: %s (%d)', url, len(namespace))
            return namespace

        log.debug('loaded namespace: %s', url)

        if self.use_namespace_cache:
            self._cache_namespace(namespace)
            self._cache_namespace_entries(namespace)

        return namespace

    def get_namespace_by_keyword_pattern(self, keyword, pattern):
        """Gets a namespace with a given keyword and pattern

        :param str keyword: The keyword to search
        :param str pattern: The pattern to search
        :rtype: Optional[Namespace]
        """
        filt = and_(Namespace.keyword == keyword, Namespace.pattern == pattern)
        return self.session.query(Namespace).filter(filt).one_or_none()

    def ensure_regex_namespace(self, keyword, pattern):
        """Gets or creates a regular expression namespace

        :param str keyword: The keyword of a regular expression namespace
        :param str pattern: The pattern for a regular expression namespace
        :rtype: Namespace
        """
        if pattern is None:
            raise ValueError('cannot have null pattern')

        namespace = self.get_namespace_by_keyword_pattern(keyword, pattern)

        if namespace is None:
            log.info('creating regex namespace: %s:%s', keyword, pattern)
            namespace = Namespace(
                keyword=keyword,
                pattern=pattern
            )
            self.session.add(namespace)
            self.session.commit()

        return namespace

    def get_namespace_entry(self, url, name):
        """Gets a given NamespaceEntry object.

        :param str url: The url of the namespace source
        :param str name: The value of the namespace from the given url's document
        :rtype: Optional[NamespaceEntry]
        """
        if self.namespace_object_cache and url in self.namespace_object_cache:
            return self.namespace_object_cache[url][name]

        entry_filter = and_(Namespace.url == url, NamespaceEntry.name == name)

        result = self.session.query(NamespaceEntry).join(Namespace).filter(entry_filter).all()

        if 0 == len(result):
            return

        if 1 < len(result):
            log.warning('result for get_namespace_entry is too long. Returning first of %s', [str(r) for r in result])

        return result[0]

    def get_or_create_regex_namespace_entry(self, namespace, pattern, name):
        """Gets a namespace entry from a regular expression. Need to commit after!

        :param str namespace: The name of the namespace
        :param str pattern: The regular expression pattern for the namespace
        :param str name: The entry to get
        :return:
        """
        namespace = self.ensure_regex_namespace(namespace, pattern)

        n_filter = and_(Namespace.pattern == pattern, NamespaceEntry.name == name)

        name_model = self.session.query(NamespaceEntry).join(Namespace).filter(n_filter).one_or_none()

        if name_model is None:
            name_model = NamespaceEntry(
                namespace=namespace,
                name=name
            )
            self.session.add(name_model)

        return name_model


class OwlNamespaceManager(NamespaceManager):
    """Manages OWL namespaces"""

    def get_or_create_owl_namespace(self, url, keyword=None, encoding=None):
        """Caches an ontology at the given IRI

        :param str url: The location of the ontology
        :param str keyword: The keyword for the namespace
        :param str encoding: The encoding for the entries in the namespace
        :rtype: Namespace
        """
        namespace = self.get_namespace_by_url(url)

        if namespace is not None:
            return namespace

        log.debug('inserting owl %s', url)

        namespace = Namespace(url=url, keyword=keyword)

        graph = parse_owl(url)

        encoding = BELNS_ENCODING_STR if encoding is None else encoding

        name_to_entry = {
            node: NamespaceEntry(name=node, encoding=encoding)
            for node in graph
        }
        namespace.entries = list(name_to_entry.values())

        for parent, child in graph.edges_iter():
            parent_entry = name_to_entry[parent]
            child_entry = name_to_entry[child]
            parent_entry.children.append(child_entry)

        self.session.add(namespace)
        self.session.commit()

        return namespace

    def ensure_namespace_owl(self, url, keyword=None, encoding=None):
        """Caches an ontology at the given URL if it is not already in the cache

        :param str url: The location of the ontology
        :param str keyword: The optional keyword to use for the namespace if it gets downloaded
        :param str encoding: The optional encoding to use for the namespace if it gets downloaded
        :rtype: Namespace
        """
        if url in self.namespace_model:
            return self.namespace_model[url]

        namespace = self.get_or_create_owl_namespace(url, keyword=keyword, encoding=encoding)

        if not self.use_namespace_cache:
            return namespace

        for entry in namespace.entries:
            self.namespace_object_cache[namespace.url][entry.name] = entry

        return namespace

    def get_namespace_owl_terms(self, url, keyword=None, encoding=None):
        """

        :param str url: The location of the ontology
        :param str keyword: The optional keyword to use for the namespace if it gets downloaded
        :param str encoding: The optional encoding to use for the namespace if it gets downloaded
        :rtype: dict[str,str]
        """
        namespace = self.ensure_namespace_owl(url, keyword=keyword, encoding=encoding)

        if isinstance(namespace, dict):
            return namespace

        return namespace.to_values()

    def get_namespace_owl_edges(self, url, keyword=None):
        """Gets a set of directed edge pairs from the graph representing the ontology at the given IRI

        :param str url: The location of the ontology
        :param str keyword: The optional keyword to use for the namespace if it gets downloaded
        :rtype: list[tuple[str,str]]
        """
        namespace = self.ensure_namespace_owl(url, keyword=keyword)

        return namespace.to_tree_list()


class AnnotationManager(BaseManager):
    """Manages BEL annotations"""

    def __init__(self, use_annotation_cache=None, *args, **kwargs):
        super(AnnotationManager, self).__init__(*args, **kwargs)

        self.use_annotation_cache = (
            use_annotation_cache
            if use_annotation_cache is not None
            else config.get('PYBEL_IN_MEMORY_ANNOTATION_CACHE', False)
        )
        self._annotation_model = {}
        self._annotation_object_cache = defaultdict(dict)

        log.debug('annotation manager caching: %s', self.use_annotation_cache)

    @property
    def annotation_model(self):
        """A dictionary from {annotation URL: Annotation}

        :rtype: dict[str:Annotation]
        """
        return self._annotation_model

    @property
    def annotation_object_cache(self):
        """A dictionary from {annotation URL: {name: AnnotationEntry}}

        :rtype: dict[str,dict[str,AnnotationEntry]]
        """
        return self._annotation_object_cache

    def list_annotations(self):
        """Return a list of all annotations

        :rtype: list[Annotation]
        """
        return self.session.query(Annotation).all()

    def count_annotations(self):
        """Count the number of annotations in the database

        :rtype: int
        """
        return self.session.query(Annotation).count()

    def count_annotation_entries(self):
        """Count the number of annotation entries in the database

        :rtype: int
        """
        return self.session.query(AnnotationEntry).count()

    def drop_annotations(self):
        """Drops all annotations"""
        self.annotation_object_cache.clear()
        self.annotation_model.clear()

        for annotation in self.session.query(AnnotationEntry).all():
            annotation.children[:] = []
            self.session.commit()

        self.session.query(AnnotationEntry).delete()
        self.session.query(Annotation).delete()
        self.session.commit()

    def _cache_annotation(self, annotation):
        """Caches an annotation

        :param Annotation annotation:
        """
        url = annotation.url

        if url in self.annotation_model:
            return

        self.annotation_model[url] = annotation

        for entry in annotation.entries:
            self.annotation_object_cache[url][entry.name] = entry

    def get_annotation_by_url(self, url):
        """Gets an annotation by URL

        :param str url:
        :rtype: Optional[Annotation]
        """
        return self.session.query(Annotation).filter(Annotation.url == url).one_or_none()

    def get_or_create_annotation(self, url):
        """Inserts the namespace file at the given location to the cache

        :param str url: the location of the namespace file
        :rtype: Annotation
        :raises: pybel.resources.exc.ResourceError
        """
        annotation = self.get_annotation_by_url(url)

        if annotation is not None:
            return annotation

        t = time.time()

        bel_resource = get_bel_resource(url)

        annotation = Annotation(
            url=url,
            **_get_annotation_insert_values(bel_resource)
        )
        annotation.entries = [
            AnnotationEntry(name=name, label=label)
            for name, label in bel_resource['Values'].items()
            if name
        ]

        self._cache_annotation(annotation)
        self.session.add(annotation)
        self.session.commit()

        log.info('inserted annotation: %s (%d terms in %.2f seconds)', url, len(bel_resource['Values']),
                 time.time() - t)

        return annotation

    def ensure_annotation(self, url):
        """Caches an annotation file if not already in the cache

        :param str url: the location of the annotation file
        :rtype: Annotation
        :raises: pybel.resources.exc.ResourceError
        """
        if url in self.annotation_model:
            log.debug('already in memory: %s (%d)', url, len(self.annotation_object_cache[url]))
            return self.annotation_model[url]

        result = self.session.query(Annotation).filter(Annotation.url == url).one_or_none()

        if result is not None:
            self._cache_annotation(result)
            log.debug('cached annotation: %s (%d)', url, len(self.annotation_object_cache[url]))
            return result

        return self.get_or_create_annotation(url)

    def get_annotation_entries(self, url):
        """Returns a dict of annotations and their labels for the given annotation file

        :param str url: the location of the annotation file
        :rtype: set[str]
        """
        annotation = self.ensure_annotation(url)
        return annotation.get_entries()

    def get_annotation_entry(self, url, value):
        """Gets a given AnnotationEntry object.

        :param str url: The url of the annotation source
        :param str value: The name of the annotation entry from the given url's document
        :rtype: AnnotationEntry
        """
        if self.annotation_object_cache and url in self.annotation_object_cache:
            annotation_entry = self.annotation_object_cache[url][value]
        else:
            annotation = self.session.query(Annotation).filter(Annotation.url == url).one()
            annotation_entry = self.session.query(AnnotationEntry).filter_by(annotation=annotation, name=value).one()

        return annotation_entry


class OwlAnnotationManager(AnnotationManager):
    """Manages OWL annotations"""

    def get_or_create_owl_annotation(self, url, keyword=None):
        """Caches an ontology as a namespace from the given IRI

        :param str url: the location of the ontology
        :param str keyword: The optional keyword to use for the annotation if it gets downloaded
        :rtype: Annotation
        """
        annotation = self.get_annotation_by_url(url)

        if annotation is not None:
            return annotation

        log.debug('inserting owl %s', url)

        annotation = Annotation(url=url, keyword=keyword)

        graph = parse_owl(url)

        entries = {
            node: AnnotationEntry(name=node, annotation=annotation)  # TODO add label
            for node in graph
        }
        annotation.entries = list(entries.values())

        for u, v in graph.edges_iter():
            entries[u].children.append(entries[v])

        self.session.add(annotation)
        self.session.commit()

        return annotation

    def ensure_annotation_owl(self, url, keyword=None):
        """Caches an ontology as an annotation from the given IRI

        :param str url: the location of the ontology
        :param str keyword: The optional keyword to use for the annotation if it gets downloaded
        :rtype: Annotation
        """
        if url in self.annotation_model:
            return self.annotation_model[url]

        annotation = self.get_or_create_owl_annotation(url, keyword)

        for entry in annotation.entries:
            self.annotation_object_cache[url][entry.name] = entry

        return annotation

    def get_annotation_owl_terms(self, url, keyword=None):
        """Gets a set of classes and individuals in the ontology at the given IRI

        :param str url: the location of the ontology
        :param str keyword: The optional keyword to use for the annotation if it gets downloaded
        :rtype: set[str]
        """
        annotation = self.ensure_annotation_owl(url, keyword)
        return annotation.get_entries()

    def get_annotation_owl_edges(self, url, keyword=None):
        """Gets a set of directed edge pairs from the graph representing the ontology at the given IRI

        :param str url: the location of the ontology
        :param str keyword: The optional keyword to use for the annotation if it gets downloaded
        """
        annotation = self.ensure_annotation_owl(url, keyword=keyword)
        return annotation.to_tree_list()


class EquivalenceManager(NamespaceManager):
    """Manages BEL equivalences"""

    def drop_equivalences(self):
        """Drops all equivalence classes"""
        self.session.query(NamespaceEntryEquivalence).delete()
        self.session.commit()

    def get_equivalence_by_label(self, label):
        """Gets an equivalence class by its label.

        :param str label: the label of the equivalence class. example: '0b20937b-5eb4-4c04-8033-63b981decce7'
                                    for Alzheimer's Disease
        :rtype: NamespaceEntryEquivalence
        """
        return self.session.query(NamespaceEntryEquivalence).filter(NamespaceEntryEquivalence.label == label).one()

    def ensure_equivalence_class(self, label):
        """Ensures the equivalence class is loaded in the database"""
        result = self.session.query(NamespaceEntryEquivalence).filter_by(label=label).one_or_none()

        if result is None:
            result = NamespaceEntryEquivalence(label=label)
            self.session.add(result)
            self.session.commit()

        return result

    def insert_equivalences(self, equivalence_url, namespace_url):
        """Given a url to a .beleq file and its accompanying namespace url, populate the database

        :param str equivalence_url:
        :param str namespace_url:
        :raises: pybel.resources.exc.ResourceError
        """
        namespace = self.ensure_namespace(namespace_url)

        if not isinstance(namespace, Namespace):
            raise ValueError("Can't insert equivalences for non-cachable namespace")

        equivalence_resource = get_bel_resource(equivalence_url)
        values = equivalence_resource['Values']

        for entry in namespace.entries:
            label = values[entry.name]
            entry.equivalence = self.ensure_equivalence_class(label=label)

        namespace.has_equivalences = True

        log.info('inserted equivalences: %s (%d terms)', equivalence_url, len(values))

        self.session.commit()

    def ensure_equivalences(self, url, namespace_url):
        """Check if the equivalence file is already loaded, and if not, load it

        :param str url: The URL of the equivalence file corresponding to the namespace file
        :param str namespace_url: The URL of the namespace file
        :raises: pybel.resources.exc.ResourceError
        """
        self.ensure_namespace(namespace_url)

        ns = self.get_namespace_by_url(namespace_url)

        if not ns.has_equivalences:
            self.insert_equivalences(url, namespace_url)

    def get_equivalence_by_entry(self, url, name):
        """Gets the equivalence class of the entry in the given namespace

        :param str url: The url of the namespace source
        :param str name: The value of the namespace from the given url's document
        :rtype: NamespaceEntryEquivalence
        """
        entry = self.get_namespace_entry(url, name)
        return entry.equivalence

    def get_equivalence_members(self, label):
        """Gets all members of the given equivalence class

        :param str label: the label of the equivalence class. example: '0b20937b-5eb4-4c04-8033-63b981decce7'
                                    for Alzheimer's Disease
        :rtype: list[NamespaceEntry]
        """
        eq = self.get_equivalence_by_label(label)
        return eq.members


class NetworkManager(NamespaceManager, AnnotationManager):
    """Groups functions for inserting and querying networks in the database's network store."""

    def count_networks(self):
        """Counts the number of networks in the cache

        :rtype: int
        """
        return self.session.query(func.count(Network.id)).scalar()

    def list_networks(self):
        """Lists all networks in the cache

        :rtype: list[Network]
        """
        return self.session.query(Network).all()

    # FIXME there must be a better way to do this on the server without getting problems with logical inconsistencies
    def list_recent_networks(self):
        """Lists the most recently created version of each network (by name)

        :rtype: list[Network]
        """
        networks = self.session.query(Network).order_by(Network.name, Network.created.desc())
        return [
            next(si)
            for k, si in groupby(networks, lambda n: n.name)
        ]

    def has_name_version(self, name, version):
        """Checks if the name/version combination is already in the database

        :param str name: The network name
        :param str version: The network version
        :rtype: bool
        """
        return self.session.query(exists().where(and_(Network.name == name, Network.version == version))).scalar()

    @staticmethod
    def iterate_singleton_edges_from_network(network):
        """Gets all edges that only belong to the given network

        :type network: Network
        :rtype: iter[Edge]
        """
        return (  # TODO implement with nested SQLAlchemy query for better speed
            edge
            for edge in network.edges
            if edge.networks.count() == 1
        )

    def drop_network(self, network):
        """Drops a network, while also cleaning up any edges that are no longer part of any network.

        :type network: Network
        """
        for edge in self.iterate_singleton_edges_from_network(network):
            self.session.delete(edge)

        self.session.delete(network)
        self.session.commit()

    def drop_network_by_id(self, network_id):
        """Drops a network by its database identifier

        :param int network_id: The network's database identifier
        """
        network = self.session.query(Network).get(network_id)
        self.drop_network(network)

    def drop_networks(self):
        """Drops all networks"""
        for network in self.session.query(Network).all():
            self.session.delete(network)
            self.session.commit()

    def get_network_versions(self, name):
        """Returns all of the versions of a network with the given name

        :param str name: The name of the network to query
        :rtype: set[str]
        """
        return {
            version
            for version, in self.session.query(Network.version).filter(Network.name == name).all()
        }

    def get_network_by_name_version(self, name, version):
        """Loads most recently added graph with the given name, or allows for specification of version

        :param str name: The name of the network.
        :param str version: The version string of the network.
        :rtype: BELGraph
        """
        network = self.session.query(Network).filter(Network.name == name, Network.version == version).one()
        return network.as_bel()

    def get_networks_by_name(self, name):
        """Gets all networks with the given name. Useful for getting all versions of a given network.

        :param str name: The name of the network
        :rtype: list[Network]
        """
        return self.session.query(Network).filter(Network.name.like(name)).all()

    def get_most_recent_network_by_name(self, name):
        """Gets the most recently created network with the given name.

        :param str name: The name of the network
        :rtype: Network
        """
        return self.session.query(Network).filter(Network.name == name).order_by(Network.created.desc()).first()

    def get_network_by_id(self, network_id):
        """Gets a network from the database by its identifier.

        :param int network_id: The network's database identifier
        :rtype: Network
        """
        return self.session.query(Network).get(network_id)

    def get_graph_by_id(self, network_id):
        """Gets a network from the database by its identifier and converts it to a BEL graph

        :param int network_id: The network's database identifier
        :rtype: BELGraph
        """
        network = self.get_network_by_id(network_id)
        return network.as_bel()

    def get_networks_by_ids(self, network_ids):
        """Gets a list of networks with the given identifiers. Note: order is not necessarily preserved.

        :param iter[int] network_ids: The identifiers of networks in the database
        :rtype: list[Network]
        """
        return self.session.query(Network).filter(Network.id.in_(network_ids)).all()

    def get_graphs_by_ids(self, network_ids):
        """Gets a list of networks with the given identifiers and converts to BEL graphs. Note: order is not
        necessarily preserved.

        :param iter[int] network_ids: The identifiers of networks in the database
        :rtype: list[BELGraph]
        """
        return [
            self.get_graph_by_id(network_id)
            for network_id in network_ids
        ]

    def get_graph_by_ids(self, network_ids):
        """Gets a combine BEL Graph from a list of network identifiers

        :param list[int] network_ids: A list of network identifiers
        :rtype: BELGraph
        """
        if len(network_ids) == 1:
            return self.get_graph_by_id(network_ids[0])

        return union(self.get_graphs_by_ids(network_ids))


class InsertManager(NamespaceManager, AnnotationManager, LookupManager):
    """Manages inserting data into the edge store"""

    def __init__(self, *args, **kwargs):
        super(InsertManager, self).__init__(*args, **kwargs)

        # A set of dictionaries that contains objects of the type described by the key
        self.object_cache_modification = {}
        self.object_cache_property = {}
        self.object_cache_node = {}
        self.object_cache_edge = {}
        self.object_cache_evidence = {}
        self.object_cache_citation = {}
        self.object_cache_author = {}

    def insert_graph(self, graph, store_parts=True):
        """Inserts a graph in the database and returns the corresponding Network model.

        :param BELGraph graph: A BEL graph
        :param bool store_parts: Should the graph be stored in the edge store?
        :rtype: Network
        :raises: pybel.resources.exc.ResourceError
        """
        if not graph.name:
            raise ValueError('Can not upload a graph without a name')

        if not graph.version:
            raise ValueError('Can not upload a graph without a version')

        log.debug('inserting %s v%s', graph.name, graph.version)

        t = time.time()

        self.ensure_default_namespace()

        for url in graph.namespace_url.values():
            if url in graph.uncached_namespaces:
                continue

            self.ensure_namespace(url)

        for keyword, pattern in graph.namespace_pattern.items():
            self.ensure_regex_namespace(keyword, pattern)

        for url in graph.annotation_url.values():
            self.ensure_annotation(url)

        network = Network(**{
            key: value
            for key, value in graph.document.items()
            if key in METADATA_INSERT_KEYS
        })

        network.store_bel(graph)

        if store_parts:
            self._store_graph_parts(network, graph)

        self.session.add(network)
        self.session.commit()

        log.info('inserted %s v%s in %.2f seconds', graph.name, graph.version, time.time() - t)

        return network

    def _store_graph_parts(self, network, graph):
        """Stores the given graph into the edge store.

        :param Network network: A SQLAlchemy PyBEL Network object
        :param BELGraph graph: A BEL Graph
        :raises: pybel.resources.exc.ResourceError
        :raises: EdgeAddError
        """
        self.ensure_namespace(GOCC_LATEST)

        log.debug('inserting %s into edge store', graph)
        log.debug('storing graph parts: nodes')
        t = time.time()

        for node in graph:
            namespace = graph.node[node].get(NAMESPACE)

            if graph.skip_storing_namespace(namespace):
                continue  # already know this node won't be cached

            node_object = self.get_or_create_node(graph, node)

            if node_object is None:
                log.warning('can not add node %s', node)
                continue

            network.nodes.append(node_object)

        log.debug('stored nodes in %.2f seconds', time.time() - t)
        log.debug('storing graph parts: edges')
        t = time.time()
        c = 0
        for u, v, data in graph.edges_iter(data=True):

            if hash_node(u) not in self.object_cache_node:
                log.debug('Skipping uncached node: %s', u)
                continue

            if hash_node(v) not in self.object_cache_node:
                log.debug('Skipping uncached node: %s', v)
                continue

            if RELATION not in data:
                continue

            if data[RELATION] in UNQUALIFIED_EDGES:
                try:
                    self._add_unqualified_edge(network, graph, u, v, data)
                except Exception as e:
                    self.session.rollback()
                    log.exception('error storing edge in database. edge data: %s', data)
                    six.raise_from(EdgeAddError(e, u, v, data), e)

            elif EVIDENCE not in data or CITATION not in data:
                continue

            elif CITATION_TYPE not in data[CITATION] or CITATION_REFERENCE not in data[CITATION]:
                continue

            else:
                try:
                    self._add_qualified_edge(network, graph, u, v, data)
                except Exception as e:
                    self.session.rollback()
                    log.exception('error storing edge in database. edge data: %s', data)
                    six.raise_from(EdgeAddError(e, u, v, data), e)

        log.debug('stored edges in %.2f seconds', time.time() - t)

        if c:
            log.info('skipped %d edges', c)

    @staticmethod
    def _iter_annotations_from_dict(graph, data):
        """Iterates over the key/value pairs in this edge data dictionary normalized to their source URLs

        :param BELGraph graph: A BEL graph
        :param dict[str,dict[str,bool]] data: A PyBEL edge data dictionary
        :rtype: iter[tuple[str,str]]
        """
        for key, values in data.items():
            if key in graph.annotation_url:
                url = graph.annotation_url[key]
            elif key in graph.annotation_owl:
                url = graph.annotation_owl[key]
            elif key in graph.annotation_list:
                continue  # skip those
            elif key in graph.annotation_pattern:
                log.debug('pattern annotation in database not implemented yet not implemented')  # FIXME
                continue
            else:
                raise ValueError('Graph resources does not contain keyword: {}'.format(key))

            for value in values:
                yield url, value

    def _get_annotation_entries(self, graph, data):
        """Gets the annotation entries for this edge's data

        :param BELGraph graph: A BEL graph
        :param dict data: A PyBEL edge data dictionary
        :rtype: list[AnnotationEntry]
        """
        annotations = data.get(ANNOTATIONS)

        if annotations is None:
            return

        return [
            self.get_annotation_entry(url, value)
            for url, value in self._iter_annotations_from_dict(graph, annotations)
        ]

    def _add_qualified_edge(self, network, graph, u, v, data):
        citation_dict = data[CITATION]

        citation = self.get_or_create_citation(
            type=citation_dict.get(CITATION_TYPE),
            reference=citation_dict.get(CITATION_REFERENCE),
            name=citation_dict.get(CITATION_NAME),
            title=citation_dict.get(CITATION_TITLE),
            volume=citation_dict.get(CITATION_VOLUME),
            issue=citation_dict.get(CITATION_ISSUE),
            pages=citation_dict.get(CITATION_PAGES),
            date=citation_dict.get(CITATION_DATE),
            first=citation_dict.get(CITATION_FIRST_AUTHOR),
            last=citation_dict.get(CITATION_LAST_AUTHOR),
            authors=citation_dict.get(CITATION_AUTHORS),
        )

        evidence = self.get_or_create_evidence(citation, data[EVIDENCE])

        properties = self.get_or_create_properties(graph, data)
        if properties is None:
            return

        annotations = self._get_annotation_entries(graph, data)

        bel = graph.edge_to_bel(u, v, data=data)
        edge_hash = hash_edge(u, v, data)
        edge = self.get_or_create_edge(
            source=self.object_cache_node[hash_node(u)],
            target=self.object_cache_node[hash_node(v)],
            relation=data[RELATION],
            bel=bel,
            edge_hash=edge_hash,
            evidence=evidence,
            properties=properties,
            annotations=annotations,
        )
        network.edges.append(edge)

    def _add_unqualified_edge(self, network, graph, u, v, data):
        bel = graph.edge_to_bel(u, v, data=data)
        edge_hash = hash_edge(u, v, data)
        edge = self.get_or_create_edge(
            source=self.object_cache_node[hash_node(u)],
            target=self.object_cache_node[hash_node(v)],
            relation=data[RELATION],
            bel=bel,
            edge_hash=edge_hash,
        )
        network.edges.append(edge)

    def get_or_create_evidence(self, citation, text):
        """Creates entry and object for given evidence if it does not exist.

        :param Citation citation: Citation object obtained from :func:`get_or_create_citation`
        :param str text: Evidence text
        :rtype: Evidence
        """
        evidence_hash = hash_evidence(text=text, type=str(citation.type), reference=str(citation.reference))

        if evidence_hash in self.object_cache_evidence:
            evidence = self.object_cache_evidence[evidence_hash]
            self.session.add(evidence)
            return evidence

        evidence = self.get_evidence_by_hash(evidence_hash)

        if evidence is not None:
            self.object_cache_evidence[evidence_hash] = evidence
            return evidence

        evidence = Evidence(
            text=text,
            citation=citation,
            sha512=evidence_hash
        )

        self.session.add(evidence)
        self.object_cache_evidence[evidence_hash] = evidence
        return evidence

    def get_or_create_node(self, graph, node_identifier):
        """Creates entry and object for given node if it does not exist.

        :param BELGraph graph: A BEL graph
        :param tuple node_identifier: A PyBEL node tuple
        :rtype: Node
        """
        node_hash = hash_node(node_identifier)
        if node_hash in self.object_cache_node:
            return self.object_cache_node[node_hash]

        node_data = graph.node[node_identifier]
        bel = node_to_bel(node_data)

        node = self.get_node_by_hash(node_hash)

        if node is not None:
            self.object_cache_node[node_hash] = node
            return node

        type = node_data[FUNCTION]
        node = Node(type=type, bel=bel, sha512=node_hash)

        namespace = node_data.get(NAMESPACE)

        if namespace is None:
            pass

        elif namespace in graph.namespace_url:
            url = graph.namespace_url[namespace]
            name = node_data[NAME]
            entry = self.get_namespace_entry(url, name)

            if entry is None:
                log.debug('skipping node with identifier %s: %s', url, name)
                return

            self.session.add(entry)
            node.namespace_entry = entry

        elif namespace in graph.namespace_pattern:
            name = node_data[NAME]
            pattern = graph.namespace_pattern[namespace]
            entry = self.get_or_create_regex_namespace_entry(namespace, pattern, name)

            self.session.add(entry)
            node.namespace_entry = entry

        else:
            log.warning("No reference in BELGraph for namespace: {}".format(node_data[NAMESPACE]))
            return

        if VARIANTS in node_data or FUSION in node_data:
            node.is_variant = True
            node.has_fusion = FUSION in node_data

            modifications = self.get_or_create_modification(graph, node_data)

            if modifications is None:
                log.warning('could not create %s because had an uncachable modification', bel)
                return

            node.modifications = modifications

        self.session.add(node)
        self.object_cache_node[node_hash] = node
        return node

    def drop_nodes(self):
        """Drops all nodes in RDB"""
        t = time.time()

        self.session.query(Node).delete()
        self.session.commit()

        log.info('dropped all nodes in %.2f seconds', time.time() - t)

    def drop_edges(self):
        """Drops all edges in RDB"""
        t = time.time()

        self.session.query(Edge).delete()
        self.session.commit()

        log.info('dropped all edges in %.2f seconds', time.time() - t)

    def get_or_create_edge(self, source, target, relation, bel, edge_hash, evidence=None, annotations=None,
                           properties=None):
        """Creates entry for given edge if it does not exist.

        :param Node source: Source node of the relation
        :param Node target: Target node of the relation
        :param str relation: Type of the relation between source and target node
        :param str bel: BEL statement that describes the relation
        :param str edge_hash: A hash of the edge
        :param Evidence evidence: Evidence object that proves the given relation
        :param list[Property] properties: List of all properties that belong to the edge
        :param list[AnnotationEntry] annotations: List of all annotations that belong to the edge
        :rtype: Edge
        """
        if edge_hash in self.object_cache_edge:
            edge = self.object_cache_edge[edge_hash]
            self.session.add(edge)
            return edge

        edge = self.get_edge_by_hash(edge_hash)

        if edge is not None:
            self.object_cache_edge[edge_hash] = edge
            return edge

        edge = Edge(
            source=source,
            target=target,
            relation=relation,
            bel=bel,
            sha512=edge_hash,
        )

        if evidence is not None:
            edge.evidence = evidence
        if properties is not None:
            edge.properties = properties
        if annotations is not None:
            edge.annotations = annotations

        self.session.add(edge)
        self.object_cache_edge[edge_hash] = edge
        return edge

    def get_or_create_citation(self, type, reference, name=None, title=None, volume=None, issue=None, pages=None,
                               date=None, first=None, last=None, authors=None):
        """Creates entry for given citation if it does not exist.

        :param str type: Citation type (e.g. PubMed)
        :param str reference: Identifier of the given citation (e.g. PubMed id)
        :param str name: Name of the publication
        :param str title: Title of article
        :param str volume: Volume of publication
        :param str issue: Issue of publication
        :param str pages: Pages of issue
        :param str date: Date of publication in ISO 8601 (YYYY-MM-DD) format
        :param str first: Name of first author
        :param str last: Name of last author
        :param str or list[str] authors: Either a list of authors separated by |, or an actual list of authors
        :rtype: Citation
        """
        type = type.strip()
        reference = reference.strip()

        citation_hash = hash_citation(type=type, reference=reference)

        if citation_hash in self.object_cache_citation:
            citation = self.object_cache_citation[citation_hash]
            self.session.add(citation)
            return citation

        citation = self.get_citation_by_hash(citation_hash)

        if citation is not None:
            self.object_cache_citation[citation_hash] = citation
            return citation

        citation = Citation(
            type=type,
            reference=reference,
            sha512=citation_hash,
            name=name,
            title=title,
            volume=volume,
            issue=issue,
            pages=pages
        )
        if date is not None:
            citation.date = parse_datetime(date)

        if first is not None:
            citation.first = self.get_or_create_author(first)

        if last is not None:
            citation.last = self.get_or_create_author(last)

        if authors is not None:
            for author in (authors.split('|') if isinstance(authors, string_types) else authors):
                author_model = self.get_or_create_author(author)
                if author_model not in citation.authors:
                    citation.authors.append(author_model)

        self.session.add(citation)
        self.object_cache_citation[citation_hash] = citation
        return citation

    def get_or_create_author(self, name):
        """Gets an author by name, or creates one

        :param str name: An author's name
        :rtype: Author
        """
        author = self.object_cache_author.get(name)

        if author is not None:
            self.session.add(author)
            return author

        author = self.get_author_by_name(name)

        if author is not None:
            self.object_cache_author[name] = author
            return author

        author = self.object_cache_author[name] = Author(name=name)
        self.session.add(author)
        return author

    def get_modification_by_hash(self, modification_hash):
        return self.session.query(Modification).filter(Modification.sha512 == modification_hash).one_or_none()

    def get_or_create_modification(self, graph, node_data):
        """Creates a list of modification objects (Modification) that belong to the node described by
        node_data.

        :param BELGraph graph: A BEL graph
        :param dict node_data: Describes the given node and contains is_variant information
        :return: A list of modification objects belonging to the given node
        :rtype: list[Modification]
        """
        modification_list = []
        if FUSION in node_data:
            mod_type = FUSION
            node_data = node_data[FUSION]
            p3_namespace_url = graph.namespace_url[node_data[PARTNER_3P][NAMESPACE]]

            if p3_namespace_url in graph.uncached_namespaces:
                log.warning('uncached namespace %s in fusion()', p3_namespace_url)
                return

            p3_name = node_data[PARTNER_3P][NAME]
            p3_namespace_entry = self.get_namespace_entry(p3_namespace_url, p3_name)

            if p3_namespace_entry is None:
                log.warning('Could not find namespace entry %s %s', p3_namespace_url, p3_name)
                return  # FIXME raise?

            p5_namespace_url = graph.namespace_url[node_data[PARTNER_5P][NAMESPACE]]

            if p5_namespace_url in graph.uncached_namespaces:
                log.warning('uncached namespace %s in fusion()', p5_namespace_url)
                return

            p5_name = node_data[PARTNER_5P][NAME]
            p5_namespace_entry = self.get_namespace_entry(p5_namespace_url, p5_name)

            if p5_namespace_entry is None:
                log.warning('Could not find namespace entry %s %s', p5_namespace_url, p5_name)
                return  # FIXME raise?

            fusion_dict = {
                'type': mod_type,
                'p3_partner': p3_namespace_entry,
                'p5_partner': p5_namespace_entry,
            }

            node_range_3p = node_data.get(RANGE_3P)
            if node_range_3p and FUSION_REFERENCE in node_range_3p:
                fusion_dict.update({
                    'p3_reference': node_range_3p[FUSION_REFERENCE],
                    'p3_start': node_range_3p[FUSION_START],
                    'p3_stop': node_range_3p[FUSION_STOP],
                })

            node_range_5p = node_data.get(RANGE_5P)
            if node_range_5p and FUSION_REFERENCE in node_range_5p:
                fusion_dict.update({
                    'p5_reference': node_range_5p[FUSION_REFERENCE],
                    'p5_start': node_range_5p[FUSION_START],
                    'p5_stop': node_range_5p[FUSION_STOP],
                })

            modification_list.append(fusion_dict)

        else:
            for variant in node_data[VARIANTS]:
                mod_type = variant[KIND].strip()
                if mod_type == HGVS:
                    modification_list.append({
                        'type': mod_type,
                        'variantString': variant[IDENTIFIER]
                    })

                elif mod_type == FRAGMENT:
                    if FRAGMENT_MISSING in variant:
                        modification_list.append({
                            'type': mod_type,
                        })
                    else:
                        modification_list.append({
                            'type': mod_type,
                            'p3_start': variant[FRAGMENT_START],
                            'p3_stop': variant[FRAGMENT_STOP]
                        })

                elif mod_type in {GMOD, PMOD}:
                    variant_identifier = variant[IDENTIFIER]
                    namespace_url = normalize_url(graph, variant_identifier[NAMESPACE])

                    if namespace_url in graph.uncached_namespaces:
                        log.warning('uncached namespace %s in fusion()', namespace_url)
                        return

                    mod_entry = self.get_namespace_entry(namespace_url, variant_identifier[NAME])

                    if mod_type == GMOD:
                        modification_list.append({
                            'type': mod_type,
                            'identifier': mod_entry
                        })
                    if mod_type == PMOD:
                        modification_list.append({
                            'type': mod_type,
                            'identifier': mod_entry,
                            'residue': variant[PMOD_CODE].strip() if PMOD_CODE in variant else None,
                            'position': variant[PMOD_POSITION] if PMOD_POSITION in variant else None
                        })

        modifications = []
        for modification in modification_list:
            mod_hash = hash_dump(modification)

            mod = self.object_cache_modification.get(mod_hash)
            if mod is None:
                mod = self.get_modification_by_hash(mod_hash)
                if not mod:
                    modification['sha512'] = mod_hash
                    mod = Modification(**modification)

                self.object_cache_modification[mod_hash] = mod
            modifications.append(mod)

        return modifications

    def get_property_by_hash(self, property_hash):
        """Gets a property by its hash if it exists

        :param str property_hash: The hash of the property to search
        :rtype: Optional[Property]
        """
        return self.session.query(Property).filter(Property.sha512 == property_hash).one_or_none()

    def _make_property_from_dict(self, property_def):
        property_hash = hash_dump(property_def)

        edge_property = self.object_cache_property.get(property_hash)
        if edge_property is None:
            edge_property = self.get_property_by_hash(property_hash)

            if not edge_property:
                property_def['sha512'] = property_hash
                edge_property = Property(**property_def)

            self.object_cache_property[property_hash] = edge_property

        return edge_property

    def get_or_create_properties(self, graph, edge_data):  # TODO make for just single property then loop with other fn.
        """Creates a list of all subject and object related properties of the edge. Returns None if the property cannot
        be constructed due to missing cache entries.

        :param BELGraph graph: A BEL graph
        :param dict edge_data: Describes the context of the given edge.
        :return: A list of all subject and object properties of the edge
        :rtype: list[Property]
        """
        property_list = []
        for participant in (SUBJECT, OBJECT):
            participant_data = edge_data.get(participant)
            if participant_data is None:
                continue

            location = participant_data.get(LOCATION)
            if location is not None:
                location_property_dict = {
                    'is_subject': participant == SUBJECT,
                    'modifier': LOCATION
                }

                location_namespace = location[NAMESPACE]

                if location_namespace == GOCC_KEYWORD and GOCC_KEYWORD not in graph.namespace_url:
                    namespace_url = GOCC_LATEST
                else:
                    namespace_url = graph.namespace_url[location_namespace]

                    if namespace_url in graph.uncached_namespaces:
                        log.warning('uncached namespace %s in loc() on line %s', location_namespace,
                                    edge_data.get(LINE))
                        return

                participant_name = location[NAME]
                location_property_dict['effect'] = self.get_namespace_entry(namespace_url, participant_name)
                if location_property_dict['effect'] is None:
                    raise IndexError('did not get {}: {}'.format(namespace_url, participant_name))

                property_list.append(location_property_dict)

            modifier = participant_data.get(MODIFIER)
            if modifier is not None:
                modifier_property_dict = {
                    'is_subject': participant == SUBJECT,
                    'modifier': modifier
                }

                if modifier == TRANSLOCATION and EFFECT in participant_data:
                    for effect_type, effect_value in participant_data[EFFECT].items():
                        tmp_dict = deepcopy(modifier_property_dict)
                        tmp_dict['relative_key'] = effect_type

                        if NAMESPACE not in effect_value:
                            tmp_dict['propValue'] = effect_value
                            raise ValueError('shouldnt use propValue')
                        else:
                            effect_namespace = effect_value[NAMESPACE]

                            if effect_namespace == GOCC_KEYWORD and GOCC_KEYWORD not in graph.namespace_url:
                                namespace_url = GOCC_LATEST
                            elif effect_namespace in graph.namespace_url:
                                namespace_url = graph.namespace_url[effect_namespace]
                            else:
                                log.warning('namespace not enumerated in modifier %s', effect_namespace)
                                return

                            if namespace_url in graph.uncached_namespaces:
                                log.warning('uncached namespace %s in tloc() on line %s ', effect_namespace,
                                            edge_data.get(LINE))
                                return

                            effect_name = effect_value[NAME]
                            tmp_dict['effect'] = self.get_namespace_entry(namespace_url, effect_name)

                            if tmp_dict['effect'] is None:
                                log.warning('could not find tloc() %s %s', namespace_url, effect_name)
                                return  # FIXME raise?

                        property_list.append(tmp_dict)

                elif modifier == ACTIVITY:
                    effect = participant_data.get(EFFECT)
                    if effect is not None:
                        namespace_url = normalize_url(graph, effect[NAMESPACE])

                        if namespace_url in graph.uncached_namespaces:
                            log.warning('uncached namespace %s in fusion()', namespace_url)
                            return

                        modifier_property_dict['effect'] = self.get_namespace_entry(namespace_url, effect[NAME])

                    property_list.append(modifier_property_dict)

                elif modifier == DEGRADATION:
                    property_list.append(modifier_property_dict)

                else:
                    raise ValueError('unknown modifier: {}'.format(modifier))

        return [
            self._make_property_from_dict(property_def)
            for property_def in property_list
        ]


class Manager(QueryManager, InsertManager, NetworkManager, EquivalenceManager, OwlNamespaceManager,
              OwlAnnotationManager):
    """The definition cache manager takes care of storing BEL namespace and annotation files for later use. It uses
    SQLite by default for speed and lightness, but any database can be used with its SQLAlchemy interface.
    """

    @staticmethod
    def ensure(connection=None, *args, **kwargs):
        """A convenience method for turning a string into a connection, or passing a :class:`Manager` through.

        :param connection: An RFC-1738 database connection string, a pre-built :class:`Manager`, or ``None``
                            for default connection
        :type connection: Optional[str or Manager]
        :param list args: Positional arguments to pass to the constructor of :class:`Manager`
        :param dict kwargs: Keyword arguments to pass to the constructor of :class:`Manager`
        :rtype: Manager
        """
        if connection is None or isinstance(connection, string_types):
            return Manager(connection=connection, *args, **kwargs)

        return connection


def normalize_url(graph, keyword):  # FIXME move to utilities and unit test
    """
    :type graph: BELGraph
    :param str keyword: Namespace URL keyword
    :rtype: Optional[str]
    """
    if keyword == BEL_DEFAULT_NAMESPACE and BEL_DEFAULT_NAMESPACE not in graph.namespace_url:
        return BEL_DEFAULT_NAMESPACE_URL

    if keyword == GOCC_KEYWORD and GOCC_KEYWORD not in graph.namespace_url:
        return GOCC_LATEST

    return graph.namespace_url.get(keyword)
