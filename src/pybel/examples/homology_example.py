# -*- coding: utf-8 -*-

"""The following is an example of orthology annotations from
`HomoloGene:37670 <https://www.ncbi.nlm.nih.gov/homologene?LinkName=gene_homologene&from_uid=5594>`_"""

from ..dsl.nodes import gene
from ..struct.graph import BELGraph

__all__ = [
    'homology_graph'
]

# TODO make SGD resource

homology_graph = BELGraph(
    name='Homology and Equivalence Example Graph',
    version='1.0.0',
    description="Adds several equivalence and orthology relationships related to the mitogen-activated protein kinase "
                "(MAPK1)",
    authors='Charles Tapley Hoyt',
    contact='charles.hoyt@scai.fraunhofer.de',
)

homology_graph.namespace_url.update({
    'HGNC': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/hgnc-human-genes/hgnc-human-genes-20170725.belns',
    'MGI': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/hgnc-human-genes/hgnc-human-genes-20170725.belns',
    'RGD': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/hgnc-human-genes/hgnc-human-genes-20170725.belns',
    'FLYBASE': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/hgnc-human-genes/hgnc-human-genes-20170725.belns',
    # 'SGD': '?',

})

human_mapk1 = gene(namespace='HGNC', name='MAPK1', identifier='HGNC:6871')
human_mapk1_entrez = gene(namespace='ENTREZ', name='MAPK1', identifier='5594')

mouse_mapk1 = gene(namespace='MGI', name='Mapk1', identifier='MGI:1346858')
mouse_mapk1_entrez = gene(namespace='ENTREZ', name='Mapk1', identifier='26413')

rat_mapk1 = gene(namespace='RGD', name='Mapk1', identifier='70500')
rat_mapk1_entrez = gene(namespace='ENTREZ', name='Mapk1', identifier='116590')

fly_mapk1 = gene(namespace='FLYBASE', name='rl', identifier='FBgn0003256')
fly_mapk1_entrez = gene(namespace='ENTREZ', name='rl', identifier='3354888')

# yeast_mapk1 = gene(namespace='SGD', name='KSS1', identifier='SGD:S000003272')
# yeast_mapk1_entrez = gene(namespace='ENTREZ', name='KSS1', identifier='852931')

# TODO make homologene resource and add is_a relationships for this
# mapk1_homologene = gene(namespace='HOMOLOGENE', identifier='37670')

homology_graph.add_equivalence(human_mapk1, human_mapk1_entrez)
homology_graph.add_equivalence(mouse_mapk1, mouse_mapk1_entrez)
homology_graph.add_equivalence(rat_mapk1, rat_mapk1_entrez)
homology_graph.add_equivalence(fly_mapk1, fly_mapk1_entrez)
# graph.add_equivalence(yeast_mapk1, yeast_mapk1_entrez)

homology_graph.add_orthology(human_mapk1, mouse_mapk1)
homology_graph.add_orthology(human_mapk1, rat_mapk1)
homology_graph.add_orthology(human_mapk1, fly_mapk1)
# graph.add_orthology(human_mapk1, yeast_mapk1)
