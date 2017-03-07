# -*- coding: utf-8 -*-

"""

This module contains the Graph Cache Manager

"""

import logging

from . import models
from .base_cache import BaseCacheManager
from .utils import parse_datetime
from ..canonicalize import decanonicalize_edge, decanonicalize_node
from ..constants import *
from ..graph import BELGraph
from ..io import to_bytes, from_bytes
from ..parser.utils import subdict_matches

try:
    import cPickle as pickle
except ImportError:
    import pickle

log = logging.getLogger(__name__)


class GraphCacheManager(BaseCacheManager):
    def insert_graph(self, graph, store_parts=False):
        """Stores a graph in the database

        :param graph: a BEL network
        :type graph: pybel.BELGraph
        :param store_parts: Should the graph be stored in the Edge Store?
        :type store_parts: bool
        :return: A Network object
        :rtype: models.Network
        """
        graph_bytes = to_bytes(graph)

        network = models.Network(blob=graph_bytes, **graph.document)

        if store_parts:
            self.store_graph_parts(network, graph)

        self.session.add(network)
        self.session.commit()

        return network

    def store_graph_parts(self, network, graph):
        """Stores the given graph into the Edge Store

        :param network: A SQLAlchemy PyBEL Network objet
        :type network: models.Network
        :param graph: A BEL Graph
        :type graph: pybel.BELGraph
        """
        nc = {node: self.get_or_create_node(graph, node) for node in graph.nodes_iter()}

        for u, v, k, data in graph.edges_iter(data=True, keys=True):
            source, target = nc[u], nc[v]

            if CITATION not in data or EVIDENCE not in data:
                continue

            citation = self.get_or_create_citation(**data[CITATION])
            evidence = self.get_or_create_evidence(citation, data[EVIDENCE])

            bel = decanonicalize_edge(graph, u, v, k)
            edge = models.Edge(
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
                    edge.annotations.append(self.get_bel_annotation_entry(url, value))

            network.edges.append(edge)

    def get_bel_annotation_entry(self, url, value):
        """Gets a given AnnotationEntry

        :param url: The url of the annotation source
        :type url: str
        :param value: The value of the annotation from the given url's document
        :type value: str
        :return: An AnnotationEntry object
        :rtype: models.AnnotationEntry
        """
        annotation = self.session.query(models.Annotation).filter_by(url=url).one()
        return self.session.query(models.AnnotationEntry).filter_by(annotation=annotation, name=value).one()

    def get_or_create_evidence(self, citation, text):
        """Creates entry for given evidence if it does not exist.

        :param citation: Citation object obtained from get_or_create_citation()
        :type citation: models.Citation
        :param text: Evidence text
        :type text: str
        :return: An Evidence object
        :rtype: models.Evidence
        """

        result = self.session.query(models.Evidence).filter_by(text=text).one_or_none()

        if result is None:
            result = models.Evidence(text=text, citation=citation)
            self.session.add(result)
            self.session.flush()
            # self.session.commit()  # TODO remove?

        return result

    def get_or_create_node(self, graph, node):
        """Creates entry for given node if it does not exist.

        :param graph: A BEL network
        :type graph: pybel.BELGraph
        :param node: Key for the node to insert.
        :type node: tuple
        :return: A Node object
        :rtype: models.Node
        """
        bel = decanonicalize_node(graph, node)
        blob = pickle.dumps(graph.node[node])

        result = self.session.query(models.Node).filter_by(bel=bel).one_or_none()

        if result is None:
            result = models.Node(bel=bel, blob=blob)
            self.session.add(result)

        return result

    def get_or_create_edge(self, source, target, evidence, bel, relation):
        """Creates entry for given edge if it does not exist.

        :param source: Source node of the relation
        :type source: models.Node
        :param target: Target node of the relation
        :type target: models.Node
        :param evidence: Evidence object that proves the given relation
        :type evidence: models.Evidence
        :param bel: BEL statement that describes the relation
        :type bel: str
        :param relation: Type of the relation between source and target node
        :type relation: str
        :return: An Edge object
        :rtype: models.Edge
        """
        result = self.session.query(models.Edge).filter_by(bel=bel).one_or_none()

        if result:
            return result

        result = models.Edge(source=source, target=target, relation=relation, evidence=evidence, bel=bel)

        return result

    def get_or_create_citation(self, type, name, reference, date=None, authors=None, comments=None):
        """Creates entry for given citation if it does not exist.

        :param type: Citation type (e.g. PubMed)
        :type type: str
        :param name: Title of the publication that is cited
        :type name: str
        :param reference: Identifier of the given citation (e.g. PubMed id)
        :type reference: str
        :param date: Date of publication
        :type date: date
        :param authors: List of authors separated by |
        :type authors: str
        :param comments: Comments on the citation
        :type comments: str
        :return: A Citation object
        :rtype: models.Citation
        """

        result = self.session.query(models.Citation).filter_by(type=type, reference=reference).one_or_none()

        if result is None:
            if date is not None:
                date = parse_datetime(date)

            result = models.Citation(type=type, name=name, reference=reference, date=date, comments=comments)

            if authors is not None:
                for author in authors.split('|'):
                    result.authors.append(self.get_or_create_author(author))

            self.session.add(result)

        return result

    def get_or_create_author(self, name):
        """Gets an author by name, or creates one

        :param name: An author's name
        :type name: str
        :return: An Author object
        :rtype: models.Author
        """
        result = self.session.query(models.Author).filter_by(name=name).one_or_none()

        if result:
            return result

        result = models.Author(name=name)
        self.session.add(result)

        return result

    def get_graph_versions(self, name):
        """Returns all of the versions of a graph with the given name"""
        return {x for x, in self.session.query(models.Network.version).filter(models.Network.name == name).all()}

    def get_graph(self, name, version=None):
        """Loads most recent graph, or allows for specification of version

        :param name: The name of the graph
        :type name: str
        :param version: The version string of the graph. If not specified, loads most recent graph added with this name
        :type version: None or str
        :return: A BEL Graph
        :rtype: pybel.BELGraph
        """
        if version is not None:
            n = self.session.query(models.Network).filter(models.Network.name == name,
                                                          models.Network.version == version).one()
        else:
            n = self.session.query(models.Network).filter(models.Network.name == name).order_by(
                models.Network.created.desc()).first()

        return from_bytes(n.blob)

    def get_graph_by_id(self, id):
        """Gets the graph from the database by its identifier

        :param id: The graph's database ID
        :type id: int
        :return: A Network object
        :rtype: models.Network
        """
        return self.session.query(models.Network).get(id)

    def drop_graph(self, network_id):
        """Drops a graph by ID

        :param network_id: The network's database id
        :type network_id: int
        """

        # TODO delete with cascade
        self.session.query(models.Network).filter(models.Network.id == network_id).delete()
        self.session.commit()

    def ls(self):
        """Lists network id, network name, and network version triples"""
        return [(network.id, network.name, network.version) for network in self.session.query(models.Network).all()]

    def get_edge_iter_by_filter(self, **annotations):
        """Returns an iterator over models.Edge object that match the given annotations

        :param annotations: dictionary of {URL: values}
        :type annotations: dict
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

        :param annotations: dictionary of {URL: values}
        :type annotations: dict
        :return: A BEL Graph
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
