"""
Agent Factory — Dynamic agent creation for the Lumi Virtual Lab.

Replaces the static 17-agent swarm with on-demand agent spawning.
The CSO orchestrator analyzes a query, determines what specialist
capabilities are needed, and the AgentFactory creates purpose-built
agents with the right system prompts, tools, and model tiers.

Key components:
- AgentFactory: Creates agents on-demand from capability specs
- AgentBlueprint: Declarative spec for what an agent needs (tools, prompt, model)
- CapabilityRouter: Maps query requirements to agent blueprints

Design rationale (vs static swarm):
- Token efficiency: Only load agents relevant to the query
- Better specialization: Agents tailored to exact sub-questions
- Cost control: Fewer agents = fewer LLM calls
- Aligns with ADAS (Automated Design of Agentic Systems) literature

Integration:
- CSO calls CapabilityRouter to determine needed capabilities
- CapabilityRouter returns AgentBlueprints
- AgentFactory instantiates agents from blueprints with full tool wiring
- Division leads can still spawn_specialist() but now through the factory
"""
