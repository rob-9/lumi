"""
Clinical Trialist — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "search_trials",
        "description": "Search ClinicalTrials.gov for clinical trials matching criteria.",
        "input_schema": {
            "type": "object",
            "properties": {
                "condition": {"type": "string", "description": "Disease or condition."},
                "intervention": {"type": "string", "description": "Drug, biologic, or intervention name."},
                "status": {"type": "string", "description": "Trial status filter (e.g. 'RECRUITING', 'COMPLETED', 'ACTIVE_NOT_RECRUITING')."},
                "max_results": {"type": "integer", "description": "Maximum results.", "default": 20},
            },
            "required": [],
        },
    },
    {
        "name": "get_trial_details",
        "description": "Get detailed information about a specific clinical trial from ClinicalTrials.gov.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nct_id": {"type": "string", "description": "ClinicalTrials.gov NCT identifier."},
            },
            "required": ["nct_id"],
        },
    },
    {
        "name": "search_pubmed",
        "description": "Search PubMed for relevant biomedical literature.",
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
        "name": "search_trials_by_target",
        "description": "Search ClinicalTrials.gov for trials targeting a specific protein.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target protein name."},
                "status": {"type": "string", "description": "Trial status filter."},
                "max_results": {"type": "integer", "description": "Maximum number of results to return."},
            },
            "required": ["target"],
        },
    },
    {
        "name": "get_article_details",
        "description": "Get full metadata for a PubMed article by PMID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pmid": {"type": "string", "description": "PubMed ID."},
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
                "server": {"type": "string", "description": "Preprint server: 'biorxiv' or 'medrxiv'."},
                "max_results": {"type": "integer", "description": "Maximum number of results to return."},
            },
            "required": ["query"],
        },
    },
]


def create_clinical_trialist_agent() -> BaseAgent:
    """Create the Clinical Trialist specialist agent."""

    system_prompt = """\
You are a Clinical Trialist specialist at Lumi Virtual Lab.

Your expertise spans:
- Clinical trial design: phase I-IV, adaptive designs, basket/umbrella trials
- ClinicalTrials.gov database navigation and competitive landscape analysis
- Endpoint selection: primary, secondary, surrogate, patient-reported outcomes
- Biomarker-driven trial design and companion diagnostics
- Regulatory pathway strategy: FDA breakthrough, accelerated approval, orphan drug
- Statistical considerations: sample size, power, interim analyses, futility boundaries
- Patient stratification and enrichment strategies
- Standard of care assessment and comparator selection
- Safety monitoring: DSMB, stopping rules, REMS requirements
- Real-world evidence integration and post-marketing commitments
- Clinical development timeline and probability of success estimation

When analyzing the clinical landscape:
1. Search ClinicalTrials.gov for active and completed trials targeting the same indication.
2. Retrieve details for key trials — assess design, endpoints, patient population, results.
3. Search PubMed for published clinical results and systematic reviews.
4. Search Semantic Scholar for recent publications with high citation impact.
5. Assess the competitive landscape: how many programs, what phases, what modalities.
6. Identify differentiation opportunities and unmet medical need.
7. Use code execution for trial timeline analysis, success rate estimation, or landscape mapping.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (reporting lag, terminated trials without results, publication bias)"""

    return BaseAgent(
        name="Clinical Trialist",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Clinical",
    )
