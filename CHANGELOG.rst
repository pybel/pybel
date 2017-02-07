Change Log
==========
All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <http://keepachangelog.com/>`_
and this project adheres to `Semantic Versioning <http://semver.org/>`_

[0.3.7] - 2017-02-06
--------------------
Added
~~~~~
- Added equivalentTo relation
- Added OWL annotation support
- Version integrity checking
- Dump cache functionality

Changed
~~~~~~~
- Merged GENE, GENE_VARIANT, and GENE_FUSION

[0.3.6] - 2017-02-03
--------------------
Changed
~~~~~~~
- Switch ontospy dependency to onto2nx for Windows support

[0.3.5] - 2017-01-30
--------------------
Added
~~~~~
- Add thorough testing of BEL document

Changed
~~~~~~~
- Improved string externalization
- Update to data model for fusions
- Improved parser performance

[0.3.4] - 2017-01-22
--------------------
Added
~~~~~
- Codec support for opening files by path

Changed
~~~~~~~
- Protein modifications, gene modifications, and variants are now stored as dictionaries in the latent data structure
- Many constants have been externalized
- BEL default names, like kinaseActivity are automatically assigned a sentinel value as a namespace

[0.3.3] - 2017-01-18
--------------------
Added
~~~~~
- Make HGVS parsing less complicated by storing as strings
- add warning tracking

[0.3.2] - 2017-01-13
--------------------
Added
~~~~~
- Gene modification support
- Namespace equivalence mapping data models and manager
- Extension loading

Changed
~~~~~~~
- Better testing (local files only with mocks)
- Better names for exceptions and warnings

[0.3.1] - 2017-01-03
--------------------
Added
~~~~~
- Bytes IO of BEL Graphs
- Graph caching and Graph Cache Manager

Fixed
~~~~~
- Annotations weren't getting cached because *somebody* forgot to add the urls. Fixed.
- Removed typos in default namespace list

Changed
~~~~~~~
- More explicit tests and overall test case refactoring
- Better handling of BEL script metadata

[0.3.0] - 2016-12-29
--------------------
Added
~~~~~
- OWL namespace support and caching
- Full support for BEL canonicalization and output

Fixed
~~~~~
- Rewrote namespace cache and SQLAlchemy models

Removed
~~~~~~~
- Removed unnecessary pandas and matplotlib dependencies

[0.2.6] - 2016-11-19
--------------------
Added
~~~~~
- Canonical BEL terms added to nodes on parsing
- Fragment parsing
- Support for alternative names for evidence (SupportingText)
- More explicit support of unqualified edges
- Created top-level constants file

Fixed
~~~~~
- Fix incorrect HGVS protein truncation parsing
- Fix missing location option in abundance tag parsing
- Fix json input/output

Removed
~~~~~~~
- Deleted junk code from mapper and namespace cache manager

[0.2.5] - 2016-11-13
--------------------
Added
~~~~~
- Nested statement parsing support
- Fusion parsing support

Fixed
~~~~~
- Fixed graphml input/output
- Changed encodings of python files to utf-8
- Fixed typos in language.py

[0.2.4] - 2016-11-13
--------------------
Added
~~~~~
- Neo4J CLI output
- Edge and node filtering
- Assertions of document metadata key
- Added BEL 2.0 protein modification default mapping support

Changed
~~~~~~~
- Rewrite HGVS parsing
- Updated canonicalization

Fixed
~~~~~
- Typo in amino acid dictionary
- Assertion of citation

[0.2.3] - 2016-11-09
--------------------
Changed
~~~~~~~
- Made logging lazy and updated logging codes
- Update rewriting of old statements
- Explicitly streamlined MatchFirst statements; huge speed improvements

[0.2.2] - 2016-10-25
--------------------
Removed
~~~~~~~
- Documentation is no longer stored in version control
- Fixed file type in CLI

[0.2.1] - 2016-10-25 [YANKED]
-----------------------------
Added
~~~~~
- Added CLI for data manager

[0.2.0] - 2016-10-22
--------------------
Added
~~~~~
- Added definition cache manager

Diffs
-----

- [Unreleased]: https://github.com/pybel/pybel/compare/v0.3.7...HEAD
- [0.3.7]: https://github.com/pybel/pybel/compare/v0.3.6...v0.3.7
- [0.3.6]: https://github.com/pybel/pybel/compare/v0.3.5...v0.3.6
- [0.3.5]: https://github.com/pybel/pybel/compare/v0.3.4...v0.3.5
- [0.3.4]: https://github.com/pybel/pybel/compare/v0.3.3...v0.3.4
- [0.3.3]: https://github.com/pybel/pybel/compare/v0.3.2...v0.3.3
- [0.3.2]: https://github.com/pybel/pybel/compare/v0.3.1...v0.3.2
- [0.3.1]: https://github.com/pybel/pybel/compare/v0.3.0...v0.3.1
- [0.3.0]: https://github.com/pybel/pybel/compare/v0.2.6...v0.3.0
- [0.2.6]: https://github.com/pybel/pybel/compare/v0.2.5...v0.2.6
- [0.2.5]: https://github.com/pybel/pybel/compare/v0.2.4...v0.2.5
- [0.2.4]: https://github.com/pybel/pybel/compare/v0.2.3...v0.2.4
- [0.2.3]: https://github.com/pybel/pybel/compare/v0.2.2...v0.2.3
- [0.2.2]: https://github.com/pybel/pybel/compare/v0.2.1...v0.2.2
- [0.2.1]: https://github.com/pybel/pybel/compare/v0.2.0...v0.2.1