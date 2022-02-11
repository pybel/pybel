# -*- coding: utf-8 -*-

"""Tests for edge predicate builders."""

import unittest

from pybel.constants import CITATION, CITATION_AUTHORS, CITATION_TYPE_PUBMED
from pybel.language import citation_dict
from pybel.struct.filters.edge_predicate_builders import (
    build_author_inclusion_filter,
    build_pmid_inclusion_filter,
)

pmid1 = "1"
pmid2 = "2"
pmid3 = "3"

author1 = "1"
author2 = "2"
author3 = "3"


class TestEdgePredicateBuilders(unittest.TestCase):
    """Tests for edge predicate builders."""

    def test_build_pmid_inclusion_filter(self):
        """Test building a predicate for a single PubMed identifier."""
        pmid_inclusion_filter = build_pmid_inclusion_filter(pmid1)

        self.assertTrue(
            pmid_inclusion_filter(
                {
                    CITATION: citation_dict(namespace=CITATION_TYPE_PUBMED, identifier=pmid1),
                }
            )
        )

        self.assertFalse(
            pmid_inclusion_filter(
                {
                    CITATION: citation_dict(namespace=CITATION_TYPE_PUBMED, identifier=pmid2),
                }
            )
        )

    def test_build_pmid_set_inclusion_filter(self):
        """Test building a predicate for multiple PubMed identifiers."""
        pmids = {pmid1, pmid2}
        pmid_inclusion_filter = build_pmid_inclusion_filter(pmids)

        self.assertTrue(
            pmid_inclusion_filter(
                {
                    CITATION: citation_dict(namespace=CITATION_TYPE_PUBMED, identifier=pmid1),
                }
            )
        )

        self.assertTrue(
            pmid_inclusion_filter(
                {
                    CITATION: citation_dict(namespace=CITATION_TYPE_PUBMED, identifier=pmid2),
                }
            )
        )

        self.assertFalse(
            pmid_inclusion_filter(
                {
                    CITATION: citation_dict(namespace=CITATION_TYPE_PUBMED, identifier=pmid3),
                }
            )
        )

    def test_build_author_inclusion_filter(self):
        """Test building a predicate for a single author."""
        author_inclusion_filter = build_author_inclusion_filter(author1)

        self.assertTrue(
            author_inclusion_filter(
                {
                    CITATION: citation_dict(
                        namespace=CITATION_TYPE_PUBMED,
                        identifier=pmid3,
                        authors=[author1],
                    ),
                }
            )
        )

        self.assertTrue(
            author_inclusion_filter(
                {
                    CITATION: citation_dict(
                        namespace=CITATION_TYPE_PUBMED,
                        identifier=pmid3,
                        authors=[author1, author2],
                    ),
                }
            )
        )

        self.assertFalse(
            author_inclusion_filter(
                {
                    CITATION: citation_dict(
                        namespace=CITATION_TYPE_PUBMED,
                        identifier=pmid3,
                        authors=[author3],
                    ),
                }
            )
        )

    def test_build_author_set_inclusion_filter(self):
        """Test building a predicate for multiple authors."""
        author = {author1, author2}
        author_inclusion_filter = build_author_inclusion_filter(author)

        self.assertTrue(author_inclusion_filter({CITATION: {CITATION_AUTHORS: [author1]}}))

        self.assertTrue(author_inclusion_filter({CITATION: {CITATION_AUTHORS: [author1, author2]}}))

        self.assertFalse(author_inclusion_filter({CITATION: {CITATION_AUTHORS: [author3]}}))
