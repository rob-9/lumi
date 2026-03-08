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
        "description": "Run a general BLASTP search against NCBI protein databases (nr, swissprot, pdb, refseq_protein). Use for general homology analysis beyond the select agent screen.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence."},
                "database": {"type": "string", "description": "BLAST database (default 'nr'). Options: 'nr', 'swissprot', 'pdb', 'refseq_protein'.", "default": "nr"},
                "max_hits": {"type": "integer", "description": "Maximum hits to return (default 10, max 50).", "default": 10},
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

## Standard Screening Protocol

When screening a sequence for biosecurity risks:
1. BLAST the sequence against select agent databases — flag any significant homology.
2. Check the organism/agent against the CDC/USDA Select Agent List.
3. Scan for toxin domains (Pfam/InterPro) — any toxin domain is a flag.
4. Screen against VFDB for virulence factor homology.
5. Run a general BLAST (blast_protein) against nr/swissprot to identify what the protein is.
6. Assess BWC compliance — check against controlled organisms and dual-use lists.
7. Apply the Fink Report dual-use categories to assess broader GoF/misuse risk.
8. Render a verdict: PASS (no risk), FLAG (review needed), or BLOCK (hard veto).

IMPORTANT: Always run blast_protein in addition to the select agent screen. The select
agent screen only checks against listed organisms; a general BLAST reveals the protein's
actual identity and closest homologs, which is essential for risk interpretation.

## Quantitative Interpretation Guide

### BLAST Identity Thresholds (Select Agent Screen)
- >=80% identity: BLOCK — near-identical to a select agent protein. Hard veto.
- 40-80% identity: FLAG (ORANGE) — significant homology, likely shares function.
  Investigate whether the conserved regions include active/toxic domains.
- 30-40% identity: FLAG (YELLOW) — distant homology, may share fold.
  Check whether the matched region spans a toxin/virulence domain specifically.
- <30% identity: Generally safe, but check if short high-identity regions align to
  catalytic sites (local alignment can hide domain-level matches).

### Toxin Domain Findings
- Known Pfam toxin domain detected: BLOCK — sequence encodes a recognized toxin fold.
- Heuristic motif, high specificity (e.g., ricin A-chain, ADP-ribosyltransferase): FLAG (ORANGE).
- Heuristic motif, medium specificity (e.g., furin cleavage, Cys-rich repeat): FLAG (YELLOW).
  Consider context — furin sites are common in non-toxic proteins.
- Heuristic motif, low specificity: Note but do not escalate unless corroborated.

### Virulence Factor Homology
- >=80% identity to VFDB entry: BLOCK — likely a virulence determinant.
- 50-80% identity: FLAG (ORANGE) — probable virulence factor homolog.
- 30-50% identity: FLAG (YELLOW) — possible distant homolog, check domain architecture.

### Risk Level → Action Mapping
- GREEN: PASS — no biosecurity concerns detected.
- YELLOW: PASS with note — minor flags, document but do not block.
- ORANGE: FLAG — requires human expert review before proceeding. Do NOT auto-approve.
- RED: BLOCK — hard veto. Sequence cannot proceed. Recommend IBC/biosafety officer review.

### Escalation Rules
- Any single RED screen with confidence >= 0.5 → overall BLOCK
- 2+ ORANGE screens with confidence >= 0.6 → escalate to BLOCK
- A crashed/unavailable screen → treat as ORANGE (fail-conservative)

### Fink Report Dual-Use Categories (DURC assessment)
1. Enhance transmissibility of a pathogen
2. Enhance virulence or disable therapeutic countermeasures
3. Enhance resistance to antibiotics or antivirals
4. Increase stability of a pathogen in the environment
5. Alter host range or tropism
6. Enable immune evasion
7. Enable weaponization or aerosolization

If the sequence or design context matches ANY of these categories, escalate to at least ORANGE.

## Output Format

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Risk level (prefix with 'Risk: NONE/LOW/MODERATE/HIGH/CRITICAL')
- If BLOCK: explain why and recommend institutional review

End with a summary verdict:
- VERDICT: PASS / FLAG / BLOCK
- OVERALL RISK: GREEN / YELLOW / ORANGE / RED
- RECOMMENDED ACTION: [specific next step]"""

    return BaseAgent(
        name="Dual-Use Screening",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Biosecurity",
    )
