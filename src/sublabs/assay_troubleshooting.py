"""Assay Troubleshooting sublab -- root-cause analysis of experimental issues.

Diagnoses unexpected experimental results by combining assay design
expertise with functional genomics and expression data. Uses query-aware
phase routing to focus investigation on the most likely problem category
and an elimination-style debate to rank root causes by plausibility.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.sublabs.base import Sublab
from src.utils.llm import ModelTier
from src.utils.types import (
    Claim,
    DivisionReport,
    FinalReport,
    Phase,
    Priority,
)

logger = logging.getLogger("lumi.sublabs.assay_troubleshooting")

# ---------------------------------------------------------------------------
# Query classification keywords
# ---------------------------------------------------------------------------

_SIGNAL_NOISE_KEYWORDS = [
    "background", "noise", "signal", "snr", "artifact", "autofluorescence",
    "nonspecific", "non-specific", "bleed-through", "crosstalk", "blank",
    "false positive", "false negative",
]

_VARIABILITY_KEYWORDS = [
    "inconsistent", "variability", "replicate", "cv", "coefficient of variation",
    "irreproducible", "plate effect", "edge effect", "drift", "batch",
    "z-factor", "z-prime", "z'",
]

_EXPRESSION_KEYWORDS = [
    "expression", "transfection", "transduction", "knockdown", "knockout",
    "overexpression", "silencing", "low yield", "protein production",
    "folding", "solubility", "inclusion body", "aggregation",
]

_PROTOCOL_KEYWORDS = [
    "incubation", "wash", "lysis", "blocking", "antibody", "conjugate",
    "substrate", "reagent", "buffer", "ph", "temperature", "timing",
    "dilution", "concentration", "elisa", "western", "flow cytometry",
]


def _classify_query(query: str) -> list[str]:
    """Classify a troubleshooting query into problem categories.

    Returns a list of matched categories ordered by relevance.  Always
    includes ``"general"`` as a fallback.
    """
    q = query.lower()
    categories: list[str] = []

    score_map = {
        "signal_noise": sum(1 for kw in _SIGNAL_NOISE_KEYWORDS if kw in q),
        "variability": sum(1 for kw in _VARIABILITY_KEYWORDS if kw in q),
        "expression": sum(1 for kw in _EXPRESSION_KEYWORDS if kw in q),
        "protocol": sum(1 for kw in _PROTOCOL_KEYWORDS if kw in q),
    }

    for cat, score in sorted(score_map.items(), key=lambda x: x[1], reverse=True):
        if score > 0:
            categories.append(cat)

    if not categories:
        categories.append("general")
    return categories


class AssayTroubleshootingSublab(Sublab):
    """Focused pipeline for diagnosing assay and experimental issues.

    Enhancements over the base sublab:

    1. **Query-aware phase routing** -- analyses the user query to select
       relevant investigation phases (signal/noise, variability, expression,
       or protocol review).
    2. **Elimination debate** -- ranks root cause hypotheses by plausibility,
       eliminates low-confidence causes, and scores remediation strategies.
    3. **Structured synthesis** -- populates the six report sections with
       ranked root causes, protocol modifications, and positive controls.
    """

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

    # ------------------------------------------------------------------
    # Query-aware phase routing
    # ------------------------------------------------------------------

    def _build_phases(self, query: str) -> list[Phase]:
        categories = _classify_query(query)
        phases: list[Phase] = []
        phase_id = 0

        # Phase 1 (always): Problem characterisation via assay_design agent.
        phase_id += 1
        phases.append(
            Phase(
                phase_id=phase_id,
                name="Problem Characterization & Data Review",
                division="Experimental Design",
                agents=["assay_design"],
                dependencies=[],
                parallel_eligible=False,
                priority=Priority.HIGH,
                estimated_cost=0.80,
            ),
        )
        characterization_id = phase_id

        # Phase 2 (conditional): Signal/noise or variability investigation.
        if "signal_noise" in categories or "variability" in categories or "general" in categories:
            phase_id += 1
            if "signal_noise" in categories:
                name = "Signal-to-Noise & Artifact Analysis"
            elif "variability" in categories:
                name = "Replicate Variability & QC Analysis"
            else:
                name = "Assay Performance Analysis"
            phases.append(
                Phase(
                    phase_id=phase_id,
                    name=name,
                    division="Experimental Design",
                    agents=["assay_design"],
                    dependencies=[characterization_id],
                    parallel_eligible=False,
                    priority=Priority.HIGH,
                    estimated_cost=0.80,
                ),
            )

        # Phase 3 (conditional): Expression & functional context when
        # the problem may be biology-driven.
        if "expression" in categories or "general" in categories:
            phase_id += 1
            phases.append(
                Phase(
                    phase_id=phase_id,
                    name="Expression & Functional Context",
                    division="Target Identification",
                    agents=["functional_genomics", "single_cell_atlas"],
                    dependencies=[characterization_id],
                    parallel_eligible=True,
                    priority=Priority.MEDIUM,
                    estimated_cost=1.00,
                ),
            )

        # Phase 4 (always): Solution proposal depends on all prior phases.
        prior_ids = [p.phase_id for p in phases]
        phase_id += 1
        phases.append(
            Phase(
                phase_id=phase_id,
                name="Root Cause Ranking & Solution Proposal",
                division="Experimental Design",
                agents=["assay_design"],
                dependencies=prior_ids,
                parallel_eligible=False,
                priority=Priority.HIGH,
                estimated_cost=0.80,
            ),
        )

        return phases

    # ------------------------------------------------------------------
    # Elimination debate
    # ------------------------------------------------------------------

    async def _run_debate(
        self,
        query: str,
        reports: list[DivisionReport],
    ) -> list[dict[str, Any]]:
        """Run elimination-style debate to rank root cause hypotheses.

        Unlike the base majority-vote debate, elimination works in rounds:
        1. Enumerate all candidate root causes from agent findings.
        2. Each agent argues for/against each cause with evidence.
        3. Low-plausibility causes are eliminated each round.
        4. Surviving causes are ranked with remediation feasibility scores.
        """
        all_claims: list[Claim] = []
        for r in reports:
            for sr in r.specialist_results:
                all_claims.extend(sr.findings)

        if len(all_claims) < 2:
            return []

        claims_text = "\n".join(
            f"- [{c.agent_id}] {c.claim_text} "
            f"(confidence: {c.confidence.level.value}, score: {c.confidence.score:.2f})"
            for c in all_claims
        )

        debate_prompt = (
            "You are moderating an elimination-style troubleshooting debate.\n\n"
            f"Original problem: {query}\n\n"
            f"Agent findings:\n{claims_text}\n\n"
            "Run an elimination debate in 2-3 rounds:\n"
            "Round 1 — Enumerate all candidate root causes from the findings.\n"
            "  For each cause, have the relevant agent argue its plausibility.\n"
            "  Eliminate causes with plausibility < 0.3.\n"
            "Round 2 — Surviving causes are challenged by other agents.\n"
            "  Each challenger provides counter-evidence or caveats.\n"
            "  Eliminate causes that cannot withstand challenge.\n"
            "Round 3 (final) — Rank surviving causes by:\n"
            "  - plausibility (0-1)\n"
            "  - remediation_feasibility (0-1, how easy to fix)\n"
            "  - evidence_strength (0-1)\n\n"
            "Return a JSON array of round objects:\n"
            "[\n"
            "  {\n"
            '    "round": 1,\n'
            '    "candidates": [\n'
            "      {\n"
            '        "cause": "description of root cause",\n'
            '        "agent_id": "proposing agent",\n'
            '        "plausibility": 0.8,\n'
            '        "argument": "why this is a likely cause",\n'
            '        "evidence": ["evidence references"],\n'
            '        "eliminated": false\n'
            "      }\n"
            "    ]\n"
            "  },\n"
            "  ...\n"
            "  {\n"
            '    "round": 3,\n'
            '    "ranked_causes": [\n'
            "      {\n"
            '        "rank": 1,\n'
            '        "cause": "most likely root cause",\n'
            '        "plausibility": 0.85,\n'
            '        "remediation_feasibility": 0.9,\n'
            '        "evidence_strength": 0.7,\n'
            '        "recommended_fix": "specific fix"\n'
            "      }\n"
            "    ]\n"
            "  }\n"
            "]\n\n"
            "Return ONLY the JSON array."
        )

        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": debate_prompt}],
                model=ModelTier.SONNET,
                system=(
                    f"You are the elimination debate moderator for the {self.name} sublab. "
                    "Your job is to rigorously rank root cause hypotheses by plausibility "
                    "and remediation feasibility, eliminating weak candidates."
                ),
            )
            text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            cleaned = text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [ln for ln in lines if not ln.strip().startswith("```")]
                cleaned = "\n".join(lines)
            rounds = json.loads(cleaned)
            if isinstance(rounds, list):
                return rounds
        except Exception as exc:
            logger.warning("[%s] Elimination debate failed: %s", self.name, exc)

        return []

    # ------------------------------------------------------------------
    # Structured synthesis
    # ------------------------------------------------------------------

    async def _synthesize(
        self,
        query: str,
        reports: list[DivisionReport],
        debate_rounds: list[dict[str, Any]],
    ) -> FinalReport:
        """Synthesise findings into the six assay troubleshooting report sections.

        Produces structured output with ranked root causes, protocol
        modification checklists, and positive control recommendations.
        """
        all_claims: list[Claim] = []
        all_evidence: list[Any] = []

        report_texts: list[str] = []
        for r in reports:
            report_texts.append(
                f"### {r.division_name}\n"
                f"Confidence: {r.confidence.level.value} ({r.confidence.score})\n"
                f"Synthesis: {r.synthesis[:1500]}\n"
            )
            for sr in r.specialist_results:
                all_claims.extend(sr.findings)
                for claim in sr.findings:
                    all_evidence.extend(claim.supporting_evidence)

        # Build debate context for the synthesis prompt.
        debate_context = ""
        if debate_rounds:
            final_round = debate_rounds[-1] if debate_rounds else {}
            ranked = final_round.get("ranked_causes", [])
            if ranked:
                debate_context = "\n\nElimination debate results (ranked root causes):\n"
                for rc in ranked:
                    debate_context += (
                        f"  {rc.get('rank', '?')}. {rc.get('cause', 'unknown')} "
                        f"(plausibility: {rc.get('plausibility', '?')}, "
                        f"fix feasibility: {rc.get('remediation_feasibility', '?')})\n"
                        f"     Recommended fix: {rc.get('recommended_fix', 'N/A')}\n"
                    )
            else:
                n_rounds = len(debate_rounds)
                debate_context = f"\n\nElimination debate ran {n_rounds} round(s)."

        synthesis_prompt = (
            f"You are synthesising an assay troubleshooting report.\n\n"
            f"Original problem: {query}\n\n"
            f"Division reports:\n{''.join(report_texts)}\n"
            f"{debate_context}\n\n"
            "Produce a JSON object with exactly these six keys matching the "
            "report sections:\n\n"
            "{\n"
            '  "problem_description": "Clear description of the reported issue, '
            "the assay type, key parameters, and observed vs expected behaviour.\",\n"
            '  "potential_root_causes": [\n'
            "    {\n"
            '      "rank": 1,\n'
            '      "cause": "description",\n'
            '      "plausibility": 0.85,\n'
            '      "category": "signal_noise|variability|expression|protocol|reagent|biological",\n'
            '      "evidence_summary": "supporting evidence"\n'
            "    }\n"
            "  ],\n"
            '  "data_analysis": "Summary of expression data, functional genomics '
            "findings, and any quantitative analysis relevant to diagnosis.\",\n"
            '  "recommended_solutions": [\n'
            "    {\n"
            '      "solution": "specific actionable fix",\n'
            '      "addresses_cause": 1,\n'
            '      "feasibility": "high|medium|low",\n'
            '      "estimated_effort": "brief effort description"\n'
            "    }\n"
            "  ],\n"
            '  "protocol_modifications": [\n'
            "    {\n"
            '      "step": "protocol step to modify",\n'
            '      "current": "current approach",\n'
            '      "proposed": "proposed change",\n'
            '      "rationale": "why this should help"\n'
            "    }\n"
            "  ],\n"
            '  "positive_controls": [\n'
            "    {\n"
            '      "control": "control description",\n'
            '      "purpose": "what it validates",\n'
            '      "expected_result": "expected outcome"\n'
            "    }\n"
            "  ],\n"
            '  "executive_summary": "2-3 paragraph summary of the diagnosis and '
            'recommended action plan."\n'
            "}\n\n"
            "Return ONLY the JSON object."
        )

        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": synthesis_prompt}],
                model=ModelTier.SONNET,
                system=(
                    f"You are the synthesis engine for the {self.name} sublab. "
                    "Produce a structured troubleshooting report with ranked root causes, "
                    "actionable protocol modifications, and positive control recommendations."
                ),
            )
            text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            cleaned = text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [ln for ln in lines if not ln.strip().startswith("```")]
                cleaned = "\n".join(lines)
            synthesis = json.loads(cleaned)

            # Build evidence_synthesis dict from the structured sections.
            evidence_synthesis: dict[str, Any] = {
                "Problem Description": synthesis.get("problem_description", ""),
                "Potential Root Causes": synthesis.get("potential_root_causes", []),
                "Data Analysis": synthesis.get("data_analysis", ""),
                "Recommended Solutions": synthesis.get("recommended_solutions", []),
                "Protocol Modifications": synthesis.get("protocol_modifications", []),
                "Positive Controls": synthesis.get("positive_controls", []),
            }

            # Derive recommended_experiments from solutions and protocol mods.
            recommended_experiments: list[dict[str, str]] = []
            for sol in synthesis.get("recommended_solutions", []):
                recommended_experiments.append({
                    "experiment": sol.get("solution", ""),
                    "rationale": f"Addresses root cause #{sol.get('addresses_cause', '?')}",
                    "feasibility": sol.get("feasibility", "medium"),
                })

            # Compute overall confidence from root cause plausibilities.
            root_causes = synthesis.get("potential_root_causes", [])
            top_plausibility = root_causes[0].get("plausibility", 0.5) if root_causes else 0.5
            limitations = []
            if top_plausibility < 0.6:
                limitations.append(
                    "Top root cause plausibility is below 0.6 — diagnosis is uncertain. "
                    "Consider providing additional experimental data."
                )
            if len(root_causes) > 3:
                limitations.append(
                    f"{len(root_causes)} candidate root causes remain — "
                    "further investigation may be needed to narrow the diagnosis."
                )

            return FinalReport(
                query_id=self._query_id,
                user_query=query,
                executive_summary=synthesis.get("executive_summary", ""),
                evidence_synthesis=evidence_synthesis,
                key_findings=all_claims[:20],
                risk_assessment={
                    "diagnostic_confidence": top_plausibility,
                    "num_candidate_causes": len(root_causes),
                },
                recommended_experiments=recommended_experiments,
                limitations=limitations,
                provenance_chain=all_evidence[:50],
            )

        except Exception as exc:
            logger.error("[%s] Synthesis failed: %s", self.name, exc)
            return FinalReport(
                query_id=self._query_id,
                user_query=query,
                executive_summary=f"Synthesis failed: {exc}",
                key_findings=all_claims[:10],
                limitations=[f"Synthesis error: {exc}"],
                provenance_chain=all_evidence[:20],
            )
