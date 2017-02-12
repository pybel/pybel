# -*- coding: utf-8 -*-

import os

SMALL_CORPUS_URL = 'http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel'
LARGE_CORPUS_URL = 'http://resource.belframework.org/belframework/1.0/knowledge/large_corpus.bel'

GOCC_LATEST = 'http://resources.openbel.org/belframework/20150611/namespace/go-cellular-component.belns'
GOCC_KEYWORD = 'GOCC'

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

KIND = 'kind'
HGVS = 'hgvs'
PMOD = 'pmod'
GMOD = 'gmod'
FRAGMENT = 'frag'
FUNCTION = 'function'
NAMESPACE = 'namespace'
NAME = 'name'
IDENTIFIER = 'identifier'
VARIANTS = 'variants'
RELATION = 'relation'
CITATION = 'citation'
EVIDENCE = 'evidence'
ANNOTATIONS = 'annotations'

CITATION_TYPE = 'type'
CITATION_NAME = 'name'
CITATION_REFERENCE = 'reference'
CITATION_DATE = 'date'
CITATION_AUTHORS = 'authors'
CITATION_COMMENTS = 'comments'

CITATION_ENTRIES = CITATION_TYPE, CITATION_NAME, CITATION_REFERENCE, CITATION_DATE, CITATION_AUTHORS, CITATION_COMMENTS

#: .. seealso:: https://wiki.openbel.org/display/BELNA/Citation
CITATION_TYPES = {'Book', 'PubMed', 'Journal', 'Online Resource', 'Other'}

#: .. seealso:: https://wiki.openbel.org/display/BELNA/Custom+Namespaces
NAMESPACE_DOMAIN_TYPES = {"BiologicalProcess", "Chemical", "Gene and Gene Products", "Other"}

DIRTY = 'dirty'

ACTIVITY = 'Activity'
DEGRADATION = 'Degradation'
TRANSLOCATION = 'Translocation'
CELL_SECRETION = 'CellSecretion'
CELL_SURFACE_EXPRESSION = 'CellSurfaceExpression'

PARTNER_3P = 'partner_3p'
PARTNER_5P = 'partner_5p'
RANGE_3P = 'range_3p'
RANGE_5P = 'range_5p'

FUSION = 'fusion'
MODIFIER = 'modifier'
EFFECT = 'effect'
TARGET = 'target'
FROM_LOC = 'fromLoc'
TO_LOC = 'toLoc'
MEMBERS = 'members'
REACTANTS = 'reactants'
PRODUCTS = 'products'
LOCATION = 'location'

SUBJECT = 'subject'
OBJECT = 'object'

GENE = 'Gene'
RNA = 'RNA'
PROTEIN = 'Protein'
MIRNA = 'miRNA'
ABUNDANCE = 'Abundance'
BIOPROCESS = 'BiologicalProcess'
PATHOLOGY = 'Pathology'
COMPOSITE = 'Composite'
COMPLEX = 'Complex'
REACTION = 'Reaction'

HAS_REACTANT = 'hasReactant'
HAS_PRODUCT = 'hasProduct'
HAS_COMPONENT = 'hasComponent'
HAS_VARIANT = 'hasVariant'
HAS_MEMBER = 'hasMember'
TRANSCRIBED_TO = 'transcribedTo'
TRANSLATED_TO = 'translatedTo'

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

TWO_WAY_RELATIONS = {
    NEGATIVE_CORRELATION,
    POSITIVE_CORRELATION,
    ASSOCIATION,
    ORTHOLOGOUS,
    ANALOGOUS_TO,
    EQUIVALENT_TO,
}

BLACKLIST_EDGE_ATTRIBUTES = {RELATION, SUBJECT, OBJECT, CITATION, EVIDENCE}

# BEL Keywords

BEL_KEYWORD_SET = 'SET'
BEL_KEYWORD_DOCUMENT = 'DOCUMENT'
BEL_KEYWORD_METADATA_AUTHORS = 'Authors'
BEL_KEYWORD_METADATA_CONTACT = 'ContactInfo'
BEL_KEYWORD_METADATA_COPYRIGHT = 'Copyright'
BEL_KEYWORD_METADATA_DESCRIPTION = 'Description'
BEL_KEYWORD_METADATA_DISCLAIMER = 'Disclaimer'
BEL_KEYWORD_METADATA_LICENSES = 'Licenses'
BEL_KEYWORD_METADATA_NAME = 'Name'
BEL_KEYWORD_METADATA_VERSION = 'Version'

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

# Internal metadata representation

METADATA_NAME = 'name'
METADATA_VERSION = 'version'
METADATA_DESCRIPTION = 'description'
METADATA_AUTHORS = 'authors'
METADATA_CONTACT = 'contact'

REQUIRED_METADATA = {
    METADATA_NAME,
    METADATA_VERSION,
    METADATA_DESCRIPTION,
    METADATA_AUTHORS,
    METADATA_CONTACT
}

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
