# -*- coding: utf-8 -*-

"""
BEL language parameters
"""

import logging

from pyparsing import *

from .parse_exceptions import PlaceholderAminoAcidWarning

log = logging.getLogger('pybel')

document_keys = {
    'Authors': 'authors',
    'ContactInfo': 'contact',
    'Copyright': 'copyright',
    'Description': 'description',
    'Disclaimer': 'disclaimer',
    'Licenses': 'licenses',
    'Name': 'name',
    'Version': 'version'
}

inv_document_keys = {v: k for k, v in document_keys.items()}

activity_labels = {
    'catalyticActivity': 'CatalyticActivity',
    'cat': 'CatalyticActivity',
    'chaperoneActivity': 'ChaperoneActivity',
    'chap': 'ChaperoneActivity',
    'gtpBoundActivity': 'GTPBoundActivity',
    'gtp': 'GTPBoundActivity',
    'kinaseActivity': 'KinaseActivity',
    'kin': 'KinaseActivity',
    'peptidaseActivity': 'PeptidaseActivity',
    'pep': 'PeptidaseActivity',
    'phosphataseActivity': 'PhosphotaseActivity',
    'phos': 'PhosphotaseActivity',
    'ribosylationActivity': 'RibosylationActivity',
    'ribo': 'RibosylationActivity',
    'transcriptionalActivity': 'TranscriptionalActivity',
    'tscript': 'TranscriptionalActivity',
    'transportActivity': 'TransportActivity',
    'tport': 'TransportActivity',
    'molecularActivity': 'MolecularActivity'
}

rev_activity_labels = {
    'CatalyticActivity': 'cat',
    'ChaperoneActivity': 'chap',
    'GTPBoundActivity': 'gtp',
    'KinaseActivity': 'kin',
    'PeptidaseActivity': 'pep',
    'PhosphotaseActivity': 'phos',
    'RibosylationActivity': 'ribo',
    'TranscriptionalActivity': 'tscript',
    'TransportActivity': 'tport',
    'MolecularActivity': 'molecularActivity'
}

# TODO fill out
activity_ns = {
    'CatalyticActivity': dict(namespace='GOMF', name='catalytic activity'),
    'ChaperoneActivity': dict(namespace='GOMF', name=''),
    'GTPBoundActivity': dict(namespace='GOMF', name='GTP binding'),
    'PeptidaseActivity': dict(namespace='GOMF', name='peptidase activity'),
    'PhosphotaseActivity': dict(namespace='GOMF', name=''),
    'RibosylationActivity': dict(namespace='GOMF', name=''),
    'TranscriptionalActivity': dict(namespace='GOMF', name='nucleic acid binding transcription factor activity'),
    'TransportActivity': dict(namespace='GOMF', name='transporter activity')
}

activities = list(activity_labels.keys())

ABUNDANCE = 'Abundance'
GENE = 'Gene'
MIRNA = 'miRNA'
PROTEIN = 'Protein'
RNA = 'RNA'
BIOPROCESS = 'BiologicalProcess'
PATHOLOGY = 'Pathology'
COMPOSITE = 'Composite'
COMPLEX = 'Complex'

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

#: See https://wiki.openbel.org/display/BELNA/Assignment+of+Encoding+%28Allowed+Functions%29+for+BEL+Namespaces
value_map = {
    'G': {GENE},
    'R': {RNA, MIRNA},
    'P': {PROTEIN},
    'M': {MIRNA},
    'A': {ABUNDANCE, RNA, MIRNA, PROTEIN, GENE, COMPLEX},
    'B': {PATHOLOGY, BIOPROCESS},
    'O': {PATHOLOGY},
    'C': {COMPLEX}
}

# rev_value_map = {v: k for k, v in value_map.items()}

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
aa_placeholder = Keyword('X')


def handle_aa_placeholder(s, l, tokens):
    raise PlaceholderAminoAcidWarning('Placeholder amino acid X found')


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

#: dictionary of default protein modifications to their preferred value
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
    'polyubiquitination': 'UbPoly'
}

#: dictionary of legacy (BEL 1.0) default namespace protein modifications to their BEL 2.0 preferred value
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
}

gmod_namespace = {
    'methylation': 'Me',
    'Me': 'Me',
    'M': 'Me'
}

unqualified_edges = [
    'hasReactant',
    'hasProduct',
    'hasComponent',
    'hasVariant',
    'transcribedTo',
    'translatedTo'
]

unqualified_edge_code = {relation: (-1 - i) for i, relation in enumerate(unqualified_edges)}
