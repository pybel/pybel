# -*- coding: utf-8 -*-

"""Language constants for BEL.

This module contains mappings between PyBEL's internal constants and BEL language keywords.
"""

import warnings
from typing import Optional

from .constants import (
    ABUNDANCE, BIOPROCESS, CELL_SURFACE, COMPLEX, COMPOSITE, EXTRACELLULAR, GENE, IDENTIFIER, INTRACELLULAR, MIRNA,
    NAME, NAMESPACE, PATHOLOGY, PROTEIN, RNA, TRANSCRIBED_TO, TRANSLATED_TO,
)
from .utils import ensure_quotes


class Entity(dict):
    """Represents a named entity with a namespace and name/identifier."""

    def __init__(
        self,
        *,
        namespace: str,
        name: Optional[str] = None,
        identifier: Optional[str] = None
    ) -> None:
        """Create a dictionary representing a reference to an entity.

        :param namespace: The namespace to which the entity belongs
        :param name: The name of the entity
        :param identifier: The identifier of the entity in the namespace
        """
        if name is None and identifier is None:
            raise ValueError('cannot create an entity with neither a name nor identifier')
        if not isinstance(namespace, str):
            raise TypeError('namespace should be a string: {}'.format(namespace))
        if not namespace:
            raise ValueError('namespace should be non-empty')

        super().__init__({
            NAMESPACE: namespace,
        })

        if name is not None:
            if not isinstance(name, str):
                raise TypeError('name should be a string: {}'.format(name))
            if not name:
                raise ValueError('name should be non-empty')
            self[NAME] = name

        if identifier is not None:
            if not isinstance(identifier, str):
                raise TypeError(f'identifier should be a string. Got {type(identifier)} {identifier}')
            if not identifier:
                raise ValueError('identifier should be non-empty')
            self[IDENTIFIER] = identifier

    @property
    def namespace(self) -> str:  # noqa: D401
        """The entity's namespace."""
        return self[NAMESPACE]

    @property
    def name(self) -> str:  # noqa: D401
        """The entity's name or label."""
        return self.get(NAME)

    @property
    def identifier(self) -> str:  # noqa: D401
        """The entity's identifier."""
        return self.get(IDENTIFIER)

    @property
    def curie(self) -> str:
        """Return this entity as a CURIE."""
        return '{}:{}'.format(
            self.namespace,
            ensure_quotes(self.identifier if self.identifier else self.name),
        )

    @property
    def obo(self) -> str:
        """Return this entity as an OBO-style CURIE."""
        return '{}:{} ! {}'.format(
            self.namespace,
            ensure_quotes(self.identifier),
            ensure_quotes(self.name),
        )

    def __str__(self):  # noqa: D105
        return self.obo if self.identifier and self.name else self.curie

    def __hash__(self) -> int:
        return hash((self.namespace, self.identifier, self.name))


text_location_labels = {
    'Abstract': Entity(namespace='iao', identifier='0000315', name='abstract'),
    'Review': Entity(namespace='iao', identifier='0000311', name='publication'),  # sue me
    'Results': Entity(namespace='iao', identifier='0000318', name='results section'),
    'Legend': Entity(namespace='sio', identifier='000468 ', name='legend'),
}

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
    'act': Entity(namespace='go', name='molecular function', identifier='0003674'),
    'cat': Entity(namespace='go', name='catalytic activity', identifier='0003824'),
    'chap': Entity(namespace='go', name='protein binding involved in protein folding', identifier='0044183'),
    'gtp': Entity(namespace='go', name='GTP binding', identifier='0005525'),
    'kin': Entity(namespace='go', name='kinase activity', identifier='0016301'),
    'pep': Entity(namespace='go', name='peptidase activity', identifier='0008233'),
    'phos': Entity(namespace='go', name='phosphatase activity', identifier='0016791'),
    'ribo': Entity(
        namespace='go', name='NAD(P)+-protein-arginine ADP-ribosyltransferase activity',
        identifier='0003956',
    ),
    'tscript': Entity(
        namespace='go', name='nucleic acid binding transcription factor activity',
        identifier='0001071',
    ),
    'tport': Entity(namespace='go', name='transporter activity', identifier='0005215'),
    'molecularActivity': Entity(namespace='go', name='molecular_function', identifier='0003674'),
    'gef': Entity(namespace='go', name='guanyl-nucleotide exchange factor activity', identifier='0005085'),
    'gap': Entity(namespace='go', name='GTPase activating protein binding', identifier='0032794'),
}

activities = list(activity_labels.keys())

cytoplasm = Entity(name='cytoplasm', namespace='go', identifier='0005737')
nucleus = Entity(name='nucleus', namespace='go', identifier='0005634')
intracellular = Entity(name='intracellular', namespace='go', identifier='0005622')
extracellular = Entity(name='extracellular space', namespace='go', identifier='0005615')
cell_surface = Entity(name='cell surface', namespace='go', identifier='0009986')

#: Maps the default BEL cellular components to Gene Ontology Cellular Components
compartment_mapping = {
    INTRACELLULAR: intracellular,
    EXTRACELLULAR: extracellular,
    CELL_SURFACE: cell_surface,
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
    'complexAbundance': COMPLEX,
}

#: Maps the BEL abundance types to the Systems Biology Ontology
abundance_sbo_mapping = {
    MIRNA: Entity(namespace='sbo', name='microRNA', identifier='0000316'),
    BIOPROCESS: Entity(namespace='sbo', name='process', identifier='0000375'),
    GENE: Entity(namespace='sbo', name='gene', identifier='0000243'),
    RNA: Entity(namespace='sbo', name='messenger RNA', identifier='0000278'),
    COMPLEX: Entity(namespace='sbo', name='protein complex', identifier='0000297'),
    PATHOLOGY: Entity(namespace='sbo', name='phenotype', identifier='0000358'),
}

relation_sbo_mapping = {
    TRANSLATED_TO: Entity(namespace='sbo', name='translation', identifier='0000184'),
    TRANSCRIBED_TO: Entity(namespace='sbo', name='transcription', identifier='0000183'),
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
    'G': 'Guanine',
}

rna_nucleotide_labels = {
    'a': 'adenine',
    'u': 'uracil',
    'c': 'cytosine',
    'g': 'guanine',
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

#: Use Gene Ontology children of go_0006464: "cellular protein modification process"
pmod_mappings = {
    'Ac': {
        'synonyms': ['Ac', 'acetylation'],
        'xrefs': [
            Entity(namespace='go', identifier='0006473', name='protein acetylation'),
            Entity(namespace='mod', identifier='00394', name='acetylated residue'),
            Entity(namespace='mop', identifier='0000030', name='acetylation'),
            Entity(namespace='sbo', identifier='0000215', name='acetylation'),
        ],
    },
    'ADPRib': {
        'synonyms': ['ADPRib', 'ADP-ribosylation', 'ADPRib', 'ADP-rybosylation', 'adenosine diphosphoribosyl'],
        'xrefs': [
            Entity(namespace='go', identifier='0006471', name='protein ADP-ribosylation'),
            Entity(
                namespace='mod', identifier='00752',
                name='adenosine diphosphoribosyl (ADP-ribosyl) modified residue',
            ),
            Entity(namespace='mop', identifier='0000220', name='adenosinediphosphoribosylation'),
        ],
    },
    'Farn': {
        'synonyms': ['Farn', 'farnesylation'],
        'xrefs': [
            Entity(namespace='go', identifier='0018343', name='protein farnesylation'),
            Entity(namespace='mod', identifier='00437', name='farnesylated residue'),
            Entity(namespace='mop', identifier='0000429', name='farnesylation'),
        ],
    },
    'Gerger': {
        'synonyms': ['Gerger', 'geranylgeranylation'],
        'xrefs': [
            Entity(namespace='go', identifier='0018344', name='protein geranylgeranylation'),
            Entity(namespace='mod', identifier='00441', name='geranylgeranylated residue '),
            Entity(namespace='mop', identifier='0000431', name='geranylgeranylation'),
        ],
    },
    'Glyco': {
        'synonyms': ['Glyco', 'glycosylation'],
        'xrefs': [
            Entity(namespace='go', identifier='0006486', name='protein glycosylation'),
            Entity(namespace='mod', identifier='00693', name='glycosylated residue'),
            Entity(namespace='mop', identifier='0000162', name='glycosylation'),
        ],
    },
    'Hy': {
        'synonyms': ['Hy' 'hydroxylation'],
        'xrefs': [
            Entity(namespace='go', identifier='0018126', name='protein hydroxylation'),
            Entity(namespace='mod', identifier='00677', name='hydroxylated residue'),
            Entity(namespace='mop', identifier='0000673', name='hydroxylation'),
        ],
    },
    'ISG': {
        'synonyms': ['ISG', 'ISGylation', 'ISG15-protein conjugation'],
        'xrefs': [
            Entity(namespace='go', identifier='0032020', name='ISG15-protein conjugation'),
        ],
        'activities': [
            Entity(namespace='go', identifier='0042296', name='ISG15 transferase activity'),
        ],
    },
    'Me': {
        'synonyms': ['Me', 'methylation'],
        'xrefs': [
            Entity(namespace='go', identifier='0006479', name='protein methylation'),
            Entity(namespace='mod', identifier='00427', name='methylated residue'),
        ],
    },
    'Me1': {
        'synonyms': ['Me1', 'monomethylation', 'mono-methylation'],
        'xrefs': [
            Entity(namespace='mod', identifier='00599', name='monomethylated residue'),
        ],
        'is_a': ['Me'],
    },
    'Me2': {
        'synonyms': ['Me2', 'dimethylation', 'di-methylation'],
        'xrefs': [
            Entity(namespace='mod', identifier='00429', name='dimethylated residue'),
        ],
        'is_a': ['Me'],
    },
    'Me3': {
        'synonyms': ['Me3', 'trimethylation', 'tri-methylation'],
        'xrefs': [
            Entity(namespace='mod', identifier='00430', name='trimethylated residue'),
        ],
        'is_a': ['Me'],
    },
    'Myr': {
        'synonyms': ['Myr', 'myristoylation'],
        'xrefs': [
            Entity(namespace='go', identifier='0018377', name='protein myristoylation'),
            Entity(namespace='mod', identifier='00438', name='myristoylated residue'),
        ],
    },
    'Nedd': {
        'synonyms': ['Nedd', 'neddylation', 'RUB1-protein conjugation'],
        'xrefs': [
            Entity(namespace='go', identifier='0045116', name='protein neddylation'),
            Entity(namespace='mod', identifier='01150', name='neddylated lysine'),
        ],
    },
    'NGlyco': {
        'synonyms': ['NGlyco', 'N-linked glycosylation'],
        'xrefs': [
            Entity(namespace='go', identifier='0006487', name='protein N-linked glycosylation'),
            Entity(namespace='mod', identifier='00006', name='N-glycosylated residue'),
            Entity(namespace='mop', identifier='0002162', name='N-glycosylation'),
        ],
        'is_a': ['Glyco'],
    },
    'NO': {
        'synonyms': ['NO', 'Nitrosylation'],
        'xrefs': [
            Entity(namespace='go', identifier='0017014', name='protein nitrosylation'),
        ],
    },
    'Ox': {
        'synonyms': ["Ox", 'oxidation'],
        'xrefs': [
            Entity(namespace='go', identifier='0018158', name='protein oxidation'),
        ],
    },
    'OGlyco': {
        'synonyms': ['OGlyco', 'O-linked glycosylation'],
        'xrefs': [
            Entity(namespace='go', identifier='0006493', name='protein O-linked glycosylation'),
            Entity(namespace='mod', identifier='00396', name='O-glycosylated residue'),
            Entity(namespace='mop', identifier='0003162', name='O-glycosylation'),
        ],
        'is_a': ['Glyco'],
    },
    'Palm': {
        'synonyms': ['Palm', 'palmitoylation'],
        'xrefs': [
            Entity(namespace='go', identifier='0018345', name='protein palmitoylation'),
            Entity(namespace='mod', identifier='00440', name='palmitoylated residue'),
        ],
    },
    'Ph': {
        'synonyms': ['Ph', 'phosphorylation'],
        'xrefs': [
            Entity(namespace='go', identifier='0006468', name='protein phosphorylation'),
            Entity(namespace='mod', identifier='00696'),
        ],
    },
    'Sulf': {
        'synonyms': [
            'Sulf', 'sulfation', 'sulphation', 'sulfur addition', 'sulphur addition', 'sulfonation',
            'sulphonation',
        ],
        'xrefs': [
            Entity(namespace='go', identifier='0006477', name='protein sulfation'),
            Entity(namespace='mod', identifier='00695', name='sulfated residue'),
            Entity(namespace='mop', identifier='0000559', name='sulfonation'),
        ],
        'target': [
            Entity(namespace='chebi', identifier='29922', name='sulfo group'),
        ],
    },
    'Sumo': {
        'synonyms': ['Sumo', 'SUMOylation', 'Sumoylation'],
        'xrefs': [
            Entity(namespace='go', identifier='0016925', name='protein sumoylation'),
            Entity(namespace='mod', identifier='01149', name='sumoylated lysine'),
        ],
        'activities': [
            Entity(namespace='go', identifier='0019789', name='SUMO transferase activity'),
        ],
    },
    'Ub': {
        'synonyms': ['Ub', 'ubiquitination', 'ubiquitinylation', 'ubiquitylation'],
        'xrefs': [
            Entity(namespace='go', identifier='0016567', name='protein ubiquitination'),
            Entity(namespace='mod', identifier='01148', name='ubiquitinylated lysine'),
            Entity(namespace='sbo', identifier='0000224', name='ubiquitination'),
        ],
    },
    'UbK48': {
        'synonyms': ['UbK48', 'Lysine 48-linked polyubiquitination'],
        'xrefs': [
            Entity(namespace='go', identifier='0070936', name='protein K48-linked ubiquitination'),
        ],
    },
    'UbK63': {
        'synonyms': ['UbK63', 'Lysine 63-linked polyubiquitination'],
        'xrefs': [
            Entity(namespace='go', identifier='0070534', name='protein K63-linked ubiquitination'),
        ],
    },
    'UbMono': {
        'synonyms': ['UbMono', 'monoubiquitination'],
        'xrefs': [
            Entity(namespace='go', identifier='0006513', name='protein monoubiquitination'),
        ],
    },
    'UbPoly': {
        'synonyms': ['UbPoly', 'polyubiquitination'],
        'xrefs': [
            Entity(namespace='go', identifier='0000209', name='protein polyubiquitination'),
        ],
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
    'ADPRib': 'ADPRib',
}

#: Use Gene Ontology children of go:0006304 ! "DNA modification"
gmod_mappings = {
    'Me': {
        'synonyms': ['Me', 'M', 'methylation'],
        'xrefs': [
            Entity(namespace='go', identifier='0006306', name='DNA methylation'),
        ],
    },
    'ADPRib': {
        'synonyms': ['ADPRib'],
        'xrefs': [
            Entity(namespace='go', identifier='0030592', name='DNA ADP-ribosylation'),
        ],
    },
}


class CitationDict(Entity):
    """A dictionary describing a citation."""

    def __init__(self, namespace: str, identifier: str, *, name: Optional[str] = None, **kwargs):
        super().__init__(namespace=namespace, identifier=identifier, name=name)
        self.update(kwargs)


def citation_dict(
    *,
    namespace: Optional[str] = None,
    db: Optional[str] = None,
    identifier: Optional[str] = None,
    db_id: Optional[str] = None,
    name: Optional[str] = None,
    **kwargs,
) -> CitationDict:
    """Make a citation dictionary."""
    if namespace and db:
        raise ValueError('can not specify both namespace and db')
    if identifier and db_id:
        raise ValueError('can not specify both identifier and db_id')
    if db:
        warnings.warn(
            'usage of keyword argument `db` in citation_dict() should be replaced with `namespace`. '
            'Will be removed in PyBEL 16.', DeprecationWarning,
        )
        namespace = db
    if db_id:
        warnings.warn(
            'usage of keyword argument `db_id` in citation_dict() should be replaced with `identifier`. '
            'Will be removed in PyBEL 16.', DeprecationWarning,
        )
        identifier = db_id

    return CitationDict(namespace=namespace, identifier=identifier, name=name, **kwargs)
