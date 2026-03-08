"""
Single Cell Atlas — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "query_gene_expression_single_cell",
        "description": "Query CellxGene Census for single-cell expression of a gene in a tissue/disease context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
                "tissue": {"type": "string", "description": "Tissue or organ name."},
                "disease": {"type": "string", "description": "Disease context (use 'normal' for healthy)."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "get_gene_expression",
        "description": "Retrieve tissue-level gene expression data from GTEx and Human Protein Atlas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "get_protein_expression",
        "description": "Retrieve protein-level expression data from Human Protein Atlas immunohistochemistry.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "get_pathology_data",
        "description": "Retrieve pathology expression data (cancer vs normal) from Human Protein Atlas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "search_geo_datasets",
        "description": "Search NCBI GEO for relevant single-cell or bulk expression datasets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (e.g. 'BRCA1 scRNA-seq lung cancer')."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "query_encode_experiments",
        "description": "Search ENCODE for epigenomic experiments.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target name."},
                "assay_type": {"type": "string", "description": "Assay type (e.g. ChIP-seq, ATAC-seq)."},
                "biosample": {"type": "string", "description": "Biosample name."},
            },
            "required": ["target"],
        },
    },
    {
        "name": "get_eqtls",
        "description": "Retrieve eQTL data for a gene from GTEx.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
                "tissue": {"type": "string", "description": "GTEx tissue name."},
            },
            "required": ["gene"],
        },
    },
]


def create_single_cell_atlas_agent() -> BaseAgent:
    """Create the Single Cell Atlas specialist agent."""

    system_prompt = """\
You are a Single Cell Atlas specialist at Lumi Virtual Lab.

Your expertise spans:
- Single-cell RNA-seq analysis (scanpy, Seurat methodology)
- Cell type annotation using reference atlases and marker genes
- Differential expression across cell types and disease states
- Cell-cell communication analysis (CellChat, LIANA, NicheNet)
- Trajectory and pseudotime analysis (RNA velocity, Monocle)
- Spatial transcriptomics interpretation (Visium, MERFISH, Slide-seq)
- Integration of multi-modal single-cell data (CITE-seq, SHARE-seq)
- Human Cell Atlas and CellxGene Census data navigation

When analyzing a target gene:
1. Query CellxGene Census for cell-type-resolved expression in relevant tissues.
2. Compare expression between disease and normal conditions at single-cell resolution.
3. Identify which cell types express the gene — flag immune, stromal, or rare populations.
4. Retrieve bulk expression (GTEx, HPA) for cross-validation with single-cell data.
5. Check pathology data for tumour vs normal expression if oncology-relevant.
6. Search GEO for disease-specific scRNA-seq datasets that may provide deeper context.
7. Use code execution for expression statistics, visualization, or marker gene analysis.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (dropout rates, batch effects, limited donor numbers, atlas coverage gaps)"""

    return BaseAgent(
        name="Single Cell Atlas",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Target Identification",
    )
