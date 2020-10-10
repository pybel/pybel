# -*- coding: utf-8 -*-

"""Test the manager's citation utilities.

The test data can be created with the following script:

.. code-block:: python

    import json
    from pybel.manager.citation_utils import get_pubmed_citation_response

    DATA = {'29324713', '29359844', '9611787', '25818332', '26438529', '26649137', '27003210'}

    rv = get_pubmed_citation_response(DATA)
    with open('/Users/cthoyt/dev/bel/pybel/tests/test_manager/citation_data.json', 'w') as file:
        json.dump(rv, file, indent=2)

"""

import json
import os
import time
import unittest
from typing import Any, Iterable, Mapping
from unittest import mock

from pybel import BELGraph
from pybel.constants import (
    CITATION, CITATION_AUTHORS, CITATION_DATE, CITATION_JOURNAL, CITATION_TYPE_PUBMED,
)
from pybel.dsl import Protein
from pybel.language import CitationDict
from pybel.manager.citation_utils import (
    _enrich_citations, enrich_pubmed_citations, get_citations_by_pmids, sanitize_date,
)
from pybel.manager.models import Citation
from pybel.testing.cases import TemporaryCacheMixin
from pybel.testing.utils import n

HERE = os.path.abspath(os.path.dirname(__file__))

PUBMED_DATA_PATH = os.path.join(HERE, 'pubmed_citation_data.json')
with open(PUBMED_DATA_PATH) as _file:
    PUBMED_DATA = json.load(_file)

PMC_DATA_PATH = os.path.join(HERE, 'pmc_citation_data.json')
with open(PMC_DATA_PATH) as _file:
    PMC_DATA = json.load(_file)


def _mock_fn(pubmed_identifiers: Iterable[str]) -> Mapping[str, Any]:
    result = {
        'uids': pubmed_identifiers,
    }
    for pmid in pubmed_identifiers:
        result[pmid] = PUBMED_DATA['result'][pmid]
    return {'result': result}


mock_get_pubmed_citation_response = mock.patch(
    'pybel.manager.citation_utils.get_pubmed_citation_response',
    side_effect=_mock_fn,
)


def _mock_get_pmc_csl_item(pmc_id: str) -> Mapping[str, Any]:
    return PMC_DATA[pmc_id]


mock_get_pmc_csl_item = mock.patch(
    'pybel.manager.citation_utils.get_pmc_csl_item',
    side_effect=_mock_get_pmc_csl_item,
)


class TestSanitizeDate(unittest.TestCase):
    """Test sanitization of dates in various formats."""

    def test_sanitize_1(self):
        """Test YYYY Mon DD."""
        self.assertEqual('2012-12-19', sanitize_date('2012 Dec 19'))

    def test_sanitize_2(self):
        """Test YYYY Mon."""
        self.assertEqual('2012-12-01', sanitize_date('2012 Dec'))

    def test_sanitize_3(self):
        """Test YYYY."""
        self.assertEqual('2012-01-01', sanitize_date('2012'))

    def test_sanitize_4(self):
        """Test YYYY Mon-Mon."""
        self.assertEqual('2012-10-01', sanitize_date('2012 Oct-Dec'))

    def test_sanitize_5(self):
        """Test YYYY Season."""
        self.assertEqual('2012-03-01', sanitize_date('2012 Spring'))

    def test_sanitize_6(self):
        """Test YYYY Mon DD-DD."""
        self.assertEqual('2012-12-12', sanitize_date('2012 Dec 12-15'))

    def test_sanitize_7(self):
        """Test YYYY Mon DD-Mon DD."""
        self.assertEqual('2005-01-29', sanitize_date('2005 Jan 29-Feb 4'))

    def test_sanitize_nope(self):
        """Test failure."""
        self.assertEqual(None, sanitize_date('2012 Early Spring'))


class TestPubmed(TemporaryCacheMixin):
    """Tests for citations."""

    def setUp(self):
        super().setUp()
        self.u, self.v = (Protein(n(), n()) for _ in range(2))
        self.pmid = '9611787'
        self.graph = BELGraph()
        self.graph.add_increases(self.u, self.v, citation=self.pmid, evidence=n())

    @mock_get_pubmed_citation_response
    def test_enrich_pubmed(self, *_):
        self.assertEqual(0, self.manager.count_citations())
        get_citations_by_pmids(manager=self.manager, pmids=[self.pmid])
        self.assertEqual(1, self.manager.count_citations())

        c = self.manager.get_citation_by_pmid(self.pmid)
        self.assertIsNotNone(c)
        self.assertIsInstance(c, Citation)
        self.assertEqual(CITATION_TYPE_PUBMED, c.db)
        self.assertEqual(self.pmid, c.db_id)

    @mock_get_pubmed_citation_response
    def test_enrich_pubmed_list(self, *_):
        pmids = [
            '25818332',
            '27003210',
            '26438529',
            '26649137',
        ]

        get_citations_by_pmids(manager=self.manager, pmids=pmids)

        citation = self.manager.get_or_create_citation(namespace=CITATION_TYPE_PUBMED, identifier='25818332')
        self.assertIsNotNone(citation)

    @mock_get_pubmed_citation_response
    def test_enrich_pubmed_list_grouped(self, *_):
        pmids = [
            '25818332',
            '27003210',
            '26438529',
            '26649137',
        ]

        get_citations_by_pmids(manager=self.manager, pmids=pmids, group_size=2)

        citation = self.manager.get_citation_by_pmid('25818332')
        self.assertIsNotNone(citation)

    @mock_get_pubmed_citation_response
    def test_enrich_pubmed_overwrite(self, *_):
        citation = self.manager.get_or_create_citation(namespace=CITATION_TYPE_PUBMED, identifier=self.pmid)
        self.manager.session.commit()
        self.assertIsNone(citation.date)
        self.assertIsNone(citation.title)

        enrich_pubmed_citations(manager=self.manager, graph=self.graph)

        _, _, d = list(self.graph.edges(data=True))[0]
        citation_dict = d[CITATION]
        self.assertIsInstance(citation_dict, CitationDict)

        self.assertIn(CITATION_JOURNAL, citation_dict)
        self.assertIn(CITATION_DATE, citation_dict)
        self.assertEqual('1998-05-01', citation_dict[CITATION_DATE])

        self.assertIn(CITATION_AUTHORS, citation_dict)
        self.assertEqual(
            {'Lewell XQ', 'Judd DB', 'Watson SP', 'Hann MM'},
            set(citation_dict[CITATION_AUTHORS])
        )

    @mock_get_pubmed_citation_response
    def test_enrich_pubmed_graph(self, *_):
        enrich_pubmed_citations(manager=self.manager, graph=self.graph)

        _, _, d = list(self.graph.edges(data=True))[0]
        citation_dict = d[CITATION]
        self.assertIsInstance(citation_dict, CitationDict)

        self.assertIn(CITATION_JOURNAL, citation_dict)

        self.assertIn(CITATION_DATE, citation_dict)
        self.assertEqual('1998-05-01', citation_dict[CITATION_DATE])

        self.assertIn(CITATION_AUTHORS, citation_dict)
        self.assertEqual(
            {'Lewell XQ', 'Judd DB', 'Watson SP', 'Hann MM'},
            set(citation_dict[CITATION_AUTHORS])
        )

    @mock_get_pubmed_citation_response
    @unittest.skipIf(os.environ.get('DB') == 'mysql', reason='MySQL collation is wonky')
    def test_enrich_pubmed_accent_duplicate(self, *_):
        """Test when two authors, Gomez C and Goméz C are both checked that they are not counted as duplicates."""
        g1 = 'Gomez C'
        g2 = 'Gómez C'
        pmid_1, pmid_2 = pmids = [
            '29324713',
            '29359844',
        ]
        get_citations_by_pmids(manager=self.manager, pmids=pmids)

        time.sleep(1)

        x = self.manager.get_citation_by_pmid(pmid_1)
        self.assertIsNotNone(x)
        self.assertEqual('Martínez-Guillén JR', x.first.name, msg='wrong first author name')

        self.assertIn(g1, self.manager.object_cache_author)
        self.assertIn(g2, self.manager.object_cache_author)

        a1 = self.manager.get_author_by_name(g1)
        self.assertEqual(g1, a1.name)

        a2 = self.manager.get_author_by_name(g2)
        self.assertEqual(g2, a2.name)


class TestPMC(TemporaryCacheMixin):
    """Tests for citations."""

    def setUp(self):
        super().setUp()
        self.u, self.v = (Protein(n(), n()) for _ in range(2))
        self.citation_identifier = 'PMC6611653'
        self.graph = BELGraph()
        self.graph.add_increases(self.u, self.v, citation=('pmc', self.citation_identifier), evidence=n())

    @mock_get_pmc_csl_item
    def test_enrich_pmc(self, *_):
        errors = _enrich_citations(manager=self.manager, graph=self.graph, prefix='pmc')
        self.assertEqual(0, len(errors), msg=f'Got errors: {errors}')
        _, _, d = list(self.graph.edges(data=True))[0]
        citation_dict = d[CITATION]
        self.assertIsInstance(citation_dict, CitationDict)
        self.assertEqual('pmc', citation_dict.namespace)
        self.assertEqual(self.citation_identifier, citation_dict.identifier)

        self.assertIn(CITATION_JOURNAL, citation_dict)
        self.assertEqual('PLoS computational biology', citation_dict[CITATION_JOURNAL])

        self.assertIn(CITATION_DATE, citation_dict)
        self.assertEqual('2019-06-24', citation_dict[CITATION_DATE])

        self.assertIn(CITATION_AUTHORS, citation_dict)
        self.assertLess(0, len(citation_dict[CITATION_AUTHORS]))
        # TODO the eUtils and CSL thing both normalize the way autors look
