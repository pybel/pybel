Design Choices
==============

Dealing with Dirty Namespaces
-----------------------------

While it's not good practice to leave unqualified elements in a BEL document, sometimes there isn't a proper
namespace at the time. There's a setting in the BELGraph for these occassions. The command line interface also provides
a flat :code:`--lenient` for use. Again, this is not reccomended. If you are using names that don't have namespaces,
consult the scientific community working in your area of research and organize the development of a proper ontology,
terminology, or namespace that can be used. Ultimately, a namespace allows many people to talk, without ambiguity,
about the same thing. WARNING: Lenient mode is not tested very well. Use at your own risk.

.. code-block:: python

    >>> import pybel
    >>> pybel.from_path('~/Desktop/my_document.bel', lenient=True)

For now, the namespace for naked names is assigned the sentinel value from pybel.parser.parse_identifier.DIRTY.

Here are some suggestions on how to find an appropriate namespace:

- Search the namespaces provided by Selventa, BELIEF, and other sources
- See https://wiki.openbel.org/display/BELNA/Namespaces+Overview
- Write your own :code:`belns` file
- Use pybel-tools to convert OWL Ontologies to :code:`belns` file

Namespace and Annotation Name Choices
-------------------------------------

:code:`*.belns` and :code:`*.belanno` configuration files include an entry called "Keyword" in their respective
[Namespace] and [AnnotationDefinition] sections. To maintain understandability between BEL documents, PyBEL
enforces that the names given in :code:`*.bel` documents match their respective resources. For now, capitilization
is not considered, but in the future, PyBEL will also ensure that capitlization is properly stylized, like
the lowercase 'h' in "ChEMBL". 

Complexes
---------

Currently, an ordering is not assigned to the members of complexes . This is a post-processing implementation detail
that is not implemented in the core of PyBEL. One suggestion to assign values to members in a complex like
:code:`complex(p(HGNC:YFG1),p(HGNC:YFG2))` would be to sort over the 3-tuples of (Function, Namespace, Name) for
each of the complex's elements. This order is guaranteed to be unique and persistient.

Representation of Events and Modifiers
--------------------------------------

In the OpenBEL Framework, modifiers such as activities (kinaseActivity, etc.) and transformations (translocations,
degredations, etc.) were represented as their own nodes. In PyBEL, these modifiers are represented as a property
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
:code:`tloc(p(HGNC:YFG), GOCC:intracellular, GOCC:"cell membrange") translocates p(HGNC:YFG)`.

In PyBEL, we recognize that these modifications are actually annotations to the type of relationship between the
subject's entity and the object's entity. :code:`p(HGNC:ABC) -> tloc(p(HGNC:YFG), GOCC:intracellular, GOCC:"cell membrane")`
is about the relationship between :code:`p(HGNC:ABC)` and :code:`p(HGNC:YFG)`, while
the information about the translocation qualifies that the object is undergoing an event, and not just the abundance.
This is a confusion with the use of :code:`proteinAbundance` as a keyword, and perhaps is why many people prefer to use
just the keyword :code:`p`

This also begs the question of what statements mean. BEL 2.0 introduced the :code:`location()` element that can be
inside any abundances. This means that it's possible to unambiguously express the differences between the process of
:code:`HGNC:A` moving from one place to another and the existence of :code:`HGNC:A` in a specfic location having
different effects. In BEL 1.0, this action had its own node, but this introduced unnecessary complexity to the network
and made querying more difficult. Consider the difference between the following two statements:

- :code:`tloc(p(HGNC:A), fromLoc(GOCC:intracellular), toLoc(GOCC:"cell membrane")) -> p(HGNC:B)`
- :code:`p(HGNC:A, location(GOCC:"cell membrane")) -> p(HGNC:B)`
