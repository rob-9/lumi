"""
Cancer Biology — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "query_cbioportal_mutations",
        "description": "Query cBioPortal for somatic mutations in a gene across cancer studies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "HGNC gene symbol (e.g. 'TP53')."},
                "study_id": {"type": "string", "description": "cBioPortal study ID (e.g. 'tcga_brca_pan_can_atlas_2018')."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "get_cbioportal_copy_number",
        "description": "Retrieve copy-number alteration data for a gene from cBioPortal.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "HGNC gene symbol."},
                "study_id": {"type": "string", "description": "cBioPortal study ID."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "get_cbioportal_expression",
        "description": "Retrieve mRNA expression data for a gene from cBioPortal.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "HGNC gene symbol."},
                "study_id": {"type": "string", "description": "cBioPortal study ID."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "get_cbioportal_gene_summary",
        "description": "Get a summary of mutation frequency and alteration types for a gene across cancer studies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "HGNC gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "search_papers",
        "description": "Search scientific literature for papers matching a query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string."},
                "max_results": {"type": "integer", "description": "Maximum number of results to return."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_pubmed",
        "description": "Search PubMed for biomedical literature matching a query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "PubMed search query."},
                "max_results": {"type": "integer", "description": "Maximum number of results to return."},
            },
            "required": ["query"],
        },
    },
]


def create_cancer_biology_agent() -> BaseAgent:
    """Create the Cancer Biology specialist agent."""

    system_prompt = """\
You are a Cancer Biology specialist at Lumi Virtual Lab.

Your expertise spans:
- Tumour genomics and somatic mutation analysis across cancer types
- Driver mutation identification using recurrence, functional impact, and hotspot analysis
- Tumour mutation burden (TMB) estimation and microsatellite instability (MSI) assessment
- Clonality analysis, tumour heterogeneity, and clonal evolution modelling
- Neoantigen prediction and immunopeptidome analysis for immunotherapy
- Cancer dependency mapping (DepMap) and synthetic lethality identification
- Copy-number alteration interpretation (amplifications, deletions, LOH)
- Oncogene and tumour suppressor pathway analysis (RTK/RAS/MAPK, PI3K/AKT/mTOR, p53, Rb)

When analyzing a cancer-related target:
1. Query cBioPortal for somatic mutation frequency, hotspots, and alteration types.
2. Check copy-number alterations and mRNA expression across relevant cancer cohorts.
3. Assess gene summary across pan-cancer studies for alteration prevalence.
4. Search literature for driver status, therapeutic relevance, and resistance mechanisms.
5. Evaluate TMB context, clonality, and neoantigen potential where applicable.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (sample bias, cohort composition, variant calling pipeline differences)"""

    return BaseAgent(
        name="Cancer Biology",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Immunology & Cancer Biology",
    )
