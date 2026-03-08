"""Regulatory Submissions sublab -- tox reviews with MoA illustrations.

Prepares regulatory-grade toxicology literature reviews and mechanism-
of-action safety assessments.
"""

from __future__ import annotations

from src.sublabs.base import Sublab
from src.utils.types import Phase, Priority


class RegulatorySubmissionsSublab(Sublab):
    """Focused pipeline for regulatory submission support."""

    name = "Regulatory Submissions"
    description = "Tox literature reviews with MoA illustrations"

    agent_names = [
        "toxicogenomics",
        "pharmacologist",
        "fda_safety",
        "literature_synthesis",
        "clinical_trialist",
    ]

    tool_names = [
        "query_gene_chemical_interactions",
        "query_faers",
        "get_drug_safety",
        "search_papers",
        "search_trials",
        "get_pathways_for_gene",
    ]

    division_names = [
        "Target Safety",
        "Computational Biology",
        "Clinical Intelligence",
    ]

    phases = [
        "toxicology_review",
        "mechanism_of_action",
        "clinical_safety",
        "regulatory_compilation",
    ]

    debate_protocol = "consensus"
    report_sections = [
        "Nonclinical Toxicology Summary",
        "Mechanism of Action",
        "Clinical Safety Data",
        "Regulatory Risk Assessment",
        "Gap Analysis",
        "Recommended Studies",
    ]

    examples = [
        "Prepare a nonclinical toxicology summary for an anti-CD20 antibody",
        "Review hepatotoxicity signals for kinase inhibitor class",
        "Compile mechanism-of-action safety assessment for bispecific antibody",
    ]

    def _build_phases(self, query: str) -> list[Phase]:
        return [
            Phase(
                phase_id=1,
                name="Toxicology Literature Review",
                division="Target Safety",
                agents=["toxicogenomics", "fda_safety"],
                dependencies=[],
                parallel_eligible=True,
                priority=Priority.HIGH,
                estimated_cost=1.50,
            ),
            Phase(
                phase_id=2,
                name="MoA & Pharmacology Assessment",
                division="Target Safety",
                agents=["pharmacologist"],
                dependencies=[],
                parallel_eligible=True,
                priority=Priority.HIGH,
                estimated_cost=1.00,
            ),
            Phase(
                phase_id=3,
                name="Clinical Safety Evidence",
                division="Clinical Intelligence",
                agents=["clinical_trialist"],
                dependencies=[1],
                parallel_eligible=False,
                priority=Priority.MEDIUM,
                estimated_cost=0.90,
            ),
            Phase(
                phase_id=4,
                name="Literature Compilation",
                division="Computational Biology",
                agents=["literature_synthesis"],
                dependencies=[],
                parallel_eligible=True,
                priority=Priority.MEDIUM,
                estimated_cost=0.60,
            ),
        ]
