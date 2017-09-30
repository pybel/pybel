Data Model
==========

Molecular biology is a directed graph; not a table. BEL expresses how biological entities interact within many
different contexts, with descriptive annotations. PyBEL represents data as a directional multigraph using an extension
of :class:`networkx.MultiDiGraph`. Each node and edge has an associated data dictionary for storing relevant/contextual
information.

This allows for much easier programmatic access to answer more complicated questions, which can be written with python
code. Because the data structure is the same in Neo4J, the data can be directly exported with :func:`pybel.to_neo4j`.
Neo4J supports the Cypher querying language so that the same queries can be written in an elegant and simple way.

Constants
---------

These documents refer to many aspects of the data model using constants, which can be found in the top-level module
:mod:`pybel.constants`. In these examples, all constants are imported with the following code:

.. code-block:: python

    >>> from pybel.constants import *

Terms describing abundances, annotations, and other internal data are designated in :mod:`pybel.constants`
with full-caps, such as :data:`pybel.constants.FUNCTION` and :data:`pybel.constants.PROTEIN`.

For normal usage, we suggest referring to values in dictionaries by these constants, in case the hard-coded
strings behind these constants change.

Function Nomenclature
~~~~~~~~~~~~~~~~~~~~~

The following table shows PyBEL's internal mapping from BEL functions to its own constants. This can be accessed
programatically via :data:`pybel.parser.language.abundance_labels`

+-------------------------------------------+----------------------------------------+
| BEL Function                              | PyBEL Constant                         |
+===========================================+========================================+
| ``a()``, ``abundance()``                  | :data:`pybel.constants.ABUNDANCE`      |
+-------------------------------------------+----------------------------------------+
| ``g()``, ``geneAbundance()``              | :data:`pybel.constants.GENE`           |
+-------------------------------------------+----------------------------------------+
| ``r()``, ``rnaAbunance()``                | :data:`pybel.constants.RNA`            |
+-------------------------------------------+----------------------------------------+
| ``m()``, ``microRNAAbundance()``          | :data:`pybel.constants.MIRNA`          |
+-------------------------------------------+----------------------------------------+
| ``p()``, ``proteinAbundance()``           | :data:`pybel.constants.PROTEIN`        |
+-------------------------------------------+----------------------------------------+
| ``bp()``, ``biologicalProcess()``         | :data:`pybel.constants.BIOPROCESS`     |
+-------------------------------------------+----------------------------------------+
| ``path()``, ``pathology()``               | :data:`pybel.constants.PATHOLOGY`      |
+-------------------------------------------+----------------------------------------+
| ``complex()``, ``complexAbundance()``     | :data:`pybel.constants.COMPLEX`        |
+-------------------------------------------+----------------------------------------+
| ``composite()``, ``compositeAbundance()`` | :data:`pybel.constants.COMPOSITE`      |
+-------------------------------------------+----------------------------------------+
| ``rxn()``, ``reaction()``                 | :data:`pybel.constants.REACTION`       |
+-------------------------------------------+----------------------------------------+


Graph
-----

.. automodule:: pybel.struct

.. autoclass:: pybel.BELGraph
    :exclude-members: nodes_iter, edges_iter, add_warning
    :members:

    .. automethod:: __add__
    .. automethod:: __iadd__
    .. automethod:: __and__
    .. automethod:: __iand__

.. autofunction:: pybel.struct.left_full_join
.. autofunction:: pybel.struct.left_outer_join
.. autofunction:: pybel.struct.union

Nodes
-----
Nodes are used to represent physical entities' abundances. The relevant data about a node is stored in its associated
data dictionary in :mod:`networkx` that can be accessed with ``my_bel_graph.node[node]``. After parsing,
:code:`p(HGNC:GSK3B)` becomes:

.. code::

    {
        FUNCTION: PROTEIN,
        NAMESPACE: 'HGNC',
        NAME: 'GSK3B'
    }

This section describes the structure of the data dictionaries created for each type of node available in BEL.
Programatically, these dictionaries can be converted to tuples, which are used as the keys for the network with the
:func:`pybel.parser.canonicalize.node_to_tuple` function.

Variants
~~~~~~~~

The addition of a variant tag results in an entry called 'variants' in the data dictionary associated with a given
node. This entry is a list with dictionaries describing each of the variants. All variants have the entry 'kind' to
identify whether it is a post-translational modification (PTM), gene modification, fragment, or HGVS variant.

.. warning::

    The canonical ordering for the elements of the ``VARIANTS`` list correspond to the sorted
    order of their corresponding node tuples using :func:`pybel.parser.canonicalize.sort_dict_list`. Rather than
    directly modifying the BELGraph's structure, use :meth:`pybel.BELGraph.add_node_from_data`, which takes care of
    automatically canonicalizing this dictionary.

.. automodule:: pybel.parser.modifiers.variant

.. automodule:: pybel.parser.modifiers.gene_substitution

.. automodule:: pybel.parser.modifiers.protein_substitution

.. automodule:: pybel.parser.modifiers.truncation

.. automodule:: pybel.parser.modifiers.fragment

.. automodule:: pybel.parser.modifiers.gene_modification

.. automodule:: pybel.parser.modifiers.protein_modification

Fusions
~~~~~~~

.. automodule:: pybel.parser.modifiers.fusion

Unqualified Edges
-----------------

Unqualified edges are automatically inferred by PyBEL and do not contain citations or supporting evidence.

Variant and Modifications' Parent Relations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All variants, modifications, fragments, and truncations are connected to their parent entity with an edge having
the relationship :code:`hasParent`

For :code:`p(HGNC:GSK3B, var(p.Gly123Arg))`, the following edge is inferred:

.. code::

    p(HGNC:GSK3B, var(p.Gly123Arg)) hasParent p(HGNC:GSK3B)

All variants have this relationship to their reference node. BEL does not specify relationships between variants,
such as the case when a given phosphorylation is necessary to make another one. This knowledge could be encoded
directly like BEL, since PyBEL does not restrict users from manually asserting unqualified edges.

List Abundances
~~~~~~~~~~~~~~~
Complexes and composites that are defined by lists. As of version 0.9.0, they contain a list of the data dictionaries
that describe their members. For example :code:`complex(p(HGNC:FOS), p(HGNC:JUN))` becomes:

.. code::

    {
        FUNCTION: COMPLEX,
        MEMBERS: [
            {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'FOS'
            }, {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'JUN'
            }
        ]
    }

The following edges are also inferred:

.. code::

    complex(p(HGNC:FOS), p(HGNC:JUN)) hasMember p(HGNC:FOS)
    complex(p(HGNC:FOS), p(HGNC:JUN)) hasMember p(HGNC:JUN)


.. seealso::

    BEL 2.0 specification on `complex abundances <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcomplexA>`_

Similarly, :code:`composite(a(CHEBI:malonate), p(HGNC:JUN))` becomes:

.. code::

    {
        FUNCTION: COMPOSITE,
        MEMBERS: [
            {
                FUNCTION: ABUNDANCE,
                NAMESPACE: 'CHEBI',
                NAME: 'malonate'
            }, {
                FUNCTION: PROTEIN,
                NAMESPACE: 'HGNC',
                NAME: 'JUN'
            }
        ]
    }

The following edges are inferred:

.. code::

    composite(a(CHEBI:malonate), p(HGNC:JUN)) hasComponent a(CHEBI:malonate)
    composite(a(CHEBI:malonate), p(HGNC:JUN)) hasComponent p(HGNC:JUN)


.. warning::

    The canonical ordering for the elements of the ``MEMBERS`` list correspond to the sorted
    order of their corresponding node tuples using :func:`pybel.parser.canonicalize.sort_dict_list`. Rather than
    directly modifying the BELGraph's structure, use :meth:`BELGraph.add_node_from_data`, which takes care of
    automatically canonicalizing this dictionary.

.. seealso::

    BEL 2.0 specification on `composite abundances <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcompositeA>`_


Reactions
~~~~~~~~~
The usage of a reaction causes many nodes and edges to be created. The following example will illustrate what is
added to the network for

.. code::

    rxn(reactants(a(CHEBI:"(3S)-3-hydroxy-3-methylglutaryl-CoA"), a(CHEBI:"NADPH"), \
        a(CHEBI:"hydron")), products(a(CHEBI:"mevalonate"), a(CHEBI:"NADP(+)")))

As of version 0.9.0, the reactants' and products' data dictionaries are included as sub-lists keyed ``REACTANTS`` and
``PRODUCTS``. It becomes:

.. code::

    {
        FUNCTION: REACTION
        REACTANTS: [
            {
                FUNCTION: ABUNDANCE,
                NAMESPACE: 'CHEBI',
                NAME: '(3S)-3-hydroxy-3-methylglutaryl-CoA'
            }, {
                FUNCTION: ABUNDANCE,
                NAMESPACE: 'CHEBI',
                NAME: 'NADPH'
            }, {
                FUNCTION: ABUNDANCE,
                NAMESPACE: 'CHEBI',
                NAME: 'hydron'
            }
        ],
        PRODUCTS: [
            {
                FUNCTION: ABUNDANCE,
                NAMESPACE: 'CHEBI',
                NAME: 'mevalonate'
            }, {
                FUNCTION: ABUNDANCE,
                NAMESPACE: 'CHEBI',
                NAME: 'NADP(+)'
            }
        ]
    }

.. warning::

    The canonical ordering for the elements of the ``REACTANTS`` and ``PRODUCTS`` lists correspond to the sorted
    order of their corresponding node tuples using :func:`pybel.parser.canonicalize.sort_dict_list`. Rather than
    directly modifying the BELGraph's structure, use :meth:`BELGraph.add_node_from_data`, which takes care of
    automatically canonicalizing this dictionary.

The following edges are inferred, where :code:`X` represents the previous reaction, for brevity:

.. code::

    X hasReactant a(CHEBI:"(3S)-3-hydroxy-3-methylglutaryl-CoA")
    X hasReactant a(CHEBI:"NADPH")
    X hasReactant a(CHEBI:"hydron")
    X hasProduct a(CHEBI:"mevalonate")
    X hasProduct a(CHEBI:"NADP(+)"))

.. seealso::

    BEL 2.0 specification on `reactions <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_reaction_rxn>`_


Edges
-----

Design Choices
~~~~~~~~~~~~~~
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

Example Edge Data Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Because this data is associated with an edge, the node data for the subject and object are not included explicitly.
However, information about the activities, modifiers, and transformations on the subject and object are included.
Below is the "skeleton" for the edge data model in PyBEL:

.. code::

    {
        SUBJECT: {
            # ... modifications to the subject node. Only present if non-empty.
        },
        RELATION: POSITIVE_CORRELATION,
        OBJECT: {
            # ... modifications to the object node. Only present if non-empty.
        },
        EVIDENCE: '...',
        CITATION : {
            CITATION_TYPE: CITATION_TYPE_PUBMED,
            CITATION_REFERENCE: '...',
            CITATION_DATE: 'YYYY-MM-DD',
            CITATION_AUTHORS: 'Jon Snow|John Doe',
        },
        ANNOTATIONS: {
            'Disease': 'Colorectal Cancer',
            # ... additional annotations as key:value pairs
        }
    }

Each edge must contain the ``RELATION``, ``EVIDENCE``, ``CITATION``, and ``ANNOTATIONS`` entries. The ``CITATION``
must minimally contain ``CITATION_TYPE`` and ``CITATION_REFERENCE`` since these can be used to look up additional
metadata.

Activities
~~~~~~~~~~
Modifiers are added to this structure as well. Under this schema,
:code:`p(HGNC:GSK3B, pmod(P, S, 9)) pos act(p(HGNC:GSK3B), ma(kin))` becomes:

.. code::

    {
        RELATION: POSITIVE_CORRELATION,
        OBJECT: {
            MODIFIER: ACTIVITY,
            EFFECT: {
                NAME: 'kin'
                NAMESPACE: BEL_DEFAULT_NAMESPACE
            }
        },
        CITATION: { ... },
        EVIDENCE: '...',
        ANNOTATIONS: { ... }
    }

Activities without molecular activity annotations do not contain an :data:`pybel.constants.EFFECT` entry: Under this
schema, :code:`p(HGNC:GSK3B, pmod(P, S, 9)) pos act(p(HGNC:GSK3B))` becomes:

.. code::

    {
        RELATION: POSITIVE_CORRELATION,
        OBJECT: {
            MODIFIER: ACTIVITY
        },
        CITATION: { ... },
        EVIDENCE: '...',
        ANNOTATIONS: { ... }
    }


Locations
~~~~~~~~~

.. automodule:: pybel.parser.modifiers.location


Translocations
~~~~~~~~~~~~~~
Translocations have their own unique syntax. :code:`p(HGNC:YFG1) -> sec(p(HGNC:YFG2))` becomes:

.. code::

    {
        RELATION: INCREASES,
        OBJECT: {
            MODIFIER: TRANSLOCATION,
            EFFECT: {
                FROM_LOC: {
                    NAMESPACE: 'GOCC',
                    NAME: 'intracellular'
                },
                TO_LOC: {
                    NAMESPACE: 'GOCC',
                    NAME: 'extracellular space'
                }
            }
        },
        CITATION: { ... },
        EVIDENCE: '...',
        ANNOTATIONS: { ... }
    }

.. seealso::

    BEL 2.0 specification on `translocations <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_translocations>`_

Degradations
~~~~~~~~~~~~
Degradations are more simple, because there's no ::data:`pybel.constants.EFFECT` entry.
:code:`p(HGNC:YFG1) -> deg(p(HGNC:YFG2))` becomes:

.. code::

    {
        RELATION: INCREASES,
        OBJECT: {
            MODIFIER: DEGRADATION
        },
        CITATION: { ... },
        EVIDENCE: '...',
        ANNOTATIONS: { ... }
    }

.. seealso::

    BEL 2.0 specification on `degradations <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_degradation_deg>`_
