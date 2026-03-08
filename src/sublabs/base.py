"""Base Sublab class -- focused agent teams for specific use cases.

A Sublab defines a lightweight, scoped pipeline that activates only the
agents, tools, and YOHAS phases relevant to a particular use case.

Each concrete sublab specifies:
- **agent_names** -- specialist subset relevant to the use case
- **tool_names** -- only required MCP tools for those agents
- **phases** -- simplified YOHAS phase sequence (not all 9)
- **division_names** -- which divisions are involved
- **debate_protocol** -- consensus mechanism for the domain
- **report_format** -- output structure tailored to use case
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any

from src.agents.base_agent import BaseAgent
from src.divisions.base_lead import DivisionLead
from src.utils.llm import LLMClient, ModelTier
from src.utils.types import (
    Claim,
    ConfidenceAssessment,
    ConfidenceLevel,
    DivisionReport,
    ExecutionPlan,
    FinalReport,
    Phase,
    Priority,
    Task,
)

logger = logging.getLogger("lumi.sublabs.base")


class Sublab:
    """Base class for all sublabs.

    Subclasses must set the class-level attributes that define the sublab's
    scope and override :meth:`_build_phases` to define the pipeline.
    """

    # --- Subclass must set these -------------------------------------------
    name: str = ""
    description: str = ""
    agent_names: list[str] = []
    tool_names: list[str] = []
    division_names: list[str] = []
    phases: list[str] = []
    debate_protocol: str = "majority"
    report_sections: list[str] = []
    examples: list[str] = []

    def __init__(
        self,
        divisions: dict[str, DivisionLead],
    ) -> None:
        self.llm = LLMClient()
        self._query_id: str = ""

        # Filter divisions to only those relevant to this sublab
        self.divisions: dict[str, DivisionLead] = {
            name: lead
            for name, lead in divisions.items()
            if name in self.division_names
        }

        # Collect the active agents from wired divisions.
        # Agent names in sublab configs use snake_case (e.g. "statistical_genetics")
        # while BaseAgent.name uses Title Case (e.g. "Statistical Genetics").
        # Normalise to lowercase-no-separators for matching.
        self.agents: list[BaseAgent] = []
        active_normalised = {self._normalise(n) for n in self.agent_names}
        for lead in self.divisions.values():
            for agent in lead.specialist_agents:
                if self._normalise(agent.name) in active_normalised:
                    self.agents.append(agent)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(self, query: str) -> FinalReport:
        """Execute the sublab pipeline for *query*.

        Steps:
        1. Build a scoped execution plan (subset of YOHAS phases).
        2. Dispatch phases to relevant divisions.
        3. Run debate protocol across agent findings.
        4. Synthesise and return a FinalReport.
        """
        start_time = time.time()
        self._query_id = f"sl_{uuid.uuid4().hex[:12]}"

        logger.info(
            "[%s] Starting sublab pipeline — query_id=%s",
            self.name, self._query_id,
        )

        # 1. Build scoped plan
        plan = self._build_execution_plan(query)

        # 2. Execute phases
        reports = await self._execute_phases(plan)

        # 3. Debate
        debate_rounds = await self._run_debate(query, reports)

        # 4. Synthesise
        report = await self._synthesize(query, reports, debate_rounds)

        report.query_id = self._query_id
        report.user_query = query
        report.total_duration_seconds = time.time() - start_time
        report.total_cost = self.llm.get_cost()["total"]

        logger.info(
            "[%s] Pipeline complete — duration=%.1fs cost=$%.4f",
            self.name,
            report.total_duration_seconds,
            report.total_cost,
        )
        return report

    # ------------------------------------------------------------------
    # Pipeline building
    # ------------------------------------------------------------------

    def _build_execution_plan(self, query: str) -> ExecutionPlan:
        """Build a scoped execution plan using only the sublab's phases."""
        phase_objects = self._build_phases(query)

        return ExecutionPlan(
            query_id=self._query_id,
            user_query=query,
            confirmed_scope=f"{self.name}: {self.description}",
            phases=phase_objects,
            estimated_total_cost=sum(p.estimated_cost for p in phase_objects),
            includes_design=any("design" in p.name.lower() for p in phase_objects),
            includes_experimental=any("experiment" in p.name.lower() for p in phase_objects),
        )

    def _build_phases(self, query: str) -> list[Phase]:
        """Build the Phase objects for this sublab's pipeline.

        Subclasses should override this for custom phase logic. The
        default implementation creates one phase per division.
        """
        phase_objects: list[Phase] = []
        for i, div_name in enumerate(self.division_names):
            agents_in_div = [
                a.name for a in self.agents
                if a.division == div_name or a.name in self.agent_names
            ]
            phase_objects.append(
                Phase(
                    phase_id=i + 1,
                    name=f"{div_name} Analysis",
                    division=div_name,
                    agents=agents_in_div,
                    dependencies=[],
                    parallel_eligible=True,
                    priority=Priority.HIGH,
                    estimated_cost=1.5,
                )
            )
        return phase_objects

    # ------------------------------------------------------------------
    # Phase execution
    # ------------------------------------------------------------------

    async def _execute_phases(self, plan: ExecutionPlan) -> list[DivisionReport]:
        """Dispatch phases to divisions, respecting dependencies."""
        reports: list[DivisionReport] = []
        completed_ids: set[int] = set()
        remaining = list(plan.phases)

        while remaining:
            ready = [
                p for p in remaining
                if all(d in completed_ids for d in p.dependencies)
            ]
            still_waiting = [p for p in remaining if p not in ready]

            if not ready:
                logger.warning("[%s] Dependency deadlock — forcing remaining", self.name)
                ready = still_waiting
                still_waiting = []

            coros = [self._dispatch_phase(phase) for phase in ready]
            batch = await asyncio.gather(*coros, return_exceptions=True)

            for phase, result in zip(ready, batch):
                if isinstance(result, Exception):
                    logger.error("[%s] Phase '%s' failed: %s", self.name, phase.name, result)
                    reports.append(
                        DivisionReport(
                            division_id=f"div_{phase.phase_id}",
                            division_name=phase.division or "unknown",
                            lead_agent="sublab_fallback",
                            synthesis=f"Phase failed: {result}",
                            confidence=ConfidenceAssessment(
                                level=ConfidenceLevel.INSUFFICIENT, score=0.0,
                            ),
                        )
                    )
                else:
                    reports.append(result)
                completed_ids.add(phase.phase_id)

            remaining = still_waiting

        return reports

    async def _dispatch_phase(self, phase: Phase) -> DivisionReport:
        """Dispatch a phase to the appropriate division lead."""
        div_name = phase.division or ""
        lead = self.divisions.get(div_name)

        if lead is None:
            for name, div_lead in self.divisions.items():
                if name.lower() == div_name.lower():
                    lead = div_lead
                    break

        if lead is None:
            return DivisionReport(
                division_id=f"div_{phase.phase_id}",
                division_name=div_name,
                lead_agent="sublab_fallback",
                synthesis=f"Division '{div_name}' not available in this sublab.",
                confidence=ConfidenceAssessment(
                    level=ConfidenceLevel.INSUFFICIENT, score=0.0,
                ),
            )

        task = Task(
            task_id=f"sl_{phase.phase_id}_{uuid.uuid4().hex[:6]}",
            description=phase.name,
            division=div_name,
            priority=phase.priority,
        )

        return await lead.execute_division_task(task)

    # ------------------------------------------------------------------
    # Debate protocol
    # ------------------------------------------------------------------

    async def _run_debate(
        self,
        query: str,
        reports: list[DivisionReport],
    ) -> list[dict[str, Any]]:
        """Run the sublab's debate protocol across agent findings.

        The default implementation collects all claims and uses the LLM
        to run a structured debate. Subclasses can override for domain-
        specific consensus mechanisms.
        """
        all_claims: list[Claim] = []
        for r in reports:
            for sr in r.specialist_results:
                all_claims.extend(sr.findings)

        if len(all_claims) < 2:
            return []

        claims_text = "\n".join(
            f"- [{c.agent_id}] {c.claim_text} (confidence: {c.confidence.level.value})"
            for c in all_claims
        )

        debate_prompt = (
            f"You are moderating a scientific debate among specialist agents.\n\n"
            f"Query: {query}\n\n"
            f"Claims from agents:\n{claims_text}\n\n"
            f"Debate protocol: {self.debate_protocol}\n\n"
            f"For each claim, determine whether other agents' findings "
            f"support, challenge, or are neutral toward it. Return a JSON "
            f"array of debate round objects, each with:\n"
            f"- \"round\": integer\n"
            f"- \"agent_id\": which agent is speaking\n"
            f"- \"position\": \"support\" | \"challenge\" | \"neutral\"\n"
            f"- \"argument\": the agent's position statement\n"
            f"- \"evidence\": list of evidence IDs cited\n\n"
            f"Return ONLY the JSON array."
        )

        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": debate_prompt}],
                model=ModelTier.SONNET,
                system=f"You are the debate moderator for the {self.name} sublab.",
            )
            import json
            text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            # Parse JSON from response
            cleaned = text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [ln for ln in lines if not ln.strip().startswith("```")]
                cleaned = "\n".join(lines)
            rounds = json.loads(cleaned)
            if isinstance(rounds, list):
                return rounds
        except Exception as exc:
            logger.warning("[%s] Debate failed: %s", self.name, exc)

        return []

    # ------------------------------------------------------------------
    # Synthesis
    # ------------------------------------------------------------------

    async def _synthesize(
        self,
        query: str,
        reports: list[DivisionReport],
        debate_rounds: list[dict[str, Any]],
    ) -> FinalReport:
        """Synthesise division reports and debate into a FinalReport."""
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

        debate_summary = ""
        if debate_rounds:
            support = sum(1 for d in debate_rounds if d.get("position") == "support")
            challenge = sum(1 for d in debate_rounds if d.get("position") == "challenge")
            neutral = sum(1 for d in debate_rounds if d.get("position") == "neutral")
            debate_summary = (
                f"\n\nDebate summary: {support} support, "
                f"{challenge} challenge, {neutral} neutral positions."
            )

        import json
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

            return FinalReport(
                query_id=self._query_id,
                user_query=query,
                executive_summary=synthesis.get("executive_summary", ""),
                evidence_synthesis=synthesis.get("evidence_synthesis", {}),
                key_findings=all_claims[:20],
                risk_assessment=synthesis.get("risk_assessment", {}),
                recommended_experiments=synthesis.get("recommended_experiments", []),
                limitations=synthesis.get("limitations", []),
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

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_info(self) -> dict[str, Any]:
        """Return sublab metadata for UI display."""
        return {
            "name": self.name,
            "description": self.description,
            "agents": self.agent_names,
            "divisions": self.division_names,
            "phases": self.phases,
            "debate_protocol": self.debate_protocol,
            "report_sections": self.report_sections,
            "examples": self.examples,
        }

    @staticmethod
    def _normalise(name: str) -> str:
        """Normalise an agent name for comparison.

        ``"Statistical Genetics"`` and ``"statistical_genetics"`` both
        become ``"statisticalgenetics"``.
        """
        return name.lower().replace("_", "").replace("-", "").replace(" ", "")
