#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from copy import deepcopy

import networkx as nx
from pyparsing import Suppress, delimitedList, Forward, oneOf, Optional, Group, OneOrMore, replaceWith

from . import language
from .baseparser import BaseParser, W, WCW, nest
from .parse_abundance_modifier import VariantParser, PsubParser, GsubParser, FragmentParser, FusionParser, \
    LocationParser
from .parse_control import ControlParser
from .parse_identifier import IdentifierParser
from .parse_pmod import PmodParser
from .utils import list2tuple

log = logging.getLogger(__name__)


# TODO put inside BelParser class
def command_handler(command, loc=0, ensure_node_handler=None):
    """
    Builds a token handler
    :param command: a string for replacement, or function that takes the old token and transforms it
    :param loc: location of the token to normalize
    :param ensure_node_handler: give the self object from the parser
    :return:
    """

    def handler(s, l, tokens):
        if isinstance(command, str):
            tokens[loc] = command
        elif isinstance(command, dict):
            tokens[loc] = command[tokens[loc]]
        elif command is callable:
            tokens[loc] = command(tokens[loc])

        if ensure_node_handler is not None:
            ensure_node_handler.ensure_node(tokens)
        return tokens

    return handler


def triple(subject, relation, object):
    return Group(subject)('subject') + W + relation('relation') + W + Group(object)('object')


class BelParser(BaseParser):
    """
    Build a parser backed by a given dictionary of namespaces
    """

    def __init__(self, graph=None, namespace_dict=None, namespace_mapping=None, custom_annotations=None):
        """
        :param namespace_dict: A dictionary of {namespace: set of members}
        :param graph: the graph to put the network in. Constructs new nx.MultiDiGrap if None
        :type graph: nx.MultiDiGraph
        :param namespace_mapping: a dict of {name: {value: (other_namepace, other_name)}}
        """

        self.graph = graph if graph is not None else nx.MultiDiGraph()

        self.control_parser = ControlParser(custom_annotations=custom_annotations)
        self.identifier_parser = IdentifierParser(namespace_dict=namespace_dict, mapping=namespace_mapping)

        self.node_count = 0
        self.node_to_id = {}

        identifier = self.identifier_parser.get_language()

        # 2.2 Abundance Modifier Functions

        # 2.2.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_protein_modifications
        self.pmod = PmodParser(namespace_parser=self.identifier_parser).get_language()

        # 2.2.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_variant_var
        self.variant = VariantParser().get_language()

        # 2.2.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_proteolytic_fragments
        self.fragment = FragmentParser().get_language()

        # 2.2.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_cellular_location
        self.location = LocationParser(self.identifier_parser).get_language()

        # 2.2.X Deprecated substitution function from BEL 1.0
        self.psub = PsubParser().get_language()
        self.gsub = GsubParser().get_language()

        # 2.6 Other Functions

        # 2.6.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_fusion_fus
        self.fusion = FusionParser(self.identifier_parser).get_language()

        # 2.1 Abundance Functions

        # 2.1.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcomplexA
        general_abundance_tags = oneOf(['a', 'abundance'])('function')
        general_abundance = general_abundance_tags + nest(Group(identifier))
        general_abundance.addParseAction(command_handler('Abundance', ensure_node_handler=self))

        # 2.1.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XgeneA
        gene_tags = oneOf(['g', 'geneAbundance'])('function')
        gene_simple = gene_tags + nest(Group(identifier) + Optional(WCW + Group(self.location)))
        gene_simple.addParseAction(command_handler('Gene', ensure_node_handler=self))

        gene_modified = gene_tags + nest(Group(identifier) + OneOrMore(
            WCW + Group(self.variant | self.gsub)) + Optional(
            WCW + Group(self.location)))
        gene_modified.setParseAction(command_handler('GeneVariant', ensure_node_handler=self))

        gene_fusion = gene_tags + nest(Group(self.fusion) + Optional(WCW + Group(self.location)))
        gene_fusion.setParseAction(command_handler('GeneFusion', ensure_node_handler=self))

        gene = gene_modified | gene_simple | gene_fusion

        # 2.1.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XmicroRNAA
        mirna_tags = oneOf(['m', 'microRNAAbundance'])('function')
        mirna_simple = mirna_tags + nest(Group(identifier) + Optional(WCW + Group(self.location)))
        mirna_simple.setParseAction(command_handler('miRNA', ensure_node_handler=self))

        mirna_modified = mirna_tags + nest(identifier + OneOrMore(WCW + self.variant) + Optional(
            WCW + self.location))
        mirna_modified.setParseAction(command_handler('miRNAVariant'))

        mirna = mirna_modified | mirna_simple

        # 2.1.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XproteinA
        protein_tag = oneOf(['p', 'proteinAbundance'])('function')
        protein_simple = protein_tag + nest(Group(identifier) + Optional(WCW + Group(self.location)))
        protein_simple.setParseAction(command_handler('Protein', ensure_node_handler=self))

        protein_modified = protein_tag + nest(Group(identifier) + OneOrMore(
            WCW + Group(self.pmod | self.variant | self.fragment | self.psub)) + Optional(
            WCW + Group(self.location)))

        protein_modified.setParseAction(command_handler('ProteinVariant', ensure_node_handler=self))

        protein_fusion = protein_tag + nest(Group(self.fusion) + Optional(WCW + Group(self.location)))

        def handle_protein_fusion(s, l, tokens):
            tokens[0] = 'ProteinFusion'
            return tokens

        protein_fusion.setParseAction(handle_protein_fusion)

        protein = protein_modified | protein_simple | protein_fusion

        # 2.1.7 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XrnaA
        rna_tags = oneOf(['r', 'rnaAbundance'])('function')
        rna_simple = rna_tags + nest(Group(identifier) + Optional(WCW + Group(self.location)))
        rna_simple.setParseAction(command_handler('RNA', ensure_node_handler=self))

        rna_modified = rna_tags + nest(Group(identifier) + OneOrMore(WCW + Group(self.variant)) + Optional(
            WCW + Group(self.location)))
        rna_modified.setParseAction(command_handler('RNAVariant', ensure_node_handler=self))

        rna_fusion = rna_tags + nest(Group(self.fusion) + Optional(WCW + Group(self.location)))
        rna_fusion.setParseAction(command_handler('RNA'))

        rna = rna_fusion | rna_modified | rna_simple

        single_abundance = general_abundance | gene | mirna | protein | rna

        # 2.1.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcomplexA
        complex_tags = oneOf(['complex', 'complexAbundance'])('function')

        complex_singleton_1 = complex_tags + nest(Group(identifier))
        complex_singleton_1.setParseAction(command_handler('Complex', ensure_node_handler=self))

        complex_singleton_2 = complex_tags + nest(identifier + WCW + self.location)

        complex_partial = single_abundance | complex_singleton_1 | complex_singleton_2

        complex_list_1 = complex_tags + nest(delimitedList(Group(complex_partial)))

        def handle_complex_list_1(s, l, tokens):
            tokens[0] = 'ComplexList'

            name = self.ensure_node(tokens)
            for token in tokens[1:]:
                member_name = self.ensure_node(token)
                self.add_unqualified_edge(name, member_name, relation='hasComponent')

            return tokens

        complex_list_1.setParseAction(handle_complex_list_1)

        complex_list_2 = complex_tags + nest(delimitedList(Group(complex_partial)) + WCW + self.location)

        complex_abundances = complex_list_2 | complex_list_1 | complex_singleton_2 | complex_singleton_1

        simple_abundance = complex_abundances | single_abundance

        # 2.1.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcompositeA
        composite_abundance_tags = oneOf(['composite', 'compositeAbundance'])('function')
        composite_abundance = composite_abundance_tags + nest(delimitedList(Group(simple_abundance)))

        def handle_composite_abundance(s, loc, tokens):
            tokens[0] = 'Composite'
            name = self.ensure_node(tokens)

            for component_token in tokens[1:]:
                component_name = self.ensure_node(component_token)
                self.add_unqualified_edge(name, component_name, relation='hasComponent')

            return tokens

        composite_abundance.setParseAction(handle_composite_abundance)

        abundance = simple_abundance | composite_abundance

        # 2.4 Process Modifier Function

        # 2.4.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XmolecularA

        molecular_activity_tags = oneOf(['ma', 'molecularActivity'])

        molecular_activities_default_ns = oneOf(language.activities)
        molecular_activities_default_ns.setParseAction(command_handler(language.activity_labels))

        # backwards compatibility with BEL v1.0
        molecular_activity_default_ns = molecular_activity_tags + nest(molecular_activities_default_ns)
        molecular_activity_custom_ns = molecular_activity_tags + nest(Group(identifier))

        molecular_activity = molecular_activity_default_ns | molecular_activity_custom_ns
        molecular_activity.setParseAction(command_handler('MolecularActivity'))

        # 2.3 Process Functions

        # 2.3.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_biologicalprocess_bp
        biological_process_tags = oneOf(['bp', 'biologicalProcess'])('function')
        biological_process = biological_process_tags + nest(Group(identifier))
        biological_process.setParseAction(command_handler('BiologicalProcess', ensure_node_handler=self))

        # 2.3.2
        pathology_tags = oneOf(['path', 'pathology'])('function')
        pathology = pathology_tags + nest(Group(identifier))
        pathology.setParseAction(command_handler('Pathology', ensure_node_handler=self))

        # 2.3.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xactivity
        activity_tags = oneOf(['act', 'activity'])

        activity_modified_default_ns = activity_tags + nest(Group(abundance) + WCW + Group(
            molecular_activity))
        activity_modified_default_ns.setParseAction(command_handler('Activity'))

        activity_standard = activity_tags + nest(Group(abundance))
        activity_standard.setParseAction(command_handler('Activity'))

        activity_legacy_tags = oneOf(language.activities)
        activity_legacy = activity_legacy_tags + nest(Group(abundance))

        def handle_activity_legacy(s, l, tokens):
            log.debug('PyBEL001 legacy activity statement. Use activity() instead. {}'.format(s))
            legacy_cls = language.activity_labels[tokens[0]]
            tokens[0] = 'Activity'
            tokens.append(['MolecularActivity', legacy_cls])
            return tokens

        activity_legacy.setParseAction(handle_activity_legacy)

        activity = activity_modified_default_ns | activity_standard | activity_legacy

        process = biological_process | pathology | activity

        # 2.5 Transformation Functions

        # 2.5.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_translocations

        from_loc = Suppress('fromLoc') + nest(identifier)
        to_loc = Suppress('toLoc') + nest(identifier)

        cell_secretion_tags = oneOf(['sec', 'cellSecretion'])('modifier')
        cell_secretion = cell_secretion_tags + nest(Group(simple_abundance))

        def handle_cell_secretion(s, l, tokens):
            tokens[0] = 'CellSecretion'
            return tokens

        cell_secretion.setParseAction(handle_cell_secretion)

        cell_surface_expression_tags = oneOf(['surf', 'cellSurfaceExpression'])('modifier')
        cell_surface_expression = cell_surface_expression_tags + nest(Group(simple_abundance))

        def handle_cell_surface_expression(s, l, tokens):
            tokens[0] = 'CellSurfaceExpression'
            return tokens

        cell_surface_expression.setParseAction(handle_cell_surface_expression)

        translocation_tags = oneOf(['translocation', 'tloc'])('modifier')
        translocation_standard = translocation_tags + nest(Group(simple_abundance) + WCW + Group(
            from_loc) + WCW + Group(to_loc))

        def translocation_standard_handler(s, l, tokens):
            tokens[0] = 'Translocation'
            self.ensure_node(tokens)
            return tokens

        translocation_standard.setParseAction(command_handler('Translocation', ensure_node_handler=self))

        translocation_legacy = translocation_tags + nest(Group(simple_abundance) + WCW + Group(
            identifier) + WCW + Group(
            identifier))

        def translocation_legacy_handler(s, l, token):
            log.debug('PyBEL005 legacy translocation statement. use fromLoc() and toLoc(). {}'.format(s))
            return translocation_standard_handler(s, l, token)

        translocation_legacy.setParseAction(translocation_legacy_handler)

        translocation_legacy_singleton = translocation_tags + nest(Group(simple_abundance))

        def handle_translocation_legacy_singleton(s, l, tokens):
            log.debug('PyBEL008 legacy translocation + missing arguments: {}'.format(s))
            tokens[0] = 'Translocation'
            return tokens

        translocation_legacy_singleton.setParseAction(handle_translocation_legacy_singleton)

        translocation = translocation_standard | translocation_legacy | translocation_legacy_singleton

        # 2.5.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_degradation_deg

        degradation_tags = oneOf(['deg', 'degradation'])('modifier')
        degradation = degradation_tags + nest(Group(simple_abundance))

        def handle_degredation(s, l, tokens):
            tokens[0] = 'Degradation'
            return tokens

        degradation.setParseAction(handle_degredation)

        # 2.5.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_reaction_rxn
        reactants = Suppress('reactants') + nest(delimitedList(Group(simple_abundance))('reactants'))
        products = Suppress('products') + nest(delimitedList(Group(simple_abundance))('products'))

        reaction_tags = oneOf(['reaction', 'rxn']).setParseAction(replaceWith('Reaction'))
        reaction = reaction_tags + nest(Group(reactants) + WCW + Group(products))

        def handle_reaction(s, l, tokens):
            # TODO move to ensure node?
            cls = tokens[0]
            name = self.canonicalize_node(tokens)
            if name not in self.graph:
                self.graph.add_node(name, type=cls)

            for reactant_tokens in tokens[1]:
                reactant_name = self.canonicalize_node(reactant_tokens)
                self.add_unqualified_edge(name, reactant_name, relation='hasReactant')

            for product_tokens in tokens[2]:
                product_name = self.canonicalize_node(product_tokens)
                self.add_unqualified_edge(name, product_name, relation='hasProduct')

            return tokens

        reaction.setParseAction(handle_reaction)

        transformation = cell_secretion | cell_surface_expression | translocation | degradation | reaction

        # 3 BEL Relationships

        bel_term = transformation | process | abundance

        # 3.1 Causal relationships

        # 3.1.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xincreases
        increases_tag = oneOf(['->', '→', 'increases']).setParseAction(replaceWith('increases'))
        increases = triple(bel_term, increases_tag, bel_term)

        # 3.1.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XdIncreases
        directly_increases_tag = oneOf(['=>', '⇒', 'directlyIncreases']).setParseAction(replaceWith('directlyIncreases'))
        directly_increases = triple(bel_term, directly_increases_tag, bel_term)

        # 3.1.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xdecreases
        decreases_tag = oneOf(['-|', 'decreases']).setParseAction(replaceWith('decreases'))
        decreases = triple(bel_term, decreases_tag, bel_term)

        # 3.1.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XdDecreases
        directly_decreases_tag = oneOf(['=|', '→', 'directlyDecreases']).setParseAction(replaceWith('directlyDecreases'))
        directly_decreases = triple(bel_term, directly_decreases_tag, bel_term)

        # 3.1.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_ratelimitingstepof
        rate_limit_tag = oneOf(['rateLimitingStepOf'])
        rate_limit = triple(biological_process | activity | transformation, rate_limit_tag, biological_process)

        # 3.1.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xcnc
        causes_no_change_tag = oneOf(['cnc', 'causesNoChange']).setParseAction(replaceWith('causesNoChange'))
        causes_no_change = triple(bel_term,causes_no_change_tag, bel_term)

        # 3.1.7 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_regulates_reg
        regulates_tag = oneOf(['reg', 'regulates']).setParseAction(replaceWith('regulates'))
        regulates = triple(bel_term, regulates_tag, bel_term)

        causal_relationship = (increases | directly_increases | decreases | directly_decreases | rate_limit | causes_no_change | regulates)

        # 3.1 Causal Relationships - nested
        # TODO should this feature be discontinued?

        increases_nested = triple(bel_term, increases_tag, nest(causal_relationship))
        decreases_nested = triple(bel_term, decreases_tag, nest(causal_relationship))
        directly_increases_nested = triple(bel_term, directly_increases_tag, nest(causal_relationship))
        directly_decreases_nested = triple(bel_term, directly_decreases_tag, nest(causal_relationship))

        nested_causal_relationship = increases_nested | decreases_nested | directly_increases_nested | directly_decreases_nested

        # 3.2 Correlative Relationships

        # 3.2.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XnegCor
        negative_correlation_tag = oneOf(['neg', 'negativeCorrelation']).setParseAction(
            replaceWith('negativeCorrelation'))
        negative_correlation = triple(bel_term, negative_correlation_tag, bel_term)

        # 3.2.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XposCor
        positive_correlation_tag = oneOf(['pos', 'positiveCorrelation']).setParseAction(
            replaceWith('positiveCorrelation'))
        positive_correlation = triple(bel_term, positive_correlation_tag, bel_term)

        # 3.2.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xassociation
        association_tag = oneOf(['--', 'association']).setParseAction(replaceWith('association'))
        association = triple(bel_term, association_tag, bel_term)

        correlative_relationships = negative_correlation | positive_correlation | association

        # 3.3 Genomic Relationships

        # 3.3.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_orthologous
        orthologous_tag = oneOf(['orthologous'])
        orthologous = triple(bel_term, orthologous_tag, bel_term)

        # 3.3.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_transcribedto
        transcribed_tag = oneOf([':>', 'transcribedTo']).setParseAction(replaceWith('transcribedTo'))
        transcribed = triple(gene, transcribed_tag, rna)

        # 3.3.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_translatedto
        translated_tag = oneOf(['>>', 'translatedTo']).setParseAction(replaceWith('translatedTo'))
        translated = triple(rna, translated_tag, protein)

        genomic_relationship = orthologous | transcribed | translated

        # 3.4 Other Relationships

        # 3.4.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_hasmember
        has_member_tag = oneOf(['hasMember'])
        has_member = triple(abundance, has_member_tag, abundance)

        # 3.4.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_hasmembers
        abundance_list = Suppress('list') + nest(delimitedList(Group(abundance)))

        has_members_tag = oneOf(['hasMembers'])
        has_members = triple(abundance, has_members_tag, abundance_list)

        def handle_has_members(s, l, tokens):
            parent = self.ensure_node(tokens[0])
            for child_tokens in tokens[2]:
                child = self.ensure_node(child_tokens)
                self.graph.add_edge(parent, child, relation='hasMember')
            return tokens

        has_members.setParseAction(handle_has_members)

        # 3.4.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_hascomponent
        has_component_tag = oneOf(['hasComponent'])
        has_component = triple(complex_abundances | composite_abundance, has_component_tag, abundance)

        # 3.4.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_isa
        is_a_tag = oneOf(['isA'])
        is_a = triple(bel_term, is_a_tag, bel_term)

        # 3.4.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_subprocessof
        subprocess_of_tag = oneOf(['subProcessOf'])
        subprocess_of = triple(process | activity | transformation, subprocess_of_tag, process)

        other_relationships = has_member | has_component | is_a | subprocess_of

        # 3.5 Deprecated

        # 3.5.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_analogous
        analogous_tags = oneOf(['analogousTo'])
        analogous = triple(bel_term, analogous_tags, bel_term)

        # 3.5.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_biomarkerfor
        biomarker_tags = oneOf(['biomarkerFor'])
        biomarker = triple(bel_term, biomarker_tags, process)

        # 3.5.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_prognosticbiomarkerfor
        prognostic_biomarker_tags = oneOf(['prognosticBiomarkerFor'])
        prognostic_biomarker = triple(bel_term, prognostic_biomarker_tags, process)

        deprecated_relationships = analogous | biomarker | prognostic_biomarker

        relation = (causal_relationship | correlative_relationships | genomic_relationship |
                    other_relationships | deprecated_relationships)

        def handle_relation(s, l, tokens):
            sub = self.ensure_node(tokens[0])
            obj = self.ensure_node(tokens[2])

            attrs = {
                'relation': tokens[1]
            }

            sub_mod = self.canonicalize_modifier(tokens[0])
            if sub_mod:
                attrs['subject'] = sub_mod

            obj_mod = self.canonicalize_modifier(tokens[2])
            if obj_mod:
                attrs['object'] = obj_mod

            attrs.update(self.get_annotations())

            self.graph.add_edge(sub, obj, attr_dict=attrs)
            return tokens

        relation.setParseAction(handle_relation)

        def handle_nested_relation(s, l, tokens):
            log.warning('handling of nested statements is not yet implemented')
            # get predicate 1 and predicate 2. resolve to compoundPredicate
            # build statement subject1 compoundPredicate object
            return tokens

        nested_causal_relationship.setParseAction(handle_nested_relation)

        # has_members is handled differently from all other relations becuase it gets distrinbuted
        relation = has_members | nested_causal_relationship | relation

        self.statement = relation | bel_term
        self.language = self.control_parser.get_language() | self.statement

    def get_language(self):
        """Get language defined by this parser"""
        return self.language

    def get_annotations(self):
        """Get current annotations in this parser"""
        return self.control_parser.get_annotations()

    # TODO canonicalize order of fragments, protein modifications, etc with alphabetization

    def add_unqualified_edge(self, u, v, relation):
        """Adds unique edge that has no annotations
        :param u: source node
        :param v: target node
        :param relation: relationship label
        """
        if not self.graph.has_edge(u, v, relation):
            self.graph.add_edge(u, v, key=relation, relation=relation)

    def canonicalize_node(self, tokens):
        """Given tokens, returns node name"""
        command, *args = tokens.asList() if hasattr(tokens, 'asList') else tokens
        if command in ('Protein', 'Gene', 'Abundance', 'miRNA', 'RNA', 'Complex', 'Pathology', 'BiologicalProcess'):
            # namespace = tokens['namespace']
            # name = tokens['name']
            namespace, name = args[0]
            return command, namespace, name
        elif command in ('ComplexList', 'Composite', 'List', 'Reaction'):
            t = list2tuple(args[0])
            if t not in self.node_to_id:
                # todo make different dictionaries for numbering
                self.node_count += 1
                self.node_to_id[t] = self.node_count
            return command, self.node_to_id[t]
        elif command in ('Activity', 'Degradation', 'Translocation', 'CellSecretion', 'CellSurfaceExpression'):
            return self.canonicalize_node(args[0])
        elif command in ('GeneVariant', 'RNAVariant', 'ProteinVariant'):
            ns, val = args[0]
            # mod_title, *mod_params = args[1]
            mod = list2tuple(args[1])
            # todo: flatten then splat sorted(args[1:], key=itemgetter(0))
            # todo: give running name tally
            name = (command, ns, val) + tuple(mod)
            return name
        else:
            raise NotImplementedError("Haven't written canonicalization for {}".format(command))

    def ensure_node(self, tokens):
        """Turns parsed tokens into canonical node name and makes sure its in the graph
        :param tokens:
        :return:
        """
        if isinstance(tokens, list):
            command, *args = list2tuple(tokens)
        else:
            command, *args = list2tuple(tokens.asList() if hasattr(tokens, 'asList') else tokens)

        if command in ('GeneVariant', 'RNAVariant', 'ProteinVariant'):
            name = self.canonicalize_node(tokens)
            if name not in self.graph:
                self.graph.add_node(name, type=command)
            parent_name = self.ensure_node([language.variant_parent_dict[command], tokens[1]])
            self.add_unqualified_edge(name, parent_name, 'hasParent')
        elif command == 'Protein':
            name = self.canonicalize_node(tokens)

            if name not in self.graph:
                ns, val = args[0]
                self.graph.add_node(name, type=command, namespace=ns, value=val)

            rna_tokens = deepcopy(tokens)
            rna_tokens[0] = 'RNA'
            rna_name = self.ensure_node(rna_tokens)

            self.add_unqualified_edge(rna_name, name, relation='translatedTo')
        elif command == 'RNA':
            name = self.canonicalize_node(tokens)

            if name not in self.graph:
                ns, val = args[0]
                self.graph.add_node(name, type=command, namespace=ns, value=val)

            gene_tokens = deepcopy(tokens)
            gene_tokens[0] = 'Gene'
            gene_name = self.ensure_node(gene_tokens)

            self.add_unqualified_edge(gene_name, name, relation='transcribedTo')
        else:
            name = self.canonicalize_node(tokens)
            if name not in self.graph:
                ns, val = args[0]
                self.graph.add_node(name, type=command, namespace=ns, value=val)
        return name

    def canonicalize_modifier(self, tokens):
        """
        Get activity, transformation, or transformation information as a dictionary
        :param tokens:
        :return:
        """
        command, *args = list2tuple(tokens.asList() if hasattr(tokens, 'asList') else tokens)

        if command not in ('Activity', 'Degradation', 'Translocation', 'CellSecretion', 'CellSurfaceExpression'):
            return {}

        res = {
            'modification': command,
            'params': {}
        }

        if command == 'Activity':
            if len(args) > 1:  # has molecular activity annotation
                res['params'] = {
                    'molecularActivity': args[1][1]
                }
            # TODO switch between legacy annotation and namespace:name annotation
            return res
        elif command == 'Degradation':
            return res
        elif command == 'Translocation':
            res['params'] = {
                'fromLoc': {
                    'namespace': args[1][0],
                    'name': args[1][1]
                },
                'toLoc': {
                    'namespace': args[2][0],
                    'name': args[2][1]
                }
            }
            return res
        elif command == 'CellSecretion':
            res['params'] = {
                'fromLoc': dict(namespace='GOCC', name='intracellular'),
                'toLoc': dict(namespace='GOCC', name='extracellular space')
            }
            return res
        elif command == 'CellSurfaceExpression':
            res['params'] = {
                'fromLoc': dict(namespace='GOCC', name='intracellular'),
                'toLoc': dict(namespace='GOCC', name='cell surface')
            }
            return res


def flatten_modifier_dict(d, prefix=''):
    command = d['modification']
    res = {
        '{}_modification'.format(prefix): command
    }

    if command == 'Activity':
        if 'params' in d and 'activity' in d['params']:
            if isinstance(d['params']['activity'], (list, tuple)):
                res['{}_params_activity_namespace'.format(prefix)] = d['params']['activity']['namespace']
                res['{}_params_activity_value'.format(prefix)] = d['params']['activity']['name']
            else:
                res['{}_params_activity'.format(prefix)] = d['params']['activity']
    elif command in ('Translocation', 'CellSecretion', 'CellSurfaceExpression'):
        res['{}_params_fromLoc_namespace'.format(prefix)] = d['params']['fromLoc']['namespace']
        res['{}_params_fromLoc_value'.format(prefix)] = d['params']['fromLoc']['name']
        res['{}_params_toLoc_namespace'.format(prefix)] = d['params']['toLoc']['namespace']
        res['{}_params_toLoc_value'.format(prefix)] = d['params']['toLoc']['name']
    elif command == 'Degradation':
        pass
    return res
