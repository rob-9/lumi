# Lumi — Confidence-Aware AI Scientist with Human-in-the-Loop Routing

## Vision

Lumi is an agentic virtual lab for drug discovery that orchestrates specialist AI agents across biology, chemistry, and clinical domains. Unlike single-model copilots, Lumi runs multi-agent debate to produce **confidence-scored findings** and routes low-confidence results to human domain experts before they enter reports.

## How It Works

1. User submits a research question to a **sublab** specialized for that use case
2. The sublab orchestrates its own agent team with domain-specific tools and prompts
3. Agents query literature, databases, and computational tools via MCP servers
4. Multi-agent debate produces consensus findings with confidence scores
5. Low-confidence findings route to human experts for review
6. Final visual report combines figures, confidence data, and provenance trails

## Sublabs

Each sublab is a self-contained agent team purpose-built for a specific research workflow. Sublabs define their own agent roster, tool set, debate protocol, and report format.

| Sublab | Purpose | Key Agents |
|--------|---------|------------|
| **Target Validation** | Evidence dossiers with pathway diagrams and confidence scores | target_biologist, bio_pathways, literature_synthesis, safety |
| **Assay Troubleshooting** | Root-cause analysis of unexpected experimental results | assay_design, functional_genomics, single_cell_atlas |
| **Biomarker Curation** | Panel candidates with expression heatmaps | statistical_genetics, single_cell_atlas, clinical_trialist |
| **Regulatory Submissions** | Tox literature reviews with MoA illustrations | toxicogenomics, pharmacologist, fda_safety, literature_synthesis |
| **Lead Optimization** | Multi-parameter optimization of drug candidates | lead_optimization, antibody_engineer, developability, structure_design |
| **Clinical Translation** | Go/no-go evidence packages for IND-enabling studies | clinical_trialist, pharmacologist, statistical_genetics, fda_safety |

Sublabs share the core confidence engine, HITL routing, and report generator but customize everything else.

## Competitive Differentiation

- Confidence scoring via structured multi-agent debate (not just LLM logprobs)
- Human-in-the-loop routing for findings below confidence threshold
- Visual context reports with BioRender-style figures alongside text
- Full provenance chain from source data to final recommendation

## Stack

- **Language**: Python 3.11+
- **LLM**: Anthropic Claude (via `anthropic` SDK)
- **Agent framework**: Custom agents + FastMCP v3 for tool servers
- **Key deps**: BioPython, scanpy, RDKit, ESM, PyTorch, Pydantic
- **Async**: asyncio + uvloop

## Project Structure

```
src/
  agents/       # Specialist agents (target_biologist, antibody_engineer, etc.)
  sublabs/      # Sublab definitions — each wires agents, tools, and debate protocol
  divisions/    # Division leads that coordinate agent groups
  utils/        # Confidence scoring, LLM helpers, cost tracking, provenance
  factory.py    # System factory — wires agents, divisions, MCP bridge
  mcp_bridge.py # Connects agents to external tool servers
demos/          # Example usage scripts
tests/          # Test suite
```

## Dev Conventions

- Concise conventional commits (`feat:`, `fix:`, `refactor:`, etc.)
- Ruff for linting (line-length 120, target py311)
- pytest + pytest-asyncio for tests
- Keep agents stateless; state flows through message context
- No `Co-Authored-By` lines in commits
