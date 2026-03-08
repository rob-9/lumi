"""
Systems Biology — Lumi Virtual Lab specialist agent.
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
        "description": "Retrieve full interaction network for a set of proteins from STRING.",
        "input_schema": {
            "type": "object",
            "properties": {
                "proteins": {"type": "array", "items": {"type": "string"}, "description": "List of protein names or identifiers."},
                "species": {"type": "integer", "description": "NCBI taxonomy ID (9606 for human).", "default": 9606},
            },
            "required": ["proteins"],
        },
    },
    {
        "name": "get_enrichment",
        "description": "Perform functional enrichment analysis on a gene set using STRING enrichment API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "genes": {"type": "array", "items": {"type": "string"}, "description": "List of gene symbols."},
                "species": {"type": "integer", "description": "NCBI taxonomy ID (9606 for human).", "default": 9606},
            },
            "required": ["genes"],
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
        "name": "get_go_annotations",
        "description": "Retrieve Gene Ontology annotations (biological process, molecular function, cellular component) for a gene.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
                "species": {"type": "string", "description": "Species (e.g. 'human', 'mouse').", "default": "human"},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "go_enrichment",
        "description": "Perform Gene Ontology enrichment analysis on a gene set.",
        "input_schema": {
            "type": "object",
            "properties": {
                "genes": {"type": "array", "items": {"type": "string"}, "description": "List of gene symbols."},
                "ontology": {"type": "string", "description": "GO ontology (BP, MF, CC).", "default": "BP"},
                "species": {"type": "string", "description": "Species (e.g. 'human', 'mouse').", "default": "human"},
            },
            "required": ["genes"],
        },
    },
    {
        "name": "search_papers",
        "description": "Search Semantic Scholar for academic papers with citation data and abstracts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "year_range": {"type": "string", "description": "Year range filter (e.g. '2020-2025')."},
                "max_results": {"type": "integer", "description": "Maximum results.", "default": 10},
            },
            "required": ["query"],
        },
    },
]


def create_systems_biology_agent() -> BaseAgent:
    """Create the Systems Biology specialist agent."""

    system_prompt = """\
You are a Systems Biology specialist at Lumi Virtual Lab.

Your expertise spans:
- Network inference: protein-protein interaction networks, co-expression networks, causal reasoning
- ODE modeling of biological systems: kinetic parameter estimation, sensitivity analysis, bifurcation analysis
- Flux balance analysis: constraint-based metabolic modeling, FBA/FVA, metabolic flux prediction
- Multi-omics data integration: transcriptomics, proteomics, metabolomics, epigenomics data fusion
- Gene regulatory network reconstruction: transcription factor binding, motif analysis, network topology
- Systems pharmacology: target-pathway-disease mapping, polypharmacology, network perturbation modeling
- Boolean and logic-based modeling: signaling pathway logic models, attractor analysis
- Dynamical systems analysis: steady-state computation, stability analysis, oscillatory behavior
- Graph-theoretic analysis: centrality measures, module detection, network motifs

When performing systems-level analysis:
1. Retrieve protein-protein interactions to build the local interaction network.
2. Expand to a full network for multi-protein analyses and module detection.
3. Perform functional enrichment to identify overrepresented pathways and processes.
4. Map genes to Reactome pathways for mechanistic context.
5. Retrieve GO annotations for functional characterization of network components.
6. Perform GO enrichment analysis on gene sets to identify biological themes.
7. Search literature for systems biology studies and computational models of the system.
8. Use code execution for network analysis, ODE modeling, FBA, or multi-omics integration.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (network completeness, model assumptions, data integration biases, overfitting)"""

    return BaseAgent(
        name="Systems Biology",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Computational Biology",
    )
