# -*- coding: utf-8 -*-

import itertools as itt
import logging
from copy import deepcopy

import networkx as nx
from pyparsing import Suppress, delimitedList, oneOf, Optional, Group, replaceWith, pyparsing_common, MatchFirst

from . import language
from .baseparser import BaseParser, WCW, nest, one_of_tags, triple
from .parse_abundance_modifier import VariantParser, PsubParser, GsubParser, FragmentParser, FusionParser, \
    LocationParser, TruncParser
from .parse_control import ControlParser
from .parse_exceptions import NestedRelationNotSupportedException, IllegalTranslocationException, \
    MissingCitationException, IllegalFunctionSemantic, MissingSupportingTextException
from .parse_identifier import IdentifierParser
from .parse_pmod import PmodParser
from .utils import handle_debug, list2tuple, cartesian_dictionary

log = logging.getLogger('pybel')

TWO_WAY_RELATIONS = {'negativeCorrelation', 'positiveCorrelation', 'association', 'orthologous', 'analogousTo'}


class BelParser(BaseParser):
    def __init__(self, graph=None, valid_namespaces=None, namespace_mapping=None, valid_annotations=None,
                 lenient=False, complete_origin=False):
        """Build a parser backed by a given dictionary of namespaces

        :param graph: the graph to put the network in. Constructs new nx.MultiDiGrap if None
        :type graph: nx.MultiDiGraph
        :param valid_namespaces: A dictionary of {namespace: set of members}
        :type valid_namespaces: dict
        :param valid_annotations: a dict of {annotation: set of values}
        :type valid_annotations: dict
        :param namespace_mapping: a dict of {name: {value: (other_namepace, other_name)}}
        :type namespace_mapping: dict
        :param lenient: if true, turn off naked namespace failures
        :type lenient: bool
        """

        self.graph = graph if graph is not None else nx.MultiDiGraph()
        self.lenient = lenient
        self.complete_origin = complete_origin
        self.control_parser = ControlParser(valid_annotations=valid_annotations)
        self.identifier_parser = IdentifierParser(valid_namespaces=valid_namespaces,
                                                  mapping=namespace_mapping,
                                                  lenient=self.lenient)

        identifier = Group(self.identifier_parser.get_language())('identifier')

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

        #: 2.2.X Deprecated substitution function from BEL 1.0
        self.psub = PsubParser().get_language()
        self.gsub = GsubParser().get_language()
        self.trunc = TruncParser().get_language()

        # 2.6 Other Functions

        #: 2.6.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_fusion_fus
        self.fusion = FusionParser(self.identifier_parser).get_language()

        # 2.1 Abundance Functions

        #: 2.1.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcomplexA
        general_abundance_tags = one_of_tags(['a', 'abundance'], 'Abundance', 'function')
        self.general_abundance = general_abundance_tags + nest(identifier + opt_location)

        #: 2.1.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XgeneA
        gene_tag = one_of_tags(['g', 'geneAbundance'], 'Gene', 'function')
        self.gene_simple = nest(identifier + opt_location)

        self.gene_modified = nest(identifier + WCW + delimitedList(Group(self.variant | self.gsub))('variants') +
                                  opt_location)

        self.gene_fusion = nest(Group(self.fusion)('fusion') + opt_location)

        fusion_tag = oneOf(['fus', 'fusion']).setParseAction(replaceWith('Fusion'))

        gene_break_start = pyparsing_common.integer()
        gene_break_start.setParseAction(lambda s, l, t: [['c', '?', int(t[0])]])

        gene_break_end = pyparsing_common.integer()
        gene_break_end.setParseAction(lambda s, l, t: [['c', int(t[0]), '?']])

        self.gene_fusion_legacy = nest(Group(identifier('partner_5p') + WCW + fusion_tag + nest(
            identifier('partner_3p') + Optional(
                WCW + gene_break_start('range_5p') + WCW + gene_break_end('range_3p'))))('fusion'))

        self.gene_fusion_legacy.setParseAction(self.handle_fusion_legacy)

        self.gene = gene_tag + MatchFirst(
            [self.gene_fusion, self.gene_fusion_legacy, self.gene_modified, self.gene_simple])

        # 2.1.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XmicroRNAA
        mirna_tag = one_of_tags(['m', 'microRNAAbundance'], 'miRNA', 'function')
        self.mirna_simple = (identifier + opt_location)

        self.mirna_modified = (identifier + WCW + delimitedList(Group(self.variant))('variants') + opt_location)

        self.mirna = mirna_tag + nest(self.mirna_modified | self.mirna_simple)

        # 2.1.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XproteinA
        protein_tag = one_of_tags(['p', 'proteinAbundance'], 'Protein', 'function')

        self.protein_simple = nest(identifier + opt_location)

        self.protein_modified = nest(
            identifier,
            delimitedList(Group(MatchFirst([self.pmod, self.variant, self.fragment, self.psub, self.trunc])))(
                'variants') + opt_location)

        self.protein_fusion = nest(Group(self.fusion)('fusion') + opt_location)

        protein_break_start = pyparsing_common.integer()
        protein_break_start.setParseAction(lambda s, l, t: [['p', '?', int(t[0])]])

        protein_break_end = pyparsing_common.integer()
        protein_break_end.setParseAction(lambda s, l, t: [['p', int(t[0]), '?']])

        self.protein_fusion_legacy = nest(Group(identifier('partner_5p') + WCW + fusion_tag + nest(
            identifier('partner_3p') + Optional(
                WCW + protein_break_start('range_5p') + WCW + protein_break_end('range_3p'))))('fusion'))

        self.protein_fusion_legacy.setParseAction(self.handle_fusion_legacy)

        self.protein = protein_tag + MatchFirst(
            [self.protein_fusion, self.protein_fusion_legacy, self.protein_modified, self.protein_simple])

        # 2.1.7 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XrnaA
        rna_tag = one_of_tags(['r', 'rnaAbundance'], 'RNA', 'function')
        self.rna_simple = nest(identifier + opt_location)

        self.rna_modified = nest(identifier, delimitedList(Group(self.variant))('variants') + opt_location)

        self.rna_fusion = nest(Group(self.fusion)('fusion') + opt_location)

        rna_break_start = pyparsing_common.integer()
        rna_break_start.setParseAction(lambda s, l, t: [['r', '?', int(t[0])]])

        rna_break_end = pyparsing_common.integer()
        rna_break_end.setParseAction(lambda s, l, t: [['r', int(t[0]), '?']])

        self.rna_fusion_legacy = nest(Group(identifier('partner_5p') + WCW + fusion_tag + nest(
            identifier('partner_3p') + Optional(
                WCW + rna_break_start('range_5p') + WCW + rna_break_end('range_3p'))))('fusion'))

        self.rna_fusion_legacy.setParseAction(self.handle_fusion_legacy)

        self.rna = rna_tag + MatchFirst([self.rna_fusion, self.rna_fusion_legacy, self.rna_modified, self.rna_simple])

        self.single_abundance = MatchFirst([self.general_abundance, self.gene, self.mirna, self.protein, self.rna])

        # 2.1.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcomplexA
        complex_tag = one_of_tags(['complex', 'complexAbundance'], 'Complex', 'function')
        self.complex_singleton = complex_tag + nest(identifier + opt_location)

        self.complex_list = complex_tag + nest(
            delimitedList(Group(self.single_abundance | self.complex_singleton))('members') + opt_location)

        self.complex_abundances = self.complex_list | self.complex_singleton

        # Definition of all simple abundances that can be used in a composite abundance
        self.simple_abundance = self.complex_abundances | self.single_abundance
        self.simple_abundance.setParseAction(self.check_function_semantics)

        # 2.1.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcompositeA
        composite_abundance_tag = one_of_tags(['composite', 'compositeAbundance'], 'Composite', 'function')
        self.composite_abundance = composite_abundance_tag + nest(
            delimitedList(Group(self.simple_abundance))('members') + opt_location)

        self.abundance = self.simple_abundance | self.composite_abundance

        # 2.4 Process Modifier Function

        # 2.4.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XmolecularA

        molecular_activity_tag = Suppress(oneOf(['ma', 'molecularActivity']))

        self.molecular_activities_default_ns = oneOf(language.activities)
        self.molecular_activities_default_ns.setParseAction(lambda s, l, t: [language.activity_labels[t[0]]])

        # backwards compatibility with BEL v1.0
        molecular_activity_default = nest(self.molecular_activities_default_ns('MolecularActivity'))
        molecular_activity_custom = nest(identifier('MolecularActivity'))

        self.molecular_activity = molecular_activity_tag + (molecular_activity_default | molecular_activity_custom)

        # 2.3 Process Functions

        # 2.3.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_biologicalprocess_bp
        biological_process_tag = one_of_tags(['bp', 'biologicalProcess'], 'BiologicalProcess', 'function')
        self.biological_process = biological_process_tag + nest(identifier)

        # 2.3.2
        pathology_tag = one_of_tags(['path', 'pathology'], 'Pathology', 'function')
        self.pathology = pathology_tag + nest(identifier)

        self.bp_path = self.biological_process | self.pathology
        self.bp_path.setParseAction(self.check_function_semantics)

        # 2.3.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xactivity
        activity_tag = one_of_tags(['act', 'activity'], 'Activity', 'modifier')

        self.activity_standard = activity_tag + nest(
            Group(self.abundance)('target') + Optional(WCW + Group(self.molecular_activity)('effect')))

        activity_legacy_tags = oneOf(language.activities)('modifier')
        self.activity_legacy = activity_legacy_tags + nest(Group(self.abundance)('target'))

        def handle_activity_legacy(s, l, tokens):
            legacy_cls = language.activity_labels[tokens['modifier']]
            tokens['modifier'] = 'Activity'
            tokens['effect'] = {
                'MolecularActivity': legacy_cls
            }
            return tokens

        self.activity_legacy.setParseAction(handle_activity_legacy)
        self.activity_legacy.addParseAction(
            handle_debug('PyBEL001 legacy activity statement. Use activity() instead. {s}'))

        self.activity = self.activity_standard | self.activity_legacy

        self.process = self.bp_path | self.activity

        # 2.5 Transformation Functions

        # 2.5.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_translocations

        from_loc = Suppress('fromLoc') + nest(identifier('fromLoc'))
        to_loc = Suppress('toLoc') + nest(identifier('toLoc'))

        cell_secretion_tag = one_of_tags(['sec', 'cellSecretion'], 'CellSecretion', 'modifier')
        self.cell_secretion = cell_secretion_tag + nest(Group(self.simple_abundance)('target'))

        cell_surface_expression_tag = one_of_tags(['surf', 'cellSurfaceExpression'], 'CellSurfaceExpression',
                                                  'modifier')
        self.cell_surface_expression = cell_surface_expression_tag + nest(Group(self.simple_abundance)('target'))

        translocation_tag = one_of_tags(['translocation', 'tloc'], 'Translocation', 'modifier')

        self.translocation_standard = nest(
            Group(self.simple_abundance)('target') + WCW + Group(from_loc + WCW + to_loc)('effect'))

        self.translocation_legacy = nest(
            Group(self.simple_abundance)('target') + WCW + Group(identifier('fromLoc') + WCW + identifier('toLoc'))(
                'effect'))
        self.translocation_legacy.addParseAction(
            handle_debug('PyBEL005 legacy translocation statement. use fromLoc() and toLoc(). {s}'))

        self.translocation_illegal = nest(self.simple_abundance)

        def handle_translocation_illegal(s, l, t):
            raise IllegalTranslocationException('Unqualified translocation {} {} {}'.format(s, l, t))

        self.translocation_illegal.setParseAction(handle_translocation_illegal)

        self.translocation = translocation_tag + MatchFirst(
            [self.translocation_illegal, self.translocation_standard, self.translocation_legacy])

        # 2.5.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_degradation_deg

        degradation_tags = one_of_tags(['deg', 'degradation'], 'Degradation', 'modifier')
        self.degradation = degradation_tags + nest(Group(self.simple_abundance)('target'))

        # 2.5.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_reaction_rxn
        self.reactants = Suppress('reactants') + nest(delimitedList(Group(self.simple_abundance)))
        self.products = Suppress('products') + nest(delimitedList(Group(self.simple_abundance)))

        reaction_tags = one_of_tags(['reaction', 'rxn'], 'Reaction', 'transformation')
        self.reaction = reaction_tags + nest(Group(self.reactants)('reactants'), Group(self.products)('products'))

        self.transformation = MatchFirst(
            [self.cell_secretion, self.cell_surface_expression, self.translocation, self.degradation, self.reaction])

        # 3 BEL Relationships

        self.bel_term = MatchFirst([self.transformation, self.process, self.abundance]).streamline()

        # BEL Term to BEL Term Relationships

        # 3.1.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xincreases
        increases_tag = oneOf(['->', '→', 'increases']).setParseAction(replaceWith('increases'))

        # 3.1.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XdIncreases
        directly_increases_tag = oneOf(['=>', '⇒', 'directlyIncreases']).setParseAction(
            replaceWith('directlyIncreases'))

        # 3.1.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xdecreases
        decreases_tag = oneOf(['-|', 'decreases']).setParseAction(replaceWith('decreases'))

        # 3.1.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XdDecreases
        directly_decreases_tag = oneOf(['=|', 'directlyDecreases']).setParseAction(
            replaceWith('directlyDecreases'))

        # 3.5.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_analogous
        analogous_tag = oneOf(['analogousTo'])

        # 3.1.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xcnc
        causes_no_change_tag = oneOf(['cnc', 'causesNoChange']).setParseAction(replaceWith('causesNoChange'))

        # 3.1.7 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_regulates_reg
        regulates_tag = oneOf(['reg', 'regulates']).setParseAction(replaceWith('regulates'))

        # 3.2.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XnegCor
        negative_correlation_tag = oneOf(['neg', 'negativeCorrelation']).setParseAction(
            replaceWith('negativeCorrelation'))

        # 3.2.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XposCor
        positive_correlation_tag = oneOf(['pos', 'positiveCorrelation']).setParseAction(
            replaceWith('positiveCorrelation'))

        # 3.2.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xassociation
        association_tag = oneOf(['--', 'association']).setParseAction(replaceWith('association'))

        # 3.3.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_orthologous
        orthologous_tag = oneOf(['orthologous'])

        # 3.4.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_isa
        is_a_tag = oneOf(['isA'])

        self.bel_to_bel_relations = [
            increases_tag,
            decreases_tag,
            directly_increases_tag,
            directly_decreases_tag,
            analogous_tag,
            causes_no_change_tag,
            regulates_tag,
            negative_correlation_tag,
            positive_correlation_tag,
            association_tag,
            orthologous_tag,
            is_a_tag
        ]
        self.bel_to_bel = triple(self.bel_term, MatchFirst(self.bel_to_bel_relations), self.bel_term)

        # Mixed Relationships

        # 3.1.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_ratelimitingstepof
        rate_limit_tag = oneOf(['rateLimitingStepOf'])
        self.rate_limit = triple(MatchFirst([self.biological_process, self.activity, self.transformation]),
                                 rate_limit_tag, self.biological_process)

        # 3.4.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_subprocessof
        subprocess_of_tag = oneOf(['subProcessOf'])
        self.subprocess_of = triple(MatchFirst([self.process, self.activity, self.transformation]), subprocess_of_tag,
                                    self.process)

        # 3.3.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_transcribedto
        transcribed_tag = oneOf([':>', 'transcribedTo']).setParseAction(replaceWith('transcribedTo'))
        self.transcribed = triple(self.gene, transcribed_tag, self.rna)

        # 3.3.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_translatedto
        translated_tag = oneOf(['>>', 'translatedTo']).setParseAction(replaceWith('translatedTo'))
        self.translated = triple(self.rna, translated_tag, self.protein)

        # 3.4.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_hasmember
        has_member_tag = oneOf(['hasMember'])
        self.has_member = triple(self.abundance, has_member_tag, self.abundance)

        # 3.4.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_hasmembers
        self.abundance_list = Suppress('list') + nest(delimitedList(Group(self.abundance)))

        has_members_tag = oneOf(['hasMembers'])
        self.has_members = triple(self.abundance, has_members_tag, self.abundance_list)
        self.has_members.setParseAction(self.handle_has_members)

        # 3.4.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_hascomponent
        has_component_tag = oneOf(['hasComponent'])
        self.has_component = triple(self.complex_abundances | self.composite_abundance, has_component_tag,
                                    self.abundance)

        # 3.5.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_biomarkerfor
        biomarker_tag = oneOf(['biomarkerFor'])

        # 3.5.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_prognosticbiomarkerfor
        prognostic_biomarker_tag = oneOf(['prognosticBiomarkerFor'])

        biomarker_tags = biomarker_tag | prognostic_biomarker_tag

        self.biomarker = triple(self.bel_term, biomarker_tags, self.process)

        self.relation = MatchFirst([
            self.bel_to_bel,
            self.transcribed,
            self.translated,
            self.has_member,
            self.has_component,
            self.subprocess_of,
            self.rate_limit,
            self.biomarker,
        ])

        self.relation.setParseAction(self.handle_relation)

        # 3.1 Causal Relationships - nested. Explicitly not supported because of ambiguity

        causal_relation_tags = MatchFirst([increases_tag, decreases_tag,
                                           directly_decreases_tag, directly_increases_tag])

        self.nested_causal_relationship = triple(self.bel_term, causal_relation_tags,
                                                 nest(triple(self.bel_term, causal_relation_tags, self.bel_term)))

        self.nested_causal_relationship.setParseAction(self.handle_nested_relation)

        # has_members is handled differently from all other relations becuase it gets distrinbuted
        self.relation = MatchFirst([self.has_members, self.nested_causal_relationship, self.relation])

        self.statement = self.relation | self.bel_term.setParseAction(self.handle_term)
        self.language = self.control_parser.get_language() | self.statement

    def get_language(self):
        """Get language defined by this parser"""
        return self.language

    def get_annotations(self):
        """Get current annotations in this parser"""
        return self.control_parser.get_annotations()

    def clear(self):
        """Clears the data stored in the parser"""
        self.graph.clear()
        self.control_parser.clear()

    def handle_nested_relation(self, s, l, tokens):
        if not self.lenient:
            raise NestedRelationNotSupportedException('Nesting unsupported: {}'.format(s))

        self.handle_relation(s, l, dict(subject=tokens['subject'],
                                        relation=tokens['relation'],
                                        object=tokens['object']['subject']))

        self.handle_relation(s, l, dict(subject=tokens['object']['subject'],
                                        relation=tokens['object']['relation'],
                                        object=tokens['object']['object']))
        return tokens

    def check_function_semantics(self, s, l, tokens):
        if self.identifier_parser.namespace_dict is None or 'identifier' not in tokens:
            return tokens

        namespace, name = tokens['identifier']['namespace'], tokens['identifier']['name']

        valid_function_codes = set(itt.chain.from_iterable(
            language.value_map[v] for v in self.identifier_parser.namespace_dict[namespace][name]))

        if tokens['function'] not in valid_function_codes:
            valid_list = ','.join(self.identifier_parser.namespace_dict[namespace][name])
            fmt = "Invalid function ({}) for identifier {}:{}. Valid are: [{}]"
            raise IllegalFunctionSemantic(fmt.format(tokens['function'], namespace, name, valid_list))
        return tokens

    def handle_fusion_legacy(self, s, l, tokens):
        if 'range_5p' in tokens['fusion']:
            return tokens

        tokens['fusion']['range_5p'] = '?'
        tokens['fusion']['range_3p'] = '?'
        return tokens

    def handle_term(self, s, l, tokens):
        self.ensure_node(s, l, tokens)
        return tokens

    def check_required_annotations(self, s):
        if not self.control_parser.citation:
            raise MissingCitationException('unable to add relation {}'.format(s))

        if 'SupportingText' not in self.control_parser.annotations:
            raise MissingSupportingTextException('unable to add relation {}'.format(s))

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
            self.graph.add_edge(parent, child, relation='hasMember')
        return tokens

    def handle_relation(self, s, l, tokens):
        self.check_required_annotations(s)

        sub = self.ensure_node(s, l, tokens['subject'])
        obj = self.ensure_node(s, l, tokens['object'])

        attrs, list_attrs = self.build_attrs()

        attrs['relation'] = tokens['relation']

        sub_mod = canonicalize_modifier(tokens['subject'])
        if sub_mod:
            attrs['subject'] = sub_mod

        obj_mod = canonicalize_modifier(tokens['object'])
        if obj_mod:
            attrs['object'] = obj_mod

        for single_annotation in cartesian_dictionary(list_attrs):
            self.graph.add_edge(sub, obj, attr_dict=attrs, **single_annotation)
            if tokens['relation'] in TWO_WAY_RELATIONS:
                self.add_reverse_edge(sub, obj, attrs, **single_annotation)

        return tokens

    def add_reverse_edge(self, sub, obj, attrs, **single_annotation):
        attrs_subject, attrs_object = attrs.get('subject'), attrs.get('object')
        if attrs_subject:
            del attrs['subject']
            attrs['object'] = attrs_subject
        if attrs_object:
            del attrs['object']
            attrs['subject'] = attrs_object

        self.graph.add_edge(obj, sub, attr_dict=attrs, **single_annotation)

    def add_unqualified_edge(self, u, v, relation):
        """Adds unique edge that has no annotations

        :param u: source node
        :param v: target node
        :param relation: relationship label
        """
        key = language.unqualified_edge_code[relation]
        if not self.graph.has_edge(u, v, key):
            self.graph.add_edge(u, v, key=key, relation=relation)

    def ensure_node(self, s, l, tokens):
        """Turns parsed tokens into canonical node name and makes sure its in the graph

        :return: the canonical name of the node
        :rtype: str
        """

        if 'modifier' in tokens:
            return self.ensure_node(s, l, tokens['target'])

        name = canonicalize_node(tokens)

        if name in self.graph:
            return name

        if 'transformation' in tokens:
            if name not in self.graph:
                self.graph.add_node(name, type=tokens['transformation'])

            for reactant_tokens in tokens['reactants']:
                reactant_name = self.ensure_node(s, l, reactant_tokens)
                self.add_unqualified_edge(name, reactant_name, relation='hasReactant')

            for product_tokens in tokens['products']:
                product_name = self.ensure_node(s, l, product_tokens)
                self.add_unqualified_edge(name, product_name, relation='hasProduct')

            return name

        elif 'function' in tokens and 'members' in tokens:
            if name not in self.graph:
                self.graph.add_node(name, type=tokens['function'])

            for token in tokens['members']:
                member_name = self.ensure_node(s, l, token)
                self.add_unqualified_edge(name, member_name, relation='hasComponent')
            return name

        elif 'function' in tokens and 'variants' in tokens:
            cls, ns, val = name[:3]
            variants = tuple(name[3:])
            if name not in self.graph:
                self.graph.add_node(name,
                                    type=cls,
                                    namespace=ns,
                                    name=val,
                                    variants=variants)

            c = {
                'function': tokens['function'],
                'identifier': tokens['identifier']
            }

            parent = self.ensure_node(s, l, c)
            self.add_unqualified_edge(parent, name, relation='hasVariant')
            return name

        elif 'function' in tokens and 'fusion' in tokens:
            if name not in self.graph:
                f = tokens['fusion']
                cls = '{}Fusion'.format(tokens['function'])
                d = {
                    'partner_5p': dict(namespace=f['partner_5p']['namespace'], name=f['partner_5p']['name']),
                    'range_5p': tuple(f['range_5p']),
                    'partner_3p': dict(namespace=f['partner_3p']['namespace'], name=f['partner_3p']['name']),
                    'range_3p': tuple(f['range_3p'])
                }
                self.graph.add_node(name, type=cls, **d)
            return name

        elif 'function' in tokens and 'identifier' in tokens:
            if tokens['function'] in ('Gene', 'miRNA', 'Pathology', 'BiologicalProcess', 'Abundance', 'Complex'):
                if name not in self.graph:
                    self.graph.add_node(name,
                                        type=tokens['function'],
                                        namespace=tokens['identifier']['namespace'],
                                        name=tokens['identifier']['name'])
                return name

            elif tokens['function'] == 'RNA':
                if name not in self.graph:
                    self.graph.add_node(name,
                                        type=tokens['function'],
                                        namespace=tokens['identifier']['namespace'],
                                        name=tokens['identifier']['name'])

                if not self.complete_origin:
                    return name

                gene_tokens = deepcopy(tokens)
                gene_tokens['function'] = 'Gene'
                gene_name = self.ensure_node(s, l, gene_tokens)

                self.add_unqualified_edge(gene_name, name, relation='transcribedTo')
                return name

            elif tokens['function'] == 'Protein':
                if name not in self.graph:
                    self.graph.add_node(name,
                                        type=tokens['function'],
                                        namespace=tokens['identifier']['namespace'],
                                        name=tokens['identifier']['name'])

                if not self.complete_origin:
                    return name

                rna_tokens = deepcopy(tokens)
                rna_tokens['function'] = 'RNA'
                rna_name = self.ensure_node(s, l, rna_tokens)

                self.add_unqualified_edge(rna_name, name, relation='translatedTo')
                return name


def canonicalize_node(tokens):
    """Given tokens, returns node name

    :param tokens: tokens ParseObject or dict
    """
    if 'function' in tokens and 'variants' in tokens:
        type_name = '{}Variant'.format(tokens['function'])
        name = type_name, tokens['identifier']['namespace'], tokens['identifier']['name']
        variants = list2tuple(sorted(tokens['variants'].asList()))
        return name + variants

    elif 'function' in tokens and 'members' in tokens:
        return (tokens['function'],) + tuple(sorted(canonicalize_node(member) for member in tokens['members']))

    elif 'transformation' in tokens and tokens['transformation'] == 'Reaction':
        reactants = tuple(sorted(list2tuple(tokens['reactants'].asList())))
        products = tuple(sorted(list2tuple(tokens['products'].asList())))
        return (tokens['transformation'],) + (reactants,) + (products,)

    elif 'function' in tokens and tokens['function'] in ('Gene', 'RNA', 'Protein') and 'fusion' in tokens:
        f = tokens['fusion']
        cls = '{}Fusion'.format(tokens['function'])
        return cls, (f['partner_5p']['namespace'], f['partner_5p']['name']), tuple(f['range_5p']), (
            f['partner_3p']['namespace'], f['partner_3p']['name']), tuple(f['range_3p'])

    elif 'function' in tokens and tokens['function'] in (
            'Gene', 'RNA', 'miRNA', 'Protein', 'Abundance', 'Complex', 'Pathology', 'BiologicalProcess'):
        if 'identifier' in tokens:
            return tokens['function'], tokens['identifier']['namespace'], tokens['identifier']['name']

    if 'modifier' in tokens and tokens['modifier'] in (
            'Activity', 'Degradation', 'Translocation', 'CellSecretion', 'CellSurfaceExpression'):
        return canonicalize_node(tokens['target'])


def canonicalize_modifier(tokens):
    """Get activity, transformation, or transformation information as a dictionary

    :return: a dictionary describing the modifier
    :rtype: dict
    """

    attrs = {}

    if 'location' in tokens:
        attrs['location'] = tokens['location'].asDict()

    if 'modifier' not in tokens:
        return attrs

    if 'location' in tokens['target']:
        attrs['location'] = tokens['target']['location'].asDict()

    if tokens['modifier'] == 'Degradation':
        attrs['modifier'] = 'Degradation'

    elif tokens['modifier'] == 'Activity' and 'effect' not in tokens:
        attrs['modifier'] = tokens['modifier']
        attrs['effect'] = {}

    elif tokens['modifier'] == 'Activity' and 'effect' in tokens:
        attrs['modifier'] = tokens['modifier']
        attrs['effect'] = tokens['effect'].asDict() if hasattr(tokens['effect'], 'asDict') else dict(
            tokens['effect'])

    elif tokens['modifier'] == 'Translocation':
        attrs['modifier'] = tokens['modifier']
        attrs['effect'] = tokens['effect'].asDict()

    elif tokens['modifier'] == 'CellSecretion':
        attrs['modifier'] = 'Translocation'
        attrs['effect'] = {
            'fromLoc': dict(namespace='GOCC', name='intracellular'),
            'toLoc': dict(namespace='GOCC', name='extracellular space')
        }

    elif tokens['modifier'] == 'CellSurfaceExpression':
        attrs['modifier'] = 'Translocation'
        attrs['effect'] = {
            'fromLoc': dict(namespace='GOCC', name='intracellular'),
            'toLoc': dict(namespace='GOCC', name='cell surface')
        }

    return attrs
