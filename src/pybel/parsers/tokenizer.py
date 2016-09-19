import logging

from pyparsing import *

from . import language

log = logging.getLogger(__name__)

LPAR, RPAR = map(Suppress, '()')
WS = Suppress(ZeroOrMore(White()))
CM = Suppress(',')
WCW = WS + CM + WS


# TODO add in namespace checking and error handling
class Parser:
    """
    Build a parser backed by a given dictionary of namespaces
    """

    def __init__(self, namespaces=None):
        """
        :param namespace_dict: A dictionary of {namespace: set of members}
        """
        self.namespaces = namespaces

        relation = oneOf(language.relations)

        namespace = Word(alphanums)
        value = Word(alphanums)
        quoted_value = dblQuotedString().setParseAction(removeQuotes)

        ns_val = namespace + Suppress(':') + (value | quoted_value)

        identifier = ns_val | quoted_value | value

        ############
        aminoacids = oneOf(language.aminoacids)
        pmod_params = oneOf(language.pmod_parameters_A)

        pmod = oneOf(['pmod', 'proteinModification'])
        modification_app = (
            pmod + LPAR + pmod_params + Optional(
                WCW + aminoacids + Optional(WCW + pyparsing_common.number() + WS)) + RPAR)

        # TODO this isn't actually in the bel spec
        # TODO if both sub and pmod, what order?
        psub_app = 'sub' + LPAR + aminoacids + WCW + pyparsing_common.number() + WCW + aminoacids + RPAR

        protein_abundance_tags = ['p', 'proteinAbundance']
        protein_abundance = oneOf(protein_abundance_tags)
        protein_abundance_app = protein_abundance + LPAR + Group(identifier) + Optional(
            Group(WCW + modification_app)) + Optional(WCW + Group(psub_app)) + RPAR  # sub(G,275341,C)

        nucleotides = oneOf(['A', 'G', 'C', 'T'])
        snp = 'sub' + LPAR + nucleotides + WCW + pyparsing_common.number() + WCW + nucleotides + RPAR

        gene_abundance_tags = ['g', 'geneAbundance']
        gene_abundance = oneOf(gene_abundance_tags)
        gene_abundance_app = gene_abundance + LPAR + Group(identifier) + Group(
            Optional(WS + Suppress(',') + snp)) + RPAR
        #############

        exclude_tags = gene_abundance_tags + protein_abundance_tags
        fn_tags = [f for f in language.functions if f not in exclude_tags]

        fn = oneOf(fn_tags)
        fn_app = (fn + LPAR + Group(identifier) + RPAR) | gene_abundance_app | protein_abundance_app

        reaction_tags = ['reaction', 'rxn']
        rxn = (
            oneOf(reaction_tags) + LPAR + Group(
                'reactants' + LPAR + Group(fn_app) + ZeroOrMore(WCW + Group(fn_app)) + RPAR) +
            WCW + Group('products' + LPAR + Group(fn_app) + ZeroOrMore(WCW + Group(fn_app)) + RPAR) + RPAR)

        list_fn_tags = [l for l in language.lists if l not in reaction_tags] + ['complexAbundance']
        list_fn = oneOf(list_fn_tags)
        list_fn_app = (
            (list_fn + LPAR + Group(identifier) + RPAR) |
            (list_fn + LPAR + (OneOrMore(Group(fn_app) + WS + Suppress(',') + WS) +
                               Group(fn_app)) + RPAR)
        )

        activity = oneOf(language.activities)
        activity_app = (activity + LPAR + Group(fn_app | list_fn_app) + RPAR)

        translocation = ((oneOf(language.translocations) + LPAR + Group(fn_app) + WCW + Group(identifier) + WCW + Group(
            identifier) + RPAR)) | (oneOf(language.translocations) + LPAR + Group(fn_app) + RPAR)

        subject = activity_app | fn_app | list_fn_app | translocation | rxn

        simple_statement = (
            Group(subject) +
            WS +
            relation +
            WS +
            Group(subject)
        )

        nested_statement = (
            Group(subject) +
            WS +
            relation +
            WS +
            LPAR +
            WS +
            Group(simple_statement) +
            WS +
            RPAR
        )

        double_statement = (
            Group(subject) + WS + relation + WS + Group(subject) + WS + relation + WS + Group(subject)
        )

        self.statement = simple_statement | nested_statement | double_statement  # | subject

    def tokenize(self, s):
        if self.namespaces is not None:
            raise NotImplementedError()
        try:
            return self.statement.parseString(s).asList()
        except Exception as e:
            log.debug('failed to parse: {}'.format(s))
            return None


def handle_function(g, command, args):
    command = language.functions_canon[command]
    fn_namespace, fn_value = args[0]
    id = command, fn_namespace, fn_value
    if id not in g:
        g.add_node(id, type=command, namespace=fn_namespace, value=fn_value)


def handle_list_function(g, command, args):
    for arg in args:
        print('ARGUMENT', arg)


def handle_tokens(g, tokens, citation, annotations):
    # Handle citation and annotations
    node_annotations = annotations.copy()
    for key in citation:
        node_annotations['citation_{}'.format(key)] = citation[key]

    if len(tokens) == 1:
        raise NotImplementedError()

    s, p, o = tokens

    # handle subject
    s_command, s_args = s[0], s[1:]

    if s_command in language.functions:
        handle_function(g, s_command, s_args)
    elif s_command == 'complex':
        handle_list_function(g, s_command, s_args)

    if s[0] in language.functions and o[0] in language.functions:
        s_ns, s_name = s[1]
        o_ns, o_name = o[1]

        s_can = '{}:{}'.format(s_ns, s_name)
        o_can = '{}:{}'.format(o_ns, o_name)

        if s_can not in g:
            g.add_node(s_can, type=s[0], name=s_name, namespace=s_ns)
            log.debug('added {}:{}'.format(s[0], s_can))

        if o_can not in g:
            g.add_node(o_can, type=o[0], name=s_name, namespace=o_ns)
            log.debug('added {}:{}'.format(o[0], o_can))

        node_annotations['relation'] = p

        log.debug('added {}{}{}'.format(s_can, p, o_can))

        g.add_edge(s_can, o_can, attr_dict=node_annotations)
