# -*- coding: utf-8 -*-

"""
BEL language parameters
"""

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
    'tport': 'TransportActivity'
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
    'X': 'X'
}

dna_nucleotide_chars = ['A', 'T', 'C', 'G']
rna_nucleotide_chars = ['a', 'u', 'c', 'g']

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

# TODO add other BEL common namespaces
labels = {}
labels.update(abundance_labels)
labels.update(activity_labels)
