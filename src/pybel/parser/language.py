# -*- coding: utf-8 -*-

"""
BEL language parameters
"""

import logging

from pyparsing import *

from .parse_exceptions import PlaceholderAminoAcidException

log = logging.getLogger('pybel')

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
    'Y': 'Try',
    'V': 'Val',
}

aa_single = oneOf(list(amino_acid_dict.keys()))
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

pmod_legacy_labels = {
    'P': 'phosphorylated',
    'A': 'acetylated',
    'F': 'farnesylated',
    'G': 'glycosylated',
    'H': 'hydroxylated',
    'M': 'methylated',
    'R': 'ribosylated',
    'S': 'sumoylated',
    'U': 'ubiquitinated',
}

pmod_namespace = {
    'Ac',
    'acetylation',
    'ADPRib',
    'ADP-ribosylation',
    'adenosine diphosphoribosyl',
    'Farn',
    'farnesylation',
    'Gerger',
    'geranylgeranylation',
    'Glyco',
    'glycosylation',
    'Hy',
    'hydroxylation',
    'ISG',
    'ISGylation',
    'ISG15-protein conjugation',
    'Me',
    'methylation',
    'Me1',
    'monomethylation',
    'mono-methylation',
    'Me2',
    'dimethylation',
    'di-methylation',
    'Me3',
    'trimethylation',
    'tri-methylation',
    'Myr',
    'myristoylation',
    'Nedd',
    'neddylation',
    'NGlyco',
    'N-linked glycosylation',
    'NO',
    'Nitrosylation',
    'OGlyco',
    'O-linked glycosylation',
    'Palm',
    'palmitoylation',
    'Ph',
    'phosphorylation',
    'Sulf',
    'sulfation',
    'sulphation',
    'sulfur addition',
    'sulphur addition',
    'sulfonation',
    'sulphonation',
    'Sumo',
    'SUMOylation',
    'Ub',
    'ubiquitination',
    'ubiquitinylation',
    'ubiquitylation',
    'UbK48',
    'Lysine 48-linked polyubiquitination',
    'UbK63',
    'Lysine 63-linked polyubiquitination',
    'UbMono',
    'monoubiquitination',
    'UbPoly'
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
