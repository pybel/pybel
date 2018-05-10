Roadmap
=======
This project road map documents not only the PyBEL repository, but the PyBEL Tools and BEL Commons repositories
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
    - InterPro (Done)
    - UniProt (Done)
    - Human Phenotype Ontology
    - Uber Anatomy Ontology
    - HGNC Gene Families (Done)
    - Enyzme Classification (Done)
- Integration of knowledge sources
    - ChEMBL
    - Comparative Toxicogenomics Database (Done)
    - BRENDA
    - MetaCyc
    - Protein complex definitions

Data2BEL
--------
Integration of analytical pipelines to convert data to BEL

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
    - Cart Before the Horse
- Metapath analysis
- Reasoning and inference rules
- Subgraph Expansion application in NeuroMMSigDB
- Chemical Enrichment in NeuroMMSigDB

BEL Commons
-----------
- Integration with BELIEF
- Integration with NeuroMMSigDB (Done)
- Import and export from NDEx
