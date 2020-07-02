Data Model
==========
.. automodule:: pybel.struct

Constants
---------
These documents refer to many aspects of the data model using constants, which can be found in the top-level module
:mod:`pybel.constants`.

Terms describing abundances, annotations, and other internal data are designated in :mod:`pybel.constants`
with full-caps, such as :data:`pybel.constants.FUNCTION` and :data:`pybel.constants.PROTEIN`.

For normal usage, we suggest referring to values in dictionaries by these constants, in case the hard-coded
strings behind these constants change.

Function Nomenclature
~~~~~~~~~~~~~~~~~~~~~
The following table shows PyBEL's internal mapping from BEL functions to its own constants. This can be accessed
programatically via :data:`pybel.parser.language.abundance_labels`.

+-------------------------------------------+-----------------------------------+--------------------------------------+
| BEL Function                              | PyBEL Constant                    | PyBEL DSL                            |
+===========================================+===================================+======================================+
| ``a()``, ``abundance()``                  |:data:`pybel.constants.ABUNDANCE`  |:class:`pybel.dsl.Abundance`          |
+-------------------------------------------+-----------------------------------+--------------------------------------+
| ``g()``, ``geneAbundance()``              |:data:`pybel.constants.GENE`       |:class:`pybel.dsl.Gene`               |
+-------------------------------------------+-----------------------------------+--------------------------------------+
| ``r()``, ``rnaAbunance()``                |:data:`pybel.constants.RNA`        |:class:`pybel.dsl.Rna`                |
+-------------------------------------------+-----------------------------------+--------------------------------------+
| ``m()``, ``microRNAAbundance()``          |:data:`pybel.constants.MIRNA`      |:class:`pybel.dsl.MicroRna`           |
+-------------------------------------------+-----------------------------------+--------------------------------------+
| ``p()``, ``proteinAbundance()``           |:data:`pybel.constants.PROTEIN`    |:class:`pybel.dsl.Protein`            |
+-------------------------------------------+-----------------------------------+--------------------------------------+
| ``bp()``, ``biologicalProcess()``         |:data:`pybel.constants.BIOPROCESS` |:class:`pybel.dsl.BiologicalProcess`  |
+-------------------------------------------+-----------------------------------+--------------------------------------+
| ``path()``, ``pathology()``               |:data:`pybel.constants.PATHOLOGY`  |:class:`pybel.dsl.Pathology`          |
+-------------------------------------------+-----------------------------------+--------------------------------------+
| ``complex()``, ``complexAbundance()``     |:data:`pybel.constants.COMPLEX`    |:class:`pybel.dsl.ComplexAbundance`   |
+-------------------------------------------+-----------------------------------+--------------------------------------+
| ``composite()``, ``compositeAbundance()`` |:data:`pybel.constants.COMPOSITE`  |:class:`pybel.dsl.CompositeAbundance` |
+-------------------------------------------+-----------------------------------+--------------------------------------+
| ``rxn()``, ``reaction()``                 |:data:`pybel.constants.REACTION`   |:class:`pybel.dsl.Reaction`           |
+-------------------------------------------+-----------------------------------+--------------------------------------+

Graph
-----
.. autoclass:: pybel.BELGraph
    :exclude-members: nodes_iter, edges_iter, add_warning, fresh_copy, document
    :members:

    .. automethod:: __add__
    .. automethod:: __iadd__
    .. automethod:: __and__
    .. automethod:: __iand__


Dispatches
~~~~~~~~~~
Dispatches are classes that enable easy access to summary, mutation, and other functions
that consume graphs directly through the :class:`pybel.BELGraph` interface.

.. autoclass:: pybel.struct.graph.CountDispatch
    :members:

.. autoclass:: pybel.struct.graph.InduceDispatch
    :members:

.. autoclass:: pybel.struct.graph.SummarizeDispatch
    :members:

.. autoclass:: pybel.struct.graph.ExpandDispatch
    :members:

.. autoclass:: pybel.struct.graph.PlotDispatch
    :members:

Nodes
-----
Nodes (or *entities*) in a :class:`pybel.BELGraph` represent physical entities' abundances. Most contain information
about the identifier for the entity using a namespace/name pair. The PyBEL parser converts BEL terms to an internal
representation using an internal domain specific language (DSL) that allows for writing BEL directly in Python.

For example, after the BEL term :code:`p(hgnc:GSK3B)` is parsed, it is instantiated as a Python object using the
DSL function corresponding to the ``p()`` function in BEL, :class:`pybel.dsl.Protein`, like:

.. code:: python

    from pybel.dsl import Protein
    gsk3b_protein = Protein(namespace='hgnc', name='GSK3B')

:class:`pybel.dsl.Protein`, like the others mentioned before, inherit from :class:`pybel.dsl.BaseEntity`, which itself
inherits from :class:`dict`. Therefore, the resulting object can be used like a dict that looks like:

.. code-block:: python

    from pybel.constants import *

    {
        FUNCTION: PROTEIN,
        NAMESPACE: 'hgnc',
        NAME: 'GSK3B',
    }

Alternatively, it can be used in more exciting ways, outlined later in the documentation for :mod:`pybel.dsl`.

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

Gene Substitutions
~~~~~~~~~~~~~~~~~~
.. automodule:: pybel.parser.modifiers.gene_substitution

Gene Modifications
~~~~~~~~~~~~~~~~~~
.. automodule:: pybel.parser.modifiers.gene_modification

Protein Substitutions
~~~~~~~~~~~~~~~~~~~~~
.. automodule:: pybel.parser.modifiers.protein_substitution

Protein Modifications
~~~~~~~~~~~~~~~~~~~~~
.. automodule:: pybel.parser.modifiers.protein_modification

Protein Truncations
~~~~~~~~~~~~~~~~~~~
.. automodule:: pybel.parser.modifiers.truncation

Protein Fragments
~~~~~~~~~~~~~~~~~
.. automodule:: pybel.parser.modifiers.fragment

Fusions
~~~~~~~
.. automodule:: pybel.parser.modifiers.fusion

Unqualified Edges
-----------------
Unqualified edges are automatically inferred by PyBEL and do not contain citations or supporting evidence.

Variant and Modifications' Parent Relations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
All variants, modifications, fragments, and truncations are connected to their parent entity with an edge having
the relationship :code:`hasParent`.

For :code:`p(hgnc:GSK3B, var(p.Gly123Arg))`, the following edge is inferred:

.. code::

    p(hgnc:GSK3B, var(p.Gly123Arg)) hasParent p(hgnc:GSK3B)

All variants have this relationship to their reference node. BEL does not specify relationships between variants,
such as the case when a given phosphorylation is necessary to make another one. This knowledge could be encoded
directly like BEL, since PyBEL does not restrict users from manually asserting unqualified edges.

List Abundances
~~~~~~~~~~~~~~~
Complexes and composites that are defined by lists. As of version 0.9.0, they contain a list of the data dictionaries
that describe their members. For example :code:`complex(p(hgnc:FOS), p(hgnc:JUN))` becomes:

.. code-block:: python

    from pybel.constants import *

    {
        FUNCTION: COMPLEX,
        MEMBERS: [
            {
                FUNCTION: PROTEIN,
                NAMESPACE: 'hgnc',
                NAME: 'FOS',
            }, {
                FUNCTION: PROTEIN,
                NAMESPACE: 'hgnc',
                NAME: 'JUN',
            }
        ]
    }

The following edges are also inferred:

.. code::

    complex(p(hgnc:FOS), p(hgnc:JUN)) hasMember p(hgnc:FOS)
    complex(p(hgnc:FOS), p(hgnc:JUN)) hasMember p(hgnc:JUN)


.. seealso::

    BEL 2.0+ Tutorial on `complex abundances <https://biological-expression-language.github.io/entities/physical/#complexes-of-physical-entities>`_

Similarly, :code:`composite(a(CHEBI:malonate), p(hgnc:JUN))` becomes:

.. code-block:: python

    from pybel.constants import *

    {
        FUNCTION: COMPOSITE,
        MEMBERS: [
            {
                FUNCTION: ABUNDANCE,
                NAMESPACE: 'CHEBI',
                NAME: 'malonate',
            }, {
                FUNCTION: PROTEIN,
                NAMESPACE: 'hgnc',
                NAME: 'JUN',
            }
        ]
    }

The following edges are inferred:

.. code::

    composite(a(CHEBI:malonate), p(hgnc:JUN)) hasComponent a(CHEBI:malonate)
    composite(a(CHEBI:malonate), p(hgnc:JUN)) hasComponent p(hgnc:JUN)


.. warning::

    The canonical ordering for the elements of the :data:`pybel.constantsMEMBERS` list correspond to the sorted
    order of their corresponding node tuples using :func:`pybel.parser.canonicalize.sort_dict_list`. Rather than
    directly modifying the BELGraph's structure, use :meth:`BELGraph.add_node_from_data`, which takes care of
    automatically canonicalizing this dictionary.

.. seealso::

    BEL 2.0+ Tutorial on `composite abundances <https://biological-expression-language.github.io/entities/reified/#composites>`_


Reactions
~~~~~~~~~
The usage of a reaction causes many nodes and edges to be created. The following example will illustrate what is
added to the network for

.. code::

    rxn(reactants(a(CHEBI:"(3S)-3-hydroxy-3-methylglutaryl-CoA"), a(CHEBI:"NADPH"), \
        a(CHEBI:"hydron")), products(a(CHEBI:"mevalonate"), a(CHEBI:"NADP(+)")))

As of version 0.9.0, the reactants' and products' data dictionaries are included as sub-lists keyed ``REACTANTS`` and
``PRODUCTS``. It becomes:

.. code-block:: python

    from pybel.constants import *

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
                NAME: 'NADPH',
            }, {
                FUNCTION: ABUNDANCE,
                NAMESPACE: 'CHEBI',
                NAME: 'hydron',
            }
        ],
        PRODUCTS: [
            {
                FUNCTION: ABUNDANCE,
                NAMESPACE: 'CHEBI',
                NAME: 'mevalonate',
            }, {
                FUNCTION: ABUNDANCE,
                NAMESPACE: 'CHEBI',
                NAME: 'NADP(+)',
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

    BEL 2.0+ tutorial on `reactions <https://biological-expression-language.github.io/entities/reified/#reactions>`_


Edges
-----
Design Choices
~~~~~~~~~~~~~~
In the OpenBEL Framework, modifiers such as activities (kinaseActivity, etc.) and transformations (translocations,
degradations, etc.) were represented as their own nodes. In PyBEL, these modifiers are represented as a property
of the edge. In reality, an edge like :code:`sec(p(hgnc:A)) -> activity(p(hgnc:B), ma(kinaseActivity))` represents
a connection between :code:`hgnc:A` and :code:`hgnc:B`. Each of these modifiers explains the context of the relationship
between these physical entities. Further, querying a network where these modifiers are part of a relationship
is much more straightforward. For example, finding all proteins that are upregulated by the kinase activity of another
protein now can be directly queried by filtering all edges for those with a subject modifier whose modification is
molecular activity, and whose effect is kinase activity. Having fewer nodes also allows for a much easier display
and visual interpretation of a network. The information about the modifier on the subject and activity can be displayed
as a color coded source and terminus of the connecting edge.

The compiler in OpenBEL framework created nodes for molecular activities like :code:`kin(p(hgnc:YFG))` and induced an
edge like :code:`p(hgnc:YFG) actsIn kin(p(hgnc:YFG))`. For transformations, a statement like
:code:`tloc(p(hgnc:YFG), GO:intracellular, GO:"cell membrane")` also induced
:code:`tloc(p(hgnc:YFG), GO:intracellular, GO:"cell membrane") translocates p(hgnc:YFG)`.

In PyBEL, we recognize that these modifications are actually annotations to the type of relationship between the
subject's entity and the object's entity. ``p(hgnc:ABC) -> tloc(p(hgnc:YFG), GO:intracellular, GO:"cell membrane")``
is about the relationship between :code:`p(hgnc:ABC)` and :code:`p(hgnc:YFG)`, while
the information about the translocation qualifies that the object is undergoing an event, and not just the abundance.
This is a confusion with the use of :code:`proteinAbundance` as a keyword, and perhaps is why many people prefer to use
just the keyword :code:`p`

Example Edge Data Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Because this data is associated with an edge, the node data for the subject and object are not included explicitly.
However, information about the activities, modifiers, and transformations on the subject and object are included.
Below is the "skeleton" for the edge data model in PyBEL:

.. code-block:: python

    from pybel.constants import *

    {
        SUBJECT: {
            # ... modifications to the subject node. Only present if non-empty.
        },
        RELATION: POSITIVE_CORRELATION,
        OBJECT: {
            # ... modifications to the object node. Only present if non-empty.
        },
        EVIDENCE: ...,
        CITATION : {
            CITATION_TYPE: CITATION_TYPE_PUBMED,
            CITATION_REFERENCE: ...,
            CITATION_DATE: 'YYYY-MM-DD',
            CITATION_AUTHORS: 'Jon Snow|John Doe',
        },
        ANNOTATIONS: {
            'Disease': {
                'Colorectal Cancer': True,
            },
            # ... additional annotations as tuple[str,dict[str,bool]] pairs
        },
    }

Each edge must contain the ``RELATION``, ``EVIDENCE``, and ``CITATION`` entries. The ``CITATION``
must minimally contain ``CITATION_TYPE`` and ``CITATION_REFERENCE`` since these can be used to look up additional
metadata.

.. note:: Since version 0.10.2, annotations now always appear as dictionaries, even if only one value is present.

Activities
~~~~~~~~~~
Modifiers are added to this structure as well. Under this schema,
:code:`p(hgnc:GSK3B, pmod(P, S, 9)) pos act(p(hgnc:GSK3B), ma(kin))` becomes:

.. code-block:: python

    from pybel.constants import *

    {
        RELATION: POSITIVE_CORRELATION,
        OBJECT: {
            MODIFIER: ACTIVITY,
            EFFECT: {
                NAME: 'kin',
                NAMESPACE: BEL_DEFAULT_NAMESPACE,
            }
        },
        CITATION: { ... },
        EVIDENCE: ...,
        ANNOTATIONS: { ... },
    }

Activities without molecular activity annotations do not contain an :data:`pybel.constants.EFFECT` entry: Under this
schema, :code:`p(hgnc:GSK3B, pmod(P, S, 9)) pos act(p(hgnc:GSK3B))` becomes:

.. code-block:: python

    from pybel.constants import *

    {
        RELATION: POSITIVE_CORRELATION,
        OBJECT: {
            MODIFIER: ACTIVITY
        },
        CITATION: { ... },
        EVIDENCE: ...,
        ANNOTATIONS: { ... },
    }


Locations
~~~~~~~~~
.. automodule:: pybel.parser.modifiers.location

Translocations
~~~~~~~~~~~~~~
Translocations have their own unique syntax. :code:`p(hgnc:YFG1) -> sec(p(hgnc:YFG2))` becomes:

.. code-block:: python

    from pybel.constants import *

    {
        RELATION: INCREASES,
        OBJECT: {
            MODIFIER: TRANSLOCATION,
            EFFECT: {
                FROM_LOC: {
                    NAMESPACE: 'GO',
                    NAME: 'intracellular',
                },
                TO_LOC: {
                    NAMESPACE: 'GO',
                    NAME: 'extracellular space',
                }
            }
        },
        CITATION: { ... },
        EVIDENCE: ...,
        ANNOTATIONS: { ... },
    }

.. seealso::

    BEL 2.0+ tutorial on `translocations <https://biological-expression-language.github.io/statements/#translocations>`_

Degradations
~~~~~~~~~~~~
Degradations are more simple, because there's no ::data:`pybel.constants.EFFECT` entry.
:code:`p(hgnc:YFG1) -> deg(p(hgnc:YFG2))` becomes:

.. code-block:: python

    from pybel.constants import *

    {
        RELATION: INCREASES,
        OBJECT: {
            MODIFIER: DEGRADATION,
        },
        CITATION: { ... },
        EVIDENCE: ...,
        ANNOTATIONS: { ... },
    }

.. warning::

    Degradations only provide syntax sugar and will be automatically upgraded in a future version of PyBEL such that:

    - ``deg(X) -> Y`` is upgraded to ``X -| Y``
    - ``deg(X) -| Y`` is upgraded to ``X -> Y``
    - ``deg(X) => Y`` is upgraded to ``X =| Y``
    - ``deg(X) cnc Y`` is upgraded to ``X cnc Y``
    - ``X -> deg(Y)`` is upgraded to ``X -| Y``
    - ``X => deg(Y)`` is upgraded to ``X =| Y``
    - ``X cnc deg(Y)`` is upgraded to ``X cnc Y``
    - ``X -| deg(Y)`` is undefined
