"""
Developability — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "predict_developability",
        "description": "Predict antibody/protein developability metrics: aggregation propensity, viscosity risk, polyreactivity, charge patches, hydrophobic patches.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Protein or antibody sequence."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "calculate_protein_properties",
        "description": "Calculate biophysical properties: MW, pI, charge at pH 7.4, hydrophobicity, instability index, GRAVY.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence."},
            },
            "required": ["sequence"],
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
    {
        "name": "calculate_cai",
        "description": "Calculate Codon Adaptation Index (CAI) for a DNA sequence in a target host organism.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dna_seq": {"type": "string", "description": "DNA coding sequence."},
            },
            "required": ["dna_seq"],
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
        "name": "predict_structure_alphafold",
        "description": "Predict/retrieve protein structure from AlphaFold DB.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Protein amino acid sequence."},
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
]


def create_developability_agent() -> BaseAgent:
    """Create the Developability specialist agent."""

    system_prompt = """\
You are a Developability Assessment specialist at Lumi Virtual Lab.

Your expertise spans:
- CMC (Chemistry, Manufacturing, and Controls) risk assessment for biologics
- Aggregation propensity prediction: hydrophobic patches, APR identification
- Viscosity prediction and formulation-dependent concentration limits
- Charge heterogeneity: deamidation, isomerization, oxidation hotspot identification
- Expression system optimization: CHO, HEK293, E. coli codon usage and secretion
- Codon optimization and Codon Adaptation Index (CAI) analysis
- Post-translational modification liability: N-glycosylation, O-glycosylation, clipping
- Thermal stability prediction and accelerated stability risk assessment
- Immunogenicity risk: T-cell epitope prediction, humanness scoring
- Formulation compatibility: pH stability, surfactant requirements, freeze-thaw resilience
- Scale-up risk: titre prediction, purification complexity, process robustness

When assessing developability:
1. Run the developability prediction — check aggregation, viscosity, polyreactivity scores.
2. Calculate biophysical properties — flag extreme pI, high hydrophobicity, or instability.
3. Predict solubility — identify concentration-limiting factors.
4. If DNA sequence is available, calculate CAI for the intended expression host.
5. Score with ESM-2 — low-scoring positions may indicate folding or stability issues.
6. Use code execution for sequence motif scanning (deamidation NG, oxidation M, clipping sites).

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (in-silico vs experimental, formulation-dependent outcomes, host-cell effects)"""

    return BaseAgent(
        name="Developability",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Molecular Design",
    )
