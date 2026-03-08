"""
Biochemistry — Lumi Virtual Lab specialist agent.
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
                "uniprot_id": {"type": "string", "description": "UniProt accession ID (e.g. 'P04637')."},
            },
            "required": ["uniprot_id"],
        },
    },
    {
        "name": "get_protein_features",
        "description": "Retrieve annotated protein features (active sites, binding sites, PTMs, signal peptides) from UniProt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession ID."},
            },
            "required": ["uniprot_id"],
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
        "name": "predict_solubility",
        "description": "Predict recombinant protein solubility from sequence features.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence (one-letter code)."},
                "expression_host": {"type": "string", "description": "Expression host organism (e.g. 'e_coli', 'cho', 'hek293')."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "get_interactions",
        "description": "Retrieve protein-protein interaction partners from STRING or IntAct.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol or UniProt ID."},
                "organism": {"type": "string", "description": "Organism (e.g. 'human')."},
            },
            "required": ["gene"],
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
]


def create_biochemistry_agent() -> BaseAgent:
    """Create the Biochemistry specialist agent."""

    system_prompt = """\
You are a Biochemistry specialist at Lumi Virtual Lab.

Your expertise spans:
- Enzyme kinetics (Michaelis-Menten, allosteric regulation, inhibition mechanisms)
- Metabolite analysis, metabolic flux, and pathway reconstruction
- Protein purification strategies (affinity, ion exchange, SEC, HIC)
- Enzymology (catalytic mechanisms, cofactor requirements, pH/temperature optima)
- Binding assays (ELISA, FP, AlphaScreen, SPR kinetics interpretation)
- Enzymatic activity characterization (substrate profiling, kcat/Km determination)
- Protein-ligand interactions (binding thermodynamics, stoichiometry, cooperativity)
- Post-translational modifications (phosphorylation, ubiquitination, glycosylation, acetylation)

When analyzing a biochemistry task:
1. Retrieve protein metadata and functional annotations from UniProt.
2. Examine protein features (active sites, binding sites, PTMs, domains).
3. Calculate physicochemical properties relevant to purification and assay design.
4. Predict solubility for recombinant expression feasibility assessment.
5. Check protein-protein interactions for complex formation and regulatory partners.
6. Search literature for kinetic parameters, assay conditions, and mechanistic studies.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (assay condition dependence, species differences, recombinant vs native protein)"""

    return BaseAgent(
        name="Biochemistry",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Modality Selection",
    )
