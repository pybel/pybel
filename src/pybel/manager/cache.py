# -*- coding: utf-8 -*-

"""
Definition Cache Manager
------------------------
Under the hood, PyBEL caches namespace and annotation files for quick recall on later use. The user doesn't need to
enable this option, but can specify a database location if they choose.
"""

import datetime
import json
import logging
import time

import hashlib
from collections import defaultdict
from copy import deepcopy
from six import string_types
from sqlalchemy import func

from .base_cache import BaseCacheManager
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
from .utils import parse_owl, extract_shared_required, extract_shared_optional
from ..canonicalize import decanonicalize_edge, decanonicalize_node
from ..constants import *
from ..io.gpickle import to_bytes
from ..struct import BELGraph, union
from ..utils import get_bel_resource, parse_datetime, subdict_matches, hash_edge, hash_node

try:
    import cPickle as pickle
except ImportError:
    import pickle

__all__ = [
    'CacheManager',
    'build_manager',
]

log = logging.getLogger(__name__)

DEFAULT_BELNS_ENCODING = ''.join(sorted(belns_encodings))


def build_manager(connection=None, echo=False):
    """A convenience method for turning a string into a connection, or passing a :class:`CacheManager` through.
    
    :param connection: An RFC-1738 database connection string, a pre-built :class:`CacheManager`, or ``None`` 
                        for default connection
    :type connection: None or str or CacheManager
    :type echo: bool
    :return: A cache manager
    :rtype: CacheManager
    """
    if isinstance(connection, CacheManager):
        return connection
    return CacheManager(connection=connection, echo=echo)


class NamespaceManager(BaseCacheManager):
    """Manages namespace database"""

    def __init__(self, connection=None, echo=False):
        super(NamespaceManager, self).__init__(connection=connection, echo=echo)

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
        """Returns a list of all namespace keyword/url pairs"""
        return list(self.session.query(Namespace.keyword, Namespace.version, Namespace.url).all())

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
        log.info('inserting namespace %s', url)

        bel_resource = get_bel_resource(url)

        values = {c: e if e else DEFAULT_BELNS_ENCODING for c, e in bel_resource['Values'].items() if c}

        if bel_resource['Processing']['CacheableFlag'] not in {'yes', 'Yes', 'True', 'true'}:
            return values

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
            results = self.namespace_model[url]

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
                self.namespace_cache[url][entry.name] = list(entry.encoding)  # set()
                self.namespace_id_cache[url][entry.name] = entry.id

        if cache_objects and url not in self.namespace_object_cache:
            log.debug('loading namespace cache_objects: %s (%d)', url, len(self.namespace_cache[url]))
            for entry in results.entries:
                self.namespace_object_cache[url][entry.name] = entry

        return results

    def get_namespace(self, url):
        """Returns a dict of names and their encodings for the given namespace URL.

        :param url: the location of the namespace file
        :type url: str
        """
        result = self.ensure_namespace(url)

        if isinstance(result, dict):
            return result
        else:
            # self.ensure_namespace makes sure it's in the cache if its not cachable
            return self.namespace_cache[url]

    def get_namespace_entry(self, url, value):
        """Gets a given NamespaceEntry object.

        :param str url: The url of the namespace source
        :param str value: The value of the namespace from the given url's document
        :return: An NamespaceEntry object
        :rtype: NamespaceEntry
        """
        if self.namespace_object_cache:
            namespace_entry = self.namespace_object_cache[url][value]
        else:
            namespace = self.session.query(Namespace).filter_by(url=url).one()

            # FIXME @kono reinvestigate this
            try:
                namespace_entry = self.session.query(NamespaceEntry). \
                    filter_by(namespace=namespace, name=value).one_or_none()
            except:
                namespace_entry = self.session.query(NamespaceEntry). \
                    filter_by(namespace=namespace, name=value).first()

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


class AnnotationManager(BaseCacheManager):
    """Manages database annotations"""

    def __init__(self, connection=None, echo=False):
        super(AnnotationManager, self).__init__(connection=connection, echo=echo)

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

    def ensure_annotation(self, url, objects=False):
        """Caches an annotation file if not already in the cache

        :param str url: the location of the annotation file
        :param bool objects: Indicates if the object_cache should be filed with NamespaceEntry objects.
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

        if objects and url not in self.annotation_object_cache:
            log.debug('loading annotation objects: %s (%d)', url, len(self.annotation_cache[url]))
            for entry in results.entries:
                self.annotation_object_cache[url][entry.name] = entry

        return results

    def get_annotation(self, url):
        """Returns a dict of annotations and their labels for the given annotation file

        :param str url: the location of the annotation file
        """
        self.ensure_annotation(url)
        return self.annotation_cache[url]

    def get_annotation_entry(self, url, value):
        """Gets a given AnnotationEntry object.

        :param str url: The url of the annotation source
        :param str value: The value of the annotation from the given url's document
        :return: An AnnotationEntry object
        :rtype: AnnotationEntry
        """
        if self.annotation_object_cache:
            annotation_entry = self.annotation_object_cache[url][value]
        else:
            annotation = self.session.query(Annotation).filter_by(url=url).one()
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
    """Manages database equivalences"""

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

        ns = self.session.query(Namespace).filter_by(url=namespace_url).one()

        for entry in ns.entries:
            equivalence_label = values[entry.name]
            entry.equivalence = self.ensure_equivalence_class(equivalence_label)

        ns.has_equivalences = True

        self.session.commit()

    def ensure_equivalences(self, url, namespace_url):
        """Check if the equivalence file is already loaded, and if not, load it"""
        self.ensure_namespace(namespace_url)

        ns = self.session.query(Namespace).filter_by(url=namespace_url).one()

        if not ns.has_equivalences:
            self.insert_equivalences(url, namespace_url)

    def get_equivalence_by_entry(self, url, name):
        """Gets the equivalence class

        :param str url: the URL of the namespace
        :param str name: the name of the entry in the namespace
        :return: the equivalence class of the entry in the given namespace
        """
        namespace = self.session.query(Namespace).filter_by(url=url).one()
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
    """Manages database networks"""

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
        return {x for x, in self.session.query(Network.version).filter(Network.name == name).all()}

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

    def get_network_by_id(self, network_id):
        """Gets a network from the database by its identifier.

        :param int network_id: The network's database identifier
        :return: A Network object
        :rtype: Network
        """
        return self.session.query(Network).get(network_id)

    def get_networks_by_ids(self, network_ids):
        """Gets a list of networks with the given identifiers. Note: order is not necessarily preserved.

        :param iter[int] network_ids: The identifiers of networks in the database
        :rtype: list[Network]
        """
        return self.session.query(Network).filter(Network.id.in_(network_ids)).all()

    def get_network_by_ids(self, network_ids):
        """Gets a networks by a list of database identifiers

        :param list[int] network_ids: A network identifier or list of network identifiers
        :rtype: pybel.BELGraph
        """
        if len(network_ids) == 1:
            return self.get_network_by_id(network_ids[0]).as_bel()

        return union(
            network.as_bel()
            for network in self.get_networks_by_ids(network_ids)
        )

    def insert_graph(self, graph, store_parts=False):
        """Inserts a graph in the database.

        :param BELGraph graph: A BEL graph
        :param bool store_parts: Should the graph be stored in the edge store?
        :return: A Network object
        :rtype: Network
        """
        log.debug('inserting %s v%s', graph.name, graph.version)

        t = time.time()

        for url in graph.namespace_url.values():
            self.ensure_namespace(url, cache_objects=store_parts)

        for url in graph.annotation_url.values():
            self.ensure_annotation(url, objects=store_parts)

        network = Network(blob=to_bytes(graph), **{
            key:value
            for key, value in graph.document.items()
            if key in METADATA_INSERT_KEYS
        })

        if store_parts:
            if not self.session.query(Namespace).filter_by(keyword=GOCC_KEYWORD).first():
                self.ensure_namespace(GOCC_LATEST)

            self.store_graph_parts(network, graph)

        self.session.add(network)
        self.session.commit()

        log.info('inserted %s v%s in %.2fs', graph.name, graph.version, time.time() - t)

        return network

    def store_graph_parts(self, network, graph):
        """Stores graph parts. Needs to be overridden."""
        raise NotImplementedError


class EdgeStoreInsertManager(NamespaceManager, AnnotationManager):
    """Manages the edge store"""

    def __init__(self, *args, **kwargs):
        super(EdgeStoreInsertManager, self).__init__(*args, **kwargs)

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

    def store_graph_parts(self, network, graph):
        """Stores the given graph into the edge store.

        :param Network network: A SQLAlchemy PyBEL Network object
        :param BELGraph graph: A BEL Graph
        """
        for node in graph.nodes_iter():
            if node in self.node_model:
                node_object = self.node_model[node]
            else:
                node_object = self.get_or_create_node(graph, node)
                self.node_model[node] = node_object

            if node_object not in network.nodes:  # FIXME when would the network ever have nodes in it already?
                network.nodes.append(node_object)

        self.session.flush()

        for u, v, k, data in graph.edges_iter(data=True, keys=True):

            if CITATION not in data or EVIDENCE not in data:
                evidence = None
            else:

                citation_dict = data[CITATION]

                citation = self.get_or_create_citation(
                    type=citation_dict.get(CITATION_TYPE),
                    name=citation_dict.get(CITATION_NAME),
                    reference=citation_dict.get(CITATION_REFERENCE),
                    date=citation_dict.get(CITATION_DATE),
                    authors=citation_dict.get(CITATION_AUTHORS),
                )
                evidence = self.get_or_create_evidence(citation, data[EVIDENCE])

            properties = self.get_or_create_property(graph, data)
            annotations = [
                self.annotation_object_cache[graph.annotation_url[key]][value]
                for key, value in data[ANNOTATIONS].items()
                if key in graph.annotation_url
            ]

            bel = decanonicalize_edge(graph, u, v, k)

            edge_hash = hash_edge(u, v, k, data)

            edge = self.get_or_create_edge(
                source=self.node_model[u],
                target=self.node_model[v],
                relation=data[RELATION],
                evidence=evidence,
                bel=bel,
                properties=properties,
                annotations=annotations,
                blob=pickle.dumps(data),
                edge_hash=edge_hash,
            )

            network.edges.append(edge)

        self.session.flush()

    def get_or_create_evidence(self, citation, text):
        """Creates entry and object for given evidence if it does not exist.

        :param Citation citation: Citation object obtained from :func:`get_or_create_citation`
        :param str text: Evidence text
        :return: An Evidence object
        :rtype: Evidence
        """
        evidence_hash = hashlib.sha512(
            json.dumps({EVIDENCE: text, CITATION: citation}, sort_keys=True).encode('utf-8')).hexdigest()
        if evidence_hash in self.object_cache_evidence:
            return self.object_cache_evidence[evidence_hash]

        result = self.session.query(Evidence).filter_by(text=text, citation=citation).one_or_none()
        if result is None:
            result = Evidence(text=text, citation=citation, sha512=evidence_hash)
            self.session.add(result)

        self.object_cache_evidence[evidence_hash] = result

        return result

    def get_or_create_node(self, graph, node):
        """Creates entry and object for given node if it does not exist.

        :param BELGraph graph: A BEL graph
        :param tuple node: A BEL node
        :return: A Node object
        :rtype: Node
        """
        node_hash = hash_node(node)
        if node_hash in self.object_cache_node:
            return self.object_cache_node[node_hash]

        bel = decanonicalize_node(graph, node)
        blob = pickle.dumps(graph.node[node])
        node_data = graph.node[node]

        result = self.session.query(Node).filter_by(sha512=node_hash).one_or_none()

        if result is None:
            type = node_data[FUNCTION]

            if NAMESPACE in node_data and node_data[NAMESPACE] in graph.namespace_url:
                namespace = node_data[NAMESPACE]
                url = graph.namespace_url[namespace]
                namespace_entry = self.get_namespace_entry(url, node_data[NAME])

                result = Node(type=type, namespaceEntry=namespace_entry, bel=bel, blob=blob,
                              sha512=node_hash)

            elif NAMESPACE in node_data and node_data[NAMESPACE] in graph.namespace_pattern:
                namespace_pattern = graph.namespace_pattern[node_data[NAMESPACE]]
                result = Node(type=type, namespacePattern=namespace_pattern, bel=bel, blob=blob,
                              sha512=node_hash)

            else:
                result = Node(type=type, bel=bel, blob=blob, sha512=node_hash)

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

    def get_or_create_edge(self, source, target, evidence, bel, relation, properties, annotations, blob, edge_hash):
        """Creates entry for given edge if it does not exist.

        :param Node source: Source node of the relation
        :param Node target: Target node of the relation
        :param Evidence evidence: Evidence object that proves the given relation
        :param str bel: BEL statement that describes the relation
        :param str relation: Type of the relation between source and target node
        :param list[Property] properties: List of all properties that belong to the edge
        :param list[AnnotationEntry] annotations: List of all annotations that belong to the edge
        :param bytes blob: A blob of the edge data object.
        :return: An Edge object
        :rtype: Edge
        """
        if edge_hash in self.object_cache_edge:
            return self.object_cache_edge[edge_hash]

        # Edge already in DB?
        result = self.session.query(Edge).filter_by(sha512=edge_hash).one_or_none()

        if result is None:
            # Create new edge and add it to db_session
            edge_dict = {
                'source': source,
                'target': target,
                'evidence': evidence,
                'bel': bel,
                'relation': relation,
                'blob': blob,
                'sha512': edge_hash,
            }
            result = Edge(**edge_dict)
            self.session.add(result)

            result.properties = properties
            result.annotations = annotations

        self.object_cache_edge[edge_hash] = result

        return result

    def get_or_create_citation(self, type, name, reference, date=None, authors=None):
        """Creates entry for given citation if it does not exist.

        :param str type: Citation type (e.g. PubMed)
        :param str name: Title of the publication that is cited
        :param str reference: Identifier of the given citation (e.g. PubMed id)
        :param str date: Date of publication in ISO 8601 format
        :param str or list[str] authors: Either a list of authors separated by |, or an actual list of authors
        :return: A Citation object
        :rtype: Citation
        """
        citation_dict = {
            'type': type.strip(),
            'name': name.strip(),
            'reference': reference.strip()
        }
        citation_hash = hashlib.sha512(json.dumps(citation_dict, sort_keys=True).encode('utf-8')).hexdigest()

        if citation_hash in self.object_cache_citation:
            return self.object_cache_citation[citation_hash]

        result = self.session.query(Citation).filter_by(sha512=citation_hash).one_or_none()

        if result is None:
            if date:
                date = parse_datetime(date)
                citation_dict['date'] = date

            citation_dict['sha512'] = citation_hash
            result = Citation(**citation_dict)

            if authors is not None:
                for author in authors.split('|') if isinstance(authors, string_types) else authors:
                    result.authors.append(self.get_or_create_author(author))

            self.session.add(result)

        self.object_cache_citation[citation_hash] = result

        return result

    def get_or_create_author(self, name):
        """Gets an author by name, or creates one

        :param str name: An author's name
        :return: An Author object
        :rtype: Author
        """
        name = name.strip()

        if name in self.object_cache_author:
            return self.object_cache_author[name]

        result = self.session.query(Author).filter_by(name=name).one_or_none()

        if result is None:
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
            mod_hash = hashlib.sha512(json.dumps(modification, sort_keys=True).encode('utf-8')).hexdigest()

            if mod_hash in self.object_cache_modification:
                mod = self.object_cache_modification[mod_hash]

            else:
                mod = self.session.query(Modification).filter_by(sha512=mod_hash).one_or_none()
                if not mod:
                    modification['sha512'] = mod_hash
                    mod = Modification(**modification)

                self.object_cache_modification[mod_hash] = mod
            modifications.append(mod)

        return modifications

    def get_or_create_property(self, graph, edge_data):
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
            property_hash = hashlib.sha512(json.dumps(property_def, sort_keys=True).encode('utf-8')).hexdigest()

            if property_hash in self.object_cache_property:
                edge_property = self.object_cache_property[property_hash]
            else:
                edge_property = self.session.query(Property).filter_by(sha512=property_hash).one_or_none()

                if not edge_property:
                    property_def['sha512'] = property_hash
                    edge_property = Property(**property_def)

                self.object_cache_property[property_hash] = edge_property

            properties.append(edge_property)

        return properties


class EdgeStoreQueryManager(BaseCacheManager):
    """Groups queries over the edge store"""

    def rebuild_by_edge_filter(self, **annotations):
        """Gets all edges matching the given query annotation values

        :param dict[str,str] annotations: dictionary of {key: value}
        :return: A graph composed of the filtered edges
        :rtype: pybel.BELGraph
        """
        graph = BELGraph()
        for annotation_key, annotation_value in annotations.items():

            annotation_def = self.session.query(Annotation).filter_by(keyword=annotation_key).first()
            annotation = self.session.query(AnnotationEntry).filter_by(annotation=annotation_def,
                                                                       name=annotation_value).first()

            # Add Annotations to belGraph.annotation_url
            # Add Namespaces to belGraph.namespace_url
            # What about meta information?
            edges = self.session.query(Edge).filter(Edge.annotations.contains(annotation)).all()
            for edge in edges:
                edge_data = edge.data

                if len(edge_data['source']['key']) == 1:
                    edge_data['source'] = self.help_rebuild_list_components(edge.source)

                if len(edge_data['target']['key']) == 1:
                    edge_data['target'] = self.help_rebuild_list_components(edge.target)

                graph.add_nodes_from((edge_data['source']['node'], edge_data['target']['node']))

                graph.add_edge(
                    edge_data['source']['key'],
                    edge_data['target']['key'],
                    key=(
                        unqualified_edge_code[edge_data['data']['relation']]
                        if edge_data['data']['relation'] in UNQUALIFIED_EDGES
                        else None
                    ),
                    attr_dict=edge_data['data']
                )

        return graph

    def help_rebuild_list_components(self, node):
        """Builds data and identifier for list node objects.

        :param Node node: Node object defined in models
        :return: Dictionary with 'key' and 'node' keys.
        :rtype: dict[str,str]
        """
        node_info = node.data
        key = list(node_info['key'])
        data = node_info['data']
        if node.type in (COMPLEX, COMPOSITE):
            components = self.session.query(Edge).filter_by(source=node, relation=HAS_COMPONENT).all()
            for component in components:
                component_key = component.target.data['key']
                key.append(component_key)

        elif node.type == REACTION:
            reactant_components = self.session.query(Edge).filter_by(source=node, relation=HAS_REACTANT).all()
            product_components = self.session.query(Edge).filter_by(source=node, relation=HAS_PRODUCT).all()
            reactant_keys = tuple(reactant.target.data['key'] for reactant in reactant_components)
            product_keys = tuple(product.target.data['key'] for product in product_components)
            key.append(reactant_keys)
            key.append(product_keys)

        return {'key': tuple(key), 'node': (tuple(key), data)}

    def get_edge_iter_by_filter(self, **annotations):
        """Returns an iterator over Edge object that match the given annotations

        :param dict[str,str] annotations: dictionary of {URL: values}
        :return: An iterator over Edge object that match the given annotations
        :rtype: iter[Edge]
        """
        # TODO make smarter
        for edge in self.session.query(Edge).all():
            ad = {a.annotation.name: a.name for a in edge.annotations}
            if subdict_matches(ad, annotations):
                yield edge

    def get_graph_by_filter(self, **annotations):
        """Fills a BEL graph with edges retrieved from a filter

        :param dict[str,str] annotations: dictionary of {URL: values}
        :return: A BEL graph
        :rtype: pybel.BELGraph
        """
        graph = BELGraph()

        for edge in self.get_edge_iter_by_filter(**annotations):
            if edge.source.id not in graph:
                graph.add_node(edge.source.id, attr_dict=pickle.loads(edge.source.blob))

            if edge.target.id not in graph:
                graph.add_node(edge.target.id, attr_dict=pickle.loads(edge.target.blob))

            graph.add_edge(edge.source.id, edge.target.id, attr_dict=pickle.loads(edge.blob))

        return graph

    def get_node(self, node_id=None, bel=None, type=None, namespace=None, name=None, modification_type=None,
                 modification_name=None, as_dict_list=False):
        """Builds and runs a query over all nodes in the PyBEL cache.

        :param int node_id: The node ID to get
        :param str bel: BEL term that describes the biological entity. e.g. ``p(HGNC:APP)``
        :param str type: Type of the biological entity. e.g. Protein
        :param str namespace: Namespace keyword that is used in BEL. e.g. HGNC
        :param str name: Name of the biological entity. e.g. APP
        :param str modification_name:
        :param str modification_type:
        :param bool as_dict_list: Identifies whether the result should be a list of dictionaries or a list of
                            :class:`Node` objects.
        :return: A list of the fitting nodes as :class:`Node` objects or dicts.
        :rtype: list[Node]
        """
        q = self.session.query(Node)

        if node_id and isinstance(node_id, int):
            q = q.filter_by(id=node_id)
        else:
            if bel:
                q = q.filter(Node.bel.like(bel))

            if type:
                q = q.filter(Node.type.like(type))

            if namespace or name:
                q = q.join(NamespaceEntry)
                if namespace:
                    q = q.join(Namespace).filter(Namespace.keyword.like(namespace))
                if name:
                    q = q.filter(NamespaceEntry.name.like(name))

            if modification_type or modification_name:
                q = q.join(Modification)
                if modification_type:
                    q = q.filter(Modification.modType.like(modification_type))
                if modification_name:
                    q = q.filter(Modification.modName.like(modification_name))

        result = q.all()

        if as_dict_list:
            dict_list = []

            for node in result:
                node_dict = node.data
                node_dict['bel'] = node.bel
                dict_list.append(node_dict)

            return dict_list
        else:
            return result

    def count_nodes(self):
        """Counts the number of nodes in the cache

        :rtype: int
        """
        return self.session.query(func.count(Node.id)).scalar()

    def count_edges(self):
        """Counts the number of edges in the cache

        :rtype: int
        """
        return self.session.query(func.count(Edge.id)).scalar()

    def get_edge(self, edge_id=None, bel=None, source=None, target=None, relation=None, citation=None,
                 evidence=None, annotation=None, property=None, as_dict_list=False):
        """Builds and runs a query over all edges in the PyBEL cache.

        :param int edge_id: The edge identifier
        :param str bel: BEL statement that represents the desired edge.
        :param str or Node source: BEL term of source node e.g. ``p(HGNC:APP)`` or :class:`Node` object.
        :param str or Node target: BEL term of target node e.g. ``p(HGNC:APP)`` or :class:`Node` object.
        :param str relation: The relation that should be present between source and target node.
        :param str or Citation citation: The citation that backs the edge up. It is possible to use the reference_id
                         or a Citation object.
        :param str or Evidence evidence: The supporting text of the edge. It is possible to use a snipplet of the text or a Evidence object.
        :param  dict or str annotation: Dictionary of {annotationKey: annotationValue} parameters or just a annotationValue parameter as string.
        :param property: An edge property object or a corresponding database identifier.
        :param bool as_dict_list: Identifies whether the result should be a list of dictionaries or a list of :class:`Edge` objects.
        """
        q = self.session.query(Edge)

        if edge_id and isinstance(edge_id, int):
            q = q.filter_by(id=edge_id)
        else:
            if bel:
                q = q.filter(Edge.bel.like(bel))

            if relation:
                q = q.filter(Edge.relation.like(relation))

            if annotation:
                q = q.join(AnnotationEntry, Edge.annotations)
                if isinstance(annotation, dict):
                    q = q.join(Annotation).filter(Annotation.keyword.in_(list(annotation.keys())))
                    q = q.filter(AnnotationEntry.name.in_(list(annotation.values())))

                elif isinstance(annotation, str):
                    q = q.filter(AnnotationEntry.name.like(annotation))

            if source:
                if isinstance(source, str):
                    source = self.get_node(bel=source)[0]

                if isinstance(source, Node):
                    q = q.filter(Edge.source == source)

                    # ToDo: in_() not yet supported for relations
                    # elif isinstance(source, list) and len(source) > 0:
                    #    if isinstance(source[0], Node):
                    #        q = q.filter(Edge.source.in_(source))

            if target:
                if isinstance(target, str):
                    target = self.get_node(bel=target)[0]

                if isinstance(target, Node):
                    q = q.filter(Edge.target == target)

                    # elif isinstance(target, list) and len(target) > 0:
                    #    if isinstance(target[0], Node):
                    #        q = q.filter(Edge.source.in_(target))

            if citation or evidence:
                q = q.join(Evidence)

                if citation:
                    if isinstance(citation, Citation):
                        q = q.filter(Evidence.citation == citation)

                    elif isinstance(citation, list) and isinstance(citation[0], Citation):
                        q = q.filter(Evidence.citation.in_(citation))

                    elif isinstance(citation, str):
                        q = q.join(Citation).filter(Citation.reference.like(citation))

                if evidence:
                    if isinstance(evidence, Evidence):
                        q = q.filter(Edge.evidence == evidence)

                    elif isinstance(evidence, str):
                        q = q.filter(Evidence.text.like(evidence))

            if property:
                q = q.join(Property, Edge.properties)

                if isinstance(property, Property):
                    q = q.filter(Property.id == property.id)
                elif isinstance(property, int):
                    q = q.filter(Property.id == property)

        result = q.all()

        if as_dict_list:
            return [edge.data for edge in result]
        else:
            return result

    def get_citation(self, citation_id=None, type=None, reference=None, name=None, author=None, date=None,
                     evidence=False,
                     evidence_text=None, as_dict_list=False):
        """Builds and runs a query over all citations in the PyBEL cache.

        :param str type: Type of the citation. e.g. PubMed
        :param str reference: The identifier used for the citation. e.g. PubMed_ID
        :param str name: Title of the citation.
        :param str or list[str] author: The name or a list of names of authors participated in the citation.
        :param date: Publishing date of the citation.
        :type date: str or datetime.date
        :param bool evidence: Weather or not supporting text should be included in the return.
        :param evidence_text:
        :param bool as_dict_list: Identifies whether the result should be a list of dictionaries or a list of
                            :class:`Citation` objects.
        :return: List of :class:`Citation` objects or corresponding dicts.
        :rtype: list[Citation] or dict
        """
        q = self.session.query(Citation)

        if citation_id and isinstance(citation_id, int):
            q = q.filter_by(id=citation_id)
        else:
            if author is not None:
                q = q.join(Author, Citation.authors)
                if isinstance(author, str):
                    q = q.filter(Author.name.like(author))
                elif isinstance(author, list):
                    q = q.filter(Author.name.in_(author))

            if type:
                q = q.filter(Citation.type.like(type))

            if reference:
                q = q.filter(Citation.reference == reference)

            if name:
                q = q.filter(Citation.name.like(name))

            if date:
                if isinstance(date, datetime.date):
                    q = q.filter(Citation.date == date)
                elif isinstance(date, str):
                    q = q.filter(Citation.date == parse_datetime(date))

            if evidence_text:
                q = q.join(Evidence).filter(Evidence.text.like(evidence_text))

        result = q.all()

        if as_dict_list:
            dict_result = []
            if evidence or evidence_text:
                for citation in result:
                    for evidence in citation.evidences:
                        dict_result.append(evidence.data)
            else:
                dict_result = [cit.data for cit in result]

            result = dict_result

        return result

    def get_property(self, property_id=None, participant=None, modifier=None, as_dict_list=False):
        """Builds and runs a query over all property entries in the database.

        :param int property_id: Database primary identifier.
        :param str participant: The participant that is effected by the property (OBJECT or SUBJECT)
        :param str modifier: The modifier of the property.
        :param bool as_dict_list: Identifies weather the result should be a list of dictionaries or a list of
                             :class:`Property` objects.
        :rtype: list[Property]
        """
        q = self.session.query(Property)

        if property_id:
            q = q.filter_by(id=property_id)
        else:
            if participant:
                q = q.filter(Property.participant.like(participant))

            if modifier:
                q = q.filter(Property.modifier.like(modifier))

        result = q.all()

        if as_dict_list:
            result = [property.data for property in result]

        return result


class CacheManager(EdgeStoreQueryManager, EdgeStoreInsertManager, NetworkManager, EquivalenceManager,
                   OwlNamespaceManager, OwlAnnotationManager):
    """The definition cache manager takes care of storing BEL namespace and annotation files for later use. It uses
    SQLite by default for speed and lightness, but any database can be used with its SQLAlchemy interface.
    """
