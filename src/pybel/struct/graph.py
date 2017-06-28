# -*- coding: utf-8 -*-

import logging

import networkx

from .operations import left_full_join, left_outer_join
from ..constants import *
from ..utils import get_version, subdict_matches

try:
    import cPickle as pickle
except ImportError:
    import pickle

__all__ = [
    'BELGraph',
]

log = logging.getLogger(__name__)


class BELGraph(networkx.MultiDiGraph):
    """This class represents biological knowledge assembled in BEL as a network by extending the
    :class:`networkx.MultiDiGraph`.
    """

    def __init__(self, data=None, **kwargs):
        """The default constructor parses a BEL graph using the built-in :mod:`networkx` methods. For IO, see
        the :mod:`pybel.io` module
        
        :param data: initial graph data to pass to :class:`networkx.MultiDiGraph`
        :param kwargs: keyword arguments to pass to :class:`networkx.MultiDiGraph`
        """
        super(BELGraph, self).__init__(data=data, **kwargs)

        self._warnings = []

        if GRAPH_METADATA not in self.graph:
            self.graph[GRAPH_METADATA] = {}

        if GRAPH_PYBEL_VERSION not in self.graph:
            self.graph[GRAPH_PYBEL_VERSION] = get_version()

        if GRAPH_NAMESPACE_URL not in self.graph:
            self.graph[GRAPH_NAMESPACE_URL] = {}

        if GRAPH_NAMESPACE_OWL not in self.graph:
            self.graph[GRAPH_NAMESPACE_OWL] = {}

        if GRAPH_NAMESPACE_PATTERN not in self.graph:
            self.graph[GRAPH_NAMESPACE_PATTERN] = {}

        if GRAPH_ANNOTATION_URL not in self.graph:
            self.graph[GRAPH_ANNOTATION_URL] = {}

        if GRAPH_ANNOTATION_OWL not in self.graph:
            self.graph[GRAPH_ANNOTATION_OWL] = {}

        if GRAPH_ANNOTATION_PATTERN not in self.graph:
            self.graph[GRAPH_ANNOTATION_PATTERN] = {}

        if GRAPH_ANNOTATION_LIST not in self.graph:
            self.graph[GRAPH_ANNOTATION_LIST] = {}

        #: Is true if during BEL Parsing, a term that is not part of a relation is found
        self.has_singleton_terms = False

    @property
    def document(self):
        """A dictionary holding the metadata from the "Document" section of the BEL script. All keys are normalized
        according to :data:`pybel.constants.DOCUMENT_KEYS`
        """
        return self.graph[GRAPH_METADATA]

    @property
    def name(self, *attrs):
        """Gets the graph's name. Requires a weird hack in the signature since it's overriding a property"""
        return self.graph[GRAPH_METADATA].get(METADATA_NAME, '')

    @name.setter
    def name(self, *attrs, **kwargs):
        """The graph's name, from the ``SET DOCUMENT Name = "..."`` entry in the source BEL script"""
        self.graph[GRAPH_METADATA][METADATA_NAME] = attrs[0]

    @property
    def version(self):
        """The graph's version, from the ``SET DOCUMENT Version = "..."`` entry in the source BEL script"""
        return self.graph[GRAPH_METADATA].get(METADATA_VERSION)

    @property
    def description(self):
        """The graph's description, from the ``SET DOCUMENT Description = "..."`` entry in the source BEL Script"""
        return self.graph[GRAPH_METADATA].get(METADATA_DESCRIPTION)

    @property
    def namespace_url(self):
        """A dictionary mapping the keywords used to create this graph to the URLs of the BELNS file"""
        return self.graph[GRAPH_NAMESPACE_URL]

    @property
    def namespace_owl(self):
        """A dictionary mapping the keywords used to create this graph to the URLs of the OWL file"""
        return self.graph[GRAPH_NAMESPACE_OWL]

    @property
    def namespace_pattern(self):
        """A dictionary mapping the namespace keywords used to create this graph to their regex patterns"""
        return self.graph[GRAPH_NAMESPACE_PATTERN]

    @property
    def annotation_url(self):
        """A dictionary mapping the annotation keywords used to create this graph to the URLs of the BELANNO file"""
        return self.graph[GRAPH_ANNOTATION_URL]

    @property
    def annotation_owl(self):
        """A dictionary mapping the annotation keywords to the URL of the OWL file"""
        return self.graph[GRAPH_ANNOTATION_OWL]

    @property
    def annotation_pattern(self):
        """A dictionary mapping the annotation keywords used to create this graph to their regex patterns"""
        return self.graph[GRAPH_ANNOTATION_PATTERN]

    @property
    def annotation_list(self):
        """A dictionary mapping the keywords of locally defined annotations to a set of their values"""
        return self.graph[GRAPH_ANNOTATION_LIST]

    @property
    def pybel_version(self):
        """Stores the version of PyBEL with which this graph was produced as a string"""
        return self.graph[GRAPH_PYBEL_VERSION]

    @property
    def warnings(self):
        """Warnings are stored in a list of 4-tuples that is a property of the graph object.
        This tuple respectively contains the line number, the line text, the exception instance, and the context
        dictionary from the parser at the time of error.
        """
        return self._warnings

    def __str__(self):
        return '{} v{}'.format(self.name, self.version)

    def add_warning(self, line_number, line, exception, context=None):
        """Adds a warning to the internal warning log in the graph, with optional context information"""
        self.warnings.append((line_number, line, exception, {} if context is None else context))

    def add_unqualified_edge(self, u, v, relation):
        """Adds unique edge that has no annotations

        :param tuple u: The source BEL node
        :param tuple v: The target BEL node
        :param str relation: A relationship label from :mod:`pybel.constants`
        """
        key = unqualified_edge_code[relation]
        if not self.has_edge(u, v, key):
            self.add_edge(u, v, key=key, **{RELATION: relation, ANNOTATIONS: {}})

    # TODO better implementation using edge filters
    def edges_iter(self, nbunch=None, data=False, keys=False, default=None, **kwargs):
        """Allows for filtering by checking keyword arguments are a sub-dictionary of each edges' data.
            See :py:meth:`networkx.MultiDiGraph.edges_iter`"""
        for u, v, k, d in super(BELGraph, self).edges_iter(nbunch=nbunch, data=True, keys=True, default=default):
            if not subdict_matches(d, kwargs):
                continue
            elif keys and data:
                yield u, v, k, d
            elif data:
                yield u, v, d
            elif keys:
                yield u, v, k
            else:
                yield u, v

    # TODO better implementation using node filters
    def nodes_iter(self, data=False, **kwargs):
        """Allows for filtering by checking keyword arguments are a sub-dictionary of each nodes' data.
            See :py:meth:`networkx.MultiDiGraph.edges_iter`"""
        for n, d in super(BELGraph, self).nodes_iter(data=True):
            if not subdict_matches(d, kwargs):
                continue
            elif data:
                yield n, d
            else:
                yield n

    def add_simple_node(self, function, namespace, name):
        """Adds a simple node, with only a namespace and name

        :param str function: The node's function (:data:`pybel.constants.GENE`, :data:`pybel.constants.RNA`,
                        :data:`pybel.constants.PROTEIN`, etc)
        :param str namespace: The namespace
        :param str name: The name of the node
        """
        node = function, namespace, name
        if node not in self:
            self.add_node(node, **{FUNCTION: function, NAMESPACE: namespace, NAME: name})

    def has_edge_citation(self, u, v, key):
        """Does the given edge have a citation?"""
        return CITATION in self.edge[u][v][key]

    def get_edge_citation(self, u, v, key):
        """Gets the citation for a given edge"""
        return self.edge[u][v][key].get(CITATION)

    def has_edge_evidence(self, u, v, key):
        """Does the given edge have evidence?"""
        return EVIDENCE in self.edge[u][v][key]

    def get_edge_evidence(self, u, v, key):
        """Gets the evidence for a given edge"""
        return self.edge[u][v][key].get(EVIDENCE)

    def get_edge_annotations(self, u, v, key):
        """Gets the annotations for a given edge"""
        return self.edge[u][v][key].get(ANNOTATIONS)

    def get_node_name(self, node):
        """Gets the node's name, or return None if no name"""
        return self.node[node].get(NAME)

    def get_node_label(self, node):
        """Gets the label for a given node"""
        return self.node[node].get(LABEL)

    def set_node_label(self, node, label):
        """Sets the label for a given node"""
        self.node[node][LABEL] = label

    def get_node_description(self, node):
        """Gets the description for a given node"""
        return self.node[node].get(DESCRIPTION)

    def set_node_description(self, node, description):
        """Sets the description for a given node"""
        self.node[node][DESCRIPTION] = description

    def __iadd__(self, other):
        """Allows g += h to full join h into g"""
        left_full_join(self, other)

    def __iand__(self, other):
        """Allows g &= h to outer join h into g"""
        left_outer_join(self, other)
