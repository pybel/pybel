# -*- coding: utf-8 -*-

"""The database manager for PyBEL.

Under the hood, PyBEL caches namespace and annotation files for quick recall on later use. The user doesn't need to
enable this option, but can specify a database location if they choose.
"""

import json
import logging
import time
from copy import deepcopy
from itertools import chain
from typing import Dict, Iterable, List, Mapping, Optional, Set, Tuple, Union

import sqlalchemy
from sqlalchemy import and_, exists, func
from sqlalchemy.orm import aliased
from tqdm import tqdm

from bel_resources import get_bel_resource
from .base_manager import BaseManager, build_engine_session
from .exc import EdgeAddError
from .lookup_manager import LookupManager
from .models import (
    Author, Citation, Edge, Evidence, Modification, Namespace, NamespaceEntry, Network, Node, Property, edge_annotation,
    edge_property, network_edge, network_node,
)
from .query_manager import QueryManager
from .utils import extract_shared_optional, extract_shared_required, update_insert_values
from ..constants import (
    ACTIVITY, ANNOTATIONS, BEL_DEFAULT_NAMESPACE, CITATION, CITATION_AUTHORS, CITATION_DATE, CITATION_FIRST_AUTHOR,
    CITATION_ISSUE, CITATION_LAST_AUTHOR, CITATION_NAME, CITATION_PAGES, CITATION_REFERENCE, CITATION_TITLE,
    CITATION_TYPE, CITATION_TYPE_PUBMED, CITATION_VOLUME, DEGRADATION, EFFECT, EVIDENCE, FRAGMENT, FRAGMENT_MISSING,
    FRAGMENT_START, FRAGMENT_STOP, FUSION, FUSION_REFERENCE, FUSION_START, FUSION_STOP, GMOD, HGVS, IDENTIFIER, KIND,
    LINE, LOCATION, METADATA_INSERT_KEYS, MODIFIER, NAME, NAMESPACE, OBJECT, PARTNER_3P, PARTNER_5P, PMOD, PMOD_CODE,
    PMOD_POSITION, RANGE_3P, RANGE_5P, RELATION, SUBJECT, TRANSLOCATION, UNQUALIFIED_EDGES, VARIANTS, belns_encodings,
    get_cache_connection,
)
from ..dsl import BaseEntity
from ..language import (
    BEL_DEFAULT_NAMESPACE_URL, BEL_DEFAULT_NAMESPACE_VERSION, activity_mapping, compartment_mapping, gmod_mappings,
    pmod_mappings,
)
from ..struct.graph import AnnotationsDict, BELGraph
from ..struct.operations import union
from ..typing import EdgeData
from ..utils import hash_citation, hash_dump, hash_evidence, parse_datetime

__all__ = [
    'Manager',
    'NetworkManager',
]

log = logging.getLogger(__name__)

DEFAULT_BELNS_ENCODING = ''.join(sorted(belns_encodings))

_optional_namespace_entries_mapping = {
    'species': ('Namespace', 'SpeciesString'),
    'query_url': ('Namespace', 'QueryValueURL'),
    'domain': ('Namespace', 'DomainString'),
}


def _get_namespace_insert_values(bel_resource):
    namespace_insert_values = {
        'name': bel_resource['Namespace']['NameString'],
    }

    namespace_insert_values.update(extract_shared_required(bel_resource, 'Namespace'))
    namespace_insert_values.update(extract_shared_optional(bel_resource, 'Namespace'))

    update_insert_values(bel_resource=bel_resource, mapping=_optional_namespace_entries_mapping,
                         values=namespace_insert_values)

    return namespace_insert_values


_annotation_mapping = {
    'name': ('Citation', 'NameString')
}


def _get_annotation_insert_values(bel_resource):
    annotation_insert_values = extract_shared_required(bel_resource, 'AnnotationDefinition')
    annotation_insert_values.update(extract_shared_optional(bel_resource, 'AnnotationDefinition'))
    update_insert_values(bel_resource=bel_resource, mapping=_annotation_mapping, values=annotation_insert_values)
    return annotation_insert_values


def not_resource_cachable(bel_resource):
    """Check if the BEL resource is cacheable.

    :param dict bel_resource: A dictionary returned by :func:`get_bel_resource`.
    """
    return bel_resource['Processing'].get('CacheableFlag') not in {'yes', 'Yes', 'True', 'true'}


def _clean_bel_namespace_values(bel_resource):
    bel_resource['Values'] = {
        name: (encoding if encoding else DEFAULT_BELNS_ENCODING)
        for name, encoding in bel_resource['Values'].items()
        if name
    }


def _normalize_url(graph: BELGraph, keyword: str) -> Optional[str]:  # FIXME move to utilities and unit test
    """Normalize a URL for the BEL graph."""
    if keyword == BEL_DEFAULT_NAMESPACE and BEL_DEFAULT_NAMESPACE not in graph.namespace_url:
        return BEL_DEFAULT_NAMESPACE_URL

    return graph.namespace_url.get(keyword)


class NamespaceManager(BaseManager):
    """Manages BEL namespaces."""

    def list_namespaces(self) -> List[Namespace]:
        """List all namespaces."""
        return self._list_model(Namespace)

    def count_namespaces(self) -> int:
        """Count the number of namespaces in the database."""
        return self._count_model(Namespace)

    def count_namespace_entries(self) -> int:
        """Count the number of namespace entries in the database."""
        return self._count_model(NamespaceEntry)

    def drop_namespaces(self):
        """Drop all namespaces."""
        self.session.query(NamespaceEntry).delete()
        self.session.query(Namespace).delete()
        self.session.commit()

    def drop_namespace_by_url(self, url: str) -> None:
        """Drop the namespace at the given URL.

        Won't work if the edge store is in use.

        :param url: The URL of the namespace to drop
        """
        namespace = self.get_namespace_by_url(url)
        self.session.query(NamespaceEntry).filter(NamespaceEntry.namespace == namespace).delete()
        self.session.delete(namespace)
        self.session.commit()

    def get_namespace_by_url(self, url: str) -> Optional[Namespace]:
        """Look up a namespace by url."""
        return self.session.query(Namespace).filter(Namespace.url == url).one_or_none()

    def get_namespace_by_keyword_version(self, keyword: str, version: str) -> Optional[Namespace]:
        """Get a namespace with a given keyword and version."""
        filt = and_(Namespace.keyword == keyword, Namespace.version == version)
        return self.session.query(Namespace).filter(filt).one_or_none()

    def ensure_default_namespace(self) -> Namespace:
        """Get or create the BEL default namespace."""
        namespace = self.get_namespace_by_keyword_version(BEL_DEFAULT_NAMESPACE, BEL_DEFAULT_NAMESPACE_VERSION)

        if namespace is None:
            namespace = Namespace(
                name='BEL Default Namespace',
                contact='charles.hoyt@scai.fraunhofer.de',
                keyword=BEL_DEFAULT_NAMESPACE,
                version=BEL_DEFAULT_NAMESPACE_VERSION,
                url=BEL_DEFAULT_NAMESPACE_URL,
            )

            for name in set(chain(pmod_mappings, gmod_mappings, activity_mapping, compartment_mapping)):
                entry = NamespaceEntry(name=name, namespace=namespace)
                self.session.add(entry)

            self.session.add(namespace)
            self.session.commit()

        return namespace

    def get_or_create_namespace(self, url: str) -> Union[Namespace, Dict]:
        """Insert the namespace file at the given location to the cache.

        If not cachable, returns the dict of the values of this namespace.

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
            log.debug('loaded uncached namespace: %s (%d)', url, len(values))
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

    def get_namespace_by_keyword_pattern(self, keyword: str, pattern: str) -> Optional[Namespace]:
        """Get a namespace with a given keyword and pattern."""
        filt = and_(Namespace.keyword == keyword, Namespace.pattern == pattern)
        return self.session.query(Namespace).filter(filt).one_or_none()

    def ensure_regex_namespace(self, keyword: str, pattern: str) -> Namespace:
        """Get or create a regular expression namespace.

        :param keyword: The keyword of a regular expression namespace
        :param pattern: The pattern for a regular expression namespace
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

    def get_namespace_entry(self, url: str, name: str) -> Optional[NamespaceEntry]:
        """Get a given NamespaceEntry object.

        :param url: The url of the namespace source
        :param name: The value of the namespace from the given url's document
        """
        entry_filter = and_(Namespace.url == url, NamespaceEntry.name == name)
        result = self.session.query(NamespaceEntry).join(Namespace).filter(entry_filter).all()

        if 0 == len(result):
            return

        if 1 < len(result):
            log.warning('result for get_namespace_entry is too long. Returning first of %s', [str(r) for r in result])

        return result[0]

    def get_entity_by_identifier(self, url: str, identifier: str) -> Optional[NamespaceEntry]:
        """Get a given entity by its url/identifier combination."""
        entry_filter = and_(Namespace.url == url, NamespaceEntry.identifier == identifier)
        return self.session.query(NamespaceEntry).join(Namespace).filter(entry_filter).one_or_none()

    def get_or_create_regex_namespace_entry(self, namespace: str, pattern: str, name: str) -> NamespaceEntry:
        """Get a namespace entry from a regular expression.

        Need to commit after!

        :param namespace: The name of the namespace
        :param pattern: The regular expression pattern for the namespace
        :param name: The entry to get
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

    def list_annotations(self) -> List[Namespace]:
        """List all annotations."""
        return self.session.query(Namespace).filter(Namespace.is_annotation).all()

    def count_annotations(self) -> int:
        """Count the number of annotations in the database."""
        return self.session.query(Namespace).filter(Namespace.is_annotation).count()

    def count_annotation_entries(self) -> int:
        """Count the number of annotation entries in the database."""
        return self.session.query(NamespaceEntry).filter(NamespaceEntry.is_annotation).count()

    def get_or_create_annotation(self, url: str) -> Namespace:
        """Insert the namespace file at the given location to the cache.

        :raises: pybel.resources.exc.ResourceError
        """
        result = self.get_namespace_by_url(url)

        if result is not None:
            return result

        t = time.time()

        bel_resource = get_bel_resource(url)

        result = Namespace(
            url=url,
            is_annotation=True,
            **_get_annotation_insert_values(bel_resource)
        )
        result.entries = [
            NamespaceEntry(name=name, identifier=label)
            for name, label in bel_resource['Values'].items()
            if name
        ]

        self.session.add(result)
        self.session.commit()

        log.info('inserted annotation: %s (%d terms in %.2f seconds)', url, len(bel_resource['Values']),
                 time.time() - t)

        return result

    def get_annotation_entry_names(self, url: str) -> Set[str]:
        """Return a dict of annotations and their labels for the given annotation file.

        :param url: the location of the annotation file
        """
        annotation = self.get_or_create_annotation(url)
        return {
            x.name
            for x in self.session.query(NamespaceEntry.name).filter(NamespaceEntry.namespace == annotation)
        }

    def get_namespace_encoding(self, url: str) -> Mapping[str, str]:
        annotation = self.get_or_create_annotation(url)
        return dict(self.session.query(NamespaceEntry.name, NamespaceEntry.encoding).filter(
            NamespaceEntry.namespace == annotation))

    def get_annotation_entries_by_names(self, url: str, names: Iterable[str]) -> List[NamespaceEntry]:
        """Get annotation entries by URL and names.

        :param url: The url of the annotation source
        :param names: The names of the annotation entries from the given url's document
        """
        annotation_filter = and_(Namespace.url == url, NamespaceEntry.name.in_(names))
        return self.session.query(NamespaceEntry).join(Namespace).filter(annotation_filter).all()


class NetworkManager(NamespaceManager):
    """Groups functions for inserting and querying networks in the database's network store."""

    def count_networks(self) -> int:
        """Count the networks in the database."""
        return self._count_model(Network)

    def list_networks(self) -> List[Network]:
        """List all networks in the database."""
        return self._list_model(Network)

    def list_recent_networks(self) -> List[Network]:
        """List the most recently created version of each network (by name)."""
        most_recent_times = (
            self.session
            .query(
                Network.name.label('network_name'),
                func.max(Network.created).label('max_created')
            )
            .group_by(Network.name)
            .subquery('most_recent_times')
        )

        and_condition = and_(
            most_recent_times.c.network_name == Network.name,
            most_recent_times.c.max_created == Network.created
        )

        most_recent_networks = self.session.query(Network).join(most_recent_times, and_condition)

        return most_recent_networks.all()

    def has_name_version(self, name: str, version: str) -> bool:
        """Check if there exists a network with the name/version combination in the database."""
        return self.session.query(exists().where(and_(Network.name == name, Network.version == version))).scalar()

    def drop_networks(self) -> None:
        """Drop all networks."""
        for network in self.session.query(Network).all():
            self.drop_network(network)

    def drop_network_by_id(self, network_id: int) -> None:
        """Drop a network by its database identifier."""
        network = self.session.query(Network).get(network_id)
        self.drop_network(network)

    def drop_network(self, network: Network) -> None:
        """Drop a network, while also cleaning up any edges that are no longer part of any network."""
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

    def query_singleton_edges_from_network(self, network: Network) -> sqlalchemy.orm.query.Query:
        """Return a query selecting all edge ids that only belong to the given network."""
        ne1 = aliased(network_edge, name='ne1')
        ne2 = aliased(network_edge, name='ne2')
        singleton_edge_ids_for_network = (
            self.session
                .query(ne1.c.edge_id)
                .outerjoin(ne2, and_(
                ne1.c.edge_id == ne2.c.edge_id,
                ne1.c.network_id != ne2.c.network_id
            ))
                .filter(and_(
                ne1.c.network_id == network.id,
                ne2.c.edge_id == None  # noqa: E711
            ))
        )
        return singleton_edge_ids_for_network

    def get_network_versions(self, name: str) -> Set[str]:
        """Return all of the versions of a network with the given name."""
        return {
            version
            for version, in self.session.query(Network.version).filter(Network.name == name).all()
        }

    def get_network_by_name_version(self, name: str, version: str) -> Optional[Network]:
        """Load the network with the given name and version if it exists."""
        name_version_filter = and_(Network.name == name, Network.version == version)
        network = self.session.query(Network).filter(name_version_filter).one_or_none()
        return network

    def get_graph_by_name_version(self, name: str, version: str) -> Optional[BELGraph]:
        """Load the BEL graph with the given name, or allows for specification of version."""
        network = self.get_network_by_name_version(name, version)

        if network is None:
            return

        return network.as_bel()

    def get_networks_by_name(self, name: str) -> List[Network]:
        """Get all networks with the given name. Useful for getting all versions of a given network."""
        return self.session.query(Network).filter(Network.name.like(name)).all()

    def get_most_recent_network_by_name(self, name: str) -> Optional[Network]:
        """Get the most recently created network with the given name."""
        return self.session.query(Network).filter(Network.name == name).order_by(Network.created.desc()).first()

    def get_graph_by_most_recent(self, name: str) -> Optional[BELGraph]:
        """Get the most recently created network with the given name as a :class:`pybel.BELGraph`."""
        network = self.get_most_recent_network_by_name(name)

        if network is None:
            return

        return network.as_bel()

    def get_network_by_id(self, network_id: int) -> Network:
        """Get a network from the database by its identifier."""
        return self.session.query(Network).get(network_id)

    def get_graph_by_id(self, network_id: int) -> BELGraph:
        """Get a network from the database by its identifier and converts it to a BEL graph."""
        network = self.get_network_by_id(network_id)
        log.debug('converting network [id=%d] %s to bel graph', network_id, network)
        return network.as_bel()

    def get_networks_by_ids(self, network_ids: Iterable[int]) -> List[Network]:
        """Get a list of networks with the given identifiers.

        Note: order is not necessarily preserved.
        """
        log.debug('getting networks by identifiers: %s', network_ids)
        return self.session.query(Network).filter(Network.id_in(network_ids)).all()

    def get_graphs_by_ids(self, network_ids: Iterable[int]) -> List[BELGraph]:
        """Get a list of networks with the given identifiers and converts to BEL graphs."""
        rv = [
            self.get_graph_by_id(network_id)
            for network_id in network_ids
        ]
        log.debug('returning graphs for network identifiers: %s', network_ids)
        return rv

    def get_graph_by_ids(self, network_ids: List[int]) -> BELGraph:
        """Get a combine BEL Graph from a list of network identifiers."""
        if len(network_ids) == 1:
            return self.get_graph_by_id(network_ids[0])

        log.debug('getting graph by identifiers: %s', network_ids)
        graphs = self.get_graphs_by_ids(network_ids)

        log.debug('getting union of graphs: %s', network_ids)
        rv = union(graphs)

        return rv


class InsertManager(NamespaceManager, LookupManager):
    """Manages inserting data into the edge store."""

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

    def insert_graph(self, graph: BELGraph, store_parts: bool = True, use_tqdm: bool = False) -> Network:
        """Insert a graph in the database and returns the corresponding Network model.

        :raises: pybel.resources.exc.ResourceError
        """
        if not graph.name:
            raise ValueError('Can not upload a graph without a name')

        if not graph.version:
            raise ValueError('Can not upload a graph without a version')

        log.debug('inserting %s v%s', graph.name, graph.version)

        t = time.time()

        self.ensure_default_namespace()

        namespace_urls = graph.namespace_url.values()
        if use_tqdm:
            namespace_urls = tqdm(namespace_urls, desc='namespaces')

        for namespace_url in namespace_urls:
            if namespace_url not in graph.uncached_namespaces:
                self.get_or_create_namespace(namespace_url)

        for keyword, pattern in graph.namespace_pattern.items():
            self.ensure_regex_namespace(keyword, pattern)

        annotation_urls = graph.annotation_url.values()
        if use_tqdm:
            annotation_urls = tqdm(annotation_urls, desc='annotations')

        for annotation_url in annotation_urls:
            self.get_or_create_annotation(annotation_url)

        network = Network(**{
            key: value
            for key, value in graph.document.items()
            if key in METADATA_INSERT_KEYS
        })

        network.store_bel(graph)

        if store_parts:
            network.nodes, network.edges = self._store_graph_parts(graph, use_tqdm=use_tqdm)

        self.session.add(network)
        self.session.commit()

        log.info('inserted %s v%s in %.2f seconds', graph.name, graph.version, time.time() - t)

        return network

    def _store_graph_parts(self, graph: BELGraph, use_tqdm: bool = False) -> Tuple[List[Node], List[Edge]]:
        """Store the given graph into the edge store.

        :raises: pybel.resources.exc.ResourceError
        :raises: EdgeAddError
        """
        log.debug('inserting %s into edge store', graph)
        log.debug('building node models')
        node_model_build_start = time.time()

        nodes = list(graph)
        if use_tqdm:
            nodes = tqdm(nodes, total=graph.number_of_nodes(), desc='nodes')

        node_model = {}
        for node in nodes:
            namespace = node.get(NAMESPACE)

            if graph.skip_storing_namespace(namespace):
                continue  # already know this node won't be cached

            node_object = self.get_or_create_node(graph, node)

            if node_object is None:
                log.warning('can not add node %s', node)
                continue

            node_model[node] = node_object

        node_models = list(node_model.values())
        log.debug('built %d node models in %.2f seconds', len(node_models), time.time() - node_model_build_start)

        node_model_commit_start = time.time()
        self.session.add_all(node_models)
        self.session.commit()
        log.debug('stored %d node models in %.2f seconds', len(node_models), time.time() - node_model_commit_start)

        log.debug('building edge models')
        edge_model_build_start = time.time()

        edges = graph.edges(keys=True, data=True)
        if use_tqdm:
            edges = tqdm(edges, total=graph.number_of_edges(), desc='edges')

        edge_models = list(self._get_edge_models(graph, node_model, edges))

        log.debug('built %d edge models in %.2f seconds', len(edge_models), time.time() - edge_model_build_start)

        edge_model_commit_start = time.time()
        self.session.add_all(edge_models)
        self.session.commit()
        log.debug('stored %d edge models in %.2f seconds', len(edge_models), time.time() - edge_model_commit_start)

        return node_models, edge_models

    def _get_edge_models(self, graph: BELGraph, tuple_model: Mapping[BaseEntity, Node], edges):
        for u, v, key, data in edges:
            source = tuple_model.get(u)
            if source is None or source.sha512 not in self.object_cache_node:
                log.debug('skipping uncached source node: %s', u)
                continue

            target = tuple_model.get(v)
            if target is None or target.sha512 not in self.object_cache_node:
                log.debug('skipping uncached target node: %s', v)
                continue

            relation = data[RELATION]

            if relation in UNQUALIFIED_EDGES:
                try:
                    edge = self._add_unqualified_edge(
                        source=source,
                        target=target,
                        bel=graph.edge_to_bel(u, v, data),
                        key=key,
                        data=data,
                    )
                    if edge is None:
                        continue
                except Exception as e:
                    self.session.rollback()
                    log.exception('error storing edge in database. edge data: %s', data)
                    raise EdgeAddError(e, u, v, key, data) from e
                else:
                    yield edge

            elif EVIDENCE not in data or CITATION not in data:
                continue

            elif CITATION_TYPE not in data[CITATION] or CITATION_REFERENCE not in data[CITATION]:
                continue

            else:
                try:
                    bel = graph.edge_to_bel(u, v, data)
                    edge = self._add_qualified_edge(
                        graph=graph,
                        source=source,
                        target=target,
                        key=key,
                        bel=bel,
                        data=data,
                    )
                    if edge is None:
                        continue
                except Exception as e:
                    self.session.rollback()
                    log.exception('error storing edge in database. edge data: %s', data)
                    raise EdgeAddError(e, u, v, key, data) from e
                else:
                    yield edge

    @staticmethod
    def _iter_from_annotations_dict(graph: BELGraph,
                                    annotations_dict: AnnotationsDict,
                                    ) -> Iterable[Tuple[str, Set[str]]]:
        """Iterate over the key/value pairs in this edge data dictionary normalized to their source URLs."""
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

    def _get_annotation_entries_from_data(self, graph: BELGraph, data: EdgeData) -> Optional[List[NamespaceEntry]]:
        """Get the annotation entries from an edge data dictionary."""
        annotations_dict = data.get(ANNOTATIONS)
        if annotations_dict is not None:
            return [
                entry
                for url, names in self._iter_from_annotations_dict(graph, annotations_dict=annotations_dict)
                for entry in self.get_annotation_entries_by_names(url, names)
            ]

    def _add_qualified_edge(self, graph: BELGraph, source: Node, target: Node, key: str, bel: str, data: EdgeData):
        """Add a qualified edge to the network."""
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

        return self.get_or_create_edge(
            source=source,
            target=target,
            relation=data[RELATION],
            bel=bel,
            sha512=key,
            data=data,
            evidence=evidence,
            properties=properties,
            annotations=annotations,
        )

    def _add_unqualified_edge(self, source: Node, target: Node, key: str, bel: str, data: EdgeData) -> Edge:
        """Add an unqualified edge to the network."""
        return self.get_or_create_edge(
            source=source,
            target=target,
            relation=data[RELATION],
            bel=bel,
            sha512=key,
            data=data,
        )

    def get_or_create_evidence(self, citation: Citation, text: str) -> Evidence:
        """Create an entry and object for given evidence if it does not exist."""
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
            sha512=sha512,
        )

        self.session.add(evidence)
        self.object_cache_evidence[sha512] = evidence
        return evidence

    def get_or_create_node(self, graph: BELGraph, node: BaseEntity) -> Optional[Node]:
        """Create an entry and object for given node if it does not exist."""
        sha512 = node.as_sha512()
        if sha512 in self.object_cache_node:
            return self.object_cache_node[sha512]

        node_model = self.get_node_by_hash(sha512)

        if node_model is not None:
            self.object_cache_node[sha512] = node_model
            return node_model

        node_model = Node._start_from_base_entity(node)

        namespace = node.get(NAMESPACE)
        if namespace is None:
            pass

        elif namespace in graph.namespace_url:
            url = graph.namespace_url[namespace]
            name = node[NAME]
            entry = self.get_namespace_entry(url, name)

            if entry is None:
                log.debug('skipping node with identifier %s: %s', url, name)
                return

            self.session.add(entry)
            node_model.namespace_entry = entry

        elif namespace in graph.namespace_pattern:
            name = node[NAME]
            pattern = graph.namespace_pattern[namespace]
            entry = self.get_or_create_regex_namespace_entry(namespace, pattern, name)

            self.session.add(entry)
            node_model.namespace_entry = entry

        else:
            log.warning("No reference in BELGraph for namespace: {}".format(node[NAMESPACE]))
            return

        if VARIANTS in node or FUSION in node:
            node_model.is_variant = True
            node_model.has_fusion = FUSION in node

            modifications = self.get_or_create_modification(graph, node)

            if modifications is None:
                log.warning('could not create %s because had an uncachable modification', node.as_bel())
                return

            node_model.modifications = modifications

        self.session.add(node_model)
        self.object_cache_node[sha512] = node_model
        return node_model

    def drop_nodes(self) -> None:
        """Drop all nodes in the database."""
        t = time.time()

        self.session.query(Node).delete()
        self.session.commit()

        log.info('dropped all nodes in %.2f seconds', time.time() - t)

    def drop_edges(self) -> None:
        """Drop all edges in the database."""
        t = time.time()

        self.session.query(Edge).delete()
        self.session.commit()

        log.info('dropped all edges in %.2f seconds', time.time() - t)

    def get_or_create_edge(self,
                           source: Node,
                           target: Node,
                           relation: str,
                           bel: str,
                           sha512: str,
                           data: EdgeData,
                           evidence: Optional[Evidence] = None,
                           annotations: Optional[List[NamespaceEntry]] = None,
                           properties: Optional[List[Property]] = None,
                           ) -> Edge:
        """Create an edge if it does not exist, or return it if it does.

        :param source: Source node of the relation
        :param target: Target node of the relation
        :param relation: Type of the relation between source and target node
        :param bel: BEL statement that describes the relation
        :param sha512: The SHA512 hash of the edge as a string
        :param data: The PyBEL data dictionary
        :param Evidence evidence: Evidence object that proves the given relation
        :param properties: List of all properties that belong to the edge
        :param annotations: List of all annotations that belong to the edge
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
            data=json.dumps(data),
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

    def get_or_create_citation(self,
                               reference: str,
                               type: Optional[str] = None,
                               name: Optional[str] = None,
                               title: Optional[str] = None,
                               volume: Optional[str] = None,
                               issue: Optional[str] = None,
                               pages: Optional[str] = None,
                               date: Optional[str] = None,
                               first: Optional[str] = None,
                               last: Optional[str] = None,
                               authors: Union[None, List[str]] = None,
                               ) -> Citation:
        """Create a citation if it does not exist, or return it if it does.

        :param type: Citation type (e.g. PubMed)
        :param reference: Identifier of the given citation (e.g. PubMed id)
        :param name: Name of the publication
        :param title: Title of article
        :param volume: Volume of publication
        :param issue: Issue of publication
        :param pages: Pages of issue
        :param date: Date of publication in ISO 8601 (YYYY-MM-DD) format
        :param first: Name of first author
        :param last: Name of last author
        :param authors: Either a list of authors separated by |, or an actual list of authors
        """
        if type is None:
            type = CITATION_TYPE_PUBMED

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
            for author in authors:
                author_model = self.get_or_create_author(author)
                if author_model not in citation.authors:
                    citation.authors.append(author_model)

        self.session.add(citation)
        self.object_cache_citation[sha512] = citation
        return citation

    def get_or_create_author(self, name: str) -> Author:
        """Get an author by name, or creates one if it does not exist."""
        author = self.object_cache_author.get(name)

        if author is not None:
            self.session.add(author)
            return author

        author = self.get_author_by_name(name)

        if author is not None:
            self.object_cache_author[name] = author
            return author

        author = self.object_cache_author[name] = Author.from_name(name=name)
        self.session.add(author)
        return author

    def get_modification_by_hash(self, sha512: str) -> Optional[Modification]:
        """Get a modification by a SHA512 hash."""
        return self.session.query(Modification).filter(Modification.sha512 == sha512).one_or_none()

    def get_or_create_modification(self, graph: BELGraph, node: BaseEntity) -> Optional[List[Modification]]:
        """Create a list of node modification objects that belong to the node described by node_data.

        Return ``None`` if the list can not be constructed, and the node should also be skipped.

        :param dict node: Describes the given node and contains is_variant information
        :return: A list of modification objects belonging to the given node
        """
        modification_list = []
        if FUSION in node:
            mod_type = FUSION
            node = node[FUSION]
            p3_namespace_url = graph.namespace_url[node[PARTNER_3P][NAMESPACE]]

            if p3_namespace_url in graph.uncached_namespaces:
                log.warning('uncached namespace %s in fusion()', p3_namespace_url)
                return

            p3_name = node[PARTNER_3P][NAME]
            p3_namespace_entry = self.get_namespace_entry(p3_namespace_url, p3_name)

            if p3_namespace_entry is None:
                log.warning('Could not find namespace entry %s %s', p3_namespace_url, p3_name)
                return  # FIXME raise?

            p5_namespace_url = graph.namespace_url[node[PARTNER_5P][NAMESPACE]]

            if p5_namespace_url in graph.uncached_namespaces:
                log.warning('uncached namespace %s in fusion()', p5_namespace_url)
                return

            p5_name = node[PARTNER_5P][NAME]
            p5_namespace_entry = self.get_namespace_entry(p5_namespace_url, p5_name)

            if p5_namespace_entry is None:
                log.warning('Could not find namespace entry %s %s', p5_namespace_url, p5_name)
                return  # FIXME raise?

            fusion_dict = {
                'type': mod_type,
                'p3_partner': p3_namespace_entry,
                'p5_partner': p5_namespace_entry,
            }

            node_range_3p = node.get(RANGE_3P)
            if node_range_3p and FUSION_REFERENCE in node_range_3p:
                fusion_dict.update({
                    'p3_reference': node_range_3p[FUSION_REFERENCE],
                    'p3_start': node_range_3p[FUSION_START],
                    'p3_stop': node_range_3p[FUSION_STOP],
                })

            node_range_5p = node.get(RANGE_5P)
            if node_range_5p and FUSION_REFERENCE in node_range_5p:
                fusion_dict.update({
                    'p5_reference': node_range_5p[FUSION_REFERENCE],
                    'p5_start': node_range_5p[FUSION_START],
                    'p5_stop': node_range_5p[FUSION_STOP],
                })

            modification_list.append(fusion_dict)

        else:
            for variant in node[VARIANTS]:
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

    def get_property_by_hash(self, property_hash: str) -> Optional[Property]:
        """Get a property by its hash if it exists."""
        return self.session.query(Property).filter(Property.sha512 == property_hash).one_or_none()

    def _make_property_from_dict(self, property_def: Dict) -> Property:
        """Build an edge property from a dictionary."""
        property_hash = hash_dump(property_def)

        edge_property_model = self.object_cache_property.get(property_hash)
        if edge_property_model is None:
            edge_property_model = self.get_property_by_hash(property_hash)

            if not edge_property_model:
                property_def['sha512'] = property_hash
                edge_property_model = Property(**property_def)

            self.object_cache_property[property_hash] = edge_property_model

        return edge_property_model

    # TODO make for just single property then loop with other fn.
    def get_or_create_properties(self, graph: BELGraph, edge_data: EdgeData) -> Optional[List[Property]]:
        """Create a list of edge subject/object property models.

        Return None if the property cannot be constructed due to missing cache entries.

        :return: A list of all subject and object properties of the edge
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

                if modifier == TRANSLOCATION:
                    for effect_type, effect_value in participant_data.get(EFFECT, {}).items():
                        tmp_dict = deepcopy(modifier_property_dict)
                        tmp_dict['relative_key'] = effect_type

                        if NAMESPACE not in effect_value:
                            tmp_dict['propValue'] = effect_value
                            raise ValueError('shouldnt use propValue')
                        else:
                            effect_namespace = effect_value[NAMESPACE]

                            if effect_namespace in graph.namespace_url:
                                namespace_url = graph.namespace_url[effect_namespace]
                            elif effect_namespace == BEL_DEFAULT_NAMESPACE:
                                namespace_url = BEL_DEFAULT_NAMESPACE_URL
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

    def count_citations(self) -> int:
        """Count the number of citations stored in the database."""
        return self._count_model(Citation)

    def list_citations(self) -> List[Citation]:
        """List the citations in the database."""
        return self._list_model(Citation)


class Manager(_Manager):
    """A manager for the PyBEL database."""

    def __init__(self, connection=None, engine=None, session=None, **kwargs) -> None:
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

        super().__init__(engine=engine, session=session)
        self.create_all()
