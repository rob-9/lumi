"""
Bioimaging — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
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
    {
        "name": "search_pubmed",
        "description": "Search PubMed/MEDLINE for biomedical literature with MeSH term support.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "PubMed search query (supports MeSH terms and boolean operators)."},
                "max_results": {"type": "integer", "description": "Maximum results.", "default": 10},
            },
            "required": ["query"],
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
]


def create_bioimaging_agent() -> BaseAgent:
    """Create the Bioimaging specialist agent."""

    system_prompt = """\
You are a Bioimaging specialist at Lumi Virtual Lab.

Your expertise spans:
- Microscopy image analysis: brightfield, fluorescence, phase contrast image processing
- Cell segmentation: automated cell detection, boundary delineation, morphometric analysis
- Fluorescence quantification: intensity measurement, colocalization analysis, FRET efficiency
- High-content screening image analysis: multi-parametric phenotypic profiling, hit identification
- Confocal and super-resolution microscopy: z-stack processing, deconvolution, STORM/PALM analysis
- Live-cell imaging: time-lapse analysis, cell tracking, mitotic index, migration assays
- Whole-slide imaging: tissue scanning, region annotation, spatial statistics
- Image-based biomarker quantification: IHC scoring, H-score calculation, tissue microarray analysis
- Machine learning for imaging: CNN-based classification, U-Net segmentation, transfer learning

When performing bioimaging analysis:
1. Search literature for imaging protocols and analysis methods relevant to the target.
2. Search PubMed for imaging-specific studies and high-content screening results.
3. Retrieve protein expression data to assess tissue staining patterns and subcellular localization.
4. Retrieve pathology data to compare expression in disease vs normal tissue contexts.
5. Recommend appropriate imaging modality based on the biological question and resolution needs.
6. Define image analysis pipelines: preprocessing, segmentation, feature extraction, quantification.
7. Use code execution for image analysis workflows, statistical quantification, or visualization.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (photobleaching, autofluorescence, fixation artefacts, resolution limits, antibody specificity)"""

    return BaseAgent(
        name="Bioimaging",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Imaging",
    )
