# -*- coding: utf-8 -*-

"""Contains the main data structure for PyBEL."""

import logging
from collections import defaultdict
from copy import deepcopy
from functools import partialmethod
from itertools import chain
from typing import Any, Dict, Hashable, Iterable, List, Mapping, Optional, Set, TextIO, Tuple, Union

import networkx as nx

from .operations import left_full_join, left_node_intersection_join, left_outer_join
from ..canonicalize import edge_to_bel
from ..constants import (
    ANNOTATIONS, ASSOCIATION, CAUSES_NO_CHANGE, CITATION, CITATION_AUTHORS, CITATION_DB, CITATION_IDENTIFIER,
    CITATION_TYPE_PUBMED, CONCEPT, CORRELATION, DECREASES, DIRECTLY_DECREASES, DIRECTLY_INCREASES,
    EQUIVALENT_TO, EVIDENCE, GRAPH_ANNOTATION_LIST, GRAPH_ANNOTATION_PATTERN, GRAPH_ANNOTATION_URL,
    GRAPH_METADATA, GRAPH_NAMESPACE_PATTERN, GRAPH_NAMESPACE_URL, GRAPH_PATH, GRAPH_PYBEL_VERSION, HAS_PRODUCT,
    HAS_REACTANT, HAS_VARIANT, INCREASES, IS_A, MEMBERS, METADATA_AUTHORS, METADATA_CONTACT, METADATA_COPYRIGHT,
    METADATA_DESCRIPTION, METADATA_DISCLAIMER, METADATA_LICENSES, METADATA_NAME, METADATA_VERSION, NAMESPACE,
    NEGATIVE_CORRELATION, NO_CORRELATION, OBJECT, ORTHOLOGOUS, PART_OF, POSITIVE_CORRELATION, PRODUCTS, REACTANTS,
    REGULATES, RELATION, SUBJECT, TRANSCRIBED_TO, TRANSLATED_TO, VARIANTS,
)
from ..dsl import (
    BaseAbundance, BaseEntity, ComplexAbundance, Gene, MicroRna, Protein, ProteinModification, Reaction, Rna, activity,
)
from ..parser.exc import BELParserWarning
from ..typing import EdgeData
from ..utils import CitationDict, citation_dict, hash_edge
from ..version import get_version

__all__ = [
    'BELGraph',
]

logger = logging.getLogger(__name__)

AnnotationsDict = Mapping[str, Mapping[str, bool]]
AnnotationsHint = Union[Mapping[str, str], Mapping[str, Set[str]], AnnotationsDict]
WarningTuple = Tuple[Optional[str], BELParserWarning, EdgeData]


class BELGraph(nx.MultiDiGraph):
    """An extension to :class:`networkx.MultiDiGraph` to represent BEL."""

    def __init__(
        self,
        name: Optional[str] = None,
        version: Optional[str] = None,
        description: Optional[str] = None,
        authors: Optional[str] = None,
        contact: Optional[str] = None,
        license: Optional[str] = None,
        copyright: Optional[str] = None,
        disclaimer: Optional[str] = None,
        path: Optional[str] = None,
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
        """
        super().__init__()

        self._warnings = []

        self.graph[GRAPH_PYBEL_VERSION] = get_version()
        self.graph[GRAPH_METADATA] = {}

        self.graph[GRAPH_NAMESPACE_URL] = {}
        self.graph[GRAPH_NAMESPACE_PATTERN] = {}

        self.graph[GRAPH_ANNOTATION_URL] = {}
        self.graph[GRAPH_ANNOTATION_PATTERN] = {}
        self.graph[GRAPH_ANNOTATION_LIST] = defaultdict(set)

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

    @property
    def path(self) -> Optional[str]:  # noqa: D401
        """The graph's path, if it was derived from a BEL document."""
        return self.graph.get(GRAPH_PATH)

    @path.setter
    def path(self, path: str) -> None:
        """Set the graph's path."""
        self.graph[GRAPH_PATH] = path

    @property
    def document(self) -> Dict[str, Any]:  # noqa: D401
        """The dictionary holding the metadata from the ``SET DOCUMENT`` statements in the source BEL script.

        All keys are normalized according to :data:`pybel.constants.DOCUMENT_KEYS`.
        """
        return self.graph[GRAPH_METADATA]

    @property
    def name(self, *attrs) -> Optional[str]:  # noqa: D401 # Needs *attrs since it's an override
        """The graph's name.

        .. hint:: Can be set with the ``SET DOCUMENT Name = "..."`` entry in the source BEL script.
        """
        return self.document.get(METADATA_NAME)

    @name.setter
    def name(self, *attrs, **kwargs):  # Needs *attrs and **kwargs since it's an override
        """Set the graph's name."""
        self.document[METADATA_NAME] = attrs[0]

    @property
    def version(self) -> Optional[str]:  # noqa: D401
        """The graph's version.

        .. hint:: Can be set with the ``SET DOCUMENT Version = "..."`` entry in the source BEL script.
        """
        return self.document.get(METADATA_VERSION)

    @version.setter
    def version(self, version):
        """Set the graph's version."""
        self.document[METADATA_VERSION] = version

    @property
    def description(self) -> Optional[str]:  # noqa: D401
        """The graph's description.

        .. hint:: Can be set with the ``SET DOCUMENT Description = "..."`` entry in the source BEL document.
        """
        return self.document.get(METADATA_DESCRIPTION)

    @description.setter
    def description(self, description: str) -> None:
        """Set the graph's description."""
        self.document[METADATA_DESCRIPTION] = description

    @property
    def authors(self) -> Optional[str]:  # noqa: D401
        """The graph's authors.

        .. hint:: Can be set with the ``SET DOCUMENT Authors = "..."`` entry in the source BEL document.
        """
        return self.document.get(METADATA_AUTHORS)

    @authors.setter
    def authors(self, authors: str) -> None:
        """Set the graph's authors."""
        self.document[METADATA_AUTHORS] = authors

    @property
    def contact(self) -> Optional[str]:  # noqa: D401
        """The graph's contact information.

        .. hint:: Can be set with the ``SET DOCUMENT ContactInfo = "..."`` entry in the source BEL document.
        """
        return self.document.get(METADATA_CONTACT)

    @contact.setter
    def contact(self, contact: str) -> None:
        """Set the graph's contact."""
        self.document[METADATA_CONTACT] = contact

    @property
    def license(self) -> Optional[str]:  # noqa: D401
        """The graph's license.

        .. hint:: Can be set with the ``SET DOCUMENT Licenses = "..."`` entry in the source BEL document
        """
        return self.document.get(METADATA_LICENSES)

    @license.setter
    def license(self, license_str: str) -> None:
        """Set the graph's license."""
        self.document[METADATA_LICENSES] = license_str

    @property
    def copyright(self) -> Optional[str]:  # noqa: D401
        """The graph's copyright.

        .. hint:: Can be set with the ``SET DOCUMENT Copyright = "..."`` entry in the source BEL document
        """
        return self.document.get(METADATA_COPYRIGHT)

    @copyright.setter
    def copyright(self, copyright_str: str) -> None:
        """Set the graph's copyright."""
        self.document[METADATA_COPYRIGHT] = copyright_str

    @property
    def disclaimer(self) -> Optional[str]:  # noqa: D401
        """The graph's disclaimer.

        .. hint:: Can be set with the ``SET DOCUMENT Disclaimer = "..."`` entry in the source BEL document.
        """
        return self.document.get(METADATA_DISCLAIMER)

    @disclaimer.setter
    def disclaimer(self, disclaimer: str) -> None:
        """Set the graph's disclaimer."""
        self.document[METADATA_DISCLAIMER] = disclaimer

    @property
    def namespace_url(self) -> Dict[str, str]:  # noqa: D401
        """The mapping from the keywords used in this graph to their respective BEL namespace URLs.

        .. hint:: Can be appended with the ``DEFINE NAMESPACE [key] AS URL "[value]"`` entries in the definitions
                  section of the source BEL document.
        """
        return self.graph[GRAPH_NAMESPACE_URL]

    @property
    def defined_namespace_keywords(self) -> Set[str]:  # noqa: D401
        """The set of all keywords defined as namespaces in this graph."""
        return set(self.namespace_pattern) | set(self.namespace_url)

    @property
    def namespace_pattern(self) -> Dict[str, str]:  # noqa: D401
        """The mapping from the namespace keywords used to create this graph to their regex patterns.

        .. hint:: Can be appended with the ``DEFINE NAMESPACE [key] AS PATTERN "[value]"`` entries in the definitions
                  section of the source BEL document.
        """
        return self.graph[GRAPH_NAMESPACE_PATTERN]

    @property
    def annotation_url(self) -> Dict[str, str]:  # noqa: D401
        """The mapping from the annotation keywords used to create this graph to the URLs of the BELANNO files.

        .. hint:: Can be appended with the ``DEFINE ANNOTATION [key] AS URL "[value]"`` entries in the definitions
                  section of the source BEL document.
        """
        return self.graph[GRAPH_ANNOTATION_URL]

    @property
    def annotation_pattern(self) -> Dict[str, str]:  # noqa: D401
        """The mapping from the annotation keywords used to create this graph to their regex patterns as strings.

        .. hint:: Can be appended with the ``DEFINE ANNOTATION [key] AS PATTERN "[value]"`` entries in the definitions
                  section of the source BEL document.
        """
        return self.graph[GRAPH_ANNOTATION_PATTERN]

    @property
    def annotation_list(self) -> Dict[str, Set[str]]:  # noqa: D401
        """The mapping from the keywords of locally defined annotations to their respective sets of values.

        .. hint:: Can be appended with the ``DEFINE ANNOTATION [key] AS LIST {"[value]", ...}`` entries in the
                  definitions section of the source BEL document.
        """
        return self.graph[GRAPH_ANNOTATION_LIST]

    @property
    def defined_annotation_keywords(self) -> Set[str]:
        """Get the set of all keywords defined as annotations in this graph."""
        return (
            set(self.annotation_pattern)
            | set(self.annotation_url)
            | set(self.annotation_list)
        )

    @property
    def pybel_version(self) -> str:  # noqa: D401
        """The version of PyBEL with which this graph was produced as a string."""
        return self.graph[GRAPH_PYBEL_VERSION]

    @property
    def warnings(self) -> List[WarningTuple]:  # noqa: D401
        """A list of warnings associated with this graph."""
        return self._warnings

    def number_of_warnings(self) -> int:
        """Return the number of warnings."""
        return len(self.warnings)

    def number_of_citations(self) -> int:
        """Return the number of citations contained within the graph."""
        return len(set(self._iterate_citations()))

    def _iterate_citations(self) -> Iterable[Tuple[str, str]]:
        for _, _, data in self.edges(data=True):
            if CITATION in data:
                yield data[CITATION][CITATION_DB], data[CITATION][CITATION_IDENTIFIER]

    def number_of_authors(self) -> int:
        """Return the number of citations contained within the graph."""
        return len(set(self._iterate_authors()))

    def _iterate_authors(self) -> Iterable[str]:
        return chain.from_iterable(
            data[CITATION][CITATION_AUTHORS]
            for _, _, data in self.edges(data=True)
            if CITATION in data and CITATION_AUTHORS in data[CITATION]
        )

    def __str__(self):
        return '{} v{}'.format(self.name, self.version)

    def add_warning(
        self,
        exception: BELParserWarning,
        context: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """Add a warning to the internal warning log in the graph, with optional context information.

        :param exception: The exception that occurred
        :param context: The context from the parser when the exception occurred
        """
        self.warnings.append((
            self.path,
            exception,
            {} if context is None else context,
        ))

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

    def add_transcription(self, gene: Gene, rna: Union[Rna, MicroRna]) -> str:
        """Add a transcription relation from a gene to an RNA or miRNA node.

        :param gene: A gene node
        :param rna: An RNA or microRNA node
        """
        return self.add_unqualified_edge(gene, rna, TRANSCRIBED_TO)

    def add_translation(self, rna: Rna, protein: Protein) -> str:
        """Add a translation relation from a RNA to a protein.

        :param rna: An RNA node
        :param protein: A protein node
        """
        return self.add_unqualified_edge(rna, protein, TRANSLATED_TO)

    def _add_two_way_qualified_edge(self, u: BaseEntity, v: BaseEntity, *args, **kwargs) -> str:
        """Add an qualified edge both ways."""
        self.add_qualified_edge(u=v, v=u, *args, **kwargs)
        return self.add_qualified_edge(u=u, v=v, *args, **kwargs)

    def _add_two_way_unqualified_edge(self, u: BaseEntity, v: BaseEntity, *args, **kwargs) -> str:
        """Add an unqualified edge both ways."""
        self.add_unqualified_edge(v, u, *args, **kwargs)
        return self.add_unqualified_edge(u, v, *args, **kwargs)

    add_equivalence = partialmethod(_add_two_way_unqualified_edge, relation=EQUIVALENT_TO)
    """Add two equivalence relations for the nodes."""

    add_orthology = partialmethod(_add_two_way_unqualified_edge, relation=ORTHOLOGOUS)
    """Add two orthology relations for the nodes such that ``u orthologousTo v`` and ``v orthologousTo u``."""

    add_is_a = partialmethod(add_unqualified_edge, relation=IS_A)
    """Add an ``isA`` relationship such that ``u isA v``."""

    add_part_of = partialmethod(add_unqualified_edge, relation=PART_OF)
    """Add a ``partOf`` relationship such that ``u partOf v``."""

    add_has_variant = partialmethod(add_unqualified_edge, relation=HAS_VARIANT)
    """Add a ``hasVariant`` relationship such that ``u hasVariant v``."""

    add_has_reactant = partialmethod(add_unqualified_edge, relation=HAS_REACTANT)
    """Add a ``hasReactant`` relationship such that ``u hasReactant v``."""

    add_has_product = partialmethod(add_unqualified_edge, relation=HAS_PRODUCT)
    """Add a ``hasProduct`` relationship such that ``u hasProduct v``."""

    def add_qualified_edge(
        self,
        u,
        v,
        *,
        relation: str,
        evidence: str,
        citation: Union[str, Tuple[str, str], CitationDict],
        annotations: Optional[AnnotationsHint] = None,
        subject_modifier: Optional[Mapping] = None,
        object_modifier: Optional[Mapping] = None,
        **attr
    ) -> str:
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
        :param subject_modifier: The modifiers (like activity) on the subject node. See data model documentation.
        :param object_modifier: The modifiers (like activity) on the object node. See data model documentation.

        :return: The hash of the edge
        """
        attr = self._build_attr(
            relation=relation,
            evidence=evidence,
            citation=citation,
            annotations=annotations,
            subject_modifier=subject_modifier,
            object_modifier=object_modifier,
            **attr
        )
        return self._help_add_edge(u, v, attr)

    @staticmethod
    def _build_attr(
        relation: str,
        evidence: str,
        citation: Union[str, Tuple[str, str], CitationDict],
        annotations: Optional[AnnotationsHint] = None,
        subject_modifier: Optional[Mapping] = None,
        object_modifier: Optional[Mapping] = None,
        **attr
    ):
        attr.update({
            RELATION: relation,
            EVIDENCE: evidence,
            CITATION: _handle_citation(citation),
        })

        if annotations:  # clean up annotations
            attr[ANNOTATIONS] = _clean_annotations(annotations)

        if subject_modifier:
            attr[SUBJECT] = subject_modifier

        if object_modifier:
            attr[OBJECT] = object_modifier

        return attr

    def add_binds(
        self,
        u,
        v,
        *,
        evidence: str,
        citation: Union[str, Tuple[str, str], CitationDict],
        annotations: Optional[AnnotationsHint] = None,
        **attr
    ) -> str:
        """Add a "binding" relationship between the two entities such that ``u => complex(u, v)``."""
        complex_abundance = ComplexAbundance([u, v])
        return self.add_directly_increases(
            u,
            complex_abundance,
            citation=citation,
            evidence=evidence,
            annotations=annotations,
            **attr
        )

    add_increases = partialmethod(add_qualified_edge, relation=INCREASES)
    """Wrap :meth:`add_qualified_edge` for the :data:`pybel.constants.INCREASES` relation."""

    add_directly_increases = partialmethod(add_qualified_edge, relation=DIRECTLY_INCREASES)
    """Add a :data:`pybel.constants.DIRECTLY_INCREASES` with :meth:`add_qualified_edge`."""

    add_decreases = partialmethod(add_qualified_edge, relation=DECREASES)
    """Add a :data:`pybel.constants.DECREASES` relationship with :meth:`add_qualified_edge`."""

    add_directly_decreases = partialmethod(add_qualified_edge, relation=DIRECTLY_DECREASES)
    """Add a :data:`pybel.constants.DIRECTLY_DECREASES` relationship with :meth:`add_qualified_edge`."""

    add_association = partialmethod(_add_two_way_qualified_edge, relation=ASSOCIATION)
    """Add a :data:`pybel.constants.ASSOCIATION` relationship with :meth:`add_qualified_edge`."""

    add_regulates = partialmethod(add_qualified_edge, relation=REGULATES)
    """Add a :data:`pybel.constants.REGULATES` relationship with :meth:`add_qualified_edge`."""

    add_correlation = partialmethod(_add_two_way_qualified_edge, relation=CORRELATION)
    """Add a :data:`pybel.constants.CORRELATION` relationship with :meth:`add_qualified_edge`."""

    add_no_correlation = partialmethod(_add_two_way_qualified_edge, relation=NO_CORRELATION)
    """Add a :data:`pybel.constants.NO_CORRELATION` relationship with :meth:`add_qualified_edge`."""

    add_positive_correlation = partialmethod(_add_two_way_qualified_edge, relation=POSITIVE_CORRELATION)
    """Add a :data:`pybel.constants.POSITIVE_CORRELATION` relationship with :meth:`add_qualified_edge`."""

    add_negative_correlation = partialmethod(_add_two_way_qualified_edge, relation=NEGATIVE_CORRELATION)
    """Add a :data:`pybel.constants.NEGATIVE_CORRELATION` relationship with :meth:`add_qualified_edge`."""

    add_causes_no_change = partialmethod(add_qualified_edge, relation=CAUSES_NO_CHANGE)
    """Add a :data:`pybel.constants.CAUSES_NO_CHANGE` relationship with :meth:`add_qualified_edge`."""

    add_inhibits = partialmethod(add_decreases, object_modifier=activity())
    """Add an "inhibits" relationship.

    A more specific version of :meth:`add_decreases` that automatically populates the object modifier with an
    activity."""

    add_directly_inhibits = partialmethod(add_directly_decreases, object_modifier=activity())

    add_activates = partialmethod(add_increases, object_modifier=activity())
    """Add an "activates" relationship.

    A more specific version of :meth:`add_increases` that automatically populates the object modifier with an
    activity."""

    add_directly_activates = partialmethod(add_directly_increases, object_modifier=activity())

    def _modify(
        self,
        add_edge_fn: str,
        name: str,
        u,
        v,
        code: Optional[str] = None,
        position: Optional[int] = None,
        *,
        evidence: str,
        citation: Union[str, Mapping[str, str]],
        annotations: Optional[AnnotationsHint] = None,
        subject_modifier: Optional[Mapping] = None,
        object_modifier: Optional[Mapping] = None,
        **attr
    ):
        """Add a simple modification."""
        adder = getattr(self, add_edge_fn)
        return adder(
            u,
            v.with_variants(ProteinModification(
                name=name, code=code, position=position,
            )),
            evidence=evidence,
            citation=citation,
            annotations=annotations,
            subject_modifier=subject_modifier,
            object_modifier=object_modifier,
            **attr
        )

    add_phosphorylates = partialmethod(_modify, 'add_increases', 'Ph')
    """Add an increase of modified object with phosphorylation."""

    add_directly_phosphorylates = partialmethod(_modify, 'add_directly_increases', 'Ph')
    """Add a direct increase of modified object with phosphorylation."""

    add_dephosphorylates = partialmethod(_modify, 'add_decreases', 'Ph')
    """Add a decrease of modified object with phosphorylation."""

    add_directly_dephosphorylates = partialmethod(_modify, 'add_directly_decreases', 'Ph')
    """Add a direct decrease of modified object with phosphorylation."""

    def add_node_from_data(self, node: BaseEntity) -> None:
        """Add an entity to the graph."""
        assert isinstance(node, BaseEntity)

        if node in self:
            return

        self.add_node(node)

        if VARIANTS in node:
            self.add_has_variant(node.get_parent(), node)

        elif MEMBERS in node:
            for member in node[MEMBERS]:
                self.add_part_of(member, node)

        elif PRODUCTS in node and REACTANTS in node:
            for reactant_tokens in node[REACTANTS]:
                self.add_has_reactant(node, reactant_tokens)
            for product_tokens in node[PRODUCTS]:
                self.add_has_product(node, product_tokens)

    def add_reaction(
        self,
        reactants: Union[BaseAbundance, Iterable[BaseAbundance]],
        products: Union[BaseAbundance, Iterable[BaseAbundance]],
    ):
        """Add a reaction directly to the graph."""
        return self.add_node_from_data(Reaction(reactants=reactants, products=products))

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

    def __add__(self, other: 'BELGraph') -> 'BELGraph':
        """Copy this graph and join it with another graph with it using :func:`pybel.struct.left_full_join`.

        :param BELGraph other: Another BEL graph
        :rtype: BELGraph

        Example usage:

        >>> import pybel
        >>> g = pybel.from_bel_script('...')
        >>> h = pybel.from_bel_script('...')
        >>> k = g + h
        """
        if not isinstance(other, BELGraph):
            raise TypeError('{} is not a {}'.format(other, self.__class__.__name__))

        result = deepcopy(self)
        left_full_join(result, other)
        return result

    def __iadd__(self, other: 'BELGraph') -> 'BELGraph':
        """Join another graph into this one, in-place, using :func:`pybel.struct.left_full_join`.

        :param BELGraph other: Another BEL graph
        :rtype: BELGraph

        Example usage:

        >>> import pybel
        >>> g = pybel.from_bel_script('...')
        >>> h = pybel.from_bel_script('...')
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
        >>> g = pybel.from_bel_script('...')
        >>> h = pybel.from_bel_script('...')
        >>> k = g & h
        """
        if not isinstance(other, BELGraph):
            raise TypeError('{} is not a {}'.format(other, self.__class__.__name__))

        result = deepcopy(self)
        left_outer_join(result, other)
        return result

    def __iand__(self, other: 'BELGraph') -> 'BELGraph':
        """Join another graph into this one, in-place, using :func:`pybel.struct.left_outer_join`.

        :param BELGraph other: Another BEL graph
        :rtype: BELGraph

        Example usage:

        >>> import pybel
        >>> g = pybel.from_bel_script('...')
        >>> h = pybel.from_bel_script('...')
        >>> g &= h
        """
        if not isinstance(other, BELGraph):
            raise TypeError('{} is not a {}'.format(other, self.__class__.__name__))

        left_outer_join(self, other)
        return self

    def __xor__(self, other: 'BELGraph') -> 'BELGraph':
        """Join this graph with another using :func:`pybel.struct.left_node_intersection_join`.

        :param BELGraph other: Another BEL graph
        :rtype: BELGraph

        Example usage:

        >>> import pybel
        >>> g = pybel.from_bel_script('...')
        >>> h = pybel.from_bel_script('...')
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
    def edge_to_bel(
        u: BaseEntity,
        v: BaseEntity,
        edge_data: EdgeData,
        sep: Optional[str] = None,
        use_identifiers: bool = False,
    ) -> str:
        """Serialize a pair of nodes and related edge data as a BEL relation."""
        return edge_to_bel(u, v, data=edge_data, sep=sep, use_identifiers=use_identifiers)

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
        return CONCEPT in node and node[CONCEPT][NAMESPACE] == namespace

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
            ('Number of Citations', self.number_of_citations()),
            ('Number of Authors', self.number_of_authors()),
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


def _handle_citation(citation: Union[str, Tuple[str, str], CitationDict]) -> CitationDict:
    if isinstance(citation, str):
        return citation_dict(db=CITATION_TYPE_PUBMED, db_id=citation)
    elif isinstance(citation, tuple):
        return citation_dict(db=citation[0], db_id=citation[1])
    elif isinstance(citation, CitationDict):
        return citation
    elif isinstance(citation, dict):
        return CitationDict(**citation)
    elif citation is None:
        raise ValueError('citation was None')
    else:
        raise TypeError('citation is the wrong type: {}'.format(citation))
