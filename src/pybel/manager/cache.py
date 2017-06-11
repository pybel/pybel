# -*- coding: utf-8 -*-

"""
Definition Cache Manager
------------------------
Under the hood, PyBEL caches namespace and annotation files for quick recall on later use. The user doesn't need to
enable this option, but can specify a database location if they choose.
"""

import datetime
import logging
import time
from collections import defaultdict

from sqlalchemy import func

from . import models
from .base_cache import BaseCacheManager
from .models import (
    Network,
    Annotation,
    AnnotationEntry,
    Namespace,
    NamespaceEntryEquivalence,
    NamespaceEntry
)
from .utils import parse_owl, extract_shared_required, extract_shared_optional
from ..canonicalize import decanonicalize_edge, decanonicalize_node
from ..constants import *
from ..io.gpickle import to_bytes
from ..struct import BELGraph
from ..utils import get_bel_resource, parse_datetime, subdict_matches

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
        #: A dictionary from {namespace URL: models.Namespace}
        self.namespace_model = {}
        #: A dictionary from {namespace URL: set of (parent, child) tuples}
        self.namespace_edge_cache = {}

    def list_namespaces(self):
        """Returns a list of all namespace keyword/url pairs"""
        return list(self.session.query(Namespace.keyword, Namespace.version, Namespace.url).all())

    def drop_namespaces(self):
        """Drops all namespaces"""
        self.namespace_cache.clear()
        self.namespace_id_cache.clear()
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

        config = get_bel_resource(url)

        values = {c: e if e else DEFAULT_BELNS_ENCODING for c, e in config['Values'].items() if c}

        if config['Processing']['CacheableFlag'] not in {'yes', 'Yes', 'True', 'true'}:
            return values

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

        namespace = Namespace(**namespace_insert_values)
        namespace.entries = [NamespaceEntry(name=c, encoding=e) for c, e in values.items()]

        self.session.add(namespace)
        self.session.commit()

        return namespace

    def ensure_namespace(self, url):
        """Caches a namespace file if not already in the cache. If not cachable, returns a dict of the values

        :param url: the location of the namespace file
        :type url: str
        :return: The namespace instance
        :rtype: Namespace or dict
        """
        if url in self.namespace_model:
            log.debug('already in memory: %s (%d)', url, len(self.namespace_cache[url]))
            return self.namespace_model[url]

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
        #: A dictionary from {annotation URL: models.Annotation}
        self.annotation_model = {}
        #: A dictionary from {annotation URL: set of (parent, child) tuples}
        self.annotation_edge_cache = {}

    def drop_annotations(self):
        """Drops all annotations"""

        self.annotation_cache.clear()
        self.annotation_id_cache.clear()
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
        :rtype: models.Annotation
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

        annotation = models.Annotation(**annotation_insert_values)
        annotation.entries = [models.AnnotationEntry(name=c, label=l) for c, l in config['Values'].items() if c]

        self.session.add(annotation)
        self.session.commit()

        return annotation

    def ensure_annotation(self, url):
        """Caches an annotation file if not already in the cache

        :param url: the location of the annotation file
        :type url: str
        :return: The ensured annotation instance
        :rtype: models.Annotation
        """
        if url in self.annotation_model:
            log.debug('already in memory: %s (%d)', url, len(self.annotation_cache[url]))
            return self.annotation_model[url]

        t = time.time()
        results = self.session.query(models.Annotation).filter(models.Annotation.url == url).one_or_none()

        if results is None:
            results = self.insert_annotation(url)
        else:
            log.debug('loaded annotation: %s (%d, %.2fs)', url, len(results.entries), time.time() - t)

        self.annotation_model[url] = results

        for entry in results.entries:
            self.annotation_cache[url][entry.name] = entry.label
            self.annotation_id_cache[url][entry.name] = entry.id

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
        :rtype: models.AnnotationEntry
        """
        annotation = self.session.query(models.Annotation).filter_by(url=url).one()
        return self.session.query(models.AnnotationEntry).filter_by(annotation=annotation, name=value).one()


class OwlAnnotationManager(AnnotationManager):
    """Manages OWL annotations"""

    def insert_annotation_owl(self, iri, keyword=None):
        """Caches an ontology at the given IRI

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

    def get_equivalence_by_entry(self, namespace_url, name):
        """Gets the equivalence class

        :param str namespace_url: the URL of the namespace
        :param str name: the name of the entry in the namespace
        :return: the equivalence class of the entry in the given namespace
        """
        ns = self.session.query(Namespace).filter_by(url=namespace_url).one()
        ns_entry = self.session.query(NamespaceEntry).filter(NamespaceEntry.namespace_id == ns.id,
                                                             NamespaceEntry.name == name).one()
        return ns_entry.equivalence

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
        return self.session.query(func.count(models.Network.id)).scalar()

    def list_networks(self):
        """Lists all networks in the cache

        :rtype: list[Network]
        """
        return self.session.query(Network).all()

    def drop_network_by_id(self, network_id):
        """Drops a network by its database identifier

        :param int network_id: The network's database identifier
        """

        # TODO delete with cascade, such that the network-edge table and all edges just in that network are deleted
        self.session.query(Network).filter(Network.id == network_id).delete()
        self.session.commit()

    def drop_networks(self):
        """Drops all networks"""
        self.session.query(Network).delete()
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
        return self.session.query(Network).filter(Network.id in set(network_ids)).all()

    def insert_graph(self, graph, store_parts=False):
        """Inserts a graph in the database.

        :param BELGraph graph: A BEL graph
        :param bool store_parts: Should the graph be stored in the edge store?
        :return: A Network object
        :rtype: Network
        """
        log.debug('inserting %s v%s', graph.name, graph.version)

        t = time.time()

        namespaces = [self.ensure_namespace(url) for url in graph.namespace_url.values()]
        annotations = [self.ensure_annotation(url) for url in graph.annotation_url.values()]

        network = Network(blob=to_bytes(graph), **graph.document)

        if store_parts:
            if not self.session.query(Namespace).filter_by(keyword=GOCC_KEYWORD).first():
                self.ensure_namespace(GOCC_LATEST)

            network.namespaces.extend(namespaces)
            network.annotations.extend(annotations)

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

    def store_graph_parts(self, network, graph):
        """Stores the given graph into the edge store.

        :param Network network: A SQLAlchemy PyBEL Network object
        :param BELGraph graph: A BEL Graph
        """
        nc = {}

        for node in graph.nodes_iter():
            node_object = self.get_or_create_node(graph, node)
            nc[node] = node_object
            if node_object not in network.nodes:
                network.nodes.append(node_object)

        self.session.flush()

        for u, v, k, data in graph.edges_iter(data=True, keys=True):
            source, target = nc[u], nc[v]

            if CITATION not in data or EVIDENCE not in data:
                continue

            citation = self.get_or_create_citation(**data[CITATION])
            evidence = self.get_or_create_evidence(citation, data[EVIDENCE])

            bel = decanonicalize_edge(graph, u, v, k)
            edge = self.get_or_create_edge(
                graph_key=k,
                source=source,
                target=target,
                relation=data[RELATION],
                evidence=evidence,
                bel=bel,
                blob=pickle.dumps(data)
            )

            for key, value in data[ANNOTATIONS].items():
                if key in graph.annotation_url:
                    url = graph.annotation_url[key]
                    annotation = self.get_annotation_entry(url, value)
                    if annotation not in edge.annotations:
                        edge.annotations.append(annotation)

            properties = self.get_or_create_property(graph, data)
            for property in properties:
                if property not in edge.properties:
                    edge.properties.append(property)

            if edge not in network.edges:
                network.edges.append(edge)

            if citation not in network.citations:
                network.citations.append(citation)

            self.session.flush()

    def get_or_create_evidence(self, citation, text):
        """Creates entry and object for given evidence if it does not exist.

        :param models.Citation citation: Citation object obtained from :func:`get_or_create_citation`
        :param str text: Evidence text
        :return: An Evidence object
        :rtype: models.Evidence
        """
        result = self.session.query(models.Evidence).filter_by(text=text).one_or_none()

        if result is None:
            result = models.Evidence(text=text, citation=citation)
            self.session.add(result)
            # self.session.flush()

        return result

    def get_or_create_node(self, graph, node):
        """Creates entry and object for given node if it does not exist.

        :param BELGraph graph: A BEL graph
        :param tuple node: A BEL node
        :return: A Node object
        :rtype: models.Node
        """
        bel = decanonicalize_node(graph, node)
        blob = pickle.dumps(graph.node[node])
        node_data = graph.node[node]

        result = self.session.query(models.Node).filter_by(bel=bel).one_or_none()
        if result is None:
            type = node_data[FUNCTION]

            if NAMESPACE in node_data and node_data[NAMESPACE] in graph.namespace_url:
                namespace = node_data[NAMESPACE]
                url = graph.namespace_url[namespace]
                namespace_entry = self.get_namespace_entry(url, node_data[NAME])
                result = models.Node(type=type, namespaceEntry=namespace_entry, bel=bel, blob=blob)

            elif NAMESPACE in node_data and node_data[NAMESPACE] in graph.namespace_pattern:
                namespace_pattern = graph.namespace_pattern[node_data[NAMESPACE]]
                result = models.Node(type=type, namespacePattern=namespace_pattern, bel=bel, blob=blob)

            else:
                result = models.Node(type=type, bel=bel, blob=blob)

            if VARIANTS in node_data or FUSION in node_data:
                result.is_variant = True
                result.fusion = FUSION in node_data
                result.modifications = self.get_or_create_modification(graph, node_data)

            self.session.add(result)

        return result

    def get_or_create_edge(self, graph_key, source, target, evidence, bel, relation, blob):
        """Creates entry for given edge if it does not exist.

        :param graph_key: Key that identifies the order of edges and weather an edge is artificially created or extracted
                        from a valid BEL statement.
        :type graph_key: tuple
        :param models.Node source: Source node of the relation
        :param models.Node target: Target node of the relation
        :param models.Evidence evidence: Evidence object that proves the given relation
        :param str bel: BEL statement that describes the relation
        :param str relation: Type of the relation between source and target node
        :param bytes blob: A blob of the edge data object.
        :return: An Edge object
        :rtype: models.Edge
        """
        result = self.session.query(models.Edge).filter_by(bel=bel).one_or_none()

        if result is None:
            result = models.Edge(
                graphIdentifier=graph_key,
                source=source,
                target=target,
                evidence=evidence,
                bel=bel,
                relation=relation,
                blob=blob
            )
            self.session.add(result)

        return result

    def get_or_create_citation(self, type, name, reference, date=None, authors=None):
        """Creates entry for given citation if it does not exist.

        :param str type: Citation type (e.g. PubMed)
        :param str name: Title of the publication that is cited
        :param str reference: Identifier of the given citation (e.g. PubMed id)
        :param str date: Date of publication in ISO 8601 format
        :param str authors: List of authors separated by |
        :return: A Citation object
        :rtype: models.Citation
        """
        result = self.session.query(models.Citation).filter_by(type=type, reference=reference).one_or_none()

        if result is None:
            if date:
                date = parse_datetime(date)
            else:
                date = None

            result = models.Citation(type=type, name=name, reference=reference.strip(), date=date)

            if authors is not None:
                for author in authors.split('|'):
                    result.authors.append(self.get_or_create_author(author))

            self.session.add(result)
            self.session.flush()

        return result

    def get_or_create_author(self, name):
        """Gets an author by name, or creates one

        :param str name: An author's name
        :return: An Author object
        :rtype: models.Author
        """
        result = self.session.query(models.Author).filter_by(name=name).one_or_none()

        if result is None:
            result = models.Author(name=name)
            self.session.add(result)

        return result

    def get_or_create_modification(self, graph, node_data):
        """Creates a list of modification objects (models.Modification) that belong to the node described by
        node_data.

        :param BELGraph graph: A BEL graph
        :param dict node_data: Describes the given node and contains is_variant information
        :return: A list of modification objects belonging to the given node
        :rtype: list[models.Modification]
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
                    'p3Missing': node_data[RANGE_3P][FUSION_MISSING]
                })
            else:
                fusion_dict.update({
                    'p3Reference': node_data[RANGE_3P][FUSION_REFERENCE],
                    'p3Start': node_data[RANGE_3P][FUSION_START],
                    'p3Stop': node_data[RANGE_3P][FUSION_STOP],
                })

            if FUSION_MISSING in node_data[RANGE_5P]:
                fusion_dict.update({
                    'p5Missing': node_data[RANGE_5P][FUSION_MISSING]
                })
            else:
                fusion_dict.update({
                    'p5Reference': node_data[RANGE_5P][FUSION_REFERENCE],
                    'p5Start': node_data[RANGE_3P][FUSION_START],
                    'p5Stop': node_data[RANGE_3P][FUSION_STOP],
                })

            modification_list.append(fusion_dict)

        else:
            for variant in node_data[VARIANTS]:
                mod_type = variant[KIND]
                if mod_type == HGVS:
                    modification_list.append({
                        'modType': mod_type,
                        'variantString': variant[IDENTIFIER]
                    })

                elif mod_type == FRAGMENT:
                    if FRAGMENT_MISSING in variant:
                        modification_list.append({
                            'modType': mod_type,
                            'p3Missing': variant[FRAGMENT_MISSING]
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
                        'modNamespace': variant[IDENTIFIER][NAME],
                        'modName': variant[IDENTIFIER][NAME]
                    })

                elif mod_type == PMOD:
                    modification_list.append({
                        'modType': mod_type,
                        'modNamespace': variant[IDENTIFIER][NAMESPACE],
                        'modName': variant[IDENTIFIER][NAME],
                        'aminoA': variant[PMOD_CODE] if PMOD_CODE in variant else None,
                        'position': variant[PMOD_POSITION] if PMOD_POSITION in variant else None
                    })

        modifications = []
        for modification in modification_list:
            mod = self.session.query(models.Modification).filter_by(**modification).one_or_none()
            if not mod:
                mod = models.Modification(**modification)
            modifications.append(mod)

        return modifications

    def get_or_create_property(self, graph, edge_data):
        """Creates a list of all subject and object related properties of the edge.

        :param pybel.BELGraph graph: A BEL graph
        :param dict edge_data: Describes the context of the given edge.
        :return: A list of all subject and object properties of the edge
        :rtype: list[models.Property]
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

            if modifier in (ACTIVITY, TRANSLOCATION) and EFFECT in participant_data:
                for effect_type, effect_value in participant_data[EFFECT].items():
                    property_dict['relativeKey'] = effect_type
                    if NAMESPACE in effect_value:
                        if effect_value[NAMESPACE] == GOCC_KEYWORD and GOCC_KEYWORD not in graph.namespace_url:
                            namespace_url = GOCC_LATEST
                        else:
                            namespace_url = graph.namespace_url[effect_value[NAMESPACE]]
                        property_dict['namespaceEntry'] = self.get_namespace_entry(namespace_url, effect_value[NAME])
                    else:
                        property_dict['propValue'] = effect_value

                    property_list.append(property_dict)

            elif modifier == LOCATION:
                namespace_url = graph.namespace_url[participant_data[LOCATION][NAMESPACE]]
                property_dict['namespaceEntry'] = self.get_namespace_entry(namespace_url,
                                                                           participant_data[LOCATION][NAME])
                property_list.append(property_dict)

            else:
                property_list.append(property_dict)

        for property_def in property_list:
            edge_property = self.session.query(models.Property).filter_by(**property_def).first()
            if not edge_property:
                edge_property = models.Property(**property_def)

            if edge_property not in properties:
                properties.append(edge_property)

        return properties


class EdgeStoreQueryManager(BaseCacheManager):
    """Groups queries over the edge store"""

    def rebuild_by_edge_filter(self, **annotations):
        """Gets all edges matching the given query annotation values

        :param dict annotations: dictionary of {key: value}
        :return: A graph composed of the filtered edges
        :rtype: pybel.BELGraph
        """
        graph = BELGraph()
        for annotation_key, annotation_value in annotations.items():

            annotation_def = self.session.query(models.Annotation).filter_by(keyword=annotation_key).first()
            annotation = self.session.query(models.AnnotationEntry).filter_by(annotation=annotation_def,
                                                                              name=annotation_value).first()

            # Add Annotations to belGraph.annotation_url
            # Add Namespaces to belGraph.namespace_url
            # What about meta information?
            edges = self.session.query(models.Edge).filter(models.Edge.annotations.contains(annotation)).all()
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
                    key=edge_data['key'],
                    attr_dict=edge_data['data']
                )

        return graph

    def help_rebuild_list_components(self, node_object):
        """Builds data and identifier for list node objects.

        :param node_object: Node object defined in models.
        :return: Dictionary with 'key' and 'node' keys.
        """
        node_info = node_object.data
        key = list(node_info['key'])
        data = node_info['data']
        if node_object.type in (COMPLEX, COMPOSITE):
            components = self.session.query(models.Edge).filter_by(source=node_object, relation=HAS_COMPONENT).all()
            for component in components:
                component_key = component.target.data['key']
                key.append(component_key)

        elif node_object.type == REACTION:
            reactant_components = self.session.query(models.Edge).filter_by(source=node_object,
                                                                            relation=HAS_REACTANT).all()
            product_components = self.session.query(models.Edge).filter_by(source=node_object,
                                                                           relation=HAS_PRODUCT).all()
            reactant_keys = tuple(reactant.target.data['key'] for reactant in reactant_components)
            product_keys = tuple(product.target.data['key'] for product in product_components)
            key.append(reactant_keys)
            key.append(product_keys)

        return {'key': tuple(key), 'node': (tuple(key), data)}

    def get_edge_iter_by_filter(self, **annotations):
        """Returns an iterator over models.Edge object that match the given annotations

        :param dict annotations: dictionary of {URL: values}
        :return: An iterator over models.Edge object that match the given annotations
        :rtype: iter of models.Edge
        """
        # TODO make smarter
        for edge in self.session.query(models.Edge).all():
            ad = {a.annotation.name: a.name for a in edge.annotations}
            if subdict_matches(ad, annotations):
                yield edge

    def get_graph_by_filter(self, **annotations):
        """Fills a BEL graph with edges retrieved from a filter

        :param dict annotations: dictionary of {URL: values}
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
                            :class:`models.Node` objects.
        :return: A list of the fitting nodes as :class:`models.Node` objects or dicts.
        :rtype: list[models.Node]
        """
        q = self.session.query(models.Node)

        if node_id and isinstance(node_id, int):
            q = q.filter_by(id=node_id)
        else:
            if bel:
                q = q.filter(models.Node.bel.like(bel))

            if type:
                q = q.filter(models.Node.type.like(type))

            if namespace or name:
                q = q.join(NamespaceEntry)
                if namespace:
                    q = q.join(Namespace).filter(Namespace.keyword.like(namespace))
                if name:
                    q = q.filter(NamespaceEntry.name.like(name))

            if modification_type or modification_name:
                q = q.join(models.Modification)
                if modification_type:
                    q = q.filter(models.Modification.modType.like(modification_type))
                if modification_name:
                    q = q.filter(models.Modification.modName.like(modification_name))

        result = q.all()

        if as_dict_list:
            return [node.data for node in result]
        else:
            return result

    def count_nodes(self):
        """Counts the number of nodes in the cache

        :rtype: int
        """
        return self.session.query(func.count(models.Node.id)).scalar()

    def count_edges(self):
        """Counts the number of edges in the cache

        :rtype: int
        """
        return self.session.query(func.count(models.Edge.id)).scalar()

    def get_edge(self, edge_id=None, bel=None, source=None, target=None, relation=None, citation=None,
                 evidence=None, annotation=None, property=None, as_dict_list=False):
        """Builds and runs a query over all edges in the PyBEL cache.

        :param str bel: BEL statement that represents the desired edge.
        :param source: BEL term of source node e.g. ``p(HGNC:APP)`` or :class:`models.Node` object.
        :type source: str or models.Node
        :param target: BEL term of target node e.g. ``p(HGNC:APP)`` or :class:`models.Node` object.
        :type target: str or models.Node
        :param str relation: The relation that should be present between source and target node.
        :param citation: The citation that backs the edge up. It is possible to use the reference_id
                         or a models.Citation object.
        :type citation: str or models.Citation
        :param evidence: The supporting text of the edge. It is possible to use a snipplet of the text
                         or a models.Evidence object.
        :type evidence: str or models.Evidence
        :param annotation: Dictionary of annotationKey:annotationValue parameters or just a annotationValue parameter
                            as string.
        :type annotation: dict or str
        :param property:
        :param bool as_dict_list: Identifies whether the result should be a list of dictionaries or a list of
                            :class:`models.Edge` objects.
        :return:
        """
        q = self.session.query(models.Edge)

        if edge_id and isinstance(edge_id, int):
            q = q.filter_by(id=edge_id)
        else:
            if bel:
                q = q.filter(models.Edge.bel.like(bel))

            if relation:
                q = q.filter(models.Edge.relation.like(relation))

            if annotation:
                q = q.join(models.AnnotationEntry, models.Edge.annotations)
                if isinstance(annotation, dict):
                    q = q.join(models.Annotation).filter(models.Annotation.keyword.in_(list(annotation.keys())))
                    q = q.filter(models.AnnotationEntry.name.in_(list(annotation.values())))

                elif isinstance(annotation, str):
                    q = q.filter(models.AnnotationEntry.name.like(annotation))

            if source:
                if isinstance(source, str):
                    source = self.get_node(bel=source)[0]

                if isinstance(source, models.Node):
                    q = q.filter(models.Edge.source == source)

                    # ToDo: in_() not yet supported for relations
                    # elif isinstance(source, list) and len(source) > 0:
                    #    if isinstance(source[0], models.Node):
                    #        q = q.filter(models.Edge.source.in_(source))

            if target:
                if isinstance(target, str):
                    target = self.get_node(bel=target)[0]

                if isinstance(target, models.Node):
                    q = q.filter(models.Edge.target == target)

                    # elif isinstance(target, list) and len(target) > 0:
                    #    if isinstance(target[0], models.Node):
                    #        q = q.filter(models.Edge.source.in_(target))

            if citation or evidence:
                q = q.join(models.Evidence)

                if citation:
                    if isinstance(citation, models.Citation):
                        q = q.filter(models.Evidence.citation == citation)

                    elif isinstance(citation, list) and isinstance(citation[0], models.Citation):
                        q = q.filter(models.Evidence.citation.in_(citation))

                    elif isinstance(citation, str):
                        q = q.join(models.Citation).filter(models.Citation.reference.like(citation))

                if evidence:
                    if isinstance(evidence, models.Evidence):
                        q = q.filter(models.Edge.evidence == evidence)

                    elif isinstance(evidence, str):
                        q = q.filter(models.Evidence.text.like(evidence))

            if property:
                q = q.join(models.Property, models.Edge.properties)

                if isinstance(property, models.Property):
                    q = q.filter(models.Property.id == property.id)
                elif isinstance(property, int):
                    q = q.filter(models.Property.id == property)

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
                            :class:`models.Citation` objects.
        :return: List of :class:`models.Citation` objects or corresponding dicts.
        :rtype: list[models.Citation] or dict
        """
        q = self.session.query(models.Citation)

        if citation_id and isinstance(citation_id, int):
            q = q.filter_by(id=citation_id)
        else:
            if author:
                q = q.join(models.Author, models.Citation.authors)
                if isinstance(author, str):
                    q = q.filter(models.Author.name.like(author))
                elif isinstance(author, list):
                    q = q.filter(models.Author.name.in_(author))

            if type:
                q = q.filter(models.Citation.type.like(type))

            if reference:
                q = q.filter(models.Citation.reference == reference)

            if name:
                q = q.filter(models.Citation.name.like(name))

            if date:
                if isinstance(date, datetime.date):
                    q = q.filter(models.Citation.date == date)
                elif isinstance(date, str):
                    q = q.filter(models.Citation.date == parse_datetime(date))

            if evidence_text:
                q = q.join(models.Evidence).filter(models.Evidence.text.like(evidence_text))

        result = q.all()

        if not as_dict_list:
            return result

        dict_result = []
        if evidence or evidence_text:
            for citation in result:
                for evidence in citation.evidences:
                    dict_result.append(evidence.data)
        else:
            dict_result = [cit.data for cit in result]

        return dict_result

    def get_property(self, property_id=None, participant=None, modifier=None, as_dict_list=False):
        """Builds and runs a query over all property entries in the database.

        :param int property_id: Database primary identifier.
        :param str participant: The participant that is effected by the property (OBJECT or SUBJECT)
        :param str modifier: The modifier of the property.
        :param bool as_dict_list: Identifies weather the result should be a list of dictionaries or a list of
                             :class:`models.Property` objects.
        :return:
        :rtype: list[models.Property]
        """
        q = self.session.query(models.Property)

        if property_id:
            q = q.filter_by(id=property_id)
        else:
            if participant:
                q = q.filter(models.Property.participant.like(participant))

            if modifier:
                q = q.filter(models.Property.modifier.like(modifier))

        result = q.all()

        if as_dict_list:
            result = [property.data for property in result]

        return result


class CacheManager(EdgeStoreQueryManager, EdgeStoreInsertManager, NetworkManager, EquivalenceManager,
                   OwlNamespaceManager, OwlAnnotationManager):
    """The definition cache manager takes care of storing BEL namespace and annotation files for later use. It uses
    SQLite by default for speed and lightness, but any database can be used wiht its SQLAlchemy interface.
    """
