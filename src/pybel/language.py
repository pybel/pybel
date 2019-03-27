# -*- coding: utf-8 -*-

"""Language constants for BEL.

This module contains mappings between PyBEL's internal constants and BEL language keywords.
"""

import logging
from typing import Optional

from .constants import (
    ABUNDANCE, BEL_DEFAULT_NAMESPACE, BIOPROCESS, CELL_SURFACE, COMPLEX, COMPOSITE, EXTRACELLULAR, GENE, IDENTIFIER,
    INTRACELLULAR, MIRNA, NAME, NAMESPACE, PATHOLOGY, PROTEIN, RNA, TRANSCRIBED_TO, TRANSLATED_TO,
)
from .utils import ensure_quotes

log = logging.getLogger(__name__)


class Entity(dict):
    """Represents a named entity with a namespace and name/identifier."""

    def __init__(self, namespace: str, name: Optional[str] = None, identifier: Optional[str] = None) -> None:
        """Create a dictionary representing a reference to an entity.

        :param namespace: The namespace to which the entity belongs
        :param name: The name of the entity
        :param identifier: The identifier of the entity in the namespace
        """
        if name is None and identifier is None:
            raise ValueError('cannot create an entity with neither a name nor identifier')

        super().__init__({
            NAMESPACE: namespace,
        })

        if name is not None:
            self[NAME] = name

        if identifier is not None:
            self[IDENTIFIER] = identifier

    def __str__(self):  # noqa: D105
        if self[NAMESPACE] == BEL_DEFAULT_NAMESPACE:
            return self[NAME]

        return '{}:{}'.format(self[NAMESPACE], ensure_quotes(self[NAME]))


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
activity_mapping = {
    'cat': Entity(namespace='GO', name='catalytic activity', identifier='GO:0003824'),
    'chap': Entity(namespace='GO', name='protein binding involved in protein folding', identifier='GO:0044183'),
    'gtp': Entity(namespace='GO', name='GTP binding', identifier='GO:0005525'),
    'kin': Entity(namespace='GO', name='kinase activity', identifier='GO:0016301'),
    'pep': Entity(namespace='GO', name='peptidase activity', identifier='GO:0008233'),
    'phos': Entity(namespace='GO', name='phosphatase activity', identifier='GO:0016791'),
    'ribo': Entity(namespace='GO', name='NAD(P)+-protein-arginine ADP-ribosyltransferase activity',
                   identifier='GO:0003956'),
    'tscript': Entity(namespace='GO', name='nucleic acid binding transcription factor activity',
                      identifier='GO:0001071'),
    'tport': Entity(namespace='GO', name='transporter activity', identifier='GO:0005215'),
    'molecularActivity': Entity(namespace='GO', name='molecular_function', identifier='GO:0003674'),
    'gef': Entity(namespace='GO', name='guanyl-nucleotide exchange factor activity', identifier='GO:0005085'),
    'gap': Entity(namespace='GO', name='GTPase activating protein binding', identifier='GO:0032794'),
}

activities = list(activity_labels.keys())

cytoplasm = Entity(name='cytoplasm', namespace='GO', identifier='GO:0005737')
nucleus = Entity(name='nucleus', namespace='GO', identifier='GO:0005634')

#: Maps the default BEL cellular components to Gene Ontology Cellular Components
compartment_mapping = {
    INTRACELLULAR: Entity(name='intracellular', namespace='GO', identifier='GO:0005622'),
    EXTRACELLULAR: Entity(name='extracellular space', namespace='GO', identifier='GO:0005615'),
    CELL_SURFACE: Entity(name='cell surface', namespace='GO', identifier='GO:0009986'),
    'cytoplasm': cytoplasm,
    'nucleus': nucleus,
}

compartments = list(compartment_mapping)

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

#: Maps the BEL abundance types to the Systems Biology Ontology
abundance_sbo_mapping = {
    MIRNA: Entity(namespace='SBO', name='microRNA', identifier='SBO:0000316'),
    BIOPROCESS: Entity(namespace='SBO', name='process', identifier='SBO:0000375'),
    GENE: Entity(namespace='SBO', name='gene', identifier='SBO:0000243'),
    RNA: Entity(namespace='SBO', name='messenger RNA', identifier='SBO:0000278'),
    COMPLEX: Entity(namespace='SBO', name='protein complex', identifier='SBO:0000297'),
    PATHOLOGY: Entity(namespace='SBO', name='phenotype', identifier='SBO:0000358'),
}

relation_sbo_mapping = {
    TRANSLATED_TO: Entity(namespace='SBO', name='translation', identifier='SBO:0000184'),
    TRANSCRIBED_TO: Entity(namespace='SBO', name='transcription', identifier='SBO:0000183'),
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

dna_nucleotide_labels = {
    'A': 'Adenine',
    'T': 'Thymine',
    'C': 'Cytosine',
    'G': 'Guanine'
}

rna_nucleotide_labels = {
    'a': 'adenine',
    'u': 'uracil',
    'c': 'cytosine',
    'g': 'guanine'
}

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
            Entity(namespace='SBO', identifier='SBO:0000215', name='acetylation'),
            Entity(namespace='GO', identifier='GO:0006473', name='protein acetylation'),
            Entity(namespace='MOD', identifier='MOD:00394'),
        ]
    },
    'ADPRib': {
        'synonyms': ['ADPRib', 'ADP-ribosylation', 'ADPRib', 'ADP-rybosylation', 'adenosine diphosphoribosyl'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0006471', name='protein ADP-ribosylation'),
            Entity(namespace='MOD', identifier='MOD:00752'),
        ]
    },
    'Farn': {
        'synonyms': ['Farn', 'farnesylation'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0018343', name='protein farnesylation'),
            Entity(namespace='MOD', identifier='MOD:00437'),
        ]
    },
    'Gerger': {
        'synonyms': ['Gerger', 'geranylgeranylation'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0018344', name='protein geranylgeranylation'),
            Entity(namespace='MOD', identifier='MOD:00441'),
        ]
    },
    'Glyco': {
        'synonyms': ['Glyco', 'glycosylation'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0006486', name='protein glycosylation'),
            Entity(namespace='MOD', identifier='MOD:00693'),
        ]
    },
    'Hy': {
        'synonyms': ['Hy' 'hydroxylation'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0018126', name='protein hydroxylation'),
            Entity(namespace='MOD', identifier='MOD:00677'),
        ]
    },
    'ISG': {
        'synonyms': ['ISG', 'ISGylation', 'ISG15-protein conjugation'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0032020', name='ISG15-protein conjugation'),
        ]
    },
    'Me': {
        'synonyms': ['Me', 'methylation'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0006479', name='protein methylation'),
            Entity(namespace='MOD', identifier='MOD:00427'),
        ]

    },
    'Me1': {
        'synonyms': ['Me1', 'monomethylation', 'mono-methylation'],
        'xrefs': [
            Entity(namespace='MOD', identifier='MOD:00599', name='monomethylated residue'),
        ]
    },
    'Me2': {
        'synonyms': ['Me2', 'dimethylation', 'di-methylation'],
        'xrefs': [
            Entity(namespace='MOD', identifier='MOD:00429', name='dimethylated residue'),
        ]
    },
    'Me3': {
        'synonyms': ['Me3', 'trimethylation', 'tri-methylation'],
        'xrefs': [
            Entity(namespace='MOD', identifier='MOD:00430', name='trimethylated residue'),
        ]
    },
    'Myr': {
        'synonyms': ['Myr', 'myristoylation'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0018377', name='protein myristoylation'),
            Entity(namespace='MOD', identifier='MOD:00438'),
        ]
    },
    'Nedd': {
        'synonyms': ['Nedd', 'neddylation', 'RUB1-protein conjugation'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0045116', name='protein neddylation'),
            Entity(namespace='MOD', identifier='MOD:01150'),
        ]
    },
    'NGlyco': {
        'synonyms': ['NGlyco', 'N-linked glycosylation'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0006487', name='protein N-linked glycosylation'),
            Entity(namespace='MOD', identifier='MOD:00006'),
        ]
    },
    'NO': {
        'synonyms': ['NO', 'Nitrosylation'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0017014', name='protein nitrosylation'),
        ]
    },
    'Ox': {
        'synonyms': ["Ox", 'oxidation'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0018158', name='protein oxidation'),
        ]
    },
    'OGlyco': {
        'synonyms': ['OGlyco', 'O-linked glycosylation'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0006493', name='protein O-linked glycosylation'),
            Entity(namespace='MOD', identifier='MOD:00396'),
        ]
    },
    'Palm': {
        'synonyms': ['Palm', 'palmitoylation'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0018345', name='protein palmitoylation'),
            Entity(namespace='MOD', identifier='MOD:00440'),
        ]
    },
    'Ph': {
        'synonyms': ['Ph', 'phosphorylation'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0006468', name='protein phosphorylation'),
            Entity(namespace='MOD', identifier='MOD:00696'),
        ]
    },
    'Sulf': {
        'synonyms': ['Sulf', 'sulfation', 'sulphation', 'sulfur addition', 'sulphur addition'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0006477', name='protein sulfation'),
            Entity(namespace='MOD', identifier='MOD:00695'),
        ]
    },
    'sulfonation': {
        'synonyms': ['sulfonation', 'sulphonation'],
        'xrefs': [
            Entity(namespace='MOP', identifier='MOP:0000559', name='sulfonation'),
        ]
    },
    'Sumo': {
        'synonyms': ['Sumo', 'SUMOylation', 'Sumoylation'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0016925', name='protein sumoylation'),
            Entity(namespace='MOD', identifier='MOD:01149'),
        ]
    },
    'Ub': {
        'synonyms': ['Ub', 'ubiquitination', 'ubiquitinylation', 'ubiquitylation'],
        'xrefs': [
            Entity(namespace='SBO', identifier='SBO:0000224', name='ubiquitination'),
            Entity(namespace='GO', identifier='GO:0016567', name='protein ubiquitination'),
            Entity(namespace='MOD', identifier='MOD:01148'),
        ]
    },
    'UbK48': {
        'synonyms': ['UbK48', 'Lysine 48-linked polyubiquitination'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0070936', name='protein K48-linked ubiquitination'),
        ]
    },
    'UbK63': {
        'synonyms': ['UbK63', 'Lysine 63-linked polyubiquitination'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0070534', name='protein K63-linked ubiquitination'),
        ]
    },
    'UbMono': {
        'synonyms': ['UbMono', 'monoubiquitination'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0006513', name='protein monoubiquitination'),
        ]
    },
    'UbPoly': {
        'synonyms': ['UbPoly', 'polyubiquitination'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0000209', name='protein polyubiquitination'),
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
    'O': 'Ox',
}

#: A dictionary of default gene modifications. This is a PyBEL variant to the BEL specification.
gmod_namespace = {
    'methylation': 'Me',
    'Me': 'Me',
    'M': 'Me',
}

#: Use Gene Ontology children of GO_0006304: "DNA modification"
gmod_mappings = {
    'Me': {
        'synonyms': ['Me', 'M', 'methylation'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0006306', name='DNA methylation'),
        ]
    },
    'ADPRib': {
        'synonyms': ['ADPRib'],
        'xrefs': [
            Entity(namespace='GO', identifier='GO:0030592', name='DNA ADP-ribosylation'),
        ]
    }
}

BEL_DEFAULT_NAMESPACE_VERSION = '2.1.1'
BEL_DEFAULT_NAMESPACE_URL = 'http://openbel.org/2.1.1.belns'  # just needs something unique... will change later
