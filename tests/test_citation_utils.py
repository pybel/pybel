# -*- coding: utf-8 -*-

import unittest

from pybel import BELGraph
from pybel.constants import *
from pybel.manager.citation_utils import enrich_pubmed_citations, get_citations_by_pmids, sanitize_date
from pybel.manager.models import Citation
from pybel.struct.summary.provenance import get_pubmed_identifiers
from tests.constants import TemporaryCacheMixin


class TestSanitizeDate(unittest.TestCase):
    def test_sanitize_1(self):
        self.assertEqual('2012-12-19', sanitize_date('2012 Dec 19'))

    def test_sanitize_2(self):
        self.assertEqual('2012-12-01', sanitize_date('2012 Dec'))

    def test_sanitize_3(self):
        self.assertEqual('2012-01-01', sanitize_date('2012'))

    def test_sanitize_4(self):
        self.assertEqual('2012-10-01', sanitize_date('2012 Oct-Dec'))

    def test_sanitize_5(self):
        self.assertEqual('2012-03-01', sanitize_date('2012 Spring'))

    def test_sanitize_6(self):
        self.assertEqual('2012-12-12', sanitize_date('2012 Dec 12-15'))

    def test_sanitize_nope(self):
        self.assertEqual(None, sanitize_date('2012 Early Spring'))


class TestCitations(TemporaryCacheMixin):
    def setUp(self):
        super(TestCitations, self).setUp()

        self.pmid = "9611787"

        g = BELGraph()

        g.add_node(1)
        g.add_node(2)

        g.add_edge(1, 2, attr_dict={
            CITATION: {
                CITATION_TYPE: CITATION_TYPE_PUBMED,
                CITATION_REFERENCE: self.pmid
            }
        })

        self.graph = g

    def test_enrich(self):
        pmids = get_pubmed_identifiers(self.graph)

        stored_citations = self.manager.session.query(Citation).all()

        self.assertEqual(0, len(stored_citations))

        get_citations_by_pmids(pmids, manager=self.manager)

        stored_citations = self.manager.session.query(Citation).all()
        self.assertEqual(1, len(stored_citations))

    def test_enrich_list(self):
        pmids = [
            '25818332',
            '27003210',
            '26438529',
            '26649137',
        ]

        get_citations_by_pmids(pmids, manager=self.manager)

        citation = self.manager.get_or_create_citation(type=CITATION_TYPE_PUBMED, reference='25818332')
        self.assertIsNotNone(citation)

    def test_enrich_list_grouped(self):
        pmids = [
            '25818332',
            '27003210',
            '26438529',
            '26649137',
        ]

        get_citations_by_pmids(pmids, manager=self.manager, group_size=2)

        citation = self.manager.get_or_create_citation(type=CITATION_TYPE_PUBMED, reference='25818332')
        self.assertIsNotNone(citation)

    def test_enrich_overwrite(self):
        citation = self.manager.get_or_create_citation(type=CITATION_TYPE_PUBMED, reference=self.pmid)
        self.manager.session.commit()
        self.assertIsNone(citation.date)
        self.assertIsNone(citation.name)

        enrich_pubmed_citations(self.graph, manager=self.manager)

        _, _, d = self.graph.edges(data=True)[0]
        citation_dict = d[CITATION]

        self.assertIn(CITATION_NAME, citation_dict)

        self.assertIn(CITATION_DATE, citation_dict)
        self.assertEqual('1998-05-01', citation_dict[CITATION_DATE])

        self.assertIn(CITATION_AUTHORS, citation_dict)
        self.assertEqual(
            {'Lewell XQ', 'Judd DB', 'Watson SP', 'Hann MM'},
            set(citation_dict[CITATION_AUTHORS])
        )

    def test_enrich_graph(self):
        enrich_pubmed_citations(self.graph, manager=self.manager)

        _, _, d = self.graph.edges(data=True)[0]
        citation_dict = d[CITATION]

        self.assertIn(CITATION_NAME, citation_dict)

        self.assertIn(CITATION_DATE, citation_dict)
        self.assertEqual('1998-05-01', citation_dict[CITATION_DATE])

        self.assertIn(CITATION_AUTHORS, citation_dict)
        self.assertEqual(
            {'Lewell XQ', 'Judd DB', 'Watson SP', 'Hann MM'},
            set(citation_dict[CITATION_AUTHORS])
        )


if __name__ == '__main__':
    unittest.main()
