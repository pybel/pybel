import networkx as nx

from .cache import BaseCacheManager
from .models import Network
from ..graph import BELGraph

try:
    import cPickle as pickle
except ImportError:
    import pickle


class GraphCacheManager(BaseCacheManager):
    def __init__(self, connection=None, echo=False):
        BaseCacheManager.__init__(self, connection=connection, echo=echo)

    def store_graph(self, graph):
        """

        :param graph:
        :type graph: :class:`pybel.BELGraph`
        :return:
        """

        d = {k.lower(): v for k, v in graph.document.items()}
        d['blob'] = pickle.dumps(nx.MultiDiGraph(graph), protocol=pickle.HIGHEST_PROTOCOL)

        g = Network(**d)

        self.session.add(g)
        self.session.commit()

        return g

    def load_graph(self, name, version):
        n = self.session.query(Network).filter(Network.name == name, Network.version == version).one()
        g = BELGraph(data=pickle.loads(n.blob))
        return g

    def ls(self):
        return [(x.name, x.version) for x in self.session.query(Network).all()]


