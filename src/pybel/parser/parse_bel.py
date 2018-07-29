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
    FragmentParser, FusionParser, GeneModificationParser, GeneSubstitutionParser, LocationParser,
    ProteinModificationParser, ProteinSubstitutionParser, TruncationParser, VariantParser,
)
from .modifiers.fusion import build_legacy_fusion
from .parse_control import ControlParser
from .parse_identifier import IdentifierParser
from .utils import WCW, nest, one_of_tags, quote, triple
from .. import language
from ..constants import (
    ABUNDANCE, ACTIVITY, ANALOGOUS_TO, ASSOCIATION, BEL_DEFAULT_NAMESPACE, BIOMARKER_FOR, BIOPROCESS, CAUSES_NO_CHANGE,
    CELL_SECRETION, CELL_SURFACE_EXPRESSION, COMPLEX, COMPOSITE, DECREASES, DEGRADATION, DIRECTLY_DECREASES,
    DIRECTLY_INCREASES, DIRTY, EFFECT, EQUIVALENT_TO, FROM_LOC, FUNCTION, FUSION, GENE, HAS_COMPONENT, HAS_MEMBER,
    HAS_PRODUCT, HAS_REACTANT, HAS_VARIANT, IDENTIFIER, INCREASES, IS_A, LINE, MEMBERS, MIRNA, MODIFIER, NAME,
    NAMESPACE, NEGATIVE_CORRELATION, OBJECT, ORTHOLOGOUS, PART_OF, PATHOLOGY, POSITIVE_CORRELATION, PRODUCTS,
    PROGONSTIC_BIOMARKER_FOR, PROTEIN, RATE_LIMITING_STEP_OF, REACTANTS, REACTION, REGULATES, RELATION, RNA, SUBJECT,
    SUBPROCESS_OF, TARGET, TO_LOC, TRANSCRIBED_TO, TRANSLATED_TO, TRANSLOCATION, TWO_WAY_RELATIONS, VARIANTS,
    belns_encodings,
)
from ..tokens import modifier_po_to_dict, po_to_dict

__all__ = ['BelParser']

log = logging.getLogger('pybel.parser')

general_abundance_tags = one_of_tags(['a', 'abundance'], ABUNDANCE, FUNCTION)
gene_tag = one_of_tags(['g', 'geneAbundance'], GENE, FUNCTION)
mirna_tag = one_of_tags(['m', 'microRNAAbundance'], MIRNA, FUNCTION)
protein_tag = one_of_tags(['p', 'proteinAbundance'], PROTEIN, FUNCTION)
rna_tag = one_of_tags(['r', 'rnaAbundance'], RNA, FUNCTION)
complex_tag = one_of_tags(['complex', 'complexAbundance'], COMPLEX, FUNCTION)
composite_abundance_tag = one_of_tags(['composite', 'compositeAbundance'], COMPOSITE, FUNCTION)
biological_process_tag = one_of_tags(['bp', 'biologicalProcess'], BIOPROCESS, FUNCTION)
pathology_tag = one_of_tags(['o', 'path', 'pathology'], PATHOLOGY, FUNCTION)
activity_tag = one_of_tags(['act', 'activity'], ACTIVITY, MODIFIER)
cell_secretion_tag = one_of_tags(['sec', 'cellSecretion'], CELL_SECRETION, MODIFIER)
cell_surface_expression_tag = one_of_tags(['surf', 'cellSurfaceExpression'], CELL_SURFACE_EXPRESSION, MODIFIER)
translocation_tag = one_of_tags(['translocation', 'tloc'], TRANSLOCATION, MODIFIER)
degradation_tags = one_of_tags(['deg', 'degradation'], DEGRADATION, MODIFIER)
reaction_tags = one_of_tags(['reaction', 'rxn'], REACTION, FUNCTION)
molecular_activity_tags = Suppress(oneOf(['ma', 'molecularActivity']))


class BelParser(BaseParser):
    """Build a parser backed by a given dictionary of namespaces"""

    def __init__(self, graph, namespace_dict=None, annotation_dict=None, namespace_regex=None, annotation_regex=None,
                 allow_naked_names=False, allow_nested=False, allow_unqualified_translocations=False,
                 citation_clearing=True, no_identifier_validation=False, autostreamline=True,
                 required_annotations=None):
        """
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
        :param bool allow_unqualified_translocations: If true, allow translocations without TO and FROM clauses.
        :param bool citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
         Delegated to :class:`pybel.parser.ControlParser`
        :param bool autostreamline: Should the parser be streamlined on instantiation?
        :param Optional[list[str]] required_annotations: Optional list of required annotations
        """
        self.graph = graph
        self.allow_nested = allow_nested

        self.control_parser = ControlParser(
            annotation_dict=annotation_dict,
            annotation_regex=annotation_regex,
            citation_clearing=citation_clearing,
            required_annotations=required_annotations,
        )

        if no_identifier_validation:
            self.identifier_parser = IdentifierParser(
                allow_naked_names=allow_naked_names,
            )
        else:
            self.identifier_parser = IdentifierParser(
                allow_naked_names=allow_naked_names,
                namespace_dict=namespace_dict,
                namespace_regex=namespace_regex,
            )

        identifier = Group(self.identifier_parser.language)(IDENTIFIER)
        ungrouped_identifier = self.identifier_parser.language

        # 2.2 Abundance Modifier Functions

        #: `2.2.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_protein_modifications>`_
        self.pmod = ProteinModificationParser(self.identifier_parser).language

        #: `2.2.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_variant_var>`_
        self.variant = VariantParser().language

        #: `2.2.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_proteolytic_fragments>`_
        self.fragment = FragmentParser().language

        #: `2.2.4 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_cellular_location>`_
        self.location = LocationParser(self.identifier_parser).language
        opt_location = Optional(WCW + self.location)

        #: DEPRECATED: `2.2.X Amino Acid Substitutions <http://openbel.org/language/version_1.0/bel_specification_version_1.0.html#_amino_acid_substitutions>`_
        self.psub = ProteinSubstitutionParser().language

        #: DEPRECATED: `2.2.X Sequence Variations <http://openbel.org/language/version_1.0/bel_specification_version_1.0.html#_sequence_variations>`_
        self.gsub = GeneSubstitutionParser().language

        #: DEPRECATED
        #: `Truncated proteins <http://openbel.org/language/version_1.0/bel_specification_version_1.0.html#_truncated_proteins>`_
        self.trunc = TruncationParser().language

        #: PyBEL BEL Specification variant
        self.gmod = GeneModificationParser().language  # FIXME add identifier parser to this

        # 2.6 Other Functions

        #: `2.6.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_fusion_fus>`_
        self.fusion = FusionParser(self.identifier_parser).language

        # 2.1 Abundance Functions

        #: `2.1.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XcomplexA>`_
        self.general_abundance = general_abundance_tags + nest(ungrouped_identifier + opt_location)

        self.gene_modified = ungrouped_identifier + Optional(
            WCW + delimitedList(Group(self.variant | self.gsub | self.gmod))(VARIANTS))

        self.gene_fusion = Group(self.fusion)(FUSION)
        self.gene_fusion_legacy = Group(build_legacy_fusion(identifier, 'c'))(FUSION)

        self.gene = gene_tag + nest(MatchFirst([
            self.gene_fusion,
            self.gene_fusion_legacy,
            self.gene_modified
        ]) + opt_location)
        """`2.1.4 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XgeneA>`_"""

        self.mirna_modified = ungrouped_identifier + Optional(
            WCW + delimitedList(Group(self.variant))(VARIANTS)) + opt_location

        self.mirna = mirna_tag + nest(self.mirna_modified)
        """`2.1.5 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XmicroRNAA>`_"""

        self.protein_modified = ungrouped_identifier + Optional(
            WCW + delimitedList(Group(MatchFirst([self.pmod, self.variant, self.fragment, self.psub, self.trunc])))(
                VARIANTS))

        self.protein_fusion = Group(self.fusion)(FUSION)
        self.protein_fusion_legacy = Group(build_legacy_fusion(identifier, 'p'))(FUSION)

        self.protein = protein_tag + nest(MatchFirst([
            self.protein_fusion,
            self.protein_fusion_legacy,
            self.protein_modified,
        ]) + opt_location)
        """`2.1.6 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XproteinA>`_"""

        self.rna_modified = ungrouped_identifier + Optional(WCW + delimitedList(Group(self.variant))(VARIANTS))

        self.rna_fusion = Group(self.fusion)(FUSION)
        self.rna_fusion_legacy = Group(build_legacy_fusion(identifier, 'r'))(FUSION)

        self.rna = rna_tag + nest(MatchFirst([
            self.rna_fusion,
            self.rna_fusion_legacy,
            self.rna_modified,
        ]) + opt_location)
        """`2.1.7 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XrnaA>`_"""

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

        self.activity = self.activity_standard | self.activity_legacy
        """`2.3.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#Xactivity>`_"""

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

        if not allow_unqualified_translocations:
            self.translocation_unqualified.setParseAction(self.handle_translocation_illegal)

        self.translocation = translocation_tag + MatchFirst([
            self.translocation_unqualified,
            self.translocation_standard,
            self.translocation_legacy
        ])
        """`2.5.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_translocations>`_"""

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

        # BEL Term to BEL Term Relationships

        #: `3.1.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#Xincreases>`_
        increases_tag = oneOf(['->', '→', 'increases']).setParseAction(replaceWith(INCREASES))

        #: `3.1.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XdIncreases>`_
        directly_increases_tag = one_of_tags(['=>', '⇒', 'directlyIncreases'], DIRECTLY_INCREASES)

        #: `3.1.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#Xdecreases>`_
        decreases_tag = one_of_tags(['-|', 'decreases'], DECREASES)

        #: `3.1.4 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#XdDecreases>`_
        directly_decreases_tag = one_of_tags(['=|', 'directlyDecreases'], DIRECTLY_DECREASES)

        #: `3.5.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_analogous>`_
        analogous_tag = one_of_tags(['analogousTo'], ANALOGOUS_TO)

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
        orthologous_tag = one_of_tags(['orthologous'], ORTHOLOGOUS)

        #: `3.4.5 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_isa>`_
        is_a_tag = Keyword(IS_A)

        #: PyBEL Variants
        equivalent_tag = one_of_tags(['eq', EQUIVALENT_TO], EQUIVALENT_TO)
        partof_tag = Keyword(PART_OF)

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
        rate_limit_tag = oneOf(['rateLimitingStepOf']).setParseAction(replaceWith(RATE_LIMITING_STEP_OF))
        self.rate_limit = triple(
            MatchFirst([self.biological_process, self.activity, self.transformation]),
            rate_limit_tag,
            self.biological_process
        )

        #: `3.4.6 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_subprocessof>`_
        subprocess_of_tag = oneOf(['subProcessOf']).setParseAction(replaceWith(SUBPROCESS_OF))
        self.subprocess_of = triple(
            MatchFirst([self.process, self.activity, self.transformation]),
            subprocess_of_tag,
            self.process
        )

        #: `3.3.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_transcribedto>`_
        transcribed_tag = oneOf([':>', 'transcribedTo']).setParseAction(replaceWith(TRANSCRIBED_TO))
        self.transcribed = triple(self.gene, transcribed_tag, self.rna)

        #: `3.3.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_translatedto>`_
        translated_tag = oneOf(['>>', 'translatedTo']).setParseAction(replaceWith(TRANSLATED_TO))
        self.translated = triple(self.rna, translated_tag, self.protein)

        #: `3.4.1 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_hasmember>`_
        has_member_tag = oneOf(['hasMember']).setParseAction(replaceWith(HAS_MEMBER))
        self.has_member = triple(self.abundance, has_member_tag, self.abundance)

        #: `3.4.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_hasmembers>`_
        self.abundance_list = Suppress('list') + nest(delimitedList(Group(self.abundance)))

        has_members_tag = oneOf(['hasMembers'])
        self.has_members = triple(self.abundance, has_members_tag, self.abundance_list)
        self.has_members.setParseAction(self.handle_has_members)

        has_components_tag = oneOf(['hasComponents'])
        self.has_components = triple(self.abundance, has_components_tag, self.abundance_list)
        self.has_components.setParseAction(self.handle_has_components)

        self.has_list = self.has_members | self.has_components

        # `3.4.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_hascomponent>`_
        has_component_tag = oneOf(['hasComponent']).setParseAction(replaceWith(HAS_COMPONENT))
        self.has_component = triple(
            self.complex_abundances | self.composite_abundance,
            has_component_tag,
            self.abundance
        )

        #: `3.5.2 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_biomarkerfor>`_
        biomarker_tag = oneOf(['biomarkerFor']).setParseAction(replaceWith(BIOMARKER_FOR))

        #: `3.5.3 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_prognosticbiomarkerfor>`_
        prognostic_biomarker_tag = oneOf(['prognosticBiomarkerFor']).setParseAction(
            replaceWith(PROGONSTIC_BIOMARKER_FOR))

        biomarker_tags = biomarker_tag | prognostic_biomarker_tag

        self.biomarker = triple(self.bel_term, biomarker_tags, self.process)

        has_variant_tags = oneOf(['hasVariant']).setParseAction(replaceWith(HAS_VARIANT))
        self.has_variant_relation = triple(self.abundance, has_variant_tags, self.abundance)

        has_reactant_tags = oneOf(['hasReactant']).setParseAction(replaceWith(HAS_REACTANT))
        has_product_tags = oneOf(['hasProduct']).setParseAction(replaceWith(HAS_PRODUCT))
        part_of_reaction_tags = has_reactant_tags | has_product_tags
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

        super(BelParser, self).__init__(self.language, streamline=autostreamline)

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
        """Handles BEL terms (the subject and object of BEL relations)

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        """
        self.ensure_node(tokens)
        return tokens

    def _handle_list_helper(self, tokens, relation):
        """Provides the functionality for :meth:`handle_has_members` and :meth:`handle_has_components`"""
        parent_node_tuple, parent_node_attr = self.ensure_node(tokens[0])

        for child_tokens in tokens[2]:
            child_node_tuple, child_node_attr = self.ensure_node(child_tokens)
            self.graph.add_unqualified_edge(parent_node_tuple, child_node_tuple, relation)

        return tokens

    def handle_has_members(self, line, position, tokens):
        """Handles list relations like ``p(X) hasMembers list(p(Y), p(Z), ...)``

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        """
        return self._handle_list_helper(tokens, HAS_MEMBER)

    def handle_has_components(self, line, position, tokens):
        """Handles list relations like ``p(X) hasComponents list(p(Y), p(Z), ...)``

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        """
        return self._handle_list_helper(tokens, HAS_COMPONENT)

    def _add_qualified_edge_helper(self, u, v, relation, annotations, subject_modifier, object_modifier):
        """Adds a qualified edge from the internal aspects of the parser"""
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
        """Adds an edge, then adds the opposite direction edge if it should"""
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
        """A policy in which all annotations are stored as sets, including single annotations

        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        """
        subject_node_tuple, _ = self.ensure_node(tokens[SUBJECT])
        object_node_tuple, _ = self.ensure_node(tokens[OBJECT])

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
            subject_node_tuple,
            object_node_tuple,
            relation=tokens[RELATION],
            annotations=annotations,
            subject_modifier=subject_modifier,
            object_modifier=object_modifier,
        )

    def _handle_relation_harness(self, line, position, tokens):
        """Handles BEL relations based on the policy specified on instantiation. Note: this can't be changed after
        instantiation!

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
        """Handles unqualified relations

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        """
        subject_node_tuple, _ = self.ensure_node(tokens[SUBJECT])
        object_node_tuple, _ = self.ensure_node(tokens[OBJECT])
        rel = tokens[RELATION]
        self.graph.add_unqualified_edge(subject_node_tuple, object_node_tuple, rel)

    def handle_label_relation(self, line, position, tokens):
        """Handles statements like ``p(X) label "Label for X"``

        :param str line: The line being parsed
        :param int position: The position in the line being parsed
        :param pyparsing.ParseResult tokens: The tokens from PyParsing
        :raises: RelabelWarning
        """
        subject_node_tuple, _ = self.ensure_node(tokens[SUBJECT])
        description = tokens[OBJECT]

        if self.graph.has_node_description(subject_node_tuple):
            raise RelabelWarning(
                line_number=self.line_number,
                line=line,
                position=position,
                node=self.graph.node,
                old_label=self.graph.get_node_description(subject_node_tuple),
                new_label=description
            )

        self.graph.set_node_description(subject_node_tuple, description)

    def ensure_node(self, tokens):
        """Turns parsed tokens into canonical node name and makes sure its in the graph

        :param pyparsing.ParseResult tokens: Tokens from PyParsing
        :return: A pair of the PyBEL node tuple and the PyBEL node data dictionary
        :rtype: tuple[tuple, dict]
        """
        if MODIFIER in tokens:
            return self.ensure_node(tokens[TARGET])

        node_attr_dict = po_to_dict(tokens)
        node_tuple = self.graph.add_node_from_data(node_attr_dict)

        return node_tuple, node_attr_dict

    def handle_translocation_illegal(self, line, position, tokens):
        raise MalformedTranslocationWarning(self.line_number, line, position, tokens)


# HANDLERS

def handle_molecular_activity_default(line, position, tokens):
    """Handles BEL 2.0 style molecular activities with BEL 1.0 default names

    :param str line: The line being parsed
    :param int position: The position in the line being parsed
    :param pyparsing.ParseResult tokens: The tokens from PyParsing
    """
    upgraded = language.activity_labels[tokens[0]]
    log.log(5, 'upgraded legacy activity to %s', upgraded)
    tokens[NAMESPACE] = BEL_DEFAULT_NAMESPACE
    tokens[NAME] = upgraded
    return tokens


def handle_activity_legacy(line, position, tokens):
    """Handles nodes with BEL 1.0 activities

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
