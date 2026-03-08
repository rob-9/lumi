"""
Bio Pathways — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "get_interactions",
        "description": "Retrieve protein-protein interactions from STRING database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "protein": {"type": "string", "description": "Protein name or identifier."},
                "species": {"type": "integer", "description": "NCBI taxonomy ID (9606 for human).", "default": 9606},
            },
            "required": ["protein"],
        },
    },
    {
        "name": "get_network",
        "description": "Build a STRING interaction network for a set of proteins.",
        "input_schema": {
            "type": "object",
            "properties": {
                "proteins": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of protein names.",
                },
            },
            "required": ["proteins"],
        },
    },
    {
        "name": "get_enrichment",
        "description": "Run functional enrichment analysis (GO, KEGG, Reactome) on a protein set via STRING.",
        "input_schema": {
            "type": "object",
            "properties": {
                "proteins": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of protein names.",
                },
            },
            "required": ["proteins"],
        },
    },
    {
        "name": "get_protein_domains",
        "description": "Retrieve InterPro/Pfam domain annotations for a protein from UniProt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession."},
            },
            "required": ["uniprot_id"],
        },
    },
    {
        "name": "get_pathways_for_gene",
        "description": "Retrieve Reactome pathways in which a gene participates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "get_pathway_details",
        "description": "Get detailed information about a Reactome pathway including participants and diagram.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pathway_id": {"type": "string", "description": "Reactome stable ID (e.g. 'R-HSA-123456')."},
            },
            "required": ["pathway_id"],
        },
    },
    {
        "name": "get_go_annotations",
        "description": "Retrieve Gene Ontology annotations (BP, MF, CC) for a gene.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "biogrid_search_interactions",
        "description": "Search BioGRID for protein-protein interactions involving a gene.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene_symbol": {"type": "string", "description": "Gene symbol (e.g. BRCA1, TP53)."},
                "organism": {"type": "integer", "description": "NCBI Taxonomy ID (9606 for human)."},
                "max_results": {"type": "integer", "description": "Max interactions to return."},
            },
            "required": ["gene_symbol"],
        },
    },
    {
        "name": "biogrid_get_interaction_network",
        "description": "Get full BioGRID interaction network for a set of genes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene_list": {"type": "string", "description": "Pipe-separated gene symbols (e.g. 'BRCA1|TP53|EGFR')."},
                "organism": {"type": "integer", "description": "NCBI Taxonomy ID."},
            },
            "required": ["gene_list"],
        },
    },
]


def create_bio_pathways_agent() -> BaseAgent:
    """Create the Bio Pathways specialist agent."""

    system_prompt = """\
You are a Biological Pathways specialist at Lumi Virtual Lab.

Your expertise spans:
- Signalling pathway analysis (MAPK, PI3K/AKT/mTOR, Wnt, Notch, JAK-STAT, NF-kB)
- Protein-protein interaction network analysis and hub identification
- Gene Ontology enrichment and functional annotation
- Reactome and KEGG pathway mapping and cross-talk analysis
- Protein domain architecture and functional implications
- Network topology: betweenness centrality, clustering, modularity
- Pathway crosstalk, feedback loops, and compensatory mechanisms
- Integration of pathway data with genetic and expression evidence

When analyzing a target gene:
1. Retrieve protein-protein interactions from STRING — identify high-confidence partners.
2. Build an interaction network and identify pathway modules and hub proteins.
3. Run functional enrichment to identify overrepresented GO terms and pathways.
4. Map the gene to Reactome pathways — assess pathway centrality and redundancy.
5. Retrieve protein domain architecture from InterPro/Pfam — identify druggable domains.
6. Assess GO annotations across Biological Process, Molecular Function, Cellular Component.
7. Use code execution for network analysis (centrality, clustering) or enrichment statistics.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (interaction score thresholds, literature bias, tissue-specificity of interactions)"""

    return BaseAgent(
        name="Bio Pathways",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Target Safety",
    )
