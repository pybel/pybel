Overview
========

Background on Biological Expression Language (BEL)
--------------------------------------------------
Biological Expression Language (BEL) is a domain specific language that enables the expression of complex molecular
relationships and their context in a machine-readable form. Its simple grammar and expressive power have led to its
successful use in the `IMI <https://www.imi.europa.eu/>`_ project, `AETIONOMY <http://www.aetionomy.eu/>`_, to describe
complex disease networks with several thousands of relationships.

Design Choices
--------------

Do All Statements Need Supporting Text?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! All statements must be minimally qualified with a citation and evidence (now called SupportingText in BEL 2.0) to
maintain provenance. Statements without evidence can't be traced to their source or evaluated independently from the
curator, so they will be excluded from the analysis.

Missing Namespaces and Improper Names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The use of controlled vocabularies (namespaces) within BEL facilitates the exchange and consistiency of information.
The OpenBEL Framework provides a variety of `namespaces <https://wiki.openbel.org/display/BELNA/Namespaces+Overview>`_
covering each of the BEL function types. The *identifier* for an entitiy encoded in BEL must be written as a
:code:`namespace:name` pair.

Often, finding the correct identifier is difficult. Due to the huge number of terms across many namespaces, it's
difficult for curators to know the domain-specific synonyms that obscure the *controlled* or preferred term.
Additionally, the namespaces provided by OpenBEL do not necessarily reflect the cutting-edge terminologies used in
specific disease areas. For some of these cases, it is appropriate to design a new namespace, using the
`specification <http://openbel-framework.readthedocs.io/en/latest/tutorials/building_custom_namespaces.html>`_
provided by the OpenBEL Framework.

However, the issue of synonym resolution and semantic searching has already been generally solved by the use of
ontologies. Ontologies provide more than a controlled vocabulary, but also a hierarchical model of knowledge and the
information for semantic reasoning. The ontologies describing the biomedical domain (ex. `OBO <obofoundry.org>`_ and
`EMBL-EBI OLS <http://www.ebi.ac.uk/ols/index>`_) are much more rich and better maintained than the OpenBEL Framework's.

PyBEL extends the BEL language to offer namespace definitions that draw directly from the ontologies in these services,
using statements like :code:`DEFINE NAMESPACE OMIT as OWL http://purl.obolibrary.org/obo/omit/dev/omit.owl`
Ontologies can also provide immediate access to hierarchical knowledge like subclass relationships that can provide
better context in analysis.

Additionally, as a tool for curators, the Ontology Lookup Service allows for semantic searching. Simple queries for the
terms 'mitochondrial dysfunction' and 'amyloid beta-peptides' immediately returned results from relevant ontologies,
and ended a long debate over how to represent these objects within BEL. EMBL-EBI also provides a programmatic API to
the OLS service, for searching terms (http://www.ebi.ac.uk/ols/api/search?q=folic%20acid) and
suggesting resolutions (http://www.ebi.ac.uk/ols/api/suggest?q=folic+acid)

Finally, the different formats of ontology syntax can be interconverted using the University of Manchester
`OWL Syntax Converter <http://owl.cs.manchester.ac.uk/converter>`_ to convert OWL ontologies encoded in RDF/XML, OBO,
and other formats to the ammenable OWL/XML Format with calls to their API like:
http://owl.cs.manchester.ac.uk/converter/convert?format=OWL/XML&ontology=http://www.co-ode.org/ontologies/pizza/pizza.owl

Implementation
--------------

PyBEL is implemented using the PyParsing module. It provides flexibility and incredible speed in parsing compared
to regular expression implementation. It also allows for the addition of parsing action hooks, which allow
the graph to be checked semantically at compile-time.

It uses SQLite to provide a consistent and lightweight caching system for external data, such as
namespaces, annotations, ontologies, and SQLAlchemy to provide a cross-platform interface. The same data management
system is used to store graphs for high-performance querying.

In-Memory Data Model
~~~~~~~~~~~~~~~~~~~~
Molecular biology is a directed graph; not a table. BEL expresses how biological entities interact within many
different contexts, with descriptive annotations. PyBEL represents data as a logical MultiDiGraph using the NetworkX
package. Each node and edge has an associated data dictionary for storing relevant/contextual information.

This allows for much easier programmatic access to answer more complicated questions, which can be written with python
code. Because the data structure is the same in Neo4J, the data can be directly exported with :code:`pybel.to_neo4j`.
Neo4J supports the Cypher querying language so that the same queries can be written in an elegant and simple way.

Why Not RDF?
~~~~~~~~~~~~
Current bel2rdf serialization tools build URLs with the OpenBEL Framework domain as a namespace, rather than respect
the original namespaces of original entities. This does not follow the best
practices of the semantic web, where URL’s representing an object point to a real page with additional information.
For example, UniProt Knowledge Base does an exemplary job of this. Ultimately, using non-standard URL’s makes
harmonizing and data integration difficult.

Additionally, the RDF format does not easily allow for the annotation of edges. A simple statement in BEL that one
protein upregulates another can be easily represented in a triple in RDF, but when the annotations and citation from
the BEL document need to be included, this forces RDF serialization to use approaches like representing the statement
itself as a node. RDF was not intended to represent this type of information, but more properly for locating resources
(hence its name). Furthermore, many blank nodes are introduced throughout the process. This makes RDF incredibly
difficult to understand or work with. Later, writing queries in SPARQL becomes very difficult because the data format
is complicated and the language is limited. For example, it would be incredibly complicated to write a query in SPARQL
to get the objects of statements from publications by a certain author.

Representation of Events and Modifiers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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

Things to Consider
------------------

Multiple Annotations
~~~~~~~~~~~~~~~~~~~~
When an annotation has a list, it means that the following BEL relations are true for each of the listed values.
The lines below show a BEL relation that corresponds to two edges, each with the same citation but different values
for :code:`ExampleAnnotation`. This should be considered carefully for analyses dealing with the number of edges
between two entities.

- ``SET Citation = {"PubMed","Example Article","12345"}``
- ``SET ExampleAnnotation = {"Example Value 1", "Example Value 2"}``
- ``p(HGNC:YFG1) -> p(HGNC:YFG2)``

Furthermore, if there are multiple annotations with lists, the following BEL relations are true for all of the
different combinations of them. The following statements will produce four edges, as the cartesian product of the values
used for both :code:`ExampleAnnotation1` and :code:`ExampleAnnotation2`. This might not be the knowledge that the
annotator wants to express, and is prone to mistakes, so use of annotation lists are not reccomended.

- ``SET Citation = {"PubMed","Example Article","12345"}``
- ``SET ExampleAnnotation1 = {"Example Value 11", "Example Value 12"}``
- ``SET ExampleAnnotation2 = {"Example Value 21", "Example Value 22"}``
- ``p(HGNC:YFG1) -> p(HGNC:YFG2)``

Namespace and Annotation Name Choices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:code:`*.belns` and :code:`*.belanno` configuration files include an entry called "Keyword" in their respective
[Namespace] and [AnnotationDefinition] sections. To maintain understandability between BEL documents, PyBEL
warns when the names given in :code:`*.bel` documents do not match their respective resources. For now, capitalization
is not considered, but in the future, PyBEL will also warn when capitalization is not properly stylized, like forgetting
the lowercase 'h' in "ChEMBL".

Why Not Nested Statements?
~~~~~~~~~~~~~~~~~~~~~~~~~~
BEL has different relationships for modeling direct and indirect causal relations.

Direct
******
- :code:`A => B` means that `A` directly increases `B` through a physical process.
- :code:`A =| B` means that `A` directly decreases `B` through a physical process.

Indirect
********
The relationship between two entities can be coded in BEL, even if the process is not well understood.

- :code:`A -> B` means that `A` indirectly increases `B`. There are hidden elements in `X` that mediate this interaction
  through a pathway direct interactions :code:`A (=> or =|) X_1 (=> or =|) ... X_n (=> or =|) B`, or through an entire
  network.

- :code:`A -| B` means that `A` indirectly decreases `B`. Like for :code:`A -> B`, this process involves hidden
  components with varying activities.

Increasing Nested Relationships
*******************************
BEL also allows object of a relationship to be another statement.

- :code:`A => (B => C)` means that `A` increases the process by which `B` increases `C`. The example in the BEL Spec
  :code:`p(HGNC:GATA1) => (act(p(HGNC:ZBTB16)) => r(HGNC:MPL))` represents GATA1 directly increasing the process by
  which ZBTB16 directly increases MPL. Before, we were using directly increasing to specify physical contact, so it's
  reasonable to conclude that  :code:`p(HGNC:GATA1) => act(p(HGNC:ZBTB16))`. The specification cites examples when `B`
  is an activitythat only is affected in the context of `A` and `C`. This complicated enough that it is both impractical
  to standardize during curation, and impractical to represent in a network.

- :code:`A -> (B => C)` can be interpreted by assuming that `A` indirectly increases `B`, and because of monotonicity,
  conclude that :code:`A -> C` as well.

- :code:`A => (B -> C)` is more difficult to interpret, because it does not describe which part of process
  :code:`B -> C` is affected by `A` or how. Is it that :code:`A => B`, and :code:`B => C`, so we conclude
  :code:`A -> C`, or does it mean something else? Perhaps `A` impacts a different portion of the hidden process in
  :code:`B -> C`. These statements are ambiguous enough that they should be written as just :code:`A => B`, and
  :code:`B -> C`. If there is no literature evidence for the statement :code:`A -> C`, then it is not the job of the
  curator to make this inference. Identifying statements of this might be the goal of a bioinformatics analysis of the
  BEL network after compilation.

- :code:`A -> (B -> C)` introduces even more ambiguity, and it should not be used.

- :code:`A => (B =| C)` states `A` increases the process by which `B` decreases `C`. One interpretation of this
  statement might be that :code:`A => B` and :code:`B =| C`. An analysis could infer :code:`A -| C`.  Statements in the
  form of :code:`A -> (B =| C)` can also be resolved this way, but with added ambiguity.

Decreasing Nested Relationships
*******************************
While we could agree on usage for the previous examples, the decrease of a nested statement introduces an unreasonable
amount of ambiguity.

- :code:`A =| (B => C)` could mean `A` decreases `B`, and `B` also increases `C`. Does this mean A decreases C, or does
  it mean that C is still increased, but just not as much? Which of these statements takes precedence? Or do their
  effects cancel? The same can be said about :code:`A -| (B => C)`, and with added ambiguity for indirect increases
  :code:`A -| (B -> C)`

- :code:`A =| (B =| C)` could mean that `A` decreases `B` and `B` decreases `C`. We could conclude that `A` increases
  `C`, or could we again run into the problem of not knowing the precedence? The same is true for the indirect versions.

Reccomendations for Use in PyBEL
********************************
We considered the ambiguity of nested statements to be too great of a risk to include their usage in the PyBEL compiler.
In our group at Fraunhofer SCAI, curators resolved these statements to single statements to improve the precision and
readability of our BEL documents.

While most statements in the form :code:`A rel1 (B rel2 C)` can be reasonably expanded to :code:`A rel1 B` and
:code:`B rel2 C`, the few that cannot are the difficult-to-interpret cases that we need to be careful about in our
curation and later analyses.
