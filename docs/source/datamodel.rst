Data Model
==========

Molecular biology is a directed graph; not a table. BEL expresses how biological entities interact within many
different contexts, with descriptive annotations. PyBEL represents data as a logical MultiDiGraph using the NetworkX
package. Each node and edge has an associated data dictionary for storing relevant/contextual information.

This allows for much easier programmatic access to answer more complicated questions, which can be written with python
code. Because the data structure is the same in Neo4J, the data can be directly exported with :code:`pybel.to_neo4j`.
Neo4J supports the Cypher querying language so that the same queries can be written in an elegant and simple way.

Nomenclature
------------

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

But these terms can be more readily accessed by :code:`pybel.constants.PROTEIN`,
:code:`pybel.constants.GENE`, and so on.

Simple Abundances
-----------------
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

.. automodule:: pybel.parser.modifiers.variant

.. automodule:: pybel.parser.modifiers.gene_substitution

.. automodule:: pybel.parser.modifiers.protein_substitution

.. automodule:: pybel.parser.modifiers.truncation

.. automodule:: pybel.parser.modifiers.fragment

.. automodule:: pybel.parser.modifiers.gene_modification

.. automodule:: pybel.parser.modifiers.protein_modification

.. automodule:: pybel.parser.modifiers.fusion


List Abundances
---------------
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
In the OpenBEL Framework, modifiers such as activities (kinaseActivity, etc.) and transformations (translocations,
degradations, etc.) were represented as their own nodes. In PyBEL, these modifiers are represented as a property
of the edge. In reality, an edge like :code:`sec(p(HGNC:A)) -> activity(p(HGNC:B), ma(kinaseActivity))` represents
a connection between :code:`HGNC:A` and :code:`HGNC:B`. Each of these modifiers explains the context of the relationship
between these physical entities. Further, querying a network where these modifiers are part of a relationship
is much more straightforward. For example, finding all proteins that are upregulated by the kinase activity of another
protein now can be directly queried by filtering all edges for those with a subject modifier whose modification is
molecular activity, and whose effect is kinase activity. Having fewer nodes also allows for a much easier display
and visual interpretation of a network. The information about the modifier on the subject and activity can be displayed
as a color coded source and terminus of the connecting edge.

The compiler in OpenBEL framework created nodes for molecular activities like :code:`kin(p(HGNC:YFG))` and induced an
edge like :code:`p(HGNC:YFG) actsIn kin(p(HGNC:YFG))`. For transformations, a statement like
:code:`tloc(p(HGNC:YFG), GOCC:intracellular, GOCC:"cell membrane")` also induced
:code:`tloc(p(HGNC:YFG), GOCC:intracellular, GOCC:"cell membrane") translocates p(HGNC:YFG)`.

In PyBEL, we recognize that these modifications are actually annotations to the type of relationship between the
subject's entity and the object's entity. :code:`p(HGNC:ABC) -> tloc(p(HGNC:YFG), GOCC:intracellular, GOCC:"cell membrane")`
is about the relationship between :code:`p(HGNC:ABC)` and :code:`p(HGNC:YFG)`, while
the information about the translocation qualifies that the object is undergoing an event, and not just the abundance.
This is a confusion with the use of :code:`proteinAbundance` as a keyword, and perhaps is why many people prefer to use
just the keyword :code:`p`

This also begs the question of what statements mean. BEL 2.0 introduced the :code:`location()` element that can be
inside any abundances. This means that it's possible to unambiguously express the differences between the process of
:code:`HGNC:A` moving from one place to another and the existence of :code:`HGNC:A` in a specific location having
different effects. In BEL 1.0, this action had its own node, but this introduced unnecessary complexity to the network
and made querying more difficult. Consider the difference between the following two statements:

- :code:`tloc(p(HGNC:A), fromLoc(GOCC:intracellular), toLoc(GOCC:"cell membrane")) -> p(HGNC:B)`
- :code:`p(HGNC:A, location(GOCC:"cell membrane")) -> p(HGNC:B)`

Activities
~~~~~~~~~~
Modifiers are added to this structure as well. Under this schema,
:code:`p(HGNC:GSK3B, pmod(P, S, 9)) pos act(p(HGNC:GSK3B), ma(kin))` becomes:

.. code::

    {
        'subject': {
            'function': 'Protein',
            'identifier': {
                    'namespace': 'HGNC',
                    'name': 'GSK3B'
            },
            'variants': [
                {
                    'kind': 'pmod',
                    'code': 'Ser',
                    'identifier': {
                        'name': 'Ph',
                        'namespace': 'PYBEL'
                    },
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
                'name': 'kin'
                'namespace': 'PYBEL'
            }
        },
    }


.. automodule:: pybel.parser.modifiers.location


Translocations
~~~~~~~~~~~~~~
Translocations have their own unique syntax. :code:`p(HGNC:YFG1) -> sec(p(HGNC:YFG2))` becomes:

.. code::

    {
        'subject': {
            'function': 'Protein',
            'identifier': 'identifier': {
                    'namespace': 'HGNC',
                    'name': 'YFG1'
            }
        },
        'relation': 'increases',
        'object': {
            'modifier': 'Translocation',
            'target': {
                'function': 'Protein',
                'identifier': {
                    'namespace': 'HGNC',
                    'name': 'YFG2'
                }
            },
            'effect': {
                'fromLoc': {
                    'namespace': 'GOMF',
                    'name': 'intracellular'
                },
                'toLoc': {
                    'namespace': 'GOMF',
                    'name': 'extracellular space'
                }
            }
        },
    }

Degradations
~~~~~~~~~~~~
Degradations are more simple, because there's no 'effect' entry. :code:`p(HGNC:YFG1) -> deg(p(HGNC:YFG2))` becomes:

.. code::

    {
        'subject': {
            'function': 'Protein',
            'identifier': 'identifier': {
                    'namespace': 'HGNC',
                    'name': 'YFG1'
            }
        },
        'relation': 'increases',
        'object': {
            'modifier': 'Degradation',
            'target': {
                'function': 'Protein',
                'identifier': {
                    'namespace': 'HGNC',
                    'name': 'YFG2'
                }
            },
        },
    }
