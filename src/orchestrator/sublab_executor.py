"""SubLab Executor — runs dynamically composed agent teams.

Creates agents from a :class:`SubLabPlan`, executes them in the
specified group order (parallel within groups, sequential across groups),
and wraps results in :class:`DivisionReport` objects so the downstream
pipeline (review, synthesis) works unchanged.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid

from src.agents.base_agent import BaseAgent
from src.agents.dynamic_factory import create_dynamic_agent
from src.utils.types import (
    AgentResult,
    AgentSpec,
    ConfidenceAssessment,
    ConfidenceLevel,
    DivisionReport,
    SubLabPlan,
    Task,
)

logger = logging.getLogger("lumi.orchestrator.sublab_executor")


class SubLabExecutor:
    """Executes a dynamic SubLab plan."""

    async def execute(
        self,
        sublab_plan: SubLabPlan,
        task_description: str,
    ) -> list[DivisionReport]:
        """Create dynamic agents and execute the SubLab plan.

        Args:
            sublab_plan: The plan specifying agents and execution order.
            task_description: The overall task description to pass to agents.

        Returns:
            A list of :class:`DivisionReport` objects, one per agent,
            compatible with the downstream review/synthesis pipeline.
        """
        # 1. Create all agents
        agents: dict[str, BaseAgent] = {}
        spec_map: dict[str, AgentSpec] = {}
        for spec in sublab_plan.agents:
            agent = create_dynamic_agent(
                name=spec.name,
                role_description=spec.role,
                tool_names=spec.tools,
                domains=spec.domains,
                model=spec.model_tier,
            )
            agents[spec.name] = agent
            spec_map[spec.name] = spec

        logger.info(
            "[SubLabExecutor] Created %d dynamic agents",
            len(agents),
        )
        for name, agent in agents.items():
            tool_count = len([t for t in agent.tools if t.get("name") != "execute_code"])
            logger.info(
                "[SubLabExecutor]   '%s': %d tools, model=%s",
                name,
                tool_count,
                agent.model.value,
            )

        # 2. Execute groups sequentially; agents within a group in parallel
        all_results: dict[str, AgentResult] = {}
        prior_context = ""

        for group_idx, group in enumerate(sublab_plan.execution_groups):
            logger.info(
                "[SubLabExecutor] Executing group %d/%d: %s",
                group_idx + 1,
                len(sublab_plan.execution_groups),
                group,
            )

            coros = []
            group_agent_names = []
            for agent_name in group:
                agent = agents.get(agent_name)
                if agent is None:
                    logger.warning(
                        "[SubLabExecutor] Agent '%s' not found in plan — skipping",
                        agent_name,
                    )
                    continue

                # Build task with prior context
                task_text = task_description
                if prior_context:
                    task_text += f"\n\n--- Prior findings from earlier agents ---\n{prior_context}"

                task = Task(
                    task_id=f"sublab_{uuid.uuid4().hex[:8]}",
                    description=task_text,
                    agent=agent_name,
                )

                coros.append(agent.execute(task))
                group_agent_names.append(agent_name)

            # Run group in parallel
            batch = await asyncio.gather(*coros, return_exceptions=True)

            for agent_name, result in zip(group_agent_names, batch):
                if isinstance(result, Exception):
                    logger.error(
                        "[SubLabExecutor] Agent '%s' failed: %s",
                        agent_name,
                        result,
                    )
                    all_results[agent_name] = AgentResult(
                        agent_id=agent_name,
                        task_id="failed",
                        raw_data={"error": str(result)},
                    )
                else:
                    all_results[agent_name] = result

            # Build context from this group's results for the next group
            context_parts: list[str] = []
            for agent_name in group_agent_names:
                r = all_results.get(agent_name)
                if r is None:
                    continue
                findings_text = "\n".join(
                    f"  - {c.claim_text} (confidence: {c.confidence.level.value})"
                    for c in r.findings
                ) or "(no structured findings)"
                raw_excerpt = r.raw_data.get("final_response", "")[:500]
                context_parts.append(
                    f"[{agent_name}]\nFindings:\n{findings_text}\n{raw_excerpt}"
                )

            if context_parts:
                prior_context += "\n\n".join(context_parts) + "\n"

        # 3. Wrap each agent result in a DivisionReport
        reports: list[DivisionReport] = []
        for spec in sublab_plan.agents:
            result = all_results.get(spec.name)
            if result is None:
                continue

            # Compute an aggregate confidence from the agent's findings
            if result.findings:
                avg_score = sum(c.confidence.score for c in result.findings) / len(result.findings)
                if avg_score >= 0.7:
                    level = ConfidenceLevel.HIGH
                elif avg_score >= 0.4:
                    level = ConfidenceLevel.MEDIUM
                elif avg_score >= 0.15:
                    level = ConfidenceLevel.LOW
                else:
                    level = ConfidenceLevel.INSUFFICIENT
            else:
                avg_score = 0.0
                level = ConfidenceLevel.INSUFFICIENT

            reports.append(DivisionReport(
                division_id=f"sublab_{spec.name.lower().replace(' ', '_')}",
                division_name=f"SubLab: {spec.name}",
                lead_agent=spec.name,
                specialist_results=[result],
                synthesis=result.raw_data.get("final_response", "")[:2000],
                confidence=ConfidenceAssessment(level=level, score=avg_score),
            ))

        logger.info(
            "[SubLabExecutor] Execution complete — %d reports produced",
            len(reports),
        )
        return reports
