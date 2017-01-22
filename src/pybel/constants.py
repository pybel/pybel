import os

SMALL_CORPUS_URL = 'http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel'
LARGE_CORPUS_URL = 'http://resource.belframework.org/belframework/1.0/knowledge/large_corpus.bel'

GOCC_LATEST = 'http://resources.openbel.org/belframework/20150611/namespace/go-cellular-component.belns'
GOCC_KEYWORD = 'GOCC'

PYBEL_DIR = os.path.expanduser('~/.pybel')
if not os.path.exists(PYBEL_DIR):
    os.mkdir(PYBEL_DIR)

PYBEL_DATA = os.path.join(PYBEL_DIR, 'data')
if not os.path.exists(PYBEL_DATA):
    os.mkdir(PYBEL_DATA)

PYBEL_CONTEXT_TAG = 'pybel_context'

PYBEL_DEFAULT_NAMESPACE = 'PYBEL'

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
EVIDENCE = 'SupportingText'

CITATION_ENTRIES = 'type', 'name', 'reference', 'date', 'authors', 'comments'
CITATION_TYPES = {'Book', 'PubMed', 'Journal', 'Online Resource', 'Other'}
BLACKLIST_EDGE_ATTRIBUTES = {'relation', 'subject', 'object', 'citation', 'SupportingText'}
DIRTY = 'dirty'
