# -*- coding: utf-8 -*-

"""The database manager for PyBEL.

Under the hood, PyBEL caches namespace and annotation files for quick recall on later use. The user doesn't need to
enable this option, but can specify a database location if they choose.
"""

from __future__ import unicode_literals

import logging
import time
from collections import defaultdict
from copy import deepcopy
from itertools import chain

import six
from six import string_types
from sqlalchemy import and_, exists, func
from sqlalchemy.orm import aliased
from tqdm import tqdm

from .base_manager import BaseManager, build_engine_session
from .exc import EdgeAddError
from .lookup_manager import LookupManager
from .models import (
    Annotation, AnnotationEntry, Author, Citation, Edge, Evidence, Modification, Namespace, NamespaceEntry, Network,
    Node, Property, edge_annotation, edge_property, network_edge, network_node,
)
from .query_manager import QueryManager
from .utils import extract_shared_optional, extract_shared_required, update_insert_values
from ..canonicalize import node_to_bel
from ..constants import (
    ACTIVITY, ANNOTATIONS, BEL_DEFAULT_NAMESPACE, CITATION, CITATION_AUTHORS, CITATION_DATE, CITATION_FIRST_AUTHOR,
    CITATION_ISSUE, CITATION_LAST_AUTHOR, CITATION_NAME, CITATION_PAGES, CITATION_REFERENCE, CITATION_TITLE,
    CITATION_TYPE, CITATION_VOLUME, DEGRADATION, EFFECT, EVIDENCE, FRAGMENT, FRAGMENT_MISSING, FRAGMENT_START,
    FRAGMENT_STOP, FUNCTION, FUSION, FUSION_REFERENCE, FUSION_START, FUSION_STOP, GMOD, GOCC_KEYWORD, GOCC_LATEST, HGVS,
    IDENTIFIER, KIND, LINE, LOCATION, METADATA_INSERT_KEYS, MODIFIER, NAME, NAMESPACE, OBJECT, PARTNER_3P, PARTNER_5P,
    PMOD, PMOD_CODE, PMOD_POSITION, RANGE_3P, RANGE_5P, RELATION, SUBJECT, TRANSLOCATION, UNQUALIFIED_EDGES, VARIANTS,
    belns_encodings, config, get_cache_connection,
)
from ..language import (
    BEL_DEFAULT_NAMESPACE_URL, BEL_DEFAULT_NAMESPACE_VERSION, activity_mapping, gmod_mappings, pmod_mappings,
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


def _normalize_url(graph, keyword):  # FIXME move to utilities and unit test
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
        namespace = self.get_namespace_by_url(url)
        self.session.query(NamespaceEntry).filter(NamespaceEntry.namespace == namespace).delete()
        self.session.delete(namespace)
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
            log.debug('not caching namespace: %s (%d terms in %.2f seconds)', url, len(values), time.time() - t)
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

    def drop_annotation_by_url(self, url):
        """Drops the annotation at the given URL. Won't work if the edge store is in use.

        :param str url: The URL of the annotation to drop
        """
        annotation = self.get_annotation_by_url(url)
        self.session.query(AnnotationEntry).filter(AnnotationEntry.annotation == annotation).delete()
        self.session.delete(annotation)
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

    def get_annotation_entry_names(self, url):
        """Return a dict of annotations and their labels for the given annotation file.

        :param str url: the location of the annotation file
        :rtype: set[str]
        """
        annotation = self.ensure_annotation(url)
        return annotation.get_entry_names()

    def get_annotation_entry_by_name(self, url, name):
        """Get an annotation entry by URL and name.

        :param str url: The url of the annotation source
        :param str name: The name of the annotation entry from the given url's document
        :rtype: AnnotationEntry
        """
        if self.annotation_object_cache and url in self.annotation_object_cache:
            return self.annotation_object_cache[url][name]

        annotation_filter = and_(Annotation.url == url, AnnotationEntry.name == name)
        return self.session.query(AnnotationEntry).join(Annotation).filter(annotation_filter).one()

    def get_annotation_entries_by_names(self, url, names):
        """Get annotation entries by URL and names.

        :param str url: The url of the annotation source
        :param list[str] names: The names of the annotation entries from the given url's document
        :rtype: list[AnnotationEntry]
        """
        annotation_filter = and_(Annotation.url == url, AnnotationEntry.name.in_(names))
        return self.session.query(AnnotationEntry).join(Annotation).filter(annotation_filter).all()


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
        """Lists the most recently created version of each network (by name)

        :rtype: list[Network]
        """
        most_recent_times = (
            self.session.query(
                Network.name.label('network_name'),
                func.max(Network.created).label('max_created')
            )
                .group_by(Network.name)
                .subquery('most_recent_times')
        )

        most_recent_networks = (
            self.session.query(Network)
                .join(most_recent_times, and_(
                most_recent_times.c.network_name == Network.name,
                most_recent_times.c.max_created == Network.created
            ))
        )

        return most_recent_networks.all()

    def has_name_version(self, name, version):
        """Checks if the name/version combination is already in the database

        :param str name: The network name
        :param str version: The network version
        :rtype: bool
        """
        return self.session.query(exists().where(and_(Network.name == name, Network.version == version))).scalar()

    def query_singleton_edges_from_network(self, network):
        """Returns a query selecting all edge ids that only belong to the given network

        :type network: Network
        :rtype: sqlalchemy.orm.query.Query
        """
        ne1 = aliased(network_edge, name='ne1')
        ne2 = aliased(network_edge, name='ne2')
        singleton_edge_ids_for_network = (
            self.session.query(ne1.c.edge_id)
                .outerjoin(ne2, and_(
                ne1.c.edge_id == ne2.c.edge_id,
                ne1.c.network_id != ne2.c.network_id
            ))
                .filter(and_(
                ne1.c.network_id == network.id,
                ne2.c.edge_id == None
            ))
        )
        return singleton_edge_ids_for_network

    def drop_network(self, network):
        """Drops a network, while also cleaning up any edges that are no longer part of any network.

        :type network: Network
        """
        # get the IDs of the edges that will be orphaned by deleting this network
        # FIXME: this list could be a problem if it becomes very large; possible optimization is a temporary table in DB
        edge_ids = [result.edge_id for result in self.query_singleton_edges_from_network(network)]

        # delete the network-to-node mappings for this network
        self.session.query(network_node).filter(network_node.c.network_id == network.id).delete(
            synchronize_session=False)

        # delete the edge-to-property mappings for the to-be-orphaned edges
        self.session.query(edge_property).filter(edge_property.c.edge_id.in_(edge_ids)).delete(
            synchronize_session=False)

        # delete the edge-to-annotation mappings for the to-be-orphaned edges
        self.session.query(edge_annotation).filter(edge_annotation.c.edge_id.in_(edge_ids)).delete(
            synchronize_session=False)

        # delete the edge-to-network mappings for this network
        self.session.query(network_edge).filter(network_edge.c.network_id == network.id).delete(
            synchronize_session=False)

        # delete the now-orphaned edges
        self.session.query(Edge).filter(Edge.id.in_(edge_ids)).delete(synchronize_session=False)

        # delete the network
        self.session.query(Network).filter(Network.id == network.id).delete(synchronize_session=False)

        # commit it!
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
            self.drop_network(network)

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
        """Loads most network with the given name and version

        :param str name: The name of the network.
        :param str version: The version string of the network.
        :rtype: Optional[Network]
        """
        name_version_filter = and_(Network.name == name, Network.version == version)
        network = self.session.query(Network).filter(name_version_filter).one_or_none()
        return network

    def get_graph_by_name_version(self, name, version):
        """Loads most recently added graph with the given name, or allows for specification of version

        :param str name: The name of the network.
        :param str version: The version string of the network.
        :rtype: Optional[BELGraph]
        """
        network = self.get_network_by_name_version(name, version)

        if network is None:
            return

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
        :rtype: Optional[Network]
        """
        network = self.session.query(Network).filter(Network.name == name).order_by(Network.created.desc()).first()
        return network

    def get_graph_by_most_recent(self, name):
        """Gets the most recently created network with the given name as a :class:`pybel.BELGraph`.

        :param str name: The name of the network
        :rtype: Optional[BELGraph]
        """
        network = self.get_most_recent_network_by_name(name)

        if network is None:
            return

        return network.as_bel()

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
        log.debug('converting network [id=%d] %s to bel graph', network_id, network)
        return network.as_bel()

    def get_networks_by_ids(self, network_ids):
        """Gets a list of networks with the given identifiers. Note: order is not necessarily preserved.

        :param iter[int] network_ids: The identifiers of networks in the database
        :rtype: list[Network]
        """
        log.debug('getting networks by identifiers: %s', network_ids)
        return self.session.query(Network).filter(Network.id_in(network_ids)).all()

    def get_graphs_by_ids(self, network_ids):
        """Gets a list of networks with the given identifiers and converts to BEL graphs. Note: order is not
        necessarily preserved.

        :param iter[int] network_ids: The identifiers of networks in the database
        :rtype: list[BELGraph]
        """
        rv = [
            self.get_graph_by_id(network_id)
            for network_id in network_ids
        ]
        log.debug('returning graphs for network identifiers: %s', network_ids)
        return rv

    def get_graph_by_ids(self, network_ids):
        """Gets a combine BEL Graph from a list of network identifiers

        :param list[int] network_ids: A list of network identifiers
        :rtype: BELGraph
        """
        if len(network_ids) == 1:
            return self.get_graph_by_id(network_ids[0])

        log.debug('getting graph by identifiers: %s', network_ids)
        graphs = self.get_graphs_by_ids(network_ids)

        log.debug('getting union of graphs: %s', network_ids)
        rv = union(graphs)

        return rv


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

    def insert_graph(self, graph, store_parts=True, use_tqdm=False):
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
            self._store_graph_parts(network, graph, use_tqdm=use_tqdm)

        self.session.add(network)
        self.session.commit()

        log.info('inserted %s v%s in %.2f seconds', graph.name, graph.version, time.time() - t)

        return network

    def _store_graph_parts(self, network, graph, use_tqdm=False):
        """Stores the given graph into the edge store.

        :param Network network: A SQLAlchemy PyBEL Network object
        :param BELGraph graph: A BEL Graph
        :raises: pybel.resources.exc.ResourceError
        :raises: EdgeAddError
        """
        # FIXME check if GOCC is needed
        self.ensure_namespace(GOCC_LATEST)

        log.debug('inserting %s into edge store', graph)
        log.debug('storing graph parts: nodes')
        t = time.time()

        nodes_iter = (
            tqdm(graph, total=graph.number_of_nodes(), desc='Nodes')
            if use_tqdm else
            graph
        )

        for node in nodes_iter:
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

        edges = (
            tqdm(graph.edges(data=True), total=graph.number_of_edges(), desc='Edges')
            if use_tqdm else
            graph.edges(data=True)
        )

        for u, v, data in edges:
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
    def _iter_from_annotations_dict(graph, annotations_dict):
        """Iterate over the key/value pairs in this edge data dictionary normalized to their source URLs.

        :param BELGraph graph: A BEL graph
        :param dict[str,dict[str,bool]] annotations_dict: A PyBEL edge data dictionary
        :rtype: iter[tuple[str,set[str]]]
        """
        for key, names in annotations_dict.items():
            if key in graph.annotation_url:
                url = graph.annotation_url[key]
            elif key in graph.annotation_list:
                continue  # skip those
            elif key in graph.annotation_pattern:
                log.debug('pattern annotation in database not implemented yet not implemented')  # FIXME
                continue
            else:
                raise ValueError('Graph resources does not contain keyword: {}'.format(key))

            yield url, set(names)

    def _get_annotation_entries_from_data(self, graph, data):
        """Get the annotation entries from an edge data dictionary.

        :param BELGraph graph: A BEL graph
        :param dict data: A PyBEL edge data dictionary
        :rtype: Optional[list[AnnotationEntry]]
        """
        annotations_dict = data.get(ANNOTATIONS)

        if annotations_dict is None:
            return

        return [
            entry
            for url, names in self._iter_from_annotations_dict(graph, annotations_dict=annotations_dict)
            for entry in self.get_annotation_entries_by_names(url, names)
        ]

    def _add_qualified_edge(self, network, graph, u, v, data):
        """Add a qualified edge to the network.

        :type network: Network
        :type graph: BELGraph
        :type u: tuple
        :type v: tuple
        :type data: dict
        """
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

        annotations = self._get_annotation_entries_from_data(graph, data)

        bel = graph.edge_to_bel(u, v, data=data)
        sha512 = hash_edge(u, v, data)
        edge = self.get_or_create_edge(
            source=self.object_cache_node[hash_node(u)],
            target=self.object_cache_node[hash_node(v)],
            relation=data[RELATION],
            bel=bel,
            sha512=sha512,
            evidence=evidence,
            properties=properties,
            annotations=annotations,
        )
        network.edges.append(edge)

    def _add_unqualified_edge(self, network, graph, u, v, data):
        """Add an unqualified edge to the network.

        :type network: Network
        :type graph: BELGraph
        :type u: tuple
        :type v: tuple
        :type data: dict
        """
        bel = graph.edge_to_bel(u, v, data=data)
        sha512 = hash_edge(u, v, data)
        edge = self.get_or_create_edge(
            source=self.object_cache_node[hash_node(u)],
            target=self.object_cache_node[hash_node(v)],
            relation=data[RELATION],
            bel=bel,
            sha512=sha512,
        )
        network.edges.append(edge)

    def get_or_create_evidence(self, citation, text):
        """Creates entry and object for given evidence if it does not exist.

        :param Citation citation: Citation object obtained from :func:`get_or_create_citation`
        :param str text: Evidence text
        :rtype: Evidence
        """
        sha512 = hash_evidence(text=text, type=str(citation.type), reference=str(citation.reference))

        if sha512 in self.object_cache_evidence:
            evidence = self.object_cache_evidence[sha512]
            self.session.add(evidence)
            return evidence

        evidence = self.get_evidence_by_hash(sha512)

        if evidence is not None:
            self.object_cache_evidence[sha512] = evidence
            return evidence

        evidence = Evidence(
            text=text,
            citation=citation,
            sha512=sha512
        )

        self.session.add(evidence)
        self.object_cache_evidence[sha512] = evidence
        return evidence

    def get_or_create_node(self, graph, node_tuple):
        """Creates entry and object for given node if it does not exist.

        :param BELGraph graph: A BEL graph
        :param tuple node_tuple: A PyBEL node tuple
        :rtype: Node
        """
        sha512 = hash_node(node_tuple)
        if sha512 in self.object_cache_node:
            return self.object_cache_node[sha512]

        node_data = graph.node[node_tuple]
        bel = node_to_bel(node_data)

        node = self.get_node_by_hash(sha512)

        if node is not None:
            self.object_cache_node[sha512] = node
            return node

        type = node_data[FUNCTION]
        node = Node(type=type, bel=bel, sha512=sha512)

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
        self.object_cache_node[sha512] = node
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

    def get_or_create_edge(self, source, target, relation, bel, sha512, evidence=None, annotations=None,
                           properties=None):
        """Creates entry for given edge if it does not exist.

        :param Node source: Source node of the relation
        :param Node target: Target node of the relation
        :param str relation: Type of the relation between source and target node
        :param str bel: BEL statement that describes the relation
        :param str sha512: The SHA512 hash of the edge as a string
        :param Evidence evidence: Evidence object that proves the given relation
        :param Optional[list[Property]] properties: List of all properties that belong to the edge
        :param Optional[list[AnnotationEntry]] annotations: List of all annotations that belong to the edge
        :rtype: Edge
        """
        if sha512 in self.object_cache_edge:
            edge = self.object_cache_edge[sha512]
            self.session.add(edge)
            return edge

        edge = self.get_edge_by_hash(sha512)

        if edge is not None:
            self.object_cache_edge[sha512] = edge
            return edge

        edge = Edge(
            source=source,
            target=target,
            relation=relation,
            bel=bel,
            sha512=sha512,
        )

        if evidence is not None:
            edge.evidence = evidence
        if properties is not None:
            edge.properties = properties
        if annotations is not None:
            edge.annotations = annotations

        self.session.add(edge)
        self.object_cache_edge[sha512] = edge
        return edge

    def get_or_create_citation(self, type, reference, name=None, title=None, volume=None, issue=None, pages=None,
                               date=None, first=None, last=None, authors=None):
        """Create an entry for given citation if it does not exist, or return it if it does.

        :param str type: Citation type (e.g. PubMed)
        :param str reference: Identifier of the given citation (e.g. PubMed id)
        :param Optional[str] name: Name of the publication
        :param Optional[str] title: Title of article
        :param Optional[str] volume: Volume of publication
        :param Optional[str] issue: Issue of publication
        :param Optional[str] pages: Pages of issue
        :param Optional[str] date: Date of publication in ISO 8601 (YYYY-MM-DD) format
        :param Optional[str] first: Name of first author
        :param Optional[str] last: Name of last author
        :param authors: Either a list of authors separated by |, or an actual list of authors
        :type authors: None or str or list[str]
        :rtype: Citation
        """
        type = type.strip()
        reference = reference.strip()

        sha512 = hash_citation(type=type, reference=reference)

        if sha512 in self.object_cache_citation:
            citation = self.object_cache_citation[sha512]
            self.session.add(citation)
            return citation

        citation = self.get_citation_by_hash(sha512)

        if citation is not None:
            self.object_cache_citation[sha512] = citation
            return citation

        citation = Citation(
            type=type,
            reference=reference,
            sha512=sha512,
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
        self.object_cache_citation[sha512] = citation
        return citation

    def get_or_create_author(self, name):
        """Get an author by name, or creates one if it does not exist.

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

    def get_modification_by_hash(self, sha512):
        """Get a modification by a SHA512 hash.

        :param str sha512: A SHA512 hash of a modification
        :rtype: Optional[Modification]
        """
        return self.session.query(Modification).filter(Modification.sha512 == sha512).one_or_none()

    def get_or_create_modification(self, graph, node_data):
        """Creates a list of modification objects that belong to the node described by node_data.

        :param BELGraph graph: A BEL graph
        :param dict node_data: Describes the given node and contains is_variant information
        :return: A list of modification objects belonging to the given node
        :rtype: Optional[list[Modification]]
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
                    namespace_url = _normalize_url(graph, variant_identifier[NAMESPACE])

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
        """Get a property by its hash if it exists.

        :param str property_hash: The hash of the property to search
        :rtype: Optional[Property]
        """
        return self.session.query(Property).filter(Property.sha512 == property_hash).one_or_none()

    def _make_property_from_dict(self, property_def):
        """Build an edge property from a dictionary.

        :param property_def:
        :rtype: Property
        """
        property_hash = hash_dump(property_def)

        edge_property_model = self.object_cache_property.get(property_hash)
        if edge_property_model is None:
            edge_property_model = self.get_property_by_hash(property_hash)

            if not edge_property_model:
                property_def['sha512'] = property_hash
                edge_property_model = Property(**property_def)

            self.object_cache_property[property_hash] = edge_property_model

        return edge_property_model

    def get_or_create_properties(self, graph, edge_data):  # TODO make for just single property then loop with other fn.
        """Creates a list of all subject and object related properties of the edge. Returns None if the property cannot
        be constructed due to missing cache entries.

        :param BELGraph graph: A BEL graph
        :param dict edge_data: Describes the context of the given edge.
        :return: A list of all subject and object properties of the edge
        :rtype: Optional[list[Property]]
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
                        namespace_url = _normalize_url(graph, effect[NAMESPACE])

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


class _Manager(QueryManager, InsertManager, NetworkManager):
    """A wrapper around PyBEL managers that can be directly instantiated with an engine and session."""


class Manager(_Manager):
    """A manager for the PyBEL database."""

    def __init__(self, connection=None, engine=None, session=None, **kwargs):
        """Create a connection to database and a persistent session using SQLAlchemy.

        A custom default can be set as an environment variable with the name :data:`pybel.constants.PYBEL_CONNECTION`,
        using an `RFC-1738 <http://rfc.net/rfc1738.html>`_ string. For example, a MySQL string can be given with the
        following form:

        :code:`mysql+pymysql://<username>:<password>@<host>/<dbname>?charset=utf8[&<options>]`

        A SQLite connection string can be given in the form:

        ``sqlite:///~/Desktop/cache.db``

        Further options and examples can be found on the SQLAlchemy documentation on
        `engine configuration <http://docs.sqlalchemy.org/en/latest/core/engines.html>`_.

        :param Optional[str] connection: An RFC-1738 database connection string. If ``None``, tries to load from the
         environment variable ``PYBEL_CONNECTION`` then from the config file ``~/.config/pybel/config.json`` whose
         value for ``PYBEL_CONNECTION`` defaults to :data:`pybel.constants.DEFAULT_CACHE_LOCATION`.
        :param engine: Optional engine to use. Must be specified with a session and no connection.
        :param session: Optional session to use. Must be specified with an engine and no connection.
        :param bool echo: Turn on echoing sql
        :param Optional[bool] autoflush: Defaults to True if not specified in kwargs or configuration.
        :param Optional[bool] autocommit: Defaults to False if not specified in kwargs or configuration.
        :param Optional[bool] expire_on_commit: Defaults to False if not specified in kwargs or configuration.
        :param scopefunc: Scoped function to pass to :func:`sqlalchemy.orm.scoped_session`

        From the Flask-SQLAlchemy documentation:

        An extra key ``'scopefunc'`` can be set on the ``options`` dict to
        specify a custom scope function.  If it's not provided, Flask's app
        context stack identity is used. This will ensure that sessions are
        created and removed with the request/response cycle, and should be fine
        in most cases.

        Allowed Usages:

        Instantiation with connection string as positional argument

        >>> my_connection = 'sqlite:///~/Desktop/cache.db'
        >>> manager = Manager(my_connection)

        Instantiation with connection string as positional argument with keyword arguments

        >>> my_connection = 'sqlite:///~/Desktop/cache.db'
        >>> manager = Manager(my_connection, echo=True)

        Instantiation with connection string as keyword argument

        >>> my_connection = 'sqlite:///~/Desktop/cache.db'
        >>> manager = Manager(connection=my_connection)

        Instantiation with connection string as keyword argument with keyword arguments

        >>> my_connection = 'sqlite:///~/Desktop/cache.db'
        >>> manager = Manager(connection=my_connection, echo=True)

        Instantiation with user-supplied engine and session objects as keyword arguments

        >>> my_engine, my_session = ...  # magical creation! See SQLAlchemy documentation
        >>> manager = Manager(engine=my_engine, session=my_session)
        """
        if connection and (engine or session):
            raise ValueError('can not specify connection with engine/session')

        if engine is None and session is None:
            if connection is None:
                connection = get_cache_connection()

            engine, session = build_engine_session(connection=connection, **kwargs)

        elif engine is None or session is None:
            raise ValueError('need both engine and session to be specified')

        elif kwargs:
            raise ValueError('keyword arguments should not be used with engine/session')

        super(Manager, self).__init__(engine=engine, session=session)
        self.create_all()
