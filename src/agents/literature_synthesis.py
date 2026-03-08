"""
Literature Synthesis — Lumi Virtual Lab specialist agent.
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
        "name": "get_paper_details",
        "description": "Get full details for a paper including abstract, authors, references, and citation count.",
        "input_schema": {
            "type": "object",
            "properties": {
                "paper_id": {"type": "string", "description": "Semantic Scholar paper ID, DOI, or PMID."},
            },
            "required": ["paper_id"],
        },
    },
    {
        "name": "get_citations",
        "description": "Get papers that cite a given paper.",
        "input_schema": {
            "type": "object",
            "properties": {
                "paper_id": {"type": "string", "description": "Semantic Scholar paper ID, DOI, or PMID."},
                "max_results": {"type": "integer", "description": "Maximum citing papers to return.", "default": 20},
            },
            "required": ["paper_id"],
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
        "name": "search_preprints",
        "description": "Search bioRxiv/medRxiv for preprints.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "server": {"type": "string", "description": "Preprint server: 'biorxiv' or 'medrxiv'.", "default": "biorxiv"},
                "max_results": {"type": "integer", "description": "Maximum results.", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_fulltext",
        "description": "Search Europe PMC for full-text content across open-access publications.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Full-text search query."},
                "max_results": {"type": "integer", "description": "Maximum results.", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_references",
        "description": "Get references cited by a paper from Semantic Scholar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "paper_id": {"type": "string", "description": "Semantic Scholar paper ID, DOI, or PMID."},
                "max_results": {"type": "integer", "description": "Maximum number of results to return."},
            },
            "required": ["paper_id"],
        },
    },
    {
        "name": "get_author_papers",
        "description": "Get papers by a specific author.",
        "input_schema": {
            "type": "object",
            "properties": {
                "author_id": {"type": "string", "description": "Semantic Scholar author ID."},
                "max_results": {"type": "integer", "description": "Maximum number of results to return."},
            },
            "required": ["author_id"],
        },
    },
    {
        "name": "get_article_citations",
        "description": "Get citing articles from Europe PMC.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Source database (e.g. 'MED', 'PMC')."},
                "identifier": {"type": "string", "description": "Article identifier."},
            },
            "required": ["source", "identifier"],
        },
    },
    {
        "name": "get_preprint_details",
        "description": "Get full details of a bioRxiv/medRxiv preprint.",
        "input_schema": {
            "type": "object",
            "properties": {
                "doi": {"type": "string", "description": "Preprint DOI."},
            },
            "required": ["doi"],
        },
    },
]


def create_literature_synthesis_agent() -> BaseAgent:
    """Create the Literature Synthesis specialist agent."""

    system_prompt = """\
You are a Literature Synthesis specialist at Lumi Virtual Lab.

Your expertise spans:
- Systematic literature review methodology and PRISMA guidelines
- PubMed/MEDLINE search strategy optimization using MeSH terms and boolean logic
- Semantic Scholar citation network analysis and influence scoring
- Preprint evaluation: bioRxiv/medRxiv novelty assessment and reproducibility flags
- Evidence hierarchy: meta-analyses > RCTs > cohort studies > case reports
- Publication bias detection and funnel plot interpretation
- Narrative synthesis across heterogeneous evidence sources
- Knowledge gap identification and research frontier mapping
- Contradictory evidence resolution and consensus assessment
- Rapid evidence assessment for time-critical drug discovery decisions

When synthesizing literature:
1. Search Semantic Scholar for high-impact papers — sort by citation count and recency.
2. Search PubMed with optimized MeSH queries for comprehensive coverage.
3. Check bioRxiv/medRxiv for recent preprints that may not yet be indexed in PubMed.
4. Search Europe PMC full-text for specific findings that may be in supplementary material.
5. For key papers, retrieve full details and citation networks to identify seminal works.
6. Trace citation chains to understand how the field has evolved.
7. Use code execution for citation analysis, co-occurrence matrices, or timeline construction.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (publication bias, preprint status, small sample sizes, conflicting evidence)"""

    return BaseAgent(
        name="Literature Synthesis",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="CompBio",
    )
