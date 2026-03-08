"""
Red Team Agent — tool-equipped adversarial specialist for Lumi Virtual Lab.

Unlike the ReviewPanel (which is a prompt-only reviewer), the RedTeamAgent
is a full specialist agent with tools.  It can independently search literature,
query databases, and run analyses to fact-check and challenge claims produced
by other agents.

Invoked after ReviewPanel (Phase 7) identifies issues, and before HITL
routing (Phase 7.5).  Contested or unverifiable findings get their confidence
scores adjusted downward, which feeds into the HITL router's thresholds.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    # --- Literature verification ---
    {
        "name": "search_papers",
        "description": "Search Semantic Scholar for academic papers to verify or refute claims.",
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
        "description": "Search PubMed/MEDLINE for biomedical literature to cross-check claims.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "PubMed search query (supports MeSH terms)."},
                "max_results": {"type": "integer", "description": "Maximum results.", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_paper_details",
        "description": "Get full details for a paper including abstract, authors, references.",
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
        "description": "Get papers that cite a given paper — useful for checking if findings have been replicated or refuted.",
        "input_schema": {
            "type": "object",
            "properties": {
                "paper_id": {"type": "string", "description": "Semantic Scholar paper ID, DOI, or PMID."},
                "max_results": {"type": "integer", "description": "Maximum citing papers.", "default": 20},
            },
            "required": ["paper_id"],
        },
    },
    {
        "name": "search_preprints",
        "description": "Search bioRxiv/medRxiv preprint servers for recent unpublished findings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Preprint search query."},
                "server": {"type": "string", "description": "Server: 'biorxiv' or 'medrxiv'.", "default": "biorxiv"},
                "max_results": {"type": "integer", "description": "Maximum results.", "default": 10},
            },
            "required": ["query"],
        },
    },
    # --- Genomics & target verification ---
    {
        "name": "query_target_disease",
        "description": "Query Open Targets for target-disease association evidence.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_id": {"type": "string", "description": "Ensembl gene ID (e.g. ENSG00000141510)."},
                "disease_id": {"type": "string", "description": "EFO disease ID (e.g. EFO_0000311)."},
            },
            "required": ["target_id", "disease_id"],
        },
    },
    {
        "name": "get_target_info",
        "description": "Get comprehensive target information from Open Targets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_id": {"type": "string", "description": "Ensembl gene ID."},
            },
            "required": ["target_id"],
        },
    },
    {
        "name": "get_gene_expression",
        "description": "Get gene expression data from Human Protein Atlas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol (e.g. TP53)."},
            },
            "required": ["gene"],
        },
    },
    # --- Protein & structure verification ---
    {
        "name": "get_protein_info",
        "description": "Get protein information from UniProt for verifying protein-level claims.",
        "input_schema": {
            "type": "object",
            "properties": {
                "accession": {"type": "string", "description": "UniProt accession (e.g. P04637)."},
            },
            "required": ["accession"],
        },
    },
    {
        "name": "get_protein_features",
        "description": "Get protein features and annotations from UniProt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "accession": {"type": "string", "description": "UniProt accession."},
            },
            "required": ["accession"],
        },
    },
    # --- Pathway & interaction verification ---
    {
        "name": "get_interactions",
        "description": "Get protein-protein interactions from STRING to verify interaction claims.",
        "input_schema": {
            "type": "object",
            "properties": {
                "protein": {"type": "string", "description": "Protein name or identifier."},
                "species": {"type": "integer", "description": "NCBI taxonomy ID.", "default": 9606},
                "score_threshold": {"type": "number", "description": "Minimum interaction score.", "default": 0.7},
            },
            "required": ["protein"],
        },
    },
    {
        "name": "get_pathways_for_gene",
        "description": "Get pathway memberships for a gene from Reactome.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
                "species": {"type": "string", "description": "Species.", "default": "Homo sapiens"},
            },
            "required": ["gene"],
        },
    },
    # --- Clinical & safety verification ---
    {
        "name": "search_trials",
        "description": "Search ClinicalTrials.gov to verify clinical claims.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query for clinical trials."},
                "status": {"type": "string", "description": "Trial status filter."},
                "max_results": {"type": "integer", "description": "Maximum results.", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_adverse_events",
        "description": "Search FDA FAERS for adverse event reports to verify safety claims.",
        "input_schema": {
            "type": "object",
            "properties": {
                "drug_name": {"type": "string", "description": "Drug name to search."},
                "reaction": {"type": "string", "description": "Adverse reaction term."},
                "max_results": {"type": "integer", "description": "Maximum results.", "default": 10},
            },
            "required": ["drug_name"],
        },
    },
    # --- Disease association verification ---
    {
        "name": "disgenet_gene_diseases",
        "description": "Get gene-disease associations from DisGeNET to verify disease claims.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene_symbol": {"type": "string", "description": "Gene symbol."},
                "min_score": {"type": "number", "description": "Minimum association score.", "default": 0.3},
            },
            "required": ["gene_symbol"],
        },
    },
]


_SYSTEM_PROMPT = """\
You are the Red Team Agent for Lumi Virtual Lab — a tool-equipped adversarial
investigator.  Your mission is to independently verify, challenge, and
fact-check claims produced by specialist agents.

You have access to literature databases, genomics APIs, protein databases,
clinical trial registries, and safety databases.  Use them actively.

For each claim you are given to investigate:

1. **Search for supporting evidence** — can you independently find sources
   that corroborate the claim?
2. **Search for contradicting evidence** — are there papers, data, or known
   facts that contradict or limit the claim?
3. **Check the specifics** — are gene names, protein IDs, trial numbers,
   and statistical claims accurate?
4. **Assess confidence calibration** — is the stated confidence level
   appropriate given the evidence you found?

For each investigated claim, output a structured assessment:

Finding: <your assessment of the claim>
Verdict: VERIFIED | CONTESTED | REFUTED | UNVERIFIABLE
Original_Confidence: <the agent's stated confidence>
Adjusted_Confidence: <your recommended confidence after investigation>
Evidence: <key sources you found>
Rationale: <why you reached this verdict>

Be thorough but fair.  The goal is scientific accuracy, not contrarianism.
Challenge claims when warranted, but acknowledge strong evidence when it exists.
"""


def create_red_team_agent() -> BaseAgent:
    """Factory function for the Red Team adversarial verification agent."""
    return BaseAgent(
        name="red_team",
        system_prompt=_SYSTEM_PROMPT,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        max_steps=25,
        division="review",
    )
