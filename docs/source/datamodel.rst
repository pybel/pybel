Data Model
==========

Molecular biology is a directed graph; not a table. BEL expresses how biological entities interact within many
different contexts, with descriptive annotations. PyBEL represents data as a logical MultiDiGraph using the NetworkX
package. Each node and edge has an associated data dictionary for storing relevant/contextual information.

This allows for much easier programmatic access to answer more complicated questions, which can be written with python
code. Because the data structure is the same in Neo4J, the data can be directly exported with :func:`pybel.to_neo4j`.
Neo4J supports the Cypher querying language so that the same queries can be written in an elegant and simple way.

Constants
---------

These documents refer to many aspects of the data model using constants, which can be found in the top-level module
:code:`pybel.constants`. In these examples, all constants are imported with the following code:

.. code-block:: python

    >>> from pybel.constants import *
    >>> from pybel.parser.modifiers import FragmentParser, GmodParser, PmodParser, FusionParser

Terms describing abundances, annotations, and other internal data are designated in :code:`pybel.constants`
with full-caps, such as :data:`pybel.constants.FUNCTION` and :data:`pybel.constants.PROTEIN`.

For normal usage, we suggest referring to values in dictionaries by these constants, in case the hard-coded
strings behind these constants change.

Function Nomenclature
~~~~~~~~~~~~~~~~~~~~~

The following table shows PyBEL's internal mapping from BEL functions to its own constants. This can be accessed
programatically via :py:data:`pybel.parser.language.abundance_labels`

+--------------------+----------------+
| BEL Function       | PyBEL Constant |
+====================+================+
| a                  | ABUNDANCE      |
+--------------------+----------------+
| abundance          | ABUNDANCE      |
+--------------------+----------------+
| geneAbundance      | GENE           |
+--------------------+----------------+
| g                  | GENE           |
+--------------------+----------------+
| rnaAbunance        | RNA            |
+--------------------+----------------+
| r                  | RNA            |
+--------------------+----------------+
| microRNAAbundance  | MIRNA          |
+--------------------+----------------+
| m                  | MIRNA          |
+--------------------+----------------+
| proteinAbundance   | PROTEIN        |
+--------------------+----------------+
| p                  | PROTEIN        |
+--------------------+----------------+
| biologicalProcess  | BIOPROCESS     |
+--------------------+----------------+
| bp                 | BIOPROCESS     |
+--------------------+----------------+
| pathology          | PATHOLOGY      |
+--------------------+----------------+
| path               | PATHOLOGY      |
+--------------------+----------------+
| complexAbundance   | COMPLEX        |
+--------------------+----------------+
| complex            | COMPLEX        |
+--------------------+----------------+
| compositeAbundance | COMPOSITE      |
+--------------------+----------------+
| composite          | COMPOSITE      |
+--------------------+----------------+
| reaction           | REACTION       |
+--------------------+----------------+
| rxn                | REACTION       |
+--------------------+----------------+

Graph
-----

.. automodule:: pybel.graph

.. autoclass:: pybel.BELGraph
    :exclude-members: parse_lines, parse_document, parse_definitions, parse_statements, nodes_iter, edges_iter, add_warning
    :members:

Nodes
-----
Nodes are used to represent physical entities' abundances. The relevant data about a node is stored in its associated
dictionary in NetworkX. After parsing, :code:`p(HGNC:GSK3B)` becomes:

.. code::

    {
        FUNCTION: PROTEIN,
        NAMESPACE: 'HGNC',
        NAME: 'GSK3B'
    }

.. automodule:: pybel.parser.modifiers.variant

.. automodule:: pybel.parser.modifiers.gene_substitution

.. automodule:: pybel.parser.modifiers.protein_substitution

.. automodule:: pybel.parser.modifiers.truncation

.. automodule:: pybel.parser.modifiers.fragment

.. automodule:: pybel.parser.modifiers.gene_modification

.. automodule:: pybel.parser.modifiers.protein_modification

.. automodule:: pybel.parser.modifiers.fusion


Unqualified Edges
-----------------

Unqualified edges are automatically inferred by PyBEL and do not contain citations or supporting evidence.

Variant and Modifications' Parent Relations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All variants, modifications, fragments, and truncations are connected to their parent entity with an edge having
the relationship :code:`hasParent`


List Abundances
~~~~~~~~~~~~~~~
Complexes and composites that are defined by lists do not recieve information about the identifier, and are only
described by their function. :code:`complex(p(HGNC:FOS), p(HGNC:JUN))` becomes:

.. code::

    {
        FUNCTION: COMPLEX
    }

The following edges are inferred:

.. code::

    complex(p(HGNC:FOS), p(HGNC:JUN)) hasMember p(HGNC:FOS)
    complex(p(HGNC:FOS), p(HGNC:JUN)) hasMember p(HGNC:JUN)


.. seealso::

    BEL 2.0 specification on `complex abundances <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcomplexA>`_

Similarly, :code:`composite(a(CHEBI:malonate), p(HGNC:JUN))` becomes:

.. code::

    {
        FUNCTION: COMPOSITE
    }

The following edges are inferred:

.. code::

    composite(a(CHEBI:malonate), p(HGNC:JUN)) hasComponent a(CHEBI:malonate)
    composite(a(CHEBI:malonate), p(HGNC:JUN)) hasComponent p(HGNC:JUN)


.. seealso::

    BEL 2.0 specification on `composite abundances <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcompositeA>`_


Reactions
~~~~~~~~~
The usage of a reaction causes many nodes and edges to be created. The following example will illustrate what is
added to the network for

.. code::

    rxn(reactants(a(CHEBI:"(3S)-3-hydroxy-3-methylglutaryl-CoA"), a(CHEBI:"NADPH"), \
        a(CHEBI:"hydron")), products(a(CHEBI:"mevalonate"), a(CHEBI:"NADP(+)")))

results in the following data:

.. code::

    {
        FUNCTION: REACTION
    }

The following edges are inferred, where :code:`X` represents the previous reaction, for brevity:

.. code::

    X hasReactant a(CHEBI:"(3S)-3-hydroxy-3-methylglutaryl-CoA")
    X hasReactant a(CHEBI:"NADPH")
    X hasReactant a(CHEBI:"hydron")
    X hasProduct a(CHEBI:"mevalonate")
    X hasProduct a(CHEBI:"NADP(+)"))

.. seealso::

    BEL 2.0 specification on `reactions <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_reaction_rxn>`_

Central Dogma
~~~~~~~~~~~~~

When encountering protein abundance nodes, PyBEL infers the RNA from which it was translated and the DNA from which
it was transcribed. After the mention of :code:`p(HGNC:YFG)`, the following two edges are inferred:

.. code::

    r(HGNC:YFG) translatedTo p(HGNC:YFG)
    g(HGNC:YFG) transcribedTo r(HGNC:YFG)

When encountering RNA abundances, PyBEL only infers the genetic origin. PyBEL will not make forward inferences,
because the function of a gene or RNA may not be clear.

Currently, PyBEL does not make these inferences for miRNAs, but could in the future.

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
        RELATION: 'positiveCorrelation',
        OBJECT: {
            # ... modifications to the object node. Only present if non-empty.
        },
        EVIDENCE: '...',
        CITATION : {
            # ... citation information
        }
        ANNOTATIONS: {
            # ... additional annotations as key:value pairs
        }
    }


Activities
~~~~~~~~~~
Modifiers are added to this structure as well. Under this schema,
:code:`p(HGNC:GSK3B, pmod(P, S, 9)) pos act(p(HGNC:GSK3B), ma(kin))` becomes:

.. code::

    {
        RELATION: 'positiveCorrelation',
        OBJECT: {
            MODIFIER: ACTIVITY,
            EFFECT: {
                NAME: 'kin'
                NAMESPACE: BEL_DEFAULT_NAMESPACE
            }
        },
        CITATION: { ... }
        EVIDENCE: '...',
        ANNOTATIONS: { ... }
    }

Activities without molecular activity annotations do not contain an :code:`EFFECT` entry: Under this schema,
:code:`p(HGNC:GSK3B, pmod(P, S, 9)) pos act(p(HGNC:GSK3B))` becomes:

.. code::

    {
        RELATION: 'positiveCorrelation',
        OBJECT: {
            MODIFIER: ACTIVITY
        },
        CITATION: { ... }
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
        RELATION: 'increases',
        OBJECT: {
            MODIFIER: TRANSLOCATION,
            EFFECT: {
                FROM_LOC: {
                    NAMESPACE: 'GOMF',
                    NAME: 'intracellular'
                },
                TO_LOC: {
                    NAMESPACE: 'GOMF',
                    NAME: 'extracellular space'
                }
            }
        },
        CITATION: { ... }
        EVIDENCE: '...',
        ANNOTATIONS: { ... }
    }

.. seealso::

    BEL 2.0 specification on `translocations <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_translocations>`_

Degradations
~~~~~~~~~~~~
Degradations are more simple, because there's no :code:`EFFECT` entry. :code:`p(HGNC:YFG1) -> deg(p(HGNC:YFG2))` becomes:

.. code::

    {
        RELATION: 'increases',
        OBJECT: {
            MODIFIER: DEGRADATION
        },
        CITATION: { ... }
        EVIDENCE: '...',
        ANNOTATIONS: { ... }
    }

.. seealso::

    BEL 2.0 specification on `degradations <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_degradation_deg>`_
