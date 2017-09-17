# -*- coding: utf-8 -*-

"""
Definition Cache Manager
------------------------
Under the hood, PyBEL caches namespace and annotation files for quick recall on later use. The user doesn't need to
enable this option, but can specify a database location if they choose.
"""

import logging
import time

from collections import defaultdict
from copy import deepcopy
from six import string_types
from six.moves.cPickle import dumps
from sqlalchemy import func, exists

from .base_manager import BaseManager
from .models import (
    Network,
    Annotation,
    AnnotationEntry,
    Namespace,
    NamespaceEntryEquivalence,
    NamespaceEntry,
    Node,
    Edge,
    Evidence,
    Citation,
    Property,
    Author,
    Modification,
)
from .query_manager import QueryManager
from .utils import parse_owl, extract_shared_required, extract_shared_optional
from ..canonicalize import edge_to_bel, node_to_bel
from ..constants import *
from ..io.gpickle import to_bytes
from ..struct import BELGraph, union
from ..utils import (
    get_bel_resource,
    parse_datetime,
    hash_edge,
    hash_node,
    hash_evidence,
    hash_citation,
    hash_dump,
)

__all__ = [
    'Manager',
    'NetworkManager',
]

log = logging.getLogger(__name__)

DEFAULT_BELNS_ENCODING = ''.join(sorted(belns_encodings))


class NamespaceManager(BaseManager):
    """Manages BEL namespaces"""

    def __init__(self, *args, **kwargs):
        super(NamespaceManager, self).__init__(*args, **kwargs)

        #: A dictionary from {namespace URL: {name: set of encodings}}
        self.namespace_cache = defaultdict(dict)
        #: A dictionary from {namespace URL: {name: database ID}}
        self.namespace_id_cache = defaultdict(dict)
        #: A dictionary from {namespace URL: Namespace}
        self.namespace_model = {}

        #: A dictionary from {namespace URL: {name: NamespaceEntry}}
        self.namespace_object_cache = defaultdict(dict)

        #: A dictionary from {namespace URL: set of (parent, child) tuples}
        self.namespace_edge_cache = {}

    def list_namespaces(self):
        """Returns a list of all namespaces

        :rtype: list[Namespace]
        """
        return self.session.query(Namespace).all()

    def drop_namespaces(self):
        """Drops all namespaces"""
        self.namespace_cache.clear()
        self.namespace_id_cache.clear()
        self.namespace_object_cache.clear()
        self.namespace_model.clear()
        self.namespace_edge_cache.clear()

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

    def insert_namespace(self, url):
        """Inserts the namespace file at the given location to the cache. If not cachable, returns the dict of
        the values of this namespace.

        :param str url: the location of the namespace file
        :return: SQL Alchemy model instance, populated with data from URL
        :rtype: Namespace or dict
        """
        log.info('downloading namespace %s', url)

        bel_resource = get_bel_resource(url)

        values = {c: e if e else DEFAULT_BELNS_ENCODING for c, e in bel_resource['Values'].items() if c}

        if bel_resource['Processing']['CacheableFlag'] not in {'yes', 'Yes', 'True', 'true'}:
            return values

        log.info('inserting namespace %s', url)

        namespace_insert_values = {
            'name': bel_resource['Namespace']['NameString'],
            'url': url,
            'domain': bel_resource['Namespace']['DomainString']
        }

        namespace_insert_values.update(extract_shared_required(bel_resource, 'Namespace'))
        namespace_insert_values.update(extract_shared_optional(bel_resource, 'Namespace'))

        namespace_mapping = {
            'species': ('Namespace', 'SpeciesString'),
            'query_url': ('Namespace', 'QueryValueURL')
        }

        for database_column, (section, key) in namespace_mapping.items():
            if section in bel_resource and key in bel_resource[section]:
                namespace_insert_values[database_column] = bel_resource[section][key]

        namespace = Namespace(**namespace_insert_values)
        namespace.entries = [NamespaceEntry(name=c, encoding=e) for c, e in values.items()]

        self.session.add(namespace)
        self.session.commit()

        return namespace

    def ensure_namespace(self, url, cache_objects=False):
        """Caches a namespace file if not already in the cache. If not cachable, returns a dict of the values

        :param str url: the location of the namespace file
        :param bool cache_objects: Indicates if the object_cache should be filed with NamespaceEntry objects.
        :return: The namespace instance
        :rtype: Namespace or dict
        """
        if url in self.namespace_model:
            log.debug('already in memory: %s (%d)', url, len(self.namespace_cache[url]))
            return self.namespace_model[url]

        else:
            t = time.time()
            results = self.session.query(Namespace).filter(Namespace.url == url).one_or_none()

            if results is None:
                results = self.insert_namespace(url)
            else:
                log.debug('loaded namespace: %s (%d, %.2fs)', url, len(results.entries), time.time() - t)

            if results is None:
                raise ValueError('No results for {}'.format(url))
            elif isinstance(results, dict):
                return results
            elif not results.entries:
                raise ValueError('No entries for {}'.format(url))

            self.namespace_model[url] = results

            for entry in results.entries:
                self.namespace_cache[url][entry.name] = list(entry.encoding if entry.encoding else belns_encodings)
                self.namespace_id_cache[url][entry.name] = entry.id

        if cache_objects and url not in self.namespace_object_cache:
            log.debug('loading namespace cache_objects: %s (%d)', url, len(self.namespace_cache[url]))
            for entry in results.entries:
                self.namespace_object_cache[url][entry.name] = entry

        return results

    # TODO merge get_namespace and ensure_namespace
    def get_namespace(self, url, cache_objects=False):
        """Returns a dict of names and their encodings for the given namespace URL.

        :param str url: the location of the namespace file
        :param bool cache_objects: Indicates if the object_cache should be filed with :class:`NamespaceEntry` objects.
        """
        result = self.ensure_namespace(url, cache_objects=cache_objects)

        if isinstance(result, dict):
            return result
        else:
            # self.ensure_namespace makes sure it's in the cache if its not cachable
            return self.namespace_cache[url]

    def get_namespace_by_url(self, url):
        """Looks up a namespace by url

        :param str url:
        :rtype: Namespace
        """
        return self.session.query(Namespace).filter(Namespace.url == url).one_or_none()

    def get_namespace_entry(self, url, value):
        """Gets a given NamespaceEntry object.

        :param str url: The url of the namespace source
        :param str value: The value of the namespace from the given url's document
        :return: An NamespaceEntry object
        :rtype: NamespaceEntry
        """
        if self.namespace_object_cache and url in self.namespace_object_cache:
            return self.namespace_object_cache[url][value]

        namespace = self.session.query(Namespace).filter(Namespace.url == url).one()
        namespace_entry = self.session.query(NamespaceEntry).filter_by(namespace=namespace, name=value).one_or_none()

        return namespace_entry


class OwlNamespaceManager(NamespaceManager):
    """Manages OWL namespaces"""

    def insert_namespace_owl(self, iri, keyword=None, encoding=None):
        """Caches an ontology at the given IRI

        :param str iri: the location of the ontology
        """
        log.info('inserting owl %s', iri)

        namespace = Namespace(url=iri, keyword=keyword)

        graph = parse_owl(iri)

        encoding = encoding if encoding else DEFAULT_BELNS_ENCODING

        entries = {
            node: NamespaceEntry(name=node, namespace=namespace, encoding=encoding)
            for node in graph.nodes_iter()
        }
        namespace.entries = list(entries.values())

        for u, v in graph.edges_iter():
            entries[u].children.append(entries[v])

        self.session.add(namespace)
        self.session.commit()

        return namespace

    def ensure_namespace_owl(self, iri, keyword=None):
        """Caches an ontology at the given IRI if it is not already in the cache

        :param str iri: the location of the ontology
        """
        if iri in self.namespace_cache:
            return

        results = self.session.query(Namespace).filter(Namespace.url == iri).one_or_none()
        if results is None:
            results = self.insert_namespace_owl(iri, keyword)

        for entry in results.entries:
            self.namespace_cache[iri][entry.name] = list(entry.encoding)  # set()
            self.namespace_id_cache[iri][entry.name] = entry.id

        self.namespace_edge_cache[iri] = {
            (sub.name, sup.name)
            for sub in results.entries for sup in sub.children
        }

        return results

    def get_namespace_owl_terms(self, iri, keyword=None):
        self.ensure_namespace_owl(iri, keyword)
        return self.namespace_cache[iri]

    def get_namespace_owl_edges(self, iri, keyword=None):
        """Gets a set of directed edge pairs from the graph representing the ontology at the given IRI

        :param str iri: the location of the ontology
        """
        self.ensure_namespace_owl(iri, keyword=keyword)
        return self.namespace_edge_cache[iri]


class AnnotationManager(BaseManager):
    """Manages BEL annotations"""

    def __init__(self, *args, **kwargs):
        super(AnnotationManager, self).__init__(*args, **kwargs)

        #: A dictionary from {annotation URL: {name: label}}
        self.annotation_cache = defaultdict(dict)
        #: A dictionary from {annotation URL: {name: database ID}}
        self.annotation_id_cache = defaultdict(dict)
        #: A dictionary from {annotation URL: Annotation}
        self.annotation_model = {}

        #: A dictionary from {annotation URL: {name: AnnotationEntry}}
        self.annotation_object_cache = defaultdict(dict)

        #: A dictionary from {annotation URL: set of (parent, child) tuples}
        self.annotation_edge_cache = {}

    def list_annotations(self):
        """Return a list of all annotations

        :rtype: list[Annotation]
        """
        return self.session.query(Annotation).all()

    def drop_annotations(self):
        """Drops all annotations"""

        self.annotation_cache.clear()
        self.annotation_id_cache.clear()
        self.annotation_object_cache.clear()
        self.annotation_model.clear()
        self.annotation_edge_cache.clear()

        for annotation in self.session.query(AnnotationEntry).all():
            annotation.children[:] = []
            self.session.commit()

        self.session.query(AnnotationEntry).delete()
        self.session.query(Annotation).delete()
        self.session.commit()

    def insert_annotation(self, url):
        """Inserts the namespace file at the given location to the cache

        :param str url: the location of the namespace file
        :return: SQL Alchemy model instance, populated with data from URL
        :rtype: Annotation
        """
        log.info('inserting annotation %s', url)

        config = get_bel_resource(url)

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

        annotation = Annotation(**annotation_insert_values)
        annotation.entries = [AnnotationEntry(name=c, label=l) for c, l in config['Values'].items() if c]

        self.session.add(annotation)
        self.session.commit()

        return annotation

    def ensure_annotation(self, url, cache_objects=False):
        """Caches an annotation file if not already in the cache

        :param str url: the location of the annotation file
        :param bool cache_objects: Indicates if the object_cache should be filed with :class:`AnnotationEntry` objects.
        :return: The ensured annotation instance
        :rtype: Annotation
        """
        if url in self.annotation_model:
            log.debug('already in memory: %s (%d)', url, len(self.annotation_cache[url]))
            results = self.annotation_model[url]

        else:
            t = time.time()
            results = self.session.query(Annotation).filter(Annotation.url == url).one_or_none()

            if results is None:
                results = self.insert_annotation(url)
            else:
                log.debug('loaded annotation: %s (%d, %.2fs)', url, len(results.entries), time.time() - t)

            self.annotation_model[url] = results

            for entry in results.entries:
                self.annotation_cache[url][entry.name] = entry.label
                self.annotation_id_cache[url][entry.name] = entry.id

        if cache_objects and url not in self.annotation_object_cache:
            log.debug('caching annotation objects: %s (%d)', url, len(self.annotation_cache[url]))
            self.annotation_object_cache[url] = {
                entry.name: entry
                for entry in results.entries
            }

        return results

    # TODO merge get_annotation and ensure_annotation
    def get_annotation(self, url):
        """Returns a dict of annotations and their labels for the given annotation file

        :param str url: the location of the annotation file
        """
        self.ensure_annotation(url)
        return self.annotation_cache[url]

    def get_annotation_by_url(self, url):
        """Gets an annotation by URL

        :param str url:
        :rtype: Annotation
        """
        return self.session.query(Annotation).filter(Annotation.url == url).one_or_none()

    def get_annotation_entry(self, url, value):
        """Gets a given AnnotationEntry object.

        :param str url: The url of the annotation source
        :param str value: The name of the annotation entry from the given url's document
        :rtype: AnnotationEntry
        """
        if self.annotation_object_cache:
            annotation_entry = self.annotation_object_cache[url][value]
        else:
            annotation = self.session.query(Annotation).filter(Annotation.url == url).one()
            annotation_entry = self.session.query(AnnotationEntry).filter_by(annotation=annotation, name=value).one()

        return annotation_entry


class OwlAnnotationManager(AnnotationManager):
    """Manages OWL annotations"""

    def insert_annotation_owl(self, iri, keyword=None):
        """Caches an ontology as a namespace from the given IRI

        :param str iri: the location of the ontology
        """
        log.info('inserting owl %s', iri)

        annotation = Annotation(url=iri, keyword=keyword)

        graph = parse_owl(iri)

        entries = {
            node: AnnotationEntry(name=node, annotation=annotation)  # TODO add label
            for node in graph.nodes_iter()
        }
        annotation.entries = list(entries.values())

        for u, v in graph.edges_iter():
            entries[u].children.append(entries[v])

        self.session.add(annotation)
        self.session.commit()

        return annotation

    def ensure_annotation_owl(self, iri, keyword=None):
        """Caches an ontology as an annotation from the given IRI

        :param str iri: the location of the ontology
        """
        if iri in self.annotation_cache:
            return

        results = self.session.query(Annotation).filter(Annotation.url == iri).one_or_none()
        if results is None:
            results = self.insert_annotation_owl(iri, keyword)

        for entry in results.entries:
            self.annotation_cache[iri][entry.name] = entry.label
            self.annotation_id_cache[iri][entry.name] = entry.id

        self.annotation_edge_cache[iri] = {
            (sub.name, sup.name)
            for sub in results.entries for sup in sub.children
        }

        return results

    def get_annotation_owl_terms(self, iri, keyword=None):
        """Gets a set of classes and individuals in the ontology at the given IRI

        :param str iri: the location of the ontology
        """
        self.ensure_annotation_owl(iri, keyword)
        return self.annotation_cache[iri]

    def get_annotation_owl_edges(self, iri, keyword=None):
        """Gets a set of directed edge pairs from the graph representing the ontology at the given IRI

        :param str iri: the location of the ontology
        """
        self.ensure_annotation_owl(iri, keyword=keyword)
        return self.annotation_edge_cache[iri]


class EquivalenceManager(NamespaceManager):
    """Manages BEL equivalences"""

    def drop_equivalences(self):
        """Drops all equivalence classes"""
        self.session.query(NamespaceEntryEquivalence).delete()
        self.session.commit()

    def ensure_equivalence_class(self, label):
        """Ensures the equivalence class is loaded in the database"""
        result = self.session.query(NamespaceEntryEquivalence).filter_by(label=label).one_or_none()

        if result is None:
            result = NamespaceEntryEquivalence(label=label)
            self.session.add(result)
            self.session.commit()

        return result

    def insert_equivalences(self, url, namespace_url):
        """Given a url to a .beleq file and its accompanying namespace url, populate the database"""
        self.ensure_namespace(namespace_url)

        log.info('inserting equivalences: %s', url)

        config = get_bel_resource(url)
        values = config['Values']

        ns = self.session.query(Namespace).filter(Namespace.url == namespace_url).one()

        for entry in ns.entries:
            equivalence_label = values[entry.name]
            entry.equivalence = self.ensure_equivalence_class(equivalence_label)

        ns.has_equivalences = True

        self.session.commit()

    def ensure_equivalences(self, url, namespace_url):
        """Check if the equivalence file is already loaded, and if not, load it"""
        self.ensure_namespace(namespace_url)

        ns = self.get_namespace_by_url(namespace_url)

        if not ns.has_equivalences:
            self.insert_equivalences(url, namespace_url)

    def get_equivalence_by_entry(self, url, name):
        """Gets the equivalence class

        :param str url: the URL of the namespace
        :param str name: the name of the entry in the namespace
        :return: the equivalence class of the entry in the given namespace
        """
        namespace = self.get_namespace_by_url(url)
        entry = self.session.query(NamespaceEntry).filter(NamespaceEntry.namespace_id == namespace.id,
                                                          NamespaceEntry.name == name).one()
        return entry.equivalence

    def get_equivalence_members(self, equivalence_class):
        """Gets all members of the given equivalence class

        :param equivalence_class: the label of the equivalence class. example: '0b20937b-5eb4-4c04-8033-63b981decce7'
                                    for Alzheimer's Disease
        :return: a list of members of the class
        """
        eq = self.session.query(NamespaceEntryEquivalence).filter_by(label=equivalence_class).one()
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

    def list_recent_networks(self):
        """Lists the most recently uploaded version of each network

        :rtype: list[Network]
        """
        return self.session.query(Network).group_by(Network.name).having(func.max(Network.created)).order_by(
            Network.created.desc()).all()

    def has_name_version(self, name, version):
        """Checks if the name/version combination is already in the database

        :param str name: The network name
        :param str version: The network version
        :rtype: bool
        """
        return self.session.query(exists().where(Network.name == name, Network.version == version)).scalar()

    def drop_network_by_id(self, network_id):
        """Drops a network by its database identifier

        :param int network_id: The network's database identifier
        """
        network = self.session.query(Network).get(network_id)
        self.session.delete(network)
        self.session.commit()

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
        :return: A BEL graph
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
        """Gets a network from the database by its identifier and converts to a BEL graph

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
        :rtype: pybel.BELGraph
        """
        if len(network_ids) == 1:
            return self.get_graph_by_id(network_ids[0])

        return union(self.get_graphs_by_ids(network_ids))

    def insert_graph(self, graph, store_parts=False):
        """Inserts a graph in the database.

        :param BELGraph graph: A BEL graph
        :param bool store_parts: Should the graph be stored in the edge store?
        :return: A Network object
        :rtype: Network
        """
        if not graph.name:
            raise ValueError('Can not upload a graph without a name')

        if not graph.version:
            raise ValueError('Can not upload a graph without a version')

        log.debug('inserting %s v%s', graph.name, graph.version)

        t = time.time()

        for url in graph.namespace_url.values():
            self.ensure_namespace(url, cache_objects=store_parts)

        for url in graph.annotation_url.values():
            self.ensure_annotation(url, cache_objects=store_parts)

        network = Network(blob=to_bytes(graph), **{
            key: value
            for key, value in graph.document.items()
            if key in METADATA_INSERT_KEYS
        })

        if store_parts:
            self._store_graph_parts(network, graph)

        self.session.add(network)
        self.session.commit()

        log.info('inserted %s v%s in %.2fs', graph.name, graph.version, time.time() - t)

        return network

    def _store_graph_parts(self, network, graph):
        """Stores graph parts. Needs to be overridden."""
        raise NotImplementedError


class InsertManager(NamespaceManager, AnnotationManager):
    """Manages inserting data into the edge store"""

    def __init__(self, *args, **kwargs):
        super(InsertManager, self).__init__(*args, **kwargs)

        #: A dictionary that maps node tuples to their models
        self.node_model = {}

        # A set of dictionaries that contains objects of the type described by the key
        self.object_cache_modification = {}
        self.object_cache_property = {}
        self.object_cache_node = {}
        self.object_cache_edge = {}
        self.object_cache_citation = {}
        self.object_cache_evidence = {}
        self.object_cache_author = {}

    @staticmethod
    def _map_annotations_dict(graph, data):
        for key, value in data.items():
            if key in graph.annotation_url:
                url = graph.annotation_url[key]
            elif key in graph.annotation_owl:
                url = graph.annotation_owl[key]
            else:
                raise ValueError('Graph resources does not contain keyword: {}'.format(key))
            yield url, value

    def get_annotations(self, graph, data):
        return [
            self.get_annotation_entry(url, value)
            for url, value in self._map_annotations_dict(graph, data)
        ]

    def _add_qualified_edge(self, network, graph, u, v, k, data):
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
        annotations = self.get_annotations(graph, data[ANNOTATIONS])

        bel = edge_to_bel(graph, u, v, k)
        edge_hash = hash_edge(u, v, k, data)
        edge = self.get_or_create_edge(
            source=self.node_model[u],
            target=self.node_model[v],
            relation=data[RELATION],
            bel=bel,
            blob=dumps(data),
            edge_hash=edge_hash,
            evidence=evidence,
            properties=properties,
            annotations=annotations,
        )
        network.edges.append(edge)

    def _add_unqualified_edge(self, network, graph, u, v, k, data):
        bel = edge_to_bel(graph, u, v, k)
        edge_hash = hash_edge(u, v, k, data)
        edge = self.get_or_create_edge(
            source=self.node_model[u],
            target=self.node_model[v],
            relation=data[RELATION],
            bel=bel,
            blob=dumps(data),
            edge_hash=edge_hash,
        )
        network.edges.append(edge)

    def _store_graph_parts(self, network, graph):
        """Stores the given graph into the edge store.

        :param Network network: A SQLAlchemy PyBEL Network object
        :param BELGraph graph: A BEL Graph
        """
        self.ensure_namespace(GOCC_LATEST, cache_objects=True)

        for node in graph.nodes_iter():
            try:
                node_object = self.get_or_create_node(graph, node)
                self.node_model[node] = node_object
            except:
                continue

            if node_object not in network.nodes:  # FIXME when would the network ever have nodes in it already?
                network.nodes.append(node_object)

        self.session.flush()

        for u, v, k, data in graph.edges_iter(data=True, keys=True):
            if u not in self.node_model:
                log.debug('Skipping uncached node: %s', u)
                continue

            if v not in self.node_model:
                log.debug('Skipping uncached node: %s', v)
                continue

            if RELATION not in data:
                continue

            if data[RELATION] in UNQUALIFIED_EDGES:
                self._add_unqualified_edge(network, graph, u, v, k, data)

            elif EVIDENCE not in data or CITATION not in data:
                continue

            elif CITATION_TYPE not in data[CITATION] or CITATION_REFERENCE not in data[CITATION]:
                continue

            else:
                self._add_qualified_edge(network, graph, u, v, k, data)

        self.session.flush()

    def get_or_create_evidence(self, citation, text):
        """Creates entry and object for given evidence if it does not exist.

        :param Citation citation: Citation object obtained from :func:`get_or_create_citation`
        :param str text: Evidence text
        :rtype: Evidence
        """
        evidence_hash = hash_evidence(text, citation.type, citation.reference)

        if evidence_hash in self.object_cache_evidence:
            return self.object_cache_evidence[evidence_hash]

        result = self.session.query(Evidence).filter(Evidence.sha512 == evidence_hash).one_or_none()

        if result is not None:
            self.object_cache_evidence[evidence_hash] = result
            return result

        result = Evidence(
            text=text,
            citation=citation,
            sha512=evidence_hash
        )

        self.session.add(result)
        self.object_cache_evidence[evidence_hash] = result
        return result

    def get_or_create_node(self, graph, node):
        """Creates entry and object for given node if it does not exist.

        :param BELGraph graph: A BEL graph
        :param tuple node: A BEL node
        :rtype: Node
        """
        node_hash = hash_node(node)
        if node_hash in self.object_cache_node:
            return self.object_cache_node[node_hash]

        bel = node_to_bel(graph, node)
        blob = dumps(graph.node[node])
        node_data = graph.node[node]

        result = self.session.query(Node).filter(Node.sha512 == node_hash).one_or_none()

        if result is not None:
            self.object_cache_node[node_hash] = result
            return result

        type = node_data[FUNCTION]

        result = Node(type=type, bel=bel, blob=blob, sha512=node_hash)

        if NAMESPACE not in node_data:
            pass

        elif node_data[NAMESPACE] in graph.namespace_url:
            namespace = node_data[NAMESPACE]
            url = graph.namespace_url[namespace]
            result.namespace_entry = self.get_namespace_entry(url, node_data[NAME])

        elif node_data[NAMESPACE] in graph.namespace_pattern:
            result.namespace_pattern = graph.namespace_pattern[node_data[NAMESPACE]]

        else:
            raise ValueError("No reference in BELGraph for namespace: {}".format(node_data[NAMESPACE]))

        if VARIANTS in node_data or FUSION in node_data:
            result.is_variant = True
            result.fusion = FUSION in node_data
            result.modifications = self.get_or_create_modification(graph, node_data)

        self.session.add(result)
        self.object_cache_node[node_hash] = result
        return result

    def drop_nodes(self):
        """Drops all nodes in RDB"""
        for node in self.session.query(Node).all():
            self.session.delete(node)
        self.session.commit()

    def drop_edges(self):
        """Drops all edges in RDB"""
        for edge in self.session.query(Edge).all():
            self.session.delete(edge)
        self.session.commit()

    def get_or_create_edge(self, source, target, relation, bel, blob, edge_hash, evidence=None, annotations=None,
                           properties=None):
        """Creates entry for given edge if it does not exist.

        :param Node source: Source node of the relation
        :param Node target: Target node of the relation
        :param str relation: Type of the relation between source and target node
        :param str bel: BEL statement that describes the relation
        :param bytes blob: A blob of the edge data object.
        :param str edge_hash: A hash of the edge
        :param Evidence evidence: Evidence object that proves the given relation
        :param list[Property] properties: List of all properties that belong to the edge
        :param list[AnnotationEntry] annotations: List of all annotations that belong to the edge
        :rtype: Edge
        """
        if edge_hash in self.object_cache_edge:
            return self.object_cache_edge[edge_hash]

        result = self.session.query(Edge).filter(Edge.sha512 == edge_hash).one_or_none()

        if result is not None:
            self.object_cache_edge[edge_hash] = result
            return result

        result = Edge(
            source=source,
            target=target,
            relation=relation,
            bel=bel,
            blob=blob,
            sha512=edge_hash,
        )
        if evidence is not None:
            result.evidence = evidence
        if properties is not None:
            result.properties = properties
        if annotations is not None:
            result.annotations = annotations

        self.session.add(result)
        self.object_cache_edge[edge_hash] = result
        return result

    def get_or_create_citation(self, type, reference, name=None, title=None, volume=None, issue=None, pages=None,
                               date=None, first=None, last=None, authors=None):
        """Creates entry for given citation if it does not exist.

        :param str type: Citation type (e.g. PubMed)
        :param str reference: Identifier of the given citation (e.g. PubMed id)
        :param str name: Title of the publication that is cited
        :param str date: Date of publication in ISO 8601 (YYYY-MM-DD) format
        :param str or list[str] authors: Either a list of authors separated by |, or an actual list of authors
        :rtype: Citation
        """
        type = type.strip()
        reference = reference.strip()

        citation_hash = hash_citation(type, reference)

        if citation_hash in self.object_cache_citation:
            return self.object_cache_citation[citation_hash]

        result = self.session.query(Citation).filter(Citation.sha512 == citation_hash).one_or_none()

        if result is not None:
            self.object_cache_citation[citation_hash] = result
            return result

        result = Citation(
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
            result.date = parse_datetime(date)

        if first is not None:
            result.first = self.get_or_create_author(first)

        if last is not None:
            result.last = self.get_or_create_author(last)

        if authors is not None:
            for author in (authors.split('|') if isinstance(authors, string_types) else authors):
                author_model = self.get_or_create_author(author)
                if author_model not in result.authors:
                    result.authors.append(author_model)

        self.session.add(result)
        self.object_cache_citation[citation_hash] = result
        return result

    def get_or_create_author(self, name):
        """Gets an author by name, or creates one

        :param str name: An author's name
        :rtype: Author
        """
        name = name.strip()

        if name in self.object_cache_author:
            return self.object_cache_author[name]

        result = self.session.query(Author).filter(Author.name == name).one_or_none()

        if result is not None:
            self.object_cache_author[name] = result
            return result

        result = Author(name=name)
        self.session.add(result)
        self.object_cache_author[name] = result
        return result

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
            p3_namespace_entry = self.get_namespace_entry(p3_namespace_url, node_data[PARTNER_3P][NAME])

            p5_namespace_url = graph.namespace_url[node_data[PARTNER_5P][NAMESPACE]]
            p5_namespace_entry = self.get_namespace_entry(p5_namespace_url, node_data[PARTNER_5P][NAME])

            fusion_dict = {
                'modType': mod_type,
                'p3Partner': p3_namespace_entry,
                'p5Partner': p5_namespace_entry,
            }

            if FUSION_MISSING in node_data[RANGE_3P]:
                fusion_dict.update({
                    'p3Missing': node_data[RANGE_3P][FUSION_MISSING].strip()
                })
            else:
                fusion_dict.update({
                    'p3Reference': node_data[RANGE_3P][FUSION_REFERENCE].strip(),
                    'p3Start': node_data[RANGE_3P][FUSION_START],
                    'p3Stop': node_data[RANGE_3P][FUSION_STOP],
                })

            if FUSION_MISSING in node_data[RANGE_5P]:
                fusion_dict.update({
                    'p5Missing': node_data[RANGE_5P][FUSION_MISSING].strip()
                })
            else:
                fusion_dict.update({
                    'p5Reference': node_data[RANGE_5P][FUSION_REFERENCE].strip(),
                    'p5Start': node_data[RANGE_5P][FUSION_START],
                    'p5Stop': node_data[RANGE_5P][FUSION_STOP],
                })

            modification_list.append(fusion_dict)

        else:
            for variant in node_data[VARIANTS]:
                mod_type = variant[KIND].strip()
                if mod_type == HGVS:
                    modification_list.append({
                        'modType': mod_type,
                        'variantString': variant[IDENTIFIER].strip()
                    })

                elif mod_type == FRAGMENT:
                    if FRAGMENT_MISSING in variant:
                        modification_list.append({
                            'modType': mod_type,
                            'p3Missing': variant[FRAGMENT_MISSING].strip()
                        })
                    else:
                        modification_list.append({
                            'modType': mod_type,
                            'p3Start': variant[FRAGMENT_START],
                            'p3Stop': variant[FRAGMENT_STOP]
                        })

                elif mod_type == GMOD:
                    modification_list.append({
                        'modType': mod_type,
                        'modNamespace': variant[IDENTIFIER][NAMESPACE].strip(),
                        'modName': variant[IDENTIFIER][NAME].strip()
                    })

                elif mod_type == PMOD:
                    modification_list.append({
                        'modType': mod_type,
                        'modNamespace': variant[IDENTIFIER][NAMESPACE].strip(),
                        'modName': variant[IDENTIFIER][NAME].strip(),
                        'aminoA': variant[PMOD_CODE].strip() if PMOD_CODE in variant else None,
                        'position': variant[PMOD_POSITION] if PMOD_POSITION in variant else None
                    })

        modifications = []
        for modification in modification_list:
            mod_hash = hash_dump(modification)

            if mod_hash in self.object_cache_modification:
                mod = self.object_cache_modification[mod_hash]

            else:
                mod = self.session.query(Modification).filter(Modification.sha512 == mod_hash).one_or_none()
                if not mod:
                    modification['sha512'] = mod_hash
                    mod = Modification(**modification)

                self.object_cache_modification[mod_hash] = mod
            modifications.append(mod)

        return modifications

    def get_or_create_properties(self, graph, edge_data):
        """Creates a list of all subject and object related properties of the edge.

        :param pybel.BELGraph graph: A BEL graph
        :param dict edge_data: Describes the context of the given edge.
        :return: A list of all subject and object properties of the edge
        :rtype: list[Property]
        """
        properties = []
        property_list = []
        for participant in (SUBJECT, OBJECT):
            if participant not in edge_data:
                continue

            participant_data = edge_data[participant]
            modifier = participant_data[MODIFIER] if MODIFIER in participant_data else LOCATION
            property_dict = {
                'participant': participant,
                'modifier': modifier
            }

            if modifier == TRANSLOCATION and EFFECT in participant_data:
                for effect_type, effect_value in participant_data[EFFECT].items():
                    tmp_dict = deepcopy(property_dict)
                    tmp_dict['relativeKey'] = effect_type
                    if NAMESPACE in effect_value:
                        if effect_value[NAMESPACE] == GOCC_KEYWORD and GOCC_KEYWORD not in graph.namespace_url:
                            namespace_url = GOCC_LATEST
                        else:
                            namespace_url = graph.namespace_url[effect_value[NAMESPACE]]
                        tmp_dict['namespaceEntry'] = self.get_namespace_entry(namespace_url, effect_value[NAME])
                    else:
                        tmp_dict['propValue'] = effect_value

                    property_list.append(tmp_dict)

            elif modifier == ACTIVITY and EFFECT in participant_data:
                property_dict['effectNamespace'] = participant_data[EFFECT][NAMESPACE]
                property_dict['effectName'] = participant_data[EFFECT][NAME]

                property_list.append(property_dict)

            elif modifier == LOCATION:
                if participant_data[LOCATION][NAMESPACE] == GOCC_KEYWORD and GOCC_KEYWORD not in graph.namespace_url:
                    namespace_url = GOCC_LATEST
                else:
                    namespace_url = graph.namespace_url[participant_data[LOCATION][NAMESPACE]]
                property_dict['namespaceEntry'] = self.get_namespace_entry(namespace_url,
                                                                           participant_data[LOCATION][NAME])
                property_list.append(property_dict)

            else:
                property_list.append(property_dict)

        for property_def in property_list:
            property_hash = hash_dump(property_def)

            if property_hash in self.object_cache_property:
                edge_property = self.object_cache_property[property_hash]
            else:
                edge_property = self.session.query(Property).filter(Property.sha512 == property_hash).one_or_none()

                if not edge_property:
                    property_def['sha512'] = property_hash
                    edge_property = Property(**property_def)

                self.object_cache_property[property_hash] = edge_property

            properties.append(edge_property)

        return properties


class Manager(QueryManager, InsertManager, NetworkManager, EquivalenceManager, OwlNamespaceManager,
              OwlAnnotationManager):
    """The definition cache manager takes care of storing BEL namespace and annotation files for later use. It uses
    SQLite by default for speed and lightness, but any database can be used with its SQLAlchemy interface.
    """

    @staticmethod
    def ensure(connection=None, **kwargs):
        """A convenience method for turning a string into a connection, or passing a :class:`Manager` through.

        :param connection: An RFC-1738 database connection string, a pre-built :class:`Manager`, or ``None``
                            for default connection
        :type connection: None or str or Manager
        :param kwargs: Keyword arguments to pass to the constructor of :class:`Manager`
        :rtype: Manager
        """
        if isinstance(connection, Manager):
            return connection
        return Manager(connection=connection, **kwargs)
