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


class BELGraph(nx.MultiDiGraph):
    """
    An extension of a NetworkX MultiGraph to hold a BEL graph.
    """

    def parse_from_url(self, url):
        """
        Parses a BEL file from URL resource and adds to graph
        :param url: URL to BEL Resource
        :return: self
        :rtype: BELGraph
        """
        return self

    def parse_from_file(self, fl):
        """
        Parses a BEL file from a file-like object and adds to graph
        :param fl: file-like object backed by BEL data
        :return: self
        :rtype: BELGraph
        """
        return self
