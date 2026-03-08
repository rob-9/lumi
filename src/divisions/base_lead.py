"""
Division Lead base class for the Lumi Virtual Lab swarm.

A :class:`DivisionLead` sits between the CSO Orchestrator (Tier 1) and
the specialist agents (Tier 3).  It receives a division-level task,
decomposes it into specialist sub-tasks via an LLM call, dispatches
them (respecting parallelism and dependencies), collects results, and
synthesises a cohesive :class:`DivisionReport`.
"""

from __future__ import annotations

import asyncio
import json
import logging
import textwrap
import uuid
from typing import Any

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier
from src.utils.types import (
    AgentResult,
    ConfidenceAssessment,
    ConfidenceLevel,
    DivisionReport,
    Task,
)

logger = logging.getLogger("lumi.divisions.base_lead")


class DivisionLead(BaseAgent):
    """Base class for division leads.

    Decomposes tasks, dispatches to specialists, synthesises results.
    """

    def __init__(
        self,
        name: str,
        division_name: str,
        system_prompt: str,
        specialist_agents: list[BaseAgent],
        model: ModelTier = ModelTier.SONNET,
        max_dynamic_specialists: int = 5,
    ):
        super().__init__(
            name=name,
            system_prompt=system_prompt,
            model=model,
            division=division_name,
        )
        self.division_name = division_name
        self.specialist_agents = list(specialist_agents)
        self.max_dynamic_specialists = max_dynamic_specialists
        self._dynamic_specialist_count = 0

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def execute_division_task(self, task: Task) -> DivisionReport:
        """Execute a full division-level task.

        Steps:
        1. Decompose into specialist sub-tasks via LLM.
        2. Identify parallel vs sequential tasks.
        3. Execute parallel tasks with ``asyncio.gather``.
        4. Execute sequential tasks in dependency order.
        5. Collect all :class:`AgentResult` objects.
        6. Synthesise findings into a division report via LLM.
        7. Return :class:`DivisionReport`.
        """
        logger.info(
            "[%s] Starting division task: %s", self.division_name, task.task_id
        )

        # 1. Decompose
        sub_tasks = await self._decompose_task(task)
        if not sub_tasks:
            logger.warning("[%s] Decomposition produced zero sub-tasks", self.division_name)
            return self._empty_report(task)

        # 2+3+4. Execute in correct order
        results = await self._execute_sub_tasks(sub_tasks)

        # 6. Synthesise
        synthesis_text, confidence = await self._synthesize_results(task, results)

        # 7. Build report
        return DivisionReport(
            division_id=f"div_{self.division_name.lower().replace(' ', '_')}",
            division_name=self.division_name,
            lead_agent=self.name,
            specialist_results=results,
            synthesis=synthesis_text,
            confidence=confidence,
        )

    # ------------------------------------------------------------------
    # Task decomposition (LLM call)
    # ------------------------------------------------------------------

    async def _decompose_task(self, task: Task) -> list[Task]:
        """Use the LLM to decompose *task* into specialist sub-tasks.

        The LLM is asked to return a JSON array where each element has:
        - ``task_id``: unique sub-task identifier
        - ``description``: what the specialist should do
        - ``agent``: name of the specialist agent to assign
        - ``parallel``: whether this can run in parallel with others
        - ``depends_on``: list of sub-task IDs that must finish first
        """
        available_agents = [a.name for a in self.specialist_agents]

        decomposition_prompt = textwrap.dedent(f"""\
            You are the {self.division_name} Division Lead.

            Your available specialist agents are:
            {json.dumps(available_agents, indent=2)}

            You have received the following task from the CSO Orchestrator:

            Task ID: {task.task_id}
            Description: {task.description}
            Priority: {task.priority.value}

            Decompose this task into sub-tasks for your specialist agents.
            Return ONLY a JSON array (no markdown fences, no commentary) where each element has:
            - "task_id": a unique string like "sub_1", "sub_2", etc.
            - "description": what the specialist should do (be specific)
            - "agent": the name of the specialist agent to assign (must be one of the available agents listed above, or "dynamic" if a new specialist is needed)
            - "parallel": true if this sub-task can run concurrently with others, false if it must wait
            - "depends_on": a list of task_id strings that must complete before this sub-task starts (empty list if none)

            Guidelines:
            - Maximise parallelism where sub-tasks are independent.
            - Only mark a task as sequential (parallel=false) if it truly depends on another sub-task's output.
            - Be specific in descriptions so specialists know exactly what to do.
            - Assign the most appropriate specialist for each sub-task.
        """)

        messages = [{"role": "user", "content": decomposition_prompt}]

        try:
            response = await self.llm.chat(
                messages=messages,
                model=self.model,
                system=self.system_prompt,
            )

            response_text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )

            # Parse JSON from response (strip markdown fences if present)
            json_text = response_text.strip()
            if json_text.startswith("```"):
                # Remove fences
                lines = json_text.split("\n")
                lines = [ln for ln in lines if not ln.strip().startswith("```")]
                json_text = "\n".join(lines)

            sub_task_defs: list[dict[str, Any]] = json.loads(json_text)

        except (json.JSONDecodeError, Exception) as exc:
            logger.error(
                "[%s] Failed to parse decomposition response: %s",
                self.division_name,
                exc,
            )
            # Fallback: create a single sub-task assigned to the first available agent
            agent_name = available_agents[0] if available_agents else "unknown"
            sub_task_defs = [
                {
                    "task_id": "sub_fallback",
                    "description": task.description,
                    "agent": agent_name,
                    "parallel": True,
                    "depends_on": [],
                }
            ]

        # Convert dicts to Task objects
        sub_tasks: list[Task] = []
        for defn in sub_task_defs:
            sub_tasks.append(
                Task(
                    task_id=defn.get("task_id", f"sub_{uuid.uuid4().hex[:8]}"),
                    description=defn.get("description", ""),
                    division=self.division_name,
                    agent=defn.get("agent", ""),
                    priority=task.priority,
                    dependencies=defn.get("depends_on", []),
                )
            )

        logger.info(
            "[%s] Decomposed into %d sub-tasks: %s",
            self.division_name,
            len(sub_tasks),
            [t.task_id for t in sub_tasks],
        )
        return sub_tasks

    # ------------------------------------------------------------------
    # Sub-task execution (parallel + sequential)
    # ------------------------------------------------------------------

    async def _execute_sub_tasks(self, sub_tasks: list[Task]) -> list[AgentResult]:
        """Execute sub-tasks respecting dependency ordering.

        Tasks whose ``dependencies`` list is empty (or whose deps are
        already satisfied) are launched with staggered starts to avoid
        overwhelming the API.  Each specialist starts after a short delay
        from the previous one, but they still run concurrently.
        """
        results: list[AgentResult] = []
        completed_ids: set[str] = set()
        remaining = list(sub_tasks)

        while remaining:
            # Find tasks whose dependencies are all satisfied
            ready: list[Task] = []
            still_waiting: list[Task] = []

            for t in remaining:
                if all(dep in completed_ids for dep in t.dependencies):
                    ready.append(t)
                else:
                    still_waiting.append(t)

            if not ready:
                # Deadlock — force-execute everything remaining
                logger.warning(
                    "[%s] Dependency deadlock detected; forcing execution of %d tasks",
                    self.division_name,
                    len(still_waiting),
                )
                ready = still_waiting
                still_waiting = []

            # Stagger specialist launches: create tasks with increasing
            # delays so they don't all hit the API at the same instant
            async def _staggered_run(task: Task, delay: float) -> AgentResult:
                if delay > 0:
                    await asyncio.sleep(delay)
                return await self._run_specialist(task)

            stagger_interval = 3.0  # seconds between each specialist start
            coros = [
                _staggered_run(t, i * stagger_interval)
                for i, t in enumerate(ready)
            ]
            batch_results = await asyncio.gather(*coros, return_exceptions=True)

            for task_obj, result in zip(ready, batch_results):
                if isinstance(result, Exception):
                    logger.error(
                        "[%s] Specialist failed on %s: %s",
                        self.division_name,
                        task_obj.task_id,
                        result,
                    )
                    # Record a failure result
                    results.append(
                        AgentResult(
                            agent_id=task_obj.agent or "unknown",
                            task_id=task_obj.task_id,
                            raw_data={"error": str(result)},
                        )
                    )
                else:
                    results.append(result)
                completed_ids.add(task_obj.task_id)

            remaining = still_waiting

        return results

    async def _run_specialist(self, task: Task) -> AgentResult:
        """Route a sub-task to the appropriate specialist agent and execute."""
        agent_name = task.agent or ""

        # Try to find a matching specialist
        agent = self._get_agent_by_name(agent_name)

        if agent is None and agent_name == "dynamic":
            # Attempt to spawn a dynamic specialist
            agent = await self.spawn_specialist(
                name=f"Dynamic-{task.task_id}",
                system_prompt=(
                    f"You are a specialist agent dynamically created for the "
                    f"{self.division_name} division. Complete the assigned task "
                    f"using your tools and scientific reasoning."
                ),
                tools=[],
            )

        if agent is None:
            logger.warning(
                "[%s] No specialist found for '%s'; falling back to division lead",
                self.division_name,
                agent_name,
            )
            # Fall back to executing the task ourselves (the division lead)
            return await self.execute(task)

        return await agent.execute(task)

    # ------------------------------------------------------------------
    # Result synthesis (LLM call)
    # ------------------------------------------------------------------

    async def _synthesize_results(
        self, task: Task, results: list[AgentResult]
    ) -> tuple[str, ConfidenceAssessment]:
        """Use the LLM to synthesise specialist results into a cohesive narrative.

        Returns ``(synthesis_text, confidence_assessment)``.
        """
        # Build a summary of each specialist's findings
        specialist_summaries: list[str] = []
        for r in results:
            findings_text = "\n".join(
                f"  - {c.claim_text} (confidence: {c.confidence.level.value})"
                for c in r.findings
            ) or "  (no structured findings)"

            raw_response = r.raw_data.get("final_response", "")
            if raw_response:
                raw_response = raw_response[:1000]  # truncate for context window

            specialist_summaries.append(
                f"### Agent: {r.agent_id} (task: {r.task_id})\n"
                f"Findings:\n{findings_text}\n"
                f"Raw response excerpt:\n{raw_response}\n"
            )

        synthesis_prompt = textwrap.dedent(f"""\
            You are the {self.division_name} Division Lead synthesising specialist results.

            Original task:
            Task ID: {task.task_id}
            Description: {task.description}

            Specialist results:
            {"".join(specialist_summaries)}

            Please provide:
            1. A cohesive synthesis of the findings (2-4 paragraphs).
            2. An overall confidence assessment as a JSON object on a separate line starting with "CONFIDENCE_JSON:" containing:
               - "level": one of "HIGH", "MEDIUM", "LOW", "INSUFFICIENT"
               - "score": float between 0 and 1
               - "caveats": list of strings
               - "alternative_explanations": list of strings

            Focus on:
            - Points of agreement across specialists
            - Contradictions or gaps
            - Actionable conclusions
            - What additional investigation might be needed
        """)

        messages = [{"role": "user", "content": synthesis_prompt}]

        try:
            response = await self.llm.chat(
                messages=messages,
                model=self.model,
                system=self.system_prompt,
            )

            response_text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )

            # Parse out confidence JSON
            synthesis_text = response_text
            confidence = ConfidenceAssessment(level=ConfidenceLevel.MEDIUM, score=0.5)

            if "CONFIDENCE_JSON:" in response_text:
                parts = response_text.split("CONFIDENCE_JSON:", 1)
                synthesis_text = parts[0].strip()
                try:
                    json_str = parts[1].strip()
                    # Handle if the JSON is followed by more text
                    # Find the closing brace
                    brace_depth = 0
                    end_idx = 0
                    for i, ch in enumerate(json_str):
                        if ch == "{":
                            brace_depth += 1
                        elif ch == "}":
                            brace_depth -= 1
                            if brace_depth == 0:
                                end_idx = i + 1
                                break
                    if end_idx > 0:
                        json_str = json_str[:end_idx]

                    conf_data = json.loads(json_str)
                    confidence = ConfidenceAssessment(
                        level=ConfidenceLevel(conf_data.get("level", "MEDIUM")),
                        score=float(conf_data.get("score", 0.5)),
                        caveats=conf_data.get("caveats", []),
                        alternative_explanations=conf_data.get(
                            "alternative_explanations", []
                        ),
                    )
                except (json.JSONDecodeError, ValueError, KeyError) as exc:
                    logger.warning(
                        "[%s] Failed to parse confidence JSON: %s",
                        self.division_name,
                        exc,
                    )

            return synthesis_text, confidence

        except Exception as exc:
            logger.error(
                "[%s] Synthesis LLM call failed: %s", self.division_name, exc
            )
            return (
                f"Synthesis failed: {exc}",
                ConfidenceAssessment(level=ConfidenceLevel.INSUFFICIENT, score=0.1),
            )

    # ------------------------------------------------------------------
    # Agent lookup
    # ------------------------------------------------------------------

    def _get_agent_by_name(self, name: str) -> BaseAgent | None:
        """Look up a specialist agent by name (case-insensitive)."""
        name_lower = name.lower()
        for agent in self.specialist_agents:
            if agent.name.lower() == name_lower:
                return agent
        return None

    # ------------------------------------------------------------------
    # Dynamic specialist spawning
    # ------------------------------------------------------------------

    async def spawn_specialist(
        self,
        name: str,
        system_prompt: str,
        tools: list[dict],
        model: ModelTier = ModelTier.SONNET,
    ) -> BaseAgent | None:
        """Dynamically create a specialist agent.

        Tracks the count against :attr:`max_dynamic_specialists`.
        Returns ``None`` if the limit has been reached.
        """
        if self._dynamic_specialist_count >= self.max_dynamic_specialists:
            logger.warning(
                "[%s] Cannot spawn specialist '%s': dynamic limit reached (%d/%d)",
                self.division_name,
                name,
                self._dynamic_specialist_count,
                self.max_dynamic_specialists,
            )
            return None

        agent = BaseAgent(
            name=name,
            system_prompt=system_prompt,
            model=model,
            tools=tools,
            division=self.division_name,
        )
        self.specialist_agents.append(agent)
        self._dynamic_specialist_count += 1

        logger.info(
            "[%s] Spawned dynamic specialist '%s' (%d/%d)",
            self.division_name,
            name,
            self._dynamic_specialist_count,
            self.max_dynamic_specialists,
        )
        return agent

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _empty_report(self, task: Task) -> DivisionReport:
        """Return an empty/fallback division report."""
        return DivisionReport(
            division_id=f"div_{self.division_name.lower().replace(' ', '_')}",
            division_name=self.division_name,
            lead_agent=self.name,
            specialist_results=[],
            synthesis="No sub-tasks were generated for this task.",
            confidence=ConfidenceAssessment(
                level=ConfidenceLevel.INSUFFICIENT,
                score=0.0,
                caveats=["Decomposition produced zero sub-tasks"],
            ),
        )
