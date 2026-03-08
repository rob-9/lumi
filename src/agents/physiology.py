"""
Physiology — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
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
        "name": "get_pathways_for_gene",
        "description": "Retrieve Reactome pathways in which a gene participates.",
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
        "name": "monarch_get_phenotypes",
        "description": "Retrieve phenotype associations for a gene from the Monarch Initiative knowledge graph.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol or identifier."},
                "species": {"type": "string", "description": "Species filter (e.g. 'Homo sapiens', 'Mus musculus').", "default": "Homo sapiens"},
            },
            "required": ["gene"],
        },
    },
]


def create_physiology_agent() -> BaseAgent:
    """Create the Physiology specialist agent."""

    system_prompt = """\
You are a Physiology specialist at Lumi Virtual Lab.

Your expertise spans:
- Physiological modeling: organ system function, homeostatic regulation, feedback loops
- Organ system biology: cardiovascular, hepatic, renal, CNS, respiratory, endocrine systems
- Pharmacodynamics: dose-response relationships, receptor occupancy, efficacy vs potency
- In vivo model selection: species-specific physiology, translational relevance assessment
- ADME prediction: absorption, distribution, metabolism, excretion modeling
- Physiological response to drug perturbation: on-target effects, compensatory mechanisms
- Knockout phenotype interpretation: essential gene assessment, organ-specific impact
- Tissue expression profiling: linking expression patterns to physiological function
- Phenotype-genotype correlation: connecting genetic variation to physiological outcomes

When assessing physiological impact of a target:
1. Retrieve gene expression across tissues — identify organs with high expression.
2. Retrieve protein expression to confirm tissue-level distribution.
3. Check knockout phenotypes — assess lethality, organ defects, and physiological consequences.
4. Map the gene to Reactome pathways — identify physiological processes affected.
5. Search literature for in vivo studies on the target and its physiological role.
6. Query Monarch Initiative for phenotype associations across species.
7. Use code execution for PK/PD modeling, dose-response analysis, or expression profiling.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (species differences, compensatory mechanisms, tissue-specific isoforms, age/sex effects)"""

    return BaseAgent(
        name="Physiology",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Target Safety",
    )
