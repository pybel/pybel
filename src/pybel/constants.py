import os

SMALL_CORPUS_URL = 'http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel'
LARGE_CORPUS_URL = 'http://resource.belframework.org/belframework/1.0/knowledge/large_corpus.bel'

GOCC_LATEST = 'http://resources.openbel.org/belframework/20150611/namespace/go-cellular-component.belns'

PYBEL_DIR = os.path.expanduser('~/.pybel')
if not os.path.exists(PYBEL_DIR):
    os.mkdir(PYBEL_DIR)

PYBEL_DATA = os.path.join(PYBEL_DIR, 'data')
if not os.path.exists(PYBEL_DATA):
    os.mkdir(PYBEL_DATA)
