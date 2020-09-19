# -*- coding: utf-8 -*-

"""Test grounding."""

import unittest

from pybel.constants import ANNOTATIONS, CONCEPT, GMOD, IDENTIFIER, KIND, MEMBERS, NAME, NAMESPACE, PMOD, VARIANTS
from pybel.grounding import SYNONYM_TO_KEY, _process_annotations, _process_concept, _process_node
from pybel.language import Entity


class TestGround(unittest.TestCase):
    """Test grounding."""

    def test_process_concept(self):
        """Test several cases in processing concepts."""
        r = [
            (
                'Normalize prefix to correct case',
                {CONCEPT: {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'}},
                {CONCEPT: {NAMESPACE: 'MESH', NAME: 'Neurons', IDENTIFIER: 'D009474'}},
            ),
            (
                'Normalize prefix by synonym',
                {CONCEPT: {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'}},
                {CONCEPT: {NAMESPACE: 'MESHA', NAME: 'Neurons', IDENTIFIER: 'D009474'}},
            ),
            (
                'Look up identifier by name',
                {CONCEPT: {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'}},
                {CONCEPT: {NAMESPACE: 'MESH', NAME: 'Neurons'}},
            ),
            (
                'Lookup by UniProt identifier as name',
                {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'}},
                {CONCEPT: {NAMESPACE: 'UniProt', NAME: 'O60921'}},
            ),
            (
                'Lookup by UniProt mnemonic as name',
                {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'}},
                {CONCEPT: {NAMESPACE: 'UniProt', NAME: 'HUS1_HUMAN'}},
            ),
            (
                'Rewrite wrong UniProt name',
                {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'}},
                {CONCEPT: {NAMESPACE: 'UniProt', NAME: 'WRONG!!!!', IDENTIFIER: 'O60921'}},
            ),
            (
                'Overwrite name by identifier',
                {CONCEPT: {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'}},
                {CONCEPT: {NAMESPACE: 'MESH', NAME: 'Nonsense name!', IDENTIFIER: 'D009474'}},
            ),
            (
                'Remap example 1',
                {CONCEPT: {NAMESPACE: 'fplx', NAME: 'TAP', IDENTIFIER: 'TAP'}},
                {CONCEPT: {NAMESPACE: 'SFAM', NAME: 'TAP Family'}},
            ),
            (
                'Remap example 2',
                {CONCEPT: {NAMESPACE: 'fplx', NAME: 'Gamma_secretase', IDENTIFIER: 'Gamma_secretase'}},
                {CONCEPT: {NAMESPACE: 'SCOMP', NAME: 'gamma Secretase Complex'}},
            ),
        ]
        for name, expected, result in r:
            with self.subTest(name=name):
                self.assertIn(expected[CONCEPT][NAMESPACE], SYNONYM_TO_KEY)
                _process_concept(concept=result[CONCEPT], node=result)
                self.assertEqual(expected, result)

    def test_process_nodes(self):
        """Test several cases dealing with full nodes."""
        r = [
            (
                'Look up identifier of member by name',
                {MEMBERS: [{CONCEPT: {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'}}]},
                {MEMBERS: [{CONCEPT: {NAMESPACE: 'MESH', NAME: 'Neurons'}}]},
            ),
            (
                'Look up identifier of member by name AND name of complex',
                {
                    CONCEPT: {NAMESPACE: 'complexportal', NAME: 'Checkpoint clamp complex', IDENTIFIER: 'CPX-1829'},
                    MEMBERS: [
                        {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'}},
                        {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'RAD9A_HUMAN', IDENTIFIER: 'Q99638'}},
                        {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'RAD1_HUMAN', IDENTIFIER: 'O60671'}},
                    ]
                },
                {
                    CONCEPT: {NAMESPACE: 'complexportal', NAME: 'Checkpoint clamp complex'},
                    MEMBERS: [
                        {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'}},
                        {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'RAD9A_HUMAN'}},
                        {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'RAD1_HUMAN'}},
                    ]
                },
            ),
            (
                'Normalize pmod by name',
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
            ),
            (
                'Fix name in pmod by identifier lookup',
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
            ),
            (
                'Normalize pmod using default BEL namespace',
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
            ),
            (
                'Normalize pmod using default BEL namespace - Me (to investigate conflict with gmod)',
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
            ),
            (
                'Normalize gmod using default BEL namespace - Me (to investigate conflict with pmod)',
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
            ),
        ]
        for name, expected, result in r:
            with self.subTest(name=name):
                _process_node(result)
                self.assertEqual(expected, result)

    def test_process_annotations(self):
        """Test processing annotations data."""
        r = [
            (
                'Test Upgrade MeSH disease, MeSH anatomy, and species',
                {  # Expected
                    ANNOTATIONS: {
                        'Disease': [Entity(namespace='mesh', identifier='D010300', name='Parkinson Disease')],
                        'Anatomy': [Entity(namespace='mesh', identifier='D013378', name='Substantia Nigra')],
                        'Species': [Entity(namespace='ncbitaxon', identifier='9606', name='Homo sapiens')],
                    },
                },
                {  # Original
                    ANNOTATIONS: {
                        'MeSHDisease': [Entity(namespace='MeSHDisease', identifier='Parkinson Disease')],
                        'MeSHAnatomy': [Entity(namespace='MeSHAnatomy', identifier='Substantia Nigra')],
                        'Species': [Entity(namespace='Species', identifier='Homo sapiens')],
                    },
                },
            ),
            (
                'Test Upgrade MeSH disease, MeSH anatomy, and species but with names',
                {  # Expected
                    ANNOTATIONS: {
                        'Disease': [Entity(namespace='mesh', identifier='D010300', name='Parkinson Disease')],
                        'Anatomy': [Entity(namespace='mesh', identifier='D013378', name='Substantia Nigra')],
                        'Species': [Entity(namespace='ncbitaxon', identifier='9606', name='Homo sapiens')],
                    },
                },
                {  # Original
                    ANNOTATIONS: {
                        'MeSHDisease': [Entity(namespace='MeSHDisease', name='Parkinson Disease')],
                        'MeSHAnatomy': [Entity(namespace='MeSHAnatomy', name='Substantia Nigra')],
                        'Species': [Entity(namespace='Species', name='Homo sapiens')],
                    },
                },
            ),
            (
                'When the name of the annotation does not need to be mapped via identifiers',
                {  # Expected
                    ANNOTATIONS: {
                        'Disease': [Entity(namespace='doid', identifier='14330', name="Parkinson's disease")],
                        'Cell': [Entity(namespace='cl', identifier='0000030', name='glioblast')],
                    },
                },
                {
                    ANNOTATIONS: {
                        'Disease': [Entity(namespace='doid', identifier="Parkinson's disease")],
                        'Cell': [Entity(namespace='Cell', identifier='glioblast')],
                    },
                },
            ),
            (
                'When the name of the annotation does not need to be mapped via names',
                {  # Expected
                    ANNOTATIONS: {
                        'Disease': [Entity(namespace='doid', identifier='14330', name="Parkinson's disease")],
                        'Cell': [Entity(namespace='cl', identifier='0000030', name='glioblast')],
                    },
                },
                {
                    ANNOTATIONS: {
                        'Disease': [Entity(namespace='doid', name="Parkinson's disease")],
                        'Cell': [Entity(namespace='cl', name='glioblast')],
                    },
                },
            ),
            (
                'Check unmappable disease',
                {  # Expected
                    ANNOTATIONS: {
                        'Disease': [Entity(namespace='doid', identifier='Failure')],
                    },
                },
                {
                    ANNOTATIONS: {
                        'Disease': [Entity(namespace='Disease', identifier='Failure')],
                    },
                },
            ),
            (
                'Check unhandled annotation',
                {  # Expected
                    ANNOTATIONS: {
                        'Custom Annotation': [Entity(namespace='Custom Annotation', identifier="Custom Value")],
                    }
                },
                {
                    ANNOTATIONS: {
                        'Custom Annotation': [Entity(namespace='Custom Annotation', identifier="Custom Value")],
                    },
                },
            ),
        ]
        for name, expected_data, data in r:
            with self.subTest(name=name):
                _process_annotations(data)
                self.assertEqual(expected_data, data)
