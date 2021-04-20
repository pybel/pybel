# -*- coding: utf-8 -*-

"""The database manager for PyBEL.

Under the hood, PyBEL caches namespace and annotation files for quick recall on later use. The user doesn't need to
enable this option, but can specify a database location if they choose.
"""

import logging
import time
from typing import Iterable, List, Mapping, Optional, Set, Tuple

import pandas as pd
import requests
import sqlalchemy
from sqlalchemy import and_, exists, func
from sqlalchemy.orm import aliased
from tqdm.autonotebook import tqdm

from bel_resources import get_bel_resource
from .base_manager import BaseManager, build_engine_session
from .exc import EdgeAddError
from .lookup_manager import LookupManager
from .models import (
    Author, Citation, Edge, Evidence, Namespace, NamespaceEntry, Network, Node, edge_annotation, network_edge,
    network_node,
)
from .query_manager import QueryManager
from .utils import extract_shared_optional, extract_shared_required, update_insert_values
from ..constants import (
    ANNOTATIONS, CITATION, CITATION_TYPE_PUBMED, EVIDENCE, IDENTIFIER, METADATA_INSERT_KEYS, NAMESPACE, RELATION,
    SOURCE_MODIFIER, TARGET_MODIFIER, UNQUALIFIED_EDGES, belns_encodings, get_cache_connection,
)
from ..dsl import BaseConcept, BaseEntity
from ..language import Entity
from ..struct.graph import AnnotationsDict, BELGraph
from ..struct.operations import union
from ..typing import EdgeData

__all__ = [
    'Manager',
    'NetworkManager',
]

logger = logging.getLogger(__name__)

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

    update_insert_values(
        bel_resource=bel_resource,
        mapping=_optional_namespace_entries_mapping,
        values=namespace_insert_values,
    )

    return namespace_insert_values


_annotation_mapping = {
    'name': ('Citation', 'NameString'),
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

    def _ensure_namespace_urls(
        self,
        urls: Iterable[str],
        use_tqdm: bool = True,
        is_annotation: bool = False,
    ) -> List[Namespace]:
        ext = 'belanno' if is_annotation else 'belns'

        rv = []
        url_to_namespace = {}
        url_to_values = {}
        url_to_name_to_id = {}

        tag = 'annotations' if is_annotation else 'namespaces'

        if use_tqdm:
            urls = tqdm(urls, desc=f'downloading {tag}')
        for url in urls:
            result = self.get_namespace_by_url(url)
            if result:
                rv.append(result)
                continue
            bel_resource = get_bel_resource(url)
            _clean_bel_namespace_values(bel_resource)
            url_to_values[url] = bel_resource['Values']

            if is_annotation:
                namespace_kwargs = _get_annotation_insert_values(bel_resource)
            else:
                namespace_kwargs = _get_namespace_insert_values(bel_resource)
            result = url_to_namespace[url] = Namespace(url=url, **namespace_kwargs)
            rv.append(result)
            if url.endswith(f'-names.{ext}'):
                mapping_url = url[:-len(f'-names.{ext}')] + f'.{ext}.mapping'
                try:
                    res = requests.get(mapping_url)
                    res.raise_for_status()
                except requests.exceptions.HTTPError:
                    logger.warning('No mappings found for %s', url)
                else:
                    mappings = res.json()
                    logger.debug('got %d mappings', len(mappings))
                    url_to_name_to_id[url] = {v: k for k, v in res.json().items()}

        self.session.add_all(url_to_namespace.values())
        self.session.commit()

        url_to_id = {url: namespace.id for url, namespace in url_to_namespace.items()}

        if not url_to_values:
            return rv

        rows = []
        it = url_to_values.items()
        if use_tqdm:
            it = tqdm(it, desc=f'making {tag} entry table')
        if is_annotation:
            for url, values in it:
                for name, identifier in values.items():
                    if not name:
                        continue
                    rows.append((url_to_id[url], name, None, identifier))  # TODO is this a fair assumption?
        else:
            for url, values in it:
                name_to_id = url_to_name_to_id.get(url, {})
                for name, encoding in values.items():
                    if not name:
                        continue
                    rows.append((url_to_id[url], name, encoding, name_to_id.get(name)))

        df = pd.DataFrame(rows, columns=['namespace_id', 'name', 'encoding', 'identifier'])
        logger.info('preparing sql objects for %s', tag)
        df.to_sql(NamespaceEntry.__tablename__, con=self.engine, if_exists='append', index=False)
        logger.info('committing %s', tag)
        start_commit_time = time.time()
        self.session.commit()
        logger.info('done committing %s after %.2f seconds', tag, time.time() - start_commit_time)

        return rv

    def get_or_create_namespace(self, url: str) -> Namespace:
        """Insert the namespace file at the given location to the cache.

        If not cachable, returns the dict of the values of this namespace.

        :raises: pybel.resources.exc.ResourceError
        """
        return self._ensure_namespace_urls([url])[0]

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
            logger.info('creating regex namespace: %s:%s', keyword, pattern)
            namespace = Namespace(
                keyword=keyword,
                pattern=pattern,
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
            logger.debug('could not find namespace entry for %s in url=%s', name, url)
            return

        if 1 < len(result):
            logger.warning(
                'result for get_namespace_entry is too long. Returning first of %s',
                [str(r) for r in result],
            )

        return result[0]

    def get_entity_by_identifier(self, url: str, identifier: str) -> Optional[NamespaceEntry]:
        """Get a given entity by its url/identifier combination."""
        entry_filter = and_(Namespace.url == url, NamespaceEntry.identifier == identifier)
        return self.session.query(NamespaceEntry).join(Namespace).filter(entry_filter).one_or_none()

    def get_or_create_regex_namespace_entry(self, *, pattern: str, concept: Entity) -> NamespaceEntry:
        """Get a namespace entry from a regular expression.

        Need to commit after!

        :param pattern: The regular expression pattern for the namespace
        :param concept: The prefix/identifier/name triple
        """
        namespace = self.ensure_regex_namespace(concept.namespace, pattern)

        n_filter = and_(Namespace.pattern == pattern, NamespaceEntry.name == concept.name)

        namespace_entry = self.session.query(NamespaceEntry).join(Namespace).filter(n_filter).one_or_none()

        if namespace_entry is None:
            namespace_entry = NamespaceEntry(
                namespace=namespace,
                name=concept.name,
                identifier=concept.identifier,
            )
            self.session.add(namespace_entry)

        return namespace_entry

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
        return self._ensure_namespace_urls([url], is_annotation=True)[0]

    def get_annotation_entries_by_names(self, url: str, entities: Iterable[Entity]) -> List[NamespaceEntry]:
        """Get annotation entries by URL and names.

        :param url: The url of the annotation source
        :param entities: The names of the annotation entries from the given url's document
        """
        names = [e.identifier if isinstance(e, Entity) else e for e in entities]
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
        most_recent_times = self.session.query(
            Network.name.label('network_name'),
            func.max(Network.created).label('max_created'),
        )

        most_recent_times = most_recent_times.group_by(Network.name).subquery('most_recent_times')

        and_condition = and_(
            most_recent_times.c.network_name == Network.name,
            most_recent_times.c.max_created == Network.created,
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
            synchronize_session=False,
        )

        # delete the edge-to-annotation mappings for the to-be-orphaned edges
        self.session.query(edge_annotation).filter(edge_annotation.c.edge_id.in_(edge_ids)).delete(
            synchronize_session=False,
        )

        # delete the edge-to-network mappings for this network
        self.session.query(network_edge).filter(network_edge.c.network_id == network.id).delete(
            synchronize_session=False,
        )

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
                .outerjoin(
                    ne2, and_(
                        ne1.c.edge_id == ne2.c.edge_id,
                        ne1.c.network_id != ne2.c.network_id,
                    ),
                )
                .filter(  # noqa: E131
                    and_(
                        ne1.c.network_id == network.id,
                        ne2.c.edge_id == None,  # noqa: E711
                    ),
                )
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
        logger.debug('converting network [id=%d] %s to bel graph', network_id, network)
        return network.as_bel()

    def get_networks_by_ids(self, network_ids: Iterable[int]) -> List[Network]:
        """Get a list of networks with the given identifiers.

        Note: order is not necessarily preserved.
        """
        logger.debug('getting networks by identifiers: %s', network_ids)
        return self.session.query(Network).filter(Network.id_in(network_ids)).all()

    def get_graphs_by_ids(self, network_ids: Iterable[int]) -> List[BELGraph]:
        """Get a list of networks with the given identifiers and converts to BEL graphs."""
        rv = [
            self.get_graph_by_id(network_id)
            for network_id in network_ids
        ]
        logger.debug('returning graphs for network identifiers: %s', network_ids)
        return rv

    def get_graph_by_ids(self, network_ids: List[int]) -> BELGraph:
        """Get a combine BEL Graph from a list of network identifiers."""
        if len(network_ids) == 1:
            return self.get_graph_by_id(network_ids[0])

        logger.debug('getting graph by identifiers: %s', network_ids)
        graphs = self.get_graphs_by_ids(network_ids)

        logger.debug('getting union of graphs: %s', network_ids)
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
        self.curie_to_citation = {}
        self.object_cache_author = {}

    def insert_graph(
        self,
        graph: BELGraph,
        use_tqdm: bool = True,
    ) -> Network:
        """Insert a graph in the database and returns the corresponding Network model.

        :raises: pybel.resources.exc.ResourceError
        """
        if not graph.name:
            raise ValueError('Can not upload a graph without a name')

        if not graph.version:
            raise ValueError('Can not upload a graph without a version')

        logger.debug('inserting %s v%s', graph.name, graph.version)

        t = time.time()

        namespace_urls = graph.namespace_url.values()
        self._ensure_namespace_urls(namespace_urls, use_tqdm=use_tqdm)
        for keyword, pattern in graph.namespace_pattern.items():
            self.ensure_regex_namespace(keyword, pattern)

        annotation_urls = graph.annotation_url.values()
        self._ensure_namespace_urls(annotation_urls, use_tqdm=use_tqdm, is_annotation=True)

        network = Network(**{
            key: value
            for key, value in graph.document.items()
            if key in METADATA_INSERT_KEYS
        })

        network.store_bel(graph)

        network.nodes, network.edges = self._store_graph_parts(graph, use_tqdm=use_tqdm)

        self.session.add(network)
        self.session.commit()

        logger.info('inserted %s v%s in %.2f seconds', graph.name, graph.version, time.time() - t)

        return network

    def _store_graph_parts(self, graph: BELGraph, use_tqdm: bool = False) -> Tuple[List[Node], List[Edge]]:
        """Store the given graph into the edge store.

        :raises: pybel.resources.exc.ResourceError
        :raises: EdgeAddError
        """
        logger.debug('inserting %s into edge store', graph)
        logger.debug('building node models')
        node_model_build_start = time.time()

        nodes = list(graph)
        if use_tqdm:
            nodes = tqdm(nodes, total=graph.number_of_nodes(), desc='nodes')

        node_model = {}
        for node in nodes:
            node_object = self.get_or_create_node(graph, node)

            if node_object is None:
                logger.warning('can not add node %s', node)
                continue

            node_model[node] = node_object

        node_models = list(node_model.values())
        logger.debug('built %d node models in %.2f seconds', len(node_models), time.time() - node_model_build_start)

        node_model_commit_start = time.time()
        self.session.add_all(node_models)
        self.session.commit()
        logger.debug('stored %d node models in %.2f seconds', len(node_models), time.time() - node_model_commit_start)

        logger.debug('building edge models')
        edge_model_build_start = time.time()

        edges = graph.edges(keys=True, data=True)
        if use_tqdm:
            edges = tqdm(edges, total=graph.number_of_edges(), desc='edges')

        edge_models = list(self._get_edge_models(graph, node_model, edges))

        logger.debug('built %d edge models in %.2f seconds', len(edge_models), time.time() - edge_model_build_start)

        edge_model_commit_start = time.time()
        self.session.add_all(edge_models)
        self.session.commit()
        logger.debug('stored %d edge models in %.2f seconds', len(edge_models), time.time() - edge_model_commit_start)

        return node_models, edge_models

    def _get_edge_models(
        self,
        graph: BELGraph,
        tuple_model: Mapping[BaseEntity, Node],
        edges,
    ) -> Iterable[Edge]:
        for u, v, key, data in edges:
            source = tuple_model.get(u)
            if source is None or source.md5 not in self.object_cache_node:
                logger.warning('skipping uncached source node: %s', u)
                continue

            target = tuple_model.get(v)
            if target is None or target.md5 not in self.object_cache_node:
                logger.warning('skipping uncached target node: %s', v)
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
                    logger.exception('error storing edge in database. edge data: %s', data)
                    raise EdgeAddError(e, u, v, key, data) from e
                else:
                    yield edge

            elif EVIDENCE not in data or CITATION not in data:
                continue

            elif NAMESPACE not in data[CITATION] or IDENTIFIER not in data[CITATION]:
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
                    logger.exception('error storing edge in database. edge data: %s', data)
                    raise EdgeAddError(e, u, v, key, data)
                else:
                    yield edge

    @staticmethod
    def _iter_from_annotations_dict(
        graph: BELGraph,
        annotations_dict: AnnotationsDict,
    ) -> Iterable[Tuple[str, Set[Entity]]]:
        """Iterate over the key/value pairs in this edge data dictionary normalized to their source URLs."""
        for key, entities in annotations_dict.items():
            if key in graph.annotation_url:
                url = graph.annotation_url[key]
            elif key in graph.annotation_list:
                continue  # skip those
            elif key in graph.annotation_pattern:
                logger.debug('pattern annotation in database not implemented yet not implemented')  # FIXME
                continue
            else:
                raise ValueError('Graph resources does not contain keyword: {}'.format(key))

            yield url, set(entities)

    def _get_annotation_entries_from_data(self, graph: BELGraph, data: EdgeData) -> Optional[List[NamespaceEntry]]:
        """Get the annotation entries from an edge data dictionary."""
        annotations_dict = data.get(ANNOTATIONS)
        if annotations_dict is None:
            return
        rv = []
        for url, entities in self._iter_from_annotations_dict(graph, annotations_dict=annotations_dict):
            for entry in self.get_annotation_entries_by_names(url, entities):
                rv.append(entry)
        return rv

    def _add_qualified_edge(
        self,
        graph: BELGraph,
        source: Node,
        target: Node,
        key: str,
        bel: str,
        data: EdgeData,
    ) -> Optional[Edge]:
        """Add a qualified edge to the network."""
        citation_dict = data[CITATION]
        citation = self.get_or_create_citation(
            namespace=citation_dict[NAMESPACE],
            identifier=citation_dict[IDENTIFIER],
        )
        evidence = self.get_or_create_evidence(citation, data[EVIDENCE])
        annotations = self._get_annotation_entries_from_data(graph, data)

        return self.get_or_create_edge(
            source=source,
            target=target,
            relation=data[RELATION],
            bel=bel,
            md5=key,
            data=data,
            evidence=evidence,
            annotations=annotations,
        )

    def _add_unqualified_edge(self, source: Node, target: Node, key: str, bel: str, data: EdgeData) -> Edge:
        """Add an unqualified edge to the network."""
        return self.get_or_create_edge(
            source=source,
            target=target,
            relation=data[RELATION],
            bel=bel,
            md5=key,
            data=data,
        )

    def get_or_create_evidence(self, citation: Citation, text: str) -> Evidence:
        """Create an entry and object for given evidence if it does not exist."""
        evidence_tuple = citation.db, citation.db_id, text
        if evidence_tuple in self.object_cache_evidence:
            evidence = self.object_cache_evidence[evidence_tuple]
            self.session.add(evidence)
            return evidence

        evidence = self.get_evidence_by_citation_text(citation, text)
        if evidence is not None:
            self.object_cache_evidence[evidence_tuple] = evidence
            return evidence

        self.object_cache_evidence[evidence_tuple] = evidence = Evidence(
            citation=citation,
            text=text,
        )

        self.session.add(evidence)
        return evidence

    def get_or_create_node(self, graph: BELGraph, node: BaseEntity) -> Optional[Node]:
        """Create an entry and object for given node if it does not exist."""
        node_md5 = node.md5
        if node_md5 in self.object_cache_node:
            return self.object_cache_node[node_md5]

        node_model = self.get_node_by_hash(node_md5)
        if node_model is not None:
            self.object_cache_node[node_md5] = node_model
            return node_model

        node_model = Node._start_from_base_entity(node)

        if not isinstance(node, BaseConcept):
            self.session.add(node_model)
            self.object_cache_node[node_md5] = node_model
            return node_model

        if node.namespace in graph.namespace_url:
            url = graph.namespace_url[node.namespace]
            name = node.name
            entry = self.get_namespace_entry(url, name)

            if entry is None:
                logger.debug('skipping node with entity %s:%s from url=%s', node.namespace, name, url)
                return

            self.session.add(entry)
            node_model.namespace_entry = entry

        elif node.namespace in graph.namespace_pattern:
            entry = self.get_or_create_regex_namespace_entry(
                concept=node.entity,
                pattern=graph.namespace_pattern[node.namespace],
            )
            self.session.add(entry)
            node_model.namespace_entry = entry

        else:
            logger.warning("No reference in BELGraph for namespace: {}".format(node.namespace))
            return

        self.session.add(node_model)
        self.object_cache_node[node_md5] = node_model
        return node_model

    def drop_nodes(self) -> None:
        """Drop all nodes in the database."""
        t = time.time()

        self.session.query(Node).delete()
        self.session.commit()

        logger.info('dropped all nodes in %.2f seconds', time.time() - t)

    def drop_edges(self) -> None:
        """Drop all edges in the database."""
        t = time.time()

        self.session.query(Edge).delete()
        self.session.commit()

        logger.info('dropped all edges in %.2f seconds', time.time() - t)

    def get_or_create_edge(
        self,
        source: Node,
        target: Node,
        relation: str,
        bel: str,
        md5: str,
        data: EdgeData,
        evidence: Optional[Evidence] = None,
        annotations: Optional[List[NamespaceEntry]] = None,
    ) -> Edge:
        """Create an edge if it does not exist, or return it if it does.

        :param source: Source node of the relation
        :param target: Target node of the relation
        :param relation: Type of the relation between source and target node
        :param bel: BEL statement that describes the relation
        :param md5: The MD5 hash of the edge as a string
        :param data: The PyBEL data dictionary
        :param evidence: Evidence object that proves the given relation
        :param annotations: List of all annotations that belong to the edge
        """
        if md5 in self.object_cache_edge:
            edge = self.object_cache_edge[md5]
            self.session.add(edge)
            return edge

        edge = self.get_edge_by_hash(md5)

        if edge is not None:
            self.object_cache_edge[md5] = edge
            return edge

        edge = Edge(
            source=source,
            source_modifier=data.get(SOURCE_MODIFIER),
            target=target,
            target_modifier=data.get(TARGET_MODIFIER),
            relation=relation,
            bel=bel,
            md5=md5,
            data=data,
        )

        if evidence is not None:
            edge.evidence = evidence
        if annotations is not None:
            edge.annotations = annotations

        self.session.add(edge)
        self.object_cache_edge[md5] = edge
        return edge

    def get_or_create_citation(
        self,
        *,
        identifier: str,
        namespace: Optional[str] = None,
    ) -> Citation:
        """Create a citation if it does not exist, or return it if it does.

        :param identifier: Identifier of the given citation (e.g. PubMed id)
        :param namespace: Citation type (defaults to PubMed)
        """
        if namespace is None:
            namespace = CITATION_TYPE_PUBMED

        citation_curie = f'{namespace}:{identifier}'
        if citation_curie in self.curie_to_citation:
            citation = self.curie_to_citation[citation_curie]
            self.session.add(citation)
            return citation

        citation = self.get_citation_by_reference(namespace, identifier)

        if citation is not None:
            self.curie_to_citation[citation_curie] = citation
            return citation

        self.curie_to_citation[citation_curie] = citation = Citation(db=namespace, db_id=identifier)
        self.session.add(citation)
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

        author = self.object_cache_author[name] = Author(name=name)
        self.session.add(author)
        return author


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

    def __init__(
        self,
        connection: Optional[str] = None,
        engine=None,
        session=None,
        **kwargs
    ) -> None:
        """Create a connection to database and a persistent session using SQLAlchemy.

        A custom default can be set as an environment variable with the name :data:`pybel.constants.PYBEL_CONNECTION`,
        using an `RFC-1738 <http://rfc.net/rfc1738.html>`_ string. For example, a MySQL string can be given with the
        following form:

        :code:`mysql+pymysql://<username>:<password>@<host>/<dbname>?charset=utf8[&<options>]`

        A SQLite connection string can be given in the form:

        ``sqlite:///~/Desktop/cache.db``

        Further options and examples can be found on the SQLAlchemy documentation on
        `engine configuration <http://docs.sqlalchemy.org/en/latest/core/engines.html>`_.

        :param connection: An RFC-1738 database connection string. If ``None``, tries to load from the
         environment variable ``PYBEL_CONNECTION`` then from the config file ``~/.config/pybel/config.json`` whose
         value for ``PYBEL_CONNECTION`` defaults to :data:`pybel.constants.DEFAULT_CACHE_CONNECTION`.
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
