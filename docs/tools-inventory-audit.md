# Lumi Tools Inventory & Biomni Gap Analysis

**Date**: 2026-03-08

---

## A) All Tools/MCPs/Integrations Currently in Lumi

### MCP Servers (13 total, in `src/mcp_servers/`)

| # | MCP Server | Tool Count | External Services |
|---|-----------|------------|-------------------|
| 1 | **genomics** | 9 | Open Targets, Ensembl, GWAS Catalog, gnomAD, ClinVar, VEP, dbSNP, PharmGKB |
| 2 | **protein** | 15 | UniProt, RCSB PDB, AlphaFold DB, InterPro, STRING v12.0 |
| 3 | **protein_design** | 10 | ESM-2 (local), Biopython, AlphaFold DB, NCBI BLAST |
| 4 | **expression** | 7 | GTEx, Human Protein Atlas, CellxGene Census, NCBI GEO, ENCODE |
| 5 | **pathways** | 9 | Reactome, Gene Ontology, KEGG, WikiPathways |
| 6 | **clinical** | 11 | ClinicalTrials.gov, PubMed, ChEMBL, OpenFDA, FDA Labeling, DailyMed |
| 7 | **safety** | 8 | CTD, ToxCast/Tox21, SIDER, IMPC/MGI |
| 8 | **literature** | 9 | Semantic Scholar, bioRxiv/medRxiv, Europe PMC, PubMed |
| 9 | **cheminformatics** | 10 | RDKit (local), PubChem, ZINC |
| 10 | **metabolic** | 11 | COBRApy (local), BiGG Models, KEGG |
| 11 | **biosecurity** | 6 | CDC/USDA Select Agents, NCBI BLAST, InterPro/Pfam, VFDB, BWC |
| 12 | **tamarind** | 12 | Tamarind Bio (AlphaFold2, RFdiffusion, ProteinMPNN, DiffDock, OpenMM) |
| 13 | **biorender** | 16 | AntV MCP Server Chart, BioRender SDK |

**Total MCP tools: ~133**

### Detailed Tool Registry by MCP Server

#### Genomics (9 tools)
- `query_target_disease` → Open Targets GraphQL
- `get_target_info` → Open Targets profile
- `query_gwas_associations` → GWAS Catalog REST
- `query_gene_variants` → gnomAD GraphQL (pLI, LOEUF)
- `query_clinvar_gene` → NCBI ClinVar
- `get_gene_info` → Ensembl REST API
- `get_variant_consequences` → Ensembl VEP REST
- `query_rsid` → NCBI dbSNP
- `query_pharmgkb_gene` → PharmGKB REST

#### Protein & Structure (15 tools)
- `get_protein_info` → UniProt REST
- `search_proteins` → UniProt REST
- `get_protein_sequence` → UniProt REST
- `get_protein_features` → UniProt REST
- `search_structures` → RCSB PDB Search API
- `get_structure_info` → RCSB PDB Data API
- `get_binding_sites` → RCSB PDB
- `get_predicted_structure` → AlphaFold DB API
- `get_pae` → AlphaFold PAE matrix
- `get_protein_domains` → InterPro API
- `search_domains_by_name` → InterPro API
- `get_interactions` → STRING v12.0
- `get_network` → STRING v12.0
- `get_enrichment` → STRING (GO, KEGG, Reactome enrichment)

#### Protein Design / Yami Simulator (10 tools)
- `esm2_score_sequence` → ESM-2 (local, 650M params)
- `esm2_mutant_effect` → ESM-2
- `esm2_embed` → ESM-2
- `calculate_protein_properties` → Biopython ProtParam
- `predict_solubility` → Local heuristic
- `predict_structure_alphafold` → AlphaFold DB / local cache
- `blast_sequence` → NCBI BLAST
- `calculate_cai` → Codon Adaptation Index (local)
- `number_antibody` → ANARCI (Chothia/IMGT/Kabat)
- `predict_developability` → In-house heuristic

#### Expression (7 tools)
- `get_gene_expression` → GTEx Portal + Human Protein Atlas
- `get_protein_expression` → Human Protein Atlas
- `get_pathology_data` → HPA tumour pathology
- `query_gene_expression_single_cell` → CellxGene Census
- `search_geo_datasets` → NCBI GEO
- `get_eqtls` → GTEx eQTL
- `query_encode_experiments` → ENCODE portal

#### Pathways & Ontology (9 tools)
- `get_pathways_for_gene` → Reactome
- `get_pathway_details` → Reactome
- `pathway_enrichment` → Reactome Analysis Service
- `get_go_annotations` → Gene Ontology API
- `go_enrichment` → Gene Ontology
- `get_kegg_pathways` → KEGG REST
- `get_pathway_genes` → KEGG REST
- `get_pathway_info` → WikiPathways
- `search_pathways` → WikiPathways

#### Clinical & Drug (11 tools)
- `search_trials` → ClinicalTrials.gov API v2
- `get_trial_details` → ClinicalTrials.gov
- `search_trials_by_target` → ClinicalTrials.gov
- `search_pubmed` → PubMed/MEDLINE via NCBI E-utilities
- `get_article_details` → PubMed
- `get_target_compounds` → ChEMBL API
- `get_compound_info` → ChEMBL
- `get_drug_info` → ChEMBL / FDA
- `search_adverse_events` → OpenFDA FAERS
- `get_drug_label` → FDA Drug Labeling / DailyMed
- `get_drug_label_sections` → DailyMed

#### Safety & Toxicology (8 tools)
- `query_gene_chemical_interactions` → CTD
- `query_gene_disease_associations` → CTD
- `query_chemical_diseases` → CTD
- `query_toxicity_assays` → ToxCast/Tox21 (EPA)
- `get_side_effects` → SIDER
- `get_drug_indications` → SIDER
- `get_knockout_phenotypes` → IMPC/MGI
- `get_safety_summary` → Aggregated

#### Literature (9 tools)
- `search_papers` → Semantic Scholar Graph API
- `get_paper_details` → Semantic Scholar
- `get_citations` → Semantic Scholar
- `get_references` → Semantic Scholar
- `get_author_papers` → Semantic Scholar
- `search_preprints` → bioRxiv/medRxiv API
- `get_preprint_details` → bioRxiv/medRxiv
- `search_fulltext` → Europe PMC REST
- `get_article_citations` → Europe PMC

#### Cheminformatics (10 tools)
- `calculate_descriptors` → RDKit (local)
- `check_drug_likeness` → RDKit (Lipinski, Veber, Ghose, Egan)
- `compute_fingerprint` → RDKit (Morgan fingerprints)
- `compute_similarity` → RDKit (Tanimoto)
- `substructure_search` → RDKit
- `convert_molecule` → RDKit (SMILES/InChI/MOL)
- `search_compound` → PubChem PUG REST
- `get_compound_bioactivity` → PubChem
- `get_compound_safety` → PubChem
- `search_zinc` → ZINC15

#### Metabolic / Virtual Cell (11 tools)
- `run_fba` → COBRApy
- `run_fva` → COBRApy
- `simulate_gene_knockout` → COBRApy
- `simulate_reaction_knockout` → COBRApy
- `add_heterologous_pathway` → COBRApy
- `list_available_models` → BiGG Models API
- `get_model_info` → BiGG Models
- `get_model_reactions` → BiGG Models
- `optimize_codons` → Local (E. coli, CHO tables)
- `predict_expression_level` → Local heuristic

#### Biosecurity (6 tools)
- `screen_against_select_agents` → CDC/USDA + NCBI BLAST
- `blast_protein` → NCBI BLAST (HTTP polling with RID)
- `check_select_agent_list` → CDC/USDA Select Agent & Toxin List (offline)
- `scan_toxin_domains` → InterPro/Pfam
- `screen_virulence_factors` → VFDB (keyword heuristic)
- `check_bwc_compliance` → BWC/Australia Group (offline)

#### Tamarind Bio (12 tools)
- `tamarind_list_tools` → Tamarind Bio REST API
- `tamarind_submit_job` → Tamarind (AlphaFold, RFdiffusion, ProteinMPNN, DiffDock, OpenMM)
- `tamarind_submit_batch` → Tamarind
- `tamarind_get_jobs` → Tamarind
- `tamarind_poll_until_complete` → Tamarind (exponential backoff)
- `tamarind_get_result` → Tamarind (S3 presigned URLs)
- `tamarind_upload_file` → Tamarind
- `tamarind_list_files` → Tamarind
- `tamarind_submit_pipeline` → Tamarind
- `tamarind_run_pipeline` → Tamarind
- `tamarind_delete_job` → Tamarind
- `tamarind_get_finetuned_models` → Tamarind

#### BioRender / Figure Generation (16 tools)
- `generate_volcano_plot` → AntV MCP Server Chart
- `generate_expression_heatmap` → AntV
- `generate_pathway_diagram` → AntV
- `generate_target_comparison_radar` → AntV
- `generate_gene_expression_bar` → AntV
- `generate_drug_target_sankey` → AntV
- `generate_pipeline_flow` → AntV
- `generate_moa_diagram` → AntV
- `generate_literature_wordcloud` → AntV
- `generate_confidence_distribution` → AntV
- `generate_clinical_timeline` → AntV
- `generate_category_pie` → AntV
- `generate_venn_diagram` → AntV
- `search_biorender_icons` → BioRender
- `search_biorender_templates` → BioRender
- `download_figure` → Local export

---

### Specialist Agents (17 total, in `src/agents/`)

| Agent | Division | # Tools | Primary External Services |
|-------|----------|---------|--------------------------|
| Statistical Genetics | Target ID | 9 | Open Targets, Ensembl, GWAS, gnomAD, ClinVar, PharmGKB |
| Functional Genomics | Target ID | 5 | Open Targets, GTEx, HPA, CellxGene |
| Single Cell Atlas | Target ID | 5 | CellxGene, GTEx, HPA, GEO |
| Bio Pathways | Target Safety | 7 | STRING, InterPro, Reactome, GO |
| FDA Safety | Target Safety | 5 | OpenFDA, SIDER, IMPC/MGI, CTD |
| Toxicogenomics | Target Safety | 4 | CTD, ToxCast, GTEx, IMPC/MGI |
| Target Biologist | Modality | 7 | UniProt, AlphaFold, PDB, InterPro |
| Pharmacologist | Modality | 6 | ChEMBL, PubMed, RDKit |
| Protein Intelligence | Mol Design | 10 | ESM-2, Biopython, AlphaFold, NCBI BLAST, Tamarind |
| Structure Design | Mol Design | 9 | RCSB PDB, AlphaFold, ESM-2, Tamarind |
| Antibody Engineer | Mol Design | 6 | ANARCI, ESM-2, NCBI BLAST, Biopython |
| Lead Optimization | Mol Design | 6 | ESM-2, RDKit, Biopython |
| Developability | Mol Design | 5 | Biopython, ESM-2 |
| Assay Design | Experimental | 3 | PubMed, Semantic Scholar, ChEMBL |
| Literature Synthesis | CompBio | 6 | Semantic Scholar, PubMed, bioRxiv/medRxiv, Europe PMC |
| Clinical Trialist | Clinical | 4 | ClinicalTrials.gov, PubMed, Semantic Scholar |
| Dual-Use Screening | Biosecurity | 5 | CDC/USDA, VFDB, InterPro, NCBI BLAST, BWC |

### Domain Engines (3)

| Engine | Technologies |
|--------|-------------|
| **Biosecurity Engine** | 5-screen pipeline (select agents, toxin domains, virulence factors, GoF risk, BWC compliance) |
| **Yami Simulator** | ESM-2, AlphaFold DB, NCBI BLAST, Biopython ProtParam |
| **Virtual Cell Simulator** | COBRApy, BiGG Models, codon optimization |

### Local ML Models & Libraries

- **ESM-2** — 650M parameter protein language model (Meta `esm2_t33_650M_UR50D`)
- **RDKit** — Cheminformatics (descriptors, fingerprints, drug-likeness, similarity)
- **COBRApy** — Constraint-based metabolic modeling (FBA, FVA, gene knockouts)
- **Biopython** — Sequence analysis, ProtParam biophysical properties

### Code Execution Sandbox

Python subprocess sandbox with approved packages:
- Scientific: numpy, pandas, scipy, statsmodels, scikit-learn, xgboost, lightgbm, torch, transformers
- Bioinformatics: Biopython, scanpy, anndata, scvi, biotite, prody, cobra
- Networks: networkx, igraph
- Cheminformatics: RDKit, datamol
- Protein models: ESM (fair-esm)
- Visualization: matplotlib, seaborn, plotly

### All External APIs/Databases (40+)

**No auth required:** Open Targets, GWAS Catalog, Ensembl, VEP, gnomAD, ClinVar, dbSNP, PharmGKB, GTEx, Human Protein Atlas, CellxGene, NCBI GEO, ENCODE, UniProt, RCSB PDB, AlphaFold DB, InterPro, STRING, Semantic Scholar, bioRxiv/medRxiv, Europe PMC, ClinicalTrials.gov, ChEMBL, OpenFDA, DailyMed, CTD, ToxCast/Tox21, SIDER, IMPC/MGI, Reactome, Gene Ontology, KEGG, WikiPathways, PubChem, ZINC15, BiGG Models, NCBI BLAST, VFDB

**Optional API keys:** `NCBI_API_KEY`, `SEMANTIC_SCHOLAR_API_KEY`, `TAMARIND_API_KEY`

### Conditional Dependencies

| Component | Required | Status |
|-----------|----------|--------|
| COBRApy | Metabolic server | Optional — graceful fallback |
| Tamarind API key | Tamarind server | Optional — requires `TAMARIND_API_KEY` |
| Node.js + npx | BioRender server | Optional — requires AntV chart server |
| RDKit | Cheminformatics server | Optional — graceful fallback |

---

## B) Biomni Tools NOT Yet Integrated into Lumi

[Biomni](https://github.com/snap-stanford/Biomni) is Stanford's general-purpose biomedical AI agent integrating **150 specialized tools, 105 software packages, and 59 databases** across 22 domain modules.

### Missing Database API Integrations

From Biomni's 33 `schema_db` APIs, these have **no equivalent** in Lumi:

| # | Database | What It Does | Priority |
|---|----------|-------------|----------|
| 1 | **cBioPortal** | Cancer genomics (mutations, CNVs, expression across tumours) | High |
| 2 | **JASPAR** | Transcription factor binding profiles | Medium |
| 3 | **Monarch Initiative** | Disease-gene-phenotype integration, rare disease | High |
| 4 | **MPD** (Mouse Phenome DB) | Mouse strain phenotypes | Medium |
| 5 | **PRIDE** | Proteomics data repository | Medium |
| 6 | **QuickGO** | GO annotation browser (richer than Lumi's basic GO) | Low (partial overlap) |
| 7 | **UCSC Genome Browser** | Genome annotations, tracks, sequence retrieval | High |
| 8 | **UniChem** | Cross-reference chemical identifiers across databases | Medium |
| 9 | **Paleobiology DB** | Fossil records, evolutionary biology | Low |
| 10 | **WoRMS** | World Register of Marine Species | Low |
| 11 | **IUCN** | Conservation status of species | Low (commercial license) |
| 12 | **REMAP** | Regulatory regions, ChIP-seq peaks atlas | Medium (commercial license) |

### Missing Data Lake Datasets

Biomni ships a ~11GB local data lake with ~77 datasets. Key ones absent from Lumi:

| Dataset | What It Provides |
|---------|-----------------|
| **COSMIC** | Somatic mutations in cancer (requires commercial license) |
| **BindingDB** | Binding affinity data |
| **BioGRID** | Protein-protein interactions |
| **MSigDB** | Hallmark gene sets (requires commercial license) |
| **DisGeNET** | Gene-disease associations |
| **DDInter** | Drug-drug interactions |
| **DepMap** | Cancer dependency map |
| **Genebass** | Exome-based associations |
| **HPO** (Human Phenotype Ontology) | Standardized phenotype terms |
| **McPAS-TCR** | T-cell receptor-antigen associations |
| **miRDB** / **miRTarBase** | microRNA target predictions |
| **MouseMine** | Mouse genetics data |
| **P-HIPSTER** | Protein-protein interactions |
| **TXGNN** | Therapeutic gene network |
| **Broad Repurposing Hub** | Drug repurposing screening data |
| **Enamine** | Commercial compound screening library (proprietary) |

### Missing Domain Tool Modules

Biomni organizes tools into 22 domain `.py` modules. These entire categories are **absent** from Lumi:

| # | Biomni Module | Coverage | Lumi Status |
|---|---------------|----------|-------------|
| 1 | **biochemistry.py** | Enzyme kinetics, metabolite analysis, protein purification | **Missing** |
| 2 | **bioengineering.py** | Genetic circuit design, CRISPR guide design, plasmid construction | **Missing** |
| 3 | **bioimaging.py** | Microscopy image analysis, cell segmentation, fluorescence | **Missing** |
| 4 | **biophysics.py** | Molecular dynamics, thermodynamics, binding energy calculations | **Missing** |
| 5 | **cancer_biology.py** | Tumour mutation burden, driver analysis, clonality, neoantigens | **Missing** |
| 6 | **cell_biology.py** | Cell cycle analysis, organelle detection, proliferation assays | **Missing** |
| 7 | **genetics.py** | GWAS (PLINK), heritability, linkage disequilibrium, PRS | **Partial** |
| 8 | **glycoengineering.py** | Glycan structure analysis, glycoprotein engineering | **Missing** |
| 9 | **immunology.py** | Immune cell typing, TCR/BCR analysis, cytokine profiling | **Missing** |
| 10 | **lab_automation.py** | Liquid handler protocols, plate layout, robotics | **Missing** |
| 11 | **microbiology.py** | Microbiome analysis, AMR gene detection, phylogenetics | **Missing** |
| 12 | **molecular_biology.py** | Primer design, cloning strategy, restriction analysis, qPCR | **Missing** |
| 13 | **pathology.py** | Histopathology image analysis, tissue classification | **Missing** |
| 14 | **physiology.py** | Physiological modeling, organ system simulation | **Missing** |
| 15 | **synthetic_biology.py** | Part registry, genetic circuit simulation | **Partial** (codon opt exists) |
| 16 | **systems_biology.py** | Network inference, ODE modeling | **Partial** (COBRApy exists) |
| 17 | **protocols.py** | Wet-lab protocol generation and retrieval | **Missing** |

### Missing CLI Bioinformatics Tools

| Tool | Purpose |
|------|---------|
| **PLINK 2.0** | GWAS analysis, population genetics |
| **IQ-TREE** | Maximum-likelihood phylogenetics |
| **GCTA** | Genome-wide complex trait analysis |
| **BWA** | Short-read sequence alignment |
| **FastTree** | Approximate phylogenetic trees |
| **MUSCLE** | Multiple sequence alignment |
| **HOMER** | Motif discovery, ChIP-seq analysis |
| **samtools** | SAM/BAM file manipulation |
| **LUMPY** | Structural variant detection |
| **MACS2** | ChIP-seq peak calling |

### Missing: R Runtime

Biomni has full R code execution via `run_r_code()`. Lumi has **no R runtime**, excluding the entire Bioconductor ecosystem (DESeq2, edgeR, Seurat, limma, clusterProfiler, etc.).

---

## Summary Comparison

| Category | Lumi | Biomni | Gap |
|----------|------|--------|-----|
| MCP Servers / Domain Modules | 13 | 22 | ~9 missing domains |
| Database API Integrations | ~25 | 33 (schema_db) + data lake | ~12 missing APIs |
| Registered Tools | ~133 | ~150 | Similar count, different coverage |
| Software Packages | ~30 | 105 | ~75 missing (CLI tools + R ecosystem) |
| Data Lake Datasets | 0 (all API) | ~77 local (~11GB) | Entire concept missing |
| CLI Bioinformatics Tools | 0 | 10+ | All missing |
| R Runtime | No | Yes | Missing |

### Biggest Gaps (by impact)

1. **Cancer biology** — cBioPortal, COSMIC, DepMap (oncology is a primary drug discovery domain)
2. **CRISPR/Bioengineering** — guide design, circuit simulation, plasmid construction
3. **Immunology** — TCR/BCR analysis, immune cell typing (critical for immunotherapy)
4. **Imaging/Pathology** — histopathology, microscopy analysis
5. **CLI bioinformatics** — PLINK, BWA, samtools, MACS2 (raw data processing)
6. **Local data lake** — pre-processed datasets for faster queries
7. **Molecular biology** — primer design, cloning strategies, qPCR design
8. **R runtime** — Bioconductor ecosystem access
