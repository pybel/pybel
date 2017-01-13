Data Model
==========

Node
----
The relevant data about a node is stored in its associated dictionary in NetworkX. After parsing, :code:`p(HGNC:GSK3B)`
becomes:

.. code::

    {
        'function': 'Protein',
        'identifier': {
            'namespace': 'HGNC',
            'name': 'GSK3B'
        }
    }

With the addition of a variant (:code:`var()`), post-translational modification (:code:`pmod()`), or gene modification
(:code:`gmod()`) to a BEL statement, an additional entry called :code:`variants` is added. It is a list of all of the
modifications and variants (in alphabetical order) on the node. Under this schema, :code:`p(HGNC:GSK3B, pmod(P, S, 9))`
becomes:

.. code::

    {
        'function': 'Protein',
        'identifier': dict(namespace='HGNC', name='GSK3B'),
        'variants': [
            {
                'code': 'Ser',
                'identifier': 'Ph',
                'pos': 9
            }
        ]
    }


Mapping for BEL functions to PyBEL functions is done based on the following dictionary
(:code:`pybel.parser.language.abundance_labels`)

.. code::

    {
        'abundance': 'Abundance',
        'a': 'Abundance',
        'geneAbundance': 'Gene',
        'g': 'Gene',
        'microRNAAbundance': 'miRNA',
        'm': 'miRNA',
        'proteinAbundance': 'Protein',
        'p': 'Protein',
        'rnaAbundance': 'RNA',
        'r': 'RNA',
        'biologicalProcess': 'BiologicalProcess',
        'bp': 'BiologicalProcess',
        'pathology': 'Pathology',
        'path': 'Pathology'
    }


Edge
----
Modifiers are added to this structure as well. Under this schema,
:code:`p(HGNC:GSK3B, pmod(P, S, 9)) pos act(p(HGNC:GSK3B), ma(kin))` becomes:

.. code::

    {
        'subject': {
            'function': 'Protein',
            'identifier': 'identifier': {
                    'namespace': 'HGNC',
                    'name': 'GSK3B'
            },
            'variants': [
                {
                    'code': 'Ser',
                    'identifier': 'Ph',
                    'pos': 9
                }
            ]
        },
        'relation': 'positiveCorrelation',
        'object': {
            'modifier': 'Activity',
            'target': {
                'function': 'Protein',
                'identifier': {
                    'namespace': 'HGNC',
                    'name': 'GSK3B'
                }
            },
            'effect': {
                'MolecularActivity': 'KinaseActivity'
            }
        },
    }

Location data also is added into the information in the edge for the node (subject or object) for which it was
annotated. :code:`p(HGNC:GSK3B, pmod(P, S, 9), loc(GOCC:lysozome)) pos act(p(HGNC:GSK3B), ma(kin))` becomes:

.. code::

    {
        'subject': {
            'function': 'Protein',
            'identifier': 'identifier': {
                    'namespace': 'HGNC',
                    'name': 'GSK3B'
            },
            'variants': [
                {
                    'code': 'Ser',
                    'identifier': 'Ph',
                    'pos': 9
                }
            ],
            'location': {
                'namespace': 'GOCC',
                'name': 'lysozome'
            }
        },
        'relation': 'positiveCorrelation',
        'object': {
            'modifier': 'Activity',
            'target': {
                'function': 'Protein',
                'identifier': {
                    'namespace': 'HGNC',
                    'name': 'GSK3B'
                }
            },
            'effect': {
                'MolecularActivity': 'KinaseActivity'
            }
        },
    }