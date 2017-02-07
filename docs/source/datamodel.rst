Data Model
==========

Molecular biology is a directed graph; not a table. BEL expresses how biological entities interact within many
different contexts, with descriptive annotations. PyBEL represents data as a logical MultiDiGraph using the NetworkX
package. Each node and edge has an associated data dictionary for storing relevant/contextual information.

This allows for much easier programmatic access to answer more complicated questions, which can be written with python
code. Because the data structure is the same in Neo4J, the data can be directly exported with :code:`pybel.to_neo4j`.
Neo4J supports the Cypher querying language so that the same queries can be written in an elegant and simple way.

Constants
---------

These documents refer to many aspects of the data model using constants, which can be found in the top-level module
:code:`pybel.constants`. In these examples, constants will be prefixed with :code:`pbc` such as in :code:`pbc.FUNCTION`.

For normal usage, we suggest referring to values in dictionaries by these constants, in case the hard-coded
strings behind these constants change. They can be made readily available with:

.. code-block:: python

    >>> from pybel import constants as pbc

Abundance Nomenclature
~~~~~~~~~~~~~~~~~~~~~~

Internally, PyBEL uses the following table, :code:`pybel.parser.language.abundance_labels`, to map from BEL language
functions to its internal constants.

.. code::

    {
        'abundance': pbc.ABUNDANCE,
        'a': pbc.ABUNDANCE,
        'geneAbundance': pbc.GENE,
        'g': pbc.GENE,
        'microRNAAbundance': pbc.MIRNA,
        'm': pbc.MIRNA,
        'proteinAbundance': pbc.PROTEIN,
        'p': pbc.PROTEIN,
        'rnaAbundance': pbc.RNA,
        'r': pbc.RNA,
        'biologicalProcess': pbc.BIOPROCESS,
        'bp': pbc.BIOPROCESS,
        'pathology': pbc.PATHOLOGY,
        'path': pbc.PATHOLOGY,
        'complex': pbc.COMPLEX
        'complexAbundance': pbc.COMPLEX,
        'composite': pbc.COMPOSITE
        'compositeAbundance': pbc.COMPOSITE
    }

Simple Abundances
-----------------
The relevant data about a node is stored in its associated dictionary in NetworkX. After parsing, :code:`p(HGNC:GSK3B)`
becomes:

.. code::

    {
        pbc.FUNCTION: pbc.PROTEIN,
        pbc.NAMESPACE: 'HGNC',
        pbc.NAME: 'GSK3B'
    }

.. automodule:: pybel.parser.modifiers.variant

.. automodule:: pybel.parser.modifiers.gene_substitution

.. automodule:: pybel.parser.modifiers.protein_substitution

.. automodule:: pybel.parser.modifiers.truncation

.. automodule:: pybel.parser.modifiers.fragment

.. automodule:: pybel.parser.modifiers.gene_modification

.. automodule:: pybel.parser.modifiers.protein_modification

.. automodule:: pybel.parser.modifiers.fusion


Context-Free Edges
------------------

1. Variants/Modifications' relation to their reference
2. Memberships to complexes and composities
3. Reactions
4. Central Dogma (transcription and translation)

List Abundances
~~~~~~~~~~~~~~~
Complexes and composites that are defined by lists do not recieve information about the identifier, and are only
described by their function. :code:`complex(p(HGNC:FOS), p(HGNC:JUN))` becomes:

.. code::

    {
        pbc.FUNCTION: pbc.COMPOSITE
    }

The remaining information is encoded in the edges to the resulting protein nodes from :code:`p(HGNC:FOS)` and
:code:`p(HGNC:JUN)` with connections having the relation :code:`hasMember`.

.. seealso::

    BEL 2.0 specification on `complex abundances <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#XcomplexA>`_

Reactions
~~~~~~~~~
The usage of a reaction causes many nodes and edges to be created. The following example will illustrate what is
added to the network for

.. code::

    rxn(reactants(a(CHEBI:"(3S)-3-hydroxy-3-methylglutaryl-CoA"), a(CHEBI:NADPH), a(CHEBI:hydron)),\
        products(a(CHEBI:mevalonate), a(CHEBI:"NADP(+)"))) \
        subProcessOf bp(GOBP:"cholesterol biosynthetic process")

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
        pbc.SUBJECT: {
            # ... modifications to the subject node
        },
        pbc.RELATION: 'positiveCorrelation',
        pbc.OBJECT: {
            # ... modifications to the object node
        },
        pbc.EVIDENCE: '...',
        pbc.CITATION : {
            # ... citation information
        }
        # ... additional annotations as key:value pairs
    }


Activities
~~~~~~~~~~
Modifiers are added to this structure as well. Under this schema,
:code:`p(HGNC:GSK3B, pmod(P, S, 9)) pos act(p(HGNC:GSK3B), ma(kin))` becomes:

.. code::

    {
        pbc.SUBJECT: {},
        pbc.RELATION: 'positiveCorrelation',
        pbc.OBJECT: {
            pbc.MODIFIER: pbc.ACTIVITY,
            pbc.EFFECT: {
                pbc.NAME: 'kin'
                pbc.NAMESPACE: pbc.BEL_DEFAULT_NAMESPACE
            }
        },
        pbc.EVIDENCE: '...',
        pbc.CITATION: { ... }
    }


Locations
~~~~~~~~~

.. automodule:: pybel.parser.modifiers.location


Translocations
~~~~~~~~~~~~~~
Translocations have their own unique syntax. :code:`p(HGNC:YFG1) -> sec(p(HGNC:YFG2))` becomes:

.. code::

    {
        pbc.SUBJECT: {},
        pbc.RELATION: 'increases',
        pbc.OBJECT: {
            pbc.MODIFIER: pbc.TRANSLOCATION,
            pbc.EFFECT: {
                pbc.FROM_LOC: {
                    pbc.NAMESPACE: 'GOMF',
                    pbc.NAME: 'intracellular'
                },
                pbc.TO_LOC: {
                    pbc.NAMESPACE: 'GOMF',
                    pbc.NAME: 'extracellular space'
                }
            }
        },
        pbc.EVIDENCE: '...',
        pbc.CITATION: { ... }
    }

.. seealso::

    BEL 2.0 specification on `translocations <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_translocations>`_

Degradations
~~~~~~~~~~~~
Degradations are more simple, because there's no pbc.EFFECT entry. :code:`p(HGNC:YFG1) -> deg(p(HGNC:YFG2))` becomes:

.. code::

    {
        pbc.SUBJECT: {},
        pbc.RELATION: 'increases',
        pbc.OBJECT: {
            pbc.MODIFIER: pbc.DEGRADATION
        },
        pbc.EVIDENCE: '...',
        pbc.CITATION: { ... }
    }

.. seealso::

    BEL 2.0 specification on `degradations <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_degradation_deg>`_
