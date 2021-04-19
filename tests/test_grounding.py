# -*- coding: utf-8 -*-

"""Test grounding."""

import unittest
from unittest import mock

import bioregistry
import pyobo
from pyobo.mocks import get_mock_id_name_mapping

from pybel.constants import ANNOTATIONS, CONCEPT, GMOD, IDENTIFIER, KIND, MEMBERS, NAME, NAMESPACE, PMOD, VARIANTS
from pybel.grounding import _NAME_REMAPPING, _process_annotations, _process_concept, _process_node
from pybel.language import Entity


def _failer(*_, **__):
    """Fail for all calls to this function."""
    raise ValueError('Called a PyOBO function that should be mocked')


pyobo.getters.get = _failer
pyobo.api.names.cached_mapping = _failer
pyobo.api.names.cached_multidict = _failer

mock_id_name_data = {
    'mesh': {
        'D009474': 'Neurons',
        'D010300': 'Parkinson Disease',
        'D013378': 'Substantia Nigra',
    },
    'doid': {
        '14330': "Parkinson's disease",
    },
    'go': {
        '0006468': 'protein phosphorylation',
    },
    'complexportal': {
        'CPX-1829': 'Checkpoint clamp complex',
    },
    'ncbitaxon': {
        '9606': 'Homo sapiens',
    },
    'cl': {
        '0000030': 'glioblast',
    },
}

mock_id_name_mapping = get_mock_id_name_mapping(mock_id_name_data)

_mock_mnemonic_data = {
    'O60921': 'HUS1_HUMAN',
    'Q99638': 'RAD9A_HUMAN',
    'O60671': 'RAD1_HUMAN',
}
_mock_reverse_mnemonic_data = {v: k for k, v in _mock_mnemonic_data.items()}


def _mock_get_mnemonic(identifier, *_, **__):
    return _mock_mnemonic_data[identifier]


mock_get_mnemonic = mock.patch('pybel.grounding.get_mnemonic', side_effect=_mock_get_mnemonic)
mock_get_id_from_mnemonic = mock.patch(
    'pybel.grounding.get_id_from_mnemonic',
    side_effect=_mock_reverse_mnemonic_data.get,
)


@mock_id_name_mapping
@mock_get_mnemonic
@mock_get_id_from_mnemonic
class TestProcessConcept(unittest.TestCase):
    """Test the :func:`_process_concept` function."""

    def _help(self, expected, d, msg=None):
        expected = {CONCEPT: expected}
        d = {CONCEPT: d}
        self.assertIsNotNone(bioregistry.normalize_prefix(expected[CONCEPT][NAMESPACE]), msg='Unrecognized namespace')
        _process_concept(concept=d[CONCEPT], node=d)
        self.assertEqual(expected[CONCEPT], d[CONCEPT], msg=msg)

    def test_normalize_prefix_case(self, *_):
        """Test normalizing the prefix to the correct case."""
        self._help(
            {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'},
            {NAMESPACE: 'MESH', NAME: 'Neurons', IDENTIFIER: 'D009474'},
        )

    def test_normalize_prefix_synonym(self, *_):
        """Test normalizing the prefix based on the synonym dictionary."""
        self._help(
            {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'},
            {NAMESPACE: 'MESHA', NAME: 'Neurons', IDENTIFIER: 'D009474'},
        )

    def test_lookup_identifier(self, *_):
        """Test look up of the identifier when given the name."""
        self._help(
            {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'},
            {NAMESPACE: 'MESH', NAME: 'Neurons'},
        )

    def test_lookup_name_as_identifier(self, *_):
        """Test look up of the name when given as the identifier."""
        self._help(
            {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'},
            {NAMESPACE: 'MESH', IDENTIFIER: 'Neurons'},
        )

    def test_lookup_uniprot_identifier(self, *_):
        """Test looking up a uniprot identifier."""
        self._help(
            {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
            {NAMESPACE: 'UniProt', NAME: 'HUS1_HUMAN'},
        )

    def test_fix_uniprot_identifier_as_name(self, *_):
        """Test lookup of the UniProt identifier when given a UniProt identifier as the name."""
        self._help(
            {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
            {NAMESPACE: 'UniProt', NAME: 'O60921'},
        )

    def test_fix_wrong_name(self, *_):
        """Test overwriting a wrong name (not UniProt)."""
        self._help(
            {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'},
            {NAMESPACE: 'MESH', NAME: 'Nonsense name!', IDENTIFIER: 'D009474'},
        )

    def test_fix_wrong_uniprot_name(self, *_):
        """Test overwriting a wrong name (UniProt)."""
        self._help(
            {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
            {NAMESPACE: 'UniProt', NAME: 'WRONG!!!!', IDENTIFIER: 'O60921'},
        )

    def test_remap_sfam(self, *_):
        """Test remapping SFAM to FPLX."""
        self._help(
            {NAMESPACE: 'fplx', NAME: 'TAP', IDENTIFIER: 'TAP'},
            {NAMESPACE: 'SFAM', NAME: 'TAP Family'},
        )

    def test_remap_scomp(self, *_):
        """Test remapping SFAM to FPLX."""
        self.assertIsNotNone(bioregistry.normalize_prefix('BEL'))
        self.assertIn(
            ('bel', 'gamma Secretase Complex'),
            _NAME_REMAPPING,
            msg='name remapping is not populated properly',
        )
        self._help(
            {NAMESPACE: 'fplx', NAME: 'Gamma_secretase', IDENTIFIER: 'Gamma_secretase'},
            {NAMESPACE: 'SCOMP', NAME: 'gamma Secretase Complex'},
        )


@mock_id_name_mapping
@mock_get_mnemonic
@mock_get_id_from_mnemonic
class TestGround(unittest.TestCase):
    """Test grounding."""

    def _help(self, expected, result):
        _process_node(result)
        self.assertEqual(expected, result)

    def test_lookup_identifier_member(self, *_):
        """Test looking up the identifier of a member by name."""
        self._help(
            {MEMBERS: [{CONCEPT: {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'}}]},
            {MEMBERS: [{CONCEPT: {NAMESPACE: 'MESH', NAME: 'Neurons'}}]},
        )

    def test_lookup_identifier_complex(self, *_):
        """Test looking up the identifier of a named complex and its members at the same time."""
        self._help(
            {
                CONCEPT: {NAMESPACE: 'complexportal', NAME: 'Checkpoint clamp complex', IDENTIFIER: 'CPX-1829'},
                MEMBERS: [
                    {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'}},
                    {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'RAD9A_HUMAN', IDENTIFIER: 'Q99638'}},
                    {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'RAD1_HUMAN', IDENTIFIER: 'O60671'}},
                ],
            },
            {
                CONCEPT: {NAMESPACE: 'complexportal', NAME: 'Checkpoint clamp complex'},
                MEMBERS: [
                    {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'}},
                    {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'RAD9A_HUMAN'}},
                    {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'RAD1_HUMAN'}},
                ],
            },
        )

    def test_lookup_identifier_protein(self, *_):
        """Test looking up the identifier based on a protein's name."""
        self._help(
            {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'}},
            {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'}},
        )

    def test_lookup_name_protein(self, *_):
        """Test looking up the name based on a protein's identifier."""
        self._help(
            {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'}},
            {CONCEPT: {NAMESPACE: 'uniprot', IDENTIFIER: 'O60921'}},
        )

    def test_fix_name_protein(self, *_):
        """Test fixing a wrong name by overwriting by identifier-based lookup."""
        self._help(
            {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'}},
            {CONCEPT: {NAMESPACE: 'uniprot', IDENTIFIER: 'O60921', NAME: 'wrong!!!'}},
        )

    def test_lookup_identifier_pmod(self, *_):
        """Test looking up a protein modification's identifier by name."""
        self._help(
            {
                CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                VARIANTS: [
                    {
                        KIND: PMOD,
                        CONCEPT: {NAMESPACE: 'go', IDENTIFIER: '0006468', NAME: 'protein phosphorylation'},
                    },
                ]
            },
            {
                CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'},
                VARIANTS: [
                    {
                        KIND: PMOD,
                        CONCEPT: {NAMESPACE: 'GO', NAME: 'protein phosphorylation'},
                    },
                ]
            },
        )

    def test_lookup_name_pmod(self, *_):
        """Test looking up a protein modification's name by identifier."""
        self._help(
            {
                CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                VARIANTS: [
                    {
                        KIND: PMOD,
                        CONCEPT: {NAMESPACE: 'go', IDENTIFIER: '0006468', NAME: 'protein phosphorylation'},
                    },
                ]
            },
            {
                CONCEPT: {NAMESPACE: 'uniprot', IDENTIFIER: 'O60921'},
                VARIANTS: [
                    {
                        KIND: PMOD,
                        CONCEPT: {NAMESPACE: 'GO', IDENTIFIER: '0006468'},
                    },
                ]
            },
        )

    def test_fix_pmod_name(self, *_):
        """Test fixing a wrong name in a pmod."""
        self._help(
            {
                CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                VARIANTS: [
                    {
                        KIND: PMOD,
                        CONCEPT: {NAMESPACE: 'go', IDENTIFIER: '0006468', NAME: 'protein phosphorylation'},
                    },
                ]
            },
            {
                CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'},
                VARIANTS: [
                    {
                        KIND: PMOD,
                        CONCEPT: {NAMESPACE: 'GO', IDENTIFIER: '0006468', NAME: 'WRONG!'},
                    },
                ]
            },
        )

    def test_normalize_pmod_default(self, *_):
        """Test normalizing a pmod using the default bel namespace."""
        self._help(
            {
                CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                VARIANTS: [
                    {
                        KIND: PMOD,
                        CONCEPT: {NAMESPACE: 'go', IDENTIFIER: '0006468', NAME: 'protein phosphorylation'},
                    },
                ]
            },
            {
                CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'},
                VARIANTS: [
                    {
                        KIND: PMOD,
                        CONCEPT: {NAMESPACE: 'bel', NAME: 'Ph'},
                    },
                ]
            },
        )

    def test_normalize_pmod_default_methylation(self, *_):
        """Test normalizing the default namespace's Me entry because of conflict with gmods."""
        self._help(
            {
                CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                VARIANTS: [
                    {
                        KIND: PMOD,
                        CONCEPT: {NAMESPACE: 'go', IDENTIFIER: '0006479', NAME: 'protein methylation'}
                    },
                ]
            },
            {
                CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'},
                VARIANTS: [
                    {
                        KIND: PMOD,
                        CONCEPT: {NAMESPACE: 'bel', NAME: 'Me'}
                    },
                ]
            },
        )

    def normalize_gmod_default_methylation(self, *_):
        """Test normalizing the default namespace's Me entry because of conflict with pmods."""
        self._help(
            {
                CONCEPT: {NAMESPACE: 'hgnc', NAME: 'MAPT', IDENTIFIER: '6893'},
                VARIANTS: [
                    {CONCEPT: {NAMESPACE: 'go', IDENTIFIER: '0006306', NAME: 'DNA methylation'}, KIND: GMOD},
                ]
            },
            {
                CONCEPT: {NAMESPACE: 'HGNC', NAME: 'MAPT'},
                VARIANTS: [
                    {CONCEPT: {NAMESPACE: 'bel', NAME: 'Me'}, KIND: GMOD},
                ]
            },
        )


@mock_id_name_mapping
class TestAnnotations(unittest.TestCase):
    """Test processing annotations."""

    def _help(self, expected_data, data):
        expected_data = {ANNOTATIONS: expected_data}
        data = {ANNOTATIONS: data}
        _process_annotations(data)
        self.assertEqual(expected_data, data)

    def test_lookup_by_identifier(self, *_):
        """Test lookup by identifier."""
        self._help(
            {'Disease': [Entity(namespace='mesh', identifier='D010300', name='Parkinson Disease')]},
            {'Disease': [Entity(namespace='mesh', identifier='D010300')]},
        )

    def test_lookup_by_name(self, *_):
        """Test lookup by name."""
        self._help(
            {'Disease': [Entity(namespace='mesh', identifier='D010300', name='Parkinson Disease')]},
            {'Disease': [Entity(namespace='mesh', name='Parkinson Disease')]},
        )

    def test_lookup_by_name_as_identifier(self, *_):
        """Test lookup by name if it's accidentally in the identifier slot."""
        self._help(
            {'Disease': [Entity(namespace='mesh', identifier='D010300', name='Parkinson Disease')]},
            {'Disease': [Entity(namespace='mesh', identifier='Parkinson Disease')]},
        )

    def test_upgrade_category(self, *_):
        """Test upgrading the category."""
        self._help(
            {'Disease': [Entity(namespace='mesh', identifier='D010300', name='Parkinson Disease')]},
            {'MeSHDisease': [Entity(namespace='mesh', identifier='D010300', name='Parkinson Disease')]},
        )

    def test_upgrade_category_and_namespace(self, *_):
        """Test upgrading the category and the namespace simultaneously."""
        self._help(
            {'Disease': [Entity(namespace='mesh', identifier='D010300', name='Parkinson Disease')]},
            {'MeSHDisease': [Entity(namespace='MeSHDisease', identifier='D010300', name='Parkinson Disease')]},
        )

    def test_upgrade_with_name_as_identifier(self, *_):
        """Test upgrading MeSH disease, MeSH anatomy, and Species tags and lookup by name, in the identifiers space."""
        self._help(
            {  # Expected
                'Disease': [Entity(namespace='mesh', identifier='D010300', name='Parkinson Disease')],
                'Anatomy': [Entity(namespace='mesh', identifier='D013378', name='Substantia Nigra')],
                'Species': [Entity(namespace='ncbitaxon', identifier='9606', name='Homo sapiens')],
            },
            {  # Original
                'MeSHDisease': [Entity(namespace='MeSHDisease', identifier='Parkinson Disease')],
                'MeSHAnatomy': [Entity(namespace='MeSHAnatomy', identifier='Substantia Nigra')],
                'Species': [Entity(namespace='Species', identifier='Homo sapiens')],
            },
        )

    def test_upgrade_by_identifier(self, *_):
        """Test upgrading and lookup by identifier."""
        self._help(
            {  # Expected
                'Disease': [Entity(namespace='mesh', identifier='D010300', name='Parkinson Disease')],
                'Anatomy': [Entity(namespace='mesh', identifier='D013378', name='Substantia Nigra')],
                'Species': [Entity(namespace='ncbitaxon', identifier='9606', name='Homo sapiens')],
            },
            {  # Original
                'MeSHDisease': [Entity(namespace='MeSHDisease', identifier='D010300')],
                'MeSHAnatomy': [Entity(namespace='MeSHAnatomy', identifier='D013378')],
                'Species': [Entity(namespace='Species', identifier='9606')],
            },
        )

    def test_upgrade_by_name(self, *_):
        """Test upgrading and lookup by name."""
        self._help(
            {  # Expected
                'Disease': [Entity(namespace='mesh', identifier='D010300', name='Parkinson Disease')],
                'Anatomy': [Entity(namespace='mesh', identifier='D013378', name='Substantia Nigra')],
                'Species': [Entity(namespace='ncbitaxon', identifier='9606', name='Homo sapiens')],
            },
            {  # Original
                'MeSHDisease': [Entity(namespace='MeSHDisease', name='Parkinson Disease')],
                'MeSHAnatomy': [Entity(namespace='MeSHAnatomy', name='Substantia Nigra')],
                'Species': [Entity(namespace='Species', name='Homo sapiens')],
            },
        )

    def test_unmappable_category(self, *_):
        """Test when the category can't be mapped."""
        self._help(
            {  # Expected
                'Custom Annotation': [Entity(namespace='Custom Annotation', identifier="Custom Value")],
            },
            {
                'Custom Annotation': [Entity(namespace='Custom Annotation', identifier="Custom Value")],
            },
        )

    def test_unmappable_identifier(self, *_):
        """Test when the identifier can not be resolved."""
        self._help(
            {  # Expected
                'Disease': [Entity(namespace='doid', identifier='Failure')],
            },
            {
                'Disease': [Entity(namespace='Disease', identifier='Failure')],
            },
        )

    def test_unmappable_name(self, *_):
        """Test when the identifier can not be looked up by name."""
        self._help(
            {  # Expected
                'Disease': [Entity(namespace='doid', name='Failure')],
            },
            {
                'Disease': [Entity(namespace='Disease', name='Failure')],
            },
        )
