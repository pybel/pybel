# -*- coding: utf-8 -*-

"""Contains the main data structure for PyBEL."""

import logging
from copy import deepcopy
from typing import Any, Dict, Hashable, Iterable, List, Mapping, Optional, Set, TextIO, Tuple, Union

import networkx as nx
from pkg_resources import iter_entry_points
from six import string_types

from .operations import left_full_join, left_node_intersection_join, left_outer_join
from ..canonicalize import edge_to_bel
from ..constants import (
    ANNOTATIONS, ASSOCIATION, CITATION, CITATION_REFERENCE, CITATION_TYPE, CITATION_TYPE_PUBMED, DECREASES, DESCRIPTION,
    DIRECTLY_DECREASES, DIRECTLY_INCREASES, EQUIVALENT_TO, EVIDENCE, GRAPH_ANNOTATION_LIST, GRAPH_ANNOTATION_PATTERN,
    GRAPH_ANNOTATION_URL, GRAPH_METADATA, GRAPH_NAMESPACE_PATTERN, GRAPH_NAMESPACE_URL, GRAPH_PATH, GRAPH_PYBEL_VERSION,
    GRAPH_UNCACHED_NAMESPACES, HAS_COMPONENT, HAS_MEMBER, HAS_PRODUCT, HAS_REACTANT, HAS_VARIANT, INCREASES, IS_A,
    MEMBERS, METADATA_AUTHORS, METADATA_CONTACT, METADATA_COPYRIGHT, METADATA_DESCRIPTION, METADATA_DISCLAIMER,
    METADATA_LICENSES, METADATA_NAME, METADATA_VERSION, NAMESPACE, OBJECT, ORTHOLOGOUS, PART_OF, PRODUCTS, REACTANTS,
    RELATION, SUBJECT, TRANSCRIBED_TO, TRANSLATED_TO, VARIANTS,
)
from ..dsl import BaseEntity, Gene, MicroRna, Protein, Rna, activity
from ..parser.exc import PyBelParserWarning
from ..typing import EdgeData
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

CitationDict = Mapping[str, str]
AnnotationsDict = Mapping[str, Mapping[str, bool]]
AnnotationsHint = Union[Mapping[str, str], Mapping[str, Set[str]], AnnotationsDict]


class BELGraph(nx.MultiDiGraph):
    """An extension to :class:`networkx.MultiDiGraph` to represent BEL."""

    def __init__(self,
                 name: Optional[str] = None,
                 version: Optional[str] = None,
                 description: Optional[str] = None,
                 authors: Optional[str] = None,
                 contact: Optional[str] = None,
                 license: Optional[str] = None,
                 copyright: Optional[str] = None,
                 disclaimer: Optional[str] = None,
                 path: Optional[str] = None,
                 data=None,
                 **kwargs
                 ) -> None:
        """Initialize a BEL graph with its associated metadata.

        :param name: The graph's name
        :param version: The graph's version. Recommended to use `semantic versioning <http://semver.org/>`_ or
         ``YYYYMMDD`` format.
        :param description: A description of the graph
        :param authors: The authors of this graph
        :param contact: The contact email for this graph
        :param license: The license for this graph
        :param copyright: The copyright for this graph
        :param disclaimer: The disclaimer for this graph
        :param data: initial graph data to pass to :class:`networkx.MultiDiGraph`
        :param kwargs: keyword arguments to pass to :class:`networkx.MultiDiGraph`

        For IO, see the :mod:`pybel.io` module.
        """
        super().__init__(data=data, **kwargs)

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

        if path:
            self.path = path

        if GRAPH_PYBEL_VERSION not in self.graph:
            self.graph[GRAPH_PYBEL_VERSION] = get_version()

        for resource_dict in RESOURCE_DICTIONARY_NAMES:
            if resource_dict not in self.graph:
                self.graph[resource_dict] = {}

        if GRAPH_UNCACHED_NAMESPACES not in self.graph:
            self.graph[GRAPH_UNCACHED_NAMESPACES] = set()

    def fresh_copy(self) -> 'BELGraph':
        """Create an unfilled :class:`BELGraph` as a hook for other :mod:`networkx` functions.

        Is necessary for .copy() to work.
        """
        return BELGraph()

    @property
    def path(self) -> Optional[str]:
        """Get the graph's path."""
        return self.graph.get(GRAPH_PATH)

    @path.setter
    def path(self, path: str) -> None:
        """Set the graph's path."""
        self.graph[GRAPH_PATH] = path

    @property
    def document(self):
        """Get the dictionary holding the metadata from the ``SET DOCUMENT`` statements in the source BEL script.

        All keys are normalized according to :data:`pybel.constants.DOCUMENT_KEYS`.

        :rtype: dict[str,Any]
        """
        return self.graph[GRAPH_METADATA]

    @property
    def name(self, *attrs) -> str:  # Needs *attrs since it's an override
        """Get the graph's name.

        .. hint:: Can be set with the ``SET DOCUMENT Name = "..."`` entry in the source BEL script.
        """
        return self.document.get(METADATA_NAME)

    @name.setter
    def name(self, *attrs, **kwargs):  # Needs *attrs and **kwargs since it's an override
        """Set the graph's name."""
        self.document[METADATA_NAME] = attrs[0]

    @property
    def version(self) -> str:
        """Get the graph's version.

        .. hint:: Can be set with the ``SET DOCUMENT Version = "..."`` entry in the source BEL script.
        """
        return self.document.get(METADATA_VERSION)

    @version.setter
    def version(self, version):
        """Set the graph's version."""
        self.document[METADATA_VERSION] = version

    @property
    def description(self) -> str:
        """Get the graph's description.

        .. hint:: Can be set with the ``SET DOCUMENT Description = "..."`` entry in the source BEL document.
        """
        return self.document.get(METADATA_DESCRIPTION)

    @description.setter
    def description(self, description: str) -> None:
        """Set the graph's description."""
        self.document[METADATA_DESCRIPTION] = description

    @property
    def authors(self) -> str:
        """Get the graph's description.

        .. hint:: Can be set with the ``SET DOCUMENT Authors = "..."`` entry in the source BEL document.
        """
        return self.document[METADATA_AUTHORS]

    @authors.setter
    def authors(self, authors: str) -> None:
        """Set the graph's authors."""
        self.document[METADATA_AUTHORS] = authors

    @property
    def contact(self) -> str:
        """Get the graph's contact information.

        .. hint:: Can be set with the ``SET DOCUMENT ContactInfo = "..."`` entry in the source BEL document.
        """
        return self.document.get(METADATA_CONTACT)

    @contact.setter
    def contact(self, contact: str) -> None:
        """Set the graph's contact."""
        self.document[METADATA_CONTACT] = contact

    @property
    def license(self) -> Optional[str]:
        """Get the graph's license.

        .. hint:: Can be set with the ``SET DOCUMENT Licenses = "..."`` entry in the source BEL document
        """
        return self.document.get(METADATA_LICENSES)

    @license.setter
    def license(self, license_str: str) -> None:
        """Set the graph's license."""
        self.document[METADATA_LICENSES] = license_str

    @property
    def copyright(self) -> Optional[str]:
        """Get the graph's copyright.

        .. hint:: Can be set with the ``SET DOCUMENT Copyright = "..."`` entry in the source BEL document
        """
        return self.document.get(METADATA_COPYRIGHT)

    @copyright.setter
    def copyright(self, copyright_str: str) -> None:
        """Set the graph's copyright."""
        self.document[METADATA_COPYRIGHT] = copyright_str

    @property
    def disclaimer(self) -> Optional[str]:
        """Get the graph's disclaimer.

        .. hint:: Can be set with the ``SET DOCUMENT Disclaimer = "..."`` entry in the source BEL document.
        """
        return self.document.get(METADATA_DISCLAIMER)

    @disclaimer.setter
    def disclaimer(self, disclaimer: str) -> None:
        """Set the graph's disclaimer."""
        self.document[METADATA_DISCLAIMER] = disclaimer

    @property
    def namespace_url(self) -> Dict[str, str]:
        """Get the mapping from the keywords used in this graph to their respective BEL namespace URLs.

        .. hint:: Can be appended with the ``DEFINE NAMESPACE [key] AS URL "[value]"`` entries in the definitions
                  section of the source BEL document.
        """
        return self.graph[GRAPH_NAMESPACE_URL]

    @property
    def defined_namespace_keywords(self) -> Set[str]:
        """Get the set of all keywords defined as namespaces in this graph."""
        return set(self.namespace_pattern) | set(self.namespace_url)

    @property
    def uncached_namespaces(self) -> Set[str]:
        """Get the set of namespaces URLs that are present in the graph, but cannot be cached.

        Namespaces are added to this set when their corresponding resources' cachable flags being set to "no."
        """
        return self.graph[GRAPH_UNCACHED_NAMESPACES]

    @property
    def namespace_pattern(self) -> Dict[str, str]:
        """Get the mapping from the namespace keywords used to create this graph to their regex patterns.

        .. hint:: Can be appended with the ``DEFINE NAMESPACE [key] AS PATTERN "[value]"`` entries in the definitions
                  section of the source BEL document.
        """
        return self.graph[GRAPH_NAMESPACE_PATTERN]

    @property
    def annotation_url(self) -> Dict[str, str]:
        """Get the mapping from the annotation keywords used to create this graph to the URLs of the BELANNO files.

        .. hint:: Can be appended with the ``DEFINE ANNOTATION [key] AS URL "[value]"`` entries in the definitions
                  section of the source BEL document.
        """
        return self.graph[GRAPH_ANNOTATION_URL]

    @property
    def annotation_pattern(self) -> Dict[str, str]:
        """Get the mapping from the annotation keywords used to create this graph to their regex patterns as strings.

        .. hint:: Can be appended with the ``DEFINE ANNOTATION [key] AS PATTERN "[value]"`` entries in the definitions
                  section of the source BEL document.
        """
        return self.graph[GRAPH_ANNOTATION_PATTERN]

    @property
    def annotation_list(self) -> Dict[str, Set[str]]:
        """Get the mapping from the keywords of locally defined annotations to their respective sets of values.

        .. hint:: Can be appended with the ``DEFINE ANNOTATION [key] AS LIST {"[value]", ...}`` entries in the
                  definitions section of the source BEL document.
        """
        return self.graph[GRAPH_ANNOTATION_LIST]

    @property
    def defined_annotation_keywords(self) -> Set[str]:
        """Get the set of all keywords defined as annotations in this graph."""
        return (
            set(self.annotation_pattern) |
            set(self.annotation_url) |
            set(self.annotation_list)
        )

    @property
    def pybel_version(self) -> str:
        """Get the version of PyBEL with which this graph was produced as a string."""
        return self.graph[GRAPH_PYBEL_VERSION]

    @property
    def warnings(self) -> List[Tuple[int, str, PyBelParserWarning, Mapping[str, str]]]:
        """Get the warnings stored in a list of 4-tuples that is a property of the graph object.

        This tuple respectively contains the line number, the line text, the exception instance, and the context
        dictionary from the parser at the time of error.
        """
        return self._warnings

    def number_of_warnings(self) -> int:
        """Return the number of warnings."""
        return len(self.warnings)

    def __str__(self):
        return '{} v{}'.format(self.name, self.version)

    def skip_storing_namespace(self, namespace: Optional[str]) -> bool:
        """Check if the namespace should be skipped."""
        return (
            namespace is not None and
            namespace in self.namespace_url and
            self.namespace_url[namespace] in self.uncached_namespaces
        )

    def add_warning(self,
                    line_number: int,
                    line: str,
                    exception: Exception,
                    context: Optional[Mapping[str, Any]] = None,
                    ) -> None:
        """Add a warning to the internal warning log in the graph, with optional context information.

        :param line_number: The line number on which the exception occurred
        :param line: The line on which the exception occurred
        :param exception: The exception that occurred
        :param context: The context from the parser when the exception occurred
        """
        self.warnings.append((line_number, line, exception, {} if context is None else context))

    def _help_add_edge(self, u: BaseEntity, v: BaseEntity, attr: Mapping) -> str:
        """Help add a pre-built edge."""
        self.add_node_from_data(u)
        self.add_node_from_data(v)

        return self._help_add_edge_helper(u, v, attr)

    def _help_add_edge_helper(self, u: BaseEntity, v: BaseEntity, attr: Mapping) -> str:
        key = hash_edge(u, v, attr)

        if not self.has_edge(u, v, key):
            self.add_edge(u, v, key=key, **attr)

        return key

    def add_unqualified_edge(self, u: BaseEntity, v: BaseEntity, relation: str) -> str:
        """Add a unique edge that has no annotations.

        :param u: The source node
        :param v: The target node
        :param relation: A relationship label from :mod:`pybel.constants`
        :return: The key for this edge (a unique hash)
        """
        attr = {RELATION: relation}
        return self._help_add_edge(u, v, attr)

    def add_transcription(self, u: Gene, v: Union[Rna, MicroRna]) -> str:
        """Add a transcription relation from a gene to an RNA or miRNA node."""
        return self.add_unqualified_edge(u, v, TRANSCRIBED_TO)

    def add_translation(self, u: Rna, v: Protein) -> str:
        """Add a translation relation from a RNA to a protein."""
        return self.add_unqualified_edge(u, v, TRANSLATED_TO)

    def _add_two_way_unqualified_edge(self, u: BaseEntity, v: BaseEntity, relation: str) -> str:
        """Add an unqualified edge both ways."""
        self.add_unqualified_edge(v, u, relation)
        return self.add_unqualified_edge(u, v, relation)

    def add_equivalence(self, u: BaseEntity, v: BaseEntity) -> str:
        """Add two equivalence relations for the nodes."""
        return self._add_two_way_unqualified_edge(u, v, EQUIVALENT_TO)

    def add_orthology(self, u: BaseEntity, v: BaseEntity) -> str:
        """Add two orthology relations for the nodes."""
        return self._add_two_way_unqualified_edge(u, v, ORTHOLOGOUS)

    def add_is_a(self, u: BaseEntity, v: BaseEntity) -> str:
        """Add an isA relationship such that ``u isA v``."""
        return self.add_unqualified_edge(u, v, IS_A)

    def add_part_of(self, u: BaseEntity, v: BaseEntity) -> str:
        """Add a ``partOf`` relationship such that ``u partOf v``."""
        return self.add_unqualified_edge(u, v, PART_OF)

    def add_has_member(self, u: BaseEntity, v: BaseEntity) -> str:
        """Add a ``hasMember`` relationship such that ``u hasMember v``."""
        return self.add_unqualified_edge(u, v, HAS_MEMBER)

    def add_has_component(self, u: BaseEntity, v: BaseEntity) -> str:
        """Add an ``hasComponent`` relationship such that u hasComponent v."""
        return self.add_unqualified_edge(u, v, HAS_COMPONENT)

    def add_has_variant(self, u: BaseEntity, v: BaseEntity) -> str:
        """Add an ``hasVariant`` relationship such that ``u hasVariant v``."""
        return self.add_unqualified_edge(u, v, HAS_VARIANT)

    def add_increases(self,
                      u: BaseEntity,
                      v: BaseEntity,
                      evidence: str,
                      citation: Union[str, CitationDict],
                      annotations: Optional[AnnotationsHint] = None,
                      subject_modifier: Optional[Mapping] = None,
                      object_modifier: Optional[Mapping] = None,
                      **attr,
                      ) -> str:
        """Wrap :meth:`add_qualified_edge` for the :data:`pybel.constants.INCREASES` relation."""
        return self.add_qualified_edge(
            u=u, v=v, relation=INCREASES, evidence=evidence, citation=citation, annotations=annotations,
            subject_modifier=subject_modifier, object_modifier=object_modifier, **attr,
        )

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

    def add_qualified_edge(self,
                           u,
                           v,
                           relation: str,
                           evidence: str,
                           citation: Union[str, Mapping[str, str]],
                           annotations: Optional[AnnotationsHint] = None,
                           subject_modifier=None,
                           object_modifier=None,
                           **attr) -> str:
        """Add a qualified edge.

        Qualified edges have a relation, evidence, citation, and optional annotations, subject modifications,
        and object modifications.

        :param u: The source node
        :param v: The target node
        :param relation: The type of relation this edge represents
        :param evidence: The evidence string from an article
        :param citation: The citation data dictionary for this evidence. If a string is given,
                                                assumes it's a PubMed identifier and auto-fills the citation type.
        :param annotations: The annotations data dictionary
        :param Optional[dict] subject_modifier: The modifiers (like activity) on the subject node. See data model
         documentation.
        :param Optional[dict] object_modifier: The modifiers (like activity) on the object node. See data model
         documentation.

        :return: The hash of the edge
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

    def _has_edge_attr(self, u: BaseEntity, v: BaseEntity, key: str, attr: Hashable) -> bool:
        assert isinstance(u, BaseEntity)
        assert isinstance(v, BaseEntity)
        return attr in self[u][v][key]

    def has_edge_citation(self, u: BaseEntity, v: BaseEntity, key: str) -> bool:
        """Check if the given edge has a citation."""
        return self._has_edge_attr(u, v, key, CITATION)

    def has_edge_evidence(self, u: BaseEntity, v: BaseEntity, key: str) -> bool:
        """Check if the given edge has an evidence."""
        return self._has_edge_attr(u, v, key, EVIDENCE)

    def _get_edge_attr(self, u: BaseEntity, v: BaseEntity, key: str, attr: str):
        return self[u][v][key].get(attr)

    def get_edge_citation(self, u: BaseEntity, v: BaseEntity, key: str) -> Optional[CitationDict]:
        """Get the citation for a given edge."""
        return self._get_edge_attr(u, v, key, CITATION)

    def get_edge_evidence(self, u: BaseEntity, v: BaseEntity, key: str) -> Optional[str]:
        """Get the evidence for a given edge."""
        return self._get_edge_attr(u, v, key, EVIDENCE)

    def get_edge_annotations(self, u, v, key: str) -> Optional[AnnotationsDict]:
        """Get the annotations for a given edge."""
        return self._get_edge_attr(u, v, key, ANNOTATIONS)

    def _get_node_attr(self, node: BaseEntity, attr: str) -> Any:
        assert isinstance(node, BaseEntity)
        return self.nodes[node].get(attr)

    def _has_node_attr(self, node: BaseEntity, attr: str) -> Any:
        assert isinstance(node, BaseEntity)
        return attr in self.nodes[node]

    def _set_node_attr(self, node: BaseEntity, attr: str, value: Any) -> None:
        assert isinstance(node, BaseEntity)
        self.nodes[node][attr] = value

    def get_node_description(self, node: BaseEntity) -> Optional[str]:
        """Get the description for a given node."""
        return self._get_node_attr(node, DESCRIPTION)

    def has_node_description(self, node: BaseEntity) -> bool:
        """Check if a node description is already present."""
        return self._has_node_attr(node, DESCRIPTION)

    def set_node_description(self, node: BaseEntity, description: str) -> None:
        """Set the description for a given node."""
        self._set_node_attr(node, DESCRIPTION, description)

    def __add__(self, other: 'BELGraph') -> 'BELGraph':
        """Copy this graph and join it with another graph with it using :func:`pybel.struct.left_full_join`.

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

    def __iadd__(self, other: 'BELGraph') -> 'BELGraph':
        """Join another graph into this one, in-place, using :func:`pybel.struct.left_full_join`.

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

    def __and__(self, other: 'BELGraph') -> 'BELGraph':
        """Create a deep copy of this graph and left outer joins another graph.

        Uses :func:`pybel.struct.left_outer_join`.

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

    def __iand__(self, other: 'BELGraph') -> 'BELGraph':
        """Join another graph into this one, in-place, using :func:`pybel.struct.left_outer_join`.

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

    def __xor__(self, other: 'BELGraph') -> 'BELGraph':
        """Join this graph with another using :func:`pybel.struct.left_node_intersection_join`.

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
    def node_to_bel(n: BaseEntity) -> str:
        """Serialize a node as BEL."""
        return n.as_bel()

    @staticmethod
    def edge_to_bel(u: BaseEntity, v: BaseEntity, edge_data: EdgeData, sep: Optional[str] = None) -> str:
        """Serialize a pair of nodes and related edge data as a BEL relation."""
        return edge_to_bel(u, v, data=edge_data, sep=sep)

    def _has_no_equivalent_edge(self, u: BaseEntity, v: BaseEntity) -> bool:
        return not any(
            EQUIVALENT_TO == data[RELATION]
            for data in self[u][v].values()
        )

    def _equivalent_node_iterator_helper(self, node: BaseEntity, visited: Set[BaseEntity]) -> BaseEntity:
        """Iterate over nodes and their data that are equal to the given node, starting with the original."""
        for v in self[node]:
            if v in visited:
                continue

            if self._has_no_equivalent_edge(node, v):
                continue

            visited.add(v)
            yield v
            yield from self._equivalent_node_iterator_helper(v, visited)

    def iter_equivalent_nodes(self, node: BaseEntity) -> Iterable[BaseEntity]:
        """Iterate over nodes that are equivalent to the given node, including the original."""
        yield node
        yield from self._equivalent_node_iterator_helper(node, {node})

    def get_equivalent_nodes(self, node: BaseEntity) -> Set[BaseEntity]:
        """Get a set of equivalent nodes to this node, excluding the given node."""
        if isinstance(node, BaseEntity):
            return set(self.iter_equivalent_nodes(node))

        return set(self.iter_equivalent_nodes(node))

    @staticmethod
    def _node_has_namespace_helper(node: BaseEntity, namespace: str) -> bool:
        """Check that the node has namespace information.

        Might have cross references in future.
        """
        return namespace == node.get(NAMESPACE)

    def node_has_namespace(self, node: BaseEntity, namespace: str) -> bool:
        """Check if the node have the given namespace.

        This also should look in the equivalent nodes.
        """
        return any(
            self._node_has_namespace_helper(n, namespace)
            for n in self.iter_equivalent_nodes(node)
        )

    def _describe_list(self) -> List[Tuple[str, float]]:
        """Return useful information about the graph as a list of tuples."""
        number_nodes = self.number_of_nodes()
        return [
            ('Number of Nodes', number_nodes),
            ('Number of Edges', self.number_of_edges()),
            ('Network Density', '{:.2E}'.format(nx.density(self))),
            ('Number of Components', nx.number_weakly_connected_components(self)),
            ('Number of Warnings', self.number_of_warnings()),
        ]

    def summary_dict(self) -> Mapping[str, float]:
        """Return a dictionary that summarizes the graph."""
        return dict(self._describe_list())

    def summary_str(self) -> str:
        """Return a string that summarizes the graph."""
        return '{}\n'.format(self) + '\n'.join(
            '{}: {}'.format(label, value)
            for label, value in self._describe_list()
        )

    def summarize(self, file: Optional[TextIO] = None) -> None:
        """Print a summary of the graph."""
        print(self.summary_str(), file=file)

    def serialize(self, fmt: str = 'nodelink', file: Union[str, TextIO] = None):
        """Serialize the graph to an object or file if given."""
        if file is None:
            return self._serialize_object(fmt=fmt)
        elif isinstance(file, string_types):
            with open(file, 'w') as file_obj:
                self._serialize_file(fmt=fmt, file=file_obj)
        else:
            self._serialize_file(fmt=fmt, file=file)

    def _serialize_object(self, fmt: str):
        object_exporter = self._get_serialize_entry_point('pybel.object_exporter', fmt)
        return object_exporter(self)

    def _serialize_file(self, fmt: str, file: TextIO):
        file_exporter = self._get_serialize_entry_point('pybel.file_exporter', fmt)
        return file_exporter(self, file)

    @staticmethod
    def _get_serialize_entry_point(group: str, name: str):
        entry_points = list(iter_entry_points(group=group, name=name))

        if 0 == len(entry_points):
            raise ValueError('no format {}'.format(name))

        return entry_points[0].load()


def _clean_annotations(annotations_dict: AnnotationsHint) -> AnnotationsDict:
    """Fix the formatting of annotation dict."""
    return {
        key: (
            values if isinstance(values, dict) else
            {v: True for v in values} if isinstance(values, set) else
            {values: True}
        )
        for key, values in annotations_dict.items()
    }
