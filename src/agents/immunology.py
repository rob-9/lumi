"""
Immunology — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
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
        "name": "get_protein_domains",
        "description": "Retrieve domain architecture and functional regions for a protein.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession ID."},
            },
            "required": ["uniprot_id"],
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
        "name": "monarch_search_entity",
        "description": "Search the Monarch Initiative knowledge graph for genes, diseases, or phenotypes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term (gene name, disease, or phenotype)."},
                "category": {"type": "string", "description": "Entity category filter (e.g. 'gene', 'disease', 'phenotype')."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "monarch_get_associations",
        "description": "Retrieve gene-disease or gene-phenotype associations from Monarch Initiative.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Monarch entity ID (e.g. 'HGNC:11998')."},
                "association_type": {"type": "string", "description": "Association type (e.g. 'disease', 'phenotype', 'gene')."},
            },
            "required": ["entity_id"],
        },
    },
]


def create_immunology_agent() -> BaseAgent:
    """Create the Immunology specialist agent."""

    system_prompt = """\
You are an Immunology specialist at Lumi Virtual Lab.

Your expertise spans:
- Immune cell typing, lineage markers, and flow/mass cytometry panel design
- TCR/BCR repertoire analysis, clonotype diversity, and antigen specificity prediction
- Cytokine profiling, signaling cascades (JAK-STAT, NF-κB, NFAT), and inflammatory networks
- Immune checkpoint biology (PD-1/PD-L1, CTLA-4, LAG-3, TIM-3, TIGIT)
- Immunotherapy response prediction and biomarker identification
- Autoimmunity mechanisms, tolerance breakdown, and autoantibody profiling
- Innate immunity (pattern recognition receptors, complement, NK cell biology)
- Vaccine immunology, adjuvant mechanisms, and mucosal immunity

When analyzing an immunology-related target:
1. Search literature for immune relevance, expression in immune cell subsets, and pathway roles.
2. Retrieve protein information and domain architecture for immune receptors/ligands.
3. Check protein-protein interactions for immune signaling partners and co-receptors.
4. Query Monarch Initiative for immune-related disease associations and phenotypes.
5. Assess therapeutic implications (checkpoint blockade, CAR-T targets, cytokine modulation).

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (species differences, context-dependent immune responses, assay limitations)"""

    return BaseAgent(
        name="Immunology",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Immunology & Cancer Biology",
    )
