Change Log
==========
All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <http://keepachangelog.com/>`_
and this project adheres to `Semantic Versioning <http://semver.org/>`_

`0.11.11 <https://github.com/pybel/pybel/compare/v0.11.10...0.11.11>`_ - 2018-07-31
-----------------------------------------------------------------------------------
Added
~~~~~
- Automatic generation of CLI documentation with ``sphinx-click``
- Several edge creation convenience functions to the ``BELGraph``
- Graph summary functions

Changed
~~~~~~~
- Improve Drop networks (Thanks @scolby33) (https://github.com/pybel/pybel/pull/319)
- Huge improvements to documentation and code style reccomended by flake8

Fixed
~~~~~
- Fixed handling of tuples (64d0685)

Removed
~~~~~~~
- Remove function ``BELGraph.iter_data``

`0.11.10 <https://github.com/pybel/pybel/compare/v0.11.9...0.11.10>`_ - 2018-07-23
----------------------------------------------------------------------------------
Added
~~~~~
- Several subgraph functions (https://github.com/pybel/pybel/pull/315)

Changed
~~~~~~~
- Better SQL implementation of get_recent_networks (https://github.com/pybel/pybel/pull/312)

`0.11.9 <https://github.com/pybel/pybel/compare/v0.11.8...0.11.9>`_ - 2018-07-??
--------------------------------------------------------------------------------
Removed
~~~~~~~
- Removed CX and NDEx IO in favor of https://github.com/pybel/pybel-cx

Changed
~~~~~~~
- Better (less annoying) logging for deprecated transformations
- Turn off SQL echoing by default
- Update getting annotation entries
- Better options for using TQDM while parsing

Added
~~~~~
- Flag to INDRA machine to run locally
- Add require annotations option to parser (https://github.com/pybel/pybel/issues/255)
- Data missing key node predicate builder

`0.11.8 <https://github.com/pybel/pybel/compare/v0.11.7...0.11.8>`_ - 2018-06-27
--------------------------------------------------------------------------------
Added
~~~~~
- Deprecation system for pipeline functions (for when they're renamed)

Changed
~~~~~~~
- Rely on edge predicates more heavily in selection/induction/expansion transformations
- Rename several functions related to the "central dogma" for more clarity

`0.11.7 <https://github.com/pybel/pybel/compare/v0.11.6...0.11.7>`_ - 2018-06-26
--------------------------------------------------------------------------------
Fixed
~~~~~
- Bug where data did not get copied to sub-graphs on induction (https://github.com/pybel/pybel/issues/#307)

`0.11.6 <https://github.com/pybel/pybel/compare/v0.11.5...0.11.6>`_ - 2018-06-25
--------------------------------------------------------------------------------
Added
~~~~~
- Added get_annotation_values function to pybel.struct.summary

Removed
~~~~~~~
- Removed Manager.ensure function

Fixed
~~~~~
- Fixed a bug in Manager.from_connection (https://github.com/pybel/pybel/issues/#306)

`0.11.5 <https://github.com/pybel/pybel/compare/v0.11.4...0.11.5>`_ - 2018-06-22
--------------------------------------------------------------------------------
Changed
~~~~~~~
- Changed arguments in pybel.struct.mutations.get_subgraphs_by_annotation
- Moved utility functions in pybel.struct.mutations

`0.11.4 <https://github.com/pybel/pybel/compare/v0.11.3...0.11.4>`_ - 2018-06-22
--------------------------------------------------------------------------------
Changed
~~~~~~~
- Use BELGraph.fresh_copy instead of importing the class in mutator functions

Added
~~~~~
- Add pipeline (https://github.com/pybel/pybel/issues/301)
- Testing of neighborhood functions
- Added several transformation and grouping functions for BELGraph
- INDRA Machine in CLI

Fixed
~~~~~
- Add missing field from BaseAbundance (https://github.com/pybel/pybel/issues/302)

`0.11.3 <https://github.com/pybel/pybel/compare/v0.11.2...0.11.3>`_ - 2018-06-04
--------------------------------------------------------------------------------
Added
~~~~~
- Made testing code and date install as part of main package(https://github.com/pybel/pybel/pull/298)

Removed
~~~~~~~
- Remove extension hook and extension loader (https://github.com/pybel/pybel/pull/300)

`0.11.2 <https://github.com/pybel/pybel/compare/v0.11.1...0.11.2>`_ - 2018-05-10
--------------------------------------------------------------------------------
Added
~~~~~
- Calculation of SHA512 hash to DSL abundances
- Documented the deployment extra for setup.py
- Added to and from JSON path IO functions
- PMI Contact for CBN import and more default namespaces
- Added common query builders to SQLAlchemy models

Fixed
~~~~~
- Fixed name/version lookup in the database
- Safer creation of directories (https://github.com/pybel/pybel/issues/#284)
- Make export to GraphML more boring and permissive
- Implement to_tuple for CentralDogma (https://github.com/pybel/pybel/issues/#281)
- Unicode compatibility error. Thanks @bgyori! (https://github.com/pybel/pybel/pull/289)

Changed
~~~~~~~
- Made parsing of fragments permissive to quoting (https://github.com/pybel/pybel/issues/#282)
- Update citation handling
- Update namespace methods in CLI
- Added ``as_bel`` method to DSL
- Update authentication with BEL Commons (https://github.com/pybel/pybel/commit/4f6b8b0ecab411e1d2b110e00c8bac77ace88308)
- Unpin SQLAlchemy version. Most up-to-date should remain safe.

Removed
~~~~~~~
- Removed static function ``pybel.BELGraph.hash_node`` since it just wraps ``pybel.utils.node_to_tuple``
- Removed unnecessary configuration editing from CLI
- Removed OWL Parser (https://github.com/pybel/pybel/issues/290)
- Removed support for BELEQ files (https://github.com/pybel/pybel/issues/294)
- Remove artifactory code and migrated to https://github.com/pybel/pybel-artifactory. (https://github.com/pybel/pybel/issues/292)

`0.11.1 <https://github.com/pybel/pybel/compare/v0.11.0...0.11.1>`_ - 2018-02-19
--------------------------------------------------------------------------------
Added
~~~~~
- Added additional DSL shortcuts for building edges with the BELGraph
- Added example graphs (statins, BRAF, orthology examples)
- Added knowledge transfer function
- Added progress bar for parser

`0.11.0 <https://github.com/pybel/pybel/compare/v0.10.1...0.11.0>`_ - 2018-02-07
--------------------------------------------------------------------------------
Changed
~~~~~~~
- Updated SQL schema and made new minimum unpickle version 0.11.0.
- Parser now uses a compact representation of annotations instead of exploding to multiple edges (https://github.com/pybel/pybel/issues/261)
- Update annotation filtering functions to reflect new data format (https://github.com/pybel/pybel/issues/262)
- Update GraphML Output (https://github.com/pybel/pybel/issues/260)
- Better error message when missing namespace resource (https://github.com/pybel/pybel/issues/265)

Fixed
~~~~~
- Fixed more problems with edge store and testing (https://github.com/pybel/pybel/issues/225, https://github.com/pybel/pybel/issues/256, https://github.com/pybel/pybel/issues/257)
- Fixed windows testing (https://github.com/pybel/pybel/issues/243)
- Fixed broken network cascade, but is still slow (https://github.com/pybel/pybel/issues/256, https://github.com/pybel/pybel/issues/257, https://github.com/pybel/pybel/issues/259)
- Fixed JGIF import (https://github.com/pybel/pybel/issues/266) and added scripts directory (3dc6b1f)
- Fix extras in setup.py and requirements.txt

Added
~~~~~
- Additional regex format for date parsing from PubMed (https://github.com/pybel/pybel/issues/259)
- Add labels to nodes in GraphML output (https://github.com/pybel/pybel/issues/260)
- Add edge predicate builders (https://github.com/pybel/pybel/issues/262)
- Testing on multiple databases (SQLite, MySQL, PostgreSQL) (https://github.com/pybel/pybel/issues/238)
- Added ``pybel.struct.mutations`` module
- Added graph-based equivalency checking
- Add more documentation to BELGraph (https://github.com/pybel/pybel/issues/271)

`0.10.1 <https://github.com/pybel/pybel/compare/v0.10.0...0.10.1>`_ - 2017-12-28
--------------------------------------------------------------------------------
Fixed
~~~~~
- Fixed truncation description parsing to handle double quotes

Changed
~~~~~~~
- Made DSL functions into classes to allow inheritance and isinstance checking as well as
  preliminary to_tuple functionality

Added
~~~~~
- Added more edge predicates (has_activity, has_degree, has_translocation, has_annotation)

`0.10.0 <https://github.com/pybel/pybel/compare/v0.9.7...0.10.0>`_ - 2017-12-22
-------------------------------------------------------------------------------
Changed
~~~~~~~
- Updated SQL schema and made new minimum unpickle version 0.10.0.
- Moved `pybel.parser.language` to `pybel.language`
- Moved `pybel.parser.canoncalize` to `pybel.tokens`
- Overhaul of `pybel.struct.filters` - included many more functions, tests, and updated nomenclature
- Update canoncalize functions to be generally reusable (take node data dictionaries)
- Make NDEx2, Neo4j, OWL parsing, and INDRA setup.py install extras

Fixed
~~~~~
- Names defined by regular expressions can now be included in the database cache (https://github.com/pybel/pybel/issues/250, https://github.com/pybel/pybel/issues/251)
- Fixed ``Manager.has_name_version`` (https://github.com/pybel/pybel/issues/246)
- Fixed CX output and upgraded to NDEx2 client
- When joining graphs, keep their metadata (https://github.com/pybel/pybel/commit/affaecc73d2b4affa8aeecb3834ed7c6f5697cac)

Added
~~~~~
- Included partOf relationship in BEL language (https://github.com/pybel/pybel/issues/244)
- Added additional date formats to parse from PubMed (https://github.com/pybel/pybel/issues/239)
- Filled out many more DSL functions and added testing
- Added ability to set relationship parsing policy in BEL Parser (https://github.com/pybel/pybel/commit/09614465d80d2931e901fd54d067a5151e327283)
- Implemented from PyBEL Web Function
- Implemented to INDRA function

`0.9.7 <https://github.com/pybel/pybel/compare/v0.9.6...0.9.7>`_ - 2017-11-20
-----------------------------------------------------------------------------
Changed
~~~~~~~
- Use ``HASH`` as dictionary key instead of ``ID``
- Allow DSL to create nodes without names but with identifiers
- Rename instance variables in parsers for consistency
- Greater usage of DSL in parser

`0.9.6 <https://github.com/pybel/pybel/compare/v0.9.5...0.9.6>`_ - 2017-11-12
-----------------------------------------------------------------------------
Added
~~~~~
- Additional keyword arguments for JSON output functions

Changed
~~~~~~~
- Updated parser intermediate data structure. Should have no affect on end users.
- Smarter serialization of PyBEL data dictionaries to BEL

Fixed
~~~~~
- Better handling of citations that have authors pre-parsed into lists (https://github.com/pybel/pybel/issues/247)

`0.9.5 <https://github.com/pybel/pybel/compare/v0.9.4...0.9.5>`_ - 2017-11-07
-----------------------------------------------------------------------------
Added
~~~~~
- Updates to DSL
- More node filters and predicates
- Added "partOf" relationship (https://github.com/pybel/pybel/issues/244)
- Added more regular expressions for date parsing (https://github.com/pybel/pybel/issues/239)

Fixed
~~~~~
- Fixed incorrect checking of network storage (https://github.com/pybel/pybel/issues/246)

Changed
~~~~~~~
- Reorganized resources module to reduce dependencies on PyBEL Tools, which has lots of other big requirements
- Moved ``pybel.summary`` module to ``pybel.struct.summary``


`0.9.4 <https://github.com/pybel/pybel/compare/v0.9.3...0.9.4>`_ - 2017-11-03
-----------------------------------------------------------------------------
Fixed
~~~~~
- Problem with uploading products, reactants, and members to NDEx (#230)
- Checking for adding uncachable nodes when populating edge store

Added
~~~~~
- Database seeding functions
- Citation management
- Added PubMed Central as type in citation

Removed
~~~~~~~
- Don't keep blobs in node or edge cache anymore

`0.9.3 <https://github.com/pybel/pybel/compare/v0.9.2...0.9.3>`_ - 2017-10-19
-----------------------------------------------------------------------------
Added
~~~~~
- Convenience functions for adding qualified and unqualified edges to BELGraph class
- Sialic Acid Example BEL Graph
- EGF Example BEL Graph
- Added PyBEL Web export and stub for import
- BioPAX Import
- Dedicated BEL Syntax error

Changed
~~~~~~~
- Update the BEL Script canonicalization rules to group citations then evidences better
- Removed requirement of annotation entry in edge data dictionaries
- Confident enough to make using the edge store True by default

Fixed
~~~~~
- Fixed unset list parsing so it doesn't need quotes (#234)

Removed
~~~~~~~
- In-memory caching of authors

`0.9.2 <https://github.com/pybel/pybel/compare/v0.9.1...0.9.2>`_ - 2017-09-27
-----------------------------------------------------------------------------
Fixed
~~~~~
- JSON Serialization bug for authors in Citation Model

`0.9.1 <https://github.com/pybel/pybel/compare/v0.9.0...0.9.1>`_ - 2017-09-26
-----------------------------------------------------------------------------
Added
~~~~~
- INDRA Import
- Usage of built-in operators on BEL Graphs

Changed
~~~~~~~
- Update list recent networks function to work better with SQL 99 compliant (basically everything except the
  old version of MySQL and SQLite) RDBMS
- Better tests for queries to edge store
- Better testing when extensions not installed (c1ac850)
- Update documentation to new OpenBEL website links

Fixed
~~~~~
- Fix crash when uploading network to edge store that has annotation pattern definitions (still needs some work though)
- Added foreign keys for first and last authors in Citation model (requires database rebuild)
- Froze NetworkX version at 1.11 since 2.0 breaks everything

Removed
~~~~~~~
- Don't cache SQLAlchemy models locally (3d7d238)

`0.9.0 <https://github.com/pybel/pybel/compare/v0.8.1...0.9.0>`_ - 2017-09-19
-----------------------------------------------------------------------------
Added
~~~~~
- Option for setting scopefunc in Manager
- Include extra citation information on inserting graph to database that might have come from citation enrichment
- Node model to tuple and json functions are now complete

Changed
~~~~~~~
- Added members lists to the node data dictionaries for complex and composite nodes
- Added reactants and products lists to the node data dictionaries for reaction nodes

Fixed
~~~~~~~
- GOCC and other location caching problem
- Node tuples for reactions are now using standard node tuples for reactants and products. This was a huge issue
  but it had never come up before. DANGER - this means all old code will still work, but any node-tuple reliant
  code will have unexpected results. This also means that the node hashes in the database for all reactions will
  now be outdated, so the minimum version is being bumped.

`0.8.1 <https://github.com/pybel/pybel/compare/v0.8.0...v0.8.1>`_ - 2017-09-08
------------------------------------------------------------------------------
Changed
~~~~~~~
- Change CacheManager class name to Manager
- Change references from build_manager to Manager.ensure
- Automatically update default database to minimum import version
- Constants for extra citation fields and update to_json for Citation model

Fixed
~~~~~
- Bug in author insertion for non-unique authors

`0.8.0 <https://github.com/pybel/pybel/compare/v0.7.3...v0.8.0>`_ - 2017-09-08
------------------------------------------------------------------------------
Changed
~~~~~~~
- Made new minimum unpickle version 0.8.0. From now on, all unpickle changes (before a 1.0.0 release) will be accompanied by a minor version bump.
- Overall better handling of citation insertion
- Updated data models. Added to Citation model and renamed namespaceEntry in Node model.
- Better init function for BELGraph
- Force name and version to not be null in the database
- Update pickle references to use six module
- Update base cache manager - better connection handling and more exposed arguments

Added
~~~~~
- Get graph functions to cache manager
- Added more useful functions to cache manager
- Kwargs for setting name, version, and description in BELGraph init
- Getters and setters for version and description in BELGraph
- Node data to tuple functions (https://github.com/pybel/pybel/issues/145)

`0.7.3 <https://github.com/pybel/pybel/compare/v0.7.2...v0.7.3>`_ - 2017-09-05
------------------------------------------------------------------------------
Changed
~~~~~~~
- Update logging for parsing of bad version strings
- Change where kwargs go in parse_lines function
- Make non-standard parsing modes part of kwargs

Fixed
~~~~~
- On-purpose singletons now properly identified (https://github.com/pybel/pybel/issues/218)

Added
~~~~~
- CLI command for set connection (https://github.com/pybel/pybel/issues/220)
- GEF and GAP activities added for INDRA

`0.7.2 <https://github.com/pybel/pybel/compare/v0.7.1...v0.7.2>`_ - 2017-08-10
------------------------------------------------------------------------------
Changed
~~~~~~~
- Externalized more parsing constants
- Updated version management
- Keep track of all singleton lines in parsing
- Update CLI
- Update JGIF export from CBN

Fixed
~~~~~
- Change node hashing ot only use type and reference

Added
~~~~~
- Node intersection merge
- Get most recent network by name in manager

`0.7.1 <https://github.com/pybel/pybel/compare/v0.7.0...v0.7.1>`_ - 2017-07-25
------------------------------------------------------------------------------
Changed
~~~~~~~
- Externalized some PyParsing elements

Fixed
~~~~~
- Version string tokenization

`0.7.0 <https://github.com/pybel/pybel/compare/v0.6.2...v0.7.0>`_ - 2017-07-21
------------------------------------------------------------------------------
Added
~~~~~
- Added Project key to document metadata parser (https://github.com/pybel/pybel/issues/215)
- Reusable protocols for hashing nodes and edges

Fixed
~~~~~
- Edge store working (https://github.com/pybel/pybel/issues/212)

Changed
~~~~~~~
- Update resource urls (https://github.com/pybel/pybel/issues/211)
- General improvements to exception handling
- Made new minimum unpickle version 0.7.0

`0.6.2 <https://github.com/pybel/pybel/compare/v0.6.1...v0.6.2>`_ - 2017-06-28
------------------------------------------------------------------------------
Added
~~~~~
- Environment variable for data locations
- Add get network by ids merger

`0.6.1 <https://github.com/pybel/pybel/compare/v0.6.0...v0.6.1>`_ - 2017-06-25
------------------------------------------------------------------------------
Added
~~~~~
- Node and edge filter framework (https://github.com/pybel/pybel/issues/206)
- Network joining (https://github.com/pybel/pybel/issues/205 and https://github.com/pybel/pybel/issues/204)
- More thorough tests of IO

Fixed
~~~~~
- Bug when getting multiple networks by identifier (https://github.com/pybel/pybel/issues/208)
- Arguments to exceptions mixed up

Changed
~~~~~~~
- Use context in command line interface to streamline code
- Remove old, unused code


`0.6.0 <https://github.com/pybel/pybel/compare/v0.5.11...v0.6.0>`_ - 2017-06-11
-------------------------------------------------------------------------------
Changed
~~~~~~~
- Merge OWL and BEL namespaces (https://github.com/pybel/pybel/issues/118)
- Remove lots of unused/redundant code
- Lots of functions renamed and moved... Sorry people.

Added
~~~~~
- Multiple options for graph joining
- Filter functions (https://github.com/pybel/pybel/issues/206)


`0.5.11 <https://github.com/pybel/pybel/compare/v0.5.10...v0.5.11>`_ - 2017-06-07
---------------------------------------------------------------------------------
Changed
~~~~~~~
- Added line numbers to parsing exceptions
- Update minimum pickle parsing from 0.5.10 to 0.5.11 to reflect changes in parsing exceptions


`0.5.10 <https://github.com/pybel/pybel/compare/v0.5.9...v0.5.10>`_ - 2017-06-06
--------------------------------------------------------------------------------
Added
~~~~~
- Network outer join (https://github.com/pybel/pybel/issues/205)
- Network full join with hash (https://github.com/pybel/pybel/issues/204 and https://github.com/pybel/pybel/issues/204)
- Option to suppress singleton warnings (https://github.com/pybel/pybel/issues/200)

Changed
~~~~~~~
- Moved :mod:`pybel.graph` to :mod:`pybel.struct.graph`
- Parse exceptions are renamed
- Update minimum pickle parsing from 0.5.4 to 0.5.10 to reflect changes in parsing execeptions and project structure

Fixed
~~~~~
- Rewrote the CSV Exporter (https://github.com/pybel/pybel/issues/201)

`0.5.9 <https://github.com/pybel/pybel/compare/v0.5.8...v0.5.9>`_ - 2017-05-28
------------------------------------------------------------------------------
Added
~~~~~
- JGIF interchange (https://github.com/pybel/pybel/issues/193) and (https://github.com/pybel/pybel/issues/194)
- Configuration file parsing (https://github.com/pybel/pybel/issues/197)

`0.5.8 <https://github.com/pybel/pybel/compare/v0.5.7...v0.5.8>`_ - 2017-05-25
------------------------------------------------------------------------------
Changed
~~~~~~~
- CX is now unstreamified on load, making compatibility with other CX sources (like NDEx) possible
- Testing now enables ``PYBEL_TEST_CONNECTION`` environment variable to set a persistient database
- Testing data cut down to reduce memory consumption

Added
~~~~~
- NDEx upload and download

`0.5.7 <https://github.com/pybel/pybel/compare/v0.5.5...v0.5.7>`_ - 2017-05-20
------------------------------------------------------------------------------
Changed
~~~~~~~
- Public IO changed for to/from_json and to/from_cx (https://github.com/pybel/pybel/issues/192)
- Better error output for metadata failure (https://github.com/pybel/pybel/issues/191)

Added
~~~~~
- Add BEL script line to edges (https://github.com/pybel/pybel/issues/155)
- Export to GSEA gene list (https://github.com/pybel/pybel/issues/189)
- Non-caching of namespaces support (https://github.com/pybel/pybel/issues/190)

Note: I made a mistake with the release on 0.5.6, so I just bumped the patch one more.

`0.5.5 <https://github.com/pybel/pybel/compare/v0.5.4...v0.5.5>`_ - 2017-05-08
------------------------------------------------------------------------------
Changed
~~~~~~~
- Updated CX output to have full provenance and list definitions (https://github.com/pybel/pybel/issues/180)

Added
~~~~~
- DOI and URL are now acceptable citation types (https://github.com/pybel/pybel/issues/188)
- Citation can now be given as a double of type and reference (https://github.com/pybel/pybel/issues/187)


`0.5.4 <https://github.com/pybel/pybel/compare/v0.5.3...v0.5.4>`_ - 2017-04-28
------------------------------------------------------------------------------
Fixed
~~~~~
- MySQL truncations of large BLOBs
- Session management problems

Changed
~~~~~~~
- If a namespace/annotation was redefined, will now thrown an exception instead of just a logging a warning
- Update minimum pickle parsing from 0.5.3 to 0.5.4 to reflect changes in parse exceptions

Added
~~~~~
- Ability to drop graph that isn't in graph store from CLI


`0.5.3 <https://github.com/pybel/pybel/compare/v0.5.2...v0.5.3>`_ - 2017-04-19
------------------------------------------------------------------------------
Added
~~~~~
- Lenient parsing mode for unqualified translocations (https://github.com/pybel/pybel/issues/178)

Changed
~~~~~~~
- Check for dead URLs at BEL framework (https://github.com/pybel/pybel/issues/177)
- Don't throw warnings for versions that are in YYYYMMDD format (https://github.com/pybel/pybel/issues/175)
- Include character positions in some exceptions (https://github.com/pybel/pybel/issues/176)
- Update minimum pickle parsing from 0.4.2 to 0.5.3 to reflect the new parse exceptions's names and arguments


`0.5.2 <https://github.com/pybel/pybel/compare/v0.5.1...v0.5.2>`_ - 2017-04-16
------------------------------------------------------------------------------
Fixed
~~~~~
- Ensure existence of namespaces/annotations during graph upload (https://github.com/pybel/pybel/issues/165)

`0.5.1 <https://github.com/pybel/pybel/compare/v0.5.0...v0.5.1>`_ - 2017-04-10
------------------------------------------------------------------------------
Added
~~~~~
- Parsing of labels (https://github.com/pybel/pybel/issues/173)

Fixed
~~~~~
- Parsing of hasComponents lists (https://github.com/pybel/pybel/issues/172)

`0.5.0 <https://github.com/pybel/pybel/compare/v0.4.4...v0.5.0>`_ - 2017-04-07
------------------------------------------------------------------------------
Added
~~~~~
- Debugging on lines starting with #: comments (https://github.com/pybel/pybel/issues/162)
- Added missing relations in pybel constants (https://github.com/pybel/pybel/issues/161)

Changed
~~~~~~~
- Merge definition and graph cache (https://github.com/pybel/pybel/issues/164)
- Warn when not using semantic versioning (https://github.com/pybel/pybel/issues/160)


`0.4.4 <https://github.com/pybel/pybel/compare/v0.4.3...v0.4.4>`_ - 2017-04-03
------------------------------------------------------------------------------
Added
~~~~~
- File paths in definition parsing (https://github.com/pybel/pybel/issues/158)
- Quotes around variant string (https://github.com/pybel/pybel/issues/156)

Changed
~~~~~~~
- Reorganized package to split line parsing from core data structure (https://github.com/pybel/pybel/issues/154)


`0.4.3 <https://github.com/pybel/pybel/compare/v0.4.2...v0.4.3>`_ - 2017-03-21
------------------------------------------------------------------------------
Added
~~~~~
- Documentation for constants (https://github.com/pybel/pybel/issues/146)
- Date validation on parse-time (https://github.com/pybel/pybel/issues/147)

Changed
~~~~~~~
- Externalized strings from modifier parsers
- Move ``pybel.cx.hash_tuple`` to ``pybel.utils.hash_tuple`` (https://github.com/pybel/pybel/issues/144)

Fixed
~~~~~
- Output to CX on CLI crashing (https://github.com/pybel/pybel/issues/152)
- Assignment of graph metadata on reload (https://github.com/pybel/pybel/issues/153)

`0.4.2 <https://github.com/pybel/pybel/compare/v0.4.1...v0.4.2>`_ - 2017-03-16
------------------------------------------------------------------------------
Added
~~~~~
- Node property data model and I/O
- Edge property data model and I/O

Changed
~~~~~~~
- Update version checking to be more lenient. v0.4.2 is now the minimum for reloading a graph

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
