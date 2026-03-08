"""
Cell Biology — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "get_gene_expression",
        "description": "Retrieve bulk gene expression data across tissues from GTEx or similar databases.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "HGNC gene symbol (e.g. 'TP53')."},
                "dataset": {"type": "string", "description": "Expression dataset to query (e.g. 'gtex', 'hpa')."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "get_protein_expression",
        "description": "Retrieve protein-level expression and localization data from the Human Protein Atlas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "HGNC gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "query_gene_expression_single_cell",
        "description": "Query single-cell RNA-seq expression data for a gene across cell types.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "HGNC gene symbol."},
                "tissue": {"type": "string", "description": "Tissue or organ to query (e.g. 'liver', 'brain')."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "get_pathology_data",
        "description": "Retrieve pathology-related expression and staining data from the Human Protein Atlas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "HGNC gene symbol."},
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
    {
        "name": "get_go_annotations",
        "description": "Retrieve Gene Ontology annotations for a gene (biological process, molecular function, cellular component).",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "HGNC gene symbol or UniProt ID."},
                "aspect": {"type": "string", "description": "GO aspect filter ('P' for process, 'F' for function, 'C' for component)."},
            },
            "required": ["gene"],
        },
    },
]


def create_cell_biology_agent() -> BaseAgent:
    """Create the Cell Biology specialist agent."""

    system_prompt = """\
You are a Cell Biology specialist at Lumi Virtual Lab.

Your expertise spans:
- Cell cycle analysis (G1/S/G2/M checkpoints, CDK/cyclin regulation, senescence)
- Organelle biology (ER, Golgi, mitochondria, lysosomes, endosomes, autophagy)
- Cell signaling pathways (MAPK, Wnt, Notch, Hedgehog, Hippo, TGF-beta)
- Proliferation and apoptosis assays (MTT, BrdU, Annexin V, caspase activity)
- Cell culture optimization (media formulation, passage protocols, contamination control)
- Transfection methods (lipofection, electroporation, nucleofection, viral transduction)
- Subcellular localization, membrane trafficking, and protein sorting
- Cell migration, adhesion, and extracellular matrix interactions

When analyzing a cell biology task:
1. Query gene and protein expression data across tissues and cell types.
2. Check single-cell expression for cell-type-specific patterns.
3. Retrieve pathology data for disease-relevant expression changes.
4. Obtain GO annotations for biological process, function, and compartment context.
5. Search literature for functional studies, assay protocols, and mechanistic insights.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (in vitro vs in vivo differences, cell line artifacts, passage effects)"""

    return BaseAgent(
        name="Cell Biology",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Modality Selection",
    )
