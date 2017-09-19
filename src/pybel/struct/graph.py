# -*- coding: utf-8 -*-

import logging

import networkx
from copy import deepcopy

from .operations import left_full_join, left_outer_join
from ..constants import *
from ..parser.canonicalize import add_node_from_data
from ..utils import get_version, subdict_matches

__all__ = [
    'BELGraph',
]

log = logging.getLogger(__name__)

RESOURCE_DICTIONARY_NAMES = (
    GRAPH_NAMESPACE_URL,
    GRAPH_NAMESPACE_OWL,
    GRAPH_NAMESPACE_PATTERN,
    GRAPH_ANNOTATION_URL,
    GRAPH_ANNOTATION_OWL,
    GRAPH_ANNOTATION_PATTERN,
    GRAPH_ANNOTATION_LIST,
)


class BELGraph(networkx.MultiDiGraph):
    """This class represents biological knowledge assembled in BEL as a network by extending the
    :class:`networkx.MultiDiGraph`.
    """

    def __init__(self, name=None, version=None, description=None, data=None, **kwargs):
        """The default constructor parses a BEL graph using the built-in :mod:`networkx` methods. For IO, see
        the :mod:`pybel.io` module

        :param str name: The graph's name
        :param str version: The graph's version. Recommended to use semantic versioning or YYYYMMDD format.
        :param str description: A description of the graph
        :param data: initial graph data to pass to :class:`networkx.MultiDiGraph`
        :param kwargs: keyword arguments to pass to :class:`networkx.MultiDiGraph`
        """
        super(BELGraph, self).__init__(data=data, **kwargs)

        self._warnings = []

        if GRAPH_METADATA not in self.graph:
            self.graph[GRAPH_METADATA] = {}

        if name:
            self.graph[GRAPH_METADATA][METADATA_NAME] = name

        if version:
            self.graph[GRAPH_METADATA][METADATA_VERSION] = version

        if description:
            self.graph[GRAPH_METADATA][METADATA_DESCRIPTION] = description

        if GRAPH_PYBEL_VERSION not in self.graph:
            self.graph[GRAPH_PYBEL_VERSION] = get_version()

        for resource_dict in RESOURCE_DICTIONARY_NAMES:
            if resource_dict not in self.graph:
                self.graph[resource_dict] = {}

    @property
    def document(self):
        """A dictionary holding the metadata from the "Document" section of the BEL script. All keys are normalized
        according to :data:`pybel.constants.DOCUMENT_KEYS`
        """
        return self.graph[GRAPH_METADATA]

    @property
    def name(self, *attrs):
        """The graph's name, from the ``SET DOCUMENT Name = "..."`` entry in the source BEL script"""
        return self.graph[GRAPH_METADATA].get(METADATA_NAME, '')

    @name.setter
    def name(self, *attrs, **kwargs):
        self.graph[GRAPH_METADATA][METADATA_NAME] = attrs[0]

    @property
    def version(self):
        """The graph's version, from the ``SET DOCUMENT Version = "..."`` entry in the source BEL script"""
        return self.graph[GRAPH_METADATA].get(METADATA_VERSION)

    @version.setter
    def version(self, version):
        self.graph[GRAPH_METADATA][METADATA_VERSION] = version

    @property
    def description(self):
        """The graph's description, from the ``SET DOCUMENT Description = "..."`` entry in the source BEL Script"""
        return self.graph[GRAPH_METADATA].get(METADATA_DESCRIPTION)

    @description.setter
    def description(self, description):
        self.graph[GRAPH_METADATA][METADATA_DESCRIPTION] = description

    @property
    def namespace_url(self):
        """A dictionary mapping the keywords used to create this graph to the URLs of the BELNS files from the
        ``DEFINE NAMESPACE [key] AS URL "[value]"`` entries in the definitions section.
        """
        return self.graph[GRAPH_NAMESPACE_URL]

    @property
    def namespace_owl(self):
        """A dictionary mapping the keywords used to create this graph to the URLs of the OWL files from the
        ``DEFINE NAMESPACE [key] AS OWL "[value]"`` entries in the definitions section"""
        return self.graph[GRAPH_NAMESPACE_OWL]

    @property
    def namespace_pattern(self):
        """A dictionary mapping the namespace keywords used to create this graph to their regex patterns from the
        ``DEFINE NAMESPACE [key] AS PATTERN "[value]"`` entries in the definitions section"""
        return self.graph[GRAPH_NAMESPACE_PATTERN]

    @property
    def annotation_url(self):
        """A dictionary mapping the annotation keywords used to create this graph to the URLs of the BELANNO files
        from the ``DEFINE ANNOTATION [key] AS URL "[value]"`` entries in the definitions section"""
        return self.graph[GRAPH_ANNOTATION_URL]

    @property
    def annotation_owl(self):
        """A dictionary mapping the annotation keywords used to creat ethis graph to the URLs of the OWL files
        from the ``DEFINE ANNOTATION [key] AS OWL "[value]"`` entries in the definitions section"""
        return self.graph[GRAPH_ANNOTATION_OWL]

    @property
    def annotation_pattern(self):
        """A dictionary mapping the annotation keywords used to create this graph to their regex patterns
        from the ``DEFINE ANNOTATION [key] AS PATTERN "[value]"`` entries in the definitions section
        """
        return self.graph[GRAPH_ANNOTATION_PATTERN]

    @property
    def annotation_list(self):
        """A dictionary mapping the keywords of locally defined annotations to a set of their values
        from the ``DEFINE ANNOTATION [key] AS LIST {"[value]", ...}`` entries in the definitions section"""
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

    def add_node_from_data(self, attr_dict):
        """Converts a PyBEL node data dictionary to a canonical PyBEL node tuple and ensures it is in the graph.

        :param dict attr_dict: A PyBEL node data dictionary
        :return: The PyBEL node tuple representing this node
        :rtype: tuple
        """
        return add_node_from_data(self, attr_dict)

    def add_simple_node(self, function, namespace, name):
        """Adds a simple node, with only a namespace and name

        :param str function: The node's function (:data:`pybel.constants.GENE`, :data:`pybel.constants.PROTEIN`, etc)
        :param str namespace: The node's namespace
        :param str name: The node's name
        :return: The PyBEL node tuple representing this node
        :rtype: tuple
        """
        return self.add_node_from_data({
            FUNCTION: function,
            NAMESPACE: namespace,
            NAME: name
        })

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

    def __add__(self, other):
        """Allows g + h to full join g and h and return a new graph"""
        result = deepcopy(self)
        left_full_join(result, other)
        return result

    def __iadd__(self, other):
        """Allows g += h to full join h into g"""
        left_full_join(self, other)

    def __iand__(self, other):
        """Allows g &= h to outer join h into g"""
        left_outer_join(self, other)

    def __and__(self, other):
        """Allows g & h to outer join h and g and return a new graph"""
        result = deepcopy(self)
        left_outer_join(result, other)
        return result
