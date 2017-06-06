# -*- coding: utf-8 -*-

"""
PyBEL Constants
---------------

This module maintains the strings used throughout the PyBEL codebase to promote consistency.

Configuration Loading
---------------------
By default, PyBEL loads its configuration from ``~/.config/pybel/config.json``. This json is stored in the object
:data:`pybel.constants.config`.
"""

from json import load, dump
from logging import getLogger
from os import path, mkdir, environ, makedirs

log = getLogger(__name__)

BELFRAMEWORK_DOMAIN = 'http://resource.belframework.org'
OPENBEL_DOMAIN = 'http://resources.openbel.org'

SMALL_CORPUS_URL = OPENBEL_DOMAIN + '/belframework/20150611/knowledge/small_corpus.bel'
LARGE_CORPUS_URL = OPENBEL_DOMAIN + '/belframework/20150611/knowledge/large_corpus.bel'

FRAUNHOFER_RESOURCES = 'https://owncloud.scai.fraunhofer.de/index.php/s/JsfpQvkdx3Y5EMx/download?path='
OPENBEL_NAMESPACE_RESOURCES = OPENBEL_DOMAIN + '/belframework/20150611/namespace/'
OPENBEL_ANNOTATION_RESOURCES = OPENBEL_DOMAIN + '/belframework/20150611/annotation/'
DEFAULT_NAMESPACE_RESOURCES = FRAUNHOFER_RESOURCES
DEFAULT_ANNOTATION_RESOURCES = FRAUNHOFER_RESOURCES

#: GOCC is the only namespace that needs to be stored because translocations use some of its values by default
GOCC_LATEST = DEFAULT_NAMESPACE_RESOURCES + 'go-cellular-component.belns'
GOCC_KEYWORD = 'GOCC'

#: The environment variable that contains the default SQL connection information for the PyBEL cache
PYBEL_CONNECTION = 'PYBEL_CONNECTION'

#: The default directory where PyBEL files, including logs and the  default cache, are stored. Created if not exists.
PYBEL_DIR = path.join(path.expanduser('~'), '.pybel')
if not path.exists(PYBEL_DIR):
    mkdir(PYBEL_DIR)

#: The default directory where PyBEL logs are stored
PYBEL_LOG_DIR = path.join(PYBEL_DIR, 'logs')
if not path.exists(PYBEL_LOG_DIR):
    mkdir(PYBEL_LOG_DIR)

#: The default directory where PyBEL data are stored
PYBEL_DATA_DIR = path.join(PYBEL_DIR, 'data')
if not path.exists(PYBEL_DATA_DIR):
    mkdir(PYBEL_DATA_DIR)

DEFAULT_CACHE_NAME = 'pybel_cache.db'
#: The default cache location is ``~/.pybel/data/pybel_cache.db``
DEFAULT_CACHE_LOCATION = path.join(PYBEL_DATA_DIR, DEFAULT_CACHE_NAME)
#: The default cache connection string uses sqlite.
DEFAULT_CACHE_CONNECTION = 'sqlite:///' + DEFAULT_CACHE_LOCATION

PYBEL_CONFIG_DIR = path.join(path.expanduser('~'), '.config', 'pybel')
if not path.exists(PYBEL_CONFIG_DIR):
    makedirs(PYBEL_CONFIG_DIR)

#: The global configuration for PyBEL is stored here. By default, it loads from ``~/.config/pybel/config.json``
config = {}

PYBEL_CONFIG_PATH = path.join(PYBEL_CONFIG_DIR, 'config.json')
if not path.exists(PYBEL_CONFIG_PATH):
    with open(PYBEL_CONFIG_PATH, 'w') as f:
        config.update({PYBEL_CONNECTION: DEFAULT_CACHE_CONNECTION})
        dump(config, f)
else:
    with open(PYBEL_CONFIG_PATH) as f:
        config.update(load(f))
        config.setdefault(PYBEL_CONNECTION, DEFAULT_CACHE_CONNECTION)


def get_cache_connection():
    """Returns the default cache connection string"""
    if PYBEL_CONNECTION in environ:
        log.info('connecting to environment-defined database: %s', environ[PYBEL_CONNECTION])
        return environ[PYBEL_CONNECTION]

    log.info('connecting to %s', config[PYBEL_CONNECTION])
    return config[PYBEL_CONNECTION]


PYBEL_CONTEXT_TAG = 'pybel_context'
PYBEL_AUTOEVIDENCE = 'Automatically added by PyBEL'

#: The default namespace given to entities in the BEL language
BEL_DEFAULT_NAMESPACE = 'bel'

CITATION_TYPE_BOOK = 'Book'
CITATION_TYPE_PUBMED = 'PubMed'
CITATION_TYPE_JOURNAL = 'Journal'
CITATION_TYPE_ONLINE = 'Online Resource'
CITATION_TYPE_URL = 'URL'
CITATION_TYPE_DOI = 'DOI'
CITATION_TYPE_OTHER = 'Other'
#: The valid citation types
#: .. seealso:: https://wiki.openbel.org/display/BELNA/Citation
CITATION_TYPES = {
    CITATION_TYPE_BOOK,
    CITATION_TYPE_PUBMED,
    CITATION_TYPE_JOURNAL,
    CITATION_TYPE_ONLINE,
    CITATION_TYPE_URL,
    CITATION_TYPE_DOI,
    CITATION_TYPE_OTHER
}

NAMESPACE_DOMAIN_BIOPROCESS = 'BiologicalProcess'
NAMESPACE_DOMAIN_CHEMICAL = 'Chemical'
NAMESPACE_DOMAIN_GENE = 'Gene and Gene Products'
NAMESPACE_DOMAIN_OTHER = 'Other'
#: The valid namespace types
#: .. seealso:: https://wiki.openbel.org/display/BELNA/Custom+Namespaces
NAMESPACE_DOMAIN_TYPES = {
    NAMESPACE_DOMAIN_BIOPROCESS,
    NAMESPACE_DOMAIN_CHEMICAL,
    NAMESPACE_DOMAIN_GENE,
    NAMESPACE_DOMAIN_OTHER
}

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
#: The node data key specifying the node's function (e.g. :data:`GENE`, :data:`MIRNA`, :data:`BIOPROCESS`, etc.)
FUNCTION = 'function'
#: The key specifying an identifier dictionary's namespace. Used for nodes, activities, and transformations.
NAMESPACE = 'namespace'
#: The key specifying an identifier dictionary's name. Used for nodes, activities, and transformations.
NAME = 'name'
#: The key specifying an identifier dictionary
IDENTIFIER = 'identifier'
#: The key specifying an optional label for the node
LABEL = 'label'
#: The key specifying an optional description for the node
DESCRIPTION = 'description'

#: The node data key specifying a fusion dictionary, containing :data:`PARTNER_3P`, :data:`PARTNER_5P`,
# :data:`RANGE_3P`, and :data:`RANGE_5P`
FUSION = 'fusion'
#: The key specifying the identifier dictionary of the fusion's 3-Prime partner
PARTNER_3P = 'partner_3p'
#: The key specifying the identifier dictionary of the fusion's 5-Prime partner
PARTNER_5P = 'partner_5p'
#: The key specifying the range dictionary of the fusion's 3-Prime partner
RANGE_3P = 'range_3p'
#: The key specifying the range dictionary of the fusion's 5-Prime partner
RANGE_5P = 'range_5p'

FUSION_REFERENCE = 'reference'
FUSION_START = 'left'
FUSION_STOP = 'right'
FUSION_MISSING = 'missing'

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
#: The key or an internal edge data dictonary for the line number
LINE = 'line'

#: A BEL relationship
HAS_REACTANT = 'hasReactant'
#: A BEL relationship
HAS_PRODUCT = 'hasProduct'
#: A BEL relationship
HAS_COMPONENT = 'hasComponent'
#: A BEL relationship
HAS_VARIANT = 'hasVariant'
#: A BEL relationship
HAS_MEMBER = 'hasMember'
#: A BEL relationship
#: :data:`GENE` to :data:`RNA` is called transcription
TRANSCRIBED_TO = 'transcribedTo'
#: A BEL relationship
#: :data:`RNA` to :data:`PROTEIN` is called translation
TRANSLATED_TO = 'translatedTo'
#: A BEL relationship
INCREASES = 'increases'
#: A BEL relationship
DIRECTLY_INCREASES = 'directlyIncreases'
#: A BEL relationship
DECREASES = 'decreases'
#: A BEL relationship
DIRECTLY_DECREASES = 'directlyDecreases'
#: A BEL relationship
CAUSES_NO_CHANGE = 'causesNoChange'
#: A BEL relationship
REGULATES = 'regulates'
#: A BEL relationship
NEGATIVE_CORRELATION = 'negativeCorrelation'
#: A BEL relationship
POSITIVE_CORRELATION = 'positiveCorrelation'
#: A BEL relationship
ASSOCIATION = 'association'
#: A BEL relationship
ORTHOLOGOUS = 'orthologous'
#: A BEL relationship
ANALOGOUS_TO = 'analogousTo'
#: A BEL relationship
IS_A = 'isA'
#: A BEL relationship
RATE_LIMITING_STEP_OF = 'rateLimitingStepOf'
#: A BEL relationship
SUBPROCESS_OF = 'subProcessOf'
#: A BEL relationship
BIOMARKER_FOR = 'biomarkerFor'
#: A BEL relationship
PROGONSTIC_BIOMARKER_FOR = 'prognosticBiomarkerFor'
#: A BEL relationship, added by PyBEL
EQUIVALENT_TO = 'equivalentTo'

#: A set of all causal relationships that have an increasing effect
CAUSAL_INCREASE_RELATIONS = {INCREASES, DIRECTLY_INCREASES}
#: A set of all causal relationships that have a decreasing effect
CAUSAL_DECREASE_RELATIONS = {DECREASES, DIRECTLY_DECREASES}
#: A set of all causal relationships
CAUSAL_RELATIONS = CAUSAL_INCREASE_RELATIONS | CAUSAL_DECREASE_RELATIONS

#: A set of all relationships that are inherently directionless, and are therefore added to the graph twice
TWO_WAY_RELATIONS = {
    NEGATIVE_CORRELATION,
    POSITIVE_CORRELATION,
    ASSOCIATION,
    ORTHOLOGOUS,
    ANALOGOUS_TO,
    EQUIVALENT_TO,
}

#: A set of all correlative relationships
CORRELATIVE_RELATIONS = {
    POSITIVE_CORRELATION,
    NEGATIVE_CORRELATION
}

#: A list of relationship types that don't require annotations or evidence
#: This must be maintained as a list, since the :data:`unqualified_edge_code` is calculated based on the order
#: and needs to be consistient
unqualified_edges = [
    HAS_REACTANT,
    HAS_PRODUCT,
    HAS_COMPONENT,
    HAS_VARIANT,
    TRANSCRIBED_TO,
    TRANSLATED_TO,
    HAS_MEMBER,
    IS_A,
]

#: Unqualified edges are given negative keys since the standard networkx edge key factory starts at 0 and counts up
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

# Internal metadata representation. See BELGraph documentation, since these are shielded from the user by properties.

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

#: The key for the starting position of a fragment range
FRAGMENT_START = 'start'
#: The key for the stopping position of a fragment range
FRAGMENT_STOP = 'stop'
#: The key signifying that there is neither a start nor stop position defined
FRAGMENT_MISSING = 'missing'
#: The key for any additional descriptive data about a fragment
FRAGMENT_DESCRIPTION = 'description'

#: The order for serializing gene modification data
GMOD_ORDER = [KIND, IDENTIFIER]

#: The key for the reference nucleotide in a gene substitution.
#: Only used during parsing  since this is converted to HGVS.
GSUB_REFERENCE = 'reference'
#: The key for the position of a gene substitution.
#: Only used during parsing  since this is converted to HGVS
GSUB_POSITION = 'position'
#: The key for the effect of a gene substitution.
#: Only used during parsing since this is converted to HGVS
GSUB_VARIANT = 'variant'

#: The key for the protein modification code.
PMOD_CODE = 'code'
#: The key for the protein modification position.
PMOD_POSITION = 'pos'
#: The order for serializing information about a protein modification
PMOD_ORDER = [KIND, IDENTIFIER, PMOD_CODE, PMOD_POSITION]

#: The key for the reference amino acid in a protein substitution.
#: Only used during parsing since this is concerted to HGVS
PSUB_REFERENCE = 'reference'
#: The key for the position of a protein substitution. Only used during parsing since this is converted to HGVS.
PSUB_POSITION = 'position'
#: The key for the variant of a protein substitution.Only used during parsing since this is converted to HGVS.
PSUB_VARIANT = 'variant'

#: The key for the position at which a protein is truncated
TRUNCATION_POSITION = 'position'

#: The mapping from BEL namespace codes to PyBEL internal abundance constants
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
