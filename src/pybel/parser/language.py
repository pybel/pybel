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
from ..dsl.utils import entity

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
    'cat': entity(namespace='GOMF', name='catalytic activity', identifier='GO:0003824'),
    'chap': entity(namespace='GOMF', name='protein binding involved in protein folding', identifier='GO:0044183'),
    'gtp': entity(namespace='GOMF', name='GTP binding', identifier='GO:0005525'),
    'kin': entity(namespace='GOMF', name='kinase activity', identifier='GO:0016301'),
    'pep': entity(namespace='GOMF', name='peptidase activity', identifier='GO:0008233'),
    'phos': entity(namespace='GOMF', name='phosphatase activity', identifier='GO:0016791'),
    'ribo': entity(namespace='GOMF', name='NAD(P)+-protein-arginine ADP-ribosyltransferase activity',
                   identifier='GO:0003956'),
    'tscript': entity(namespace='GOMF', name='nucleic acid binding transcription factor activity',
                      identifier='GO:0001071'),
    'tport': entity(namespace='GOMF', name='transporter activity', identifier='GO:0005215'),
    'molecularActivity': entity(namespace='GOMF', name='molecular_function', identifier='GO:0003674'),
    'gef': entity(namespace='GOMF', name='guanyl-nucleotide exchange factor activity', identifier='GO:0005085'),
    'gap': entity(namespace='GOMF', name='GTPase activating protein binding', identifier='GO:0032794'),
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
    MIRNA: entity(namespace='SBO', name='microRNA', identifier='SBO:0000316'),
    BIOPROCESS: entity(namespace='SBO', name='process', identifier='SBO:0000375'),
    GENE: entity(namespace='SBO', name='gene', identifier='SBO:0000243'),
    RNA: entity(namespace='SBO', name='messenger RNA', identifier='SBO:0000278'),
    COMPLEX: entity(namespace='SBO', name='protein complex', identifier='SBO:0000297'),
}

relation_sbo_mapping = {
    TRANSLATED_TO: entity(namespace='SBO', name='translation', identifier='SBO:0000184'),
    TRANSCRIBED_TO: entity(namespace='SBO', name='transcription', identifier='SBO:0000183'),
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

#: Use Gene Ontology children of GO_0006464: "cellular protein modification process"
pmod_mappings = {
    'Ac': {
        'synonyms': ['Ac', 'acetylation'],
        'xrefs': [
            entity(namespace='SBO', identifier='SBO:0000215', name='acetylation'),
            entity(namespace='GO', identifier='GO:0006473 ', name='protein acetylation'),
        ]
    },
    'ADPRib': {
        'synonyms': ['ADPRib', 'ADP-ribosylation', 'ADPRib', 'adenosine diphosphoribosyl'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0006471', name='protein ADP-ribosylation'),
        ]
    },
    'Farn': {
        'synonyms': ['Farn', 'farnesylation'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0018343', name='protein farnesylation'),
        ]
    },
    'Gerger': {
        'synonyms': ['Gerger', 'geranylgeranylation'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0018344', name='protein geranylgeranylation'),
        ]
    },
    'Glyco': {
        'synonyms': ['Glyco', 'glycosylation'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0006486', name='protein glycosylation'),
        ]
    },
    'Hy': {
        'synonyms': ['Hy' 'hydroxylation'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0018126', name='protein hydroxylation'),
        ]
    },
    'ISG': {
        'synonyms': ['ISG', 'ISGylation', 'ISG15-protein conjugation'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0032020', name='ISG15-protein conjugation'),
        ]
    },
    'Me': {
        'synonyms': ['Me', 'methylation'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0006479', name='protein methylation'),
        ]

    },
    'Me1': {
        'synonyms': ['Me1', 'monomethylation', 'mono-methylation'],
    },
    'Me2': {
        'synonyms': ['Me2', 'dimethylation', 'di-methylation'],
    },
    'Me3': {
        'synonyms': ['Me3', 'trimethylation', 'tri-methylation'],
    },
    'Myr': {
        'synonyms': ['Myr', 'myristoylation'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0018377', name='protein myristoylation'),
        ]
    },
    'Nedd': {
        'synonyms': ['Nedd', 'neddylation', 'RUB1-protein conjugation'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0045116', name='protein neddylation'),
        ]
    },
    'NGlyco': {
        'synonyms': ['NGlyco', 'N-linked glycosylation'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0006487', name='protein N-linked glycosylation'),
        ]
    },
    'NO': {
        'synonyms': ['NO', 'Nitrosylation'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0017014', name='protein nitrosylation'),
        ]
    },
    'Ox': {
        'synonyms': ["Ox", 'oxidation'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0018158', name='protein oxidation'),
        ]
    },
    'OGlyco': {
        'synonyms': ['OGlyco', 'O-linked glycosylation'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0006493', name='protein O-linked glycosylation'),
        ]
    },
    'Palm': {
        'synonyms': ['Palm', 'palmitoylation'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0018345', name='protein palmitoylation'),
        ]
    },
    'Ph': {
        'synonyms': ['Ph', 'phosphorylation'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0006468', name='protein phosphorylation'),
        ]
    },
    'Sulf': {
        'synonyms': ['Sulf', 'sulfation', 'sulphation', 'sulfur addition', 'sulphur addition'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0006477', name='protein sulfation'),
        ]
    },
    'sulfonation': {
        'synonyms': ['sulfonation', 'sulphonation'],
        'xrefs': [
            entity(namespace='MOP', identifier='MOP:0000559', name='sulfonation '),
        ]
    },
    'Sumo': {
        'synonyms': ['Sumo', 'SUMOylation'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0016925', name='protein sumoylation'),
        ]
    },
    'Ub': {
        'synonyms': ['Ub', 'ubiquitination', 'ubiquitinylation', 'ubiquitylation'],
        'xrefs': [
            entity(namespace='SBO', identifier='SBO:0000224', name='ubiquitination'),
            entity(namespace='GO', identifier='GO:0016567', name='protein ubiquitination')
        ]
    },
    'UbK48': {
        'synonyms': ['UbK48', 'Lysine 48-linked polyubiquitination'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0070936', name='protein K48-linked ubiquitination'),
        ]
    },
    'UbK63': {
        'synonyms': ['UbK63', 'Lysine 63-linked polyubiquitination'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0070534', name='protein K63-linked ubiquitination'),
        ]
    },
    'UbMono': {
        'synonyms': ['UbMono', 'monoubiquitination'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0006513', name='protein monoubiquitination'),
        ]
    },
    'UbPoly': {
        'synonyms': ['UbPoly', 'polyubiquitination'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0000209', name='protein polyubiquitination'),
        ]
    },
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
    'O': 'Ox'
}

#: A dictionary of default gene modifications. This is a PyBEL variant to the BEL specification.
gmod_namespace = {
    'methylation': 'Me',
    'Me': 'Me',
    'M': 'Me'
}

#: Use Gene Ontology children of GO_0006304: "DNA modification"
gmod_mappings = {
    'Me': {
        'synonyms': ['Me', 'M', 'methylation'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0006306', name='DNA methylation'),
        ]
    },
    'ADPRib': {
        'synonyms': ['ADPRib'],
        'xrefs': [
            entity(namespace='GO', identifier='GO:0030592', name='DNA ADP-ribosylation'),
        ]
    }
}
