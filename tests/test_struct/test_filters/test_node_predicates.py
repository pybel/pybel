# -*- coding: utf-8 -*-

"""Tests for node predicates."""

import unittest

from pybel import BELGraph
from pybel.constants import (
    ACTIVITY,
    ANNOTATIONS,
    ASSOCIATION,
    CAUSES_NO_CHANGE,
    CITATION,
    CITATION_AUTHORS,
    CITATION_TYPE_PUBMED,
    CITATION_TYPE_URL,
    DECREASES,
    DEGRADATION,
    DIRECTLY_DECREASES,
    DIRECTLY_INCREASES,
    EVIDENCE,
    GMOD,
    IDENTIFIER,
    INCREASES,
    LOCATION,
    MODIFIER,
    NAMESPACE,
    POLAR_RELATIONS,
    POSITIVE_CORRELATION,
    RELATION,
    SOURCE_MODIFIER,
    TARGET_MODIFIER,
    TRANSLOCATION,
)
from pybel.dsl import (
    abundance,
    activity,
    degradation,
    fragment,
    gene,
    gmod,
    hgvs,
    pmod,
    protein,
    secretion,
    translocation,
)
from pybel.language import Entity
from pybel.struct.filters import false_node_predicate, true_node_predicate
from pybel.struct.filters.edge_predicate_builders import build_relation_predicate
from pybel.struct.filters.edge_predicates import (
    edge_has_activity,
    edge_has_annotation,
    edge_has_degradation,
    edge_has_translocation,
    has_authors,
    has_polarity,
    has_provenance,
    has_pubmed,
    is_associative_relation,
    is_causal_relation,
    is_direct_causal_relation,
)
from pybel.struct.filters.node_predicates import (
    has_activity,
    has_causal_in_edges,
    has_causal_out_edges,
    has_fragment,
    has_gene_modification,
    has_hgvs,
    has_protein_modification,
    has_variant,
    is_abundance,
    is_causal_central,
    is_causal_sink,
    is_causal_source,
    is_degraded,
    is_gene,
    is_pathology,
    is_protein,
    is_translocated,
    none_of,
    not_pathology,
    one_of,
)
from pybel.testing.utils import n

p1 = protein(name="BRAF", namespace="HGNC")
p2 = protein(name="BRAF", namespace="HGNC", variants=[hgvs("p.Val600Glu"), pmod("Ph")])
p3 = protein(name="APP", namespace="HGNC", variants=fragment(start=672, stop=713))
p4 = protein(name="2", namespace="HGNC")

g1 = gene(name="BRAF", namespace="HGNC", variants=gmod("Me"))


class TestNodePredicates(unittest.TestCase):
    """Tests for node predicates."""

    def test_none_data(self):
        """Test permissive node predicate with a node data dictionary."""
        self.assertTrue(true_node_predicate(p1))
        self.assertFalse(false_node_predicate(p1))

    def test_none(self):
        """Test permissive node predicate with graph and tuple."""
        g = BELGraph()
        g.add_node_from_data(p1)
        self.assertTrue(true_node_predicate(g, p1))
        self.assertFalse(false_node_predicate(g, p1))

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
        g.add_node_from_data(p1)

        self.assertFalse(is_abundance(g, p1))
        self.assertFalse(is_gene(g, p1))
        self.assertTrue(is_protein(g, p1))
        self.assertFalse(is_pathology(g, p1))
        self.assertTrue(not_pathology(g, p1))

        self.assertFalse(has_variant(g, p1))
        self.assertFalse(has_protein_modification(g, p1))
        self.assertFalse(has_gene_modification(g, p1))
        self.assertFalse(has_hgvs(g, p1))

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
        g.add_node_from_data(p2)

        self.assertFalse(is_abundance(g, p2))
        self.assertFalse(is_gene(g, p2))
        self.assertTrue(is_protein(g, p2))
        self.assertFalse(is_pathology(g, p2))
        self.assertTrue(not_pathology(g, p2))

        self.assertTrue(has_variant(g, p2))
        self.assertFalse(has_gene_modification(g, p2))
        self.assertTrue(has_protein_modification(g, p2))
        self.assertTrue(has_hgvs(g, p2))

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
        self.assertTrue(has_gene_modification(g1), msg="Should have {}: {}".format(GMOD, g1))
        self.assertFalse(has_protein_modification(g1))
        self.assertFalse(has_hgvs(g1))

    def test_fragments(self):
        self.assertTrue(
            has_fragment(
                protein(
                    name="APP",
                    namespace="HGNC",
                    variants=[fragment(start=672, stop=713, description="random text")],
                )
            )
        )
        self.assertTrue(has_fragment(protein(name="APP", namespace="HGNC", variants=[fragment()])))

    def test_p1_active(self):
        """cat(p(HGNC:HSD11B1)) increases deg(a(CHEBI:cortisol))"""
        g = BELGraph()
        g.annotation_pattern["Species"] = r"\d+"

        u = protein(name="HSD11B1", namespace="HGNC")
        v = abundance(name="cortisol", namespace="CHEBI", identifier="17650")

        g.add_increases(
            u,
            v,
            citation={
                NAMESPACE: CITATION_TYPE_URL,
                IDENTIFIER: "https://www.ncbi.nlm.nih.gov/gene/3290",
            },
            evidence="Entrez Gene Summary: Human: The protein encoded by this gene is a microsomal enzyme that "
            "catalyzes the conversion of the stress hormone cortisol to the inactive metabolite cortisone. "
            "In addition, the encoded protein can catalyze the reverse reaction, the conversion of cortisone "
            "to cortisol. Too much cortisol can lead to central obesity, and a particular variation in this "
            "gene has been associated with obesity and insulin resistance in children. Two transcript "
            "variants encoding the same protein have been found for this gene.",
            annotations={"Species": "9606"},
            source_modifier=activity("cat"),
            target_modifier=degradation(),
        )

        self.assertFalse(is_translocated(g, u))
        self.assertFalse(is_degraded(g, u))
        self.assertTrue(has_activity(g, u))

        self.assertFalse(is_translocated(g, v))
        self.assertTrue(is_degraded(g, v))
        self.assertFalse(has_activity(g, v))

    def test_object_has_translocation(self):
        """p(HGNC: EGF) increases tloc(p(HGNC: VCP), GO:0005634, GO:0005737)"""
        g = BELGraph()
        g.annotation_pattern["Species"] = r"\d+"
        u = protein(name="EFG", namespace="HGNC")
        v = protein(name="VCP", namespace="HGNC")

        g.add_increases(
            u,
            v,
            citation="10855792",
            evidence="Although found predominantly in the cytoplasm and, less abundantly, in the nucleus, VCP can be "
            "translocated from the nucleus after stimulation with epidermal growth factor.",
            annotations={"Species": "9606"},
            target_modifier=translocation(
                from_loc=Entity(namespace="GO", identifier="0005634"),
                to_loc=Entity(namespace="GO", identifier="0005737"),
            ),
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
        g.annotation_pattern["Species"] = r"\d+"
        g.annotation_pattern["MeSH"] = ".*"
        u = protein(name="Il4", namespace="MGI")
        v = protein(name="Cxcl1", namespace="MGI")

        g.add_increases(
            u,
            v,
            citation="10072486",
            evidence="Compared with controls treated with culture medium alone, IL-4 and IL-5 induced significantly "
            "higher levels of MIP-2 and KC production; IL-4 also increased the production of MCP-1 "
            "(Fig. 2, A and B)....we only tested the effects of IL-3, IL-4, IL-5, and IL-13 on chemokine "
            "expression and cellular infiltration....Recombinant cytokines were used, ... to treat naive "
            "BALB/c mice.",
            annotations={"Species": "10090", "MeSH": "bronchoalveolar lavage fluid"},
            target_modifier=secretion(),
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
        g.annotation_pattern["Species"] = r"\d+"
        g.annotation_pattern["Cell"] = r".*"
        u = protein(name="S100b", namespace="MGI")
        v = abundance(name="nitric oxide", namespace="CHEBI")

        g.add_increases(
            u,
            v,
            citation="11180510",
            evidence="S100B protein is also secreted by astrocytes and acts on these cells to stimulate nitric oxide "
            "secretion in an autocrine manner.",
            annotations={"Species": "10090", "Cell": "astrocyte"},
            source_modifier=secretion(),
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

        u = protein(name="S100b", namespace="MGI")
        v = abundance(name="nitric oxide", namespace="CHEBI")
        w = abundance(name="cortisol", namespace="CHEBI", identifier="17650")

        g.add_node_from_data(u)
        g.add_node_from_data(v)
        g.add_node_from_data(w)

        f = none_of([u])

        self.assertFalse(f(u))
        self.assertTrue(f(v))
        self.assertTrue(f(w))

        f = none_of([u, v])

        self.assertFalse(f(u))
        self.assertFalse(f(v))
        self.assertTrue(f(w))

        f = none_of([])

        self.assertTrue(f(u))
        self.assertTrue(f(v))
        self.assertTrue(f(w))

    def test_node_exclusion_tuples(self):
        g = BELGraph()

        u = protein(name="S100b", namespace="MGI")
        v = abundance(name="nitric oxide", namespace="CHEBI")
        w = abundance(name="cortisol", namespace="CHEBI", identifier="17650")

        g.add_node_from_data(u)
        g.add_node_from_data(v)
        g.add_node_from_data(w)

        f = none_of([u])

        self.assertFalse(f(g, u))
        self.assertTrue(f(g, v))
        self.assertTrue(f(g, w))

        f = none_of([u, v])

        self.assertFalse(f(g, u))
        self.assertFalse(f(g, v))
        self.assertTrue(f(g, w))

        f = none_of([])

        self.assertTrue(f(g, u))
        self.assertTrue(f(g, v))
        self.assertTrue(f(g, w))

    def test_node_inclusion_data(self):
        g = BELGraph()

        u = protein(name="S100b", namespace="MGI")
        v = abundance(name="nitric oxide", namespace="CHEBI")
        w = abundance(name="cortisol", namespace="CHEBI", identifier="17650")

        g.add_node_from_data(u)
        g.add_node_from_data(v)
        g.add_node_from_data(w)

        f = one_of([u])

        self.assertTrue(f(u))
        self.assertFalse(f(v))
        self.assertFalse(f(w))

        f = one_of([u, v])

        self.assertTrue(f(u))
        self.assertTrue(f(v))
        self.assertFalse(f(w))

        f = one_of([])

        self.assertFalse(f(u))
        self.assertFalse(f(v))
        self.assertFalse(f(w))

    def test_node_inclusion_tuples(self):
        g = BELGraph()

        u = protein(name="S100b", namespace="MGI")
        v = abundance(name="nitric oxide", namespace="CHEBI")
        w = abundance(name="cortisol", namespace="CHEBI", identifier="17650")

        g.add_node_from_data(u)
        g.add_node_from_data(v)
        g.add_node_from_data(w)

        f = one_of([u])

        self.assertTrue(f(g, u))
        self.assertFalse(f(g, v))
        self.assertFalse(f(g, w))

        f = one_of([u, v])

        self.assertTrue(f(g, u))
        self.assertTrue(f(g, v))
        self.assertFalse(f(g, w))

        f = one_of([])

        self.assertFalse(f(g, u))
        self.assertFalse(f(g, v))
        self.assertFalse(f(g, w))

    def test_causal_source(self):
        g = BELGraph()
        a, b, c = (protein(n(), n()) for _ in range(3))

        g.add_increases(a, b, citation=n(), evidence=n())
        g.add_increases(b, c, citation=n(), evidence=n())

        self.assertTrue(is_causal_source(g, a))
        self.assertFalse(is_causal_central(g, a))
        self.assertFalse(is_causal_sink(g, a))

        self.assertFalse(is_causal_source(g, b))
        self.assertTrue(is_causal_central(g, b))
        self.assertFalse(is_causal_sink(g, b))

        self.assertFalse(is_causal_source(g, c))
        self.assertFalse(is_causal_central(g, c))
        self.assertTrue(is_causal_sink(g, c))


class TestEdgePredicate(unittest.TestCase):
    def test_has_polarity_dict(self):
        for relation in POLAR_RELATIONS:
            self.assertTrue(has_polarity({RELATION: relation}))

        self.assertFalse(has_polarity({RELATION: ASSOCIATION}))

    def test_has_polarity(self):
        g = BELGraph()
        a, b, c = (protein(n(), n()) for _ in range(3))
        key1 = g.add_increases(a, b, citation=n(), evidence=n())
        self.assertTrue(has_polarity(g, a, b, key1))

        key2 = g.add_association(b, c, citation=n(), evidence=n())
        self.assertFalse(has_polarity(g, b, c, key2))

    def test_has_provenance(self):
        self.assertFalse(has_provenance({}))
        self.assertFalse(has_provenance({CITATION: {}}))
        self.assertFalse(has_provenance({EVIDENCE: ""}))
        self.assertTrue(has_provenance({CITATION: {}, EVIDENCE: ""}))

    def test_has_pubmed(self):
        self.assertTrue(has_pubmed({CITATION: {NAMESPACE: CITATION_TYPE_PUBMED}}))
        self.assertFalse(has_pubmed({CITATION: {NAMESPACE: CITATION_TYPE_URL}}))
        self.assertFalse(has_pubmed({}))

    def test_has_authors(self):
        self.assertFalse(has_authors({}))
        self.assertFalse(has_authors({CITATION: {}}))
        self.assertFalse(has_authors({CITATION: {CITATION_AUTHORS: []}}))
        self.assertTrue(has_authors({CITATION: {CITATION_AUTHORS: ["One guy"]}}))

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
        g.add_edge(p1, p2, key=0, **{RELATION: ASSOCIATION})
        g.add_edge(p2, p3, key=0, **{RELATION: INCREASES})

        self.assertTrue(alternate_is_associative_relation(g, p1, p2, 0))
        self.assertFalse(alternate_is_associative_relation(g, p2, p3, 0))

    def test_build_is_increases_or_decreases(self):
        """Test build_relation_predicate with multiple relations."""
        is_increase_or_decrease = build_relation_predicate([INCREASES, DECREASES])

        g = BELGraph()
        g.add_edge(p1, p2, key=0, **{RELATION: ASSOCIATION})
        g.add_edge(p2, p3, key=0, **{RELATION: INCREASES})
        g.add_edge(p3, p4, key=0, **{RELATION: DECREASES})

        self.assertFalse(is_increase_or_decrease(g, p1, p2, 0))
        self.assertTrue(is_increase_or_decrease(g, p2, p3, 0))
        self.assertTrue(is_increase_or_decrease(g, p3, p4, 0))

    def test_has_degradation(self):
        self.assertTrue(edge_has_degradation({SOURCE_MODIFIER: {MODIFIER: DEGRADATION}}))
        self.assertTrue(edge_has_degradation({TARGET_MODIFIER: {MODIFIER: DEGRADATION}}))

        self.assertFalse(edge_has_degradation({SOURCE_MODIFIER: {MODIFIER: TRANSLOCATION}}))
        self.assertFalse(edge_has_degradation({SOURCE_MODIFIER: {MODIFIER: ACTIVITY}}))
        self.assertFalse(edge_has_degradation({SOURCE_MODIFIER: {LOCATION: None}}))
        self.assertFalse(edge_has_degradation({TARGET_MODIFIER: {MODIFIER: TRANSLOCATION}}))
        self.assertFalse(edge_has_degradation({TARGET_MODIFIER: {MODIFIER: ACTIVITY}}))
        self.assertFalse(edge_has_degradation({TARGET_MODIFIER: {LOCATION: None}}))

    def test_has_translocation(self):
        self.assertTrue(edge_has_translocation({SOURCE_MODIFIER: {MODIFIER: TRANSLOCATION}}))
        self.assertTrue(edge_has_translocation({TARGET_MODIFIER: {MODIFIER: TRANSLOCATION}}))

        self.assertFalse(edge_has_translocation({SOURCE_MODIFIER: {MODIFIER: ACTIVITY}}))
        self.assertFalse(edge_has_translocation({SOURCE_MODIFIER: {LOCATION: None}}))
        self.assertFalse(edge_has_translocation({SOURCE_MODIFIER: {MODIFIER: DEGRADATION}}))
        self.assertFalse(edge_has_translocation({TARGET_MODIFIER: {MODIFIER: ACTIVITY}}))
        self.assertFalse(edge_has_translocation({TARGET_MODIFIER: {LOCATION: None}}))
        self.assertFalse(edge_has_translocation({TARGET_MODIFIER: {MODIFIER: DEGRADATION}}))

    def test_has_activity(self):
        self.assertTrue(edge_has_activity({SOURCE_MODIFIER: {MODIFIER: ACTIVITY}}))
        self.assertTrue(edge_has_activity({TARGET_MODIFIER: {MODIFIER: ACTIVITY}}))

        self.assertFalse(edge_has_activity({SOURCE_MODIFIER: {MODIFIER: TRANSLOCATION}}))
        self.assertFalse(edge_has_activity({TARGET_MODIFIER: {MODIFIER: TRANSLOCATION}}))
        self.assertFalse(edge_has_activity({SOURCE_MODIFIER: {LOCATION: None}}))
        self.assertFalse(edge_has_activity({SOURCE_MODIFIER: {MODIFIER: DEGRADATION}}))
        self.assertFalse(edge_has_activity({TARGET_MODIFIER: {LOCATION: None}}))
        self.assertFalse(edge_has_activity({TARGET_MODIFIER: {MODIFIER: DEGRADATION}}))

    def test_has_annotation(self):
        self.assertFalse(edge_has_annotation({}, "Subgraph"))
        self.assertFalse(edge_has_annotation({ANNOTATIONS: {}}, "Subgraph"))
        self.assertFalse(edge_has_annotation({ANNOTATIONS: {"Subgraph": None}}, "Subgraph"))
        self.assertTrue(edge_has_annotation({ANNOTATIONS: {"Subgraph": "value"}}, "Subgraph"))
        self.assertFalse(edge_has_annotation({ANNOTATIONS: {"Nope": "value"}}, "Subgraph"))
