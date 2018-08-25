# -*- coding: utf-8 -*-

"""A parser for BEL.

This module handles parsing BEL relations and validation of semantics.
"""

import itertools as itt
import logging

from pyparsing import And, Group, Keyword, MatchFirst, Optional, StringEnd, Suppress, delimitedList, oneOf, replaceWith

from .baseparser import BaseParser
from .exc import (
    InvalidFunctionSemantic, MalformedTranslocationWarning, MissingAnnotationWarning, MissingCitationException,
    MissingSupportWarning, NestedRelationWarning, RelabelWarning,
)
from .modifiers import (
    get_fragment_language, get_fusion_language, get_gene_modification_language, get_gene_substitution_language,
    get_hgvs_language, get_legacy_fusion_langauge, get_location_language, get_protein_modification_language,
    get_protein_substitution_language, get_truncation_language,
)
from .parse_control import ControlParser
from .parse_identifier import IdentifierParser
from .utils import WCW, nest, one_of_tags, quote, triple
from .. import language
from ..constants import (
    ABUNDANCE, ACTIVITY, ASSOCIATION, BEL_DEFAULT_NAMESPACE, BIOPROCESS, CAUSES_NO_CHANGE, CELL_SECRETION,
    CELL_SURFACE_EXPRESSION, COMPLEX, COMPOSITE, DECREASES, DEGRADATION, DIRECTLY_DECREASES, DIRECTLY_INCREASES, DIRTY,
    EFFECT, EQUIVALENT_TO, FROM_LOC, FUNCTION, FUSION, GENE, HAS_COMPONENT, HAS_MEMBER, IDENTIFIER, INCREASES, IS_A,
    LINE, LOCATION, MEMBERS, MIRNA, MODIFIER, NAME, NAMESPACE, NEGATIVE_CORRELATION, OBJECT, PART_OF, PATHOLOGY,
    POSITIVE_CORRELATION, PRODUCTS, PROTEIN, REACTANTS, REACTION, REGULATES, RELATION, RNA, SUBJECT, TARGET, TO_LOC,
    TRANSCRIBED_TO, TRANSLATED_TO, TRANSLOCATION, TWO_WAY_RELATIONS, VARIANTS, belns_encodings,
)
from ..dsl import cell_surface_expression, secretion
from ..tokens import parse_result_to_dsl

__all__ = [
    'BELParser',
    'modifier_po_to_dict',
]

log = logging.getLogger('pybel.parser')

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
    """Build a parser backed by a given dictionary of namespaces"""

    def __init__(
            self,
            graph,
            namespace_dict=None,
            annotation_dict=None,
            namespace_regex=None,
            annotation_regex=None,
            allow_naked_names=False,
            allow_nested=False,
            disallow_unqualified_translocations=False,
            citation_clearing=True,
            skip_validation=False,
            autostreamline=True,
            required_annotations=None
    ):
        """Build a BEL parser.

        :param pybel.BELGraph graph: The BEL Graph to use to store the network
        :param namespace_dict: A dictionary of {namespace: {name: encoding}}. Delegated to
         :class:`pybel.parser.parse_identifier.IdentifierParser`
        :type namespace_dict: Optional[dict[str,dict[str,str]]]
        :param annotation_dict: A dictionary of {annotation: set of values}. Delegated to
         :class:`pybel.parser.ControlParser`
        :rype annotation_dict: Optional[dict[str,set[str]]]
        :param namespace_regex: A dictionary of {namespace: regular expression strings}. Delegated to
         :class:`pybel.parser.parse_identifier.IdentifierParser`
        :type namespace_regex: Optional[dict[str,str]]
        :param annotation_regex: A dictionary of {annotation: regular expression strings}. Delegated to
         :class:`pybel.parser.ControlParser`
        :type annotation_regex: Optional[dict[str,str]]
        :param bool allow_naked_names: If true, turn off naked namespace failures. Delegated to
         :class:`pybel.parser.parse_identifier.IdentifierParser`
        :param bool allow_nested: If true, turn off nested statement failures. Delegated to
         :class:`pybel.parser.parse_identifier.IdentifierParser`
        :param bool disallow_unqualified_translocations: If true, allow translocations without TO and FROM clauses.
        :param bool citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
         Delegated to :class:`pybel.parser.ControlParser`
        :param bool autostreamline: Should the parser be streamlined on instantiation?
        :param Optional[list[str]] required_annotations: Optional list of required annotations
        """
        self.graph = graph

        self.allow_nested = allow_nested
        self.disallow_unqualified_translocations = disallow_unqualified_translocations

        if skip_validation:
            self.control_parser = ControlParser(
                citation_clearing=citation_clearing,
                required_annotations=required_annotations,
            )

            self.identifier_parser = IdentifierParser(
                allow_naked_names=allow_naked_names,
            )
        else:
            self.control_parser = ControlParser(
                annotation_dict=annotation_dict,
                annotation_regex=annotation_regex,
                citation_clearing=citation_clearing,
                required_annotations=required_annotations,
            )

            self.identifier_parser = IdentifierParser(
                allow_naked_names=allow_naked_names,
                namespace_dict=namespace_dict,
                namespace_regex=namespace_regex,
            )

        identifier = Group(self.identifier_parser.language)(IDENTIFIER)
        ungrouped_identifier = self.identifier_parser.language

        # 2.2 Abundance Modifier Functions

        #: `2.2.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_protein_modifications>`_
        self.pmod = get_protein_modification_language(self.identifier_parser.identifier_qualified)

        #: `2.2.4 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_cellular_location>`_
        self.location = get_location_language(self.identifier_parser.language)
        opt_location = Optional(WCW + self.location)

        #: PyBEL BEL Specification variant
        self.gmod = get_gene_modification_language(self.identifier_parser.identifier_qualified)

        # 2.6 Other Functions

        #: `2.6.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_fusion_fus>`_
        self.fusion = get_fusion_language(self.identifier_parser.language)

        # 2.1 Abundance Functions

        #: `2.1.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XcomplexA>`_
        self.general_abundance = general_abundance_tags + nest(ungrouped_identifier + opt_location)

        self.gene_modified = ungrouped_identifier + Optional(
            WCW + delimitedList(Group(variant | gsub | self.gmod))(VARIANTS))

        self.gene_fusion = Group(self.fusion)(FUSION)
        self.gene_fusion_legacy = Group(get_legacy_fusion_langauge(identifier, 'c'))(FUSION)

        #: `2.1.4 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XgeneA>`_
        self.gene = gene_tag + nest(MatchFirst([
            self.gene_fusion,
            self.gene_fusion_legacy,
            self.gene_modified
        ]) + opt_location)

        self.mirna_modified = ungrouped_identifier + Optional(
            WCW + delimitedList(Group(variant))(VARIANTS)) + opt_location

        #: `2.1.5 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XmicroRNAA>`_
        self.mirna = mirna_tag + nest(self.mirna_modified)

        self.protein_modified = ungrouped_identifier + Optional(
            WCW + delimitedList(Group(MatchFirst([self.pmod, variant, fragment, psub, trunc])))(
                VARIANTS))

        self.protein_fusion = Group(self.fusion)(FUSION)
        self.protein_fusion_legacy = Group(get_legacy_fusion_langauge(identifier, 'p'))(FUSION)

        #: `2.1.6 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XproteinA>`_
        self.protein = protein_tag + nest(MatchFirst([
            self.protein_fusion,
            self.protein_fusion_legacy,
            self.protein_modified,
        ]) + opt_location)

        self.rna_modified = ungrouped_identifier + Optional(WCW + delimitedList(Group(variant))(VARIANTS))

        self.rna_fusion = Group(self.fusion)(FUSION)
        self.rna_fusion_legacy = Group(get_legacy_fusion_langauge(identifier, 'r'))(FUSION)

        #: `2.1.7 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XrnaA>`_
        self.rna = rna_tag + nest(MatchFirst([
            self.rna_fusion,
            self.rna_fusion_legacy,
            self.rna_modified,
        ]) + opt_location)

        self.single_abundance = MatchFirst([
            self.general_abundance,
            self.gene,
            self.mirna,
            self.protein,
            self.rna
        ])

        #: `2.1.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XcomplexA>`_
        self.complex_singleton = complex_tag + nest(ungrouped_identifier + opt_location)

        self.complex_list = complex_tag + nest(
            delimitedList(Group(self.single_abundance | self.complex_singleton))(MEMBERS) + opt_location)

        self.complex_abundances = self.complex_list | self.complex_singleton

        # Definition of all simple abundances that can be used in a composite abundance
        self.simple_abundance = self.complex_abundances | self.single_abundance
        self.simple_abundance.setParseAction(self.check_function_semantics)

        #: `2.1.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XcompositeA>`_
        self.composite_abundance = composite_abundance_tag + nest(
            delimitedList(Group(self.simple_abundance))(MEMBERS) +
            opt_location
        )

        self.abundance = self.simple_abundance | self.composite_abundance

        # 2.4 Process Modifier Function
        # backwards compatibility with BEL v1.0

        molecular_activity_default = oneOf(list(language.activity_labels)).setParseAction(
            handle_molecular_activity_default)

        #: `2.4.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XmolecularA>`_
        self.molecular_activity = molecular_activity_tags + nest(
            molecular_activity_default |
            self.identifier_parser.language
        )

        # 2.3 Process Functions

        #: `2.3.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_biologicalprocess_bp>`_
        self.biological_process = biological_process_tag + nest(ungrouped_identifier)

        #: `2.3.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_pathology_path>`_
        self.pathology = pathology_tag + nest(ungrouped_identifier)

        self.bp_path = self.biological_process | self.pathology
        self.bp_path.setParseAction(self.check_function_semantics)

        self.activity_standard = activity_tag + nest(
            Group(self.simple_abundance)(TARGET) +
            Optional(WCW + Group(self.molecular_activity)(EFFECT))
        )

        activity_legacy_tags = oneOf(language.activities)(MODIFIER)
        self.activity_legacy = activity_legacy_tags + nest(Group(self.simple_abundance)(TARGET))
        self.activity_legacy.setParseAction(handle_activity_legacy)

        #: `2.3.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#Xactivity>`_
        self.activity = self.activity_standard | self.activity_legacy

        self.process = self.bp_path | self.activity

        # 2.5 Transformation Functions

        from_loc = Suppress(FROM_LOC) + nest(identifier(FROM_LOC))
        to_loc = Suppress(TO_LOC) + nest(identifier(TO_LOC))

        self.cell_secretion = cell_secretion_tag + nest(Group(self.simple_abundance)(TARGET))

        self.cell_surface_expression = cell_surface_expression_tag + nest(Group(self.simple_abundance)(TARGET))

        self.translocation_standard = nest(
            Group(self.simple_abundance)(TARGET) +
            WCW +
            Group(from_loc + WCW + to_loc)(EFFECT)
        )

        self.translocation_legacy = nest(
            Group(self.simple_abundance)(TARGET) +
            WCW +
            Group(identifier(FROM_LOC) + WCW + identifier(TO_LOC))(EFFECT)
        )

        self.translocation_legacy.addParseAction(handle_legacy_tloc)
        self.translocation_unqualified = nest(Group(self.simple_abundance)(TARGET))

        if self.disallow_unqualified_translocations:
            self.translocation_unqualified.setParseAction(self.handle_translocation_illegal)

        #: `2.5.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_translocations>`_
        self.translocation = translocation_tag + MatchFirst([
            self.translocation_unqualified,
            self.translocation_standard,
            self.translocation_legacy
        ])

        #: `2.5.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_degradation_deg>`_
        self.degradation = degradation_tags + nest(Group(self.simple_abundance)(TARGET))

        #: `2.5.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_reaction_rxn>`_
        self.reactants = Suppress(REACTANTS) + nest(delimitedList(Group(self.simple_abundance)))
        self.products = Suppress(PRODUCTS) + nest(delimitedList(Group(self.simple_abundance)))

        self.reaction = reaction_tags + nest(Group(self.reactants)(REACTANTS), Group(self.products)(PRODUCTS))

        self.transformation = MatchFirst([
            self.cell_secretion,
            self.cell_surface_expression,
            self.translocation,
            self.degradation,
            self.reaction
        ])

        # 3 BEL Relationships

        self.bel_term = MatchFirst([self.transformation, self.process, self.abundance]).streamline()

        self.bel_to_bel_relations = [
            association_tag,
            increases_tag,
            decreases_tag,
            positive_correlation_tag,
            negative_correlation_tag,
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
            self.biological_process
        )

        #: `3.4.6 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_subprocessof>`_
        self.subprocess_of = triple(
            MatchFirst([self.process, self.activity, self.transformation]),
            subprocess_of_tag,
            self.process
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
            self.complex_abundances | self.composite_abundance,
            has_component_tag,
            self.abundance
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

        self.relation.setParseAction(self._handle_relation_harness)

        self.unqualified_relation = MatchFirst([
            self.has_member,
            self.has_component,
            self.has_variant_relation,
            self.part_of_reaction
        ])

        self.unqualified_relation.setParseAction(self.handle_unqualified_relation)

        #: 3.1 Causal Relationships - nested. Not enabled by default.
        causal_relation_tags = MatchFirst([
            increases_tag,
            decreases_tag,
            directly_decreases_tag,
            directly_increases_tag
        ])

        self.nested_causal_relationship = triple(
            self.bel_term,
            causal_relation_tags,
            nest(triple(self.bel_term, causal_relation_tags, self.bel_term))
        )

        self.nested_causal_relationship.setParseAction(self.handle_nested_relation)

        self.label_relationship = And([Group(self.bel_term)(SUBJECT), Suppress('labeled'), quote(OBJECT)])
        self.label_relationship.setParseAction(self.handle_label_relation)

        # has_members is handled differently from all other relations becuase it gets distrinbuted
        self.relation = MatchFirst([
            self.has_list,
            self.nested_causal_relationship,
            self.relation,
            self.unqualified_relation,
            self.label_relationship,
        ])

        self.singleton_term = (self.bel_term + StringEnd()).setParseAction(self.handle_term)

        self.statement = self.relation | self.singleton_term
        self.language = self.control_parser.language | self.statement
        self.language.setName('BEL')

        super(BELParser, self).__init__(self.language, streamline=autostreamline)

    @property
    def namespace_dict(self):
        """The dictionary of {namespace: {name: encoding}} stored in the internal identifier parser

        :rtype: dict[str,dict[str,str]]
        """
        return self.identifier_parser.namespace_dict

    @property
    def namespace_regex(self):
        """The dictionary of {namespace keyword: compiled regular expression} stored the internal identifier parser

        :rtype: dict[str,re]
        """
        return self.identifier_parser.namespace_regex_compiled

    @property
    def annotation_dict(self):
        """A dictionary of annotations to their set of values

        :rtype: dict[str,set[str]]
        """
        return self.control_parser.annotation_dict

    @property
    def annotation_regex(self):
        """A dictionary of annotations defined by regular expressions {annotation keyword: string regular expression}

        :rtype: dict[str,str]
        """
        return self.control_parser.annotation_regex

    @property
    def allow_naked_names(self):
        """Should naked names be parsed, or should errors be thrown?

        :rtype: bool
        """
        return self.identifier_parser.allow_naked_names

    def get_annotations(self):
        """Get current annotations in this parser

        :rtype: dict
        """
        return self.control_parser.get_annotations()

    def clear(self):
        """Clears the graph and all control parser data (current citation, annotations, and statement group)"""
        self.graph.clear()
        self.control_parser.clear()

    def handle_nested_relation(self, line, position, tokens):
        """Handles nested statements. If :code:`allow_nested` is False, raises a warning.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        :raises: NestedRelationWarning
        """
        if not self.allow_nested:
            raise NestedRelationWarning(self.line_number, line, position)

        self._handle_relation_harness(line, position, {
            SUBJECT: tokens[SUBJECT],
            RELATION: tokens[RELATION],
            OBJECT: tokens[OBJECT][SUBJECT]
        })

        self._handle_relation_harness(line, position, {
            SUBJECT: tokens[OBJECT][SUBJECT],
            RELATION: tokens[OBJECT][RELATION],
            OBJECT: tokens[OBJECT][OBJECT]
        })
        return tokens

    def check_function_semantics(self, line, position, tokens):
        """Raises an exception if the function used on the tokens is wrong

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        :raises: InvalidFunctionSemantic
        """
        if self.namespace_dict is None or NAMESPACE not in tokens:
            return tokens

        namespace, name = tokens[NAMESPACE], tokens[NAME]

        if namespace in self.namespace_regex:
            return tokens

        if self.allow_naked_names and tokens[NAMESPACE] == DIRTY:  # Don't check dirty names in lenient mode
            return tokens

        valid_functions = set(itt.chain.from_iterable(
            belns_encodings[k]
            for k in self.namespace_dict[namespace][name]
        ))

        if tokens[FUNCTION] not in valid_functions:
            raise InvalidFunctionSemantic(self.line_number, line, position, tokens[FUNCTION], namespace, name,
                                          valid_functions)

        return tokens

    def handle_term(self, line, position, tokens):
        """Handle BEL terms (the subject and object of BEL relations).

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        """
        self.ensure_node(tokens)
        return tokens

    def _handle_list_helper(self, tokens, relation):
        """Provide the functionality for :meth:`handle_has_members` and :meth:`handle_has_components`."""
        parent_node_dsl = self.ensure_node(tokens[0])

        for child_tokens in tokens[2]:
            child_node_dsl = self.ensure_node(child_tokens)
            self.graph.add_unqualified_edge(parent_node_dsl, child_node_dsl, relation)

        return tokens

    def handle_has_members(self, line, position, tokens):
        """Handle list relations like ``p(X) hasMembers list(p(Y), p(Z), ...).``

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        """
        return self._handle_list_helper(tokens, HAS_MEMBER)

    def handle_has_components(self, line, position, tokens):
        """Handle list relations like ``p(X) hasComponents list(p(Y), p(Z), ...)``.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        """
        return self._handle_list_helper(tokens, HAS_COMPONENT)

    def _add_qualified_edge_helper(self, u, v, relation, annotations, subject_modifier, object_modifier):
        """Add a qualified edge from the internal aspects of the parser."""
        self.graph.add_qualified_edge(
            u,
            v,
            relation=relation,
            evidence=self.control_parser.evidence,
            citation=self.control_parser.citation.copy(),
            annotations=annotations,
            subject_modifier=subject_modifier,
            object_modifier=object_modifier,
            **{LINE: self.line_number}
        )

    def _add_qualified_edge(self, u, v, relation, annotations, subject_modifier, object_modifier):
        """Add an edge, then adds the opposite direction edge if it should."""
        self._add_qualified_edge_helper(
            u,
            v,
            relation=relation,
            annotations=annotations,
            subject_modifier=subject_modifier,
            object_modifier=object_modifier,
        )

        if relation in TWO_WAY_RELATIONS:
            self._add_qualified_edge_helper(
                v,
                u,
                relation=relation,
                annotations=annotations,
                object_modifier=subject_modifier,
                subject_modifier=object_modifier,
            )

    def _handle_relation(self, tokens):
        """A policy in which all annotations are stored as sets, including single annotations.

        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        """
        subject_node_dsl = self.ensure_node(tokens[SUBJECT])
        object_node_dsl = self.ensure_node(tokens[OBJECT])

        subject_modifier = modifier_po_to_dict(tokens[SUBJECT])
        object_modifier = modifier_po_to_dict(tokens[OBJECT])

        annotations = {
            annotation_name: (
                {
                    ae: True
                    for ae in annotation_entry
                }
                if isinstance(annotation_entry, set) else
                {
                    annotation_entry: True
                }
            )
            for annotation_name, annotation_entry in self.control_parser.annotations.items()
        }

        self._add_qualified_edge(
            subject_node_dsl,
            object_node_dsl,
            relation=tokens[RELATION],
            annotations=annotations,
            subject_modifier=subject_modifier,
            object_modifier=object_modifier,
        )

    def _handle_relation_harness(self, line, position, tokens):
        """Handle BEL relations based on the policy specified on instantiation.

        Note: this can't be changed after instantiation!

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        """
        if not self.control_parser.citation:
            raise MissingCitationException(self.line_number, line, position)

        if not self.control_parser.evidence:
            raise MissingSupportWarning(self.line_number, line, position)

        missing_required_annotations = self.control_parser.get_missing_required_annotations()
        if missing_required_annotations:
            raise MissingAnnotationWarning(self.line_number, line, position, missing_required_annotations)

        self._handle_relation(tokens)

        return tokens

    def handle_unqualified_relation(self, line, position, tokens):
        """Handle unqualified relations.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        """
        subject_node_dsl = self.ensure_node(tokens[SUBJECT])
        object_node_dsl = self.ensure_node(tokens[OBJECT])
        rel = tokens[RELATION]
        self.graph.add_unqualified_edge(subject_node_dsl, object_node_dsl, rel)

    def handle_label_relation(self, line, position, tokens):
        """Handle statements like ``p(X) label "Label for X"``.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        :raises: RelabelWarning
        """
        subject_node_dsl = self.ensure_node(tokens[SUBJECT])
        description = tokens[OBJECT]

        if self.graph.has_node_description(subject_node_dsl):
            raise RelabelWarning(
                line_number=self.line_number,
                line=line,
                position=position,
                node=self.graph.node,
                old_label=self.graph.get_node_description(subject_node_dsl),
                new_label=description
            )

        self.graph.set_node_description(subject_node_dsl, description)

    def ensure_node(self, tokens):
        """Turn parsed tokens into canonical node name and makes sure its in the graph.

        :param pyparsing.ParseResult tokens: Tokens from PyParsing
        :return: A pair of the PyBEL node tuple and the PyBEL node data dictionary
        :rtype: BaseEntity
        """
        if MODIFIER in tokens:
            return self.ensure_node(tokens[TARGET])

        node_dsl = parse_result_to_dsl(tokens)
        self.graph.add_node_from_data(node_dsl)
        return node_dsl

    def handle_translocation_illegal(self, line, position, tokens):
        """Handle a malformed translocation.

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        """
        raise MalformedTranslocationWarning(self.line_number, line, position, tokens)


# HANDLERS

def handle_molecular_activity_default(line, position, tokens):
    """Handle a BEL 2.0 style molecular activity with BEL default names.

    :param str line: The line being parsed
    :param int position: The position in the line being parsed
    :param pyparsing.ParseResult tokens: The tokens from PyParsing
    """
    upgraded = language.activity_labels[tokens[0]]
    tokens[NAMESPACE] = BEL_DEFAULT_NAMESPACE
    tokens[NAME] = upgraded
    return tokens


def handle_activity_legacy(line, position, tokens):
    """Handle BEL 1.0 activities.

    :param str line: The line being parsed
    :param int position: The position in the line being parsed
    :param pyparsing.ParseResult tokens: The tokens from PyParsing
    """
    legacy_cls = language.activity_labels[tokens[MODIFIER]]
    tokens[MODIFIER] = ACTIVITY
    tokens[EFFECT] = {
        NAME: legacy_cls,
        NAMESPACE: BEL_DEFAULT_NAMESPACE
    }
    log.log(5, 'upgraded legacy activity to %s', legacy_cls)
    return tokens


def handle_legacy_tloc(line, position, tokens):
    """Handles translocations that lack the ``fromLoc`` and ``toLoc`` entries

    :param str line: The line being parsed
    :param int position: The position in the line being parsed
    :param pyparsing.ParseResult tokens: The tokens from PyParsing
    """
    log.log(5, 'legacy translocation statement: %s', line)
    return tokens


def modifier_po_to_dict(tokens):
    """Get location, activity, and/or transformation information as a dictionary.

    :return: a dictionary describing the modifier
    :rtype: dict
    """
    attrs = {}

    if LOCATION in tokens:
        attrs[LOCATION] = dict(tokens[LOCATION])

    if MODIFIER not in tokens:
        return attrs

    if LOCATION in tokens[TARGET]:
        attrs[LOCATION] = tokens[TARGET][LOCATION].asDict()

    if tokens[MODIFIER] == DEGRADATION:
        attrs[MODIFIER] = tokens[MODIFIER]

    elif tokens[MODIFIER] == ACTIVITY:
        attrs[MODIFIER] = tokens[MODIFIER]

        if EFFECT in tokens:
            attrs[EFFECT] = dict(tokens[EFFECT])

    elif tokens[MODIFIER] == TRANSLOCATION:
        attrs[MODIFIER] = tokens[MODIFIER]

        if EFFECT in tokens:
            attrs[EFFECT] = tokens[EFFECT].asDict()

    elif tokens[MODIFIER] == CELL_SECRETION:
        attrs.update(secretion())

    elif tokens[MODIFIER] == CELL_SURFACE_EXPRESSION:
        attrs.update(cell_surface_expression())

    else:
        raise ValueError('Invalid value for tokens[MODIFIER]: {}'.format(tokens[MODIFIER]))

    return attrs
