# -*- coding: utf-8 -*-

"""
PyBEL Constants
---------------

This module maintains the strings used throughout the PyBEL codebase to promote consistency.
"""

import os

SMALL_CORPUS_URL = 'http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel'
LARGE_CORPUS_URL = 'http://resource.belframework.org/belframework/1.0/knowledge/large_corpus.bel'

GOCC_LATEST = 'http://resources.openbel.org/belframework/20150611/namespace/go-cellular-component.belns'
GOCC_KEYWORD = 'GOCC'

PYBEL_CONNECTION_ENV = 'PYBEL_CONNECTION'

PYBEL_DIR = os.path.expanduser('~/.pybel')
if not os.path.exists(PYBEL_DIR):
    os.mkdir(PYBEL_DIR)

PYBEL_DATA_DIR = os.path.join(PYBEL_DIR, 'data')
if not os.path.exists(PYBEL_DATA_DIR):
    os.mkdir(PYBEL_DATA_DIR)

DEFAULT_CACHE_NAME = 'pybel_cache.db'
DEFAULT_CACHE_LOCATION = os.path.join(PYBEL_DATA_DIR, DEFAULT_CACHE_NAME)

PYBEL_CONTEXT_TAG = 'pybel_context'
PYBEL_AUTOEVIDENCE = 'Automatically added by PyBEL'

BEL_DEFAULT_NAMESPACE = 'bel'

#: The valid citation types
#: .. seealso:: https://wiki.openbel.org/display/BELNA/Citation
CITATION_TYPES = {'Book', 'PubMed', 'Journal', 'Online Resource', 'Other'}

#: The valid namespace types
#: .. seealso:: https://wiki.openbel.org/display/BELNA/Custom+Namespaces
NAMESPACE_DOMAIN_TYPES = {"BiologicalProcess", "Chemical", "Gene and Gene Products", "Other"}

#: Represents the key for the citation type in a citation dictionary
CITATION_TYPE = 'type'
#: Represents the key for the citation name in a citation dictionary
CITATION_NAME = 'name'
#: Represents the key for the citation reference in a citation dictionary
CITATION_REFERENCE = 'reference'
#: Represents the key for the citation date in a citation dictionary
CITATION_DATE = 'date'
#: Represents the key for the citation authors in a citation dictionary
CITATION_AUTHORS = 'authors'
#: Represents the key for the citation comment in a citation dictionary
CITATION_COMMENTS = 'comments'

#: Represents the ordering of the citation entries in a control statement (SET Citation = ...)
CITATION_ENTRIES = CITATION_TYPE, CITATION_NAME, CITATION_REFERENCE, CITATION_DATE, CITATION_AUTHORS, CITATION_COMMENTS

# Used during BEL parsing

MODIFIER = 'modifier'
EFFECT = 'effect'
TARGET = 'target'
FROM_LOC = 'fromLoc'
TO_LOC = 'toLoc'
MEMBERS = 'members'
REACTANTS = 'reactants'
PRODUCTS = 'products'
LOCATION = 'location'

ACTIVITY = 'Activity'
DEGRADATION = 'Degradation'
TRANSLOCATION = 'Translocation'
CELL_SECRETION = 'CellSecretion'
CELL_SURFACE_EXPRESSION = 'CellSurfaceExpression'

# Internal node data format keys
FUNCTION = 'function'
NAMESPACE = 'namespace'
NAME = 'name'
IDENTIFIER = 'identifier'

FUSION = 'fusion'
PARTNER_3P = 'partner_3p'
PARTNER_5P = 'partner_5p'
RANGE_3P = 'range_3p'
RANGE_5P = 'range_5p'

VARIANTS = 'variants'
#: The key representing what kind of variation is being represented
KIND = 'kind'
#: The value for :data:`KIND` for an HGVS variant
HGVS = 'hgvs'
#: The value for :data:`KIND` for a protein modification
PMOD = 'pmod'
#: The value for :data:`KIND` for a gene modification
GMOD = 'gmod'
#: The value for :data:`KIND` for a fragment
FRAGMENT = 'frag'

#: Used as a namespace when none is given when lenient parsing mode is turned on. Not recommended!
DIRTY = 'dirty'

#: Represents the BEL abundance, geneAbundance()
#: .. seealso:: http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#Xabundancea
GENE = 'Gene'

#: Represents the BEL abundance, rnaAbundance()
RNA = 'RNA'

#: Represents the BEL abundance, proteinAbundance()
PROTEIN = 'Protein'

#: Represents the BEL abundance, microRNAAbundance()
MIRNA = 'miRNA'

#: Represents the BEL abundance, abundance()
ABUNDANCE = 'Abundance'

#: Represents the BEL function, biologicalProcess()
BIOPROCESS = 'BiologicalProcess'

#: Represents the BEL function, pathology()
PATHOLOGY = 'Pathology'

#: Represents the BEL abundance, compositeAbundance()
COMPOSITE = 'Composite'

#: Represents the BEL abundance, complexAbundance()
COMPLEX = 'Complex'

#: Represents the BEL transformation, reaction()
REACTION = 'Reaction'

# Internal edge data keys

#: The key for an internal edge data dictionary for the relation string
RELATION = 'relation'
#: The key for an internal edge data dictionary for the citation dictionary
CITATION = 'citation'
#: The key for an internal edge data dictionary for the evidence string
EVIDENCE = 'evidence'
#: The key for an internal edge data dictionary for the annotations dictionary
ANNOTATIONS = 'annotations'
#: The key for an internal edge data dictionary for the subject modifier dictionary
SUBJECT = 'subject'
#: The key for an internal edge data dictionary for the object modifier dictionary
OBJECT = 'object'

HAS_REACTANT = 'hasReactant'
HAS_PRODUCT = 'hasProduct'
HAS_COMPONENT = 'hasComponent'
HAS_VARIANT = 'hasVariant'
HAS_MEMBER = 'hasMember'
TRANSCRIBED_TO = 'transcribedTo'  #: :data:`GENE` to :data:`RNA` is called transcription
TRANSLATED_TO = 'translatedTo'  #: RNA to PROTEIN is called translation
INCREASES = 'increases'
DIRECTLY_INCREASES = 'directlyIncreases'
DECREASES = 'decreases'
DIRECTLY_DECREASES = 'directlyDecreases'
CAUSES_NO_CHANGE = 'causesNoChange'
NEGATIVE_CORRELATION = 'negativeCorrelation'
POSITIVE_CORRELATION = 'positiveCorrelation'
ASSOCIATION = 'association'
ORTHOLOGOUS = 'orthologous'
ANALOGOUS_TO = 'analogousTo'
EQUIVALENT_TO = 'equivalentTo'

CAUSAL_INCREASE_RELATIONS = {INCREASES, DIRECTLY_INCREASES}
CAUSAL_DECREASE_RELATIONS = {DECREASES, DIRECTLY_DECREASES}
CAUSAL_RELATIONS = CAUSAL_INCREASE_RELATIONS | CAUSAL_DECREASE_RELATIONS

TWO_WAY_RELATIONS = {
    NEGATIVE_CORRELATION,
    POSITIVE_CORRELATION,
    ASSOCIATION,
    ORTHOLOGOUS,
    ANALOGOUS_TO,
    EQUIVALENT_TO,
}

CORRELATIVE_RELATIONS = {
    POSITIVE_CORRELATION,
    NEGATIVE_CORRELATION
}

unqualified_edges = [
    HAS_REACTANT,
    HAS_PRODUCT,
    HAS_COMPONENT,
    HAS_VARIANT,
    TRANSCRIBED_TO,
    TRANSLATED_TO,
    HAS_MEMBER,
]
unqualified_edge_code = {relation: (-1 - i) for i, relation in enumerate(unqualified_edges)}

# BEL Keywords

BEL_KEYWORD_SET = 'SET'
BEL_KEYWORD_DOCUMENT = 'DOCUMENT'
BEL_KEYWORD_DEFINE = 'DEFINE'
BEL_KEYWORD_NAMESPACE = 'NAMESPACE'
BEL_KEYWORD_ANNOTATION = 'ANNOTATION'
BEL_KEYWORD_AS = 'AS'
BEL_KEYWORD_URL = 'URL'
BEL_KEYWORD_LIST = 'LIST'
BEL_KEYWORD_OWL = 'OWL'
BEL_KEYWORD_PATTERN = 'PATTERN'

BEL_KEYWORD_UNSET = 'UNSET'
BEL_KEYWORD_STATEMENT_GROUP = 'STATEMENT_GROUP'
BEL_KEYWORD_CITATION = 'Citation'
BEL_KEYWORD_EVIDENCE = 'Evidence'
BEL_KEYWORD_SUPPORT = 'SupportingText'
BEL_KEYWORD_ALL = 'ALL'

BEL_KEYWORD_METADATA_NAME = 'Name'
BEL_KEYWORD_METADATA_VERSION = 'Version'
BEL_KEYWORD_METADATA_DESCRIPTION = 'Description'
BEL_KEYWORD_METADATA_AUTHORS = 'Authors'
BEL_KEYWORD_METADATA_CONTACT = 'ContactInfo'
BEL_KEYWORD_METADATA_LICENSES = 'Licenses'
BEL_KEYWORD_METADATA_COPYRIGHT = 'Copyright'
BEL_KEYWORD_METADATA_DISCLAIMER = 'Disclaimer'

# Internal metadata representation

#: The key for the document metadata dictionary. Can be accessed by :code:`graph.graph[GRAPH_METADATA]`, or by using
#: the property built in to the :class:`pybel.BELGraph`, :func:`pybel.BELGraph.document`
GRAPH_METADATA = 'document_metadata'
GRAPH_NAMESPACE_URL = 'namespace_url'
GRAPH_NAMESPACE_OWL = 'namespace_owl'
GRAPH_NAMESPACE_PATTERN = 'namespace_pattern'
GRAPH_ANNOTATION_URL = 'annotation_url'
GRAPH_ANNOTATION_OWL = 'annotation_owl'
GRAPH_ANNOTATION_PATTERN = 'annotation_pattern'
GRAPH_ANNOTATION_LIST = 'annotation_list'
GRAPH_WARNINGS = 'warnings'
GRAPH_PYBEL_VERSION = 'pybel_version'

#: The key for the document name. Can be accessed by :code:`graph.document[METADATA_NAME]` or by using the property
#: built into the :class:`pybel.BELGraph` class, :func:`pybel.BELGraph.name`
METADATA_NAME = 'name'
#: The key for the document version. Can be accessed by :code:`graph.document[METADATA_VERSION]`
METADATA_VERSION = 'version'
#: The key for the document description. Can be accessed by :code:`graph.document[METADATA_DESCRIPTION]`
METADATA_DESCRIPTION = 'description'
#: The key for the document authors. Can be accessed by :code:`graph.document[METADATA_NAME]`
METADATA_AUTHORS = 'authors'
#: The key for the document contact email. Can be accessed by :code:`graph.document[METADATA_CONTACT]`
METADATA_CONTACT = 'contact'
#: The key for the document licenses. Can be accessed by :code:`graph.document[METADATA_LICENSES]`
METADATA_LICENSES = 'licenses'
#: The key for the document copyright information. Can be accessed by :code:`graph.document[METADATA_COPYRIGHT]`
METADATA_COPYRIGHT = 'copyright'
#: The key for the document disclaimer. Can be accessed by :code:`graph.document[METADATA_DISCLAIMER]`
METADATA_DISCLAIMER = 'disclaimer'

#: Provides a mapping from BEL language keywords to internal PyBEL strings
DOCUMENT_KEYS = {
    BEL_KEYWORD_METADATA_AUTHORS: METADATA_AUTHORS,
    BEL_KEYWORD_METADATA_CONTACT: METADATA_CONTACT,
    BEL_KEYWORD_METADATA_COPYRIGHT: METADATA_COPYRIGHT,
    BEL_KEYWORD_METADATA_DESCRIPTION: METADATA_DESCRIPTION,
    BEL_KEYWORD_METADATA_DISCLAIMER: METADATA_DISCLAIMER,
    BEL_KEYWORD_METADATA_LICENSES: METADATA_LICENSES,
    BEL_KEYWORD_METADATA_NAME: METADATA_NAME,
    BEL_KEYWORD_METADATA_VERSION: METADATA_VERSION
}

#: Provides a mapping from internal PyBEL strings to BEL language keywords. Is the inverse of :data:`DOCUMENT_KEYS`
INVERSE_DOCUMENT_KEYS = {v: k for k, v in DOCUMENT_KEYS.items()}

#: A set representing the required metadata during BEL document parsing
REQUIRED_METADATA = {
    METADATA_NAME,
    METADATA_VERSION,
    METADATA_DESCRIPTION,
    METADATA_AUTHORS,
    METADATA_CONTACT
}

# Modifier parser constants

FRAGMENT_START = 'start'
FRAGMENT_STOP = 'stop'
FRAGMENT_MISSING = 'missing'
FRAGMENT_DESCRIPTION = 'description'

FUSION_REFERENCE = 'reference'
FUSION_START = 'left'
FUSION_STOP = 'right'
FUSION_MISSING = 'missing'

GMOD_ORDER = [KIND, IDENTIFIER]

GSUB_REFERENCE = 'reference'
GSUB_POSITION = 'position'
GSUB_VARIANT = 'variant'

PMOD_CODE = 'code'
PMOD_POSITION = 'pos'
PMOD_ORDER = [KIND, IDENTIFIER, PMOD_CODE, PMOD_POSITION]

PSUB_REFERENCE = 'reference'
PSUB_POSITION = 'position'
PSUB_VARIANT = 'variant'

TRUNCATION_POSITION = 'position'

#: ..seealso:: https://wiki.openbel.org/display/BELNA/Assignment+of+Encoding+%28Allowed+Functions%29+for+BEL+Namespaces
belns_encodings = {
    'G': {GENE},
    'R': {RNA, MIRNA},
    'P': {PROTEIN},
    'M': {MIRNA},
    'A': {ABUNDANCE, RNA, MIRNA, PROTEIN, GENE, COMPLEX},
    'B': {PATHOLOGY, BIOPROCESS},
    'O': {PATHOLOGY},
    'C': {COMPLEX}
}
