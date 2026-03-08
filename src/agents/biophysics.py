"""
Biophysics — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "get_structure_info",
        "description": "Retrieve 3D structure metadata from the PDB (resolution, method, ligands, chains).",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdb_id": {"type": "string", "description": "PDB identifier (e.g. '1BRS')."},
            },
            "required": ["pdb_id"],
        },
    },
    {
        "name": "get_binding_sites",
        "description": "Retrieve binding site annotations and ligand contacts from a PDB structure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdb_id": {"type": "string", "description": "PDB identifier."},
                "chain": {"type": "string", "description": "Chain identifier (e.g. 'A')."},
            },
            "required": ["pdb_id"],
        },
    },
    {
        "name": "get_predicted_structure",
        "description": "Retrieve an AlphaFold-predicted structure for a UniProt accession.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession ID (e.g. 'P04637')."},
            },
            "required": ["uniprot_id"],
        },
    },
    {
        "name": "esm2_score_sequence",
        "description": "Score a protein sequence using ESM-2 for per-residue log-likelihoods and mutation effect prediction.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence (one-letter code)."},
                "mutations": {"type": "string", "description": "Comma-separated mutations to score (e.g. 'A42G,L55P')."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "calculate_protein_properties",
        "description": "Calculate physicochemical properties (MW, pI, extinction coefficient, hydrophobicity) from an amino acid sequence.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence (one-letter code)."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "search_papers",
        "description": "Search scientific literature for papers matching a query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string."},
                "max_results": {"type": "integer", "description": "Maximum number of results to return."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "tamarind_submit_job",
        "description": "Submit a molecular dynamics simulation job to the Tamarind cloud platform.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdb_id": {"type": "string", "description": "PDB identifier or uploaded structure reference."},
                "simulation_type": {"type": "string", "description": "Simulation type (e.g. 'md', 'minimization', 'free_energy')."},
                "duration_ns": {"type": "number", "description": "Simulation duration in nanoseconds."},
                "force_field": {"type": "string", "description": "Force field to use (e.g. 'amber99sb', 'charmm36m', 'opls-aa')."},
            },
            "required": ["pdb_id", "simulation_type"],
        },
    },
    {
        "name": "tamarind_get_result",
        "description": "Retrieve results from a completed Tamarind molecular dynamics simulation job.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Tamarind job identifier."},
            },
            "required": ["job_id"],
        },
    },
]


def create_biophysics_agent() -> BaseAgent:
    """Create the Biophysics specialist agent."""

    system_prompt = """\
You are a Biophysics specialist at Lumi Virtual Lab.

Your expertise spans:
- Molecular dynamics simulations (system setup, force field selection, trajectory analysis)
- Thermodynamic analysis (binding free energy, entropy-enthalpy decomposition, thermal stability)
- Binding free energy calculations (MM-PBSA, MM-GBSA, FEP, TI)
- Protein stability analysis (ddG prediction, thermal unfolding, aggregation propensity)
- Conformational analysis (principal component analysis, clustering, metastable states)
- Biophysical characterization techniques (SPR, ITC, DSF/thermal shift, DLS, AUC)
- Structure-function relationships from experimental and predicted 3D structures
- Membrane biophysics (lipid bilayer simulations, membrane protein dynamics)

When analyzing a biophysics task:
1. Retrieve experimental 3D structures from the PDB with resolution and method details.
2. Examine binding sites, ligand contacts, and key residue interactions.
3. Obtain AlphaFold-predicted structures for targets lacking experimental data.
4. Score sequences and mutations with ESM-2 for fitness and stability prediction.
5. Calculate physicochemical properties relevant to stability and formulation.
6. Submit and retrieve molecular dynamics simulations via Tamarind for dynamics insights.
7. Search literature for experimental biophysical data and validated computational protocols.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (force field limitations, sampling convergence, crystal packing artifacts)"""

    return BaseAgent(
        name="Biophysics",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Molecular Design",
    )
