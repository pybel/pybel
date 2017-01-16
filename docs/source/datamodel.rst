Data Model
==========

Molecular biology is a directed graph; not a table. BEL expresses how biological entities interact within many
different contexts, with descriptive annotations. PyBEL represents data as a logical MultiDiGraph using the NetworkX
package. Each node and edge has an associated data dictionary for storing relevant/contextual information.

This allows for much easier programmatic access to answer more complicated questions, which can be written with python
code. Because the data structure is the same in Neo4J, the data can be directly exported with :code:`pybel.to_neo4j`.
Neo4J supports the Cypher querying language so that the same queries can be written in an elegant and simple way.

Nodes
-----
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

With the addition of a variant :code:`var()`, post-translational modification :code:`pmod()`, or gene modification
:code:`gmod()` to a BEL statement, an additional entry called :code:`variants` is added. It is a list of all of the
modifications and variants (in alphabetical order) on the node. Under this schema, :code:`p(HGNC:GSK3B, pmod(P, S, 9))`
becomes:

.. code::

    {
        'function': 'Protein',
        'identifier': {
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
    }

Nomenclature
~~~~~~~~~~~~

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
        'path': 'Pathology',
        'complex': 'Complex'
        'complexAbundance': 'Complex',
        'composite': 'Composite'
        'compositeAbundance': 'Composite'
    }

But these terms can be more readily accessed by :code:`pybel.parser.language.PROTEIN`,
:code:`pybel.parser.language.GENE`, and so on.

List Abundances
~~~~~~~~~~~~~~~
Complexes and composites that are defined by lists do not recieve information about the identifier, and are only
described by their function. :code:`complex(p(HGNC:FOS), p(HGNC:JUN))` becomes:

.. code::

    {
        'function': 'Composite'
    }

The remaining information is encoded in the edges to the resulting protein nodes from :code:`p(HGNC:FOS)` and
:code:`p(HGNC:JUN)` with connections having the relation :code:`hasMember`.

Edges
-----
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