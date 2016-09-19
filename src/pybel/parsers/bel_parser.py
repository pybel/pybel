#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

import networkx as nx
from pyparsing import *

from . import language

log = logging.getLogger(__name__)

WS = Suppress(ZeroOrMore(White()))
LP = Suppress('(') + WS
RP = WS + Suppress(')')
CM = Suppress(',')
WCW = WS + CM + WS


class Parser:
    """
    Build a parser backed by a given dictionary of namespaces
    """

    def __init__(self, graph=None, annotations=None, namespaces=None, namespace_mapping=None):
        """
        :param namespaces: A dictionary of {namespace: set of members}
        """
        self.namespaces = namespaces
        self.namespace_mapping = namespace_mapping
        self.graph = graph if graph is not None else nx.MultiDiGraph()
        self.annotations = annotations if annotations is not None else {}

        self.node_count = 0
        self.node_to_id = {}
        self.id_to_node = {}

        value = Word(alphanums)
        quoted_value = dblQuotedString().setParseAction(removeQuotes)

        ns_val = Word(alphanums) + Suppress(':') + (value | quoted_value)
        ns_val.setParseAction(self.validate_ns_pair)

        # 2.2 Abundance Modifier Functions

        # 2.2.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_protein_modifications
        aa_single = oneOf(language.aminoacid_dict)
        aa_triple = oneOf(language.aminoacid_dict.values())
        amino_acids = aa_single | aa_triple | 'X'

        pmod_tags = ['pmod', 'proteinModification']

        pmod_option_1 = oneOf(pmod_tags) + LP + ns_val + RP
        pmod_option_2 = oneOf(pmod_tags) + LP + ns_val + WCW + amino_acids + RP
        pmod_option_3 = oneOf(pmod_tags) + LP + ns_val + WCW + amino_acids + WCW + pyparsing_common.number() + RP

        pmod = pmod_option_1 | pmod_option_2 | pmod_option_3

        # 2.2.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_variant_var
        nucleotides = oneOf(['A', 'G', 'C', 'T'])

        # TODO see spec at http://www.hgvs.org/mutnomen/recs.html
        hgvs_protein = Suppress('p.') + aa_triple + pyparsing_common.integer() + aa_triple
        hgvs_genomic = Suppress('g.') + pyparsing_common.integer() + nucleotides + Suppress('>') + nucleotides
        hgvs_variant = hgvs_genomic | hgvs_protein | '=' | '?'

        variant_tags = ['var', 'variant']
        variant = oneOf(variant_tags) + LP + hgvs_variant + RP

        # 2.2.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_proteolytic_fragments
        fragment_range = (pyparsing_common.integer() | '?') + Suppress('_') + (pyparsing_common.integer() | '?' | '*')
        fragment_tags = ['frag', 'fragment']
        fragment_1 = oneOf(fragment_tags) + LP + fragment_range + RP
        fragment_2 = oneOf(fragment_tags) + LP + fragment_range + WCW + Word(alphanums) + RP
        fragment = fragment_2 | fragment_1

        # 2.2.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_cellular_location
        location_tags = ['loc', 'location']
        location = oneOf(location_tags) + LP + ns_val + RP

        # 2.6 Other Functions

        # 2.6.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_fusion_fus

        # sequence coordinates?
        range_coordinate = (oneOf(['r', 'p']) + '.' + Word(nums) + '_' + Word(nums)) | '?'

        fusion_tags = ['fus', 'fusion']
        fusion = oneOf(fusion_tags) + LP + ns_val + WCW + range_coordinate + WCW + ns_val + WCW + range_coordinate + RP

        # 2.1 Abundance Functions

        # 2.1.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcomplexA
        general_abundance_tags = ['a', 'abundance']
        general_abundance = oneOf(general_abundance_tags) + LP + Group(ns_val) + RP

        def handle_general_abundance(s, l, tokens):
            cls = tokens[0] = 'Abundance'
            ns, val = tokens[1]
            n = cls, ns, val
            if n not in self.graph:
                self.graph.add_node(n, type=cls, namespace=ns, value=val)
            return tokens

        general_abundance.addParseAction(handle_general_abundance)

        # 2.1.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XgeneA
        gene_tags = ['g', 'geneAbundance']

        gene_simple = oneOf(gene_tags) + LP + Group(ns_val) + RP

        def handle_gene_simple(s, location, tokens):
            cls = tokens[0] = 'Gene'
            ns, val = tokens[1]
            n = cls, ns, val
            if n not in self.graph:
                self.graph.add_node(n, type=cls, namespace=ns, value=val)
            return tokens

        gene_simple.addParseAction(handle_gene_simple)

        gene_modified = oneOf(gene_tags) + LP + ns_val + OneOrMore(WCW + variant) + Optional(WCW + location) + RP

        def handle_gene_modified(s, l, tokens):
            # TODO fill this in
            return tokens

        gene_modified.setParseAction(handle_gene_modified)

        gene_fusion = oneOf(gene_tags) + LP + fusion + RP

        def handle_gene_fusion(s, l, tokens):
            # TODO fill this in
            return tokens

        gene_fusion.setParseAction(handle_gene_fusion)

        gene = gene_modified | gene_simple | gene_fusion

        # 2.1.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XmicroRNAA
        mirna_tags = ['m', 'microRNAAbundance']
        mirna_simple = oneOf(mirna_tags) + LP + Group(ns_val) + RP

        def handle_mirna_simple(s, l, tokens):
            cls = tokens[0] = 'miRNA'
            ns, val = tokens[1]
            n = cls, ns, val
            if n not in self.graph:
                self.graph.add_node(n, type=cls, namespace=ns, value=value)
            return tokens

        mirna_simple.setParseAction(handle_mirna_simple)

        mirna_modified = oneOf(mirna_tags) + LP + ns_val + OneOrMore(WCW + variant) + Optional(WCW + location) + RP

        def handle_mirna_modified(s, l, tokens):
            # TODO fill this in
            return tokens

        mirna_modified.setParseAction(handle_mirna_modified)

        mirna = mirna_modified | mirna_simple

        # 2.1.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XproteinA
        protein_tags = ['p', 'proteinAbundance']
        protein_simple = oneOf(protein_tags) + LP + Group(ns_val) + RP

        def handle_protein_simple(s, l, tokens):
            cls = tokens[0] = 'Protein'
            ns, val = tokens[1]
            n = cls, ns, val
            if n not in self.graph:
                self.graph.add_node(n, type=cls, namespace=ns, value=val)
            return tokens

        protein_simple.setParseAction(handle_protein_simple)

        protein_modified = oneOf(protein_tags) + LP + ns_val + OneOrMore(WCW + (pmod | variant | fragment)) + Optional(
            WCW + location) + RP

        def handle_protein_modified(s, l, tokens):
            # TODO fill this in
            return tokens

        protein_modified.setParseAction(protein_modified)

        protein_fusion = oneOf(protein_tags) + LP + fusion + RP

        def handle_protein_fusion(s, l, tokens):
            # TODO fill this in
            return tokens

        protein_fusion.setParseAction(handle_protein_fusion)

        protein = protein_modified | protein_simple | protein_fusion

        # 2.1.7 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XrnaA
        rna_tags = ['r', 'rnaAbundance']
        rna_simple = oneOf(rna_tags) + LP + ns_val + RP

        def handle_rna_simple(s, l, tokens):
            cls = tokens[0] = 'RNA'
            ns, val = tokens[1]
            n = cls, ns, val
            if n not in self.graph:
                self.graph.add_node(n, type=cls, namespace=ns, value=value)
            return tokens

        rna_simple.setParseAction(handle_rna_simple)

        rna_modified = oneOf(rna_tags) + LP + ns_val + OneOrMore(WCW + variant) + Optional(WCW + location) + RP

        def handle_rna_modified(s, l, tokens):
            # TODO fill this in
            return tokens

        rna_modified.setParseAction(handle_rna_modified)

        rna_fusion = oneOf(rna_tags) + LP + fusion + RP

        def handle_rna_fusion(s, l, tokens):
            # TODO fill this in
            return tokens

        rna_fusion.setParseAction(handle_rna_fusion)

        rna = rna_modified | rna_simple | rna_fusion

        single_abundance = general_abundance | gene | mirna | protein | rna

        # 2.1.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcomplexA
        complex_tags = ['complex', 'complexAbundance']
        complex_singleton_1 = oneOf(complex_tags) + LP + Group(ns_val) + RP

        def handle_complex_singleton_1(s, l, tokens):
            cls = tokens[0] = 'Complex'
            ns, val = tokens[1]
            n = cls, ns, val
            if n not in self.graph:
                self.graph.add_node(n, type=cls, namespace=ns, value=value)
            return tokens

        complex_singleton_1.setParseAction(handle_complex_singleton_1)

        complex_singleton_2 = oneOf(complex_tags) + LP + ns_val + WCW + location + RP

        complex_list_1 = oneOf(complex_tags) + LP + Group(single_abundance) + OneOrMore(
            WCW + Group(single_abundance)) + RP

        def handle_complex_list_1(s, l, tokens):
            cls = tokens[0] = 'Complex'

            self.node_count += 1
            self.node_to_id[self.node_count] = tokens
            self.graph.add_node(self.node_count, type=cls)

            for token in tokens[1:]:
                v_cls = token[0]
                v_ns, v_val = token[1]
                v = v_cls, v_ns, v_val
                self.graph.add_edge(self.node_count, v, type='hasComponent', attr_dict=self.annotations.copy())

            return tokens

        complex_list_1.setParseAction(handle_complex_list_1)

        complex_list_2 = oneOf(complex_tags) + LP + Group(single_abundance) + OneOrMore(
            WCW + Group(single_abundance)) + WCW + location + RP

        complex_abundances = complex_list_2 | complex_list_1 | complex_singleton_2 | complex_singleton_1

        simple_abundance = complex_abundances | single_abundance

        # 2.1.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcompositeA
        composite_abundance_tags = ['composite', 'compositeAbundance']
        composite_abundance = oneOf(composite_abundance_tags) + LP + Group(simple_abundance) + OneOrMore(
            WCW + Group(simple_abundance)) + RP

        def handle_composite_abundance(s, loc, tokens):
            cls = tokens[0] = 'Composite'

            self.node_count += 1
            self.node_to_id[self.node_count] = tokens
            self.graph.add_node(self.node_count, type=cls)

            for token in tokens[1:]:
                v_cls = token[0]
                v_ns, v_val = token[1]
                v = v_cls, v_ns, v_val
                self.graph.add_edge(self.node_count, v, type='hasComponent', attr_dict=self.annotations.copy())

            return tokens

        composite_abundance.setParseAction(handle_composite_abundance)

        abundance = simple_abundance | composite_abundance

        # 2.4 Process Modifier Function

        # 2.4.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XmolecularA

        molecular_activity_tags = ['ma', 'molecularActivity']

        # backwards compatibility with BEL v1.0
        molecular_activity_backwards = oneOf(molecular_activity_tags) + LP + oneOf(language.activities) + RP
        molecular_activity_right = oneOf(molecular_activity_tags) + LP + ns_val + RP

        molecular_activity = molecular_activity_backwards | molecular_activity_right

        # 2.3 Process Functions

        # 2.3.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_biologicalprocess_bp
        biological_process_tags = ['bp', 'biologicalProcess']
        biological_process = oneOf(biological_process_tags) + LP + Group(ns_val) + RP

        def handle_biological_process(s, l, tokens):
            cls = tokens[0] = 'Process'
            ns, val = tokens[1]
            n = cls, ns, val
            if n not in self.graph:
                self.graph.add_node(n, type=cls, namespace=ns, value=value)
            return tokens

        biological_process.setParseAction(handle_biological_process)

        # 2.3.2
        pathology_tags = ['path', 'pathology']
        pathology = oneOf(pathology_tags) + LP + Group(ns_val) + RP

        def handle_pathology(s, l, tokens):
            cls = tokens[0] = 'Pathology'
            ns, val = tokens[1]
            n = cls, ns, val
            if n not in self.graph:
                self.graph.add_node(n, type=cls, namespace=ns, value=val)
            return tokens

        pathology.setParseAction(handle_pathology)

        # 2.3.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xactivity
        # FIXME activity consolidation
        # see http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_activity_functions
        activity_tags = ['act', 'activity']

        activity_legacy_tags = list(language.activities)
        activity_legacy = oneOf(activity_legacy_tags) + LP + Group(abundance) + RP

        def handle_activity_legacy(s, l, tokens):
            log.warning('parsing legacy activity: {}'.format(s))
            legacy_cls = tokens[0]
            cls = tokens[0] = 'activity'
            tokens.append(['molecularActivity', legacy_cls])
            return tokens

        activity_legacy.setParseAction(handle_activity_legacy)

        activity_modified = oneOf(activity_legacy_tags) + LP + Group(abundance) + WCW + Group(molecular_activity) + RP

        def handle_activity_modified(s, l, tokens):
            # TODO fill this in
            return tokens

        activity_modified.setParseAction(handle_activity_modified)

        activity = activity_modified | activity_legacy

        process = biological_process | pathology | activity

        # 2.5 Transformation Functions

        # 2.5.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_translocations

        from_loc = Suppress('fromLoc') + LP + ns_val + RP
        to_loc = Suppress('toLoc') + LP + ns_val + RP

        cell_secretion_tags = ['sec', 'cellSecretion']
        cell_secretion_correct = oneOf(cell_secretion_tags) + LP + simple_abundance + WCW + from_loc + WCW + to_loc + RP
        cell_secretion_wrong = oneOf(cell_secretion_tags) + LP + simple_abundance + WCW + ns_val + WCW + ns_val + RP
        cell_secretion_wrong.setParseAction(lambda a, b, c: log.warning('Invalid cell secretion syntax!'))

        cell_secretion = cell_secretion_wrong | cell_secretion_correct

        cell_surface_expression_tags = ['surf', 'cellSurfaceExpression']
        cell_surface_expression_correct = oneOf(
            cell_surface_expression_tags) + LP + simple_abundance + RP + WCW + from_loc + WCW + to_loc + RP
        cell_surface_expression_wrong = oneOf(
            cell_surface_expression_tags) + LP + simple_abundance + RP + WCW + from_loc + WCW + to_loc + RP

        cell_surface_expression = cell_surface_expression_wrong | cell_surface_expression_correct

        translocation_tags = ['translocation', 'tloc']
        translocation = oneOf(translocation_tags) + LP + Group(simple_abundance) + WCW + Group(from_loc) + WCW + Group(
            to_loc) + RP

        # translocation_wrong = oneOf(translocation_tags) + LP + simple_abundance + WCW + ns_val + WCW + ns_val + RP
        # translocation = translocation_wrong | translocation_right

        def translocation_handler(s, l, tokens):
            cls = tokens[0] = 'Translocation'

            ab_fn = tokens[1][0]
            ab_ns, ab_val = tokens[1][1]

            ab_n = ab_fn, ab_ns, ab_val
            if ab_n not in self.graph:
                self.graph.add_node(ab_n, type=ab_fn, namespace=ab_ns, value=ab_val)

            from_loc_ns, from_loc_val = tokens[2]
            to_loc_ns, to_loc_val = tokens[3]

            self.node_count += 1
            self.graph.add_node(self.node_count, type=cls, attr_dict={
                'from_ns': from_loc_ns,
                'from_value': from_loc_val,
                'to_ns': to_loc_ns,
                'to_value': to_loc_val
            })

            self.graph.add_edge(ab_n, self.node_count, type='participant', attr_dict=self.annotations.copy())
            return tokens

        translocation.setParseAction(translocation_handler)

        # 2.5.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_degradation_deg

        degredation_tags = ['deg', 'degredation']
        degredation = oneOf(degredation_tags) + LP + simple_abundance + RP

        # 2.5.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_reaction_rxn
        reactants = Suppress('reactants') + LP + Group(simple_abundance) + ZeroOrMore(
            WCW + Group(simple_abundance)) + RP
        products = Suppress('products') + LP + Group(simple_abundance) + ZeroOrMore(WCW + Group(simple_abundance)) + RP

        reaction_tags = ['reaction', 'rxn']
        reaction = (oneOf(reaction_tags) + LP + Group(reactants) + WCW + Group(products) + RP)

        def handle_reaction(s, l, tokens):
            cls = tokens[0] = 'Reaction'

            self.node_count += 1
            self.graph.add_node(self.node_count, type=cls)

            for reactant in tokens[1]:
                v_cls = reactant[0]
                v_ns, v_val = reactant[1]
                v = v_cls, v_ns, v_val
                self.graph.add_edge(self.node_count, v, type='hasReactant', attr_dict=self.annotations.copy())

            for product in tokens[2]:
                v_cls = product[0]
                v_ns, v_val = product[1]
                v = v_cls, v_ns, v_val
                self.graph.add_edge(self.node_count, v, type='hasProduct', attr_dict=self.annotations.copy())

            return tokens

        transformation = cell_secretion | cell_surface_expression | translocation | degredation | reaction

        # 3 BEL Relationships

        bel_term = abundance | process | transformation

        # 3.1 Causal relationships

        causal_relationship = Forward()

        # 3.1.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xincreases
        increases_tags = ['->', '→', 'increases']
        increases = Group(bel_term) + WS + oneOf(increases_tags) + WS + (
            Group(bel_term) | (LP + causal_relationship + RP))

        def handle_increases(s, l, tokens):
            tokens[1] = increases_tags[-1]

            # u = self.ensure_term(tokens[0])
            # v = self.ensure_term(tokens[2])
            # self.graph.add_edge(u, v, type=tokens[1], attr_dict=self.annotations.copy())

            return tokens

        increases.setParseAction(handle_increases)

        # 3.1.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XdIncreases
        directly_increases_tags = ['=>', '⇒', 'directlyIncreases']
        directly_increases = Group(bel_term) + WS + oneOf(directly_increases_tags) + WS + (
            Group(bel_term) | (LP + causal_relationship + RP))

        # 3.1.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xdecreases
        decreases_tags = ['-|', 'decreases']
        decreases = Group(bel_term) + WS + oneOf(decreases_tags) + WS + (
            Group(bel_term) | (LP + causal_relationship + RP))

        # 3.1.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XdDecreases
        directly_decreases_tags = ['=|', '→', 'directlyDecreases']
        directly_decreases = Group(bel_term) + WS + oneOf(directly_decreases_tags) + WS + (
            Group(bel_term) | (LP + causal_relationship + RP))

        # 3.1.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_ratelimitingstepof
        rate_limit_tags = ['rateLimitingStepOf']
        rate_limit = (biological_process | activity | transformation) + WS + oneOf(
            rate_limit_tags) + WS + biological_process

        # 3.1.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xcnc
        causes_no_change_tags = ['cnc', 'causesNoChange']
        causes_no_change = Group(bel_term) + WS + oneOf(causes_no_change_tags) + WS + Group(bel_term)

        # 3.1.7 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_regulates_reg
        regulates_tags = ['reg', 'regulates']
        regulates = Group(bel_term) + WS + oneOf(regulates_tags) + WS + Group(bel_term)

        causal_relationship << (
            increases | directly_increases | decreases | directly_decreases | rate_limit | causes_no_change | regulates)

        # 3.2 Correlative Relationships

        # 3.2.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XnegCor
        negative_correlation_tags = ['neg', 'negativeCorrelation']
        negative_correlation = Group(bel_term) + WS + oneOf(negative_correlation_tags) + WS + Group(bel_term)

        # 3.2.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XposCor
        positive_correlation_tags = ['pos', 'positiveCorrelation']
        positive_correlation = Group(bel_term) + WS + oneOf(positive_correlation_tags) + WS + Group(bel_term)

        # 3.2.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#Xassociation
        association_tags = ['--', 'association']
        association = Group(bel_term) + WS + oneOf(association_tags) + WS + Group(bel_term)

        correlative_relationships = negative_correlation | positive_correlation | association

        # 3.3 Genomic Relationships

        # 3.3.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_orthologous
        orthologous_tags = ['orthologous']
        orthologous = Group(bel_term) + WS + oneOf(orthologous_tags) + WS + Group(bel_term)

        # 3.3.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_transcribedto
        transcribed_tags = [':>', 'transcribedTo']
        transcribed = gene + WS + oneOf(transcribed_tags) + WS + rna

        # 3.3.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_translatedto
        translated_tags = [':>', 'transcribedTo']
        translated = rna + WS + oneOf(translated_tags) + WS + protein

        def handle_translated(s, loc, tokens):
            tokens[1] = translated_tags[-1]
            return tokens

        translated.setParseAction(handle_translated)

        genomic_relationship = orthologous | transcribed | translated

        # 3.4 Other Relationships

        # 3.4.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_hasmember
        has_member_tags = ['hasMember']
        has_member = Group(abundance) + WS + oneOf(has_member_tags) + WS + Group(abundance)

        # 3.4.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_hasmembers
        abundance_list = Suppress('list') + LP + OneOrMore(abundance)

        has_members_tags = ['hasMembers']
        has_members = Group(abundance) + WS + oneOf(has_members_tags) + WS + Group(abundance_list)

        # 3.4.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_hascomponent
        has_component_tags = ['hasComponent']
        has_component = Group(complex_abundances | composite_abundance) + WS + oneOf(has_component_tags) + WS + Group(
            abundance)

        # 3.4.5 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_isa
        is_a_tags = ['isA']
        is_a = Group(bel_term) + WS + oneOf(is_a_tags) + WS + Group(bel_term)

        # 3.4.6 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_subprocessof
        subprocess_of_tags = ['subProcessOf']
        subprocess_of = Group(process | activity | transformation) + WS + oneOf(subprocess_of_tags) + WS + Group(
            process)

        other_relationships = has_member | has_members | has_component | is_a | subprocess_of

        # 3.5 Deprecated

        # 3.5.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_analogous
        analogous_tags = ['analogousTo']
        analogous = Group(bel_term) + WS + oneOf(analogous_tags) + WS + Group(bel_term)

        # 3.5.2 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_biomarkerfor
        biomarker_tags = ['biomarkerFor']
        biomarker = Group(bel_term) + WS + oneOf(biomarker_tags) + Group(process)

        # 3.5.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_prognosticbiomarkerfor
        prognostic_biomarker_tags = ['progonsticBiomarkerFor']
        prognostic_biomarker = Group(bel_term) + WS + oneOf(prognostic_biomarker_tags) + WS + Group(process)

        deprecated_relationships = analogous | biomarker | prognostic_biomarker

        relation = (causal_relationship | correlative_relationships | genomic_relationship |
                    other_relationships | deprecated_relationships)

        self.statement = relation | bel_term

    def validate_ns_pair(self, s, location, tokens):
        ns, val = tokens

        if self.namespaces is None:
            pass
        elif ns not in self.namespaces:
            raise Exception('Namespace Exception: invalid namespace: {}'.format(ns))
        elif val not in self.namespaces[ns]:
            raise Exception('Namespace Exception: {} is not a valid member of {}'.format(val, ns))

        if self.namespace_mapping is None:
            pass
        elif ns in self.namespace_mapping and val in self.namespace_mapping[ns]:
            return self.namespace_mapping[ns][val]

        return tokens

    def parse(self, s):
        try:
            return self.statement.parseString(s).asList()
        except Exception as e:
            log.warn('failed to parse: {}'.format(s))
            return None

    def set_metadata(self, citation, annotations):
        self.annotations.update(annotations)
        self.annotations.update({'citation_{}'.format(k): v for k, v in citation.items()})
