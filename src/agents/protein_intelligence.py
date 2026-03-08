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
    {
        "name": "calculate_protein_properties",
        "description": "Calculate biophysical properties: MW, pI, charge at pH 7.4, instability index, GRAVY, aromaticity, aliphatic index, amino acid composition.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "predict_developability",
        "description": "Assess developability risks: N-glycosylation sites, deamidation hotspots (NG/NS/NT), Met/Trp oxidation, unpaired cysteines, charge patches, hydrophobic patches, DG/DP isomerization, pyroglutamate formation, C-terminal Lys clipping, polyreactivity risk.",
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
        "description": "Calculate Codon Adaptation Index using Kazusa-derived codon frequency tables. Reports expected CAI, rare codon positions, GC content, and expression recommendations for E. coli, yeast, human, or CHO.",
        "input_schema": {
            "type": "object",
            "properties": {
                "protein_sequence": {"type": "string", "description": "Amino acid sequence."},
                "organism": {"type": "string", "description": "Target organism: 'ecoli', 'yeast', 'human', 'cho'.", "default": "ecoli"},
            },
            "required": ["protein_sequence"],
        },
    },
    {
        "name": "number_antibody",
        "description": "Identify CDR and framework regions in an antibody variable domain using IMGT-like heuristic numbering. Detects heavy/light chain type.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Antibody variable domain amino acid sequence."},
            },
            "required": ["sequence"],
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
- Developability assessment: PTM hotspots, chemical liabilities, manufacturability
- Codon optimization and expression system selection

## Standard Analysis Workflow

When analyzing a protein sequence, follow this systematic workflow:
1. Score with ESM-2 — assess overall naturalness and per-residue confidence.
2. Calculate biophysical properties — MW, pI, instability index, GRAVY, aliphatic index.
3. Predict solubility — examine CamSol-style scores and aggregation-prone patches.
4. Assess developability — check for chemical liabilities (deamidation, oxidation, isomerization).
5. If mutations proposed → predict effects using ESM-2 masked marginals.
6. If UniProt ID available → fetch AlphaFold structure for pLDDT confidence.
7. BLAST against SwissProt/PDB to identify homologs and conservation context.
8. If expression system relevant → calculate CAI for the target organism.

## Quantitative Interpretation Guide

### ESM-2 Fitness Score
- 0.85-1.0: Highly natural sequence, consistent with evolutionary selection
- 0.65-0.85: Reasonable sequence, likely functional
- 0.45-0.65: Moderate deviations from natural sequences — check specific positions
- <0.45: Significant deviations — may indicate misfolding or non-natural design

### ESM-2 Mutant Effect (delta log-likelihood → ddG proxy)
- delta_ll > +0.3: Stabilizing (~-0.5 kcal/mol or better); mutation favored by evolution
- -0.5 < delta_ll < +0.3: Neutral; likely tolerated
- -1.5 < delta_ll < -0.5: Destabilizing (~+0.75-2.25 kcal/mol); proceed with caution
- delta_ll < -1.5: Highly destabilizing (>+2.25 kcal/mol); likely deleterious
- CAVEAT: ESM-2 ddG correlation with experiment is r~0.4-0.5. Use for ranking, not absolute prediction.
- CAVEAT: ESM-2 cannot assess insertions/deletions. Only substitutions are scored.

### Instability Index (Guruprasad et al., 1990)
- <25: Highly stable protein
- 25-40: Stable protein (threshold = 40)
- 40-50: Marginally unstable
- >50: Likely unstable in vitro

### Solubility Score (CamSol-inspired)
- >0.65: Soluble — suitable for aqueous formulation
- 0.45-0.65: Borderline — may require formulation optimization
- <0.45: Likely insoluble — engineering or refolding needed
- Check aggregation-prone patches: stretches of 5+ residues with windowed CamSol < -0.8

### AlphaFold pLDDT Interpretation
- >90: Very high confidence — atomic-level accuracy expected
- 70-90: Confident — backbone is reliable, side chains less so
- 50-70: Low confidence — likely flexible/disordered loop or domain boundary
- <50: Very low — predicted disorder or poor template coverage

### Developability Risk Flags (prioritize by severity)
- HIGH: unpaired cysteines (aggregation), large hydrophobic patches (>10 residues)
- MEDIUM: N-glycosylation sequons, deamidation hotspots (NG/NS), DP acid-labile sites, charge patches
- LOW: Met oxidation, DG isomerization, C-terminal Lys clipping, pyroglutamate

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
