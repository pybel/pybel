import networkx as nx


def from_url(url):
    """
    Parses a BEL file from URL resource
    :param url: URL to BEL resource
    :return: a BEL MultiGraph
    :rtype BELGraph
    """
    return BELGraph().parse_from_url(url)


def from_file(fl):
    """
    Parses a BEL file from a file-like object
    :param fl: file-like object backed by BEL data
    :return: a BEL MultiGraph
    :rtype BELGraph
    """
    return BELGraph().parse_from_file(fl)


class BELGraph(nx.MultiGraph):
    """
    An extension of a NetworkX MultiGraph to hold a BEL graph.
    """

    def parse_from_url(self, url):
        return self

    def parse_from_file(self, fl):
        return self
