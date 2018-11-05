# -*- coding: utf-8 -*-

"""Contains the main data structure for PyBEL."""

from __future__ import print_function

import logging
from copy import deepcopy
from pkg_resources import iter_entry_points

import networkx as nx
from six import string_types

from .operations import left_full_join, left_node_intersection_join, left_outer_join
from ..canonicalize import edge_to_bel
from ..constants import (
    ANNOTATIONS, ASSOCIATION, CITATION, CITATION_REFERENCE, CITATION_TYPE, CITATION_TYPE_PUBMED, DECREASES, DESCRIPTION,
    DIRECTLY_DECREASES, DIRECTLY_INCREASES, EQUIVALENT_TO, EVIDENCE, GRAPH_ANNOTATION_LIST, GRAPH_ANNOTATION_PATTERN,
    GRAPH_ANNOTATION_URL, GRAPH_METADATA, GRAPH_NAMESPACE_PATTERN, GRAPH_NAMESPACE_URL, GRAPH_PYBEL_VERSION,
    GRAPH_UNCACHED_NAMESPACES, HAS_COMPONENT, HAS_MEMBER, HAS_PRODUCT, HAS_REACTANT, HAS_VARIANT, INCREASES, IS_A,
    MEMBERS, METADATA_AUTHORS, METADATA_CONTACT, METADATA_COPYRIGHT, METADATA_DESCRIPTION, METADATA_DISCLAIMER,
    METADATA_LICENSES, METADATA_NAME, METADATA_VERSION, NAMESPACE, OBJECT, ORTHOLOGOUS, PART_OF, PRODUCTS, REACTANTS,
    RELATION, SUBJECT, TRANSCRIBED_TO, TRANSLATED_TO, VARIANTS,
)
from ..dsl import BaseEntity, activity
from ..utils import get_version, hash_edge

__all__ = [
    'BELGraph',
]

log = logging.getLogger(__name__)

RESOURCE_DICTIONARY_NAMES = (
    GRAPH_NAMESPACE_URL,
    GRAPH_NAMESPACE_PATTERN,
    GRAPH_ANNOTATION_URL,
    GRAPH_ANNOTATION_PATTERN,
    GRAPH_ANNOTATION_LIST,
)


def _clean_annotations(annotations_dict):
    """Fix the formatting of annotation dict.

    :type annotations_dict: dict[str,str] or dict[str,set[str]] or dict[str,dict[str,bool]]
    :rtype: dict[str,dict[str,bool]]
    """
    return {
        key: (
            values if isinstance(values, dict) else
            {v: True for v in values} if isinstance(values, set) else
            {values: True}
        )
        for key, values in annotations_dict.items()
    }


class BELGraph(nx.MultiDiGraph):
    """An extension to :class:`networkx.MultiDiGraph` to represent BEL."""

    def __init__(self, name=None, version=None, description=None, authors=None, contact=None, license=None,
                 copyright=None, disclaimer=None, data=None, **kwargs):
        """The default constructor parses a BEL graph using the built-in :mod:`networkx` methods.

        :param str name: The graph's name
        :param str version: The graph's version. Recommended to use `semantic versioning <http://semver.org/>`_ or
         ``YYYYMMDD`` format.
        :param str description: A description of the graph
        :param str authors: The authors of this graph
        :param str contact: The contact email for this graph
        :param str license: The license for this graph
        :param str copyright: The copyright for this graph
        :param str disclaimer: The disclaimer for this graph
        :param data: initial graph data to pass to :class:`networkx.MultiDiGraph`
        :param kwargs: keyword arguments to pass to :class:`networkx.MultiDiGraph`

        For IO, see the :mod:`pybel.io` module.
        """
        # TODO check that kwargs doesn't use any special pybel ones!

        super(BELGraph, self).__init__(data=data, **kwargs)

        self._warnings = []

        if GRAPH_METADATA not in self.graph:
            self.graph[GRAPH_METADATA] = {}

        if name:
            self.name = name

        if version:
            self.version = version

        if description:
            self.description = description

        if authors:
            self.authors = authors

        if contact:
            self.contact = contact

        if license:
            self.license = license

        if copyright:
            self.copyright = copyright

        if disclaimer:
            self.disclaimer = disclaimer

        if GRAPH_PYBEL_VERSION not in self.graph:
            self.graph[GRAPH_PYBEL_VERSION] = get_version()

        for resource_dict in RESOURCE_DICTIONARY_NAMES:
            if resource_dict not in self.graph:
                self.graph[resource_dict] = {}

        if GRAPH_UNCACHED_NAMESPACES not in self.graph:
            self.graph[GRAPH_UNCACHED_NAMESPACES] = set()

    def fresh_copy(self):
        """Create an unfilled :class:`BELGraph` as a hook for other :mod:`networkx` functions.

        Is necessary for .copy() to work.

        :rtype: BELGraph
        """
        return BELGraph()

    @property
    def document(self):
        """A dictionary holding the metadata from the "Document" section of the BEL script. All keys are normalized
        according to :data:`pybel.constants.DOCUMENT_KEYS`

        :rtype: dict[str,str]
        """
        return self.graph[GRAPH_METADATA]

    @property
    def name(self, *attrs):  # Needs *attrs since it's an override
        """The graph's name, from the ``SET DOCUMENT Name = "..."`` entry in the source BEL script

        :rtype: str
        """
        return self.document.get(METADATA_NAME)

    @name.setter
    def name(self, *attrs, **kwargs):  # Needs *attrs and **kwargs since it's an override
        self.document[METADATA_NAME] = attrs[0]

    @property
    def version(self):
        """The graph's version, from the ``SET DOCUMENT Version = "..."`` entry in the source BEL script

        :rtype: str
        """
        return self.document.get(METADATA_VERSION)

    @version.setter
    def version(self, version):
        self.document[METADATA_VERSION] = version

    @property
    def description(self):
        """The graph's description, from the ``SET DOCUMENT Description = "..."`` entry in the source BEL Script

        :rtype: str
        """
        return self.document.get(METADATA_DESCRIPTION)

    @description.setter
    def description(self, description):
        self.document[METADATA_DESCRIPTION] = description

    @property
    def authors(self):
        """The graph's description, from the ``SET DOCUMENT Authors = "..."`` entry in the source BEL Script

        :rtype: str
        """
        return self.document[METADATA_AUTHORS]

    @authors.setter
    def authors(self, authors):
        self.document[METADATA_AUTHORS] = authors

    @property
    def contact(self):
        """The graph's description, from the ``SET DOCUMENT ContactInfo = "..."`` entry in the source BEL Script

        :rtype: str
        """
        return self.document.get(METADATA_CONTACT)

    @contact.setter
    def contact(self, contact):
        self.document[METADATA_CONTACT] = contact

    @property
    def license(self):
        """The graph's license, from the `SET DOCUMENT Licenses = "..."`` entry in the source BEL Script

        :rtype: Optional[str]
        """
        return self.document.get(METADATA_LICENSES)

    @license.setter
    def license(self, license):
        self.document[METADATA_LICENSES] = license

    @property
    def copyright(self):
        """The graph's copyright, from the `SET DOCUMENT Copyright = "..."`` entry in the source BEL Script

        :rtype: Optional[str]
        """
        return self.document.get(METADATA_COPYRIGHT)

    @copyright.setter
    def copyright(self, copyright):
        self.document[METADATA_COPYRIGHT] = copyright

    @property
    def disclaimer(self):
        """The graph's disclaimer, from the `SET DOCUMENT Disclaimer = "..."`` entry in the source BEL Script

        :rtype: Optional[str]
        """
        return self.document.get(METADATA_DISCLAIMER)

    @disclaimer.setter
    def disclaimer(self, disclaimer):
        self.document[METADATA_DISCLAIMER] = disclaimer

    @property
    def namespace_url(self):
        """A dictionary mapping the keywords used to create this graph to the URLs of the BELNS files from the
        ``DEFINE NAMESPACE [key] AS URL "[value]"`` entries in the definitions section.

        :rtype: dict[str,str]
        """
        return self.graph[GRAPH_NAMESPACE_URL]

    @property
    def defined_namespace_keywords(self):
        """Returns the set of all keywords defined as namespaces in this graph

        :rtype: set[str]
        """
        return set(self.namespace_pattern) | set(self.namespace_url)

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
    def annotation_pattern(self):
        """A dictionary mapping the annotation keywords used to create this graph to their regex patterns
        from the ``DEFINE ANNOTATION [key] AS PATTERN "[value]"`` entries in the definitions section

        :rtype: dict[str,str]
        """
        return self.graph[GRAPH_ANNOTATION_PATTERN]

    @property
    def annotation_list(self):
        """A dictionary mapping the keywords of locally defined annotations to a set of their values
        from the ``DEFINE ANNOTATION [key] AS LIST {"[value]", ...}`` entries in the definitions section

        :rtype: dict[str,set[str]]
        """
        return self.graph[GRAPH_ANNOTATION_LIST]

    @property
    def defined_annotation_keywords(self):
        """Returns the set of all keywords defined as annotations in this graph

        :rtype: set[str]
        """
        return (
            set(self.annotation_pattern) |
            set(self.annotation_url) |
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
        """Add a warning to the internal warning log in the graph, with optional context information.

        :param int line_number: The line number on which the exception occurred
        :param str line: The line on which the exception occurred
        :param Exception exception: The exception that occurred
        :param Optional[dict] context: The context from the parser when the exception occurred
        """
        self.warnings.append((line_number, line, exception, {} if context is None else context))

    def _help_add_edge(self, u, v, attr):
        """Help add a pre-built edge.

        :type u: BaseEntity
        :type v: BaseEntity
        :type attr: dict
        :return: str
        """
        self.add_node_from_data(u)
        self.add_node_from_data(v)

        return self._help_add_edge_helper(u, v, attr)

    def _help_add_edge_helper(self, u, v, attr):
        key = hash_edge(u, v, attr)

        if not self.has_edge(u, v, key):
            self.add_edge(u, v, key=key, **attr)

        return key

    def add_unqualified_edge(self, u, v, relation):
        """Add a unique edge that has no annotations.

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        :param str relation: A relationship label from :mod:`pybel.constants`

        :return: The key for this edge (a unique hash)
        :rtype: str
        """
        attr = {RELATION: relation}
        return self._help_add_edge(u, v, attr)

    def add_transcription(self, u, v):
        """Add a transcription relation from a gene to an RNA or miRNA node.

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        """
        return self.add_unqualified_edge(u, v, TRANSCRIBED_TO)

    def add_translation(self, u, v):
        """Add a translation relation from a RNA to a protein.

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        """
        return self.add_unqualified_edge(u, v, TRANSLATED_TO)

    def _add_two_way_unqualified_edge(self, u, v, relation):
        """Add an unqualified edge both ways."""
        self.add_unqualified_edge(v, u, relation)
        return self.add_unqualified_edge(u, v, relation)

    def add_equivalence(self, u, v):
        """Add two equivalence relations for the nodes.

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        """
        return self._add_two_way_unqualified_edge(u, v, EQUIVALENT_TO)

    def add_orthology(self, u, v):
        """Add two orthology relations for the nodes.

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        """
        return self._add_two_way_unqualified_edge(u, v, ORTHOLOGOUS)

    def add_is_a(self, u, v):
        """Add an isA relationship such that ``u isA v``.

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        """
        return self.add_unqualified_edge(u, v, IS_A)

    def add_part_of(self, u, v):
        """Add an partOf relationship such that ``u partOf v``.

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        """
        return self.add_unqualified_edge(u, v, PART_OF)

    def add_has_member(self, u, v):
        """Add an hasMember relationship such that ``u hasMember v``.

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        """
        return self.add_unqualified_edge(u, v, HAS_MEMBER)

    def add_has_component(self, u, v):
        """Add an hasComponent relationship such that u hasComponent v.

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        """
        return self.add_unqualified_edge(u, v, HAS_COMPONENT)

    def add_has_variant(self, u, v):
        """Add an hasVariant relationship such that ``u hasVariant v``.

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        """
        return self.add_unqualified_edge(u, v, HAS_VARIANT)

    def add_increases(self, u, v, evidence, citation, annotations=None, subject_modifier=None, object_modifier=None,
                      **attr):
        """Add an increases relationship with :meth:`add_qualified_edge` using :data:`pybel.constants.INCREASES`.

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        :param str evidence: The evidence string from an article
        :param dict[str,str] or str citation: The citation data dictionary for this evidence. If a string is given,
                                                assumes it's a PubMed identifier and auto-fills the citation type.
        :param annotations: The annotations data dictionary
        :type annotations: Optional[dict[str,str] or dict[str,set] or dict[str,dict[str,bool]]]
        :param Optional[dict] subject_modifier: The modifiers (like activity) on the subject node. See data model
         documentation.
        :param Optional[dict] object_modifier: The modifiers (like activity) on the object node. See data model
         documentation.

        :return: The hash of the edge
        :rtype: str
        """
        return self.add_qualified_edge(u=u, v=v, relation=INCREASES, evidence=evidence, citation=citation,
                                       annotations=annotations, subject_modifier=subject_modifier,
                                       object_modifier=object_modifier, **attr)

    def add_directly_increases(self, u, v, evidence, citation, annotations=None, subject_modifier=None,
                               object_modifier=None, **attr):
        """Add a :data:`pybel.constants.DIRECTLY_INCREASES` with :meth:`add_qualified_edge`.

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        :param str evidence: The evidence string from an article
        :param dict[str,str] or str citation: The citation data dictionary for this evidence. If a string is given,
                                                assumes it's a PubMed identifier and auto-fills the citation type.
        :param annotations: The annotations data dictionary
        :type annotations: Optional[dict[str,str] or dict[str,set] or dict[str,dict[str,bool]]]
        :param Optional[dict] subject_modifier: The modifiers (like activity) on the subject node. See data model
         documentation.
        :param Optional[dict] object_modifier: The modifiers (like activity) on the object node. See data model
         documentation.

        :return: The hash of the edge
        :rtype: str
        """
        return self.add_qualified_edge(u=u, v=v, relation=DIRECTLY_INCREASES, evidence=evidence, citation=citation,
                                       annotations=annotations, subject_modifier=subject_modifier,
                                       object_modifier=object_modifier, **attr)

    def add_decreases(self, u, v, evidence, citation, annotations=None, subject_modifier=None, object_modifier=None,
                      **attr):
        """Add a :data:`pybel.constants.DECREASES` relationship with :meth:`add_qualified_edge`.

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        :param str evidence: The evidence string from an article
        :param dict[str,str] or str citation: The citation data dictionary for this evidence. If a string is given,
                                                assumes it's a PubMed identifier and auto-fills the citation type.
        :param annotations: The annotations data dictionary
        :type annotations: Optional[dict[str,str] or dict[str,set] or dict[str,dict[str,bool]]]
        :param Optional[dict] subject_modifier: The modifiers (like activity) on the subject node. See data model
         documentation.
        :param Optional[dict] object_modifier: The modifiers (like activity) on the object node. See data model
         documentation.

        :return: The hash of the edge
        :rtype: str
        """
        return self.add_qualified_edge(u=u, v=v, relation=DECREASES, evidence=evidence, citation=citation,
                                       annotations=annotations, subject_modifier=subject_modifier,
                                       object_modifier=object_modifier, **attr)

    def add_directly_decreases(self, u, v, evidence, citation, annotations=None, subject_modifier=None,
                               object_modifier=None, **attr):
        """Add a :data:`pybel.constants.DIRECTLY_DECREASES` relationship with :meth:`add_qualified_edge`.

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        :param str evidence: The evidence string from an article
        :param dict[str,str] or str citation: The citation data dictionary for this evidence. If a string is given,
                                                assumes it's a PubMed identifier and auto-fills the citation type.
        :param annotations: The annotations data dictionary
        :type annotations: Optional[dict[str,str] or dict[str,set] or dict[str,dict[str,bool]]]
        :param Optional[dict] subject_modifier: The modifiers (like activity) on the subject node. See data model
         documentation.
        :param Optional[dict] object_modifier: The modifiers (like activity) on the object node. See data model
         documentation.

        :return: The hash of the edge
        :rtype: str
        """
        return self.add_qualified_edge(u=u, v=v, relation=DIRECTLY_DECREASES, evidence=evidence, citation=citation,
                                       annotations=annotations, subject_modifier=subject_modifier,
                                       object_modifier=object_modifier, **attr)

    def add_association(self, u, v, evidence, citation, annotations=None, subject_modifier=None, object_modifier=None,
                        **attr):
        """Add an association relation to the network.

        Wraps :meth:`add_qualified_edge` for :data:`pybel.constants.ASSOCIATION`.

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        :param str evidence: The evidence string from an article
        :param dict[str,str] or str citation: The citation data dictionary for this evidence. If a string is given,
                                                assumes it's a PubMed identifier and auto-fills the citation type.
        :param annotations: The annotations data dictionary
        :type annotations: Optional[dict[str,str] or dict[str,set] or dict[str,dict[str,bool]]]
        :param Optional[dict] subject_modifier: The modifiers (like activity) on the subject node. See data model
         documentation.
        :param Optional[dict] object_modifier: The modifiers (like activity) on the object node. See data model
         documentation.

        :return: The hash of the edge
        :rtype: str
        """
        return self.add_qualified_edge(u=u, v=v, relation=ASSOCIATION, evidence=evidence, citation=citation,
                                       annotations=annotations, subject_modifier=subject_modifier,
                                       object_modifier=object_modifier, **attr)

    def add_node_from_data(self, node):
        """Convert a PyBEL node data dictionary to a canonical PyBEL node and ensures it is in the graph.

        :param BaseEntity node: A PyBEL node
        :rtype: BaseEntity
        """
        assert isinstance(node, BaseEntity)

        if node in self:
            return node

        self.add_node(node)

        if VARIANTS in node:
            self.add_has_variant(node.get_parent(), node)

        elif MEMBERS in node:
            for member in node[MEMBERS]:
                self.add_has_component(node, member)

        elif PRODUCTS in node and REACTANTS in node:
            for reactant_tokens in node[REACTANTS]:
                self.add_unqualified_edge(node, reactant_tokens, HAS_REACTANT)

            for product_tokens in node[PRODUCTS]:
                self.add_unqualified_edge(node, product_tokens, HAS_PRODUCT)

        return node

    def add_qualified_edge(self, u, v, relation, evidence, citation, annotations=None, subject_modifier=None,
                           object_modifier=None, **attr):
        """Add a qualified edge.

        Qualified edges have a relation, evidence, citation, and optional annotations, subject modifications,
        and object modifications.

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        :param str relation: The type of relation this edge represents
        :param str evidence: The evidence string from an article
        :param dict[str,str] or str citation: The citation data dictionary for this evidence. If a string is given,
                                                assumes it's a PubMed identifier and auto-fills the citation type.
        :param annotations: The annotations data dictionary
        :type annotations: Optional[dict[str,str] or dict[str,set] or dict[str,dict[str,bool]]]
        :param Optional[dict] subject_modifier: The modifiers (like activity) on the subject node. See data model
         documentation.
        :param Optional[dict] object_modifier: The modifiers (like activity) on the object node. See data model
         documentation.

        :return: The hash of the edge
        :rtype: str
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

        if annotations:  # clean up annotations
            attr[ANNOTATIONS] = _clean_annotations(annotations)

        if subject_modifier:
            attr[SUBJECT] = subject_modifier

        if object_modifier:
            attr[OBJECT] = object_modifier

        return self._help_add_edge(u, v, attr)

    def add_inhibits(self, u, v, evidence, citation, annotations=None, object_modifier=None):
        """Add an "inhibits" relationship.

        A more specific version of add_qualified edge that automatically populates the relation and object
        modifier

        :param BaseEntity u: The source node
        :param BaseEntity v: The target node
        :param str evidence: The evidence string from an article
        :param dict[str,str] or str citation: The citation data dictionary for this evidence. If a string is given,
                                                assumes it's a PubMed identifier and autofills the citation type.
        :param annotations: The annotations data dictionary
        :type annotations: Optional[dict[str,str] or dict[str,set] or dict[str,dict[str,bool]]]
        :param Optional[dict] object_modifier: A non-default activity.

        :return: The hash of the edge
        :rtype: str
        """
        return self.add_qualified_edge(
            u,
            v,
            relation=DECREASES,
            evidence=evidence,
            citation=citation,
            annotations=annotations,
            object_modifier=object_modifier or activity()
        )

    def _has_edge_attr(self, u, v, key, attr):
        """
        :type u: BaseEntity
        :type v: BaseEntity
        :type key: str
        :type attr: str
        :rtype: bool
        """
        assert isinstance(u, BaseEntity)
        assert isinstance(v, BaseEntity)

        return attr in self[u][v][key]

    def has_edge_citation(self, u, v, key):
        """Check if the given edge has a citation.

        :rtype: bool
        """
        return self._has_edge_attr(u, v, key, CITATION)

    def has_edge_evidence(self, u, v, key):
        """Check if the given edge has an evidence.

        :rtype: boolean
        """
        return self._has_edge_attr(u, v, key, EVIDENCE)

    def _get_edge_attr(self, u, v, key, attr):
        return self[u][v][key].get(attr)

    def get_edge_citation(self, u, v, key):
        """Get the citation for a given edge.

        :rtype: Optional[dict]
        """
        return self._get_edge_attr(u, v, key, CITATION)

    def get_edge_evidence(self, u, v, key):
        """Get the evidence for a given edge.

        :rtype: Optional[str]
        """
        return self._get_edge_attr(u, v, key, EVIDENCE)

    def get_edge_annotations(self, u, v, key):
        """Get the annotations for a given edge.

        :rtype: Optional[dict]
        """
        return self._get_edge_attr(u, v, key, ANNOTATIONS)

    def _get_node_attr(self, node, attr):
        assert isinstance(node, BaseEntity)
        return self.nodes[node].get(attr)

    def _has_node_attr(self, node, attr):
        assert isinstance(node, BaseEntity)
        return attr in self.nodes[node]

    def _set_node_attr(self, node, attr, value):
        assert isinstance(node, BaseEntity)
        self.nodes[node][attr] = value

    def get_node_description(self, node):
        """Get the description for a given node.

        :type node: BaseEntity
        :rtype: Optional[str]
        """
        return self._get_node_attr(node, DESCRIPTION)

    def has_node_description(self, node):
        """Check if a node description is already present.

        :param BaseEntity node: A PyBEL node tuple
        :rtype: bool
        """
        return self._has_node_attr(node, DESCRIPTION)

    def set_node_description(self, node, description):
        """Set the description for a given node.

        :param BaseEntity node: A PyBEL node
        :type description: str
        """
        self._set_node_attr(node, DESCRIPTION, description)

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
        if not isinstance(other, BELGraph):
            raise TypeError('{} is not a {}'.format(other, self.__class__.__name__))

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
        if not isinstance(other, BELGraph):
            raise TypeError('{} is not a {}'.format(other, self.__class__.__name__))

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
        if not isinstance(other, BELGraph):
            raise TypeError('{} is not a {}'.format(other, self.__class__.__name__))

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
        if not isinstance(other, BELGraph):
            raise TypeError('{} is not a {}'.format(other, self.__class__.__name__))

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
        if not isinstance(other, BELGraph):
            raise TypeError('{} is not a {}'.format(other, self.__class__.__name__))

        return left_node_intersection_join(self, other)

    @staticmethod
    def node_to_bel(n):
        """Serialize a node as BEL.

        :param BaseEntity n: A PyBEL node
        :rtype: str
        """
        return n.as_bel()

    @staticmethod
    def edge_to_bel(u, v, data, sep=None):
        """Serialize a pair of nodes and related edge data as a BEL relation.

        :type u: BaseEntity
        :type v: BaseEntity
        :param dict data: A PyBEL edge data dictionary
        :param Optional[str] sep: The separator between the source, relation, and target. Defaults to ' '
        :rtype: str
        """
        return edge_to_bel(u, v, data=data, sep=sep)

    def _has_no_equivalent_edge(self, u, v):
        return not any(
            EQUIVALENT_TO == data[RELATION]
            for data in self[u][v].values()
        )

    def _equivalent_node_iterator_helper(self, node, visited):
        """Iterate over nodes and their data that are equal to the given node, starting with the original.

        :param BaseEntity node: A PyBEL node
        :rtype: iter[BaseEntity]
        """
        for v in self[node]:
            if v in visited:
                continue

            if self._has_no_equivalent_edge(node, v):
                continue

            yield v
            visited.add(v)

            for w in self._equivalent_node_iterator_helper(v, visited):
                yield w

    def iter_equivalent_nodes(self, node):
        """Iterate over nodes that are equivalent to the given node, including the original,

        :param BaseEntity node: A PyBEL node
        :rtype: iter[BaseEntity]
        """
        yield node

        for n in self._equivalent_node_iterator_helper(node, {node}):
            yield n

    def get_equivalent_nodes(self, node):
        """Get a set of equivalent nodes to this node, excluding the given node.

        :param node: A PyBEL node
        :type node: BaseEntity
        :rtype: set[BaseEntity]
        """
        if isinstance(node, BaseEntity):
            return set(self.iter_equivalent_nodes(node))

        return set(self.iter_equivalent_nodes(node))

    def _node_has_namespace_helper(self, node, namespace):
        """Check that the node has namespace information.

        Might have cross references in future.

        :param BaseEntity node: A PyBEL node
        :rtype: bool
        """
        return namespace == node.get(NAMESPACE)

    def node_has_namespace(self, node, namespace):
        """Check if the node have the given namespace?

        This also should look in the equivalent nodes.

        :param BaseEntity node: A PyBEL node
        :param str namespace: A namespace
        :rtype: bool
        """
        return any(
            self._node_has_namespace_helper(n, namespace)
            for n in self.iter_equivalent_nodes(node)
        )

    def _describe_list(self):
        """Return useful information about the graph as a list of tuples.

        :rtype: list[tuple[str,float]]
        """
        number_nodes = self.number_of_nodes()
        return [
            ('Number of Nodes', number_nodes),
            ('Number of Edges', self.number_of_edges()),
            ('Network Density', '{:.2E}'.format(nx.density(self))),
            ('Number of Components', nx.number_weakly_connected_components(self)),
            ('Number of Warnings', len(self.warnings)),
        ]

    def summary_dict(self):
        """Return a dictionary that summarizes the graph.

        :rtype: dict[str,float]
        """
        return dict(self._describe_list())

    def summary_str(self):
        """Return a string that summarizes the graph.

        :rtype: str
        """
        return '{}\n'.format(self) + '\n'.join(
            '{}: {}'.format(label, value)
            for label, value in self._describe_list()
        )

    def summarize(self, file=None):
        """Print a summary of the graph.

        :param Optional[file] file: A file or file-like to print to. Defaults to standard out.
        """
        print(self.summary_str(), file=file)

    def serialize(self, fmt='nodelink', file=None):
        """Serialize the graph to an object or file if given."""
        if file is None:
            return self._serialize_object(fmt=fmt)
        elif isinstance(file, string_types):
            with open(file, 'w') as file_obj:
                self._serialize_file(fmt=fmt, file=file_obj)
        else:
            self._serialize_file(fmt=fmt, file=file)

    def _serialize_object(self, fmt):
        object_exporter = self._get_serialize_entry_point('pybel.object_exporter', fmt)
        return object_exporter(self)

    def _serialize_file(self, fmt, file):
        file_exporter = self._get_serialize_entry_point('pybel.file_exporter', fmt)
        return file_exporter(self, file)

    @staticmethod
    def _get_serialize_entry_point(group, name):
        entry_points = list(iter_entry_points(group=group, name=name))

        if 0 == len(entry_points):
            raise ValueError('no format {}'.format(name))

        return entry_points[0].load()
