"""Target Validation sublab -- evidence dossiers with pathway diagrams.

Produces a comprehensive target validation dossier by coordinating
genetic evidence, safety profiling, and literature synthesis agents.
"""

from __future__ import annotations

from src.sublabs.base import Sublab
from src.utils.types import Phase, Priority


class TargetValidationSublab(Sublab):
    """Focused pipeline for building target validation evidence dossiers."""

    name = "Target Validation"
    description = "Evidence dossiers with pathway diagrams and confidence scores"

    agent_names = [
        "target_biologist",
        "bio_pathways",
        "literature_synthesis",
        "fda_safety",
        "statistical_genetics",
        "functional_genomics",
        "single_cell_atlas",
    ]

    tool_names = [
        "query_target_disease",
        "get_target_info",
        "query_gwas_associations",
        "query_gene_variants",
        "query_clinvar_gene",
        "get_gene_expression",
        "get_pathways_for_gene",
        "search_papers",
        "query_faers",
        "query_gene_chemical_interactions",
    ]

    division_names = [
        "Target Identification",
        "Target Safety",
        "Computational Biology",
    ]

    phases = [
        "genetic_evidence",
        "functional_validation",
        "safety_assessment",
        "literature_synthesis",
        "integration",
    ]

    debate_protocol = "convergence"
    report_sections = [
        "Genetic Evidence",
        "Functional Validation",
        "Pathway Analysis",
        "Safety Profile",
        "Literature Context",
        "Confidence Assessment",
        "Recommended Experiments",
    ]

    examples = [
        "Evaluate BRCA1 as a therapeutic target for triple-negative breast cancer",
        "Assess PCSK9 inhibition safety profile based on genetic evidence",
        "Validate KRAS G12C as a druggable target in non-small cell lung cancer",
    ]

    def _build_phases(self, query: str) -> list[Phase]:
        return [
            Phase(
                phase_id=1,
                name="Genetic Evidence Collection",
                division="Target Identification",
                agents=["statistical_genetics", "functional_genomics", "single_cell_atlas"],
                dependencies=[],
                parallel_eligible=True,
                priority=Priority.HIGH,
                estimated_cost=1.50,
            ),
            Phase(
                phase_id=2,
                name="Safety Assessment",
                division="Target Safety",
                agents=["fda_safety", "bio_pathways"],
                dependencies=[1],
                parallel_eligible=True,
                priority=Priority.HIGH,
                estimated_cost=1.20,
            ),
            Phase(
                phase_id=3,
                name="Literature Synthesis",
                division="Computational Biology",
                agents=["literature_synthesis"],
                dependencies=[],
                parallel_eligible=True,
                priority=Priority.MEDIUM,
                estimated_cost=0.80,
            ),
        ]
