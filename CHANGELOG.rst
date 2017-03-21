Change Log
==========
All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <http://keepachangelog.com/>`_
and this project adheres to `Semantic Versioning <http://semver.org/>`_

`0.4.3 <https://github.com/pybel/pybel/compare/v0.4.2...v0.4.3>`_ - 2017-03-21
------------------------------------------------------------------------------
Added
~~~~~
- Documentation for constants
- Date validation on parse-time

Changed
~~~~~~~
- Externalized strings from modifier parsers
- Move pybel.cx.hash_tuple to pybel.utils.hash_tuple

Fixed
~~~~~
- Output to CX on CLI crashing
- Assignment of graph metadata on reload

`0.4.2 <https://github.com/pybel/pybel/compare/v0.4.1...v0.4.2>`_ - 2017-03-16
------------------------------------------------------------------------------
Added
~~~~~
- Node property data model and I/O
- Edge property data model and I/O

Changed
~~~~~~~
- Update version checking to be more lenient

Removed
~~~~~~~
- Origin completion option on BEL parsing. See `PyBEL Tools <http://pybel-tools.readthedocs.io/en/latest/mutation.html#pybel_tools.mutation.infer_central_dogma>`_

`0.4.1 <https://github.com/pybel/pybel/compare/v0.4.0...v0.4.1>`_ - 2017-03-11
------------------------------------------------------------------------------
Added
~~~~~
- More output options for BEL
- Explicit parsing of hasVariant, hasReactant, and hasProduct

Fixed
~~~~~
- Allow parsing of non-standard ordering of annotations
- Superfluous output of single nodes when writing BEL scripts

`0.4.0 <https://github.com/pybel/pybel/compare/v0.3.11...v0.4.0>`_ - 2017-03-07
-------------------------------------------------------------------------------
Added
~~~~~
- Stable CX import and export
- Edge Store data models and loading
- Alternative control parsing technique without citation clearing
- Node name calculator

`0.3.11 <https://github.com/pybel/pybel/compare/v0.3.10...v0.3.11>`_ - 2017-03-05
---------------------------------------------------------------------------------
Fixed
~~~~~
- Fixed has_members not adding annotations tag
- Reliance on node identifiers in canonicalization of complexes and composites
- Fixed graph iterator filter

`0.3.10 <https://github.com/pybel/pybel/compare/v0.3.9...v0.3.10>`_ - 2017-03-01
--------------------------------------------------------------------------------
Added
~~~~~
- Shortcut for adding unqualified edges

Fixed
~~~~~
- All edges have annotations dictionary now
- JSON Export doesn't crash if there aren't list annotations
- All exceptions have __str__ function for stringification by JSON export if desired

`0.3.9 <https://github.com/pybel/pybel/compare/v0.3.8...v0.3.9>`_ - 2017-02-21
------------------------------------------------------------------------------
Added
~~~~~
- Experimental CX export for use with NDEx

Changed
~~~~~~~
- Better testing with thorough BEL

Fixed
~~~~~
- ParseResult objects no longer propogate through graph
- Fixed outputting to JSON

Removed
~~~~~~~
- Support for importing GraphML is no longer continued because there's too much information loss

`0.3.8 <https://github.com/pybel/pybel/compare/v0.3.7...v0.3.8>`_ - 2017-02-12
------------------------------------------------------------------------------
Added
~~~~~
- Annotation pattern definitions
- Alternative json output to in-memory dictionary

Changed
~~~~~~~
- Removed url rewriting for OpenBEL Framework
- Group all annotations in edge data (see Data Model in docs)

`0.3.7 <https://github.com/pybel/pybel/compare/v0.3.6...v0.3.7>`_ - 2017-02-06
------------------------------------------------------------------------------
Added
~~~~~
- Added equivalentTo relation
- Added OWL annotation support
- Version integrity checking
- Dump cache functionality

Changed
~~~~~~~
- Merged GENE, GENE_VARIANT, and GENE_FUSION

`0.3.6 <https://github.com/pybel/pybel/compare/v0.3.5...v0.3.6>`_ - 2017-02-03
------------------------------------------------------------------------------
Changed
~~~~~~~
- Switch ontospy dependency to onto2nx for Windows support

`0.3.5 <https://github.com/pybel/pybel/compare/v0.3.4...v0.3.5>`_ - 2017-01-30
------------------------------------------------------------------------------
Added
~~~~~
- Add thorough testing of BEL document

Changed
~~~~~~~
- Improved string externalization
- Update to data model for fusions
- Improved parser performance

`0.3.4 <https://github.com/pybel/pybel/compare/v0.3.3...v0.3.4>`_ - 2017-01-22
------------------------------------------------------------------------------
Added
~~~~~
- Codec support for opening files by path

Changed
~~~~~~~
- Protein modifications, gene modifications, and variants are now stored as dictionaries in the latent data structure
- Many constants have been externalized
- BEL default names, like kinaseActivity are automatically assigned a sentinel value as a namespace

`0.3.3 <https://github.com/pybel/pybel/compare/v0.3.2...v0.3.3>`_ - 2017-01-18
------------------------------------------------------------------------------
Added
~~~~~
- Make HGVS parsing less complicated by storing as strings
- add warning tracking

`0.3.2 <https://github.com/pybel/pybel/compare/v0.3.1...v0.3.2>`_ - 2017-01-13
------------------------------------------------------------------------------
Added
~~~~~
- Gene modification support
- Namespace equivalence mapping data models and manager
- Extension loading

Changed
~~~~~~~
- Better testing (local files only with mocks)
- Better names for exceptions and warnings

`0.3.1 <https://github.com/pybel/pybel/compare/v0.3.0...v0.3.1>`_ - 2017-01-03
------------------------------------------------------------------------------
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

`0.3.0 <https://github.com/pybel/pybel/compare/v0.2.6...v0.3.0>`_ - 2016-12-29
------------------------------------------------------------------------------
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

`0.2.6 <https://github.com/pybel/pybel/compare/v0.2.5...v0.2.6>`_ - 2016-11-19
------------------------------------------------------------------------------
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

`0.2.5 <https://github.com/pybel/pybel/compare/v0.2.4...v0.2.5>`_ - 2016-11-13
------------------------------------------------------------------------------
Added
~~~~~
- Nested statement parsing support
- Fusion parsing support

Fixed
~~~~~
- Fixed graphml input/output
- Changed encodings of python files to utf-8
- Fixed typos in language.py

`0.2.4 <https://github.com/pybel/pybel/compare/v0.2.4...v0.2.5>`_ - 2016-11-13
------------------------------------------------------------------------------
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

`0.2.3 <https://github.com/pybel/pybel/compare/v0.2.2...v0.2.3>`_ - 2016-11-09
------------------------------------------------------------------------------
Changed
~~~~~~~
- Made logging lazy and updated logging codes
- Update rewriting of old statements
- Explicitly streamlined MatchFirst statements; huge speed improvements

`0.2.2 <https://github.com/pybel/pybel/compare/v0.2.1...v0.2.2>`_ - 2016-10-25
------------------------------------------------------------------------------
Removed
~~~~~~~
- Documentation is no longer stored in version control
- Fixed file type in CLI

`0.2.1 <https://github.com/pybel/pybel/compare/v0.2.0...v0.2.1>`_ - 2016-10-25 [YANKED]
---------------------------------------------------------------------------------------
Added
~~~~~
- Added CLI for data manager

0.2.0 - 2016-10-22
------------------
Added
~~~~~
- Added definition cache manager

Diffs
-----
- [Unreleased]: https://github.com/pybel/pybel/compare/v0.4.3...HEAD
- [0.4.3]: https://github.com/pybel/pybel/compare/v0.4.2...v0.4.3
- [0.4.2]: https://github.com/pybel/pybel/compare/v0.4.1...v0.4.2
- [0.4.1]: https://github.com/pybel/pybel/compare/v0.4.0...v0.4.1
- [0.4.0]: https://github.com/pybel/pybel/compare/v0.3.11...v0.4.0
- [0.3.11]: https://github.com/pybel/pybel/compare/v0.3.10...v0.3.11
- [0.3.10]: https://github.com/pybel/pybel/compare/v0.3.9...v0.3.10
- [0.3.9]: https://github.com/pybel/pybel/compare/v0.3.8...v0.3.9
- [0.3.8]: https://github.com/pybel/pybel/compare/v0.3.7...v0.3.8
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
