from pyparsing import *

from . import language

LPAR, RPAR = map(Suppress, '()')
WS = Suppress(ZeroOrMore(White()))

relation = oneOf(language.relations)

namespace = Word(alphanums)
value = Word(alphanums)
quoted_value = dblQuotedString().setParseAction(removeQuotes)

identifier = namespace + Suppress(':') + (value | quoted_value)

# TODO add protein abundance
# TODO translocation function
############
aminoacids = oneOf(language.aminoacids)
pmod_params = oneOf(language.pmod_parameters_A)

modifications = oneOf(language.modifications)
modification_app = modifications + LPAR + RPAR

protein_abundance_tags = ['p', 'proteinAbundance']
protein_abundance = oneOf(protein_abundance_tags)
protein_abundance_app = protein_abundance + LPAR + Group(identifier) + RPAR

# sub(G,275341,C)

nucleotides = oneOf(['A', 'G', 'C', 'T'])
snp = 'sub' + LPAR + nucleotides + Suppress(',') + pyparsing_common.number() + Suppress(',') + nucleotides + RPAR

gene_abundance_tags = ['g', 'geneAbundance']
gene_abundance = oneOf(gene_abundance_tags)
gene_abundance_app = gene_abundance + LPAR + Group(identifier) + Group(Optional(WS + Suppress(',') + snp)) + RPAR
#############

fn = oneOf([f for f in language.functions if f not in gene_abundance_tags])
fn_app = (fn + LPAR + Group(identifier) + RPAR) | gene_abundance_app

list_fn = oneOf(language.lists + ['complexAbundance'])
list_fn_app = (
    (list_fn + LPAR + Group(identifier) + RPAR) |
    (list_fn + LPAR + (OneOrMore(Group(fn_app) + Suppress(',') + WS) +
                            Group(fn_app)) + RPAR)
)

activity = oneOf(language.activities)
activity_app = (activity + LPAR + Group(fn_app | list_fn_app) + RPAR)

subject = activity_app | fn_app | list_fn_app

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

statement = simple_statement | nested_statement #| subject


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
        if self.namespaces is None:
            return statement.parseString(s).asList()
        raise NotImplementedError()
