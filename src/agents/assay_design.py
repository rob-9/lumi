"""
Assay Design — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "search_pubmed",
        "description": "Search PubMed for relevant biomedical literature including assay protocols.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "PubMed search query."},
                "max_results": {"type": "integer", "description": "Maximum results.", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_papers",
        "description": "Search Semantic Scholar for academic papers with citation data.",
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
        "name": "get_target_compounds",
        "description": "Retrieve known compounds/drugs targeting a protein from ChEMBL, including assay types used.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_name": {"type": "string", "description": "Target name or gene symbol."},
            },
            "required": ["target_name"],
        },
    },
    {
        "name": "get_article_details",
        "description": "Get full metadata for a PubMed article by PMID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pmid": {"type": "string", "description": "PubMed article ID."},
            },
            "required": ["pmid"],
        },
    },
    {
        "name": "search_preprints",
        "description": "Search bioRxiv/medRxiv for preprints.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "server": {"type": "string", "description": "Preprint server (bioRxiv or medRxiv)."},
                "max_results": {"type": "integer", "description": "Maximum results."},
            },
            "required": ["query"],
        },
    },
]


def create_assay_design_agent() -> BaseAgent:
    """Create the Assay Design specialist agent."""

    system_prompt = """\
You are an Assay Design and Experimental Validation specialist at Lumi Virtual Lab.

Your expertise spans:
- Biochemical assay design: enzymatic, binding (SPR, ITC, FP), reporter gene
- Cell-based assay design: proliferation, viability, signalling pathway reporters
- High-throughput screening (HTS) cascade design and hit triaging strategy
- Biophysical characterization: SPR kinetics, DSF thermal shift, SEC-MALS, DLS
- In-vivo model selection: xenograft, syngeneic, GEM, PDX models
- Antibody characterization assays: ELISA, flow cytometry, BLI, cell killing (ADCC/CDC)
- Assay development: Z-factor optimization, DMSO tolerance, counter-screens
- Dose-response curve fitting and IC50/EC50 determination methodology
- Selectivity profiling: kinase panels, safety pharmacology, off-target screening
- Translational biomarker strategy and PD marker selection
- Experimental controls, statistical power, and reproducibility best practices

When designing experiments:
1. Search PubMed for published assay protocols for the target or pathway of interest.
2. Search Semantic Scholar for recent methodological papers and assay innovations.
3. Query ChEMBL for assay types historically used to characterize this target.
4. Design a tiered screening cascade: primary screen -> confirmation -> selectivity -> cellular.
5. Specify positive/negative controls, readouts, expected dynamic range, and acceptance criteria.
6. Use code execution for power calculations, plate layout design, or data analysis planning.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (assay artifacts, cell-line specificity, translational relevance of models)"""

    return BaseAgent(
        name="Assay Design",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Experimental",
    )
