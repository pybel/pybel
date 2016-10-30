# -*- coding: utf-8 -*-

"""
BEL language parameters
"""

import logging

from pyparsing import *

from .parse_exceptions import PlaceholderAminoAcidException

log = logging.getLogger('pybel')

document_keys = {
    'Authors',
    'ContactInfo',
    'Copyright',
    'Description',
    'Disclaimer',
    'Licenses',
    'Name',
    'Version'
}

activity_labels = {
    'catalyticActivity': 'CatalyticActivity',
    'cat': 'CatalyticActivity',
    'chaperoneActivity': 'ChaperoneActivity',
    'chap': 'ChaperoneActivity',
    'gtpBoundActivity': 'GTPBoundActivity',
    'gtp': 'GTPBoungActivity',
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

abundance_labels = {
    'abundance': 'Abundance',
    'a': 'Abundance',
    'geneAbundance': 'Gene',
    'g': 'Gene',
    'microRNAAbundance': 'miRNA',
    'm': 'miRNA',
    'proteinAbundance': 'Protein',
    'p': 'Protein',
    'rnaAbundance': 'RNA',
    'r': 'RNA',
    'biologicalProcess': 'Process',
    'bp': 'Process',
    'pathology': 'Pathology',
    'path': 'Pathology'
}

rev_abundance_labels = {
    'Abundance': 'a',
    'Gene': 'g',
    'miRNA': 'm',
    'Protein': 'p',
    'RNA': 'r',
    'Process': 'bp',
    'Pathology': 'path',
    'Complex': 'complex'
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
aa_placeholder = Keyword('X')


def handle_aa_placeholder(s, l, tokens):
    raise PlaceholderAminoAcidException('Placeholder amino acid X found')


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

pmod_namespace = {
    'Ac': 'acetylation',
    'acetylation': 'acetylation',
    'ADPRib': 'ADPRib',
    'ADP-ribosylation': 'ADPRib',
    'adenosine diphosphoribosyl': 'ADPRib',
    'Farn': 'farnesylation',
    'farnesylation': 'farnesylation',
    'Gerger': 'geranylgeranylation',
    'geranylgeranylation': 'geranylgeranylation',
    'Glyco': 'glycosylation',
    'glycosylation': 'glycosylation',
    'Hy': 'hydroxylation',
    'hydroxylation': 'hydroxylation',
    'ISG': 'ISGylation',
    'ISGylation': 'ISGylation',
    'ISG15-protein conjugation': 'ISGylation',
    'Me': 'methylation',
    'methylation': 'methylation',
    'Me1': 'monomethylation',
    'monomethylation': 'monomethylation',
    'mono-methylation': 'monomethylation',
    'Me2': 'dimethylation',
    'dimethylation': 'dimethylation',
    'di-methylation': 'dimethylation',
    'Me3': 'trimethylation',
    'trimethylation': 'trimethylation',
    'tri-methylation': 'trimethylation',
    'Myr': 'myristoylation',
    'myristoylation': 'myristoylation',
    'Nedd': 'neddylation',
    'neddylation': 'neddylation',
    'NGlyco': 'NGlyco',
    'N-linked glycosylation': 'NGlyco',
    'NO': 'Nitrosylation',
    'Nitrosylation': 'Nitrosylation',
    'OGlyco': 'OGlyco',
    'O-linked glycosylation': 'OGlyco',
    'Palm': 'palmitoylation',
    'palmitoylation': 'palmitoylation',
    'Ph': 'phosphorylation',
    'phosphorylation': 'phosphorylation',
    'Sulf': 'sulfation',
    'sulfation': 'sulfation',
    'sulphation': 'sulfation',
    'sulfur addition': 'sulfation',
    'sulphur addition': 'sulfation',
    'sulfonation': 'sulfonation',
    'sulphonation': 'sulfonation',
    'Sumo': 'SUMOylation',
    'SUMOylation': 'SUMOylation',
    'Ub': 'ubiquitination',
    'ubiquitination': 'ubiquitination',
    'ubiquitinylation': 'ubiquitination',
    'ubiquitylation': 'ubiquitination',
    'UbK48': 'UbK48',
    'Lysine 48-linked polyubiquitination': 'UbK48',
    'UbK63': 'UbK63',
    'Lysine 63-linked polyubiquitination': 'UbK63',
    'UbMono': 'monoubiquitination',
    'monoubiquitination': 'monoubiquitination',
    'UbPoly': 'polyubiquitination',
    'polyubiquitination': 'polyubiquitination'
}

pmod_legacy_labels = {
    'P': 'phosphorylation',
    'A': 'acetylation',
    'F': 'farnesylation',
    'G': 'glycosylated',
    'H': 'hydroxylated',
    'M': 'methylation',
    'R': 'ADPRib',
    'S': 'SUMOylation',
    'U': 'ubiquitination',
}

relation_labels = {
    'pmod': 'ProteinModification',
    'proteinModification': 'ProteinModification'
}

variant_parent_dict = {
    'GeneVariant': 'Gene',
    'RNAVariant': 'RNA',
    'ProteinVariant': 'Protein'
}

# See https://wiki.openbel.org/display/BELNA/Assignment+of+Encoding+%28Allowed+Functions%29+for+BEL+Namespaces
value_map = {
    'G': 'Gene',
    'R': 'RNA',
    'P': 'Protein',
    'M': 'microRNA',
    'A': 'Abundance',
    'B': 'BiologicalProcess',
    'O': 'Pathology',
    'C': 'Complex'
}
