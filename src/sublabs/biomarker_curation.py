"""Biomarker Curation sublab -- panel candidates with expression heatmaps.

Curates biomarker panels by integrating genetic association data,
single-cell expression profiles, and clinical trial evidence.
"""

from __future__ import annotations

from src.sublabs.base import Sublab
from src.utils.types import Phase, Priority


class BiomarkerCurationSublab(Sublab):
    """Focused pipeline for curating biomarker panels."""

    name = "Biomarker Curation"
    description = "Panel candidates with expression heatmaps"

    agent_names = [
        "statistical_genetics",
        "single_cell_atlas",
        "clinical_trialist",
        "literature_synthesis",
    ]

    tool_names = [
        "query_gwas_associations",
        "query_gene_variants",
        "get_gene_expression",
        "get_single_cell_expression",
        "search_trials",
        "search_papers",
    ]

    division_names = [
        "Target Identification",
        "Clinical Intelligence",
        "Computational Biology",
    ]

    phases = [
        "genetic_association_scan",
        "expression_profiling",
        "clinical_correlation",
        "panel_assembly",
    ]

    debate_protocol = "ranked_voting"
    report_sections = [
        "Candidate Biomarkers",
        "Genetic Evidence",
        "Expression Profiles",
        "Clinical Correlation",
        "Panel Recommendation",
        "Validation Strategy",
    ]

    examples = [
        "Identify circulating biomarkers for early pancreatic cancer detection",
        "Curate a pharmacodynamic biomarker panel for JAK inhibitor response",
        "Find predictive biomarkers for immune checkpoint inhibitor response",
    ]

    def _build_phases(self, query: str) -> list[Phase]:
        return [
            Phase(
                phase_id=1,
                name="Genetic Association Scan",
                division="Target Identification",
                agents=["statistical_genetics", "single_cell_atlas"],
                dependencies=[],
                parallel_eligible=True,
                priority=Priority.HIGH,
                estimated_cost=1.20,
            ),
            Phase(
                phase_id=2,
                name="Clinical Correlation Analysis",
                division="Clinical Intelligence",
                agents=["clinical_trialist"],
                dependencies=[1],
                parallel_eligible=False,
                priority=Priority.HIGH,
                estimated_cost=0.90,
            ),
            Phase(
                phase_id=3,
                name="Literature Context",
                division="Computational Biology",
                agents=["literature_synthesis"],
                dependencies=[],
                parallel_eligible=True,
                priority=Priority.MEDIUM,
                estimated_cost=0.60,
            ),
        ]
