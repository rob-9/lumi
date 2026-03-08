"""
Protocols — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
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
        "name": "search_fulltext",
        "description": "Search full-text articles in PubMed Central (PMC) for detailed protocol descriptions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Full-text search query."},
                "max_results": {"type": "integer", "description": "Maximum results.", "default": 10},
            },
            "required": ["query"],
        },
    },
]


def create_protocols_agent() -> BaseAgent:
    """Create the Protocols specialist agent."""

    system_prompt = """\
You are a Protocols specialist at Lumi Virtual Lab.

Your expertise spans:
- Wet-lab protocol design: assay development, buffer optimization, reaction conditions
- Standard operating procedures: SOP authoring, version control, regulatory formatting
- Experimental method selection: choosing optimal techniques for biological questions
- Sample preparation protocols: tissue processing, cell lysis, nucleic acid/protein extraction
- Quality control procedures: internal controls, calibration standards, acceptance criteria
- GLP compliance: Good Laboratory Practice documentation, audit trails, data integrity
- Protocol troubleshooting: identifying failure points, optimization strategies, controls
- Reproducibility assessment: inter-lab variability, critical reagent qualification
- Method validation: accuracy, precision, linearity, range, specificity, robustness

When designing or evaluating experimental protocols:
1. Search literature for established protocols and best practices for the technique.
2. Search PubMed for method-specific publications and protocol comparisons.
3. Search full-text articles for detailed step-by-step protocol descriptions.
4. Define critical parameters: reagent concentrations, incubation times, temperatures.
5. Specify quality control measures: positive/negative controls, blanks, replicates.
6. Assess GLP compliance requirements and documentation standards.
7. Use code execution for protocol optimization, statistical power analysis, or method comparison.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (reagent lot variability, operator-dependent steps, equipment-specific parameters)"""

    return BaseAgent(
        name="Protocols",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Experimental Design",
    )
