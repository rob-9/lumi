"""
Dual-Use Screening (Biosecurity) — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "screen_against_select_agents",
        "description": "BLAST a protein/nucleotide sequence against CDC/USDA Select Agent and Toxin List organisms. Returns alignments with identity, coverage, and risk classification.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid or nucleotide sequence."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "check_select_agent_list",
        "description": "Check whether an organism, toxin, or agent appears on the CDC/USDA Select Agent and Toxin List.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Organism name, toxin name, or agent identifier."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "scan_toxin_domains",
        "description": "Scan a protein sequence for known toxin domains using InterPro/Pfam domain search.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "screen_virulence_factors",
        "description": "Screen a sequence against the Virulence Factor Database (VFDB) for known virulence determinants.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid or nucleotide sequence."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "check_bwc_compliance",
        "description": "Assess compliance with the Biological Weapons Convention (BWC) for an organism or agent. Checks against BWC Annex lists and export control regulations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "organism_or_agent": {"type": "string", "description": "Organism name, agent name, or relevant identifier."},
            },
            "required": ["organism_or_agent"],
        },
    },
    {
        "name": "blast_protein",
        "description": "Run BLAST protein search against NCBI databases.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Protein sequence to search."},
                "database": {"type": "string", "description": "BLAST database (e.g. 'nr', 'swissprot')."},
                "max_results": {"type": "integer", "description": "Maximum number of results to return."},
            },
            "required": ["sequence"],
        },
    },
]


def create_dual_use_screening_agent() -> BaseAgent:
    """Create the Dual-Use Screening (Biosecurity) specialist agent."""

    system_prompt = """\
You are a Dual-Use Research Screening specialist at Lumi Virtual Lab — the biosecurity
gatekeeper with HARD VETO authority.

CRITICAL: If a sequence or research proposal poses biosecurity risk, you MUST flag it
immediately. When in doubt, err on the side of caution. False positives are acceptable;
false negatives are not.

Your expertise spans:
- CDC/USDA Select Agent and Toxin List screening and classification
- Biological Weapons Convention (BWC) compliance assessment
- Dual-Use Research of Concern (DURC) evaluation per Fink Report categories
- Toxin domain identification: AB toxins, pore-forming toxins, enzymatic toxins
- Virulence factor detection: adhesins, invasins, immune evasion, secretion systems
- Gain-of-function (GoF) risk assessment for enhanced pathogenicity or transmissibility
- Export control regulations: Australia Group, Wassenaar Arrangement
- Sequence-based threat assessment: homology to pathogens and toxins
- De novo risk assessment for synthetic biology constructs
- Responsible disclosure and institutional biosafety committee (IBC) referral

When screening for biosecurity risks:
1. BLAST the sequence against select agent databases — flag any significant homology (>30% identity).
2. Check the organism/agent against the CDC/USDA Select Agent List.
3. Scan for toxin domains (Pfam/InterPro) — any toxin domain is a flag.
4. Screen against VFDB for virulence factor homology.
5. Assess BWC compliance — check against controlled organisms and dual-use lists.
6. Apply the Fink Report dual-use categories to assess broader GoF/misuse risk.
7. Render a verdict: PASS (no risk), FLAG (review needed), or BLOCK (hard veto).

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Risk level (prefix with 'Risk: NONE/LOW/MODERATE/HIGH/CRITICAL')
- If BLOCK: explain why and recommend institutional review"""

    return BaseAgent(
        name="Dual-Use Screening",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Biosecurity",
    )
