"""Assay Troubleshooting sublab -- root-cause analysis of experimental issues.

Diagnoses unexpected experimental results by combining assay design
expertise with functional genomics and expression data.
"""

from __future__ import annotations

from src.sublabs.base import Sublab
from src.utils.types import Phase, Priority


class AssayTroubleshootingSublab(Sublab):
    """Focused pipeline for diagnosing assay and experimental issues."""

    name = "Assay Troubleshooting"
    description = "Root-cause analysis of unexpected experimental results"

    agent_names = [
        "assay_design",
        "functional_genomics",
        "single_cell_atlas",
    ]

    tool_names = [
        "get_gene_expression",
        "get_protein_expression",
        "query_depmap",
        "get_single_cell_expression",
        "search_papers",
    ]

    division_names = [
        "Experimental Design",
        "Target Identification",
    ]

    phases = [
        "problem_characterization",
        "data_analysis",
        "root_cause_identification",
        "solution_proposal",
    ]

    debate_protocol = "elimination"
    report_sections = [
        "Problem Description",
        "Potential Root Causes",
        "Data Analysis",
        "Recommended Solutions",
        "Protocol Modifications",
        "Positive Controls",
    ]

    examples = [
        "Why is my ELISA showing high background in serum samples?",
        "Troubleshoot low transfection efficiency in HEK293 cells",
        "Diagnose inconsistent IC50 values across plate replicates",
    ]

    def _build_phases(self, query: str) -> list[Phase]:
        return [
            Phase(
                phase_id=1,
                name="Problem Characterization & Data Review",
                division="Experimental Design",
                agents=["assay_design"],
                dependencies=[],
                parallel_eligible=False,
                priority=Priority.HIGH,
                estimated_cost=0.80,
            ),
            Phase(
                phase_id=2,
                name="Expression & Functional Context",
                division="Target Identification",
                agents=["functional_genomics", "single_cell_atlas"],
                dependencies=[],
                parallel_eligible=True,
                priority=Priority.MEDIUM,
                estimated_cost=1.00,
            ),
        ]
