# -*- coding: utf-8 -*-

"""A parser for BEL.

This module handles parsing BEL relations and validation of semantics.
"""

import itertools as itt
import logging
from functools import lru_cache
from typing import Any, Dict, List, Mapping, Optional, Pattern, Set, Union

import pyparsing
from pyparsing import Group, Keyword, MatchFirst, ParseResults, StringEnd, Suppress, delimitedList, oneOf, replaceWith

from .baseparser import BaseParser
from .constants import NamespaceTermEncodingMapping
from .modifiers import (
    get_fragment_language, get_fusion_language, get_gene_modification_language, get_gene_substitution_language,
    get_hgvs_language, get_legacy_fusion_langauge, get_location_language, get_protein_modification_language,
    get_protein_substitution_language, get_truncation_language,
)
from .parse_concept import ConceptParser
from .parse_control import ControlParser
from .utils import WCW, nest, one_of_tags, triple
from .. import language
from ..constants import (
    ABUNDANCE, ACTIVITY, ASSOCIATION, BINDS, BIOPROCESS, CAUSES_NO_CHANGE, CELL_SECRETION, CELL_SURFACE_EXPRESSION,
    COMPLEX, COMPOSITE, CONCEPT, CORRELATION, DECREASES, DEGRADATION, DIRECTLY_DECREASES, DIRECTLY_INCREASES, DIRTY,
    EFFECT, EQUIVALENT_TO, FROM_LOC, FUNCTION, FUSION, GENE, IDENTIFIER, INCREASES, IS_A, LINE, LOCATION, MEMBERS,
    MIRNA, MODIFIER, NAME, NAMESPACE, NEGATIVE_CORRELATION, NO_CORRELATION, PART_OF, PATHOLOGY, POPULATION,
    POSITIVE_CORRELATION, PRODUCTS, PROTEIN, REACTANTS, REACTION, REGULATES, RELATION, RNA, SOURCE, TARGET, TO_LOC,
    TRANSCRIBED_TO, TRANSLATED_TO, TRANSLOCATION, TWO_WAY_RELATIONS, VARIANTS, belns_encodings,
)
from ..dsl import BaseEntity
from ..exceptions import (
    InvalidEntity, InvalidFunctionSemantic, MalformedTranslocationWarning, MissingAnnotationWarning,
    MissingCitationException, MissingSupportWarning, NestedRelationWarning,
)
from ..struct.graph import BELGraph
from ..tokens import parse_result_to_dsl

__all__ = [
    'BELParser',
    'modifier_po_to_dict',
    'parse',
]

logger = logging.getLogger('pybel.parser')

###########################
# 2.1 Abundance Functions #
###########################

#: 2.1.1 http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#Xabundancea>
general_abundance_tags = one_of_tags(['a', 'abundance'], ABUNDANCE, FUNCTION)

#: 2.1.2 http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XcomplexA
complex_tag = one_of_tags(['complex', 'complexAbundance'], COMPLEX, FUNCTION)

#: 2.1.3 http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XcompositeA
composite_abundance_tag = one_of_tags(['composite', 'compositeAbundance'], COMPOSITE, FUNCTION)

#: 2.1.4 http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XgeneA
gene_tag = one_of_tags(['g', 'geneAbundance'], GENE, FUNCTION)

#: 2.1.5 http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XmicroRNAA
mirna_tag = one_of_tags(['m', 'microRNAAbundance'], MIRNA, FUNCTION)

#: 2.1.6 http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XproteinA
protein_tag = one_of_tags(['p', 'proteinAbundance'], PROTEIN, FUNCTION)

#: 2.1.7 http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XrnaA
rna_tag = one_of_tags(['r', 'rnaAbundance'], RNA, FUNCTION)

######################
# Modifier Functions #
######################

# `2.2.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_protein_modifications>`_
# See below (needs identifier)

#: `2.2.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_variant_var>`_
variant = get_hgvs_language()

#: `2.2.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_proteolytic_fragments>`_
fragment = get_fragment_language()

# `2.2.4 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_cellular_location>`_
# See below (needs identifier)

#: DEPRECATED
#: <http://openbel.org/language/version_1.0/bel_specification_version_1.0.html#_amino_acid_substitutions>
psub = get_protein_substitution_language()

#: DEPRECATED
#: http://openbel.org/language/version_1.0/bel_specification_version_1.0.html#_sequence_variations>
gsub = get_gene_substitution_language()

#: DEPRECATED
#: http://openbel.org/language/version_1.0/bel_specification_version_1.0.html#_truncated_proteins>
trunc = get_truncation_language()

###############################
# 2.3 & 2.4 Process Functions #
###############################

#: 2.3.1 http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_biologicalprocess_bp
biological_process_tag = one_of_tags(['bp', 'biologicalProcess'], BIOPROCESS, FUNCTION)

#: 2.3.2 http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_pathology_path
pathology_tag = one_of_tags(['o', 'path', 'pathology'], PATHOLOGY, FUNCTION)

population_tag = one_of_tags(['pop', 'populationAbundance'], POPULATION, FUNCTION)

#: 2.3.3 http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#Xactivity
activity_tag = one_of_tags(['act', 'activity'], ACTIVITY, MODIFIER)

#: 2.4.1 http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XmolecularA
molecular_activity_tags = Suppress(oneOf(['ma', 'molecularActivity']))

################################
# 2.5 Transformation Functions #
################################

#: 2.5.1a http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_translocation_tloc
translocation_tag = one_of_tags(['translocation', 'tloc'], TRANSLOCATION, MODIFIER)

#: 2.5.1b http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_cellsecretion_sec
cell_secretion_tag = one_of_tags(['sec', 'cellSecretion'], CELL_SECRETION, MODIFIER)

#: 2.5.1c http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_cellsurfaceexpression_surf
cell_surface_expression_tag = one_of_tags(['surf', 'cellSurfaceExpression'], CELL_SURFACE_EXPRESSION, MODIFIER)

#: 2.5.2 http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_degradation_deg
degradation_tags = one_of_tags(['deg', 'degradation'], DEGRADATION, MODIFIER)

#: 2.5.3 http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_reaction_rxn
reaction_tags = one_of_tags(['reaction', 'rxn'], REACTION, FUNCTION)

#####################
# BEL Relationships #
#####################

#: `3.1.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#Xincreases>`_
increases_tag = oneOf(['->', '→', 'increases']).setParseAction(replaceWith(INCREASES))

#: `3.1.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XdIncreases>`_
directly_increases_tag = one_of_tags(['=>', '⇒', 'directlyIncreases'], DIRECTLY_INCREASES)

#: `3.1.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#Xdecreases>`_
decreases_tag = one_of_tags(['-|', 'decreases'], DECREASES)

#: `3.1.4 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XdDecreases>`_
directly_decreases_tag = one_of_tags(['=|', 'directlyDecreases'], DIRECTLY_DECREASES)

#: `3.1.5 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_ratelimitingstepof>`_
rate_limit_tag = Keyword('rateLimitingStepOf')

#: `3.1.6 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#Xcnc>`_
causes_no_change_tag = one_of_tags(['cnc', 'causesNoChange'], CAUSES_NO_CHANGE)

#: `3.1.7 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_regulates_reg>`_
regulates_tag = one_of_tags(['reg', 'regulates'], REGULATES)

#: Binds relation
binds_tag = Keyword(BINDS)

#: Correlation relation
correlation_tag = one_of_tags(['cor', 'correlation'], CORRELATION)

#: No Correlation relation
no_correlation_tag = one_of_tags(['noCor', 'noCorrelation'], NO_CORRELATION)

#: `3.2.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XnegCor>`_
negative_correlation_tag = one_of_tags(['neg', 'negativeCorrelation'], NEGATIVE_CORRELATION)

#: `3.2.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XposCor>`_
positive_correlation_tag = one_of_tags(['pos', 'positiveCorrelation'], POSITIVE_CORRELATION)

#: `3.2.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#Xassociation>`_
association_tag = one_of_tags(['--', 'association'], ASSOCIATION)

#: `3.3.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_orthologous>`_
orthologous_tag = Keyword('orthologous')

#: `3.3.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_transcribedto>`_
transcribed_tag = oneOf([':>', 'transcribedTo']).setParseAction(replaceWith(TRANSCRIBED_TO))

#: `3.3.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_translatedto>`_
translated_tag = oneOf(['>>', 'translatedTo']).setParseAction(replaceWith(TRANSLATED_TO))

#: `3.4.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_hasmember>`_
has_member_tag = Keyword('hasMember')

#: `3.4.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_hasmembers>`_
has_members_tag = Keyword('hasMembers')

#: `3.4.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_hascomponent>`_
has_component_tag = Keyword('hasComponent')

#: `3.4.4 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_hascomponents>`_
has_components_tag = Keyword('hasComponents')

#: `3.4.5 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_isa>`_
is_a_tag = Keyword(IS_A)

#: `3.4.6 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_subprocessof>`_
subprocess_of_tag = Keyword('subProcessOf')

#: `3.5.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_analogous>`_
analogous_tag = Keyword('analogousTo')

#: `3.5.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_biomarkerfor>`_
biomarker_tag = Keyword('biomarkerFor')

#: `3.5.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_prognosticbiomarkerfor>`_
prognostic_biomarker_tag = Keyword('prognosticBiomarkerFor')

biomarker_tags = biomarker_tag | prognostic_biomarker_tag

# Computed edges
has_variant_tags = Keyword('hasVariant')
has_reactant_tags = Keyword('hasReactant')
has_product_tags = Keyword('hasProduct')
part_of_reaction_tags = has_reactant_tags | has_product_tags

#: The ``equivalentTp`` relationship has been proposed for BEL 2.0.0+
equivalent_tag = one_of_tags(['eq', EQUIVALENT_TO], EQUIVALENT_TO)

#: The ``partOf`` relationship has been proposed for BEL 2.0.0+
partof_tag = Keyword(PART_OF)


class BELParser(BaseParser):
    """Build a parser backed by a given dictionary of namespaces."""

    def __init__(
        self,
        graph: Optional[BELGraph] = None,
        namespace_to_term_to_encoding: Optional[NamespaceTermEncodingMapping] = None,
        namespace_to_pattern: Optional[Mapping[str, Pattern]] = None,
        annotation_to_term: Optional[Mapping[str, Set[str]]] = None,
        annotation_to_pattern: Optional[Mapping[str, Pattern]] = None,
        annotation_to_local: Optional[Mapping[str, Set[str]]] = None,
        allow_naked_names: bool = False,
        disallow_nested: bool = False,
        disallow_unqualified_translocations: bool = False,
        citation_clearing: bool = True,
        skip_validation: bool = False,
        autostreamline: bool = True,
        required_annotations: Optional[List[str]] = None,
    ) -> None:
        """Build a BEL parser.

        :param graph: The BEL graph to use to store the network
        :param namespace_to_term_to_encoding: A dictionary of {namespace: {name: encoding}}. Delegated to
         :class:`pybel.parser.parse_identifier.IdentifierParser`
        :param namespace_to_pattern: A dictionary of {namespace: compiled regular expression}. Delegated to
         :class:`pybel.parser.parse_identifier.IdentifierParser`
        :param annotation_to_term: A dictionary of {annotation: set of values}. Delegated to
         :class:`pybel.parser.ControlParser`
        :param annotation_to_pattern: A dictionary of {annotation: regular expression strings}. Delegated to
         :class:`pybel.parser.ControlParser`
        :param annotation_to_local: A dictionary of {annotation: set of values}. Delegated to
         :class:`pybel.parser.ControlParser`
        :param allow_naked_names: If true, turn off naked namespace failures. Delegated to
         :class:`pybel.parser.parse_identifier.IdentifierParser`
        :param disallow_nested: If true, turn on nested statement failures. Delegated to
         :class:`pybel.parser.parse_identifier.IdentifierParser`
        :param disallow_unqualified_translocations: If true, allow translocations without TO and FROM clauses.
        :param citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
         Delegated to :class:`pybel.parser.ControlParser`
        :param autostreamline: Should the parser be streamlined on instantiation?
        :param required_annotations: Optional list of required annotations
        """
        self.graph = graph

        self.disallow_nested = disallow_nested
        self.disallow_unqualified_translocations = disallow_unqualified_translocations

        if skip_validation:
            self.control_parser = ControlParser(
                citation_clearing=citation_clearing,
                required_annotations=required_annotations,
            )

            self.concept_parser = ConceptParser(
                allow_naked_names=allow_naked_names,
                skip_validation=skip_validation,
            )
        else:
            self.control_parser = ControlParser(
                annotation_to_term=annotation_to_term,
                annotation_to_pattern=annotation_to_pattern,
                annotation_to_local=annotation_to_local,
                #
                citation_clearing=citation_clearing,
                required_annotations=required_annotations,
            )

            self.concept_parser = ConceptParser(
                namespace_to_term_to_encoding=namespace_to_term_to_encoding,
                namespace_to_pattern=namespace_to_pattern,
                #
                allow_naked_names=allow_naked_names,
                skip_validation=skip_validation,
            )

        self.control_parser.get_line_number = self.get_line_number
        self.concept_parser.get_line_number = self.get_line_number

        concept = Group(self.concept_parser.language)(CONCEPT)

        # 2.2 Abundance Modifier Functions

        #: `2.2.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_protein_modifications>`_
        self.pmod = get_protein_modification_language(
            concept_fqualified=self.concept_parser.identifier_fqualified,
            concept_qualified=self.concept_parser.identifier_qualified,
        )

        #: `2.2.4 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_cellular_location>`_
        self.location = get_location_language(self.concept_parser.language)
        opt_location = pyparsing.Optional(WCW + self.location)

        #: PyBEL BEL Specification variant
        self.gmod = get_gene_modification_language(
            concept_fqualified=self.concept_parser.identifier_fqualified,
            concept_qualified=self.concept_parser.identifier_qualified,
        )

        # 2.6 Other Functions

        #: `2.6.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_fusion_fus>`_
        self.fusion = get_fusion_language(self.concept_parser.language)

        # 2.1 Abundance Functions

        #: `2.1.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XcomplexA>`_
        self.general_abundance = general_abundance_tags + nest(concept + opt_location)

        self.gene_modified = concept + pyparsing.Optional(
            WCW + delimitedList(Group(variant | gsub | self.gmod))(VARIANTS),
        )

        self.gene_fusion = Group(self.fusion)(FUSION)
        self.gene_fusion_legacy = Group(get_legacy_fusion_langauge(concept, 'c'))(FUSION)

        #: `2.1.4 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XgeneA>`_
        self.gene = gene_tag + nest(
            MatchFirst([
                self.gene_fusion,
                self.gene_fusion_legacy,
                self.gene_modified,
            ]) + opt_location,
        )

        self.mirna_modified = concept + pyparsing.Optional(
            WCW + delimitedList(Group(variant))(VARIANTS),
        ) + opt_location

        #: `2.1.5 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XmicroRNAA>`_
        self.mirna = mirna_tag + nest(self.mirna_modified)

        self.protein_modified = concept + pyparsing.Optional(
            WCW + delimitedList(Group(MatchFirst([self.pmod, variant, fragment, psub, trunc])))(
                VARIANTS,
            ),
        )

        self.protein_fusion = Group(self.fusion)(FUSION)
        self.protein_fusion_legacy = Group(get_legacy_fusion_langauge(concept, 'p'))(FUSION)

        #: `2.1.6 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XproteinA>`_
        self.protein = protein_tag + nest(
            MatchFirst([
                self.protein_fusion,
                self.protein_fusion_legacy,
                self.protein_modified,
            ]) + opt_location,
        )

        self.rna_modified = concept + pyparsing.Optional(WCW + delimitedList(Group(variant))(VARIANTS))

        self.rna_fusion = Group(self.fusion)(FUSION)
        self.rna_fusion_legacy = Group(get_legacy_fusion_langauge(concept, 'r'))(FUSION)

        #: `2.1.7 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XrnaA>`_
        self.rna = rna_tag + nest(
            MatchFirst([
                self.rna_fusion,
                self.rna_fusion_legacy,
                self.rna_modified,
            ]) + opt_location,
        )

        self.population = population_tag + nest(concept)

        self.single_abundance = MatchFirst([
            self.general_abundance,
            self.gene,
            self.mirna,
            self.protein,
            self.rna,
            self.population,
        ])

        #: `2.1.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XcomplexA>`_
        self.complex_singleton = complex_tag + nest(concept + opt_location)

        self.complex_list = complex_tag + nest(
            delimitedList(Group(self.single_abundance | self.complex_singleton))(MEMBERS) + opt_location,
        )

        self.complex_abundances = self.complex_list | self.complex_singleton

        # Definition of all simple abundances that can be used in a composite abundance
        self.simple_abundance = self.complex_abundances | self.single_abundance
        self.simple_abundance.setParseAction(self.check_function_semantics)

        #: `2.1.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XcompositeA>`_
        self.composite_abundance = composite_abundance_tag + nest(
            delimitedList(Group(self.simple_abundance))(MEMBERS) + opt_location,
        )

        self.abundance = self.simple_abundance | self.composite_abundance

        # 2.4 Process Modifier Function
        # backwards compatibility with BEL v1.0

        molecular_activity_default = oneOf(list(language.activity_labels)).setParseAction(
            handle_molecular_activity_default,
        )

        #: `2.4.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XmolecularA>`_
        self.molecular_activity = molecular_activity_tags + nest(
            molecular_activity_default | self.concept_parser.language,
        )

        # 2.3 Process Functions

        #: `2.3.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_biologicalprocess_bp>`_
        self.biological_process = biological_process_tag + nest(concept)

        #: `2.3.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_pathology_path>`_
        self.pathology = pathology_tag + nest(concept)

        self.bp_path = self.biological_process | self.pathology
        self.bp_path.setParseAction(self.check_function_semantics)

        self.activity_standard = activity_tag + nest(
            self.simple_abundance + pyparsing.Optional(WCW + Group(self.molecular_activity)(EFFECT)),
        )

        activity_legacy_tags = oneOf(language.activities)(MODIFIER)
        self.activity_legacy = activity_legacy_tags + nest(self.simple_abundance)
        self.activity_legacy.setParseAction(handle_activity_legacy)

        #: `2.3.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#Xactivity>`_
        self.activity = self.activity_standard | self.activity_legacy

        self.process = self.bp_path | self.activity

        # 2.5 Transformation Functions

        from_loc = Suppress(FROM_LOC) + nest(concept(FROM_LOC))
        to_loc = Suppress(TO_LOC) + nest(concept(TO_LOC))

        self.cell_secretion = cell_secretion_tag + nest(self.simple_abundance)
        self.cell_secretion.addParseAction(handle_secretion)

        self.cell_surface_expression = cell_surface_expression_tag + nest(self.simple_abundance)
        self.cell_surface_expression.addParseAction(handle_surface_expression)

        self.translocation_standard = nest(
            self.simple_abundance
            + WCW
            + Group(from_loc + WCW + to_loc)(EFFECT),
        )

        self.translocation_legacy = nest(
            self.simple_abundance
            + WCW
            + Group(concept(FROM_LOC) + WCW + concept(TO_LOC))(EFFECT),
        )

        self.translocation_legacy.addParseAction(handle_legacy_tloc)
        self.translocation_unqualified = nest(self.simple_abundance)

        if self.disallow_unqualified_translocations:
            self.translocation_unqualified.setParseAction(self.handle_translocation_illegal)

        #: `2.5.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_translocations>`_
        self.translocation = translocation_tag + MatchFirst([
            self.translocation_unqualified,
            self.translocation_standard,
            self.translocation_legacy,
        ])

        #: `2.5.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_degradation_deg>`_
        self.degradation = degradation_tags + nest(self.simple_abundance)

        #: `2.5.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_reaction_rxn>`_
        self.reactants = Suppress(REACTANTS) + nest(delimitedList(Group(self.simple_abundance)))
        self.products = Suppress(PRODUCTS) + nest(delimitedList(Group(self.simple_abundance)))

        self.reaction = reaction_tags + nest(Group(self.reactants)(REACTANTS), Group(self.products)(PRODUCTS))

        self.transformation = MatchFirst([
            self.cell_secretion,
            self.cell_surface_expression,
            self.translocation,
            self.degradation,
            self.reaction,
        ])

        # 3 BEL Relationships

        self.bel_term = MatchFirst([self.transformation, self.process, self.abundance]).streamline()

        self.bel_to_bel_relations = [
            association_tag,
            increases_tag,
            decreases_tag,
            positive_correlation_tag,
            negative_correlation_tag,
            correlation_tag,
            no_correlation_tag,
            binds_tag,
            causes_no_change_tag,
            orthologous_tag,
            is_a_tag,
            equivalent_tag,
            partof_tag,
            directly_increases_tag,
            directly_decreases_tag,
            analogous_tag,
            regulates_tag,
        ]
        self.bel_to_bel = triple(self.bel_term, MatchFirst(self.bel_to_bel_relations), self.bel_term)

        # Mixed Relationships

        #: `3.1.5 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_ratelimitingstepof>`_
        self.rate_limit = triple(
            MatchFirst([self.biological_process, self.activity, self.transformation]),
            rate_limit_tag,
            self.biological_process,
        )

        #: `3.4.6 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_subprocessof>`_
        self.subprocess_of = triple(
            MatchFirst([self.process, self.activity, self.transformation]),
            subprocess_of_tag,
            self.process,
        )

        #: `3.3.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_transcribedto>`_
        self.transcribed = triple(self.gene, transcribed_tag, self.rna)

        #: `3.3.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_translatedto>`_
        self.translated = triple(self.rna, translated_tag, self.protein)

        #: `3.4.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_hasmember>`_
        self.has_member = triple(self.abundance, has_member_tag, self.abundance)

        #: `3.4.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_hasmembers>`_
        self.abundance_list = Suppress('list') + nest(delimitedList(Group(self.abundance)))

        self.has_members = triple(self.abundance, has_members_tag, self.abundance_list)
        self.has_members.setParseAction(self.handle_has_members)

        self.has_components = triple(self.abundance, has_components_tag, self.abundance_list)
        self.has_components.setParseAction(self.handle_has_components)

        self.has_list = self.has_members | self.has_components

        # `3.4.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_hascomponent>`_
        self.has_component = triple(
            self.abundance,
            has_component_tag,
            self.abundance,
        )

        self.biomarker = triple(self.bel_term, biomarker_tags, self.process)

        self.has_variant_relation = triple(self.abundance, has_variant_tags, self.abundance)
        self.part_of_reaction = triple(self.reaction, part_of_reaction_tags, self.abundance)

        self.relation = MatchFirst([
            self.bel_to_bel,
            # self.has_member,
            # self.has_component,
            self.subprocess_of,
            self.rate_limit,
            self.biomarker,
            self.transcribed,
            self.translated,
            # self.has_variant_relation,
            # self.part_of_reaction,
        ])
        if self.graph is not None:
            self.relation.setParseAction(self._handle_relation_harness)

        self.inverted_unqualified_relation = MatchFirst([
            self.has_member,
            self.has_component,
        ])
        if self.graph is not None:
            self.inverted_unqualified_relation.setParseAction(self.handle_inverse_unqualified_relation)

        self.normal_unqualified_relation = MatchFirst([
            self.has_member,
            self.has_component,
            self.has_variant_relation,
            self.part_of_reaction,
        ])
        if self.graph is not None:
            self.normal_unqualified_relation.setParseAction(self.handle_unqualified_relation)

        #: 3.1 Causal Relationships - nested.
        causal_relation_tags = MatchFirst([
            increases_tag,
            decreases_tag,
            directly_decreases_tag,
            directly_increases_tag,
        ])

        self.nested_causal_relationship = triple(
            self.bel_term,
            causal_relation_tags,
            nest(triple(self.bel_term, causal_relation_tags, self.bel_term)),
        )

        if self.graph is not None:
            self.nested_causal_relationship.setParseAction(self.handle_nested_relation)

        # has_members is handled differently from all other relations becuase it gets distrinbuted
        self.relation = MatchFirst([
            self.has_list,
            self.nested_causal_relationship,
            self.relation,
            self.inverted_unqualified_relation,
            self.normal_unqualified_relation,
        ])

        self.singleton_term = self.bel_term + StringEnd()
        if self.graph is not None:
            self.singleton_term.setParseAction(self.handle_term)

        self.statement = self.relation | self.singleton_term
        self.language = self.control_parser.language | self.statement
        self.language.setName('BEL')

        super(BELParser, self).__init__(self.language, streamline=autostreamline)

    def parse(self, s: str) -> Mapping[str, Any]:
        """Parse the string."""
        return self.parseString(s).asDict()

    @property
    def _namespace_dict(self) -> Mapping[str, Mapping[str, str]]:
        """Get the dictionary of {namespace: {name: encoding}} stored in the internal identifier parser."""
        return self.concept_parser.namespace_to_name_to_encoding

    @property
    def _allow_naked_names(self) -> bool:
        """Return if naked names should be parsed (``True``), or if errors should be thrown (``False``)."""
        return self.concept_parser.allow_naked_names

    def get_annotations(self) -> Dict:
        """Get the current annotations in this parser."""
        return self.control_parser.get_annotations()

    def clear(self):
        """Clear the graph and all control parser data (current citation, annotations, and statement group)."""
        if self.graph is not None:
            self.graph.clear()
        self.control_parser.clear()

    def handle_nested_relation(self, line: str, position: int, tokens: ParseResults):
        """Handle nested statements.

        If :code:`self.disallow_nested` is True, raises a ``NestedRelationWarning``.

        :raises: NestedRelationWarning
        """
        if self.disallow_nested:
            raise NestedRelationWarning(self.get_line_number(), line, position)

        subject_hash = self._handle_relation_checked(
            line, position, {
                SOURCE: tokens[SOURCE],
                RELATION: tokens[RELATION],
                TARGET: tokens[TARGET][SOURCE],
            },
        )

        object_hash = self._handle_relation_checked(
            line, position, {
                SOURCE: tokens[TARGET][SOURCE],
                RELATION: tokens[TARGET][RELATION],
                TARGET: tokens[TARGET][TARGET],
            },
        )
        self.graph.add_transitivity(subject_hash, object_hash)
        return tokens

    def check_function_semantics(self, line: str, position: int, tokens: ParseResults) -> ParseResults:
        """Raise an exception if the function used on the tokens is wrong.

        :raises: InvalidFunctionSemantic
        """
        concept = tokens.get(CONCEPT)
        if not self._namespace_dict or concept is None:
            return tokens

        namespace, name = concept[NAMESPACE], concept[NAME]

        if namespace in self.concept_parser.namespace_to_pattern:
            return tokens

        if self._allow_naked_names and namespace == DIRTY:  # Don't check dirty names in lenient mode
            return tokens

        valid_functions = set(
            itt.chain.from_iterable(
                belns_encodings.get(encoding, set())
                for encoding in self._namespace_dict[namespace][name]
            ),
        )

        if not valid_functions:
            raise InvalidEntity(self.get_line_number(), line, position, namespace, name)

        if tokens[FUNCTION] not in valid_functions:
            raise InvalidFunctionSemantic(
                line_number=self.get_line_number(),
                line=line,
                position=position,
                func=tokens[FUNCTION],
                namespace=namespace,
                name=name,
                allowed_functions=valid_functions,
            )

        return tokens

    def handle_term(self, _, __, tokens: ParseResults) -> ParseResults:
        """Handle BEL terms (the subject and object of BEL relations)."""
        self.ensure_node(tokens)
        return tokens

    def _handle_list_helper(self, tokens: ParseResults, relation: str) -> ParseResults:
        """Provide the functionality for :meth:`handle_has_members` and :meth:`handle_has_components`."""
        parent_node_dsl = self.ensure_node(tokens[0])

        for child_tokens in tokens[2]:
            child_node_dsl = self.ensure_node(child_tokens)
            # Note that the polarity is switched since this is just for hasMembers
            # and hasComponents, which are both deprecated as of BEL v2.2
            self.graph.add_unqualified_edge(child_node_dsl, parent_node_dsl, relation)

        return tokens

    def handle_has_members(self, _, __, tokens: ParseResults) -> ParseResults:
        """Handle list relations like ``p(X) hasMembers list(p(Y), p(Z), ...)``."""
        return self._handle_list_helper(tokens, IS_A)

    def handle_has_components(self, _, __, tokens: ParseResults) -> ParseResults:
        """Handle list relations like ``p(X) hasComponents list(p(Y), p(Z), ...)``."""
        return self._handle_list_helper(tokens, PART_OF)

    def _add_qualified_edge_helper(
        self,
        *,
        source,
        source_modifier,
        relation,
        target,
        target_modifier,
        annotations,
    ) -> str:
        """Add a qualified edge from the internal aspects of the parser."""
        m = {
            BINDS: self.graph.add_binds,
        }
        adder = m.get(relation)
        d = dict(
            evidence=self.control_parser.evidence,
            citation=self.control_parser.get_citation(),
            annotations=annotations,
            source_modifier=source_modifier,
            target_modifier=target_modifier,
            **{LINE: self.get_line_number()},
        )
        if adder is not None:
            return adder(source=source, target=target, **d)
        else:
            return self.graph.add_qualified_edge(source=source, target=target, relation=relation, **d)

    def _add_qualified_edge(self, *, source, source_modifier, relation, target, target_modifier) -> str:
        """Add an edge, then adds the opposite direction edge if it should."""
        d = dict(
            relation=relation,
            annotations=self.control_parser.annotations,
        )
        if relation in TWO_WAY_RELATIONS:
            self._add_qualified_edge_helper(
                source=target, source_modifier=target_modifier, target=source, target_modifier=source_modifier, **d
            )
        return self._add_qualified_edge_helper(
            source=source, source_modifier=source_modifier, target=target, target_modifier=target_modifier, **d
        )

    def _handle_relation(self, tokens: ParseResults) -> str:
        """Handle a relation."""
        source = self.ensure_node(tokens[SOURCE])
        source_modifier = modifier_po_to_dict(tokens[SOURCE])
        relation = tokens[RELATION]
        target = self.ensure_node(tokens[TARGET])
        target_modifier = modifier_po_to_dict(tokens[TARGET])

        return self._add_qualified_edge(
            source=source, source_modifier=source_modifier,
            relation=relation,
            target=target, target_modifier=target_modifier,
        )

    def _handle_relation_harness(self, line: str, position: int, tokens: Union[ParseResults, Dict]) -> ParseResults:
        """Handle BEL relations based on the policy specified on instantiation.

        Note: this can't be changed after instantiation!
        """
        self._handle_relation_checked(line, position, tokens)
        return tokens

    def _handle_relation_checked(self, line, position, tokens):
        if not self.control_parser.citation_is_set:
            raise MissingCitationException(self.get_line_number(), line, position)

        if not self.control_parser.evidence:
            raise MissingSupportWarning(self.get_line_number(), line, position)

        missing_required_annotations = self.control_parser.get_missing_required_annotations()
        if missing_required_annotations:
            raise MissingAnnotationWarning(self.get_line_number(), line, position, missing_required_annotations)

        return self._handle_relation(tokens)

    def handle_unqualified_relation(self, _, __, tokens: ParseResults) -> ParseResults:
        """Handle unqualified relations."""
        subject_node_dsl = self.ensure_node(tokens[SOURCE])
        object_node_dsl = self.ensure_node(tokens[TARGET])
        relation = tokens[RELATION]
        self.graph.add_unqualified_edge(subject_node_dsl, object_node_dsl, relation)
        return tokens

    def handle_inverse_unqualified_relation(self, _, __, tokens: ParseResults) -> ParseResults:
        """Handle unqualified relations that should go reverse."""
        source = self.ensure_node(tokens[SOURCE])
        target = self.ensure_node(tokens[TARGET])
        relation = tokens[RELATION]
        self.graph.add_unqualified_edge(source=target, target=source, relation=relation)
        return tokens

    def ensure_node(self, tokens: ParseResults) -> BaseEntity:
        """Turn parsed tokens into canonical node name and makes sure its in the graph."""
        node = parse_result_to_dsl(tokens)
        self.graph.add_node_from_data(node)
        return node

    def handle_translocation_illegal(self, line: str, position: int, tokens: ParseResults) -> None:
        """Handle a malformed translocation."""
        raise MalformedTranslocationWarning(self.get_line_number(), line, position, tokens)


# HANDLERS

def handle_molecular_activity_default(_: str, __: int, tokens: ParseResults) -> ParseResults:
    """Handle a BEL 2.0 style molecular activity with BEL default names."""
    upgraded_cls = language.activity_labels[tokens[0]]
    upgraded_concept = language.activity_mapping[upgraded_cls]
    tokens[NAMESPACE] = upgraded_concept.namespace
    tokens[NAME] = upgraded_concept.name
    tokens[IDENTIFIER] = upgraded_concept.identifier
    return tokens


def handle_activity_legacy(_: str, __: int, tokens: ParseResults) -> ParseResults:
    """Handle BEL 1.0 activities."""
    legacy_cls = language.activity_labels[tokens[MODIFIER]]
    tokens[MODIFIER] = ACTIVITY
    tokens[EFFECT] = language.activity_mapping[legacy_cls]
    logger.log(5, 'upgraded legacy activity to %s', legacy_cls)
    return tokens


def handle_legacy_tloc(line: str, position: int, tokens: ParseResults) -> ParseResults:
    """Handle translocations that lack the ``fromLoc`` and ``toLoc`` entries."""
    logger.log(5, 'legacy translocation statement: %s [%d]', line, position)
    return tokens


def handle_secretion(_, __, tokens: ParseResults) -> ParseResults:
    tokens[MODIFIER] = TRANSLOCATION
    tokens[EFFECT] = {
        FROM_LOC: language.intracellular,
        TO_LOC: language.extracellular,
    }
    return tokens


def handle_surface_expression(_, __, tokens: ParseResults) -> ParseResults:
    tokens[MODIFIER] = TRANSLOCATION
    tokens[EFFECT] = {
        FROM_LOC: language.intracellular,
        TO_LOC: language.cell_surface,
    }
    return tokens


def modifier_po_to_dict(tokens):
    """Get the location, activity, and/or transformation information as a dictionary.

    :return: a dictionary describing the modifier
    :rtype: dict
    """
    attrs = {}

    if LOCATION in tokens:
        attrs[LOCATION] = dict(tokens[LOCATION])

    if MODIFIER not in tokens:
        return attrs

    if tokens[MODIFIER] == DEGRADATION:
        attrs[MODIFIER] = tokens[MODIFIER]

    elif tokens[MODIFIER] == ACTIVITY:
        attrs[MODIFIER] = tokens[MODIFIER]

        if EFFECT in tokens:
            attrs[EFFECT] = dict(tokens[EFFECT])

    elif tokens[MODIFIER] == TRANSLOCATION:
        attrs[MODIFIER] = tokens[MODIFIER]

        if EFFECT in tokens:
            try:
                attrs[EFFECT] = tokens[EFFECT].asDict()
            except AttributeError:  # for when it was auto-upgraded
                attrs[EFFECT] = dict(tokens[EFFECT])

    elif tokens[MODIFIER] == CELL_SECRETION:
        attrs[MODIFIER] = TRANSLOCATION
        attrs[EFFECT] = {
            FROM_LOC: language.intracellular,
            TO_LOC: language.extracellular,
        }

    elif tokens[MODIFIER] == CELL_SURFACE_EXPRESSION:
        attrs[MODIFIER] = TRANSLOCATION
        attrs[EFFECT] = {
            FROM_LOC: language.intracellular,
            TO_LOC: language.cell_surface,
        }

    else:
        raise ValueError('Invalid value for tokens[MODIFIER]: {}'.format(tokens[MODIFIER]))

    return attrs


@lru_cache()
def _default_parser():
    return BELParser(skip_validation=True, citation_clearing=False)


@lru_cache()
def parse(s: str, pprint=False):
    """Parse a BEL statement (without validation)."""
    rv = _default_parser().parse(s)
    if pprint:
        import json
        print(json.dumps(rv, indent=2))
    else:
        return rv
