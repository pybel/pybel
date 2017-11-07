# -*- coding: utf-8 -*-

from .arty import get_arty_annotation_url, get_arty_namespace_url

HGNC_HUMAN_GENES = get_arty_namespace_url('hgnc-human-genes', '20170511')
CHEBI = get_arty_namespace_url('chebi', '20170511')
CHEBI_IDS = get_arty_namespace_url('chebi-ids', '20170511')
HGNC_GENE_FAMILIES = get_arty_namespace_url('hgnc-gene-families', '20170515')
CONFIDENCE = get_arty_annotation_url('confidence', '1.0.0')
MESHD = get_arty_annotation_url('mesh-diseases', '20170511')
NEUROMMSIG = get_arty_annotation_url('neurommsig', '1.0.1')
NIFT = get_arty_namespace_url('imaging-ontology', '1.0.0')

default_namespace_spec = [
    ('ADO', 'alzheimer-disease-ontology', '1.0.2'),
    ('AFFX', 'affx-probeset-ids', '20170511'),
    ('BRCO', 'brain-region-ontology', '1.0.0'),
    ('CHEBI', 'chebi', '20170511'),
    ('CHEBIID', 'chebi-ids', '20170511'),
    ('CTO', 'clinical-trial-ontology', '1.0.0'),
    ('DO', 'disease-ontology', '20170511'),
    ('EGID', 'entrez-gene-ids', '20170511'),
    ('EPT', 'epilepsy-terminology', '1.0.0'),
    ('FlyBase', 'flybase', '20170508'),
    ('GOBP', 'go-biological-process', '20170511'),
    ('GOCC', 'go-cellular-component', '20170511'),
    ('GFAM', 'hgnc-gene-families', '20170515'),
    ('HGNC', 'hgnc-human-genes', '20170511'),
    ('NIFT', 'imaging-ontology', '1.0.0'),
    ('NTN', 'nutrition', '1.0.0'),
    ('MESHCS', 'mesh-cell-structures', '20170511'),
    ('MESHD', 'mesh-diseases', '20170511'),
    ('MESHPP', 'mesh-processes', '20170511'),
    ('MGI', 'mgi-mouse-genes', '20170511'),
    ('PTS', 'neurodegeneration-pathways', '20170511'),
    ('PDO', 'parkinson-disease-ontology', '20170511'),
    ('RGD', 'rgd-rat-genes', '20170511'),
    ('SCOM', 'selventa-named-complexes', '20170511'),
    ('SFAM', 'selventa-protein-families', '20170511'),
    ('SP', 'swissprot', '20170511'),
]

default_namespaces = {
    keyword: get_arty_namespace_url(namespace, version)
    for keyword, namespace, version in default_namespace_spec
}

# See: https://gist.github.com/lsauer/1312860
DBSNP_PATTERN = 'rs[0-9]+'
EC_PATTERN = '(\d+|\-)\.((\d+)|(\-))\.(\d+|\-)(\.(n)?(\d+|\-))*'
INCHI_PATTERN = '^((InChI=)?[^J][0-9BCOHNSOPrIFla+\-\(\)\\\/,pqbtmsih]{6,})$'

default_namespace_patterns = {
    'dbSNP': DBSNP_PATTERN,
    'EC': EC_PATTERN,
    'InChI': INCHI_PATTERN
}
default_annotation_spec = [
    ('Anatomy', 'anatomy', '20170511'),
    ('Cell', 'cell', '20170511'),
    ('CellLine', 'cell-line', '20170511'),
    ('CellStructure', 'cell-structure', '20170511'),
    ('Confidence', 'confidence', '1.0.0'),
    ('Disease', 'disease', '20170511'),
    ('Gender', 'gender', '1.0.0'),
    ('MeSHAnatomy', 'mesh-anatomy', '20170511'),
    ('MeSHDisease', 'mesh-diseases', '20170511'),
    ('Subgraph', 'neurommsig', '1.0.1'),
    ('SNPO', 'snpo', '20170425'),
    ('Species', 'species-taxonomy-id', '20170511'),
    ('TextLocation', 'text-location', '1.0.0'),
]

default_annotations = {
    keyword: get_arty_annotation_url(annotation, version)
    for keyword, annotation, version in default_annotation_spec
}
