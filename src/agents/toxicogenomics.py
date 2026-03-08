"""
Toxicogenomics — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "query_gene_chemical_interactions",
        "description": "Query CTD (Comparative Toxicogenomics Database) for gene-chemical interactions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "query_toxicity_assays",
        "description": "Query ToxCast/Tox21 for in-vitro toxicity assay results for a chemical.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chemical": {"type": "string", "description": "Chemical name or CAS number."},
            },
            "required": ["chemical"],
        },
    },
    {
        "name": "get_gene_expression",
        "description": "Retrieve tissue-level gene expression data from GTEx and Human Protein Atlas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "get_knockout_phenotypes",
        "description": "Retrieve mouse knockout phenotypes from IMPC/MGI for a gene.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
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
    {
        "name": "disgenet_variant_diseases",
        "description": "Get disease associations for a variant from DisGeNET.",
        "input_schema": {
            "type": "object",
            "properties": {
                "variant_id": {"type": "string", "description": "dbSNP rsID (e.g. rs1234)."},
                "max_results": {"type": "integer", "description": "Maximum associations to return."},
            },
            "required": ["variant_id"],
        },
    },
    {
        "name": "query_chemical_diseases",
        "description": "Query CTD for chemical-disease associations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chemical": {"type": "string", "description": "Chemical name."},
            },
            "required": ["chemical"],
        },
    },
    {
        "name": "disgenet_disease_genes",
        "description": "Get gene associations for a disease from DisGeNET.",
        "input_schema": {
            "type": "object",
            "properties": {
                "disease_id": {"type": "string", "description": "Disease ID."},
                "min_score": {"type": "number", "description": "Minimum GDA score (0-1)."},
                "max_results": {"type": "integer", "description": "Maximum results to return."},
            },
            "required": ["disease_id"],
        },
    },
    {
        "name": "disgenet_search_diseases",
        "description": "Search DisGeNET for diseases by keyword.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword."},
                "max_results": {"type": "integer", "description": "Maximum results to return."},
            },
            "required": ["query"],
        },
    },
]


def create_toxicogenomics_agent() -> BaseAgent:
    """Create the Toxicogenomics specialist agent."""

    system_prompt = """\
You are a Toxicogenomics specialist at Lumi Virtual Lab.

Your expertise spans:
- Toxicogenomic profiling: gene expression changes induced by chemical exposure
- Comparative Toxicogenomics Database (CTD) mining for gene-chemical-disease links
- ToxCast/Tox21 high-throughput screening data interpretation
- Adverse Outcome Pathway (AOP) framework for mechanistic toxicology
- Organ-specific toxicity gene signatures (liver, kidney, heart, CNS)
- Dose-response modelling and benchmark dose estimation
- In-vitro to in-vivo extrapolation (IVIVE) for toxicity prediction
- Mouse knockout phenotype interpretation for essential gene assessment
- Reactive metabolite prediction and bioactivation risk

When assessing toxicogenomic risk for a target:
1. Query CTD for gene-chemical interactions — identify chemicals that modulate the gene.
2. For key chemicals, query ToxCast/Tox21 assay results for toxicity endpoints.
3. Retrieve gene expression to identify tissues with high expression (exposure organs at risk).
4. Check knockout phenotypes for lethality, organ defects, or immune dysfunction.
5. Map findings to Adverse Outcome Pathways where possible.
6. Use code execution for dose-response modelling or expression analysis.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (species extrapolation, dose relevance, in-vitro vs in-vivo discrepancies)"""

    return BaseAgent(
        name="Toxicogenomics",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Target Safety",
    )
