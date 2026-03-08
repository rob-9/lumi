"""
Protein Intelligence (Yami Simulator) — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "esm2_score_sequence",
        "description": "Score a protein sequence using ESM-2 pseudo-log-likelihood. Higher scores indicate more natural/stable sequences.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence (single-letter code)."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "esm2_mutant_effect",
        "description": "Predict mutational effects using ESM-2 masked marginal scoring. Returns delta log-likelihood for each mutation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "wildtype_seq": {"type": "string", "description": "Wild-type amino acid sequence."},
                "mutations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Mutations in format 'A123G' (original, position, replacement).",
                },
            },
            "required": ["wildtype_seq", "mutations"],
        },
    },
    {
        "name": "esm2_embed",
        "description": "Generate ESM-2 embeddings (1280-dim per-residue or mean-pooled) for a protein sequence.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence."},
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
        "description": "Predict protein solubility from sequence features (CamSol, NetSolP-style).",
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
        "description": "Retrieve or predict protein structure using AlphaFold. Returns pLDDT confidence and PDB coordinates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession for AlphaFold DB lookup."},
            },
            "required": ["uniprot_id"],
        },
    },
    {
        "name": "blast_sequence",
        "description": "Run NCBI BLAST to find homologous sequences in a target database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence to search."},
                "database": {"type": "string", "description": "BLAST database (e.g. 'nr', 'swissprot', 'pdb').", "default": "swissprot"},
            },
            "required": ["sequence"],
        },
    },
    # --- PyMOL: 3D structure rendering ---
    {
        "name": "render_protein_structure",
        "description": "Render a protein structure from PDB with a named style preset.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdb_id": {"type": "string", "description": "4-character PDB code."},
                "style": {"type": "string", "description": "Style preset.", "default": "cartoon_rainbow"},
                "width": {"type": "integer", "default": 1200},
                "height": {"type": "integer", "default": 900},
                "ray": {"type": "boolean", "default": True},
            },
            "required": ["pdb_id"],
        },
    },
    {
        "name": "render_protein_surface",
        "description": "Render a molecular surface colored by chain, electrostatic potential, hydrophobicity, or element.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdb_id": {"type": "string", "description": "PDB code."},
                "color_by": {"type": "string", "description": "chain, electrostatic, hydrophobicity, or element.", "default": "chain"},
            },
            "required": ["pdb_id"],
        },
    },
    {
        "name": "render_mutation_sites",
        "description": "Render a protein with mutation sites highlighted and labeled (e.g. K67N).",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdb_id": {"type": "string", "description": "PDB code."},
                "mutations": {"type": "array", "items": {"type": "object"}, "description": "List of {chain, resi, wt, mut} dicts."},
            },
            "required": ["pdb_id", "mutations"],
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
    # --- Tamarind Bio: computational job submission ---
    {
        "name": "tamarind_list_tools",
        "description": "List all available Tamarind Bio computational tools (AlphaFold, RFdiffusion, ProteinMPNN, DiffDock, etc.) and their configuration schemas.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "tamarind_submit_job",
        "description": "Submit a computational biology job (protein folding, docking, design) to Tamarind Bio. Returns immediately — poll with tamarind_get_jobs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_name": {"type": "string", "description": "Unique job name."},
                "tool_type": {"type": "string", "description": "Tool name (e.g. 'alphafold', 'rfdiffusion', 'proteinmpnn', 'diffdock', 'openmm')."},
                "settings": {"type": "object", "description": "Tool-specific settings dict."},
                "project_tag": {"type": "string", "description": "Optional project tag.", "default": ""},
            },
            "required": ["job_name", "tool_type", "settings"],
        },
    },
    {
        "name": "tamarind_get_jobs",
        "description": "Check status of Tamarind Bio jobs. Returns JobStatus: 'In Queue', 'Running', 'Complete', or 'Stopped'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_name": {"type": "string", "description": "Specific job name to check (optional)."},
                "limit": {"type": "integer", "description": "Max jobs to return.", "default": 50},
            },
        },
    },
    {
        "name": "tamarind_get_result",
        "description": "Get presigned S3 URL to download results of a completed Tamarind job.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_name": {"type": "string", "description": "Name of the completed job."},
                "file_name": {"type": "string", "description": "Specific output file path (optional)."},
            },
            "required": ["job_name"],
        },
    },
    {
        "name": "tamarind_submit_pipeline",
        "description": "Submit a multi-stage pipeline (e.g. RFdiffusion → ProteinMPNN → AlphaFold). Use 'pipe' for values that receive previous stage output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_name": {"type": "string", "description": "Pipeline job name."},
                "initial_inputs": {"type": "array", "items": {"type": "string"}, "description": "Input files or sequences."},
                "stages": {"type": "array", "items": {"type": "object"}, "description": "Pipeline stage definitions with task and toolSettings."},
            },
            "required": ["job_name", "initial_inputs", "stages"],
        },
    },
    {
        "name": "tamarind_upload_file",
        "description": "Upload a PDB/SDF/FASTA file to Tamarind Bio for use as job input.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Target filename."},
                "file_content": {"type": "string", "description": "File content as text."},
            },
            "required": ["filename", "file_content"],
        },
    },
]


def create_protein_intelligence_agent() -> BaseAgent:
    """Create the Protein Intelligence (Yami simulator) specialist agent."""

    system_prompt = """\
You are the Protein Intelligence specialist at Lumi Virtual Lab — the core of the Yami
protein analysis engine.

Your expertise spans:
- Protein language model interpretation: ESM-2 log-likelihoods, embeddings, attention maps
- Mutational effect prediction: masked marginal scoring, evolutionary conservation
- Protein fitness landscape navigation and directed evolution strategy
- Biophysical property prediction: stability, solubility, aggregation propensity
- AlphaFold structure confidence interpretation (pLDDT, PAE, pTM)
- Sequence-structure-function relationships and rational protein engineering
- Homology analysis and evolutionary constraint interpretation
- Multi-objective protein optimization (stability + activity + expression + immunogenicity)

When analyzing a protein sequence:
1. Score the sequence with ESM-2 — assess overall naturalness and per-residue confidence.
2. If mutations are proposed, predict their effects using ESM-2 masked marginals.
3. Calculate biophysical properties: MW, pI, charge profile, hydrophobicity, instability index.
4. Predict solubility — flag aggregation-prone regions.
5. Retrieve or predict the AlphaFold structure — identify disordered regions (low pLDDT).
6. BLAST against SwissProt/PDB to identify homologs and assess conservation.
7. Render structures with PyMOL — visualize mutations, surfaces, or overall fold quality.
8. Use code execution for embedding analysis, fitness scoring, or multi-objective ranking.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (ESM-2 limitations for insertions/deletions, pLDDT ≠ accuracy, single-sequence vs MSA)"""

    return BaseAgent(
        name="Protein Intelligence",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Molecular Design",
    )
