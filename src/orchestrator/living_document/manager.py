"""Document Manager — bridges the pipeline, WorldModel, and LivingDocument.

Listens to pipeline events and automatically updates the living document
at key milestones.  Also synthesizes WorldModel data into narrative sections.
"""

from __future__ import annotations

import logging
from typing import Any

from src.utils.llm import LLMClient
from src.utils.types import (
    Claim,
    ConfidenceLevel,
    DivisionReport,
    FinalReport,
)

from .document import (
    DocumentVersion,
    LivingDocument,
    SectionType,
)

logger = logging.getLogger("lumi.living_document.manager")


class DocumentManager:
    """Manages the lifecycle of a :class:`LivingDocument` through the pipeline.

    Automatically creates and evolves document versions at key pipeline
    milestones:
    - After intake (background + hypothesis)
    - After intelligence briefing (background update)
    - After analytical execution (findings per division)
    - After review panel (contradictions, open questions)
    - After HITL (human feedback section)
    - After synthesis (executive summary, recommendations)
    """

    def __init__(self, query_id: str = "") -> None:
        self.document = LivingDocument(query_id=query_id)
        self.llm = LLMClient()

    # ------------------------------------------------------------------
    # Pipeline milestone hooks
    # ------------------------------------------------------------------

    async def on_intake(self, research_brief: dict) -> DocumentVersion:
        """Called after Phase 1 (Intake).  Creates the initial document."""
        target = research_brief.get("target", "Unknown target")
        disease = research_brief.get("disease", "")
        scope = research_brief.get("scope", "")
        query = research_brief.get("original_query", "")

        background = (
            f"**Research Query:** {query}\n\n"
            f"**Target:** {target}\n"
        )
        if disease:
            background += f"**Disease/Indication:** {disease}\n"
        background += f"\n**Scope:** {scope}\n"

        hypothesis = (
            f"Evaluating {target}"
            + (f" in the context of {disease}" if disease else "")
            + " using multi-agent scientific analysis."
        )

        return self.document.evolve(
            updates={
                SectionType.BACKGROUND: background,
                SectionType.HYPOTHESIS: hypothesis,
            },
            author="cso_orchestrator",
            trigger="phase_1_intake",
        )

    async def on_intelligence(self, intel_brief: dict) -> DocumentVersion:
        """Called after Phase 2 (Intelligence Briefing)."""
        landscape = intel_brief.get("field_landscape", "")
        feasibility = intel_brief.get("feasibility", "")
        data_availability = intel_brief.get("data_availability", "")
        recommended = intel_brief.get("recommended_divisions", [])

        content_parts = []
        if landscape:
            content_parts.append(f"**Field Landscape:** {landscape}")
        if feasibility:
            content_parts.append(f"**Feasibility Assessment:** {feasibility}")
        if data_availability:
            content_parts.append(f"**Data Availability:** {data_availability}")
        if recommended:
            content_parts.append(
                f"**Recommended Divisions:** {', '.join(recommended)}"
            )

        bg_update = "\n\n".join(content_parts) if content_parts else ""

        if bg_update:
            # Append to existing background
            current = self.document.current
            if current:
                existing_bg = ""
                bg_section = current.get_section(SectionType.BACKGROUND)
                if bg_section:
                    existing_bg = bg_section.content
                bg_update = existing_bg + "\n\n---\n\n### Intelligence Briefing\n\n" + bg_update

            return self.document.evolve(
                updates={SectionType.BACKGROUND: bg_update},
                author="chief_of_staff",
                trigger="phase_2_intelligence",
            )

        return self.document.current or self.document.create_version(
            sections=[], trigger="phase_2_intelligence_noop"
        )

    async def on_analytical_complete(
        self, reports: list[DivisionReport]
    ) -> DocumentVersion:
        """Called after Phase 5 (Analytical Execution).

        Creates a FINDINGS section for each division's results.
        """
        updates: dict[SectionType, str] = {}
        findings_parts: list[str] = []
        contradictions: list[str] = []
        open_questions: list[str] = []

        for report in reports:
            div_name = report.division_name
            confidence = report.confidence

            section_text = f"### {div_name}\n"
            section_text += f"_Confidence: {confidence.level.value} ({confidence.score:.0%})_\n\n"

            if report.synthesis:
                section_text += report.synthesis[:2000] + "\n\n"

            # Extract key claims
            claims = []
            for sr in report.specialist_results:
                claims.extend(sr.findings)

            if claims:
                section_text += "**Key Claims:**\n"
                for claim in claims[:10]:
                    bullet = f"- [{claim.confidence.score:.0%}] {claim.claim_text[:200]}"
                    section_text += bullet + "\n"
                    # Check for low confidence
                    if claim.confidence.level in (ConfidenceLevel.LOW, ConfidenceLevel.INSUFFICIENT):
                        open_questions.append(
                            f"[{div_name}] Low confidence ({claim.confidence.score:.0%}): "
                            f"{claim.claim_text[:150]}"
                        )

            # Check for caveats
            if confidence.caveats:
                for caveat in confidence.caveats:
                    contradictions.append(f"[{div_name}] {caveat}")

            findings_parts.append(section_text)

        updates[SectionType.FINDINGS] = "\n---\n\n".join(findings_parts)

        if contradictions:
            updates[SectionType.CONTRADICTIONS] = "\n".join(
                f"- {c}" for c in contradictions
            )

        if open_questions:
            updates[SectionType.OPEN_QUESTIONS] = "\n".join(
                f"- {q}" for q in open_questions
            )

        return self.document.evolve(
            updates=updates,
            author="division_leads",
            trigger="phase_5_analytical_complete",
        )

    async def on_review(self, verdict: Any) -> DocumentVersion:
        """Called after Phase 7 (Review Panel)."""
        verdict_type = getattr(verdict, "verdict", None)
        verdict_str = verdict_type.value if verdict_type else str(verdict_type)
        issues = getattr(verdict, "issues", [])
        missing = getattr(verdict, "missing_analyses", [])
        assessment = getattr(verdict, "confidence_assessment", "")

        parts = [f"**Review Verdict:** {verdict_str}\n"]

        if assessment:
            parts.append(f"**Assessment:** {assessment}\n")

        if issues:
            parts.append("**Issues Identified:**")
            for issue in issues:
                if isinstance(issue, dict):
                    desc = issue.get("description", str(issue))
                    priority = issue.get("priority", "")
                    parts.append(f"- [{priority}] {desc}")
                else:
                    parts.append(f"- {issue}")

        if missing:
            parts.append("\n**Missing Analyses:**")
            for m in missing:
                parts.append(f"- {m}")

        # Add to contradictions/open questions based on review
        updates: dict[SectionType, str] = {}

        current = self.document.current
        existing_contradictions = ""
        if current:
            c_sec = current.get_section(SectionType.CONTRADICTIONS)
            if c_sec:
                existing_contradictions = c_sec.content

        if issues:
            issue_text = "\n".join(
                f"- [Review] {i.get('description', str(i))}" if isinstance(i, dict) else f"- [Review] {i}"
                for i in issues
            )
            if existing_contradictions:
                updates[SectionType.CONTRADICTIONS] = (
                    existing_contradictions + "\n\n### Review Panel Issues\n" + issue_text
                )
            else:
                updates[SectionType.CONTRADICTIONS] = "### Review Panel Issues\n" + issue_text

        return self.document.evolve(
            updates=updates,
            author="review_panel",
            trigger="phase_7_review",
        )

    async def on_hitl_feedback(
        self, human_feedback: dict[str, str], caveated_claims: list[Claim]
    ) -> DocumentVersion:
        """Called after HITL routing resolves."""
        parts: list[str] = []

        if human_feedback:
            parts.append("### Expert Feedback Received\n")
            for req_id, feedback in human_feedback.items():
                parts.append(f"- **{req_id}:** {feedback}")

        if caveated_claims:
            parts.append("\n### Findings Included With Caveats\n")
            parts.append(
                "_The following findings did not receive expert review "
                "within the timeout window and are included with reduced confidence._\n"
            )
            for claim in caveated_claims:
                parts.append(
                    f"- [{claim.confidence.score:.0%}] {claim.claim_text[:200]}"
                )

        content = "\n".join(parts) if parts else "_No human feedback required._"

        return self.document.evolve(
            updates={SectionType.HUMAN_FEEDBACK: content},
            author="hitl_router",
            trigger="hitl_complete",
        )

    async def on_synthesis(self, report: FinalReport) -> DocumentVersion:
        """Called after Phase 9 (Synthesis).  Final document version."""
        updates: dict[SectionType, str] = {}

        # Executive summary
        if report.executive_summary:
            updates[SectionType.EXECUTIVE_SUMMARY] = report.executive_summary

        # Risk assessment
        if report.risk_assessment:
            risk_parts = []
            for key, value in report.risk_assessment.items():
                risk_parts.append(f"**{key.replace('_', ' ').title()}:** {value}")
            updates[SectionType.RISK_ASSESSMENT] = "\n\n".join(risk_parts)

        # Recommendations from experiments
        if report.recommended_experiments:
            exp_parts = []
            for exp in report.recommended_experiments:
                if isinstance(exp, dict):
                    title = exp.get("title", "Unnamed experiment")
                    rationale = exp.get("rationale", "")
                    priority = exp.get("priority", "")
                    exp_parts.append(
                        f"### {title}\n"
                        f"_Priority: {priority}_\n\n"
                        f"{rationale}\n"
                    )
            if exp_parts:
                updates[SectionType.EXPERIMENTAL_PLAN] = "\n---\n\n".join(exp_parts)

        # Recommendations
        if report.molecular_design_candidates:
            candidates_text = "### Molecular Design Candidates\n\n"
            for i, cand in enumerate(report.molecular_design_candidates[:5], 1):
                if isinstance(cand, dict):
                    candidates_text += f"**Candidate {i}:** {cand}\n\n"
            updates[SectionType.RECOMMENDATIONS] = candidates_text

        # Limitations
        if report.limitations:
            current = self.document.current
            existing_oq = ""
            if current:
                oq_sec = current.get_section(SectionType.OPEN_QUESTIONS)
                if oq_sec:
                    existing_oq = oq_sec.content

            limitations_text = "\n### Limitations\n" + "\n".join(
                f"- {lim}" for lim in report.limitations
            )
            updates[SectionType.OPEN_QUESTIONS] = (
                (existing_oq + "\n\n" if existing_oq else "") + limitations_text
            )

        # Evidence chain summary
        if report.provenance_chain:
            sources = set()
            for ev in report.provenance_chain[:30]:
                sources.add(f"{ev.source_db}:{ev.source_id}")
            evidence_text = (
                f"**Sources consulted:** {len(report.provenance_chain)}\n\n"
                + "\n".join(f"- `{s}`" for s in sorted(sources)[:20])
            )
            updates[SectionType.EVIDENCE] = evidence_text

        return self.document.evolve(
            updates=updates,
            author="cso_orchestrator",
            trigger="phase_9_synthesis",
        )

    # ------------------------------------------------------------------
    # Context helpers
    # ------------------------------------------------------------------

    def get_agent_context(
        self,
        relevant_types: list[SectionType] | None = None,
        max_chars: int = 8000,
    ) -> str:
        """Get document context formatted for agent system prompts."""
        return self.document.get_context_for_agent(
            relevant_types=relevant_types,
            max_chars=max_chars,
        )

    def render(self) -> str:
        """Render the current document as Markdown."""
        return self.document.render_markdown()
