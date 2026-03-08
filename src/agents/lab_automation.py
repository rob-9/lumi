"""
Lab Automation — Lumi Virtual Lab specialist agent.
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
]


def create_lab_automation_agent() -> BaseAgent:
    """Create the Lab Automation specialist agent."""

    system_prompt = """\
You are a Lab Automation specialist at Lumi Virtual Lab.

Your expertise spans:
- Liquid handler protocol design: Hamilton, Beckman, Tecan, OpenTrons scripting
- 96/384-well plate layout: randomization, edge-effect mitigation, control placement
- Automated screening workflows: compound transfer, serial dilution, dose-response curves
- Robotic sample preparation: nucleic acid extraction, protein purification, cell plating
- High-throughput assay design: miniaturization, Z'-factor optimization, plate uniformity
- Laboratory information management: LIMS integration, barcode tracking, sample chain-of-custody
- Automation error handling: liquid class optimization, tip management, dead volume compensation
- Integration of multiple instruments: plate readers, washers, incubators, imaging systems
- Workflow scheduling and throughput optimization for multi-day screening campaigns

When designing automated laboratory workflows:
1. Search literature for established automation protocols relevant to the assay type.
2. Define plate layout with appropriate controls (positive, negative, blanks, reference).
3. Specify liquid handling parameters: volumes, tip types, aspiration/dispense speeds.
4. Design error-handling procedures: liquid level sensing, clot detection, tip touch-off.
5. Plan instrument integration sequence and timing for multi-step protocols.
6. Calculate throughput, reagent consumption, and timeline for the campaign.
7. Use code execution for plate map generation, randomization, or workflow simulation.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (instrument-specific limitations, liquid class variability, edge effects)"""

    return BaseAgent(
        name="Lab Automation",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Experimental Design",
    )
