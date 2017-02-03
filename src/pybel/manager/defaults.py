# -*- coding: utf-8 -*-

"""
This file contains a listing of the default namespaces released in each version of OpenBEL, and other
common namespaces used to load into a new PyBEL namespace store.

Resources:

.. seealso:: Overview on OpenBEL namespaces https://wiki.openbel.org/display/BELNA/Namespaces+Overview>
.. seealso:: Building custom namespaces http://openbel-framework.readthedocs.io/en/latest/tutorials/building_custom_namespaces.html>
"""

default_namespaces_1 = [
    'http://resources.openbel.org/belframework/1.0/namespace/affy-hg-u133-plus2.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/affy-hg-u133ab.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/affy-hg-u95av2.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/affy-mg-u74abc.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/affy-moe430ab.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/affy-mouse430-2.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/affy-mouse430a-2.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/affy-rae230ab-2.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/affy-rat230-2.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/chebi-ids.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/chebi-names.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/entrez-gene-ids-hmr.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/go-biological-processes-accession-numbers.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/go-biological-processes-names.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/go-cellular-component-accession-numbers.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/go-cellular-component-terms.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/hgnc-approved-symbols.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/mesh-biological-processes.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/mesh-cellular-locations.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/mesh-diseases.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/mgi-approved-symbols.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/rgd-approved-symbols.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/selventa-legacy-chemical-names.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/selventa-legacy-diseases.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/selventa-named-human-complexes.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/selventa-named-human-protein-families.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/selventa-named-mouse-complexes.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/selventa-named-mouse-protein-families.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/selventa-named-rat-complexes.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/selventa-named-rat-protein-families.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/swissprot-accession-numbers.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/swissprot-entry-names.belns',
]
default_namespaces_2013 = [
    'http://resources.openbel.org/belframework/20131211/namespace/affy-probeset-ids.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/chebi-ids.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/chebi.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/disease-ontology-ids.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/disease-ontology.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/entrez-gene-ids.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/go-biological-process-ids.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/go-biological-process.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/go-cellular-component-ids.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/go-cellular-component.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/hgnc-human-genes.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/mesh-cellular-structures.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/mesh-diseases.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/mesh-processes.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/mgi-mouse-genes.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/rgd-rat-genes.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/selventa-legacy-chemicals.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/selventa-legacy-diseases.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/selventa-named-complexes.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/selventa-protein-families.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/swissprot-ids.belns',
    'http://resources.openbel.org/belframework/20131211/namespace/swissprot.belns',
]

default_namespaces_2015 = [
    'http://resource.belframework.org/belframework/20150611/namespace/affy-probeset-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/chebi-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/chebi.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/disease-ontology-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/disease-ontology.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/entrez-gene-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/go-biological-process-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/go-biological-process.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/go-cellular-component-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/go-cellular-component.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/hgnc-human-genes.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mesh-cellular-structures-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mesh-cellular-structures.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mesh-chemicals-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mesh-chemicals.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mesh-diseases-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mesh-diseases.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mesh-processes-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mesh-processes.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mgi-mouse-genes.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/rgd-rat-genes.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/selventa-legacy-chemicals.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/selventa-legacy-diseases.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/selventa-named-complexes.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/selventa-protein-families.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/swissprot-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/swissprot.belns'
]

default_namespaces = default_namespaces_1 + default_namespaces_2013 + default_namespaces_2015

default_annotations_1 = [
    'http://resource.belframework.org/belframework/1.0/annotation/atcc-cell-line.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-body-region.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-cardiovascular-system.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-cell-structure.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-cell.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-digestive-system.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-disease.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-embryonic-structure.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-endocrine-system.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-fluid-and-secretion.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-hemic-and-immune-system.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-integumentary-system.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-musculoskeletal-system.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-nervous-system.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-respiratory-system.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-sense-organ.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-stomatognathic-system.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-tissue.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/mesh-urogenital-system.belanno',
    'http://resource.belframework.org/belframework/1.0/annotation/species-taxonomy-id.belanno',
]

default_annotations_2013 = [
    'http://resource.belframework.org/belframework/20131211/annotation/anatomy.belanno',
    'http://resource.belframework.org/belframework/20131211/annotation/cell-line.belanno',
    'http://resource.belframework.org/belframework/20131211/annotation/cell-structure.belanno',
    'http://resource.belframework.org/belframework/20131211/annotation/cell.belanno',
    'http://resource.belframework.org/belframework/20131211/annotation/disease.belanno',
    'http://resource.belframework.org/belframework/20131211/annotation/mesh-anatomy.belanno',
    'http://resource.belframework.org/belframework/20131211/annotation/mesh-diseases.belanno',
    'http://resource.belframework.org/belframework/20131211/annotation/species-taxonomy-id.belanno',
]

default_annotations_2015 = [
    'http://resource.belframework.org/belframework/20150611/annotation/anatomy.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/cell-line.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/cell-structure.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/cell.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/disease.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/mesh-anatomy.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/mesh-diseases.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/species-taxonomy-id.belanno'
]

default_annotations = default_annotations_1 + default_annotations_2013 + default_annotations_2015

default_equivalences_1 = [
    'http://resources.openbel.org/belframework/1.0/equivalence/affy-hg-u133-plus2.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/affy-hg-u133ab.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/affy-hg-u95av2.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/affy-mg-u74abc.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/affy-moe430ab.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/affy-mouse430-2.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/affy-mouse430a-2.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/affy-rae230ab-2.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/affy-rat230-2.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/chebi-ids.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/chebi-names.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/entrez-gene-ids-hmr.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/go-biological-processes-accession-numbers.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/go-biological-processes-names.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/go-cellular-component-accession-numbers.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/go-cellular-component-terms.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/hgnc-approved-symbols.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/mesh-biological-processes.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/mesh-cellular-locations.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/mesh-diseases.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/mgi-approved-symbols.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/rgd-approved-symbols.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/selventa-named-human-complexes.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/selventa-named-human-protein-families.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/selventa-named-mouse-complexes.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/selventa-named-mouse-protein-families.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/selventa-named-rat-complexes.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/selventa-named-rat-protein-families.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/swissprot-accession-numbers.beleq',
    'http://resources.openbel.org/belframework/1.0/equivalence/swissprot-entry-names.beleq'
]

default_equivalences_2013 = [
    'http://resources.openbel.org/belframework/20131211/equivalence/affy-probeset-ids.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/chebi-ids.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/chebi.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/disease-ontology-ids.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/disease-ontology.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/entrez-gene-ids.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/go-biological-process-ids.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/go-biological-process.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/go-cellular-component-ids.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/go-cellular-component.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/hgnc-human-genes.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/mesh-cellular-structures.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/mesh-diseases.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/mesh-processes.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/mgi-mouse-genes.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/rgd-rat-genes.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/selventa-legacy-chemicals.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/selventa-legacy-diseases.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/selventa-named-complexes.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/selventa-protein-families.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/swissprot-ids.beleq',
    'http://resources.openbel.org/belframework/20131211/equivalence/swissprot.beleq'

]

default_equivalences_2015 = [
    'http://resources.openbel.org/belframework/20150611/equivalence/affy-probeset-ids.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/chebi-ids.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/chebi.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/disease-ontology-ids.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/disease-ontology.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/entrez-gene-ids.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/go-biological-process-ids.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/go-biological-process.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/go-cellular-component-ids.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/go-cellular-component.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/hgnc-human-genes.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/mesh-cellular-structures-ids.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/mesh-cellular-structures.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/mesh-chemicals-ids.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/mesh-chemicals.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/mesh-diseases-ids.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/mesh-diseases.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/mesh-processes-ids.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/mesh-processes.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/mgi-mouse-genes.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/rgd-rat-genes.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/selventa-legacy-chemicals.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/selventa-legacy-diseases.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/selventa-named-complexes.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/selventa-protein-families.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/swissprot-ids.beleq',
    'http://resources.openbel.org/belframework/20150611/equivalence/swissprot.beleq'
]

default_equivalences = default_equivalences_1 + default_equivalences_2013 + default_equivalences_2015

default_owl = [
    'http://purl.obolibrary.org/obo/hp/releases/2016-09-03/hp.owl',  # Human Phenotype Ontology
    'http://purl.obolibrary.org/obo/pr/49.0./pr-non-classified.owl'  # Protein Ontology
]
