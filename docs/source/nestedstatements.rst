Why Not Nested Statements?
==========================

BEL has different relationships for modeling direct and indirect causal relations.

Direct
------

- :code:`A => B` means that `A` directly increases `B` through a physical process.
- :code:`A =| B` means that `A` directly decreases `B` through a physical process.

Indirect
--------

The relationship between two entities can be coded in BEL, even if the process is not well understood.

- :code:`A -> B` means that `A` indirectly increases `B`. There are hidden elements in `X` that mediate this interaction through a pathway direct interactions :code:`A (=> or =|) X_1 (=> or =|) ... X_n (=> or =|) B`, or through an entire network.

- :code:`A -| B` means that `A` indirectly decreases `B`. Like for :code:`A -> B`, this process involves hidden components with varying activities.

Increasing Nested Relationships
-------------------------------

BEL also allows object of a relationship to be another statement.

- :code:`A => (B => C)` means that `A` increases the process by which `B` increases `C`. The example in the BEL Spec :code:`p(HGNC:GATA1) => (act(p(HGNC:ZBTB16)) => r(HGNC:MPL))` represents GATA1 directly increasing the process by which ZBTB16 directly increases MPL. Before, we were using directly increasing to specify physical contact, so it's reasonable to conclude that  :code:`p(HGNC:GATA1) => act(p(HGNC:ZBTB16))`. The specification cites examples when `B` is an activity that only is affected in the context of `A` and `C`. This complicated enough that it is both impractical to standardize during curation, and impractical to represent in a network.

- :code:`A -> (B => C)` can be interpreted by assuming that `A` indirectly increases `B`, and because of monotonicity, conclude that :code:`A -> C` as well.

- :code:`A => (B -> C)` is more difficult to interpret, because it does not describe which part of process :code:`B -> C` is affected by `A` or how. Is it that :code:`A => B`, and :code:`B => C`, so we conclude :code:`A -> C`, or does it mean something else? Perhaps `A` impacts a different portion of the hidden process in :code:`B -> C`. These statements are ambiguous enough that they should be written as just :code:`A => B`, and :code:`B -> C`. If there is no literature evidence for the statement :code:`A -> C`, then it is not the job of the curator to make this inference. Identifying statements of this might be the goal of a bioinformatics analysis of the BEL network after compilation.

- :code:`A -> (B -> C)` introduces even more ambiguity, and it should not be used.

- :code:`A => (B =| C)` states `A` increases the process by which `B` decreases `C`. One interpretation of this statement might be that :code:`A => B` and :code:`B =| C`. An analysis could infer :code:`A -| C`.  Statements in the form of :code:`A -> (B =| C)` can also be resolved this way, but with added ambiguity.

Decreasing Nested Relationships
-------------------------------

While we could agree on usage for the previous examples, the decrease of a nested statement introduces an unreasonable amount of ambiguity.

- :code:`A =| (B => C)` could mean `A` decreases `B`, and `B` also increases `C`. Does this mean A decreases C, or does it mean that C is still increased, but just not as much? Which of these statements takes precedence? Or do their effects cancel? The same can be said about :code:`A -| (B => C)`, and with added ambiguity for indirect increases :code:`A -| (B -> C)`

- :code:`A =| (B =| C)` could mean that `A` decreases `B` and `B` decreases `C`. We could conclude that `A` increases `C`, or could we again run into the problem of not knowing the precedence? The same is true for the indirect versions.

Reccomendations for Use in PyBEL
--------------------------------

We considered the ambiguity of nested statements to be too great of a risk to include their usage in the PyBEL compiler. In our group at Fraunhofer SCAI, curators resolved these statements to single statements to improve the precision and readability of our BEL documents.

While most statements in the form :code:`A rel1 (B rel2 C)` can be reasonably expanded to :code:`A rel1 B` and :code:`B rel2 C`, the few that cannot are the difficult-to-interpret cases that we need to be careful about in our curation and later analyses.
