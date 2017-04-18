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
    'default_namespaces_1',
    'default_namespaces_2013',
    'default_namespaces_2015',
    'default_namespaces',
    'default_annotations_1',
    'default_annotations_2013',
    'default_annotations_2015',
    'default_annotations',
    'default_equivalences_1',
    'default_equivalences_2013',
    'default_equivalences_2015',
    'default_equivalences',
    'default_owl'
]

BEL_FRAMEWORK_2012 = 'http://resource.belframework.org/belframework/1.0'
BEL_FRAMEWORK_2013 = 'http://resource.belframework.org/belframework/20131211'
BEL_FRAMEWORK_2015 = 'http://resource.belframework.org/belframework/20150611'

default_namespaces_1 = [
    BEL_FRAMEWORK_2012 + '/namespace/affy-hg-u133-plus2.belns',
    BEL_FRAMEWORK_2012 + '/namespace/affy-hg-u133ab.belns',
    BEL_FRAMEWORK_2012 + '/namespace/affy-hg-u95av2.belns',
    BEL_FRAMEWORK_2012 + '/namespace/affy-mg-u74abc.belns',
    BEL_FRAMEWORK_2012 + '/namespace/affy-moe430ab.belns',
    BEL_FRAMEWORK_2012 + '/namespace/affy-mouse430-2.belns',
    BEL_FRAMEWORK_2012 + '/namespace/affy-mouse430a-2.belns',
    BEL_FRAMEWORK_2012 + '/namespace/affy-rae230ab-2.belns',
    BEL_FRAMEWORK_2012 + '/namespace/affy-rat230-2.belns',
    BEL_FRAMEWORK_2012 + '/namespace/chebi-ids.belns',
    BEL_FRAMEWORK_2012 + '/namespace/chebi-names.belns',
    BEL_FRAMEWORK_2012 + '/namespace/entrez-gene-ids-hmr.belns',
    BEL_FRAMEWORK_2012 + '/namespace/go-biological-processes-accession-numbers.belns',
    BEL_FRAMEWORK_2012 + '/namespace/go-biological-processes-names.belns',
    BEL_FRAMEWORK_2012 + '/namespace/go-cellular-component-accession-numbers.belns',
    BEL_FRAMEWORK_2012 + '/namespace/go-cellular-component-terms.belns',
    BEL_FRAMEWORK_2012 + '/namespace/hgnc-approved-symbols.belns',
    BEL_FRAMEWORK_2012 + '/namespace/mesh-biological-processes.belns',
    BEL_FRAMEWORK_2012 + '/namespace/mesh-cellular-locations.belns',
    BEL_FRAMEWORK_2012 + '/namespace/mesh-diseases.belns',
    BEL_FRAMEWORK_2012 + '/namespace/mgi-approved-symbols.belns',
    BEL_FRAMEWORK_2012 + '/namespace/rgd-approved-symbols.belns',
    BEL_FRAMEWORK_2012 + '/namespace/selventa-legacy-chemical-names.belns',
    BEL_FRAMEWORK_2012 + '/namespace/selventa-legacy-diseases.belns',
    BEL_FRAMEWORK_2012 + '/namespace/selventa-named-human-complexes.belns',
    BEL_FRAMEWORK_2012 + '/namespace/selventa-named-human-protein-families.belns',
    BEL_FRAMEWORK_2012 + '/namespace/selventa-named-mouse-complexes.belns',
    BEL_FRAMEWORK_2012 + '/namespace/selventa-named-mouse-protein-families.belns',
    BEL_FRAMEWORK_2012 + '/namespace/selventa-named-rat-complexes.belns',
    BEL_FRAMEWORK_2012 + '/namespace/selventa-named-rat-protein-families.belns',
    BEL_FRAMEWORK_2012 + '/namespace/swissprot-accession-numbers.belns',
    BEL_FRAMEWORK_2012 + '/namespace/swissprot-entry-names.belns',
]
default_namespaces_2013 = [
    BEL_FRAMEWORK_2013 + '/namespace/affy-probeset-ids.belns',
    BEL_FRAMEWORK_2013 + '/namespace/chebi-ids.belns',
    BEL_FRAMEWORK_2013 + '/namespace/chebi.belns',
    BEL_FRAMEWORK_2013 + '/namespace/disease-ontology-ids.belns',
    BEL_FRAMEWORK_2013 + '/namespace/disease-ontology.belns',
    BEL_FRAMEWORK_2013 + '/namespace/entrez-gene-ids.belns',
    BEL_FRAMEWORK_2013 + '/namespace/go-biological-process-ids.belns',
    BEL_FRAMEWORK_2013 + '/namespace/go-biological-process.belns',
    BEL_FRAMEWORK_2013 + '/namespace/go-cellular-component-ids.belns',
    BEL_FRAMEWORK_2013 + '/namespace/go-cellular-component.belns',
    BEL_FRAMEWORK_2013 + '/namespace/hgnc-human-genes.belns',
    BEL_FRAMEWORK_2013 + '/namespace/mesh-cellular-structures.belns',
    BEL_FRAMEWORK_2013 + '/namespace/mesh-diseases.belns',
    BEL_FRAMEWORK_2013 + '/namespace/mesh-processes.belns',
    BEL_FRAMEWORK_2013 + '/namespace/mgi-mouse-genes.belns',
    BEL_FRAMEWORK_2013 + '/namespace/rgd-rat-genes.belns',
    BEL_FRAMEWORK_2013 + '/namespace/selventa-legacy-chemicals.belns',
    BEL_FRAMEWORK_2013 + '/namespace/selventa-legacy-diseases.belns',
    BEL_FRAMEWORK_2013 + '/namespace/selventa-named-complexes.belns',
    BEL_FRAMEWORK_2013 + '/namespace/selventa-protein-families.belns',
    BEL_FRAMEWORK_2013 + '/namespace/swissprot-ids.belns',
    BEL_FRAMEWORK_2013 + '/namespace/swissprot.belns',
]

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

default_namespaces_2015 = [BEL_FRAMEWORK_2015 + '/namespace/' + namespace for namespace in namespaces_2015]
fraunhofer_namespaces = [FRAUNHOFER_RESOURCES + namespace for namespace in namespaces_2015]

default_namespaces = default_namespaces_1 + default_namespaces_2013 + default_namespaces_2015

default_annotations_1 = [
    BEL_FRAMEWORK_2012 + '/annotation/atcc-cell-line.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-body-region.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-cardiovascular-system.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-cell-structure.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-cell.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-digestive-system.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-disease.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-embryonic-structure.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-endocrine-system.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-fluid-and-secretion.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-hemic-and-immune-system.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-integumentary-system.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-musculoskeletal-system.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-nervous-system.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-respiratory-system.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-sense-organ.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-stomatognathic-system.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-tissue.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/mesh-urogenital-system.belanno',
    BEL_FRAMEWORK_2012 + '/annotation/species-taxonomy-id.belanno',
]

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

default_annotations_2013 = [BEL_FRAMEWORK_2013 + '/annotation/' + annotation for annotation in annotations_current]
default_annotations_2015 = [BEL_FRAMEWORK_2015 + '/annotation/' + annotation for annotation in annotations_current]
fraunhofer_annotations = [FRAUNHOFER_RESOURCES + annotation for annotation in annotations_current]

default_annotations = default_annotations_1 + default_annotations_2013 + default_annotations_2015

default_equivalences_1 = [
    BEL_FRAMEWORK_2012 + '/equivalence/affy-hg-u133-plus2.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/affy-hg-u133ab.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/affy-hg-u95av2.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/affy-mg-u74abc.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/affy-moe430ab.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/affy-mouse430-2.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/affy-mouse430a-2.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/affy-rae230ab-2.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/affy-rat230-2.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/chebi-ids.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/chebi-names.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/entrez-gene-ids-hmr.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/go-biological-processes-accession-numbers.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/go-biological-processes-names.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/go-cellular-component-accession-numbers.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/go-cellular-component-terms.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/hgnc-approved-symbols.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/mesh-biological-processes.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/mesh-cellular-locations.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/mesh-diseases.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/mgi-approved-symbols.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/rgd-approved-symbols.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/selventa-named-human-complexes.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/selventa-named-human-protein-families.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/selventa-named-mouse-complexes.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/selventa-named-mouse-protein-families.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/selventa-named-rat-complexes.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/selventa-named-rat-protein-families.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/swissprot-accession-numbers.beleq',
    BEL_FRAMEWORK_2012 + '/equivalence/swissprot-entry-names.beleq'
]

default_equivalences_2013 = [
    BEL_FRAMEWORK_2013 + '/equivalence/affy-probeset-ids.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/chebi-ids.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/chebi.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/disease-ontology-ids.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/disease-ontology.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/entrez-gene-ids.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/go-biological-process-ids.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/go-biological-process.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/go-cellular-component-ids.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/go-cellular-component.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/hgnc-human-genes.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/mesh-cellular-structures.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/mesh-diseases.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/mesh-processes.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/mgi-mouse-genes.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/rgd-rat-genes.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/selventa-legacy-chemicals.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/selventa-legacy-diseases.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/selventa-named-complexes.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/selventa-protein-families.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/swissprot-ids.beleq',
    BEL_FRAMEWORK_2013 + '/equivalence/swissprot.beleq'

]

default_equivalences_2015 = [
    BEL_FRAMEWORK_2015 + '/equivalence/affy-probeset-ids.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/chebi-ids.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/chebi.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/disease-ontology-ids.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/disease-ontology.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/entrez-gene-ids.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/go-biological-process-ids.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/go-biological-process.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/go-cellular-component-ids.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/go-cellular-component.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/hgnc-human-genes.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/mesh-cellular-structures-ids.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/mesh-cellular-structures.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/mesh-chemicals-ids.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/mesh-chemicals.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/mesh-diseases-ids.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/mesh-diseases.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/mesh-processes-ids.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/mesh-processes.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/mgi-mouse-genes.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/rgd-rat-genes.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/selventa-legacy-chemicals.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/selventa-legacy-diseases.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/selventa-named-complexes.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/selventa-protein-families.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/swissprot-ids.beleq',
    BEL_FRAMEWORK_2015 + '/equivalence/swissprot.beleq'
]

default_equivalences = default_equivalences_1 + default_equivalences_2013 + default_equivalences_2015

default_owl = [
    'http://purl.obolibrary.org/obo/hp/releases/2016-09-03/hp.owl',  # Human Phenotype Ontology
    'http://purl.obolibrary.org/obo/pr/49.0./pr-non-classified.owl'  # Protein Ontology
]
