"""
This file contains a dictionary of the default namespaces
and URLs to load into a new PyBEL namespace store.

See: https://wiki.openbel.org/display/BELNA/Namespaces+Overview
"""

default_namespaces = [
    # 1.0 Release
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
    'http://resources.openbel.org/belframework/1.0/namespace/go-biological-processes-accession-numbers.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/go-biological-processes-names.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/go-cellular-component-accession-numbers.belns',
    'http://resources.openbel.org/belframework/1.0/namespace/go-cellular-component-accession-numbers.belns.s',
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

    # 2013 Release
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

    # 2015 Release
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

default_annotations = [
    # 1.0  Release
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

    # 2013 Release
    'http://resource.belframework.org/belframework/20131211/annotation/anatomy.belanno',
    'http://resource.belframework.org/belframework/20131211/annotation/cell-line.belanno',
    'http://resource.belframework.org/belframework/20131211/annotation/cell-structure.belanno',
    'http://resource.belframework.org/belframework/20131211/annotation/cell.belanno',
    'http://resource.belframework.org/belframework/20131211/annotation/disease.belanno',
    'http://resource.belframework.org/belframework/20131211/annotation/mesh-anatomy.belanno',
    'http://resource.belframework.org/belframework/20131211/annotation/mesh-diseases.belanno',
    'http://resource.belframework.org/belframework/20131211/annotation/species-taxonomy-id.belanno',

    # 2015 Release
    'http://resource.belframework.org/belframework/20150611/annotation/anatomy.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/cell-line.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/cell-structure.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/cell.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/disease.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/mesh-anatomy.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/mesh-diseases.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/species-taxonomy-id.belanno'
]

default_owl = [
    'http://purl.obolibrary.org/obo/hp/releases/2016-09-03/hp.owl',  # Human Phenotype Ontology
    'http://purl.obolibrary.org/obo/pr/49.0./pr-non-classified.owl'  # Protein Ontology
]
