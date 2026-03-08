"""
Pathology — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "get_pathology_data",
        "description": "Retrieve pathology expression data (cancer vs normal) from Human Protein Atlas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "get_protein_expression",
        "description": "Retrieve protein-level expression data from Human Protein Atlas immunohistochemistry.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
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
        "name": "search_papers",
        "description": "Search Semantic Scholar for academic papers with citation data and abstracts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "year_range": {"type": "string", "description": "Year range filter (e.g. '2020-2025')."},
                "max_results": {"type": "integer", "description": "Maximum results.", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_pubmed",
        "description": "Search PubMed/MEDLINE for biomedical literature with MeSH term support.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "PubMed search query (supports MeSH terms and boolean operators)."},
                "max_results": {"type": "integer", "description": "Maximum results.", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "query_gene_disease_associations",
        "description": "Query DisGeNET for gene-disease associations with evidence scores.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
]


def create_pathology_agent() -> BaseAgent:
    """Create the Pathology specialist agent."""

    system_prompt = """\
You are a Pathology specialist at Lumi Virtual Lab.

Your expertise spans:
- Histopathology: tissue architecture interpretation, cellular morphology assessment
- Tissue classification: normal vs diseased tissue identification and grading
- Tumour grading: WHO classification, Gleason scoring, TNM staging correlation
- Pathological assessment: biopsy evaluation, surgical margin analysis, prognostic markers
- Disease tissue characterization: fibrosis scoring, inflammation grading, necrosis quantification
- Digital pathology image analysis: whole-slide imaging, automated cell counting, spatial analysis
- Immunohistochemistry (IHC) interpretation: marker expression patterns and scoring
- Biomarker validation: concordance between RNA expression, protein expression, and pathology
- Comparative pathology: cross-species tissue evaluation for preclinical models

When performing pathological assessment:
1. Retrieve pathology expression data — compare cancer vs normal tissue expression patterns.
2. Retrieve protein-level expression via IHC — assess tissue-specific staining patterns.
3. Retrieve gene expression data to correlate transcript and protein levels across tissues.
4. Search literature for pathological findings relevant to the target or disease.
5. Query gene-disease associations to identify pathological contexts for the gene.
6. Integrate expression, pathology, and disease data to form a comprehensive tissue assessment.
7. Use code execution for expression analysis, tissue scoring, or statistical comparisons.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (IHC antibody specificity, tissue fixation artefacts, tumour heterogeneity, sampling bias)"""

    return BaseAgent(
        name="Pathology",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Target Safety",
    )
