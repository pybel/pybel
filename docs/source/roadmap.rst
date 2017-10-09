Roadmap
=======

This project road map documents not only the PyBEL repository, but the PyBEL Tools and PyBEL Web repositories
as well as the Bio2BEL project.

PyBEL
-----
- Performance improvements
    - Parallelization of parsing
    - On-the-fly validation with OLS or MIRIAM

Bio2BEL
-------
- Generation of new namespaces, equivalencies, and hierarchical knowledge (isA and partOf relations)
    - FlyBase
    - InterPro
    - UniProt
    - ChEBML
    - Human Phenotype Ontology
    - Uber Anatomy Ontology
    - HGNC Gene Families
    - Enyzme Classification
- Integration of knowledge sources
    - ChEMBL
    - Comparative Toxicogenomics Database
    - BRENDA
    - MetaCyc
    - Protein complex definitions
- Integration of analytical pipelines
    - LD Block Analysis
    - Gene Co-expression Analysis
    - Differential Gene Expression Analysis

PyBEL Tools
-----------
- Biological Grammar
    - Network motif identification
    - Stability analysis
    - Prior knowledge comparision
        - Molecular activity annotation
        - SNP Impact
- Implementation of standard BEL Algorithms
    - RCR
    - NPA
    - SST
- Development of new algorithms
    - Heat diffusion algorithms
    - AETIONOMY Workflow 1 (Drug Repurposing)
    - Cart Before the Horse
- Metapath analysis
- Reasoning and inference rules
- Subgraph Expansion application in NeuroMMSigDB
- Chemical Enrichment in NeuroMMSigDB

PyBEL Web
---------
- Integration with BELIEF
- Integration with NeuroMMSigDB
- Import and export from NDEx
