"""Dynamic agent creation for SubLab composition.

Creates :class:`BaseAgent` instances at runtime with query-appropriate
tool assignments and composed system prompts, rather than relying on
the static 17-agent roster.
"""

from __future__ import annotations

import logging

from src.agents.base_agent import BaseAgent
from src.agents.prompt_library import compose_system_prompt
from src.mcp_bridge import TOOL_REGISTRY, get_tool_schema
from src.utils.llm import ModelTier

logger = logging.getLogger("lumi.agents.dynamic_factory")

_MODEL_TIER_MAP: dict[str, ModelTier] = {
    "OPUS": ModelTier.OPUS,
    "SONNET": ModelTier.SONNET,
    "HAIKU": ModelTier.HAIKU,
}


def create_dynamic_agent(
    name: str,
    role_description: str,
    tool_names: list[str],
    domains: list[str] | None = None,
    model: ModelTier | str = ModelTier.SONNET,
) -> BaseAgent:
    """Create a dynamically composed agent with specified tools and domains.

    Args:
        name: Human-readable agent name.
        role_description: One-sentence role for the system prompt.
        tool_names: Tool names from the catalog to assign.
        domains: Domain keys for prompt composition. If ``None``,
            a generic prompt is used.
        model: Model tier (enum or string like ``"SONNET"``).

    Returns:
        A fully wired :class:`BaseAgent` ready for execution.
    """
    # Resolve model tier
    if isinstance(model, str):
        model_tier = _MODEL_TIER_MAP.get(model.upper(), ModelTier.SONNET)
    else:
        model_tier = model

    # Build system prompt
    system_prompt = compose_system_prompt(
        domains=domains or [],
        custom_role=role_description,
    )

    # Build tool definitions from catalog
    tools: list[dict] = []
    missing: list[str] = []
    for tool_name in tool_names:
        schema = get_tool_schema(tool_name)
        if schema is not None:
            tools.append(schema)
        else:
            missing.append(tool_name)

    if missing:
        logger.warning(
            "Dynamic agent '%s': %d tools not found in catalog: %s",
            name, len(missing), ", ".join(missing),
        )

    # Create the agent
    agent = BaseAgent(
        name=name,
        system_prompt=system_prompt,
        model=model_tier,
        tools=tools,
    )

    # Wire callables from TOOL_REGISTRY
    wired = 0
    for tool_name in tool_names:
        if tool_name in TOOL_REGISTRY:
            agent._tool_registry[tool_name] = TOOL_REGISTRY[tool_name]
            wired += 1

    logger.info(
        "Created dynamic agent '%s': %d tools wired, model=%s, domains=%s",
        name, wired, model_tier.value, domains or [],
    )

    return agent
