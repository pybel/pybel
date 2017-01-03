from .cache import BaseCacheManager
from .models import Network
from ..graph import to_bytes, from_bytes

from sqlalchemy import desc

try:
    import cPickle as pickle
except ImportError:
    import pickle


class GraphCacheManager(BaseCacheManager):
    def __init__(self, connection=None, echo=False):
        BaseCacheManager.__init__(self, connection=connection, echo=echo)

    def store_graph(self, graph):
        """Stores a graph in the database

        :param graph: a BEL network
        :type graph: :class:`pybel.BELGraph`
        """

        d = {k.lower(): v for k, v in graph.document.items()}
        d['blob'] = to_bytes(graph)

        g = Network(**d)

        self.session.add(g)
        self.session.commit()

        return g

    def get_versions(self, name):
        """Returns all of the versions of a graph with the given name"""
        return {x for x, in self.session.query(Network.version).filter(Network.name == name).all()}

    def load_graph(self, name, version=None):
        """Loads most recent graph, or allows for specification of version

        :param name: The name of the graph
        :type name: str
        :param version: The version string of the graph. If not specified, loads most recent graph added with this name
        :type version: str
        :return:
        """
        if version is not None:
            n = self.session.query(Network).filter(Network.name == name, Network.version == version).one()
        else:
            n = self.session.query(Network).filter(Network.name == name).order_by(desc(Network.created)).limit(1).one()
        return from_bytes(n.blob)

    def ls(self):
        return [(x.name, x.version) for x in self.session.query(Network).all()]

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
    gcm = GraphCacheManager(connection)
    gcm.store_graph(graph)


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
    gcm = GraphCacheManager(connection)
    return gcm.load_graph(name, version)
