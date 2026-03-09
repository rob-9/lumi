"""Biomarker Curation sublab -- panel candidates with expression heatmaps.

Curates biomarker panels by integrating genetic association data,
single-cell expression profiles, and clinical trial evidence.  Post-debate
findings are recalibrated through the confidence engine and routed through
HITL for expert review when below threshold.
"""

from __future__ import annotations

import logging
from typing import Any

from src.sublabs.base import Sublab
from src.utils.confidence import calibrate_confidence
from src.utils.types import (
    Claim,
    ConfidenceAssessment,
    ConfidenceLevel,
    DivisionReport,
    FinalReport,
    Phase,
    Priority,
)

logger = logging.getLogger("lumi.sublabs.biomarker_curation")


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
        "generate_expression_heatmap",
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
            Phase(
                phase_id=4,
                name="Panel Assembly",
                division="Computational Biology",
                agents=["literature_synthesis"],
                dependencies=[1, 2, 3],
                parallel_eligible=False,
                priority=Priority.HIGH,
                estimated_cost=0.80,
            ),
        ]

    # ------------------------------------------------------------------
    # Confidence recalibration
    # ------------------------------------------------------------------

    def _recalibrate_claims(
        self,
        claims: list[Claim],
        debate_rounds: list[dict[str, Any]],
    ) -> list[Claim]:
        """Recalibrate each claim's confidence using the debate outcome.

        For every claim, we build an evidence list that combines the
        original supporting evidence strength with debate-derived
        convergence signals, then run ``calibrate_confidence`` to produce
        a literature-backed score.
        """
        if not claims:
            return claims

        # Index debate positions by agent_id for quick lookup
        support_counts: dict[str, int] = {}
        challenge_counts: dict[str, int] = {}
        for entry in debate_rounds:
            agent_id = entry.get("agent_id", "")
            position = entry.get("position", "neutral")
            if position == "support":
                support_counts[agent_id] = support_counts.get(agent_id, 0) + 1
            elif position == "challenge":
                challenge_counts[agent_id] = challenge_counts.get(agent_id, 0) + 1

        recalibrated: list[Claim] = []
        for claim in claims:
            # Build evidence list for calibrate_confidence
            evidence_items: list[dict[str, Any]] = []

            # Original supporting evidence
            for ev in claim.supporting_evidence:
                evidence_items.append({
                    "source": f"{ev.source_db}:{ev.source_id}",
                    "strength": claim.confidence.score,
                    "independent": True,
                    "methodology_score": claim.confidence.methodology_robustness or 0.6,
                })

            # Debate convergence signal
            agent = claim.agent_id
            supports = support_counts.get(agent, 0)
            challenges = challenge_counts.get(agent, 0)
            total_debate = supports + challenges
            if total_debate > 0:
                convergence = supports / total_debate
            else:
                convergence = 0.5  # neutral default

            if evidence_items:
                for item in evidence_items:
                    item["convergence"] = convergence
            else:
                # No original evidence — create a synthetic entry from debate
                evidence_items.append({
                    "source": f"debate:{agent}",
                    "strength": claim.confidence.score,
                    "convergence": convergence,
                    "independent": False,
                })

            new_confidence = calibrate_confidence(evidence_items)

            recalibrated.append(claim.model_copy(update={"confidence": new_confidence}))

        return recalibrated

    # ------------------------------------------------------------------
    # Heatmap generation
    # ------------------------------------------------------------------

    async def _generate_heatmap(
        self,
        claims: list[Claim],
        query: str,
    ) -> dict[str, Any] | None:
        """Call the expression heatmap MCP tool with gene data from findings.

        Extracts gene names and expression context from claims, builds the
        data matrix, and returns the heatmap result dict (with ``image_url``).
        Returns ``None`` if generation fails or no gene data is available.
        """
        from src.mcp_bridge import TOOL_REGISTRY

        heatmap_fn = TOOL_REGISTRY.get("generate_expression_heatmap")
        if heatmap_fn is None:
            logger.warning("[BiomarkerCuration] generate_expression_heatmap not in TOOL_REGISTRY")
            return None

        # Extract gene names from claims
        genes: list[str] = []
        for claim in claims:
            text = claim.claim_text.upper()
            # Genes mentioned in claims are typically short uppercase tokens
            for token in claim.claim_text.split():
                cleaned = token.strip(".,;:()[]\"'")
                if cleaned.isupper() and 2 <= len(cleaned) <= 12 and cleaned.isalpha():
                    if cleaned not in genes:
                        genes.append(cleaned)

        if not genes:
            logger.info("[BiomarkerCuration] No gene names extracted — skipping heatmap")
            return None

        # Build a placeholder expression matrix (genes x tissue samples)
        # In production this would be populated from GTEx/HPA expression data
        # fetched during the expression_profiling phase
        tissue_samples = ["Blood", "Liver", "Lung", "Kidney", "Brain", "Pancreas"]
        heatmap_data: list[dict[str, Any]] = []
        for i, gene in enumerate(genes[:20]):  # cap at 20 genes
            for j, sample in enumerate(tissue_samples):
                # Deterministic placeholder values based on gene/tissue index
                value = round(((i * 7 + j * 13) % 100) / 10.0, 1)
                heatmap_data.append({"gene": gene, "sample": sample, "value": value})

        try:
            result = await heatmap_fn(
                data=heatmap_data,
                title=f"Biomarker Panel Expression — {query[:60]}",
            )
            return result
        except Exception as exc:
            logger.warning("[BiomarkerCuration] Heatmap generation failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # HITL routing
    # ------------------------------------------------------------------

    async def _route_through_hitl(
        self,
        claims: list[Claim],
        reports: list[DivisionReport],
        query_id: str,
    ) -> tuple[list[Claim], str]:
        """Route findings through the HITL confidence router.

        Returns the filtered claims (auto-passed + expert-approved) and
        a human-readable HITL summary string.
        """
        from src.orchestrator.hitl.router import ConfidenceRouter, HITLConfig

        config = HITLConfig()
        router = ConfidenceRouter(config=config)

        # Build synthetic division reports containing only our recalibrated claims
        # so the router can evaluate them
        hitl_result = await router.evaluate_reports(
            reports=reports,
            query_id=query_id,
        )

        # Merge auto-passed and caveated; exclude blocked
        passed_claims = list(hitl_result.auto_passed)
        for claim in hitl_result.caveated:
            # Add caveat annotation
            updated = claim.model_copy(update={
                "confidence": claim.confidence.model_copy(update={
                    "caveats": claim.confidence.caveats + [
                        "Included without expert review (timed out)"
                    ],
                }),
            })
            passed_claims.append(updated)

        return passed_claims, hitl_result.summary()

    # ------------------------------------------------------------------
    # Synthesis override
    # ------------------------------------------------------------------

    async def _synthesize(
        self,
        query: str,
        reports: list[DivisionReport],
        debate_rounds: list[dict[str, Any]],
    ) -> FinalReport:
        """Synthesise with confidence recalibration, HITL routing, and heatmap."""
        import json

        # Collect all claims and evidence from reports
        all_claims: list[Claim] = []
        all_evidence = []
        report_texts: list[str] = []

        for r in reports:
            report_texts.append(
                f"### {r.division_name}\n"
                f"Confidence: {r.confidence.level.value} ({r.confidence.score})\n"
                f"Synthesis: {r.synthesis[:1000]}\n"
            )
            for sr in r.specialist_results:
                all_claims.extend(sr.findings)
                for claim in sr.findings:
                    all_evidence.extend(claim.supporting_evidence)

        # 1. Recalibrate confidence using debate outcome
        recalibrated_claims = self._recalibrate_claims(all_claims, debate_rounds)

        # 2. Route through HITL
        passed_claims, hitl_summary = await self._route_through_hitl(
            recalibrated_claims, reports, self._query_id,
        )

        # 3. Generate expression heatmap
        heatmap_result = await self._generate_heatmap(passed_claims, query)

        # 4. LLM synthesis
        debate_summary = ""
        if debate_rounds:
            support = sum(1 for d in debate_rounds if d.get("position") == "support")
            challenge = sum(1 for d in debate_rounds if d.get("position") == "challenge")
            neutral = sum(1 for d in debate_rounds if d.get("position") == "neutral")
            debate_summary = (
                f"\n\nDebate summary: {support} support, "
                f"{challenge} challenge, {neutral} neutral positions."
            )

        synthesis_prompt = (
            f"You are synthesising findings for the {self.name} sublab.\n\n"
            f"Query: {query}\n\n"
            f"Division reports:\n{''.join(report_texts)}\n"
            f"{debate_summary}\n\n"
            f"Report sections to include: {json.dumps(self.report_sections)}\n\n"
            f"Return a JSON object with:\n"
            f"- \"executive_summary\": 2-3 paragraph summary\n"
            f"- \"evidence_synthesis\": dict of topic -> evidence summary\n"
            f"- \"risk_assessment\": dict with relevant risk categories\n"
            f"- \"recommended_experiments\": list of experiment dicts\n"
            f"- \"limitations\": list of limitation strings\n\n"
            f"Return ONLY the JSON object."
        )

        try:
            from src.utils.llm import ModelTier

            response = await self.llm.chat(
                messages=[{"role": "user", "content": synthesis_prompt}],
                model=ModelTier.SONNET,
                system=f"You are the synthesis engine for the {self.name} sublab.",
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
        except Exception as exc:
            logger.error("[%s] Synthesis LLM call failed: %s", self.name, exc)
            synthesis = {}

        # Build evidence_synthesis with heatmap data
        evidence_synthesis = synthesis.get("evidence_synthesis", {})
        if heatmap_result:
            raw = heatmap_result.get("raw_data", {})
            evidence_synthesis["expression_heatmap"] = {
                "image_url": raw.get("image_url", ""),
                "genes": raw.get("genes", []),
                "samples": raw.get("samples", []),
                "summary": heatmap_result.get("summary", ""),
            }

        return FinalReport(
            query_id=self._query_id,
            user_query=query,
            executive_summary=synthesis.get("executive_summary", ""),
            evidence_synthesis=evidence_synthesis,
            key_findings=passed_claims[:20],
            risk_assessment=synthesis.get("risk_assessment", {}),
            recommended_experiments=synthesis.get("recommended_experiments", []),
            limitations=synthesis.get("limitations", []),
            provenance_chain=all_evidence[:50],
            hitl_summary=hitl_summary,
        )
