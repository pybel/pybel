# -*- coding: utf-8 -*-

"""
Relation Parser
~~~~~~~~~~~~~~~
This module handles parsing BEL relations and validation of semantics.
"""

import itertools as itt
import logging
from copy import deepcopy

import networkx as nx
from pyparsing import Suppress, delimitedList, oneOf, Optional, Group, replaceWith, MatchFirst
from pyparsing import pyparsing_common as ppc

from . import language
from .baseparser import BaseParser, WCW, nest, one_of_tags, triple
from .language import value_map
from .modifiers import FusionParser, VariantParser, canonicalize_variant, FragmentParser, GmodParser, GsubParser, \
    LocationParser, PmodParser, PsubParser, TruncParser
from .parse_control import ControlParser
from .parse_exceptions import NestedRelationWarning, MalformedTranslocationWarning, \
    MissingCitationException, InvalidFunctionSemantic, MissingSupportWarning
from .parse_identifier import IdentifierParser
from .utils import list2tuple, cartesian_dictionary
from .. import constants as pbc
from ..constants import EQUIVALENT_TO
from ..constants import FUNCTION, NAMESPACE, NAME, IDENTIFIER, VARIANTS, PYBEL_DEFAULT_NAMESPACE, DIRTY, EVIDENCE, \
    GOCC_KEYWORD
from ..constants import GENE, RNA, PROTEIN, MIRNA, ABUNDANCE, BIOPROCESS, PATHOLOGY, REACTION, COMPLEX, COMPOSITE
from ..constants import HAS_VARIANT, HAS_COMPONENT, HAS_PRODUCT, HAS_REACTANT, HAS_MEMBER, TRANSCRIBED_TO, TRANSLATED_TO
from ..constants import TWO_WAY_RELATIONS, ACTIVITY, DEGRADATION, TRANSLOCATION, CELL_SECRETION, \
    CELL_SURFACE_EXPRESSION, PARTNER_3P, PARTNER_5P, RANGE_3P, RANGE_5P, FUSION, MODIFIER, EFFECT, TARGET, \
    TRANSFORMATION, FROM_LOC, TO_LOC, MEMBERS, REACTANTS, PRODUCTS, LOCATION, SUBJECT, OBJECT, RELATION

log = logging.getLogger('pybel')

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
reaction_tags = one_of_tags(['reaction', 'rxn'], REACTION, TRANSFORMATION)
molecular_activity_tags = Suppress(oneOf(['ma', 'molecularActivity']))


def fusion_handler_wrapper(reference, start):
    def fusion_handler(s, l, tokens):
        if tokens[0] == '?':
            tokens[FusionParser.MISSING] = '?'
            return tokens

        tokens[FusionParser.REF] = reference
        tokens[FusionParser.LEFT if start else FusionParser.RIGHT] = '?'
        tokens[FusionParser.RIGHT if start else FusionParser.LEFT] = int(tokens[0])

        return tokens

    return fusion_handler


class BelParser(BaseParser):
    def __init__(self, graph=None, valid_namespaces=None, namespace_mapping=None, valid_annotations=None,
                 namespace_re=None, complete_origin=False, allow_naked_names=False, allow_nested=False,
                 autostreamline=False):
        """Build a parser backed by a given dictionary of namespaces

        :param graph: the graph to put the network in. Constructs new :class:`nx.MultiDiGraph` if None
        :type graph: nx.MultiDiGraph
        :param valid_namespaces: A dictionary of {namespace: set of members}
        :type valid_namespaces: dict
        :param valid_annotations: a dict of {annotation: set of values}
        :type valid_annotations: dict
        :param namespace_re: a dictionary {namespace: regular expression strings}
        :type namespace_re: dict
        :param namespace_mapping: a dict of {name: {value: (other_namespace, other_name)}}
        :type namespace_mapping: dict
        :param complete_origin: if true, add the gene and RNA origin of proteins to the network during compilation
        :type complete_origin: bool
        :param allow_naked_names: if true, turn off naked namespace failures
        :type allow_naked_names: bool
        :param allow_nested: if true, turn off nested statement failures
        :type allow_nested: bool
        """

        self.graph = graph if graph is not None else nx.MultiDiGraph()
        self.allow_naked_names = allow_naked_names
        self.allow_nested = allow_nested
        self.complete_origin = complete_origin
        self.control_parser = ControlParser(valid_annotations=valid_annotations)
        self.identifier_parser = IdentifierParser(
            valid_namespaces=valid_namespaces,
            namespace_re=namespace_re,
            mapping=namespace_mapping,
            allow_naked_names=self.allow_naked_names
        )

        identifier = Group(self.identifier_parser.get_language())(IDENTIFIER)

        # 2.2 Abundance Modifier Functions

        #: 2.2.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_protein_modifications
        self.pmod = PmodParser(namespace_parser=self.identifier_parser).get_language()

        #: 2.2.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_variant_var
        self.variant = VariantParser().get_language()

        #: 2.2.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_proteolytic_fragments
        self.fragment = FragmentParser().get_language()

        #: 2.2.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_cellular_location
        self.location = LocationParser(self.identifier_parser).get_language()
        opt_location = Optional(WCW + self.location)

        #: 2.2.X DEPRECATED
        #: http://openbel.org/language/web/version_1.0/bel_specification_version_1.0.html#_amino_acid_substitutions
        self.psub = PsubParser().get_language()

        #: 2.2.X DEPRECATED
        #: http://openbel.org/language/web/version_1.0/bel_specification_version_1.0.html#_sequence_variations
        self.gsub = GsubParser().get_language()

        #: DEPRECATED
        #: http://openbel.org/language/web/version_1.0/bel_specification_version_1.0.html#_truncated_proteins
        self.trunc = TruncParser().get_language()

        #: PyBEL BEL Specification variant
        self.gmod = GmodParser().get_language()

        # 2.6 Other Functions

        #: 2.6.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_fusion_fus
        self.fusion = FusionParser(self.identifier_parser).get_language()

        # 2.1 Abundance Functions

        #: 2.1.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcomplexA
        self.general_abundance = general_abundance_tags + nest(identifier + opt_location)

        self.gene_modified = identifier + Optional(
            WCW + delimitedList(Group(self.variant | self.gsub | self.gmod))(VARIANTS))

        self.gene_fusion = Group(self.fusion)(FUSION)

        gene_break_5p = (ppc.integer | '?').setParseAction(fusion_handler_wrapper('c', start=True))
        gene_break_3p = (ppc.integer | '?').setParseAction(fusion_handler_wrapper('c', start=False))

        self.gene_fusion_legacy = Group(identifier(PARTNER_5P) + WCW + FusionParser.fusion_tags + nest(
            identifier(PARTNER_3P) + Optional(
                WCW + Group(gene_break_5p)(RANGE_5P) + WCW + Group(gene_break_3p)(RANGE_3P))))(FUSION)

        self.gene = gene_tag + nest(MatchFirst([
            self.gene_fusion,
            self.gene_fusion_legacy,
            self.gene_modified
        ]) + opt_location)
        """2.1.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XgeneA"""

        self.mirna_modified = identifier + Optional(WCW + delimitedList(Group(self.variant))(VARIANTS)) + opt_location

        self.mirna = mirna_tag + nest(self.mirna_modified)
        """2.1.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XmicroRNAA"""

        self.protein_modified = identifier + Optional(
            WCW + delimitedList(Group(MatchFirst([self.pmod, self.variant, self.fragment, self.psub, self.trunc])))(
                VARIANTS))

        self.protein_fusion = Group(self.fusion)(FUSION)

        protein_break_5p = (ppc.integer | '?').setParseAction(fusion_handler_wrapper('p', start=True))
        protein_break_3p = (ppc.integer | '?').setParseAction(fusion_handler_wrapper('p', start=False))

        self.protein_fusion_legacy = Group(identifier(PARTNER_5P) + WCW + FusionParser.fusion_tags + nest(
            identifier(PARTNER_3P) + Optional(
                WCW + Group(protein_break_5p)(RANGE_5P) + WCW + Group(protein_break_3p)(RANGE_3P))))(FUSION)

        self.protein = protein_tag + nest(MatchFirst([
            self.protein_fusion,
            self.protein_fusion_legacy,
            self.protein_modified,
        ]) + opt_location)
        """2.1.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XproteinA"""

        self.rna_modified = identifier + Optional(WCW + delimitedList(Group(self.variant))(VARIANTS))

        self.rna_fusion = Group(self.fusion)(FUSION)

        rna_break_start = (ppc.integer | '?').setParseAction(fusion_handler_wrapper('r', start=True))
        rna_break_end = (ppc.integer | '?').setParseAction(fusion_handler_wrapper('r', start=False))

        self.rna_fusion_legacy = Group(identifier(PARTNER_5P) + WCW + FusionParser.fusion_tags + nest(
            identifier(PARTNER_3P) + Optional(
                WCW + Group(rna_break_start)(RANGE_5P) + WCW + Group(rna_break_end)(RANGE_3P))))(FUSION)

        self.rna = rna_tag + nest(MatchFirst([
            self.rna_fusion,
            self.rna_fusion_legacy,
            self.rna_modified,
        ]) + opt_location)
        """2.1.7 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XrnaA"""

        self.single_abundance = MatchFirst([self.general_abundance, self.gene, self.mirna, self.protein, self.rna])

        #: 2.1.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcomplexA
        self.complex_singleton = complex_tag + nest(identifier + opt_location)

        self.complex_list = complex_tag + nest(
            delimitedList(Group(self.single_abundance | self.complex_singleton))(MEMBERS) + opt_location)

        self.complex_abundances = self.complex_list | self.complex_singleton

        # Definition of all simple abundances that can be used in a composite abundance
        self.simple_abundance = self.complex_abundances | self.single_abundance
        self.simple_abundance.setParseAction(self.check_function_semantics)

        #: 2.1.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcompositeA
        self.composite_abundance = composite_abundance_tag + nest(
            delimitedList(Group(self.simple_abundance))(MEMBERS) + opt_location)

        self.abundance = self.simple_abundance | self.composite_abundance

        # 2.4 Process Modifier Function
        # backwards compatibility with BEL v1.0

        def handle_molecular_activity_default(s, l, tokens):
            upgraded = language.activity_labels[tokens[0]]
            log.debug('upgraded molecular activity to %s', upgraded)
            tokens[NAMESPACE] = PYBEL_DEFAULT_NAMESPACE
            tokens[NAME] = upgraded
            return tokens

        molecular_activity_default = oneOf(language.activity_labels.keys()).setParseAction(
            handle_molecular_activity_default)

        self.molecular_activity = molecular_activity_tags + nest(
            molecular_activity_default | self.identifier_parser.get_language())
        """2.4.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XmolecularA"""

        # 2.3 Process Functions

        #: 2.3.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_biologicalprocess_bp
        self.biological_process = biological_process_tag + nest(identifier)

        #: 2.3.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_pathology_path
        self.pathology = pathology_tag + nest(identifier)

        self.bp_path = self.biological_process | self.pathology
        self.bp_path.setParseAction(self.check_function_semantics)

        self.activity_standard = activity_tag + nest(
            Group(self.abundance)(TARGET) + Optional(WCW + Group(self.molecular_activity)(EFFECT)))

        activity_legacy_tags = oneOf(language.activities)(MODIFIER)
        self.activity_legacy = activity_legacy_tags + nest(Group(self.abundance)(TARGET))

        def handle_activity_legacy(s, l, tokens):
            legacy_cls = language.activity_labels[tokens[MODIFIER]]
            tokens[MODIFIER] = ACTIVITY
            tokens[EFFECT] = {
                NAME: legacy_cls,
                NAMESPACE: PYBEL_DEFAULT_NAMESPACE
            }
            log.debug('upgraded legacy activity to %s', legacy_cls)
            return tokens

        self.activity_legacy.setParseAction(handle_activity_legacy)

        self.activity = self.activity_standard | self.activity_legacy
        """2.3.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xactivity"""

        self.process = self.bp_path | self.activity

        # 2.5 Transformation Functions

        from_loc = Suppress(FROM_LOC) + nest(identifier(FROM_LOC))
        to_loc = Suppress(TO_LOC) + nest(identifier(TO_LOC))

        self.cell_secretion = cell_secretion_tag + nest(Group(self.simple_abundance)(TARGET))

        self.cell_surface_expression = cell_surface_expression_tag + nest(Group(self.simple_abundance)(TARGET))

        self.translocation_standard = nest(
            Group(self.simple_abundance)(TARGET) + WCW + Group(from_loc + WCW + to_loc)(EFFECT))

        self.translocation_legacy = nest(
            Group(self.simple_abundance)(TARGET) + WCW + Group(identifier(FROM_LOC) + WCW + identifier(TO_LOC))(
                EFFECT))

        def handle_legacy_tloc(s, l, tokens):
            log.debug('Legacy translocation statement: %s', s)
            return tokens

        self.translocation_legacy.addParseAction(handle_legacy_tloc)

        # TODO deprecate
        self.translocation_illegal = nest(self.simple_abundance)

        def handle_translocation_illegal(s, l, t):
            raise MalformedTranslocationWarning('Unqualified translocation {} {} {}'.format(s, l, t))

        self.translocation_illegal.setParseAction(handle_translocation_illegal)

        self.translocation = translocation_tag + MatchFirst(
            [self.translocation_illegal, self.translocation_standard, self.translocation_legacy])
        """2.5.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_translocations"""

        #: 2.5.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_degradation_deg
        self.degradation = degradation_tags + nest(Group(self.simple_abundance)(TARGET))

        #: 2.5.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_reaction_rxn
        self.reactants = Suppress(REACTANTS) + nest(delimitedList(Group(self.simple_abundance)))
        self.products = Suppress(PRODUCTS) + nest(delimitedList(Group(self.simple_abundance)))

        self.reaction = reaction_tags + nest(Group(self.reactants)(REACTANTS), Group(self.products)(PRODUCTS))

        self.transformation = MatchFirst(
            [self.cell_secretion, self.cell_surface_expression, self.translocation, self.degradation, self.reaction])

        # 3 BEL Relationships

        self.bel_term = MatchFirst([self.transformation, self.process, self.abundance]).streamline()

        # BEL Term to BEL Term Relationships

        #: 3.1.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xincreases
        increases_tag = oneOf(['->', '→', 'increases']).setParseAction(replaceWith(pbc.INCREASES))

        #: 3.1.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XdIncreases
        directly_increases_tag = oneOf(['=>', '⇒', 'directlyIncreases']).setParseAction(
            replaceWith(pbc.DIRECTLY_INCREASES))

        #: 3.1.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xdecreases
        decreases_tag = oneOf(['-|', 'decreases']).setParseAction(replaceWith(pbc.DECREASES))

        #: 3.1.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XdDecreases
        directly_decreases_tag = oneOf(['=|', 'directlyDecreases']).setParseAction(
            replaceWith(pbc.DIRECTLY_DECREASES))

        #: 3.5.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_analogous
        analogous_tag = oneOf(['analogousTo'])

        #: 3.1.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xcnc
        causes_no_change_tag = oneOf(['cnc', 'causesNoChange']).setParseAction(replaceWith(pbc.CAUSES_NO_CHANGE))

        #: 3.1.7 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_regulates_reg
        regulates_tag = oneOf(['reg', 'regulates']).setParseAction(replaceWith('regulates'))

        #: 3.2.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XnegCor
        negative_correlation_tag = oneOf(['neg', 'negativeCorrelation']).setParseAction(
            replaceWith(pbc.NEGATIVE_CORRELATION))

        #: 3.2.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XposCor
        positive_correlation_tag = oneOf(['pos', 'positiveCorrelation']).setParseAction(
            replaceWith(pbc.POSITIVE_CORRELATION))

        #: 3.2.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xassociation
        association_tag = oneOf(['--', 'association']).setParseAction(replaceWith('association'))

        #: 3.3.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_orthologous
        orthologous_tag = oneOf(['orthologous'])

        #: 3.4.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_isa
        is_a_tag = oneOf(['isA'])

        #: PyBEL Variant
        equivalent_tag = oneOf(['eq', EQUIVALENT_TO]).setParseAction(replaceWith(EQUIVALENT_TO))

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
            directly_increases_tag,
            directly_decreases_tag,
            analogous_tag,
            regulates_tag,
        ]
        self.bel_to_bel = triple(self.bel_term, MatchFirst(self.bel_to_bel_relations), self.bel_term)

        # Mixed Relationships

        #: 3.1.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_ratelimitingstepof
        rate_limit_tag = oneOf(['rateLimitingStepOf'])
        self.rate_limit = triple(MatchFirst([self.biological_process, self.activity, self.transformation]),
                                 rate_limit_tag, self.biological_process)

        #: 3.4.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_subprocessof
        subprocess_of_tag = oneOf(['subProcessOf'])
        self.subprocess_of = triple(MatchFirst([self.process, self.activity, self.transformation]), subprocess_of_tag,
                                    self.process)

        #: 3.3.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_transcribedto
        transcribed_tag = oneOf([':>', 'transcribedTo']).setParseAction(replaceWith(pbc.TRANSCRIBED_TO))
        self.transcribed = triple(self.gene, transcribed_tag, self.rna)

        #: 3.3.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_translatedto
        translated_tag = oneOf(['>>', 'translatedTo']).setParseAction(replaceWith(pbc.TRANSLATED_TO))
        self.translated = triple(self.rna, translated_tag, self.protein)

        #: 3.4.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_hasmember
        has_member_tag = oneOf(['hasMember'])
        self.has_member = triple(self.abundance, has_member_tag, self.abundance)

        #: 3.4.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_hasmembers
        self.abundance_list = Suppress('list') + nest(delimitedList(Group(self.abundance)))

        has_members_tag = oneOf(['hasMembers'])
        self.has_members = triple(self.abundance, has_members_tag, self.abundance_list)
        self.has_members.setParseAction(self.handle_has_members)

        # 3.4.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_hascomponent
        has_component_tag = oneOf(['hasComponent'])
        self.has_component = triple(self.complex_abundances | self.composite_abundance, has_component_tag,
                                    self.abundance)

        #: 3.5.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_biomarkerfor
        biomarker_tag = oneOf(['biomarkerFor'])

        #: 3.5.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_prognosticbiomarkerfor
        prognostic_biomarker_tag = oneOf(['prognosticBiomarkerFor'])

        biomarker_tags = biomarker_tag | prognostic_biomarker_tag

        self.biomarker = triple(self.bel_term, biomarker_tags, self.process)

        self.relation = MatchFirst([
            self.bel_to_bel,
            self.has_member,
            self.has_component,
            self.subprocess_of,
            self.rate_limit,
            self.biomarker,
            self.transcribed,
            self.translated,
        ])

        self.relation.setParseAction(self.handle_relation)

        #: 3.1 Causal Relationships - nested. Explicitly not supported because of ambiguity
        causal_relation_tags = MatchFirst([increases_tag, decreases_tag,
                                           directly_decreases_tag, directly_increases_tag])

        self.nested_causal_relationship = triple(self.bel_term, causal_relation_tags,
                                                 nest(triple(self.bel_term, causal_relation_tags, self.bel_term)))

        self.nested_causal_relationship.setParseAction(self.handle_nested_relation)

        # has_members is handled differently from all other relations becuase it gets distrinbuted
        self.relation = MatchFirst([self.has_members, self.nested_causal_relationship, self.relation])

        self.statement = self.relation | self.bel_term.setParseAction(self.handle_term)
        self.language = self.control_parser.get_language() | self.statement
        self.language.setName('BEL')

        if autostreamline:
            self.streamline()

    def get_language(self):
        """Get language defined by this parser"""
        return self.language

    def get_annotations(self):
        """Get current annotations in this parser

        :rtype: dict
        """
        return self.control_parser.get_annotations()

    def clear(self):
        """Clears the graph and all control parser data (current citation, annotations, and statement group)"""
        self.graph.clear()
        self.control_parser.clear()

    def handle_nested_relation(self, s, l, tokens):
        if not self.allow_nested:
            raise NestedRelationWarning(s)

        self.handle_relation(s, l, {
            SUBJECT: tokens[SUBJECT],
            RELATION: tokens[RELATION],
            OBJECT: tokens[OBJECT][SUBJECT]
        })

        self.handle_relation(s, l, {
            SUBJECT: tokens[OBJECT][SUBJECT],
            RELATION: tokens[OBJECT][RELATION],
            OBJECT: tokens[OBJECT][OBJECT]
        })
        return tokens

    def check_function_semantics(self, s, l, tokens):
        if self.identifier_parser.namespace_dict is None or IDENTIFIER not in tokens:
            return tokens

        namespace, name = tokens[IDENTIFIER][NAMESPACE], tokens[IDENTIFIER][NAME]

        if namespace in self.identifier_parser.namespace_re:
            return tokens

        if self.allow_naked_names and tokens[IDENTIFIER][NAMESPACE] == DIRTY:  # Don't check dirty names in lenient mode
            return tokens

        valid_function_codes = set(itt.chain.from_iterable(
            value_map[v] for v in self.identifier_parser.namespace_dict[namespace][name]))

        if tokens[FUNCTION] not in valid_function_codes:
            valid = set(itt.chain.from_iterable(
                value_map[k] for k in self.identifier_parser.namespace_dict[namespace][name]))
            raise InvalidFunctionSemantic(tokens[FUNCTION], namespace, name, valid)

        return tokens

    def handle_term(self, s, l, tokens):
        self.ensure_node(s, l, tokens)
        return tokens

    def check_required_annotations(self, s):
        if not self.control_parser.citation:
            raise MissingCitationException(s)

        if EVIDENCE not in self.control_parser.annotations:
            raise MissingSupportWarning(s)

    def build_attrs(self, attrs=None, list_attrs=None):
        attrs = {} if attrs is None else attrs
        list_attrs = {} if list_attrs is None else list_attrs
        for annotation_name, annotation_entry in self.get_annotations().items():
            if isinstance(annotation_entry, set):
                list_attrs[annotation_name] = annotation_entry
            else:
                attrs[annotation_name] = annotation_entry
        return attrs, list_attrs

    def handle_has_members(self, s, l, tokens):
        parent = self.ensure_node(s, l, tokens[0])
        for child_tokens in tokens[2]:
            child = self.ensure_node(s, l, child_tokens)
            self.graph.add_edge(parent, child, **{RELATION: HAS_MEMBER})
        return tokens

    def handle_relation(self, s, l, tokens):
        self.check_required_annotations(s)

        sub = self.ensure_node(s, l, tokens[SUBJECT])
        obj = self.ensure_node(s, l, tokens[OBJECT])

        attrs, list_attrs = self.build_attrs()

        attrs[RELATION] = tokens[RELATION]

        sub_mod = canonicalize_modifier(tokens[SUBJECT])
        if sub_mod:
            attrs[SUBJECT] = sub_mod

        obj_mod = canonicalize_modifier(tokens[OBJECT])
        if obj_mod:
            attrs[OBJECT] = obj_mod

        for single_annotation in cartesian_dictionary(list_attrs):
            self.graph.add_edge(sub, obj, attr_dict=attrs, **single_annotation)
            if tokens[RELATION] in TWO_WAY_RELATIONS:
                self.add_reverse_edge(sub, obj, attrs, **single_annotation)

        return tokens

    def add_reverse_edge(self, sub, obj, attrs, **single_annotation):
        new_attrs = {k: v for k, v in attrs.items() if k not in {SUBJECT, OBJECT}}
        attrs_subject, attrs_object = attrs.get(SUBJECT), attrs.get(OBJECT)
        if attrs_subject:
            new_attrs[OBJECT] = attrs_subject
        if attrs_object:
            new_attrs[SUBJECT] = attrs_object

        self.graph.add_edge(obj, sub, attr_dict=new_attrs, **single_annotation)

    def add_unqualified_edge(self, u, v, relation):
        """Adds unique edge that has no annotations

        :param u: source node
        :param v: target node
        :param relation: relationship label
        """
        key = language.unqualified_edge_code[relation]
        if not self.graph.has_edge(u, v, key):
            self.graph.add_edge(u, v, key=key, **{RELATION: relation})

    def ensure_node(self, s, l, tokens):
        """Turns parsed tokens into canonical node name and makes sure its in the graph

        :return: the canonical name of the node
        :rtype: str
        """

        if MODIFIER in tokens:
            return self.ensure_node(s, l, tokens[TARGET])

        name = canonicalize_node(tokens)

        if name in self.graph:
            return name

        if TRANSFORMATION in tokens:
            self.graph.add_node(name, **{FUNCTION: tokens[TRANSFORMATION]})

            for reactant_tokens in tokens[REACTANTS]:
                reactant_name = self.ensure_node(s, l, reactant_tokens)
                self.add_unqualified_edge(name, reactant_name, HAS_REACTANT)

            for product_tokens in tokens[PRODUCTS]:
                product_name = self.ensure_node(s, l, product_tokens)
                self.add_unqualified_edge(name, product_name, HAS_PRODUCT)

            return name

        elif FUNCTION in tokens and MEMBERS in tokens:
            self.graph.add_node(name, **{FUNCTION: tokens[FUNCTION]})

            for token in tokens[MEMBERS]:
                member_name = self.ensure_node(s, l, token)
                self.add_unqualified_edge(name, member_name, HAS_COMPONENT)
            return name

        elif FUNCTION in tokens and VARIANTS in tokens:
            self.graph.add_node(name, {
                FUNCTION: tokens[FUNCTION],
                NAMESPACE: tokens[IDENTIFIER][NAMESPACE],
                NAME: tokens[IDENTIFIER][NAME],
                VARIANTS: [variant.asDict() for variant in tokens[VARIANTS]]
            })

            c = {
                FUNCTION: tokens[FUNCTION],
                IDENTIFIER: tokens[IDENTIFIER]
            }

            parent = self.ensure_node(s, l, c)
            self.add_unqualified_edge(parent, name, HAS_VARIANT)
            return name

        elif FUNCTION in tokens and FUSION in tokens:
            f = tokens[FUSION]
            d = {
                FUNCTION: tokens[FUNCTION],
                FUSION: {
                    PARTNER_5P: {NAMESPACE: f[PARTNER_5P][NAMESPACE], NAME: f[PARTNER_5P][NAME]},
                    RANGE_5P: f[RANGE_5P] if RANGE_5P in f else '?',
                    PARTNER_3P: {NAMESPACE: f[PARTNER_3P][NAMESPACE], NAME: f[PARTNER_3P][NAME]},
                    RANGE_3P: f[RANGE_3P] if RANGE_3P in f else '?'
                }
            }
            self.graph.add_node(name, **d)
            return name

        elif FUNCTION in tokens and IDENTIFIER in tokens:
            if tokens[FUNCTION] in {GENE, MIRNA, PATHOLOGY, BIOPROCESS, ABUNDANCE, COMPLEX}:
                self.graph.add_node(name, {
                    FUNCTION: tokens[FUNCTION],
                    NAMESPACE: tokens[IDENTIFIER][NAMESPACE],
                    NAME: tokens[IDENTIFIER][NAME]
                })
                return name

            elif tokens[FUNCTION] == RNA:
                self.graph.add_node(name, {
                    FUNCTION: tokens[FUNCTION],
                    NAMESPACE: tokens[IDENTIFIER][NAMESPACE],
                    NAME: tokens[IDENTIFIER][NAME]
                })

                if not self.complete_origin:
                    return name

                gene_tokens = deepcopy(tokens)
                gene_tokens[FUNCTION] = GENE
                gene_name = self.ensure_node(s, l, gene_tokens)

                self.add_unqualified_edge(gene_name, name, TRANSCRIBED_TO)
                return name

            elif tokens[FUNCTION] == PROTEIN:
                self.graph.add_node(name, {
                    FUNCTION: tokens[FUNCTION],
                    NAMESPACE: tokens[IDENTIFIER][NAMESPACE],
                    NAME: tokens[IDENTIFIER][NAME]
                })

                if not self.complete_origin:
                    return name

                rna_tokens = deepcopy(tokens)
                rna_tokens[FUNCTION] = RNA
                rna_name = self.ensure_node(s, l, rna_tokens)

                self.add_unqualified_edge(rna_name, name, TRANSLATED_TO)
                return name


def canonicalize_fusion_range(tokens, tag):
    if tag in tokens and FusionParser.MISSING not in tokens[tag]:
        return tokens[tag][FusionParser.REF], tokens[tag][FusionParser.LEFT], tokens[tag][FusionParser.RIGHT]
    else:
        return '?',


def canonicalize_node(tokens):
    """Given tokens, returns node name

    :param tokens: tokens ParseObject or dict
    """
    if FUNCTION in tokens and VARIANTS in tokens:
        type_name = tokens[FUNCTION]
        variants = tuple(sorted(canonicalize_variant(token.asDict()) for token in tokens[VARIANTS]))
        return (type_name, tokens[IDENTIFIER][NAMESPACE], tokens[IDENTIFIER][NAME]) + variants

    elif FUNCTION in tokens and MEMBERS in tokens:
        return (tokens[FUNCTION],) + tuple(sorted(canonicalize_node(member) for member in tokens[MEMBERS]))

    elif TRANSFORMATION in tokens and tokens[TRANSFORMATION] == REACTION:
        reactants = tuple(sorted(list2tuple(tokens[REACTANTS].asList())))
        products = tuple(sorted(list2tuple(tokens[PRODUCTS].asList())))
        return (tokens[TRANSFORMATION],) + (reactants,) + (products,)

    elif FUSION in tokens:
        cls = tokens[FUNCTION]
        f = tokens[FUSION]

        range5pt = canonicalize_fusion_range(f, RANGE_5P)
        range3pt = canonicalize_fusion_range(f, RANGE_3P)

        return cls, (f[PARTNER_5P][NAMESPACE], f[PARTNER_5P][NAME]), range5pt, (
            f[PARTNER_3P][NAMESPACE], f[PARTNER_3P][NAME]), range3pt

    elif FUNCTION in tokens and tokens[FUNCTION] in {GENE, RNA, MIRNA, PROTEIN, ABUNDANCE, COMPLEX, PATHOLOGY,
                                                     BIOPROCESS}:
        if IDENTIFIER in tokens:
            return tokens[FUNCTION], tokens[IDENTIFIER][NAMESPACE], tokens[IDENTIFIER][NAME]

    if MODIFIER in tokens and tokens[MODIFIER] in {ACTIVITY, DEGRADATION, TRANSLOCATION, CELL_SECRETION,
                                                   CELL_SURFACE_EXPRESSION}:
        return canonicalize_node(tokens[TARGET])


def canonicalize_modifier(tokens):
    """Get activity, transformation, or transformation information as a dictionary

    :return: a dictionary describing the modifier
    :rtype: dict
    """

    attrs = {}

    if LOCATION in tokens:
        attrs[LOCATION] = tokens[LOCATION].asDict()

    if MODIFIER not in tokens:
        return attrs

    if LOCATION in tokens[TARGET]:
        attrs[LOCATION] = tokens[TARGET][LOCATION].asDict()

    if tokens[MODIFIER] == DEGRADATION:
        attrs[MODIFIER] = DEGRADATION

    elif tokens[MODIFIER] == ACTIVITY and EFFECT not in tokens:
        attrs[MODIFIER] = tokens[MODIFIER]
        attrs[EFFECT] = {}

    elif tokens[MODIFIER] == ACTIVITY and EFFECT in tokens:
        attrs[MODIFIER] = tokens[MODIFIER]
        # TODO reinvestigate this
        if hasattr(tokens[EFFECT], 'asDict'):
            attrs[EFFECT] = tokens[EFFECT].asDict()
        else:
            attrs[EFFECT] = dict(tokens[EFFECT])
            # raise ValueError("Shouldn't be handling dicts this way")

    elif tokens[MODIFIER] == TRANSLOCATION:
        attrs[MODIFIER] = tokens[MODIFIER]
        attrs[EFFECT] = tokens[EFFECT].asDict()

    elif tokens[MODIFIER] == CELL_SECRETION:
        attrs[MODIFIER] = TRANSLOCATION
        attrs[EFFECT] = {
            FROM_LOC: {NAMESPACE: GOCC_KEYWORD, NAME: 'intracellular'},
            TO_LOC: {NAMESPACE: GOCC_KEYWORD, NAME: 'extracellular space'}
        }

    elif tokens[MODIFIER] == CELL_SURFACE_EXPRESSION:
        attrs[MODIFIER] = TRANSLOCATION
        attrs[EFFECT] = {
            FROM_LOC: {NAMESPACE: GOCC_KEYWORD, NAME: 'intracellular'},
            TO_LOC: {NAMESPACE: GOCC_KEYWORD, NAME: 'cell surface'}
        }

    return attrs
