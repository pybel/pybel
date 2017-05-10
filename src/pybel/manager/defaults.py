# -*- coding: utf-8 -*-

"""
This file contains a listing of the default namespaces released in each version of OpenBEL, and other
common namespaces used to load into a new PyBEL namespace store.

Resources:

.. seealso:: Overview on OpenBEL namespaces https://wiki.openbel.org/display/BELNA/Namespaces+Overview
.. seealso:: Building custom namespaces http://openbel-framework.readthedocs.io/en/latest/tutorials/building_custom_namespaces.html
"""

from ..constants import FRAUNHOFER_RESOURCES

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
    'default_owl'
]

BEL_FRAMEWORK_2012 = 'http://resource.belframework.org/belframework/1.0'
BEL_FRAMEWORK_2013 = 'http://resource.belframework.org/belframework/20131211'
BEL_FRAMEWORK_2015 = 'http://resource.belframework.org/belframework/20150611'

BEL_FRAMEWORK_2012_NAMESPACE = BEL_FRAMEWORK_2012 + '/namespace/'
BEL_FRAMEWORK_2013_NAMESPACE = BEL_FRAMEWORK_2013 + '/namespace/'
BEL_FRAMEWORK_2015_NAMESPACE = BEL_FRAMEWORK_2015 + '/namespace/'

BEL_FRAMEWORK_2012_ANNOTATION = BEL_FRAMEWORK_2012 + '/annotation/'
BEL_FRAMEWORK_2013_ANNOTATION = BEL_FRAMEWORK_2013 + '/annotation/'
BEL_FRAMEWORK_2015_ANNOTATION = BEL_FRAMEWORK_2015 + '/annotation/'

BEL_FRAMEWORK_2012_EQUIVALENCE = BEL_FRAMEWORK_2012 + '/equivalence/'
BEL_FRAMEWORK_2013_EQUIVALENCE = BEL_FRAMEWORK_2013 + '/equivalence/'
BEL_FRAMEWORK_2015_EQUIVALENCE = BEL_FRAMEWORK_2015 + '/equivalence/'

default_namespaces_2012_names = [
    'affy-hg-u133-plus2.belns',
    'affy-hg-u133ab.belns',
    'affy-hg-u95av2.belns',
    'affy-mg-u74abc.belns',
    'affy-moe430ab.belns',
    'affy-mouse430-2.belns',
    'affy-mouse430a-2.belns',
    'affy-rae230ab-2.belns',
    'affy-rat230-2.belns',
    'chebi-ids.belns',
    'chebi-names.belns',
    'entrez-gene-ids-hmr.belns',
    'go-biological-processes-accession-numbers.belns',
    'go-biological-processes-names.belns',
    'go-cellular-component-accession-numbers.belns',
    'go-cellular-component-terms.belns',
    'hgnc-approved-symbols.belns',
    'mesh-biological-processes.belns',
    'mesh-cellular-locations.belns',
    'mesh-diseases.belns',
    'mgi-approved-symbols.belns',
    'rgd-approved-symbols.belns',
    'selventa-legacy-chemical-names.belns',
    'selventa-legacy-diseases.belns',
    'selventa-named-human-complexes.belns',
    'selventa-named-human-protein-families.belns',
    'selventa-named-mouse-complexes.belns',
    'selventa-named-mouse-protein-families.belns',
    'selventa-named-rat-complexes.belns',
    'selventa-named-rat-protein-families.belns',
    'swissprot-accession-numbers.belns',
    'swissprot-entry-names.belns',
]

default_namespaces_2012 = [BEL_FRAMEWORK_2012_NAMESPACE + name for name in default_namespaces_2012_names]

default_namespaces_2013_names = [
    'affy-probeset-ids.belns',
    'chebi-ids.belns',
    'chebi.belns',
    'disease-ontology-ids.belns',
    'disease-ontology.belns',
    'entrez-gene-ids.belns',
    'go-biological-process-ids.belns',
    'go-biological-process.belns',
    'go-cellular-component-ids.belns',
    'go-cellular-component.belns',
    'hgnc-human-genes.belns',
    'mesh-cellular-structures.belns',
    'mesh-diseases.belns',
    'mesh-processes.belns',
    'mgi-mouse-genes.belns',
    'rgd-rat-genes.belns',
    'selventa-legacy-chemicals.belns',
    'selventa-legacy-diseases.belns',
    'selventa-named-complexes.belns',
    'selventa-protein-families.belns',
    'swissprot-ids.belns',
    'swissprot.belns',
]

default_namespaces_2013 = [BEL_FRAMEWORK_2013_NAMESPACE + name for name in default_namespaces_2013_names]

namespaces_2015 = [
    'affy-probeset-ids.belns',
    'chebi-ids.belns',
    'chebi.belns',
    'disease-ontology-ids.belns',
    'disease-ontology.belns',
    'entrez-gene-ids.belns',
    'go-biological-process-ids.belns',
    'go-biological-process.belns',
    'go-cellular-component-ids.belns',
    'go-cellular-component.belns',
    'hgnc-human-genes.belns',
    'mesh-cellular-structures-ids.belns',
    'mesh-cellular-structures.belns',
    'mesh-chemicals-ids.belns',
    'mesh-chemicals.belns',
    'mesh-diseases-ids.belns',
    'mesh-diseases.belns',
    'mesh-processes-ids.belns',
    'mesh-processes.belns',
    'mgi-mouse-genes.belns',
    'rgd-rat-genes.belns',
    'selventa-legacy-chemicals.belns',
    'selventa-legacy-diseases.belns',
    'selventa-named-complexes.belns',
    'selventa-protein-families.belns',
    'swissprot-ids.belns',
    'swissprot.belns'
]

default_namespaces_2015 = [BEL_FRAMEWORK_2015_NAMESPACE + namespace for namespace in namespaces_2015]
fraunhofer_namespaces = [FRAUNHOFER_RESOURCES + namespace for namespace in namespaces_2015]

default_namespaces = default_namespaces_2012 + default_namespaces_2013 + default_namespaces_2015

default_annotations_2012_names = [
    'atcc-cell-line.belanno',
    'mesh-body-region.belanno',
    'mesh-cardiovascular-system.belanno',
    'mesh-cell-structure.belanno',
    'mesh-cell.belanno',
    'mesh-digestive-system.belanno',
    'mesh-disease.belanno',
    'mesh-embryonic-structure.belanno',
    'mesh-endocrine-system.belanno',
    'mesh-fluid-and-secretion.belanno',
    'mesh-hemic-and-immune-system.belanno',
    'mesh-integumentary-system.belanno',
    'mesh-musculoskeletal-system.belanno',
    'mesh-nervous-system.belanno',
    'mesh-respiratory-system.belanno',
    'mesh-sense-organ.belanno',
    'mesh-stomatognathic-system.belanno',
    'mesh-tissue.belanno',
    'mesh-urogenital-system.belanno',
    'species-taxonomy-id.belanno',
]

default_annotations_2012 = [BEL_FRAMEWORK_2012_ANNOTATION + name for name in default_annotations_2012_names]

annotations_current = [
    'anatomy.belanno',
    'cell-line.belanno',
    'cell-structure.belanno',
    'cell.belanno',
    'disease.belanno',
    'mesh-anatomy.belanno',
    'mesh-diseases.belanno',
    'species-taxonomy-id.belanno',
]

default_annotations_2013 = [BEL_FRAMEWORK_2013_ANNOTATION + annotation for annotation in annotations_current]
default_annotations_2015 = [BEL_FRAMEWORK_2015_ANNOTATION + annotation for annotation in annotations_current]
fraunhofer_annotations = [FRAUNHOFER_RESOURCES + annotation for annotation in annotations_current]

default_annotations = default_annotations_2012 + default_annotations_2013 + default_annotations_2015

default_equivalences_2012_names = [
    'affy-hg-u133-plus2.beleq',
    'affy-hg-u133ab.beleq',
    'affy-hg-u95av2.beleq',
    'affy-mg-u74abc.beleq',
    'affy-moe430ab.beleq',
    'affy-mouse430-2.beleq',
    'affy-mouse430a-2.beleq',
    'affy-rae230ab-2.beleq',
    'affy-rat230-2.beleq',
    'chebi-ids.beleq',
    'chebi-names.beleq',
    'entrez-gene-ids-hmr.beleq',
    'go-biological-processes-accession-numbers.beleq',
    'go-biological-processes-names.beleq',
    'go-cellular-component-accession-numbers.beleq',
    'go-cellular-component-terms.beleq',
    'hgnc-approved-symbols.beleq',
    'mesh-biological-processes.beleq',
    'mesh-cellular-locations.beleq',
    'mesh-diseases.beleq',
    'mgi-approved-symbols.beleq',
    'rgd-approved-symbols.beleq',
    'selventa-named-human-complexes.beleq',
    'selventa-named-human-protein-families.beleq',
    'selventa-named-mouse-complexes.beleq',
    'selventa-named-mouse-protein-families.beleq',
    'selventa-named-rat-complexes.beleq',
    'selventa-named-rat-protein-families.beleq',
    'swissprot-accession-numbers.beleq',
    'swissprot-entry-names.beleq'
]

default_equivalences_2012 = [BEL_FRAMEWORK_2012_EQUIVALENCE + name for name in default_equivalences_2012_names]

default_equivalences_2013_names = [
    'affy-probeset-ids.beleq',
    'chebi-ids.beleq',
    'chebi.beleq',
    'disease-ontology-ids.beleq',
    'disease-ontology.beleq',
    'entrez-gene-ids.beleq',
    'go-biological-process-ids.beleq',
    'go-biological-process.beleq',
    'go-cellular-component-ids.beleq',
    'go-cellular-component.beleq',
    'hgnc-human-genes.beleq',
    'mesh-cellular-structures.beleq',
    'mesh-diseases.beleq',
    'mesh-processes.beleq',
    'mgi-mouse-genes.beleq',
    'rgd-rat-genes.beleq',
    'selventa-legacy-chemicals.beleq',
    'selventa-legacy-diseases.beleq',
    'selventa-named-complexes.beleq',
    'selventa-protein-families.beleq',
    'swissprot-ids.beleq',
    'swissprot.beleq'

]

default_equivalences_2013 = [BEL_FRAMEWORK_2013_EQUIVALENCE + name for name in default_equivalences_2013_names]

default_equivalences_2015_names = [
    'affy-probeset-ids.beleq',
    'chebi-ids.beleq',
    'chebi.beleq',
    'disease-ontology-ids.beleq',
    'disease-ontology.beleq',
    'entrez-gene-ids.beleq',
    'go-biological-process-ids.beleq',
    'go-biological-process.beleq',
    'go-cellular-component-ids.beleq',
    'go-cellular-component.beleq',
    'hgnc-human-genes.beleq',
    'mesh-cellular-structures-ids.beleq',
    'mesh-cellular-structures.beleq',
    'mesh-chemicals-ids.beleq',
    'mesh-chemicals.beleq',
    'mesh-diseases-ids.beleq',
    'mesh-diseases.beleq',
    'mesh-processes-ids.beleq',
    'mesh-processes.beleq',
    'mgi-mouse-genes.beleq',
    'rgd-rat-genes.beleq',
    'selventa-legacy-chemicals.beleq',
    'selventa-legacy-diseases.beleq',
    'selventa-named-complexes.beleq',
    'selventa-protein-families.beleq',
    'swissprot-ids.beleq',
    'swissprot.beleq'
]

default_equivalences_2015 = [BEL_FRAMEWORK_2015_EQUIVALENCE + name for name in default_equivalences_2015_names]

default_equivalences = default_equivalences_2012 + default_equivalences_2013 + default_equivalences_2015

default_owl = [
    'http://purl.obolibrary.org/obo/hp/releases/2016-09-03/hp.owl',  # Human Phenotype Ontology
    'http://purl.obolibrary.org/obo/pr/49.0./pr-non-classified.owl'  # Protein Ontology
]
