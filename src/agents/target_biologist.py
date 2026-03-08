"""
Target Biologist — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "get_protein_info",
        "description": "Retrieve comprehensive protein information from UniProt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id_or_gene": {"type": "string", "description": "UniProt accession or gene symbol."},
            },
            "required": ["uniprot_id_or_gene"],
        },
    },
    {
        "name": "get_protein_sequence",
        "description": "Retrieve the canonical amino acid sequence from UniProt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession."},
            },
            "required": ["uniprot_id"],
        },
    },
    {
        "name": "get_protein_features",
        "description": "Retrieve protein features (domains, PTMs, active sites, binding sites) from UniProt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession."},
            },
            "required": ["uniprot_id"],
        },
    },
    {
        "name": "get_predicted_structure",
        "description": "Retrieve AlphaFold predicted structure and pLDDT scores for a protein.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession."},
            },
            "required": ["uniprot_id"],
        },
    },
    {
        "name": "get_protein_domains",
        "description": "Retrieve InterPro/Pfam domain annotations for a protein.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession."},
            },
            "required": ["uniprot_id"],
        },
    },
    {
        "name": "search_structures",
        "description": "Search RCSB PDB for experimentally determined structures.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (gene name, UniProt ID, or keyword)."},
            },
            "required": ["query"],
        },
    },
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
        "name": "search_proteins",
        "description": "Search UniProt for proteins by keyword.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword."},
                "organism": {"type": "string", "description": "Organism filter."},
                "max_results": {"type": "integer", "description": "Maximum number of results to return."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_domains_by_name",
        "description": "Search InterPro domains by name/keyword.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Domain name or keyword."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_pae",
        "description": "Retrieve AlphaFold predicted aligned error (PAE) matrix.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession."},
            },
            "required": ["uniprot_id"],
        },
    },
]


def create_target_biologist_agent() -> BaseAgent:
    """Create the Target Biologist specialist agent."""

    system_prompt = """\
You are a Target Biologist specialist at Lumi Virtual Lab.

Your expertise spans:
- Protein structure-function relationships and druggability assessment
- Domain architecture analysis: catalytic domains, allosteric sites, binding pockets
- Post-translational modification mapping and functional consequences
- Protein family classification and phylogenetic conservation analysis
- Structural biology: X-ray crystallography, cryo-EM, NMR data interpretation
- AlphaFold confidence interpretation (pLDDT, PAE) for structure quality
- Active site characterization and mechanism of action
- Protein-protein interaction interfaces and druggable hotspots
- Isoform-specific biology and splice variant functional differences

When analyzing a target protein:
1. Retrieve comprehensive UniProt data — function, subcellular localization, tissue specificity.
2. Get the canonical sequence and identify key functional residues.
3. Map protein features: domains, PTMs, signal peptides, transmembrane regions.
4. Search PDB for experimental structures — prioritize high-resolution co-crystal structures.
5. Retrieve AlphaFold prediction — assess confidence for unresolved regions.
6. Analyze domain architecture via InterPro/Pfam — identify druggable domains.
7. Use code execution for sequence analysis, conservation scoring, or structure comparison.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (crystal packing artifacts, AlphaFold low-confidence regions, isoform ambiguity)"""

    return BaseAgent(
        name="Target Biologist",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Modality",
    )
