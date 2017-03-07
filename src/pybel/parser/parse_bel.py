# -*- coding: utf-8 -*-

"""
Relation Parser
~~~~~~~~~~~~~~~
This module handles parsing BEL relations and validation of semantics.
"""

import itertools as itt
import logging
from copy import deepcopy

from pyparsing import Suppress, delimitedList, oneOf, Optional, Group, replaceWith, MatchFirst

from .baseparser import BaseParser, WCW, nest, one_of_tags, triple
from .language import belns_encodings, activity_labels, activities
from .modifiers import FusionParser, VariantParser, canonicalize_variant, FragmentParser, GmodParser, GsubParser, \
    LocationParser, PmodParser, PsubParser, TruncParser
from .modifiers.fusion import build_legacy_fusion
from .parse_control import ControlParser
from .parse_exceptions import NestedRelationWarning, MalformedTranslocationWarning, \
    MissingCitationException, InvalidFunctionSemantic, MissingSupportWarning
from .parse_identifier import IdentifierParser
from .utils import cartesian_dictionary
from .. import constants as pbc
from ..constants import *
from ..utils import list2tuple

log = logging.getLogger(__name__)

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
    def __init__(self, graph, namespace_dicts=None, namespace_mappings=None, annotation_dicts=None,
                 namespace_expressions=None, annotation_expressions=None, complete_origin=False,
                 allow_naked_names=False, allow_nested=False, citation_clearing=True, autostreamline=False):
        """Build a parser backed by a given dictionary of namespaces

        :param graph: The BEL Graph to use to store the network
        :type graph: BELGraph
        :param namespace_dicts: A dictionary of {namespace: set of members}.
                                    Delegated to :class:`pybel.parser.parse_identifier.IdentifierParser`
        :type namespace_dicts: dict
        :param annotation_dicts: A dictionary of {annotation: set of values}.
                                    Delegated to :class:`pybel.parser.ControlParser`
        :type annotation_dicts: dict
        :param namespace_expressions: A dictionary of {namespace: regular expression strings}.
                                        Delegated to :class:`pybel.parser.parse_identifier.IdentifierParser`
        :type namespace_expressions: dict
        :param annotation_expressions: A dictionary of {annotation: regular expression strings}.
                                        Delegated to :class:`pybel.parser.ControlParser`
        :type annotation_expressions: dict
        :param namespace_mappings: A dictionary of {name: {value: (other_namespace, other_name)}}.
                                    Delegated to :class:`pybel.parser.parse_identifier.IdentifierParser`
        :type namespace_mappings: dict
        :param complete_origin: If true, infer the RNA and Gene origins of unmodified proteins
        :type complete_origin: bool
        :param allow_naked_names: If true, turn off naked namespace failures.
                                    Delegated to :class:`pybel.parser.parse_identifier.IdentifierParser`
        :type allow_naked_names: bool
        :param allow_nested: If true, turn off nested statement failures.
                                    Delegated to :class:`pybel.parser.parse_identifier.IdentifierParser`
        :type allow_nested: bool
        :param citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
                                    Delegated to :class:`pybel.parser.ControlParser`
        :type citation_clearing: bool
        """

        self.graph = graph
        self.allow_nested = allow_nested
        self.complete_origin = complete_origin

        self.control_parser = ControlParser(
            annotation_dicts=annotation_dicts,
            annotation_expressions=annotation_expressions,
            citation_clearing=citation_clearing
        )

        self.identifier_parser = IdentifierParser(
            namespace_dicts=namespace_dicts,
            namespace_expressions=namespace_expressions,
            namespace_mappings=namespace_mappings,
            allow_naked_names=allow_naked_names
        )

        # TODO replace with:
        # identifier = self.identifier_parser.as_group()
        identifier = Group(self.identifier_parser.language)(IDENTIFIER)

        # 2.2 Abundance Modifier Functions

        #: 2.2.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_protein_modifications
        self.pmod = PmodParser(self.identifier_parser).language

        #: 2.2.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_variant_var
        self.variant = VariantParser().language

        #: 2.2.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_proteolytic_fragments
        self.fragment = FragmentParser().language

        #: 2.2.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_cellular_location
        self.location = LocationParser(self.identifier_parser).language
        opt_location = Optional(WCW + self.location)

        #: 2.2.X DEPRECATED
        #: http://openbel.org/language/web/version_1.0/bel_specification_version_1.0.html#_amino_acid_substitutions
        self.psub = PsubParser().language

        #: 2.2.X DEPRECATED
        #: http://openbel.org/language/web/version_1.0/bel_specification_version_1.0.html#_sequence_variations
        self.gsub = GsubParser().language

        #: DEPRECATED
        #: http://openbel.org/language/web/version_1.0/bel_specification_version_1.0.html#_truncated_proteins
        self.trunc = TruncParser().language

        #: PyBEL BEL Specification variant
        self.gmod = GmodParser().language

        # 2.6 Other Functions

        #: 2.6.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_fusion_fus
        self.fusion = FusionParser(self.identifier_parser).language

        # 2.1 Abundance Functions

        #: 2.1.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcomplexA
        self.general_abundance = general_abundance_tags + nest(identifier + opt_location)

        self.gene_modified = identifier + Optional(
            WCW + delimitedList(Group(self.variant | self.gsub | self.gmod))(VARIANTS))

        self.gene_fusion = Group(self.fusion)(FUSION)
        self.gene_fusion_legacy = Group(build_legacy_fusion(identifier, 'c'))(FUSION)

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
        self.protein_fusion_legacy = Group(build_legacy_fusion(identifier, 'p'))(FUSION)

        self.protein = protein_tag + nest(MatchFirst([
            self.protein_fusion,
            self.protein_fusion_legacy,
            self.protein_modified,
        ]) + opt_location)
        """2.1.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XproteinA"""

        self.rna_modified = identifier + Optional(WCW + delimitedList(Group(self.variant))(VARIANTS))

        self.rna_fusion = Group(self.fusion)(FUSION)
        self.rna_fusion_legacy = Group(build_legacy_fusion(identifier, 'r'))(FUSION)

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

        molecular_activity_default = oneOf(activity_labels.keys()).setParseAction(handle_molecular_activity_default)

        self.molecular_activity = molecular_activity_tags + nest(
            molecular_activity_default | self.identifier_parser.language)
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

        activity_legacy_tags = oneOf(activities)(MODIFIER)
        self.activity_legacy = activity_legacy_tags + nest(Group(self.abundance)(TARGET))
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

        self.translocation_legacy.addParseAction(handle_legacy_tloc)
        self.translocation_illegal = nest(self.simple_abundance)
        self.translocation_illegal.setParseAction(handle_translocation_illegal)

        self.translocation = translocation_tag + MatchFirst([
            self.translocation_illegal,
            self.translocation_standard,
            self.translocation_legacy
        ])
        """2.5.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_translocations"""

        #: 2.5.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_degradation_deg
        self.degradation = degradation_tags + nest(Group(self.simple_abundance)(TARGET))

        #: 2.5.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_reaction_rxn
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
        self.language = self.control_parser.language | self.statement
        self.language.setName('BEL')

        BaseParser.__init__(self, self.language, streamline=autostreamline)

    @property
    def namespace_dict(self):
        return self.identifier_parser.namespace_dict

    @property
    def namespace_re(self):
        return self.identifier_parser.namespace_regex_compiled

    @property
    def annotation_re(self):
        return self.control_parser.annotations_re

    @property
    def allow_naked_names(self):
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
        if self.namespace_dict is None or IDENTIFIER not in tokens:
            return tokens

        namespace, name = tokens[IDENTIFIER][NAMESPACE], tokens[IDENTIFIER][NAME]

        if namespace in self.namespace_re:
            return tokens

        if self.allow_naked_names and tokens[IDENTIFIER][NAMESPACE] == DIRTY:  # Don't check dirty names in lenient mode
            return tokens

        valid_functions = set(itt.chain.from_iterable(belns_encodings[k] for k in self.namespace_dict[namespace][name]))

        if tokens[FUNCTION] not in valid_functions:
            raise InvalidFunctionSemantic(tokens[FUNCTION], namespace, name, valid_functions)

        return tokens

    def handle_term(self, s, l, tokens):
        self.ensure_node(tokens)
        return tokens

    def check_required_annotations(self, s):
        """Checks that the control parser has a citation and evidence before adding an edge"""
        if not self.control_parser.citation:
            raise MissingCitationException(s)

        if not self.control_parser.evidence:
            raise MissingSupportWarning(s)

    def handle_has_members(self, s, l, tokens):
        parent = self.ensure_node(tokens[0])
        for child_tokens in tokens[2]:
            child = self.ensure_node(child_tokens)
            self.graph.add_unqualified_edge(parent, child, HAS_MEMBER)

        return tokens

    def _build_attrs(self):
        attrs = {}
        list_attrs = {}

        for annotation_name, annotation_entry in self.control_parser.annotations.copy().items():
            if isinstance(annotation_entry, set):
                list_attrs[annotation_name] = annotation_entry
            else:
                attrs[annotation_name] = annotation_entry

        return attrs, list_attrs

    def handle_relation(self, s, l, tokens):
        self.check_required_annotations(s)

        sub = self.ensure_node(tokens[SUBJECT])
        obj = self.ensure_node(tokens[OBJECT])

        attrs, list_attrs = self._build_attrs()

        q = {
            RELATION: tokens[RELATION],
            EVIDENCE: self.control_parser.evidence,
            CITATION: self.control_parser.citation.copy()
        }

        sub_mod = canonicalize_modifier(tokens[SUBJECT])
        if sub_mod:
            q[SUBJECT] = sub_mod

        obj_mod = canonicalize_modifier(tokens[OBJECT])
        if obj_mod:
            q[OBJECT] = obj_mod

        for single_annotation in cartesian_dictionary(list_attrs):
            annots = attrs.copy()
            annots.update(single_annotation)

            self.graph.add_edge(sub, obj, attr_dict=q, **{ANNOTATIONS: annots})
            if tokens[RELATION] in TWO_WAY_RELATIONS:
                self.add_reverse_edge(sub, obj, attr_dict=q, **{ANNOTATIONS: annots})

        return tokens

    def add_reverse_edge(self, sub, obj, attr_dict, **attr):
        new_attrs = {k: v for k, v in attr_dict.items() if k not in {SUBJECT, OBJECT}}
        attrs_subject, attrs_object = attr_dict.get(SUBJECT), attr_dict.get(OBJECT)
        if attrs_subject:
            new_attrs[OBJECT] = attrs_subject
        if attrs_object:
            new_attrs[SUBJECT] = attrs_object

        self.graph.add_edge(obj, sub, attr_dict=new_attrs, **attr)

    def _ensure_reaction(self, name, tokens):
        self.graph.add_node(name, **{FUNCTION: tokens[FUNCTION]})

        for reactant_tokens in tokens[REACTANTS]:
            reactant_name = self.ensure_node(reactant_tokens)
            self.graph.add_unqualified_edge(name, reactant_name, HAS_REACTANT)

        for product_tokens in tokens[PRODUCTS]:
            product_name = self.ensure_node(product_tokens)
            self.graph.add_unqualified_edge(name, product_name, HAS_PRODUCT)

        return name

    def _ensure_members(self, name, tokens):
        self.graph.add_node(name, **{FUNCTION: tokens[FUNCTION]})

        for token in tokens[MEMBERS]:
            member_name = self.ensure_node(token)
            self.graph.add_unqualified_edge(name, member_name, HAS_COMPONENT)
        return name

    def _ensure_variants(self, name, tokens):
        self.graph.add_node(name, **canonicalize_variant_node_to_dict(tokens))

        c = {
            FUNCTION: tokens[FUNCTION],
            IDENTIFIER: tokens[IDENTIFIER]
        }

        parent = self.ensure_node(c)
        self.graph.add_unqualified_edge(parent, name, HAS_VARIANT)
        return name

    def _ensure_fusion(self, name, tokens):
        self.graph.add_node(name, **canonicalize_fusion_to_dict(tokens))
        return name

    def _ensure_simple_abundance(self, name, tokens):
        self.graph.add_node(name, **canonicalize_simple_to_dict(tokens))
        return name

    def _ensure_rna(self, name, tokens):
        self._ensure_simple_abundance(name, tokens)

        if not self.complete_origin:
            return name

        gene_tokens = deepcopy(tokens)
        gene_tokens[FUNCTION] = GENE
        gene_name = self.ensure_node(gene_tokens)

        self.graph.add_unqualified_edge(gene_name, name, TRANSCRIBED_TO)
        return name

    def _ensure_protein(self, name, tokens):
        self._ensure_simple_abundance(name, tokens)

        if not self.complete_origin:
            return name

        rna_tokens = deepcopy(tokens)
        rna_tokens[FUNCTION] = RNA
        rna_name = self.ensure_node(rna_tokens)

        self.graph.add_unqualified_edge(rna_name, name, TRANSLATED_TO)
        return name

    def ensure_node(self, tokens):
        """Turns parsed tokens into canonical node name and makes sure its in the graph

        :return: the canonical name of the node
        :rtype: str
        """

        if MODIFIER in tokens:
            return self.ensure_node(tokens[TARGET])

        name = canonicalize_node(tokens)

        if name in self.graph:
            return name

        if REACTION == tokens[FUNCTION]:
            return self._ensure_reaction(name, tokens)

        elif MEMBERS in tokens:
            return self._ensure_members(name, tokens)

        elif VARIANTS in tokens:
            return self._ensure_variants(name, tokens)

        elif FUSION in tokens:
            return self._ensure_fusion(name, tokens)

        # You're just a boring abundance
        # elif FUNCTION in tokens and IDENTIFIER in tokens:

        elif tokens[FUNCTION] in {GENE, MIRNA, PATHOLOGY, BIOPROCESS, ABUNDANCE, COMPLEX}:
            return self._ensure_simple_abundance(name, tokens)

        elif tokens[FUNCTION] == RNA:
            return self._ensure_rna(name, tokens)

        # Finally, you're just a boring old protein
        # elif tokens[FUNCTION] == PROTEIN:

        return self._ensure_protein(name, tokens)


# HANDLERS

def handle_molecular_activity_default(s, l, tokens):
    upgraded = activity_labels[tokens[0]]
    log.debug('upgraded legacy activity to %s', upgraded)
    tokens[NAMESPACE] = BEL_DEFAULT_NAMESPACE
    tokens[NAME] = upgraded
    return tokens


def handle_activity_legacy(s, l, tokens):
    legacy_cls = activity_labels[tokens[MODIFIER]]
    tokens[MODIFIER] = ACTIVITY
    tokens[EFFECT] = {
        NAME: legacy_cls,
        NAMESPACE: BEL_DEFAULT_NAMESPACE
    }
    log.debug('upgraded legacy activity to %s', legacy_cls)
    return tokens


def handle_legacy_tloc(s, l, tokens):
    log.debug('Legacy translocation statement: %s', s)
    return tokens


def handle_translocation_illegal(s, l, t):
    raise MalformedTranslocationWarning(s, l, t)


# CANONICALIZATION

def canonicalize_simple_to_dict(tokens):
    return {
        FUNCTION: tokens[FUNCTION],
        NAMESPACE: tokens[IDENTIFIER][NAMESPACE],
        NAME: tokens[IDENTIFIER][NAME]
    }


# TODO figure out how to just get dictionary rather than slicing it up like this
def canonicalize_fusion_range_to_dict(tokens):
    if FusionParser.MISSING in tokens:
        return {
            FusionParser.MISSING: '?'
        }
    else:
        return {
            FusionParser.REFERENCE: tokens[FusionParser.REFERENCE],
            FusionParser.START: tokens[FusionParser.START],
            FusionParser.STOP: tokens[FusionParser.STOP]
        }


def canonicalize_fusion_to_dict(tokens):
    f = tokens[FUSION]
    return {
        FUNCTION: tokens[FUNCTION],
        FUSION: {
            PARTNER_5P: {
                NAMESPACE: f[PARTNER_5P][NAMESPACE],
                NAME: f[PARTNER_5P][NAME]
            },
            RANGE_5P: canonicalize_fusion_range_to_dict(f[RANGE_5P]),
            PARTNER_3P: {
                NAMESPACE: f[PARTNER_3P][NAMESPACE],
                NAME: f[PARTNER_3P][NAME]
            },
            RANGE_3P: canonicalize_fusion_range_to_dict(f[RANGE_3P])
        }
    }


def canonicalize_variant_node_to_dict(tokens):
    attr_data = canonicalize_simple_to_dict(tokens)
    attr_data[VARIANTS] = [variant.asDict() for variant in tokens[VARIANTS]]
    return attr_data


def canonicalize_fusion_range(tokens, tag):
    if tag in tokens and FusionParser.MISSING not in tokens[tag]:
        fusion_range = tokens[tag]
        return fusion_range[FusionParser.REFERENCE], fusion_range[FusionParser.START], fusion_range[FusionParser.STOP]
    else:
        return '?',


def canonicalize_fusion(tokens):
    function = tokens[FUNCTION]
    fusion = tokens[FUSION]

    partner5p = fusion[PARTNER_5P]
    partner3p = fusion[PARTNER_3P]
    range5p = canonicalize_fusion_range(fusion, RANGE_5P)
    range3p = canonicalize_fusion_range(fusion, RANGE_3P)

    return function, (partner5p[NAMESPACE], partner5p[NAME]), range5p, (partner3p[NAMESPACE], partner3p[NAME]), range3p


def canonicalize_reaction(tokens):
    reactants = tuple(sorted(list2tuple(tokens[REACTANTS].asList())))
    products = tuple(sorted(list2tuple(tokens[PRODUCTS].asList())))
    return (tokens[FUNCTION],) + (reactants,) + (products,)


def canonicalize_simple(tokens):
    return tokens[FUNCTION], tokens[IDENTIFIER][NAMESPACE], tokens[IDENTIFIER][NAME]


def canonicalize_variant_node(tokens):
    variants = tuple(sorted(canonicalize_variant(token.asDict()) for token in tokens[VARIANTS]))
    return canonicalize_simple(tokens) + variants


def canonicalize_list_node(tokens):
    return (tokens[FUNCTION],) + tuple(sorted(canonicalize_node(member) for member in tokens[MEMBERS]))


def canonicalize_node(tokens):
    """Given tokens, returns node name

    :param tokens: tokens ParseObject or dict
    """

    if MODIFIER in tokens:
        return canonicalize_node(tokens[TARGET])

    elif REACTION == tokens[FUNCTION]:
        return canonicalize_reaction(tokens)

    elif VARIANTS in tokens:
        return canonicalize_variant_node(tokens)

    elif MEMBERS in tokens:
        return canonicalize_list_node(tokens)

    elif FUSION in tokens:
        return canonicalize_fusion(tokens)

    return canonicalize_simple(tokens)


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
        attrs[MODIFIER] = tokens[MODIFIER]

    elif tokens[MODIFIER] == ACTIVITY:
        attrs[MODIFIER] = tokens[MODIFIER]

        if EFFECT in tokens:
            attrs[EFFECT] = dict(tokens[EFFECT])

    elif tokens[MODIFIER] == TRANSLOCATION:
        attrs[MODIFIER] = tokens[MODIFIER]
        attrs[EFFECT] = tokens[EFFECT].asDict()

    elif tokens[MODIFIER] == CELL_SECRETION:
        attrs[MODIFIER] = TRANSLOCATION
        attrs[EFFECT] = {
            FROM_LOC: {NAMESPACE: GOCC_KEYWORD, NAME: 'intracellular'},
            TO_LOC: {NAMESPACE: GOCC_KEYWORD, NAME: 'extracellular space'}
        }

    # elif tokens[MODIFIER] == CELL_SURFACE_EXPRESSION:
    else:
        attrs[MODIFIER] = TRANSLOCATION
        attrs[EFFECT] = {
            FROM_LOC: {NAMESPACE: GOCC_KEYWORD, NAME: 'intracellular'},
            TO_LOC: {NAMESPACE: GOCC_KEYWORD, NAME: 'cell surface'}
        }

    return attrs
