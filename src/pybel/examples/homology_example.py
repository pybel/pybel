# -*- coding: utf-8 -*-

"""An example with orthology statements.

The following is an example of orthology annotations from
`HomoloGene:37670 <https://www.ncbi.nlm.nih.gov/homologene?LinkName=gene_homologene&from_uid=5594>`_

.. code-block: none

    SET Citation = {"PubMed","J Immunol 1999 Sep 1 163(5) 2452-62","10452980","","",""}
    SET Evidence = "M-CSF triggers the activation of extracellular signal-regulated protein kinases (ERK)-1/2."
    SET Species = 10090
    p(MGI:Csf1) increases kin(p(MGI:Mapk1))
"""

from ..dsl import activity, gene, protein, rna
from ..struct.graph import BELGraph

__all__ = [
    'homology_graph'
]

# TODO make SGD resource

homology_graph = BELGraph(
    name='Homology and Equivalence Example Graph',
    version='1.0.1',
    description="Adds several equivalence and orthology relationships related to the mitogen-activated protein kinase "
                "(MAPK1)",
    authors='Charles Tapley Hoyt',
    contact='charles.hoyt@scai.fraunhofer.de',
)

homology_graph.namespace_url.update({
    'HGNC': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/hgnc-human-genes/hgnc-human-genes-20170725.belns',
    'MGI': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/mgi-mouse-genes/mgi-mouse-genes-20170725.belns',
    'RGD': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/rgd-rat-genes/rgd-rat-genes-20170725.belns',
    'FLYBASE': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/flybase/flybase-20170508.belns',
    'ENTREZ': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/entrez-gene-ids/entrez-gene-ids-20170725.belns',
    # 'SGD': '?',
})

homology_graph.annotation_url.update({
    'Species': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/species-taxonomy-id/species-taxonomy-id-20170511.belanno'
})

human_mapk1_gene = gene(namespace='HGNC', name='MAPK1', identifier='HGNC:6871')
human_mapk1_gene_entrez = gene(namespace='ENTREZ', name='5594')
human_mapk1_rna = rna(namespace='HGNC', name='MAPK1', identifier='HGNC:6871')
human_mapk1_protein = protein(namespace='HGNC', name='MAPK1', identifier='HGNC:6871')

mouse_mapk1_gene = gene(namespace='MGI', name='Mapk1', identifier='MGI:1346858')
mouse_mapk1_gene_entrez = gene(namespace='ENTREZ', name='26413')
mouse_mapk1_rna = rna(namespace='MGI', name='Mapk1', identifier='MGI:1346858')
mouse_mapk1_protein = protein(namespace='MGI', name='Mapk1', identifier='MGI:1346858')

rat_mapk1 = gene(namespace='RGD', name='Mapk1', identifier='70500')
rat_mapk1_entrez = gene(namespace='ENTREZ', name='116590')

fly_mapk1 = gene(namespace='FLYBASE', name='rl', identifier='FBgn0003256')
fly_mapk1_entrez = gene(namespace='ENTREZ', name='3354888')

human_csf1_gene = gene(namespace='HGNC', name='CSF1', identifier='HGNC:2432')
human_csf1_rna = rna(namespace='HGNC', name='CSF1', identifier='HGNC:2432')
human_csf1_protein = protein(namespace='HGNC', name='CSF1', identifier='HGNC:2432')

mouse_csf1_gene = gene(namespace='MGI', name='Csf1', identifier='MGI:1339753')
mouse_csf1_rna = rna(namespace='MGI', name='Csf1', identifier='MGI:1339753')
mouse_csf1_protein = protein(namespace='MGI', name='Csf1', identifier='MGI:1339753')

# yeast_mapk1 = gene(namespace='SGD', name='KSS1', identifier='SGD:S000003272')
# yeast_mapk1_entrez = gene(namespace='ENTREZ', name='KSS1', identifier='852931')

# TODO make homologene resource and add is_a relationships for this
# mapk1_homologene = gene(namespace='HOMOLOGENE', identifier='37670')

homology_graph.add_equivalence(human_mapk1_gene, human_mapk1_gene_entrez)
homology_graph.add_equivalence(mouse_mapk1_gene, mouse_mapk1_gene_entrez)
homology_graph.add_equivalence(rat_mapk1, rat_mapk1_entrez)
homology_graph.add_equivalence(fly_mapk1, fly_mapk1_entrez)
# graph.add_equivalence(yeast_mapk1, yeast_mapk1_entrez)

homology_graph.add_orthology(human_csf1_gene, mouse_csf1_gene)
homology_graph.add_orthology(human_mapk1_gene, mouse_mapk1_gene)
homology_graph.add_orthology(human_mapk1_gene, rat_mapk1)
homology_graph.add_orthology(human_mapk1_gene, fly_mapk1)
# graph.add_orthology(human_mapk1, yeast_mapk1)


"""SET Citation = {"PubMed","J Immunol 1999 Sep 1 163(5) 2452-62","10452980","","",""}
    SET Evidence = "M-CSF triggers the activation of extracellular signal-regulated protein kinases (ERK)-1/2."
    SET Species = 10090
    p(MGI:Csf1) increases kin(p(MGI:Mapk1))"""

homology_graph.add_increases(
    u=mouse_csf1_protein,
    v=mouse_mapk1_protein,
    citation='10452980',
    evidence='M-CSF triggers the activation of extracellular signal-regulated protein kinases (ERK)-1/2.',
    object_modifier=activity('kin'),
    annotations={'Species': '10090'}
)

homology_graph.add_transcription(mouse_mapk1_gene, mouse_mapk1_rna)
homology_graph.add_translation(mouse_mapk1_rna, mouse_mapk1_protein)

homology_graph.add_transcription(human_mapk1_gene, human_mapk1_rna)
homology_graph.add_translation(human_mapk1_rna, human_mapk1_protein)

homology_graph.add_transcription(human_csf1_gene, human_csf1_rna)
homology_graph.add_translation(human_csf1_rna, human_csf1_protein)

homology_graph.add_transcription(mouse_csf1_gene, mouse_csf1_rna)
homology_graph.add_translation(mouse_csf1_rna, mouse_csf1_protein)
