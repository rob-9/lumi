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
    # --- PyMOL: 3D structure rendering ---
    {
        "name": "render_antibody_complex",
        "description": "Render an antibody-antigen complex with differentiated coloring for heavy chain, light chain, antigen, and CDR loops.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdb_id": {"type": "string", "description": "PDB code of the Ab-Ag complex."},
                "antigen_chain": {"type": "string", "description": "Chain ID of the antigen.", "default": "A"},
                "heavy_chain": {"type": "string", "description": "Chain ID of the heavy chain.", "default": "H"},
                "light_chain": {"type": "string", "description": "Chain ID of the light chain.", "default": "L"},
                "show_cdr_loops": {"type": "boolean", "description": "Highlight CDR loops (Kabat numbering).", "default": True},
            },
            "required": ["pdb_id"],
        },
    },
    {
        "name": "render_protein_structure",
        "description": "Render a protein structure from PDB with a named style preset.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdb_id": {"type": "string", "description": "4-character PDB code."},
                "style": {"type": "string", "description": "Style preset.", "default": "cartoon_rainbow"},
            },
            "required": ["pdb_id"],
        },
    },
    {
        "name": "highlight_residues",
        "description": "Highlight specific residues on a protein structure with colored sticks and labels.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdb_id": {"type": "string", "description": "PDB code."},
                "residues": {"type": "array", "items": {"type": "object"}, "description": "List of {chain, resi, color, label} dicts."},
            },
            "required": ["pdb_id", "residues"],
        },
    },
    {
        "name": "fetch_pdb_info",
        "description": "Fetch metadata about a PDB structure: chains, residue count, atom count, sequences.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdb_id": {"type": "string", "description": "PDB code."},
            },
            "required": ["pdb_id"],
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
7. Render antibody-antigen complexes with PyMOL — visualize CDR loops, paratope, and epitope.
8. Use code execution for sequence alignment, humanness scoring, or CDR analysis.

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
