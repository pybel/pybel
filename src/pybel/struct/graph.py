# -*- coding: utf-8 -*-

"""Contains the main data structure for PyBEL."""

import logging
import warnings
from collections import Counter, defaultdict
from copy import deepcopy
from functools import partialmethod
from itertools import chain
from typing import Any, Dict, Hashable, Iterable, List, Mapping, Optional, Set, TextIO, Tuple, Union

import networkx as nx
from tabulate import tabulate

from .operations import left_full_join, left_node_intersection_join, left_outer_join
from .utils import update_metadata
from ..canonicalize import edge_to_bel
from ..constants import (
    ACTIVITY, ANNOTATIONS, ASSOCIATION, CAUSES_NO_CHANGE, CITATION, CITATION_AUTHORS, CITATION_DB, CITATION_IDENTIFIER,
    CITATION_TYPE_PUBMED, CORRELATION, DECREASES, DEGRADATION, DIRECTLY_DECREASES, DIRECTLY_INCREASES, EFFECT,
    EQUIVALENT_TO, EVIDENCE, FROM_LOC, GRAPH_ANNOTATION_LIST, GRAPH_ANNOTATION_PATTERN, GRAPH_ANNOTATION_URL,
    GRAPH_METADATA, GRAPH_NAMESPACE_PATTERN, GRAPH_NAMESPACE_URL, GRAPH_PATH, GRAPH_PYBEL_VERSION, HAS_PRODUCT,
    HAS_REACTANT, HAS_VARIANT, INCREASES, IS_A, LOCATION, METADATA_AUTHORS, METADATA_CONTACT, METADATA_COPYRIGHT,
    METADATA_DESCRIPTION, METADATA_DISCLAIMER, METADATA_LICENSES, METADATA_NAME, METADATA_VERSION, MODIFIER,
    NEGATIVE_CORRELATION, NO_CORRELATION, OBJECT, ORTHOLOGOUS, PART_OF, POSITIVE_CORRELATION, REGULATES, RELATION,
    SUBJECT, TO_LOC, TRANSCRIBED_TO, TRANSLATED_TO, TRANSLOCATION,
)
from ..dsl import (
    BaseAbundance, BaseConcept, BaseEntity, CentralDogma, ComplexAbundance, Gene, ListAbundance, MicroRna, Protein,
    ProteinModification, Reaction, Rna, activity,
)
from ..language import Entity
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

        #: A refernce to the parent graph
        self.parent = None
        self._count = CountDispatch(self)
        self._expand = ExpandDispatch(self)
        self._induce = InduceDispatch(self)
        self._plot = PlotDispatch(self)
        self._summary = SummaryDispatch(self)

    def child(self) -> 'BELGraph':
        """Create an empty graph with a "parent" reference back to this one."""
        rv = BELGraph()
        rv.parent = self
        update_metadata(source=self, target=rv)
        return rv

    @property
    def count(self) -> 'CountDispatch':  # noqa: D401
        """A dispatch to count functions.

        Can be used like this:

        >>> from pybel.examples import sialic_acid_graph
        >>> sialic_acid_graph.count.functions()
        Counter({'Protein': 7, 'Complex': 1, 'Abundance': 1})
        """
        return self._count

    @property
    def summary(self) -> 'SummaryDispatch':  # noqa: D401
        """A dispatch to summarize the graph."""
        return self._summary

    @property
    def expand(self) -> 'ExpandDispatch':  # noqa: D401
        """A dispatch to expand the graph w.r.t. its parent."""
        return self._expand

    @property
    def induce(self) -> 'InduceDispatch':  # noqa: D401
        """A dispatch to mutate the graph."""
        return self._induce

    @property
    def plot(self) -> 'PlotDispatch':  # noqa: D401
        """A dispatch to plot the graph using :mod:`matplotlib` and :mod:`seaborn`."""
        return self._plot

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
        return self.count.citations()

    def number_of_authors(self) -> int:
        """Return the number of authors contained within the graph."""
        return len(self.get_authors())

    def get_authors(self) -> Set[str]:
        """Get the authors for the citations in the graph."""
        return set(self.count.authors())

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

    def _help_add_edge_helper(self, u: BaseEntity, v: BaseEntity, attr: Mapping[str, Any]) -> str:
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
        subject_modifier: Optional[Mapping[str, Any]] = None,
        object_modifier: Optional[Mapping[str, Any]] = None,
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
        subject_modifier: Optional[Mapping[str, Any]] = None,
        object_modifier: Optional[Mapping[str, Any]] = None,
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
            attr[SUBJECT] = _handle_modifier(subject_modifier)

        if object_modifier:
            attr[OBJECT] = _handle_modifier(object_modifier)

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

        if isinstance(node, CentralDogma) and node.variants:
            self.add_has_variant(node.get_parent(), node)

        elif isinstance(node, ListAbundance):
            for member in node.members:
                self.add_part_of(member, node)

        elif isinstance(node, Reaction):
            for reactant in node.reactants:
                self.add_has_reactant(node, reactant)
            for product in node.products:
                self.add_has_product(node, product)

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

        :param other: Another BEL graph

        Example usage:

        >>> from pybel.examples import ras_tloc_graph, braf_graph
        >>> k = ras_tloc_graph + braf_graph
        """
        if not isinstance(other, BELGraph):
            raise TypeError('{} is not a {}'.format(other, self.__class__.__name__))

        result = deepcopy(self)
        left_full_join(result, other)
        return result

    def __iadd__(self, other: 'BELGraph') -> 'BELGraph':
        """Join another graph into this one, in-place, using :func:`pybel.struct.left_full_join`.

        :param other: Another BEL graph

        Example usage:

        >>> from pybel.examples import ras_tloc_graph, braf_graph
        >>> ras_tloc_graph += braf_graph
        """
        if not isinstance(other, BELGraph):
            raise TypeError('{} is not a {}'.format(other, self.__class__.__name__))

        left_full_join(self, other)
        return self

    def __and__(self, other: 'BELGraph') -> 'BELGraph':
        """Create a deep copy of this graph and left outer joins another graph.

        Uses :func:`pybel.struct.left_outer_join`.

        :param other: Another BEL graph

        Example usage:

        >>> from pybel.examples import ras_tloc_graph, braf_graph
        >>> k = ras_tloc_graph & braf_graph
        """
        if not isinstance(other, BELGraph):
            raise TypeError('{} is not a {}'.format(other, self.__class__.__name__))

        result = deepcopy(self)
        left_outer_join(result, other)
        return result

    def __iand__(self, other: 'BELGraph') -> 'BELGraph':
        """Join another graph into this one, in-place, using :func:`pybel.struct.left_outer_join`.

        :param other: Another BEL graph

        Example usage:

        >>> from pybel.examples import ras_tloc_graph, braf_graph
        >>> ras_tloc_graph &= braf_graph
        """
        if not isinstance(other, BELGraph):
            raise TypeError('{} is not a {}'.format(other, self.__class__.__name__))

        left_outer_join(self, other)
        return self

    def __xor__(self, other: 'BELGraph') -> 'BELGraph':
        """Join this graph with another using :func:`pybel.struct.left_node_intersection_join`.

        :param other: Another BEL graph

        Example usage:

        >>> from pybel.examples import ras_tloc_graph, braf_graph
        >>> k = ras_tloc_graph ^ braf_graph
        """
        if not isinstance(other, BELGraph):
            raise TypeError('{} is not a {}'.format(other, self.__class__.__name__))

        return left_node_intersection_join(self, other)

    @staticmethod
    def node_to_bel(n: BaseEntity) -> str:
        """Serialize a node as BEL."""
        warnings.warn('use node.as_bel()', DeprecationWarning)
        return n.as_bel()

    @staticmethod
    def edge_to_bel(
        u: BaseEntity,
        v: BaseEntity,
        edge_data: EdgeData,
        sep: Optional[str] = None,
        use_identifiers: bool = True,
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
        return isinstance(node, BaseConcept) and node.namespace.lower() == namespace.lower()

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
        warnings.warn('use graph.summary.list()', DeprecationWarning)
        return self.summary.list()

    def summary_dict(self) -> Mapping[str, float]:
        """Return a dictionary that summarizes the graph."""
        warnings.warn('use graph.summary.dict()', DeprecationWarning)
        return self.summary.dict()

    def summary_str(self) -> str:
        """Return a string that summarizes the graph."""
        warnings.warn('use graph.summary.str()', DeprecationWarning)
        return self.summary.str()

    def summarize(self, file: Optional[TextIO] = None) -> None:
        """Print a summary of the graph."""
        warnings.warn('use graph.summary()', DeprecationWarning)
        self.summary(file=file)

    def ground(self, **kwargs) -> 'BELGraph':
        """Ground this graph."""
        from ..grounding import ground
        return ground(self, **kwargs)


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


def _handle_modifier(side_data: Dict[str, Any]) -> Mapping[str, Any]:
    modifier = side_data.get(MODIFIER)
    effect = side_data.get(EFFECT)

    if modifier == ACTIVITY:
        if effect is not None:
            side_data[EFFECT] = Entity(**effect)
    elif modifier == TRANSLOCATION:
        if effect is not None:
            effect[FROM_LOC] = Entity(**effect[FROM_LOC])
            effect[TO_LOC] = Entity(**effect[TO_LOC])
    elif modifier == DEGRADATION or modifier is None:
        pass
    else:
        raise ValueError('invalid modifier: {}'.format(modifier))

    if LOCATION in side_data:
        side_data[LOCATION] = Entity(**side_data[LOCATION])
    return side_data


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


class Dispatch:
    def __init__(self, graph: BELGraph):
        self.graph = graph


class CountDispatch(Dispatch):
    """A dispatch for count functions that can be found at :data:`pybel.BELGraph.count`."""

    def functions(self) -> Counter:
        """Count the functions in a graph.

        >>> from pybel.examples import sialic_acid_graph
        >>> sialic_acid_graph.count.functions()
        Counter({'Protein': 7, 'Complex': 1, 'Abundance': 1})
        """
        from .summary import count_functions
        return count_functions(self.graph)

    def namespaces(self) -> Counter:
        """Return a counter of namespaces' occurrences in nodes in the graph."""
        from .summary import count_namespaces
        return count_namespaces(self.graph)

    def pathologies(self) -> Counter:
        """Return a counter of pathologies' occurrences in edges in the graph."""
        from .summary import count_pathologies
        return count_pathologies(self.graph)

    def annotations(self) -> Counter:
        """Return a counter of annotations' occurrences in edges in the graph."""
        from .summary import count_annotations
        return count_annotations(self.graph)

    def variants(self) -> Counter:
        """Return a counter of variants' occurrences in nodes in the graph."""
        from .summary import count_variants
        return count_variants(self.graph)

    def relations(self) -> Counter:
        """Return a counter of relations' occurrences in edges in the graph."""
        from .summary import count_relations
        return count_relations(self.graph)

    def error_types(self) -> Counter:
        """Return a counter of error types' occurrences in BEL script underlying the graph."""
        from .summary import count_error_types
        return count_error_types(self.graph)

    def names_by_namespace(self, namespace: str) -> Counter:
        from .summary import count_names_by_namespace
        return count_names_by_namespace(self.graph, namespace=namespace)

    def modifications(self) -> Counter:
        """Return a counter of relation modifications' occurrences (activity, translocation, etc.) in the graph."""
        from .summary.node_summary import count_modifications
        return count_modifications(self.graph)

    def authors(self) -> Counter:
        """Return a counter of the number of edges to which each author contributed in the graph."""
        return Counter(_iterate_authors(self.graph))

    def citations(self) -> int:
        """Return the number of citations."""
        return len(set(_iterate_citations(self.graph)))


def _iterate_citations(graph: BELGraph) -> Iterable[Tuple[str, str]]:
    for _, _, data in graph.edges(data=True):
        if CITATION in data:
            yield data[CITATION][CITATION_DB], data[CITATION][CITATION_IDENTIFIER]


def _iterate_authors(graph: BELGraph) -> Iterable[str]:
    return chain.from_iterable(
        data[CITATION][CITATION_AUTHORS]
        for _, _, data in graph.edges(data=True)
        if CITATION in data and CITATION_AUTHORS in data[CITATION]
    )


class SummaryDispatch(Dispatch):
    """A dispatch for summary printing functions that can be found at :data:`pybel.BELGraph.summary`."""

    def __call__(self, file: Optional[TextIO] = None, examples: bool = True) -> None:
        self.statistics(file=file)
        print('', file=file)
        self.nodes(file=file, examples=examples)
        print('', file=file)
        self.namespaces(file=file, examples=examples)
        print('', file=file)
        self.edges(file=file, examples=examples)
        print('', file=file)

    def statistics(self, file: Optional[TextIO] = None):
        """Print summary statistics on the graph."""
        print(self.str(), file=file)

    def nodes(self, file: Optional[TextIO] = None, examples: bool = True):
        """Print a summary of the nodes' functions in the graph."""
        from .summary.supersummary import functions
        functions(self.graph, file=file, examples=examples)

    def namespaces(self, file: Optional[TextIO] = None, examples: bool = True):
        """Print a summary of the nodes' namespaces in the graph."""
        from .summary.supersummary import namespaces
        namespaces(self.graph, file=file, examples=examples)

    def edges(self, file: Optional[TextIO] = None, examples: bool = True):
        """Print a summary of the edges' types in the graph."""
        from .summary.supersummary import edges
        edges(self.graph, file=file, examples=examples)

    def citations(self, n: Optional[int] = 15, file: Optional[TextIO] = None):
        """Print a summary of the top citations' frequencies in the graph."""
        from .summary.supersummary import citations
        citations(self.graph, n=n, file=file)

    def dict(self) -> Mapping[str, float]:
        """Return a dictionary that summarizes the graph."""
        return dict(self.list())

    def str(self) -> str:
        """Return a string that summarizes the graph."""
        return tabulate(self.list())

    def list(self) -> List[Tuple[str, float]]:
        """Return a list of tuples that summarize the graph."""
        number_nodes = self.graph.number_of_nodes()
        return [
            ('Name', self.graph.name),
            ('Version', self.graph.version),
            ('Number of Nodes', number_nodes),
            ('Number of Namespaces', len(self.graph.count.namespaces())),
            ('Number of Edges', self.graph.number_of_edges()),
            ('Number of Annotations', len(self.graph.count.annotations())),
            ('Number of Citations', self.graph.number_of_citations()),
            ('Number of Authors', self.graph.number_of_authors()),
            ('Network Density', '{:.2E}'.format(nx.density(self.graph))),
            ('Number of Components', nx.number_weakly_connected_components(self.graph)),
            ('Number of Warnings', self.graph.number_of_warnings()),
        ]


class PlotDispatch(Dispatch):
    """A dispatch for count functions that can be found at :data:`pybel.BELGraph.plot`."""

    def summary(self, save: Optional[str] = None, **kwargs):
        """Plot a summary of the graph's nodes and edges using :mod:`matplotlib`."""
        from pybel_tools.summary.visualization import plot_summary
        fig, axes = plot_summary(self.graph, **kwargs)
        if save:
            fig.save(save)


class ExpandDispatch(Dispatch):
    """A dispatch for count functions that can be found at :data:`pybel.BELGraph.expand`."""

    @property
    def parent(self) -> BELGraph:
        """Get the parent BEL graph."""
        if not self.graph.parent:
            raise RuntimeError('Can not use expand dispatch on graph without a parent')
        return self.graph.parent

    def neighborhood(self, node: BaseEntity) -> BELGraph:
        """Expand around the neighborhood of a given node.

        >>> from pybel.examples import braf_graph
        >>> from pybel.dsl import Protein
        >>> thpo = Protein(namespace='HGNC', name='THPO', identifier='11795')
        >>> braf = Protein(namespace='HGNC', name='BRAF', identifier='1097')
        >>> raf1 = Protein(namespace='HGNC', name='RAF1', identifier='9829')
        >>> elk1 = Protein(namespace='HGNC', name='ELK1', identifier='3321')
        >>> subgraph_1 = braf_graph.induce.paths([braf, elk1])
        >>> assert thpo not in subgraph_1 and raf1 not in subgraph_1
        >>> subgraph_2 = subgraph_1.expand.neighborhood(braf)
        >>> assert thpo in subgraph_2 and raf1 not in subgraph_2
        """
        from .mutation import expand_node_neighborhood
        cp = self.graph.copy()
        expand_node_neighborhood(universe=self.parent, graph=cp, node=node)
        return cp

    def periphery(self, **kwargs):
        """Expand around the periphery of the graph w.r.t. its parent graph."""
        from pybel_tools.mutation.expansion import expand_periphery
        cp = self.graph.copy()
        expand_periphery(universe=self.parent, graph=cp, **kwargs)
        return cp

    def internal(self, **kwargs):
        """Expand missing edges between nodes in the graph w.r.t. its parent graph."""
        from pybel_tools.mutation.expansion import expand_internal
        cp = self.graph.copy()
        expand_internal(universe=self.parent, graph=cp, **kwargs)
        return cp


class InduceDispatch(Dispatch):
    """A dispatch for induction functions that can be found at :data:`pybel.BELGraph.induce`."""

    def paths(self, nodes: Iterable[BaseEntity]) -> Optional[BELGraph]:
        """Induce a subgraph on shortest paths between the nodes."""
        from .mutation import get_subgraph_by_all_shortest_paths
        return get_subgraph_by_all_shortest_paths(self.graph, nodes)

    def neighborhood(self, nodes: Iterable[BaseEntity]) -> Optional[BELGraph]:
        """Induce a subgraph around the neighborhood."""
        from .mutation import get_subgraph_by_neighborhood
        return get_subgraph_by_neighborhood(self.graph, nodes)

    def random(self, **kwargs) -> Optional[BELGraph]:
        """Induce a random subgraph."""
        from .mutation import get_random_subgraph
        return get_random_subgraph(self.graph, **kwargs)

    def annotation(self, prefix: str, identifier: str) -> Optional[BELGraph]:
        """Induce a subgraph on edges with the given annotation."""
        from .mutation import get_subgraph_by_annotation_value
        return get_subgraph_by_annotation_value(self.graph, prefix, identifier)
