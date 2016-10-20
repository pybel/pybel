Roadmap
=======

Current Features
----------------

- Easy to install with pip
- Easy to use, with most common functions at top package level
- Good documentation and tutorials
- Extensible API, allowing for bioinformaticians to develop their own algorithms and own their data, instead of using
  a complicated plugin in Cytoscape with multiple dependencies and little ability for export or customization
- Caching system for downloaded data

Issues
------

- Only the most common parts of BEL 1.0 are fully supported. If there are statements you are expressing that
  you would like added, open an issue on GitHub.
- Speed is still an issue, because documents above 100K lines still take a couple minutes to run. This issue is
  exacerbated by (optionally) logging output to the console, which can make it more than 3x or 4x as slow.
- The default namespaces from OpenBEL do not follow a standard file format. They are similar to INI config files,
  but do not use consistient delimiters. Also, many of the namespaces don't respect that the delimiter should not
  be used in the namespace names. There are also lots of names with strange characters, which may have been caused
  by copying from a data source that had specfic escape characters without proper care.
- Testing was very difficult because the example documents on the OpenBEL website had many semantic errors, such as
  using names and annotation values that were not defined within their respective namespace and annotation definition
  files. They also contained syntax errors like naked names, which are not only syntatically incorrect, but lead to
  bad science; and improper usage of activities, like illegally nesting an activity within a composite statement.

Roadmap
-------

Data Management
~~~~~~~~~~~~~~~

- Parallelization of BEL tokenization
- Query tools for BELGraph and nx.MultiDiGraph
- Database import and export with SQLAlchemy

Knowledge Assembly
~~~~~~~~~~~~~~~~~~

- Integration of prior knowledge, such orthology between genes/proteins and resolution of protein complex names
- Integration of heirarchical information, insertion of missing complex members and protein family heirarchies
- Leverage of ontologies in the OWL format for disease-specific entities and annotations

Post-Processing Tools
~~~~~~~~~~~~~~~~~~~~~

- Implementation of Reverse Causal Reasoning and Network Perturbation Amplitude
- Distributed BEL document infrastructure
- Semantic Diff tool
