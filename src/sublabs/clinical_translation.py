"""Clinical Translation sublab -- go/no-go evidence packages for IND-enabling studies.

Assembles comprehensive evidence packages to support clinical translation
decisions by integrating clinical, safety, and genetic evidence.
"""

from __future__ import annotations

from src.sublabs.base import Sublab
from src.utils.types import Phase, Priority


class ClinicalTranslationSublab(Sublab):
    """Focused pipeline for clinical translation evidence packages."""

    name = "Clinical Translation"
    description = "Go/no-go evidence packages for IND-enabling studies"

    agent_names = [
        "clinical_trialist",
        "pharmacologist",
        "statistical_genetics",
        "fda_safety",
        "literature_synthesis",
    ]

    tool_names = [
        "search_trials",
        "get_drug_info",
        "query_faers",
        "query_gwas_associations",
        "search_papers",
        "get_pathways_for_gene",
    ]

    division_names = [
        "Clinical Intelligence",
        "Target Safety",
        "Computational Biology",
    ]

    phases = [
        "clinical_landscape",
        "safety_review",
        "translatability_assessment",
        "evidence_compilation",
    ]

    debate_protocol = "weighted_consensus"
    report_sections = [
        "Clinical Landscape",
        "Competitive Intelligence",
        "Safety & Toxicology Summary",
        "Translational Evidence",
        "Go/No-Go Recommendation",
        "Risk Mitigation Strategies",
        "Recommended IND-Enabling Studies",
    ]

    examples = [
        "Build go/no-go evidence package for anti-IL-17 antibody IND filing",
        "Assess clinical translatability of preclinical efficacy data for NASH target",
        "Evaluate first-in-human dose selection strategy for bispecific T-cell engager",
    ]

    def _build_phases(self, query: str) -> list[Phase]:
        return [
            Phase(
                phase_id=1,
                name="Clinical Landscape & Trial Analysis",
                division="Clinical Intelligence",
                agents=["clinical_trialist"],
                dependencies=[],
                parallel_eligible=True,
                priority=Priority.HIGH,
                estimated_cost=1.20,
            ),
            Phase(
                phase_id=2,
                name="Safety & Toxicology Review",
                division="Target Safety",
                agents=["fda_safety", "pharmacologist"],
                dependencies=[],
                parallel_eligible=True,
                priority=Priority.HIGH,
                estimated_cost=1.30,
            ),
            Phase(
                phase_id=3,
                name="Literature & Evidence Compilation",
                division="Computational Biology",
                agents=["literature_synthesis"],
                dependencies=[],
                parallel_eligible=True,
                priority=Priority.MEDIUM,
                estimated_cost=0.70,
            ),
        ]
