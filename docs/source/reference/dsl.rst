Internal Domain Specific Language
=================================
.. automodule:: pybel.dsl

Primitives
----------
.. autoclass:: pybel.dsl.Entity
.. autoclass:: pybel.dsl.BaseEntity
.. autoclass:: pybel.dsl.BaseAbundance
.. autoclass:: pybel.dsl.ListAbundance

Named Entities
--------------
.. autoclass:: pybel.dsl.Abundance
.. autoclass:: pybel.dsl.BiologicalProcess
.. autoclass:: pybel.dsl.Pathology
.. autoclass:: pybel.dsl.Population

Central Dogma
-------------
.. autoclass:: pybel.dsl.CentralDogma
.. autoclass:: pybel.dsl.Gene
.. autoclass:: pybel.dsl.Transcribable
.. autoclass:: pybel.dsl.Rna
.. autoclass:: pybel.dsl.MicroRna
.. autoclass:: pybel.dsl.Protein

Variants
~~~~~~~~
.. autoclass:: pybel.dsl.Variant
.. autoclass:: pybel.dsl.ProteinModification
.. autoclass:: pybel.dsl.GeneModification
.. autoclass:: pybel.dsl.Hgvs
.. autoclass:: pybel.dsl.HgvsReference
.. autoclass:: pybel.dsl.HgvsUnspecified
.. autoclass:: pybel.dsl.ProteinSubstitution
.. autoclass:: pybel.dsl.Fragment

Fusions
-------
.. autoclass:: pybel.dsl.FusionBase
.. autoclass:: pybel.dsl.GeneFusion
.. autoclass:: pybel.dsl.RnaFusion
.. autoclass:: pybel.dsl.ProteinFusion

Fusion Ranges
~~~~~~~~~~~~~
.. autoclass:: pybel.dsl.FusionRangeBase
.. autoclass:: pybel.dsl.EnumeratedFusionRange
.. autoclass:: pybel.dsl.MissingFusionRange

List Abundances
~~~~~~~~~~~~~~~
.. autoclass:: pybel.dsl.ComplexAbundance
.. autoclass:: pybel.dsl.CompositeAbundance
.. autoclass:: pybel.dsl.Reaction

Utilities
---------
The following functions are useful to build DSL objects from dictionaries:

.. autofunction:: pybel.tokens.parse_result_to_dsl
