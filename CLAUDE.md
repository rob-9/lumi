# Lumi — Confidence-Aware AI Scientist with Human-in-the-Loop Routing

## Vision

Lumi is an agentic virtual lab for drug discovery that orchestrates specialist AI agents across biology, chemistry, and clinical domains. A 9-phase YOHAS pipeline produces **confidence-scored findings** with biosecurity veto gates and adversarial review, routing low-confidence results to human domain experts before they enter reports.

## How It Works

1. User submits a research question via the Streamlit UI or pipeline API
2. **CSO** (Claude Opus) parses the query; **ChiefOfStaff** (Haiku) scouts the research landscape
3. **BiosecurityOfficer** (Sonnet) pre-screens for dual-use risk — RED = hard veto
4. CSO dispatches tasks to **Division Leads**, who coordinate specialist agents
5. Agents query literature, databases, and computational tools via MCP servers
6. **ReviewPanel** (Sonnet) runs 3-pass adversarial review; up to 3 refinement cycles
7. **WorldModel** (SQLite) persists findings, entities, and contradictions across sessions
8. Final report combines confidence data, provenance trails, and visual context

## Architecture

### Tier 1 — Orchestration

| Component | Model | Role |
|-----------|-------|------|
| **CSOOrchestrator** | Opus | Strategic brain — runs the 9-phase pipeline |
| **ChiefOfStaff** | Haiku | Intelligence briefing (field landscape, feasibility) |
| **BiosecurityOfficer** | Sonnet | Hard veto authority on dual-use risk |
| **ReviewPanel** | Sonnet | Adversarial quality gate (methodology → evidence → synthesis) |
| **WorldModel** | SQLite | Persistent knowledge store (entities, claims, relationships) |

### Tier 2 — Divisions (8)

Each division lead coordinates a team of specialist agents via task decomposition.

| Division | Specialists |
|----------|-------------|
| **Target ID** | statistical_genetics, functional_genomics, single_cell_atlas |
| **Target Safety** | bio_pathways, fda_safety, toxicogenomics |
| **Modality** | target_biologist, pharmacologist |
| **Molecular Design** | protein_intelligence, antibody_engineer, structure_design, lead_optimization, developability |
| **Clinical** | clinical_trialist |
| **CompBio** | literature_synthesis |
| **Experimental** | assay_design |
| **Biosecurity** | dual_use_screening |

### Tier 3 — Specialist Agents (17)

CodeAct-style agents with tool registries wired via the MCP bridge. Stateless — state flows through message context.

### Domain Engines

| Engine | Purpose |
|--------|---------|
| **Biosecurity Engine** | 5-screen pipeline (select agents, toxin domains, virulence factors, GoF risk, BWC compliance) |
| **Yami Simulator** | Protein intelligence — ESM-2 scoring, structure confidence, solubility, stability |
| **Virtual Cell Simulator** | Metabolic modeling — expression simulation, gene knockouts, growth prediction |

## Competitive Differentiation

- Confidence scoring via structured multi-agent debate (not just LLM logprobs)
- Biosecurity hard-veto gate with 5-method screening pipeline
- Adversarial 3-pass review panel with refinement loops
- Persistent world model for cross-session knowledge accumulation
- Human-in-the-loop routing for findings below confidence threshold
- Full provenance chain from source data to final recommendation

## Stack

- **Language**: Python 3.11+
- **LLM**: Anthropic Claude (via `anthropic` SDK) — Opus / Sonnet / Haiku tiered
- **Agent framework**: Custom agents + FastMCP v3 for tool servers
- **Key deps**: BioPython, scanpy, RDKit, ESM, PyTorch, Pydantic
- **Async**: asyncio + uvloop
- **UI**: Streamlit

## Project Structure

```
src/
  orchestrator/          # Tier 1 — CSO, ChiefOfStaff, ReviewPanel, BiosecurityOfficer, WorldModel, pipeline
  divisions/             # Tier 2 — Division leads coordinating agent groups
  agents/                # Tier 3 — 17 specialist agents + base class
  biosecurity_engine/    # 5-screen biosecurity screening pipeline
  yami_simulator/        # Protein intelligence (ESM-2, AlphaFold, solubility)
  virtual_cell/          # Metabolic modeling (COBRApy, expression simulation)
  mcp_servers/           # MCP tool servers (genomics, protein, clinical, literature, etc.)
  utils/                 # Confidence scoring, LLM client, cost tracking, provenance, types
  factory.py             # System factory — wires agents, divisions, MCP bridge
  mcp_bridge.py          # Master tool registry connecting agents to MCP servers
app.py                   # Streamlit UI (query submission, results, expert review, agent monitor)
demos/                   # Example usage scripts
tests/                   # Test suite
```

## Dev Conventions

- Concise conventional commits (`feat:`, `fix:`, `refactor:`, etc.)
- Ruff for linting (line-length 120, target py311)
- pytest + pytest-asyncio for tests
- Keep agents stateless; state flows through message context
- No `Co-Authored-By` lines in commits
