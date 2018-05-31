# -*- coding: utf-8 -*-

"""
This file contains a listing of the default namespaces released in each version of OpenBEL, and other
common namespaces used to load into a new PyBEL namespace store.

Resources:

.. seealso:: Overview on OpenBEL namespaces https://wiki.openbel.org/display/BELNA/Namespaces+Overview
.. seealso:: Building custom namespaces http://openbel-framework.readthedocs.io/en/latest/tutorials/building_custom_namespaces.html
"""

__all__ = [
    'default_namespaces_2012',
    'default_namespaces_2013',
    'default_namespaces_2015',
    'default_namespaces',
    'fraunhofer_namespaces',
    'default_annotations_2012',
    'default_annotations_2013',
    'default_annotations_2015',
    'default_annotations',
    'fraunhofer_annotations',
    'default_equivalences_2012',
    'default_equivalences_2013',
    'default_equivalences_2015',
    'default_equivalences',
]

BEL_FRAMEWORK_BASE = 'http://resources.openbel.org/belframework'
BEL_FRAMEWORK_2012 = BEL_FRAMEWORK_BASE + '/1.0'
BEL_FRAMEWORK_2013 = BEL_FRAMEWORK_BASE + '/20131211'
BEL_FRAMEWORK_2015 = BEL_FRAMEWORK_BASE + '/20150611'

BEL_FRAMEWORK_2012_NAMESPACE = BEL_FRAMEWORK_2012 + '/namespace/'
BEL_FRAMEWORK_2013_NAMESPACE = BEL_FRAMEWORK_2013 + '/namespace/'
BEL_FRAMEWORK_2015_NAMESPACE = BEL_FRAMEWORK_2015 + '/namespace/'

BEL_FRAMEWORK_2012_ANNOTATION = BEL_FRAMEWORK_2012 + '/annotation/'
BEL_FRAMEWORK_2013_ANNOTATION = BEL_FRAMEWORK_2013 + '/annotation/'
BEL_FRAMEWORK_2015_ANNOTATION = BEL_FRAMEWORK_2015 + '/annotation/'

BEL_FRAMEWORK_2012_EQUIVALENCE = BEL_FRAMEWORK_2012 + '/equivalence/'
BEL_FRAMEWORK_2013_EQUIVALENCE = BEL_FRAMEWORK_2013 + '/equivalence/'
BEL_FRAMEWORK_2015_EQUIVALENCE = BEL_FRAMEWORK_2015 + '/equivalence/'

BEL_FRAMEWORK_2015_DATE = '20150601'

FRAUNHOFER_RESOURCES_BASE = 'https://arty.scai.fraunhofer.de/artifactory/bel'
FRAUNHOFER_RESOURCES_NAMESPACE = FRAUNHOFER_RESOURCES_BASE + '/namespace'
FRAUNHOFER_RESOURCES_ANNOTATION = FRAUNHOFER_RESOURCES_BASE + '/annotation'

default_namespaces_2012_names = [
    'affy-hg-u133-plus2',
    'affy-hg-u133ab',
    'affy-hg-u95av2',
    'affy-mg-u74abc',
    'affy-moe430ab',
    'affy-mouse430-2',
    'affy-mouse430a-2',
    'affy-rae230ab-2',
    'affy-rat230-2',
    'chebi-ids',
    'chebi-names',
    'entrez-gene-ids-hmr',
    'go-biological-processes-accession-numbers',
    'go-biological-processes-names',
    'go-cellular-component-accession-numbers',
    'go-cellular-component-terms',
    'hgnc-approved-symbols',
    'mesh-biological-processes',
    'mesh-cellular-locations',
    'mesh-diseases',
    'mgi-approved-symbols',
    'rgd-approved-symbols',
    'selventa-legacy-chemical-names',
    'selventa-legacy-diseases',
    'selventa-named-human-complexes',
    'selventa-named-human-protein-families',
    'selventa-named-mouse-complexes',
    'selventa-named-mouse-protein-families',
    'selventa-named-rat-complexes',
    'selventa-named-rat-protein-families',
    'swissprot-accession-numbers',
    'swissprot-entry-names',
]

default_namespaces_2012 = [
    '{}{}.belns'.format(BEL_FRAMEWORK_2012_NAMESPACE, name)
    for name in default_namespaces_2012_names
]

default_namespaces_2013_names = [
    'affy-probeset-ids',
    'chebi-ids',
    'chebi',
    'disease-ontology-ids',
    'disease-ontology',
    'entrez-gene-ids',
    'go-biological-process-ids',
    'go-biological-process',
    'go-cellular-component-ids',
    'go-cellular-component',
    'hgnc-human-genes',
    'mesh-cellular-structures',
    'mesh-diseases',
    'mesh-processes',
    'mgi-mouse-genes',
    'rgd-rat-genes',
    'selventa-legacy-chemicals',
    'selventa-legacy-diseases',
    'selventa-named-complexes',
    'selventa-protein-families',
    'swissprot-ids',
    'swissprot',
]

default_namespaces_2013 = [
    '{}{}.belns'.format(BEL_FRAMEWORK_2013_NAMESPACE, name)
    for name in default_namespaces_2013_names
]

namespaces_2015 = [
    'affy-probeset-ids',
    'chebi-ids',
    'chebi',
    'disease-ontology-ids',
    'disease-ontology',
    'entrez-gene-ids',
    'go-biological-process-ids',
    'go-biological-process',
    'go-cellular-component-ids',
    'go-cellular-component',
    'hgnc-human-genes',
    'mesh-cellular-structures-ids',
    'mesh-cellular-structures',
    'mesh-chemicals-ids',
    'mesh-chemicals',
    'mesh-diseases-ids',
    'mesh-diseases',
    'mesh-processes-ids',
    'mesh-processes',
    'mgi-mouse-genes',
    'rgd-rat-genes',
    'selventa-legacy-chemicals',
    'selventa-legacy-diseases',
    'selventa-named-complexes',
    'selventa-protein-families',
    'swissprot-ids',
    'swissprot'
]

default_namespaces_2015 = [
    '{}{}.belns'.format(BEL_FRAMEWORK_2015_NAMESPACE, namespace)
    for namespace in namespaces_2015
]
fraunhofer_namespaces = [
    '{base}/{module}/{module}-{date}.belns'.format(
        base=FRAUNHOFER_RESOURCES_NAMESPACE,
        module=namespace,
        date=BEL_FRAMEWORK_2015_DATE
    )
    for namespace in namespaces_2015
]

default_namespaces = default_namespaces_2012 + default_namespaces_2013 + default_namespaces_2015

default_annotations_2012_names = [
    'atcc-cell-line',
    'mesh-body-region',
    'mesh-cardiovascular-system',
    'mesh-cell-structure',
    'mesh-cell',
    'mesh-digestive-system',
    'mesh-disease',
    'mesh-embryonic-structure',
    'mesh-endocrine-system',
    'mesh-fluid-and-secretion',
    'mesh-hemic-and-immune-system',
    'mesh-integumentary-system',
    'mesh-musculoskeletal-system',
    'mesh-nervous-system',
    'mesh-respiratory-system',
    'mesh-sense-organ',
    'mesh-stomatognathic-system',
    'mesh-tissue',
    'mesh-urogenital-system',
    'species-taxonomy-id',
]

default_annotations_2012 = [
    '{}{}.belanno'.format(BEL_FRAMEWORK_2012_ANNOTATION, name)
    for name in default_annotations_2012_names
]

annotations_current = [
    'anatomy',
    'cell-line',
    'cell-structure',
    'cell',
    'disease',
    'mesh-anatomy',
    'mesh-diseases',
    'species-taxonomy-id',
]

default_annotations_2013 = [
    '{}{}.belanno'.format(BEL_FRAMEWORK_2013_ANNOTATION, annotation)
    for annotation in annotations_current
]
default_annotations_2015 = [
    '{}{}.belanno'.format(BEL_FRAMEWORK_2015_ANNOTATION, annotation)
    for annotation in annotations_current
]
fraunhofer_annotations = [
    '{base}/{module}/{module}-{date}.belns'.format(
        base=FRAUNHOFER_RESOURCES_ANNOTATION,
        module=annotation,
        date=BEL_FRAMEWORK_2015_DATE
    )
    for annotation in annotations_current
]

default_annotations = default_annotations_2012 + default_annotations_2013 + default_annotations_2015

default_equivalences_2012_names = [
    'affy-hg-u133-plus2',
    'affy-hg-u133ab',
    'affy-hg-u95av2',
    'affy-mg-u74abc',
    'affy-moe430ab',
    'affy-mouse430-2',
    'affy-mouse430a-2',
    'affy-rae230ab-2',
    'affy-rat230-2',
    'chebi-ids',
    'chebi-names',
    'entrez-gene-ids-hmr',
    'go-biological-processes-accession-numbers',
    'go-biological-processes-names',
    'go-cellular-component-accession-numbers',
    'go-cellular-component-terms',
    'hgnc-approved-symbols',
    'mesh-biological-processes',
    'mesh-cellular-locations',
    'mesh-diseases',
    'mgi-approved-symbols',
    'rgd-approved-symbols',
    'selventa-named-human-complexes',
    'selventa-named-human-protein-families',
    'selventa-named-mouse-complexes',
    'selventa-named-mouse-protein-families',
    'selventa-named-rat-complexes',
    'selventa-named-rat-protein-families',
    'swissprot-accession-numbers',
    'swissprot-entry-names'
]

default_equivalences_2012 = [
    '{}{}.beleq'.format(BEL_FRAMEWORK_2012_EQUIVALENCE, name)
    for name in default_equivalences_2012_names
]

default_equivalences_2013_names = [
    'affy-probeset-ids',
    'chebi-ids',
    'chebi',
    'disease-ontology-ids',
    'disease-ontology',
    'entrez-gene-ids',
    'go-biological-process-ids',
    'go-biological-process',
    'go-cellular-component-ids',
    'go-cellular-component',
    'hgnc-human-genes',
    'mesh-cellular-structures',
    'mesh-diseases',
    'mesh-processes',
    'mgi-mouse-genes',
    'rgd-rat-genes',
    'selventa-legacy-chemicals',
    'selventa-legacy-diseases',
    'selventa-named-complexes',
    'selventa-protein-families',
    'swissprot-ids',
    'swissprot'

]

default_equivalences_2013 = [
    '{}{}.beleq'.format(BEL_FRAMEWORK_2013_EQUIVALENCE, name)
    for name in default_equivalences_2013_names
]

default_equivalences_2015_names = [
    'affy-probeset-ids',
    'chebi-ids',
    'chebi',
    'disease-ontology-ids',
    'disease-ontology',
    'entrez-gene-ids',
    'go-biological-process-ids',
    'go-biological-process',
    'go-cellular-component-ids',
    'go-cellular-component',
    'hgnc-human-genes',
    'mesh-cellular-structures-ids',
    'mesh-cellular-structures',
    'mesh-chemicals-ids',
    'mesh-chemicals',
    'mesh-diseases-ids',
    'mesh-diseases',
    'mesh-processes-ids',
    'mesh-processes',
    'mgi-mouse-genes',
    'rgd-rat-genes',
    'selventa-legacy-chemicals',
    'selventa-legacy-diseases',
    'selventa-named-complexes',
    'selventa-protein-families',
    'swissprot-ids',
    'swissprot'
]

default_equivalences_2015 = [
    '{}{}.beleq'.format(BEL_FRAMEWORK_2015_EQUIVALENCE, name)
    for name in default_equivalences_2015_names
]

default_equivalences = default_equivalences_2012 + default_equivalences_2013 + default_equivalences_2015
