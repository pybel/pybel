# -*- coding: utf-8 -*-

"""Tests for node predicates."""

import unittest

from pybel import BELGraph
from pybel.constants import (
    ACTIVITY, ANNOTATIONS, ASSOCIATION, CAUSES_NO_CHANGE, CITATION, CITATION_AUTHORS,
    CITATION_REFERENCE, CITATION_TYPE, CITATION_TYPE_ONLINE, CITATION_TYPE_PUBMED, DECREASES, DEGRADATION,
    DIRECTLY_DECREASES, DIRECTLY_INCREASES, EVIDENCE, GMOD, INCREASES, LOCATION, MODIFIER, OBJECT, POLAR_RELATIONS,
    POSITIVE_CORRELATION, RELATION, SUBJECT, TRANSLOCATION,
)
from pybel.dsl import (
    abundance, activity, degradation, entity, fragment, gene, gmod, hgvs, pmod, protein, secretion,
    translocation,
)
from pybel.struct.filters.edge_predicate_builders import build_relation_predicate
from pybel.struct.filters.edge_predicates import (
    edge_has_activity, edge_has_annotation, edge_has_degradation,
    edge_has_translocation, has_authors, has_polarity, has_provenance, has_pubmed, is_associative_relation,
    is_causal_relation, is_direct_causal_relation,
)
from pybel.struct.filters.node_predicates import (
    has_activity, has_causal_in_edges, has_causal_out_edges, has_fragment,
    has_gene_modification, has_hgvs, has_protein_modification, has_variant, is_abundance, is_causal_central,
    is_causal_sink, is_causal_source, is_degraded, is_gene, is_pathology, is_protein, is_translocated,
    keep_node_permissive, node_exclusion_predicate_builder, node_inclusion_predicate_builder, not_pathology,
)
from pybel.testing.utils import n

p1 = protein(name='BRAF', namespace='HGNC')
p2 = protein(name='BRAF', namespace='HGNC', variants=[hgvs('p.Val600Glu'), pmod('Ph')])
p3 = protein(name='APP', namespace='HGNC', variants=fragment(start=672, stop=713))
p4 = protein(name='2', namespace='HGNC')

g1 = gene(name='BRAF', namespace='HGNC', variants=gmod('Me'))


class TestNodePredicates(unittest.TestCase):
    """Tests for node predicates."""

    def test_none_data(self):
        """Test permissive node predicate with a node data dictionary."""
        self.assertTrue(keep_node_permissive(p1))

    def test_none(self):
        """Test permissive node predicate with graph and tuple."""
        g = BELGraph()
        p1_tuple = g.add_node_from_data(p1)
        self.assertTrue(keep_node_permissive(g, p1_tuple))

    def test_p1_data_variants(self):
        """Test node predicates on BRAF."""
        self.assertFalse(is_abundance(p1))
        self.assertFalse(is_gene(p1))
        self.assertTrue(is_protein(p1))
        self.assertFalse(is_pathology(p1))
        self.assertTrue(not_pathology(p1))

        self.assertFalse(has_variant(p1))
        self.assertFalse(has_protein_modification(p1))
        self.assertFalse(has_gene_modification(p1))
        self.assertFalse(has_hgvs(p1))
        self.assertFalse(has_fragment(p1))

    def test_p1_tuple_variants(self):
        """Test node predicates on the node tuple from BRAF.s"""
        g = BELGraph()
        p1_tuple = g.add_node_from_data(p1)

        self.assertFalse(is_abundance(g, p1_tuple))
        self.assertFalse(is_gene(g, p1_tuple))
        self.assertTrue(is_protein(g, p1_tuple))
        self.assertFalse(is_pathology(g, p1_tuple))
        self.assertTrue(not_pathology(g, p1_tuple))

        self.assertFalse(has_variant(g, p1_tuple))
        self.assertFalse(has_protein_modification(g, p1_tuple))
        self.assertFalse(has_gene_modification(g, p1_tuple))
        self.assertFalse(has_hgvs(g, p1_tuple))

    def test_p2_data_variants(self):
        self.assertFalse(is_abundance(p2))
        self.assertFalse(is_gene(p2))
        self.assertTrue(is_protein(p2))
        self.assertFalse(is_pathology(p2))
        self.assertTrue(not_pathology(p2))

        self.assertTrue(has_variant(p2))
        self.assertFalse(has_gene_modification(p2))
        self.assertTrue(has_protein_modification(p2))
        self.assertTrue(has_hgvs(p2))

    def test_p2_tuple_variants(self):
        g = BELGraph()
        p2_tuple = g.add_node_from_data(p2)

        self.assertFalse(is_abundance(g, p2_tuple))
        self.assertFalse(is_gene(g, p2_tuple))
        self.assertTrue(is_protein(g, p2_tuple))
        self.assertFalse(is_pathology(g, p2_tuple))
        self.assertTrue(not_pathology(g, p2_tuple))

        self.assertTrue(has_variant(g, p2_tuple))
        self.assertFalse(has_gene_modification(g, p2_tuple))
        self.assertTrue(has_protein_modification(g, p2_tuple))
        self.assertTrue(has_hgvs(g, p2_tuple))

    def test_p3(self):
        self.assertFalse(is_abundance(p3))
        self.assertFalse(is_gene(p3))
        self.assertTrue(is_protein(p3))
        self.assertFalse(is_pathology(p3))
        self.assertTrue(not_pathology(p3))

        self.assertTrue(has_variant(p3))
        self.assertFalse(has_gene_modification(p3))
        self.assertFalse(has_protein_modification(p3))
        self.assertFalse(has_hgvs(p3))
        self.assertTrue(has_fragment(p3))

    def test_g1_variants(self):
        self.assertFalse(is_abundance(g1))
        self.assertTrue(is_gene(g1))
        self.assertFalse(is_protein(g1))
        self.assertFalse(is_pathology(g1))

        self.assertTrue(has_variant(g1))
        self.assertTrue(has_gene_modification(g1), msg='Should have {}: {}'.format(GMOD, g1))
        self.assertFalse(has_protein_modification(g1))
        self.assertFalse(has_hgvs(g1))

    def test_fragments(self):
        self.assertTrue(has_fragment(
            protein(name='APP', namespace='HGNC', variants=[fragment(start=672, stop=713, description='random text')])))
        self.assertTrue(has_fragment(protein(name='APP', namespace='HGNC', variants=[fragment()])))

    def test_p1_active(self):
        """cat(p(HGNC:HSD11B1)) increases deg(a(CHEBI:cortisol))"""
        g = BELGraph()
        u = g.add_node_from_data(protein(name='HSD11B1', namespace='HGNC'))
        v = g.add_node_from_data(abundance(name='cortisol', namespace='CHEBI', identifier='17650'))

        g.add_qualified_edge(
            u,
            v,
            relation=INCREASES,
            citation={
                CITATION_TYPE: CITATION_TYPE_ONLINE, CITATION_REFERENCE: 'https://www.ncbi.nlm.nih.gov/gene/3290'
            },
            evidence="Entrez Gene Summary: Human: The protein encoded by this gene is a microsomal enzyme that "
                     "catalyzes the conversion of the stress hormone cortisol to the inactive metabolite cortisone. "
                     "In addition, the encoded protein can catalyze the reverse reaction, the conversion of cortisone "
                     "to cortisol. Too much cortisol can lead to central obesity, and a particular variation in this "
                     "gene has been associated with obesity and insulin resistance in children. Two transcript "
                     "variants encoding the same protein have been found for this gene.",
            annotations={'Species': '9606'},
            subject_modifier=activity('cat'),
            object_modifier=degradation()
        )

        self.assertFalse(is_translocated(g, u))
        self.assertFalse(is_degraded(g, u))
        self.assertTrue(has_activity(g, u))

        self.assertFalse(is_translocated(g, v))
        self.assertTrue(is_degraded(g, v))
        self.assertFalse(has_activity(g, v))

    def test_object_has_translocation(self):
        """p(HGNC: EGF) increases tloc(p(HGNC: VCP), GOCCID: 0005634, GOCCID: 0005737)"""
        g = BELGraph()
        u = g.add_node_from_data(protein(name='EFG', namespace='HGNC'))
        v = g.add_node_from_data(protein(name='VCP', namespace='HGNC'))

        g.add_qualified_edge(
            u,
            v,
            relation=INCREASES,
            citation='10855792',
            evidence="Although found predominantly in the cytoplasm and, less abundantly, in the nucleus, VCP can be "
                     "translocated from the nucleus after stimulation with epidermal growth factor.",
            annotations={'Species': '9606'},
            object_modifier=translocation(
                from_loc=entity(namespace='GO', identifier='0005634'),
                to_loc=entity(namespace='GO', identifier='0005737')
            )
        )

        self.assertFalse(is_translocated(g, u))
        self.assertFalse(is_degraded(g, u))
        self.assertFalse(has_activity(g, u))
        self.assertFalse(has_causal_in_edges(g, u))
        self.assertTrue(has_causal_out_edges(g, u))

        self.assertTrue(is_translocated(g, v))
        self.assertFalse(is_degraded(g, v))
        self.assertFalse(has_activity(g, v))
        self.assertTrue(has_causal_in_edges(g, v))
        self.assertFalse(has_causal_out_edges(g, v))

    def test_object_has_secretion(self):
        """p(MGI:Il4) increases sec(p(MGI:Cxcl1))"""
        g = BELGraph()
        u = g.add_node_from_data(protein(name='Il4', namespace='MGI'))
        v = g.add_node_from_data(protein(name='Cxcl1', namespace='MGI'))

        g.add_increases(
            u,
            v,
            citation='10072486',
            evidence='Compared with controls treated with culture medium alone, IL-4 and IL-5 induced significantly '
                     'higher levels of MIP-2 and KC production; IL-4 also increased the production of MCP-1 '
                     '(Fig. 2, A and B)....we only tested the effects of IL-3, IL-4, IL-5, and IL-13 on chemokine '
                     'expression and cellular infiltration....Recombinant cytokines were used, ... to treat naive '
                     'BALB/c mice.',
            annotations={'Species': '10090', 'MeSH': 'bronchoalveolar lavage fluid'},
            object_modifier=secretion()
        )

        self.assertFalse(is_translocated(g, u))
        self.assertFalse(is_degraded(g, u))
        self.assertFalse(has_activity(g, u))
        self.assertFalse(has_causal_in_edges(g, u))
        self.assertTrue(has_causal_out_edges(g, u))

        self.assertTrue(is_translocated(g, v))
        self.assertFalse(is_degraded(g, v))
        self.assertFalse(has_activity(g, v))
        self.assertTrue(has_causal_in_edges(g, v))
        self.assertFalse(has_causal_out_edges(g, v))

    def test_subject_has_secretion(self):
        """sec(p(MGI:S100b)) increases a(CHEBI:"nitric oxide")"""
        g = BELGraph()
        u = g.add_node_from_data(protein(name='S100b', namespace='MGI'))
        v = g.add_node_from_data(abundance(name='nitric oxide', namespace='CHEBI'))

        g.add_increases(
            u,
            v,
            citation='11180510',
            evidence='S100B protein is also secreted by astrocytes and acts on these cells to stimulate nitric oxide '
                     'secretion in an autocrine manner.',
            annotations={'Species': '10090', 'Cell': 'astrocyte'},
            subject_modifier=secretion()
        )

        self.assertTrue(is_translocated(g, u))
        self.assertFalse(is_degraded(g, u))
        self.assertFalse(has_activity(g, u))
        self.assertFalse(has_causal_in_edges(g, u))
        self.assertTrue(has_causal_out_edges(g, u))

        self.assertFalse(is_translocated(g, v))
        self.assertFalse(is_degraded(g, v))
        self.assertFalse(has_activity(g, v))
        self.assertTrue(has_causal_in_edges(g, v))
        self.assertFalse(has_causal_out_edges(g, v))

    def test_node_exclusion_data(self):
        g = BELGraph()

        u = protein(name='S100b', namespace='MGI')
        v = abundance(name='nitric oxide', namespace='CHEBI')
        w = abundance(name='cortisol', namespace='CHEBI', identifier='17650')

        g.add_node_from_data(u)
        g.add_node_from_data(v)
        g.add_node_from_data(w)

        f = node_exclusion_predicate_builder([u])

        self.assertFalse(f(u))
        self.assertTrue(f(v))
        self.assertTrue(f(w))

        f = node_exclusion_predicate_builder([u, v])

        self.assertFalse(f(u))
        self.assertFalse(f(v))
        self.assertTrue(f(w))

        f = node_exclusion_predicate_builder([])

        self.assertTrue(f(u))
        self.assertTrue(f(v))
        self.assertTrue(f(w))

    def test_node_exclusion_tuples(self):
        g = BELGraph()
        u = g.add_node_from_data(protein(name='S100b', namespace='MGI'))
        v = g.add_node_from_data(abundance(name='nitric oxide', namespace='CHEBI'))
        w = g.add_node_from_data(abundance(name='cortisol', namespace='CHEBI', identifier='17650'))

        f = node_exclusion_predicate_builder([u])

        self.assertFalse(f(g, u))
        self.assertTrue(f(g, v))
        self.assertTrue(f(g, w))

        f = node_exclusion_predicate_builder([u, v])

        self.assertFalse(f(g, u))
        self.assertFalse(f(g, v))
        self.assertTrue(f(g, w))

        f = node_exclusion_predicate_builder([])

        self.assertTrue(f(g, u))
        self.assertTrue(f(g, v))
        self.assertTrue(f(g, w))

    def test_node_inclusion_data(self):
        g = BELGraph()

        u = protein(name='S100b', namespace='MGI')
        v = abundance(name='nitric oxide', namespace='CHEBI')
        w = abundance(name='cortisol', namespace='CHEBI', identifier='17650')

        g.add_node_from_data(u)
        g.add_node_from_data(v)
        g.add_node_from_data(w)

        f = node_inclusion_predicate_builder([u])

        self.assertTrue(f(u))
        self.assertFalse(f(v))
        self.assertFalse(f(w))

        f = node_inclusion_predicate_builder([u, v])

        self.assertTrue(f(u))
        self.assertTrue(f(v))
        self.assertFalse(f(w))

        f = node_inclusion_predicate_builder([])

        self.assertFalse(f(u))
        self.assertFalse(f(v))
        self.assertFalse(f(w))

    def test_node_inclusion_tuples(self):
        g = BELGraph()
        u = g.add_node_from_data(protein(name='S100b', namespace='MGI'))
        v = g.add_node_from_data(abundance(name='nitric oxide', namespace='CHEBI'))
        w = g.add_node_from_data(abundance(name='cortisol', namespace='CHEBI', identifier='17650'))

        f = node_inclusion_predicate_builder([u])

        self.assertTrue(f(g, u))
        self.assertFalse(f(g, v))
        self.assertFalse(f(g, w))

        f = node_inclusion_predicate_builder([u, v])

        self.assertTrue(f(g, u))
        self.assertTrue(f(g, v))
        self.assertFalse(f(g, w))

        f = node_inclusion_predicate_builder([])

        self.assertFalse(f(g, u))
        self.assertFalse(f(g, v))
        self.assertFalse(f(g, w))

    def test_causal_source(self):
        g = BELGraph()
        a, b, c = (protein(n(), n()) for _ in range(3))

        g.add_increases(a, b, n(), n())
        g.add_increases(b, c, n(), n())

        self.assertTrue(is_causal_source(g, a.as_tuple()))
        self.assertFalse(is_causal_central(g, a.as_tuple()))
        self.assertFalse(is_causal_sink(g, a.as_tuple()))

        self.assertFalse(is_causal_source(g, b.as_tuple()))
        self.assertTrue(is_causal_central(g, b.as_tuple()))
        self.assertFalse(is_causal_sink(g, b.as_tuple()))

        self.assertFalse(is_causal_source(g, c.as_tuple()))
        self.assertFalse(is_causal_central(g, c.as_tuple()))
        self.assertTrue(is_causal_sink(g, c.as_tuple()))


class TestEdgePredicate(unittest.TestCase):
    def test_has_polarity_dict(self):
        for relation in POLAR_RELATIONS:
            self.assertTrue(has_polarity({RELATION: relation}))

        self.assertFalse(has_polarity({RELATION: ASSOCIATION}))

    def test_has_polarity(self):
        g = BELGraph()
        a, b, c = (protein(n(), n()) for _ in range(3))
        g.add_increases(a, b, n(), n(), key=0)
        self.assertTrue(has_polarity(g, a.as_tuple(), b.as_tuple(), 0))

        g.add_association(b, c, n(), n(), key=0)
        self.assertFalse(has_polarity(g, b.as_tuple(), c.as_tuple(), 0))

    def test_has_provenance(self):
        self.assertFalse(has_provenance({}))
        self.assertFalse(has_provenance({CITATION: {}}))
        self.assertFalse(has_provenance({EVIDENCE: ''}))
        self.assertTrue(has_provenance({CITATION: {}, EVIDENCE: ''}))

    def test_has_pubmed(self):
        self.assertTrue(has_pubmed({CITATION: {CITATION_TYPE: CITATION_TYPE_PUBMED}}))
        self.assertFalse(has_pubmed({CITATION: {CITATION_TYPE: CITATION_TYPE_ONLINE}}))
        self.assertFalse(has_pubmed({}))

    def test_has_authors(self):
        self.assertFalse(has_authors({}))
        self.assertFalse(has_authors({CITATION: {}}))
        self.assertFalse(has_authors({CITATION: {CITATION_AUTHORS: []}}))
        self.assertTrue(has_authors({CITATION: {CITATION_AUTHORS: ['One guy']}}))

    def test_is_causal(self):
        self.assertTrue(is_causal_relation({RELATION: INCREASES}))
        self.assertTrue(is_causal_relation({RELATION: DECREASES}))
        self.assertTrue(is_causal_relation({RELATION: DIRECTLY_INCREASES}))
        self.assertTrue(is_causal_relation({RELATION: DIRECTLY_DECREASES}))

        self.assertFalse(is_causal_relation({RELATION: ASSOCIATION}))
        self.assertFalse(is_causal_relation({RELATION: POSITIVE_CORRELATION}))

    def test_is_direct_causal(self):
        self.assertTrue(is_direct_causal_relation({RELATION: DIRECTLY_INCREASES}))
        self.assertTrue(is_direct_causal_relation({RELATION: DIRECTLY_DECREASES}))

        self.assertFalse(is_direct_causal_relation({RELATION: INCREASES}))
        self.assertFalse(is_direct_causal_relation({RELATION: DECREASES}))
        self.assertFalse(is_direct_causal_relation({RELATION: ASSOCIATION}))
        self.assertFalse(is_direct_causal_relation({RELATION: POSITIVE_CORRELATION}))

    def test_is_association(self):
        self.assertTrue(is_associative_relation({RELATION: ASSOCIATION}))

        self.assertFalse(is_associative_relation({RELATION: INCREASES}))
        self.assertFalse(is_associative_relation({RELATION: CAUSES_NO_CHANGE}))
        self.assertFalse(is_associative_relation({RELATION: DECREASES}))
        self.assertFalse(is_associative_relation({RELATION: DIRECTLY_INCREASES}))
        self.assertFalse(is_associative_relation({RELATION: DIRECTLY_DECREASES}))

    def test_build_is_association(self):
        """Test build_relation_predicate."""
        alternate_is_associative_relation = build_relation_predicate(ASSOCIATION)

        g = BELGraph()
        g.add_edge(p1.as_tuple(), p2.as_tuple(), key=0, **{RELATION: ASSOCIATION})
        g.add_edge(p2.as_tuple(), p3.as_tuple(), key=0, **{RELATION: INCREASES})

        self.assertTrue(alternate_is_associative_relation(g, p1.as_tuple(), p2.as_tuple(), 0))
        self.assertFalse(alternate_is_associative_relation(g, p2.as_tuple(), p3.as_tuple(), 0))

    def test_build_is_increases_or_decreases(self):
        """Test build_relation_predicate with multiple relations."""
        is_increase_or_decrease = build_relation_predicate([INCREASES, DECREASES])

        g = BELGraph()
        g.add_edge(p1.as_tuple(), p2.as_tuple(), key=0, **{RELATION: ASSOCIATION})
        g.add_edge(p2.as_tuple(), p3.as_tuple(), key=0, **{RELATION: INCREASES})
        g.add_edge(p3.as_tuple(), p4.as_tuple(), key=0, **{RELATION: DECREASES})

        self.assertFalse(is_increase_or_decrease(g, p1.as_tuple(), p2.as_tuple(), 0))
        self.assertTrue(is_increase_or_decrease(g, p2.as_tuple(), p3.as_tuple(), 0))
        self.assertTrue(is_increase_or_decrease(g, p3.as_tuple(), p4.as_tuple(), 0))

    def test_has_degradation(self):
        self.assertTrue(edge_has_degradation({SUBJECT: {MODIFIER: DEGRADATION}}))
        self.assertTrue(edge_has_degradation({OBJECT: {MODIFIER: DEGRADATION}}))

        self.assertFalse(edge_has_degradation({SUBJECT: {MODIFIER: TRANSLOCATION}}))
        self.assertFalse(edge_has_degradation({SUBJECT: {MODIFIER: ACTIVITY}}))
        self.assertFalse(edge_has_degradation({SUBJECT: {LOCATION: None}}))
        self.assertFalse(edge_has_degradation({OBJECT: {MODIFIER: TRANSLOCATION}}))
        self.assertFalse(edge_has_degradation({OBJECT: {MODIFIER: ACTIVITY}}))
        self.assertFalse(edge_has_degradation({OBJECT: {LOCATION: None}}))

    def test_has_translocation(self):
        self.assertTrue(edge_has_translocation({SUBJECT: {MODIFIER: TRANSLOCATION}}))
        self.assertTrue(edge_has_translocation({OBJECT: {MODIFIER: TRANSLOCATION}}))

        self.assertFalse(edge_has_translocation({SUBJECT: {MODIFIER: ACTIVITY}}))
        self.assertFalse(edge_has_translocation({SUBJECT: {LOCATION: None}}))
        self.assertFalse(edge_has_translocation({SUBJECT: {MODIFIER: DEGRADATION}}))
        self.assertFalse(edge_has_translocation({OBJECT: {MODIFIER: ACTIVITY}}))
        self.assertFalse(edge_has_translocation({OBJECT: {LOCATION: None}}))
        self.assertFalse(edge_has_translocation({OBJECT: {MODIFIER: DEGRADATION}}))

    def test_has_activity(self):
        self.assertTrue(edge_has_activity({SUBJECT: {MODIFIER: ACTIVITY}}))
        self.assertTrue(edge_has_activity({OBJECT: {MODIFIER: ACTIVITY}}))

        self.assertFalse(edge_has_activity({SUBJECT: {MODIFIER: TRANSLOCATION}}))
        self.assertFalse(edge_has_activity({OBJECT: {MODIFIER: TRANSLOCATION}}))
        self.assertFalse(edge_has_activity({SUBJECT: {LOCATION: None}}))
        self.assertFalse(edge_has_activity({SUBJECT: {MODIFIER: DEGRADATION}}))
        self.assertFalse(edge_has_activity({OBJECT: {LOCATION: None}}))
        self.assertFalse(edge_has_activity({OBJECT: {MODIFIER: DEGRADATION}}))

    def test_has_annotation(self):
        self.assertFalse(edge_has_annotation({}, 'Subgraph'))
        self.assertFalse(edge_has_annotation({ANNOTATIONS: {}}, 'Subgraph'))
        self.assertFalse(edge_has_annotation({ANNOTATIONS: {'Subgraph': None}}, 'Subgraph'))
        self.assertTrue(edge_has_annotation({ANNOTATIONS: {'Subgraph': 'value'}}, 'Subgraph'))
        self.assertFalse(edge_has_annotation({ANNOTATIONS: {'Nope': 'value'}}, 'Subgraph'))
