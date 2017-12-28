# -*- coding: utf-8 -*-

import logging
from copy import deepcopy

import networkx
from six import string_types

from .operations import left_full_join, left_node_intersection_join, left_outer_join
from ..constants import *
from ..parser.canonicalize import node_to_tuple
from ..utils import get_version

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

    def __init__(self, name=None, version=None, description=None, authors=None, contact=None, data=None, **kwargs):
        """The default constructor parses a BEL graph using the built-in :mod:`networkx` methods. For IO, see
        the :mod:`pybel.io` module

        :param str name: The graph's name
        :param str version: The graph's version. Recommended to use `semantic versioning <http://semver.org/>`_ or
                            ``YYYYMMDD`` format.
        :param str description: A description of the graph
        :param str authors: The authors of this graph
        :param str contact: The contact email for this graph
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

        if authors:
            self.graph[GRAPH_METADATA][METADATA_AUTHORS] = authors

        if contact:
            self.graph[GRAPH_METADATA][METADATA_CONTACT] = contact

        if GRAPH_PYBEL_VERSION not in self.graph:
            self.graph[GRAPH_PYBEL_VERSION] = get_version()

        for resource_dict in RESOURCE_DICTIONARY_NAMES:
            if resource_dict not in self.graph:
                self.graph[resource_dict] = {}

        if GRAPH_UNCACHED_NAMESPACES not in self.graph:
            self.graph[GRAPH_UNCACHED_NAMESPACES] = set()

    @property
    def document(self):
        """A dictionary holding the metadata from the "Document" section of the BEL script. All keys are normalized
        according to :data:`pybel.constants.DOCUMENT_KEYS`

        :rtype: dict
        """
        return self.graph[GRAPH_METADATA]

    @property
    def name(self, *attrs):
        """The graph's name, from the ``SET DOCUMENT Name = "..."`` entry in the source BEL script

        :rtype: str
        """
        return self.graph[GRAPH_METADATA].get(METADATA_NAME)

    @name.setter
    def name(self, *attrs, **kwargs):
        self.graph[GRAPH_METADATA][METADATA_NAME] = attrs[0]

    @property
    def version(self):
        """The graph's version, from the ``SET DOCUMENT Version = "..."`` entry in the source BEL script

        :rtype: str
        """
        return self.graph[GRAPH_METADATA].get(METADATA_VERSION)

    @version.setter
    def version(self, version):
        self.graph[GRAPH_METADATA][METADATA_VERSION] = version

    @property
    def description(self):
        """The graph's description, from the ``SET DOCUMENT Description = "..."`` entry in the source BEL Script

        :rtype: str
        """
        return self.graph[GRAPH_METADATA].get(METADATA_DESCRIPTION)

    @description.setter
    def description(self, description):
        self.graph[GRAPH_METADATA][METADATA_DESCRIPTION] = description

    @property
    def namespace_url(self):
        """A dictionary mapping the keywords used to create this graph to the URLs of the BELNS files from the
        ``DEFINE NAMESPACE [key] AS URL "[value]"`` entries in the definitions section.

        :rtype: dict[str,str]
        """
        return self.graph[GRAPH_NAMESPACE_URL]

    @property
    def namespace_owl(self):
        """A dictionary mapping the keywords used to create this graph to the URLs of the OWL files from the
        ``DEFINE NAMESPACE [key] AS OWL "[value]"`` entries in the definitions section

        :rtype: dict[str,str]
        """
        return self.graph[GRAPH_NAMESPACE_OWL]

    @property
    def defined_namespace_keywords(self):
        """Returns the set of all keywords defined as namespaces in this graph

        :rtype: set[str]
        """
        return (
            set(self.namespace_pattern) |
            set(self.namespace_url) |
            set(self.namespace_owl)
        )

    @property
    def uncached_namespaces(self):
        """Returns a list of namespaces's URLs that are present in the graph, but cannot be cached due to their
        corresponding resources' cachable flags being set to "no."

        :rtype: set[str]
        """
        return self.graph[GRAPH_UNCACHED_NAMESPACES]

    @property
    def namespace_pattern(self):
        """A dictionary mapping the namespace keywords used to create this graph to their regex patterns from the
        ``DEFINE NAMESPACE [key] AS PATTERN "[value]"`` entries in the definitions section

        :rtype: dict[str,str]
        """
        return self.graph[GRAPH_NAMESPACE_PATTERN]

    @property
    def annotation_url(self):
        """A dictionary mapping the annotation keywords used to create this graph to the URLs of the BELANNO files
        from the ``DEFINE ANNOTATION [key] AS URL "[value]"`` entries in the definitions section

        :rtype: dict[str,str]
        """
        return self.graph[GRAPH_ANNOTATION_URL]

    @property
    def annotation_owl(self):
        """A dictionary mapping the annotation keywords used to creat ethis graph to the URLs of the OWL files
        from the ``DEFINE ANNOTATION [key] AS OWL "[value]"`` entries in the definitions section

        :rtype: dict[str,str]
        """
        return self.graph[GRAPH_ANNOTATION_OWL]

    @property
    def annotation_pattern(self):
        """A dictionary mapping the annotation keywords used to create this graph to their regex patterns
        from the ``DEFINE ANNOTATION [key] AS PATTERN "[value]"`` entries in the definitions section

        :rtype: dict[str,str]
        """
        return self.graph[GRAPH_ANNOTATION_PATTERN]

    @property
    def annotation_list(self):
        """A dictionary mapping the keywords of locally defined annotations to a set of their values
        from the ``DEFINE ANNOTATION [key] AS LIST {"[value]", ...}`` entries in the definitions section"""
        return self.graph[GRAPH_ANNOTATION_LIST]

    @property
    def defined_annotation_keywords(self):
        """Returns the set of all keywords defined as annotations in this graph

        :rtype: set[str]
        """
        return (
            set(self.annotation_pattern) |
            set(self.annotation_url) |
            set(self.annotation_owl) |
            set(self.annotation_list)
        )

    @property
    def pybel_version(self):
        """Stores the version of PyBEL with which this graph was produced as a string

        :rtype: str
        """
        return self.graph[GRAPH_PYBEL_VERSION]

    @property
    def warnings(self):
        """Warnings are stored in a list of 4-tuples that is a property of the graph object.
        This tuple respectively contains the line number, the line text, the exception instance, and the context
        dictionary from the parser at the time of error.

        :rtype: list[tuple[int,str,Exception,dict[str,str]]]
        """
        return self._warnings

    def __str__(self):
        """Stringifies this graph as its name and version pair"""
        return '{} v{}'.format(self.name, self.version)

    def skip_storing_namespace(self, namespace):
        """Checks if the namespace should be skipped

        :param Optional[str] namespace:
        :rtype: bool
        """
        return (
            namespace is not None and
            namespace in self.namespace_url and
            self.namespace_url[namespace] in self.uncached_namespaces
        )

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
            self.add_edge(u, v, key=key, **{RELATION: relation})

    def add_node_from_data(self, attr_dict):
        """Converts a PyBEL node data dictionary to a canonical PyBEL node tuple and ensures it is in the graph.

        :param dict attr_dict: A PyBEL node data dictionary
        :return: A PyBEL node tuple
        :rtype: tuple
        """
        node_tuple = node_to_tuple(attr_dict)

        if node_tuple in self:
            return node_tuple

        self.add_node(node_tuple, attr_dict=attr_dict)

        if VARIANTS in attr_dict:
            parent_node_tuple = self.add_simple_node(attr_dict[FUNCTION], attr_dict[NAMESPACE], attr_dict[NAME])
            self.add_unqualified_edge(parent_node_tuple, node_tuple, HAS_VARIANT)

        elif MEMBERS in attr_dict:
            for member in attr_dict[MEMBERS]:
                member_node_tuple = self.add_node_from_data(member)
                self.add_unqualified_edge(node_tuple, member_node_tuple, HAS_COMPONENT)

        elif PRODUCTS in attr_dict and REACTANTS in attr_dict:
            for reactant_tokens in attr_dict[REACTANTS]:
                reactant_node_tuple = self.add_node_from_data(reactant_tokens)
                self.add_unqualified_edge(node_tuple, reactant_node_tuple, HAS_REACTANT)

            for product_tokens in attr_dict[PRODUCTS]:
                product_node_tuple = self.add_node_from_data(product_tokens)
                self.add_unqualified_edge(node_tuple, product_node_tuple, HAS_PRODUCT)

        return node_tuple

    def has_node_with_data(self, attr_dict):
        """Checks if this graph has a node with the given data dictionary

        :param dict attr_dict: A PyBEL node data dictionary
        :rtype: bool
        """
        node_tuple = node_to_tuple(attr_dict)
        return self.has_node(node_tuple)

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

    def add_qualified_edge(self, u, v, relation, evidence, citation, annotations=None, subject_modifier=None,
                           object_modifier=None, **attr):
        """Adds an edge, qualified with a relation, evidence, citation, and optional annotations, subject modifications,
        and object modifications

        :param tuple or dict u: Either a PyBEL node tuple or PyBEL node data dictionary representing the source node
        :param tuple or dict v: Either a PyBEL node tuple or PyBEL node data dictionary representing the target node
        :param str relation: The type of relation this edge represents
        :param str evidence: The evidence string from an article
        :param dict[str,str] or str citation: The citation data dictionary for this evidence. If a string is given,
                                                assumes it's a PubMed identifier and autofills the citation type.
        :param dict[str,str] annotations: The annotations data dictionary
        :param dict subject_modifier: The modifiers (like activity) on the subject node. See data model documentation.
        :param dict object_modifier: The modifiers (like activity) on the object node. See data model documentation.
        """
        attr.update({
            RELATION: relation,
            EVIDENCE: evidence,
        })

        if isinstance(citation, string_types):
            attr[CITATION] = {
                CITATION_TYPE: CITATION_TYPE_PUBMED,
                CITATION_REFERENCE: citation
            }
        elif isinstance(citation, dict):
            attr[CITATION] = citation
        else:
            raise TypeError

        if annotations:
            attr[ANNOTATIONS] = annotations

        if subject_modifier:
            attr[SUBJECT] = subject_modifier

        if object_modifier:
            attr[OBJECT] = object_modifier

        if isinstance(u, dict):
            u = self.add_node_from_data(u)

        if isinstance(v, dict):
            v = self.add_node_from_data(v)

        self.add_edge(u, v, **attr)

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

    def get_node_identifier(self, node):
        """Gets the identifier for a given node from the database (not the same as the node hash)"""
        return self.node[node].get(IDENTIFIER)

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
        """Creates a deep copy of this graph and full joins another graph with it using
        :func:`pybel.struct.left_full_join`.

        :param BELGraph other: Another BEL graph
        :rtype: BELGraph

        Example usage:

        >>> import pybel
        >>> g = pybel.from_path('...')
        >>> h = pybel.from_path('...')
        >>> k = g + h
        """
        result = deepcopy(self)
        left_full_join(result, other)
        return result

    def __iadd__(self, other):
        """Full joins another graph into this one using :func:`pybel.struct.left_full_join`.

        :param BELGraph other: Another BEL graph
        :rtype: BELGraph

        Example usage:

        >>> import pybel
        >>> g = pybel.from_path('...')
        >>> h = pybel.from_path('...')
        >>> g += h
        """
        left_full_join(self, other)
        return self

    def __and__(self, other):
        """Creates a deep copy of this graph and outer joins another graph with it using
        :func:`pybel.struct.left_outer_join`.

        :param BELGraph other: Another BEL graph
        :rtype: BELGraph

        Example usage:

        >>> import pybel
        >>> g = pybel.from_path('...')
        >>> h = pybel.from_path('...')
        >>> k = g & h
        """
        result = deepcopy(self)
        left_outer_join(result, other)
        return result

    def __iand__(self, other):
        """Outer joins another graph into this one using :func:`pybel.struct.left_outer_join`.

        :param BELGraph other: Another BEL graph
        :rtype: BELGraph

        Example usage:

        >>> import pybel
        >>> g = pybel.from_path('...')
        >>> h = pybel.from_path('...')
        >>> g &= h
        """
        left_outer_join(self, other)
        return self

    def __xor__(self, other):
        """Node intersection joins another graph using :func:`pybel.struct.left_node_intersection_join`

        :param BELGraph other: Another BEL graph

        Example usage:

        >>> import pybel
        >>> g = pybel.from_path('...')
        >>> h = pybel.from_path('...')
        >>> k = g ^ h
        """
        return left_node_intersection_join(self, other)
