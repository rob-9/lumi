"""
Structure Design — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "get_structure_info",
        "description": "Get detailed information about a PDB structure (resolution, method, ligands, chains).",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdb_id": {"type": "string", "description": "PDB ID (4 characters)."},
            },
            "required": ["pdb_id"],
        },
    },
    {
        "name": "get_binding_sites",
        "description": "Identify and characterize binding sites in a PDB structure (ligand contacts, pocket volume, druggability).",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdb_id": {"type": "string", "description": "PDB ID."},
            },
            "required": ["pdb_id"],
        },
    },
    {
        "name": "get_predicted_structure",
        "description": "Retrieve AlphaFold predicted structure and pLDDT confidence scores.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession."},
            },
            "required": ["uniprot_id"],
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
        "name": "render_protein_structure",
        "description": "Render a protein structure from PDB with a named style preset (cartoon_rainbow, publication, surface_electrostatic, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdb_id": {"type": "string", "description": "4-character PDB code (e.g. '1UBQ', '7S4S')."},
                "style": {"type": "string", "description": "Style preset: cartoon_rainbow, surface_electrostatic, surface_chain, secondary_structure, bfactor, chain_color, sticks, publication.", "default": "cartoon_rainbow"},
                "width": {"type": "integer", "description": "Image width in pixels.", "default": 1200},
                "height": {"type": "integer", "description": "Image height in pixels.", "default": 900},
                "ray": {"type": "boolean", "description": "Whether to ray-trace (higher quality, slower).", "default": True},
            },
            "required": ["pdb_id"],
        },
    },
    {
        "name": "render_binding_site",
        "description": "Render a close-up of a binding site with surrounding context. Binding residues shown as sticks with atom coloring.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdb_id": {"type": "string", "description": "PDB code."},
                "site_residues": {"type": "array", "items": {"type": "string"}, "description": "Residue numbers to highlight (e.g. ['45', '67', '112'])."},
                "site_chain": {"type": "string", "description": "Chain ID containing the binding site.", "default": "A"},
                "context_radius": {"type": "number", "description": "Angstrom radius around site to display.", "default": 8.0},
            },
            "required": ["pdb_id", "site_residues"],
        },
    },
    {
        "name": "align_structures",
        "description": "Superimpose two PDB structures, render the alignment, and report RMSD in angstroms.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdb_id_1": {"type": "string", "description": "First PDB code."},
                "pdb_id_2": {"type": "string", "description": "Second PDB code."},
            },
            "required": ["pdb_id_1", "pdb_id_2"],
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
                "style": {"type": "string", "description": "Base style preset.", "default": "cartoon_rainbow"},
            },
            "required": ["pdb_id", "residues"],
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
        "description": "List all available Tamarind Bio computational tools and their configuration schemas.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "tamarind_submit_job",
        "description": "Submit a computational biology job (folding, docking, MD simulation) to Tamarind Bio.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_name": {"type": "string", "description": "Unique job name."},
                "tool_type": {"type": "string", "description": "Tool name (e.g. 'alphafold', 'diffdock', 'openmm')."},
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
        "description": "Upload a PDB/SDF file to Tamarind Bio for use as job input.",
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


def create_structure_design_agent() -> BaseAgent:
    """Create the Structure Design specialist agent."""

    system_prompt = """\
You are a Structure-Based Design specialist at Lumi Virtual Lab.

Your expertise spans:
- Protein structure analysis: secondary structure, domain boundaries, disorder prediction
- Binding site identification and druggability assessment (Fpocket, SiteMap-style analysis)
- Structure-based drug design: pharmacophore modelling, shape complementarity
- Molecular docking interpretation and scoring function limitations
- Cryo-EM and X-ray crystallography data quality assessment (resolution, R-free, B-factors)
- AlphaFold structure interpretation: pLDDT confidence, PAE for domain boundaries
- Allosteric site identification and cryptic pocket detection
- Protein-protein interaction interface analysis and hotspot mapping
- Homology modelling for targets without experimental structures
- Structure-activity relationship rationalization from binding mode analysis

When performing structure-based analysis:
1. Retrieve PDB structure(s) — assess resolution, completeness, and ligand occupancy.
2. Identify binding sites — characterize pocket shape, volume, polarity, druggability score.
3. If no experimental structure exists, retrieve AlphaFold prediction and assess confidence.
4. Score the protein sequence with ESM-2 for per-residue confidence.
5. Calculate biophysical properties relevant to design.
6. Render 3D structures with PyMOL — use render_protein_structure, render_binding_site, or align_structures for visual evidence.
7. Use code execution for structural analysis, distance calculations, or visualization prep.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (crystal contacts, missing loops, conformational flexibility, AlphaFold limitations)"""

    return BaseAgent(
        name="Structure Design",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Molecular Design",
    )
