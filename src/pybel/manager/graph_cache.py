from sqlalchemy.orm.exc import NoResultFound

from . import models
from .cache import BaseCacheManager
from ..graph import to_bytes, from_bytes
from ..parser.canonicalize import decanonicalize_node, decanonicalize_edge

try:
    import cPickle as pickle
except ImportError:
    import pickle

ANNOTATION_KEY_BLACKLIST = {'citation', 'SupportingText', 'subject', 'object'}


class GraphCacheManager(BaseCacheManager):
    def store_graph(self, graph, store_parts=False):
        """Stores a graph in the database

        :param graph: a BEL network
        :type graph: :class:`pybel.BELGraph`
        :param store_parts: Store the nodes, edges, citation, evidence, and annotations to the cache
        :type store_parts: bool
        """

        network = models.Network(blob=to_bytes(graph), **graph.document)

        if store_parts:
            self.store_graph_parts(network, graph)

        self.session.add(network)
        self.session.commit()

        return network

    def store_graph_parts(self, network, graph):
        nc = {node: self.get_or_create_node(decanonicalize_node(graph, node)) for node in graph}

        for u, v, k, data in graph.edges_iter(data=True, keys=True):
            source, target = nc[u], nc[v]
            edge_bel = decanonicalize_edge(graph, u, v, k)

            citation = self.get_or_create_citation(**data['citation'])
            evidence = self.get_or_create_evidence(citation, data['SupportingText'])

            edge = models.Edge(source=source, target=target, citation=citation, evidence=evidence, bel=edge_bel)

            for key, value in data.items():
                if key in ANNOTATION_KEY_BLACKLIST:
                    continue
                edge.annotations.append(self.get_or_create_annotation(key, value))

            network.edges.append(edge)

    def get_graph_versions(self, name):
        """Returns all of the versions of a graph with the given name"""
        return {x for x, in self.session.query(models.Network.version).filter(models.Network.name == name).all()}

    def get_graph(self, name, version=None):
        """Loads most recent graph, or allows for specification of version

        :param name: The name of the graph
        :type name: str
        :param version: The version string of the graph. If not specified, loads most recent graph added with this name
        :type version: str
        :return:
        """
        if version is not None:
            n = self.session.query(models.Network).filter(models.Network.name == name,
                                                          models.Network.version == version).one()
        else:
            n = self.session.query(models.Network).filter(models.Network.name == name).order_by(
                models.Network.created.desc()).limit(1).one()

        return from_bytes(n.blob)

    def ls(self):
        return [(network.name, network.version) for network in self.session.query(models.Network).all()]

    def get_or_create_node(self, bel):
        """

        :param bel:
        :type bel: str
        :return:
        :rtype: models.Node
        """
        try:
            result = self.session.query(models.Node).filter_by(bel=bel).one()
        except NoResultFound:
            result = models.Node(bel=bel)
            self.session.add(result)
        return result

    def get_or_create_citation(self, type, name, reference, date=None, authors=None, comments=None):
        """

        :param type:
        :param name:
        :param reference:
        :param date:
        :param authors:
        :param comments:
        :return:
        :rtype: models.Citation
        """

    def get_or_create_evidence(self, citation, evidence):
        """

        :param citation:
        :type citation: models.Citation
        :param evidence:
        :type evidence: str
        :return:
        :rtype: models.Evidence
        """

    def get_or_create_annotation(self, anno_key, anno_val):
        """

        :param anno_key:
        :param anno_val:
        :return:
        :rtype: models.AnnotationEntry
        """


def to_database(graph, connection=None):
    """Stores a graph in a database

    :param graph: a BEL graph
    :type graph: BELGraph
    :param connection: The string form of the URL is :code:`dialect[+driver]://user:password@host/dbname[?key=value..]`,
                       where dialect is a database name such as mysql, oracle, postgresql, etc., and driver the name
                       of a DBAPI, such as psycopg2, pyodbc, cx_oracle, etc. Alternatively, the URL can be an instance
                       of URL
    :type connection: str
    """
    if isinstance(connection, GraphCacheManager):
        connection.store_graph(graph)
    else:
        GraphCacheManager(connection).store_graph(graph)


def from_database(name, version=None, connection=None):
    """Loads a BEL graph from a database


    :param name: The name of the graph
    :type name: str
    :param version: The version string of the graph. If not specified, loads most recent graph added with this name
    :type version: str
    :param connection: The string form of the URL is :code:`dialect[+driver]://user:password@host/dbname[?key=value..]`,
                       where dialect is a database name such as mysql, oracle, postgresql, etc., and driver the name
                       of a DBAPI, such as psycopg2, pyodbc, cx_oracle, etc. Alternatively, the URL can be an instance
                       of URL.
    :type connection: str
    :return: a BEL graph loaded from the database
    :rtype: BELGraph
    """
    return GraphCacheManager(connection).get_graph(name, version)
