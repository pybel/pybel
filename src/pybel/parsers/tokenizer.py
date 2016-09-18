import logging

from pyparsing import *

from . import language

log = logging.getLogger(__name__)

LPAR, RPAR = map(Suppress, '()')
WS = Suppress(ZeroOrMore(White()))
CM = Suppress(',')
WCW = WS + CM + WS

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
gene_abundance_app = gene_abundance + LPAR + Group(identifier) + Group(Optional(WS + Suppress(',') + snp)) + RPAR
#############

exclude_tags = gene_abundance_tags + protein_abundance_tags
fn_tags = [f for f in language.functions if f not in exclude_tags]

fn = oneOf(fn_tags)
fn_app = (fn + LPAR + Group(identifier) + RPAR) | gene_abundance_app | protein_abundance_app

reaction_tags = ['reaction', 'rxn']
rxn = (
    oneOf(reaction_tags) + LPAR + Group('reactants' + LPAR + Group(fn_app) + ZeroOrMore(WCW + Group(fn_app)) + RPAR) +
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

statement = simple_statement | nested_statement | double_statement  # | subject


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

    def tokenize(self, s):
        if self.namespaces is not None:
            raise NotImplementedError()
        try:
            return statement.parseString(s).asList()
        except Exception as e:
            log.debug('failed to parse: {}'.format(s))
            return None
