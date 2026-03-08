"""Lead Optimization sublab -- multi-parameter optimization of drug candidates.

Coordinates protein intelligence, antibody engineering, structure design,
and developability assessment for iterative lead optimization.
"""

from __future__ import annotations

from src.sublabs.base import Sublab
from src.utils.types import Phase, Priority


class LeadOptimizationSublab(Sublab):
    """Focused pipeline for multi-parameter lead optimization."""

    name = "Lead Optimization"
    description = "Multi-parameter optimization of drug candidates"

    agent_names = [
        "lead_optimization",
        "antibody_engineer",
        "developability",
        "structure_design",
        "protein_intelligence",
    ]

    tool_names = [
        "esm2_score_sequence",
        "predict_structure",
        "calculate_solubility",
        "calculate_stability",
        "blast_sequence",
        "get_protein_info",
        "calculate_descriptors",
    ]

    division_names = [
        "Molecular Design",
        "Modality Selection",
    ]

    phases = [
        "structure_analysis",
        "property_prediction",
        "optimization_rounds",
        "developability_filter",
        "candidate_ranking",
    ]

    debate_protocol = "pareto_ranking"
    report_sections = [
        "Starting Point Analysis",
        "Optimization Strategy",
        "Design Candidates",
        "Multi-Parameter Profiles",
        "Developability Assessment",
        "Recommended Next Steps",
    ]

    examples = [
        "Optimize a lead compound for improved oral bioavailability and reduced hERG liability",
        "Improve thermostability of anti-HER2 antibody without losing affinity",
        "Design selective kinase inhibitor with improved metabolic stability",
    ]

    def _build_phases(self, query: str) -> list[Phase]:
        return [
            Phase(
                phase_id=1,
                name="Structure & Property Analysis",
                division="Molecular Design",
                agents=["protein_intelligence", "structure_design"],
                dependencies=[],
                parallel_eligible=True,
                priority=Priority.HIGH,
                estimated_cost=2.00,
            ),
            Phase(
                phase_id=2,
                name="Optimization & Engineering",
                division="Molecular Design",
                agents=["lead_optimization", "antibody_engineer"],
                dependencies=[1],
                parallel_eligible=True,
                priority=Priority.HIGH,
                estimated_cost=2.50,
            ),
            Phase(
                phase_id=3,
                name="Developability Assessment",
                division="Molecular Design",
                agents=["developability"],
                dependencies=[2],
                parallel_eligible=False,
                priority=Priority.HIGH,
                estimated_cost=1.00,
            ),
        ]
