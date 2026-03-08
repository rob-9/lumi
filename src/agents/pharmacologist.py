"""
Pharmacologist — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "get_target_compounds",
        "description": "Retrieve known compounds/drugs targeting a protein from ChEMBL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_name": {"type": "string", "description": "Target name or gene symbol."},
            },
            "required": ["target_name"],
        },
    },
    {
        "name": "get_compound_info",
        "description": "Get detailed compound information from ChEMBL (activity, selectivity, ADMET).",
        "input_schema": {
            "type": "object",
            "properties": {
                "chembl_id": {"type": "string", "description": "ChEMBL compound ID."},
            },
            "required": ["chembl_id"],
        },
    },
    {
        "name": "get_drug_info",
        "description": "Retrieve approved drug information including mechanism, indications, and status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "drug_name": {"type": "string", "description": "Drug name (generic or brand)."},
            },
            "required": ["drug_name"],
        },
    },
    {
        "name": "search_pubmed",
        "description": "Search PubMed for relevant biomedical literature.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "PubMed search query."},
                "max_results": {"type": "integer", "description": "Maximum results.", "default": 10},
            },
            "required": ["query"],
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
        "name": "check_drug_likeness",
        "description": "Evaluate drug-likeness rules (Lipinski, Veber, Ghose, Egan) for a molecule.",
        "input_schema": {
            "type": "object",
            "properties": {
                "smiles": {"type": "string", "description": "SMILES string."},
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
    {
        "name": "ddinter_check_pair",
        "description": "Check for drug-drug interactions between two specific drugs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "drug_a": {"type": "string", "description": "First drug name."},
                "drug_b": {"type": "string", "description": "Second drug name."},
            },
            "required": ["drug_a", "drug_b"],
        },
    },
    {
        "name": "biogrid_get_chemical_interactions",
        "description": "Get chemical-protein interactions for a gene from BioGRID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene_symbol": {"type": "string", "description": "Gene symbol."},
                "organism": {"type": "integer", "description": "NCBI Taxonomy ID (9606 for human)."},
            },
            "required": ["gene_symbol"],
        },
    },
]


def create_pharmacologist_agent() -> BaseAgent:
    """Create the Pharmacologist specialist agent."""

    system_prompt = """\
You are a Pharmacologist specialist at Lumi Virtual Lab.

Your expertise spans:
- Pharmacology: mechanism of action, receptor pharmacology, dose-response analysis
- ChEMBL bioactivity data mining: IC50, EC50, Ki, Kd interpretation
- Structure-activity relationships (SAR) and selectivity profiling
- Drug-likeness assessment: Lipinski Ro5, Veber rules, CNS-MPO, oral bioavailability
- ADMET property prediction: absorption, distribution, metabolism, excretion, toxicity
- PK/PD modelling: clearance, half-life, volume of distribution, therapeutic window
- Drug repurposing: identifying new indications for existing drugs
- Competitive landscape analysis: existing drugs and clinical candidates for a target
- Multi-pharmacology and polypharmacology risk assessment

When analyzing pharmacology for a target:
1. Query ChEMBL for known compounds — assess chemical tractability and SAR trends.
2. Retrieve detailed compound data: potency, selectivity, ADMET properties.
3. Check for approved drugs targeting the same protein or pathway.
4. Search PubMed for recent pharmacology publications and reviews.
5. Calculate descriptors and drug-likeness for candidate molecules if provided.
6. Assess the competitive landscape and freedom to operate.
7. Use code execution for SAR analysis, potency comparisons, or descriptor calculations.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (assay variability, species differences, cell-based vs biochemical IC50)"""

    return BaseAgent(
        name="Pharmacologist",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Modality",
    )
