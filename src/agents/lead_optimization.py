"""
Lead Optimization — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
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
        "name": "calculate_descriptors",
        "description": "Calculate molecular descriptors (MW, logP, HBD, HBA, TPSA, rotatable bonds) from SMILES.",
        "input_schema": {
            "type": "object",
            "properties": {
                "smiles": {"type": "string", "description": "SMILES string."},
            },
            "required": ["smiles"],
        },
    },
    {
        "name": "compute_similarity",
        "description": "Compute Tanimoto similarity between two molecules using Morgan fingerprints.",
        "input_schema": {
            "type": "object",
            "properties": {
                "smiles1": {"type": "string", "description": "First SMILES string."},
                "smiles2": {"type": "string", "description": "Second SMILES string."},
            },
            "required": ["smiles1", "smiles2"],
        },
    },
    {
        "name": "bindingdb_search_by_smiles",
        "description": "Search BindingDB for binding data by compound SMILES with similarity cutoff.",
        "input_schema": {
            "type": "object",
            "properties": {
                "smiles": {"type": "string", "description": "Compound SMILES string."},
                "similarity": {"type": "number", "description": "Tanimoto similarity cutoff (0-1)."},
                "max_results": {"type": "integer", "description": "Max results to return."},
            },
            "required": ["smiles"],
        },
    },
    {
        "name": "bindingdb_get_target_affinities",
        "description": "Get binding affinities for a target protein from BindingDB by UniProt ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession for the target."},
                "max_results": {"type": "integer", "description": "Max results to return."},
            },
            "required": ["uniprot_id"],
        },
    },
]


def create_lead_optimization_agent() -> BaseAgent:
    """Create the Lead Optimization specialist agent."""

    system_prompt = """\
You are a Lead Optimization specialist at Lumi Virtual Lab.

Your expertise spans:
- Multi-parameter optimization (MPO) for drug candidates: potency, selectivity, ADMET, safety
- Protein therapeutic optimization: stability, expression, immunogenicity, half-life
- Structure-activity relationship (SAR) analysis for both biologics and small molecules
- Directed evolution strategy: library design, screening cascade, hit-to-lead progression
- Biophysical property optimization: thermal stability (Tm), aggregation, viscosity
- Pharmacokinetic optimization: clearance, bioavailability, tissue distribution
- Mutational scanning and epistasis analysis for protein engineering
- Small molecule descriptor analysis and matched molecular pair analysis
- Pareto-optimal solution identification in multi-objective optimization
- Formulation-aware design: pH stability, freeze-thaw resilience, concentration limits

When optimizing a lead candidate:
1. Score the current sequence/molecule with ESM-2 or molecular descriptors as baseline.
2. For protein leads, predict effects of proposed mutations using ESM-2 masked marginals.
3. Calculate biophysical properties and identify liabilities (charge, hydrophobicity, instability).
4. Predict solubility and flag aggregation-prone sequences.
5. For small molecules, calculate descriptors and assess similarity to known actives.
6. Use code execution for MPO scoring, Pareto analysis, or property optimization.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (in-silico predictions vs experimental, epistatic effects, model applicability domain)"""

    return BaseAgent(
        name="Lead Optimization",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Molecular Design",
    )
