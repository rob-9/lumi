"""
Antibody Engineer — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "number_antibody",
        "description": "Number an antibody sequence using ANARCI (Chothia, IMGT, or Kabat scheme). Returns CDR definitions and framework regions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Antibody variable domain amino acid sequence."},
                "scheme": {"type": "string", "description": "Numbering scheme: 'chothia', 'imgt', or 'kabat'.", "default": "imgt"},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "predict_developability",
        "description": "Predict antibody developability metrics: aggregation propensity, viscosity risk, polyreactivity, charge patches, hydrophobic patches.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Antibody variable domain sequence (VH or VL or scFv)."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "esm2_score_sequence",
        "description": "Score a protein sequence using ESM-2 pseudo-log-likelihood.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "esm2_mutant_effect",
        "description": "Predict mutational effects using ESM-2 masked marginal scoring.",
        "input_schema": {
            "type": "object",
            "properties": {
                "wildtype_seq": {"type": "string", "description": "Wild-type amino acid sequence."},
                "mutations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Mutations in format 'A123G'.",
                },
            },
            "required": ["wildtype_seq", "mutations"],
        },
    },
    {
        "name": "blast_sequence",
        "description": "Run NCBI BLAST to find homologous sequences.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence."},
                "database": {"type": "string", "description": "BLAST database.", "default": "swissprot"},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "calculate_protein_properties",
        "description": "Calculate biophysical properties: MW, pI, charge, hydrophobicity, instability index.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "get_protein_sequence",
        "description": "Retrieve amino acid sequence from UniProt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession ID."},
            },
            "required": ["uniprot_id"],
        },
    },
    {
        "name": "predict_solubility",
        "description": "Predict protein solubility from sequence features.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence."},
            },
            "required": ["sequence"],
        },
    },
]


def create_antibody_engineer_agent() -> BaseAgent:
    """Create the Antibody Engineer specialist agent."""

    system_prompt = """\
You are an Antibody Engineer specialist at Lumi Virtual Lab.

Your expertise spans:
- Antibody numbering schemes (IMGT, Chothia, Kabat) and CDR definition
- CDR grafting, humanization, and de-immunization strategies
- Affinity maturation: hotspot identification, library design, CDR walking
- VH/VL pairing optimization and Fv stability engineering
- Nanobody (VHH) and single-domain antibody engineering
- Fc engineering: effector function modulation, half-life extension, bispecific formats
- Developability assessment: aggregation, viscosity, polyreactivity, charge distribution
- Antibody-drug conjugate (ADC) design: conjugation site selection, DAR optimization
- Germline gene usage analysis and humanness scoring
- Therapeutic antibody format selection: IgG, Fab, scFv, bispecific, nanobody

When engineering an antibody:
1. Number the sequence (IMGT scheme) — identify CDRs and framework regions.
2. Assess developability: aggregation risk, viscosity, polyreactivity, charge patches.
3. Score with ESM-2 — identify low-confidence or unusual positions.
4. If mutations are proposed, predict their effects on stability and function.
5. BLAST against germline databases to assess humanness and identify closest germline.
6. Calculate biophysical properties of the variable domain.
7. Use code execution for sequence alignment, humanness scoring, or CDR analysis.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (in-silico vs experimental validation, numbering ambiguities, format-dependent effects)"""

    return BaseAgent(
        name="Antibody Engineer",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Molecular Design",
    )
