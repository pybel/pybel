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

functions = list(abundance_labels.keys())

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

# Protein Modification O is not defined by BEL Language v. 1.0
pmod_parameters_A = ['P', 'A', 'F', 'G', 'H', 'M', 'R', 'S', 'U', 'O']

# TODO add other BEL common namespaces
