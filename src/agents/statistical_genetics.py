"""
Statistical Genetics — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "query_target_disease",
        "description": "Query Open Targets for associations between a gene and a disease.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_gene": {"type": "string", "description": "HGNC gene symbol (e.g. 'BRCA1')."},
                "disease_efo_id": {"type": "string", "description": "EFO disease ID (e.g. 'EFO_0000305')."},
            },
            "required": ["target_gene", "disease_efo_id"],
        },
    },
    {
        "name": "get_target_info",
        "description": "Retrieve gene/target metadata from Ensembl via Open Targets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ensembl_gene_id": {"type": "string", "description": "Ensembl gene ID (e.g. 'ENSG00000141510')."},
            },
            "required": ["ensembl_gene_id"],
        },
    },
    {
        "name": "query_gwas_associations",
        "description": "Query the GWAS Catalog for trait associations of a gene.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "query_gene_variants",
        "description": "Retrieve gnomAD constraint metrics and variant data for a gene.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "query_clinvar_gene",
        "description": "Query ClinVar for pathogenic and likely-pathogenic variants in a gene.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "get_gene_info",
        "description": "Get comprehensive gene information from Ensembl REST API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene_symbol": {"type": "string", "description": "HGNC gene symbol."},
            },
            "required": ["gene_symbol"],
        },
    },
    {
        "name": "get_variant_consequences",
        "description": "Get VEP-predicted consequences for a genomic variant.",
        "input_schema": {
            "type": "object",
            "properties": {
                "variant": {"type": "string", "description": "Variant in HGVS or rsID format."},
            },
            "required": ["variant"],
        },
    },
    {
        "name": "query_rsid",
        "description": "Look up a dbSNP rsID and return allele frequencies and annotations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "rsid": {"type": "string", "description": "dbSNP rsID (e.g. 'rs1234')."},
            },
            "required": ["rsid"],
        },
    },
    {
        "name": "query_pharmgkb_gene",
        "description": "Query PharmGKB for pharmacogenomic annotations of a gene.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "genebass_gene_associations",
        "description": "Get exome-based phenotype associations for a gene from Genebass (UK Biobank).",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene_symbol": {"type": "string", "description": "Gene symbol (e.g. PCSK9, APOB)."},
                "p_threshold": {"type": "number", "description": "P-value threshold for significance."},
            },
            "required": ["gene_symbol"],
        },
    },
    {
        "name": "disgenet_gene_diseases",
        "description": "Get disease associations for a gene from DisGeNET with GDA scores.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene_symbol": {"type": "string", "description": "Gene symbol."},
                "min_score": {"type": "number", "description": "Minimum GDA score (0-1)."},
            },
            "required": ["gene_symbol"],
        },
    },
]


def create_statistical_genetics_agent() -> BaseAgent:
    """Create the Statistical Genetics specialist agent."""

    system_prompt = """\
You are a Statistical Genetics specialist at Lumi Virtual Lab.

Your expertise spans:
- Genome-wide association studies (GWAS) interpretation and meta-analysis
- Mendelian randomization and causal inference from genetic instruments
- Fine-mapping, credible set analysis, and colocalization (coloc, eCAVIAR)
- Population genetics: allele frequency stratification, Fst, admixture
- Polygenic risk scores (PRS) construction and cross-ancestry portability
- Gene-gene epistasis and gene-environment interaction modelling
- Constraint metrics (pLI, LOEUF, missense Z) and their clinical interpretation

When analyzing a target gene:
1. Query GWAS Catalog for genome-wide significant trait associations and effect sizes.
2. Check gnomAD for constraint metrics (pLI, LOEUF, missense Z-score) — high constraint
   suggests the gene is intolerant to loss-of-function and may have safety liabilities.
3. Query ClinVar for pathogenic / likely-pathogenic variants and their phenotypes.
4. Assess Ensembl gene metadata, transcript isoforms, and VEP consequences.
5. Check PharmGKB for pharmacogenomic relevance (drug-gene interactions, dosing guidelines).
6. Use code execution for LD-based calculations, odds-ratio conversions, or meta-analysis.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats and alternative explanations (ancestry bias, winner's curse, LD confounding)"""

    return BaseAgent(
        name="Statistical Genetics",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Target Identification",
    )
