# -*- coding: utf-8 -*-

"""
BEL Language
------------

This module contains mappings between PyBEL's internal constants and BEL language keywords
"""

import logging

from pyparsing import *

from .parse_exceptions import PlaceholderAminoAcidWarning
from ..constants import *

log = logging.getLogger(__name__)

#: A dictionary of activity labels used in the ma() function in activity(p(X), ma(Y))
activity_labels = {
    'catalyticActivity': 'cat',
    'cat': 'cat',
    'chaperoneActivity': 'chap',
    'chap': 'chap',
    'gtpBoundActivity': 'gtp',
    'gtp': 'gtp',
    'kinaseActivity': 'kin',
    'kin': 'kin',
    'peptidaseActivity': 'pep',
    'pep': 'pep',
    'phosphataseActivity': 'phos',
    'phos': 'phos',
    'ribosylationActivity': 'ribo',
    'ribo': 'ribo',
    'transcriptionalActivity': 'tscript',
    'tscript': 'tscript',
    'transportActivity': 'tport',
    'tport': 'tport',
    'molecularActivity': 'molecularActivity',

    # Added by PyBEL
    'guanineNucleotideExchangeFactorActivity': 'gef',
    'gef': 'gef',
    'gtpaseActivatingProteinActivity': 'gap',
    'gap': 'gap',
}

#: Maps the default BEL molecular activities to Gene Ontology Molecular Functions
activity_go_mapping = {
    'cat': {NAMESPACE: 'GOMF', NAME: 'catalytic activity', ID: 'GO:0003824'},
    'chap': {NAMESPACE: 'GOMF', NAME: 'protein binding involved in protein folding', ID: 'GO:0044183'},
    'gtp': {NAMESPACE: 'GOMF', NAME: 'GTP binding', ID: 'GO:0005525'},
    'kin': {NAMESPACE: 'GOMF', NAME: 'kinase activity', ID: 'GO:0016301'},
    'pep': {NAMESPACE: 'GOMF', NAME: 'peptidase activity', ID: 'GO:0008233'},
    'phos': {NAMESPACE: 'GOMF', NAME: 'phosphatase activity', ID: 'GO:0016791'},
    'ribo': {NAMESPACE: 'GOMF', NAME: 'NAD(P)+-protein-arginine ADP-ribosyltransferase activity', ID: 'GO:0003956'},
    'tscript': {NAMESPACE: 'GOMF', NAME: 'nucleic acid binding transcription factor activity', ID: 'GO:0001071'},
    'tport': {NAMESPACE: 'GOMF', NAME: 'transporter activity', ID: 'GO:0005215'},
    'molecularActivity': {NAMESPACE: 'GOMF', NAME: 'molecular_function', ID: 'GO:0003674'},
    'gef': {NAMESPACE: 'GOMF', NAME: 'guanyl-nucleotide exchange factor activity', ID: 'GO:0005085'},
    'gap': {NAMESPACE: 'GOMF', NAME: 'GTPase activating protein binding', ID: 'GO:0032794'}
}

activities = list(activity_labels.keys())

#: Provides a mapping from BEL terms to PyBEL internal constants
abundance_labels = {
    'abundance': ABUNDANCE,
    'a': ABUNDANCE,
    'geneAbundance': GENE,
    'g': GENE,
    'microRNAAbundance': MIRNA,
    'm': MIRNA,
    'proteinAbundance': PROTEIN,
    'p': PROTEIN,
    'rnaAbundance': RNA,
    'r': RNA,
    'biologicalProcess': BIOPROCESS,
    'bp': BIOPROCESS,
    'pathology': PATHOLOGY,
    'path': PATHOLOGY,
    'composite': COMPOSITE,
    'compositeAbundance': COMPOSITE,
    'complex': COMPLEX,
    'complexAbundance': COMPLEX
}

rev_abundance_labels = {
    ABUNDANCE: 'a',
    GENE: 'g',
    MIRNA: 'm',
    PROTEIN: 'p',
    RNA: 'r',
    BIOPROCESS: 'bp',
    PATHOLOGY: 'path',
    COMPLEX: 'complex',
    COMPOSITE: 'composite'
}

#: Maps the BEL abundance types to the Systems Biology Ontology
abundance_sbo_mapping = {
    MIRNA: {NAMESPACE: 'SBO', NAME:'microRNA', ID:'SBO:0000316'},
    BIOPROCESS: {NAMESPACE: 'SBO', NAME:'process', ID:'SBO:0000375'},
    GENE: {NAMESPACE: 'SBO', NAME:'gene', ID:'SBO:0000243'},
    RNA: {NAMESPACE: 'SBO', NAME:'messenger RNA', ID:'SBO:0000278'},
    COMPLEX: {NAMESPACE: 'SBO', NAME:'protein complex', ID:'SBO:0000297'},
}

relation_sbo_mapping = {
    TRANSLATED_TO: {NAMESPACE: 'SBO', NAME:'translation', ID:'SBO:0000184'},
    TRANSCRIBED_TO: {NAMESPACE: 'SBO', NAME:'transcription', ID:'SBO:0000183'},
}

amino_acid_dict = {
    'A': 'Ala',
    'R': 'Arg',
    'N': 'Asn',
    'D': 'Asp',
    'C': 'Cys',
    'E': 'Glu',
    'Q': 'Gln',
    'G': 'Gly',
    'H': 'His',
    'I': 'Ile',
    'L': 'Leu',
    'K': 'Lys',
    'M': 'Met',
    'F': 'Phe',
    'P': 'Pro',
    'S': 'Ser',
    'T': 'Thr',
    'W': 'Trp',
    'Y': 'Tyr',
    'V': 'Val',
}

aa_single = oneOf(list(amino_acid_dict.keys()))
aa_single.setParseAction(lambda s, l, t: [amino_acid_dict[t[0]]])

aa_triple = oneOf(list(amino_acid_dict.values()))

#: In biological literature, the X is used to denote a truncation. Text mining efforts often encode X as an amino
#: acid, for which we will throw an error using :func:`handle_aa_placeholder`
aa_placeholder = Keyword('X')


def handle_aa_placeholder(line, position, tokens):
    """Raises an exception when encountering a placeholder amino acid, ``X``"""
    raise PlaceholderAminoAcidWarning(-1, line, position, tokens[0])


aa_placeholder.setParseAction(handle_aa_placeholder)

amino_acid = MatchFirst([aa_triple, aa_single, aa_placeholder])

dna_nucleotide_labels = {
    'A': 'Adenine',
    'T': 'Thymine',
    'C': 'Cytosine',
    'G': 'Guanine'
}

dna_nucleotide = oneOf(list(dna_nucleotide_labels.keys()))

rna_nucleotide_labels = {
    'a': 'adenine',
    'u': 'uracil',
    'c': 'cytosine',
    'g': 'guanine'
}

rna_nucleotide = oneOf(list(rna_nucleotide_labels.keys()))

#: A dictionary of default protein modifications to their preferred value
pmod_namespace = {
    'Ac': 'Ac',
    'acetylation': 'Ac',
    'ADPRib': 'ADPRib',
    'ADP-ribosylation': 'ADPRib',
    'adenosine diphosphoribosyl': 'ADPRib',
    'Farn': 'Farn',
    'farnesylation': 'Farn',
    'Gerger': 'Gerger',
    'geranylgeranylation': 'Gerger',
    'Glyco': 'Glyco',
    'glycosylation': 'Glyco',
    'Hy': 'Hy',
    'hydroxylation': 'Hy',
    'ISG': 'ISG',
    'ISGylation': 'ISG',
    'ISG15-protein conjugation': 'ISG',
    'Me': 'Me',
    'methylation': 'Me',
    'Me1': 'Me1',
    'monomethylation': 'Me1',
    'mono-methylation': 'Me1',
    'Me2': 'Me2',
    'dimethylation': 'Me2',
    'di-methylation': 'Me2',
    'Me3': 'Me3',
    'trimethylation': 'Me3',
    'tri-methylation': 'Me3',
    'Myr': 'Myr',
    'myristoylation': 'Myr',
    'Nedd': 'Nedd',
    'neddylation': 'Nedd',
    'NGlyco': 'NGlyco',
    'N-linked glycosylation': 'NGlyco',
    'NO': 'NO',
    'Nitrosylation': 'NO',
    'OGlyco': 'OGlyco',
    'O-linked glycosylation': 'OGlyco',
    'Palm': 'Palm',
    'palmitoylation': 'Palm',
    'Ph': 'Ph',
    'phosphorylation': 'Ph',
    'Sulf': 'Sulf',
    'sulfation': 'Sulf',
    'sulphation': 'Sulf',
    'sulfur addition': 'Sulf',
    'sulphur addition': 'Sulf',
    'sulfonation': 'sulfonation',
    'sulphonation': 'sulfonation',
    'Sumo': 'Sumo',
    'SUMOylation': 'Sumo',
    'Ub': 'Ub',
    'ubiquitination': 'Ub',
    'ubiquitinylation': 'Ub',
    'ubiquitylation': 'Ub',
    'UbK48': 'UbK48',
    'Lysine 48-linked polyubiquitination': 'UbK48',
    'UbK63': 'UbK63',
    'Lysine 63-linked polyubiquitination': 'UbK63',
    'UbMono': 'UbMono',
    'monoubiquitination': 'UbMono',
    'UbPoly': 'UbPoly',
    'polyubiquitination': 'UbPoly',

    # PyBEL Variants
    'Ox': "Ox",
    'oxidation': 'Ox',
}

#: A dictionary of legacy (BEL 1.0) default namespace protein modifications to their BEL 2.0 preferred value
pmod_legacy_labels = {
    'P': 'Ph',
    'A': 'Ac',
    'F': 'Farn',
    'G': 'Glyco',
    'H': 'Hy',
    'M': 'Me',
    'R': 'ADPRib',
    'S': 'Sumo',
    'U': 'Ub',

    # PyBEL Variants
    'O': 'Ox'
}

#: A dictionary of default gene modifications. This is a PyBEL variant to the BEL specification.
gmod_namespace = {
    'methylation': 'Me',
    'Me': 'Me',
    'M': 'Me'
}
