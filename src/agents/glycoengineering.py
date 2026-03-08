"""
Glycoengineering — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "get_protein_info",
        "description": "Retrieve protein metadata and annotations from UniProt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession ID (e.g. 'P01857')."},
            },
            "required": ["uniprot_id"],
        },
    },
    {
        "name": "get_protein_features",
        "description": "Retrieve annotated protein features (glycosylation sites, signal peptides, domains) from UniProt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession ID."},
            },
            "required": ["uniprot_id"],
        },
    },
    {
        "name": "get_protein_sequence",
        "description": "Retrieve the amino acid sequence for a protein from UniProt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession ID (e.g. 'P01857')."},
            },
            "required": ["uniprot_id"],
        },
    },
    {
        "name": "predict_developability",
        "description": "Predict biotherapeutic developability risks (aggregation, viscosity, clearance, immunogenicity).",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence (one-letter code)."},
                "molecule_type": {"type": "string", "description": "Molecule type (e.g. 'mab', 'fusion_protein', 'enzyme')."},
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
        "name": "search_pubmed",
        "description": "Search PubMed for biomedical literature matching a query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "PubMed search query."},
                "max_results": {"type": "integer", "description": "Maximum number of results to return."},
            },
            "required": ["query"],
        },
    },
]


def create_glycoengineering_agent() -> BaseAgent:
    """Create the Glycoengineering specialist agent."""

    system_prompt = """\
You are a Glycoengineering specialist at Lumi Virtual Lab.

Your expertise spans:
- Glycan structure analysis (monosaccharide composition, linkage determination, branching)
- Glycoprotein engineering (glycosite introduction/removal, sequon optimization)
- N-linked glycosylation (Asn-X-Ser/Thr sequons, occupancy prediction, processing pathways)
- O-linked glycosylation (mucin-type, O-GlcNAc, O-fucose, O-mannose)
- Glycan profiling techniques (HILIC, CE-LIF, LC-MS/MS, lectin arrays)
- Glycoengineering for biotherapeutics (afucosylation for ADCC, sialylation for half-life)
- Fc glycosylation optimization (G0F/G1F/G2F ratios, mannose-5, galactosylation control)
- Host cell glycosylation (CHO, HEK293, plant-based, yeast — glycan pattern differences)

When analyzing a glycoengineering task:
1. Retrieve protein information and annotated glycosylation sites from UniProt.
2. Examine protein features for signal peptides, glycosylation annotations, and disulfide bonds.
3. Obtain protein sequences for glycosite analysis and sequon identification.
4. Predict developability risks related to glycosylation (heterogeneity, immunogenicity, clearance).
5. Search literature for glycoengineering strategies, host cell optimization, and analytical methods.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (host cell variability, batch-to-batch heterogeneity, analytical method sensitivity)"""

    return BaseAgent(
        name="Glycoengineering",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Molecular Design",
    )
