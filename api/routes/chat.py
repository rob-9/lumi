"""Chat endpoints — mock pipeline for GLP-1R / semaglutide / Parkinson's Disease.

Dynamic SubLab demo:
  1. CSO scopes query → selects dynamic SubLab mode
  2. Biosecurity pre-screen (GREEN)
  3. SubLab Planner composes team (3 agents, 2 execution groups)
  4. HITL scope approval
  5. Group 1 (parallel): Pharmacology & Drug Analyst + Neuro-Genomics Analyst
  6. Group 2 (sequential): Pathway Visualization Specialist
  7. Adversarial review panel (3-pass)
  8. HITL flag on low-confidence clinical claim → auto-resolved
  9. Integrations (Slack, BioRender, Benchling)
  10. Final synthesis streamed as markdown
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

log = logging.getLogger("lumi.chat")

from api.models import (
    AgentTrace,
    Chat,
    CreateChatRequest,
    HitlEvent,
    IntegrationEvent,
    Message,
    Role,
    SendMessageRequest,
    ToolCall,
)

router = APIRouter(prefix="/chats", tags=["chats"])

_chats: dict[str, Chat] = {}


# ===========================================================================
# Mock response text — GLP-1R neuroprotection assessment
# ===========================================================================


def _mock_response_text() -> str:
    return (
        "## GLP-1R Agonist Repurposing Assessment — Parkinson's Disease\n\n"
        "### Executive Summary\n\n"
        "GLP-1 receptor agonists, including semaglutide, represent a **scientifically plausible** "
        "neuroprotective strategy for early-stage Parkinson's disease. The GLP-1R → cAMP → PKA → "
        "CREB → BDNF signaling cascade is validated in dopaminergic neurons of the substantia nigra, "
        "with additional anti-inflammatory effects via microglial modulation. However, clinical evidence "
        "remains **preliminary**, resting primarily on a single Phase II exenatide trial (n=62).\n\n"
        "---\n\n"
        "### Dynamic SubLab Execution\n\n"
        "- **Mode**: Dynamic SubLab (cross-domain tool mixing)\n"
        "- **Team**: 3 agents, 2 execution groups, 8 tools across 5 domains\n"
        "- **Biosecurity**: Pre-screen PASSED (GREEN)\n"
        "- **Review**: 3-pass adversarial — 6/7 findings approved, 1 routed to HITL\n"
        "- **HITL**: Clinical efficacy claim reviewed and approved with uncertainty label\n\n"
        "---\n\n"
        "### Key Findings\n\n"
        "| # | Finding | Agent | Confidence |\n"
        "|---|---------|-------|------------|\n"
        "| 1 | GLP1R expressed in SN dopaminergic neurons (TPM: 3.2), co-localized with TH | neuro_genomics_analyst | **HIGH** 88% |\n"
        "| 2 | Validated cascade: GLP-1R → Gαs → cAMP → PKA → CREB → BDNF → neuronal survival | neuro_genomics_analyst | **HIGH** 91% |\n"
        "| 3 | PI3K/Akt anti-apoptotic branch provides additional neuronal protection | neuro_genomics_analyst | **HIGH** 85% |\n"
        "| 4 | Semaglutide: established safety from >10M patient-years in diabetes/obesity | pharmacology_drug_analyst | **HIGH** 95% |\n"
        "| 5 | 4 active clinical trials for GLP-1 agonists in PD (Phase II–III) | pharmacology_drug_analyst | **HIGH** 90% |\n"
        "| 6 | Epidemiological signal: 20-30% lower PD incidence in GLP-1 agonist users | neuro_genomics_analyst | **MED** 62% |\n"
        "| 7 | Disease-modifying efficacy in PD *(HITL-reviewed, Phase II only)* | pharmacology_drug_analyst | **LOW** 38% |\n\n"
        "---\n\n"
        "### GLP-1R Neuroprotective Pathway\n\n"
        "```\n"
        "Semaglutide → GLP-1R → Gαs → cAMP → PKA → CREB → BDNF → Neuronal Survival\n"
        "                                    ↘ PI3K → Akt → Anti-apoptosis\n"
        "                               ↘ Microglial NF-κB ↓ → Reduced Neuroinflammation\n"
        "```\n\n"
        "### Risk Assessment\n\n"
        "- **Biological plausibility**: Strong — GLP1R expression in target neurons, mechanism well-characterized\n"
        "- **Safety**: Low risk — extensive safety data from diabetes/obesity; CNS-specific AEs minimal\n"
        "- **Clinical evidence**: Moderate risk — Phase II positive but underpowered; Phase III pending\n"
        "- **BBB penetration**: Moderate concern — limited but detectable CSF levels; NLY01 (brain-penetrant) in Phase II\n\n"
        "### Recommended Next Steps\n\n"
        "1. Monitor Exenatide-PD3 Phase III trial (NCT04232969) — efficacy readout expected 2025\n"
        "2. Evaluate semaglutide CSF penetration via PET imaging with radiolabeled analog\n"
        "3. Profile GLP-1R expression changes across Braak stages using spatial transcriptomics\n"
        "4. Assess synergy with existing PD therapeutics (levodopa, MAO-B inhibitors) in preclinical models\n\n"
        "### Integrations\n\n"
        "- Findings posted to **#neuro-repurposing** on Slack\n"
        "- GLP-1R pathway diagram generated via **BioRender**\n"
        "- Notebook entry **EXP-2026-0417** created in **Benchling**\n\n"
        "---\n\n"
        "*Overall confidence: **MEDIUM-HIGH** (0.76) · Cost: $3.18 · Duration: 2m 34s · 3 agents · 5 domains · Dynamic SubLab*"
    )


# ===========================================================================
# Mock streaming — Dynamic SubLab pipeline
# ===========================================================================


async def _stream_mock(chat: Chat, msg_id: str):
    """Stream the GLP-1R dynamic SubLab demo with realistic timing."""
    all_traces: list[AgentTrace] = []
    all_hitl: list[HitlEvent] = []
    all_integrations: list[IntegrationEvent] = []

    def _sse(event_type: str, data: dict) -> str:
        data["message_id"] = msg_id
        data["type"] = event_type
        return f"data: {json.dumps(data, default=str)}\n\n"

    # ── Phase 1: CSO Scoping ──

    yield _sse("trace_start", {"trace": AgentTrace(
        agent_id="cso_orchestrator", division="Orchestration", status="running",
        message="Analyzing research query...",
    ).model_dump()})
    await asyncio.sleep(1.2)

    cso_done = AgentTrace(
        agent_id="cso_orchestrator", division="Orchestration", status="complete",
        message="Query parsed. Drug repurposing assessment across neurology + pharmacology. Selecting Dynamic SubLab mode.",
        tools_called=[
            ToolCall(tool_name="parse_research_query", tool_input={"query": "GLP-1R semaglutide neurodegeneration Parkinson's"}, result="Target: GLP1R | Drug: semaglutide | Indication: PD | Task: repurposing assessment", duration_ms=580),
            ToolCall(tool_name="select_sublab_mode", tool_input={"domains": ["pharmacology", "neurology", "genomics", "clinical"]}, result="Dynamic SubLab — 4 domains require cross-domain tool mixing", duration_ms=290),
        ],
        confidence_score=0.96, confidence_level="HIGH", duration_ms=1820,
    )
    yield _sse("trace_complete", {"trace": cso_done.model_dump()})
    all_traces.append(cso_done)
    await asyncio.sleep(0.6)

    # ── Phase 2: Biosecurity Pre-screen ──

    yield _sse("trace_start", {"trace": AgentTrace(
        agent_id="biosecurity_officer", division="Biosecurity", status="running",
        message="Screening for dual-use risk...",
    ).model_dump()})
    await asyncio.sleep(0.6)

    bio_tool = ToolCall(
        tool_name="screen_biosecurity",
        tool_input={"query": "semaglutide GLP-1 agonist Parkinson's neuroprotection"},
        result="5/5 screens passed — GREEN. FDA-approved diabetes drug, no dual-use concern.",
        duration_ms=740,
    )
    yield _sse("tool_call", {"agent_id": "biosecurity_officer", "tool": bio_tool.model_dump()})
    await asyncio.sleep(0.6)

    bio_done = AgentTrace(
        agent_id="biosecurity_officer", division="Biosecurity", status="complete",
        message="Pre-screen PASSED. Category: GREEN. No dual-use, toxin, or GoF risk.",
        tools_called=[bio_tool],
        confidence_score=1.0, confidence_level="HIGH", duration_ms=960,
    )
    yield _sse("trace_complete", {"trace": bio_done.model_dump()})
    all_traces.append(bio_done)
    await asyncio.sleep(0.5)

    # ── Phase 3: SubLab Planning ──

    yield _sse("trace_start", {"trace": AgentTrace(
        agent_id="sublab_planner", division="Orchestration", status="running",
        message="Planning dynamic agent team (Opus)...",
    ).model_dump()})
    await asyncio.sleep(1.2)

    plan_done = AgentTrace(
        agent_id="sublab_planner", division="Orchestration", status="complete",
        message=(
            "Team composed: 3 agents in 2 execution groups.\n"
            "Group 1 (parallel): Pharmacology & Drug Analyst, Neuro-Genomics Analyst\n"
            "Group 2 (sequential): Pathway Visualization Specialist"
        ),
        tools_called=[
            ToolCall(
                tool_name="compose_team",
                tool_input={"domains": ["pharmacology", "neurology", "genomics", "clinical", "pathways"], "tools": 119},
                result="3 agents selected, 8 tools assigned across 5 domains",
                duration_ms=1240,
            ),
        ],
        confidence_score=0.98, confidence_level="HIGH", duration_ms=2140,
    )
    yield _sse("trace_complete", {"trace": plan_done.model_dump()})
    all_traces.append(plan_done)
    await asyncio.sleep(0.6)

    # ── HITL: Scope Approval ──

    scope_hitl = {
        "finding": (
            "Dynamic SubLab team: 3 agents, 2 execution groups, 8 tools across 5 domains.\n\n"
            "Group 1 (parallel):\n"
            "• Pharmacology & Drug Analyst — get_drug_info, search_trials, get_side_effects, search_pubmed\n"
            "• Neuro-Genomics Analyst — get_gene_info, get_gene_expression, get_pathways_for_gene, query_gwas_associations\n\n"
            "Group 2 (depends on Group 1):\n"
            "• Pathway Visualization Specialist — generate_pathway_diagram, generate_moa_diagram"
        ),
        "agent_id": "sublab_planner",
        "confidence_score": 0.98,
        "reason": "Confirm team composition and tool allocation before execution. Estimated cost: ~$3.20.",
        "status": "pending",
    }
    yield _sse("hitl_flag", {"hitl": scope_hitl})
    await asyncio.sleep(2.0)

    scope_resolved = {**scope_hitl, "status": "approved", "reason": "Scope approved. Executing dynamic SubLab pipeline."}
    yield _sse("hitl_resolved", {"hitl": scope_resolved})
    all_hitl.append(HitlEvent(**scope_resolved))
    await asyncio.sleep(0.8)

    # ── Phase 4: Group 1 — Parallel Data Gathering ──

    # Start both agents simultaneously
    yield _sse("trace_start", {"trace": AgentTrace(
        agent_id="pharmacology_drug_analyst", division="Dynamic SubLab · Group 1", status="running",
        message="Gathering drug, trial, safety, and literature data...",
    ).model_dump()})
    yield _sse("trace_start", {"trace": AgentTrace(
        agent_id="neuro_genomics_analyst", division="Dynamic SubLab · Group 1", status="running",
        message="Gathering gene, expression, pathway, and GWAS data...",
    ).model_dump()})
    await asyncio.sleep(0.8)

    # Tool calls for each agent
    pharma_tools = [
        ToolCall(tool_name="get_drug_info", tool_input={"drug": "semaglutide"}, result="GLP-1 receptor agonist. MW: 4113.6 Da. Half-life: ~7 days. FDA-approved T2DM/obesity. BBB penetration: limited but detectable in CSF.", duration_ms=1180),
        ToolCall(tool_name="search_trials", tool_input={"query": "GLP-1 Parkinson's disease"}, result="4 trials: NCT01971242 (exenatide Phase II, completed), NCT04232969 (exenatide Phase III, recruiting), NCT04154072 (lixisenatide Phase II), NCT05819372 (NLY01 Phase II)", duration_ms=1420),
        ToolCall(tool_name="search_pubmed", tool_input={"query": "GLP1R neuroprotection Parkinson dopaminergic"}, result="187 results. Key: Athauda 2017 (exenatide RCT), Kim 2017 (GLP-1R in DA neurons), Yun 2018 (NLY01 neuroprotection)", duration_ms=1340),
        ToolCall(tool_name="get_side_effects", tool_input={"drug": "semaglutide"}, result="Common: nausea (20%), diarrhea (10%), vomiting (8%). Serious: pancreatitis (0.3%). Established safety >10M patient-years.", duration_ms=980),
    ]
    neuro_tools = [
        ToolCall(tool_name="get_gene_info", tool_input={"gene": "GLP1R"}, result="GLP1R: 6p21.2, 463 aa, class B1 GPCR. Expression: pancreas (high), brain (moderate — substantia nigra, hippocampus, cortex).", duration_ms=1090),
        ToolCall(tool_name="get_gene_expression", tool_input={"gene": "GLP1R", "tissue": "brain"}, result="Substantia nigra TPM: 3.2, hippocampus: 4.8, cortex: 2.1, hypothalamus: 8.7. Co-expressed with TH in DA neurons.", duration_ms=1560),
        ToolCall(tool_name="get_pathways_for_gene", tool_input={"gene": "GLP1R"}, result="KEGG: hsa04024 (cAMP), hsa04151 (PI3K-Akt). Cascade: GLP-1R → Gαs → cAMP → PKA → CREB → BDNF → neuronal survival.", duration_ms=1380),
        ToolCall(tool_name="query_gwas_associations", tool_input={"gene": "GLP1R"}, result="rs10305492 A316T: T2DM protection (OR=0.86). No direct PD GWAS hits. Epidemiological: GLP-1 users show 20-30% lower PD incidence.", duration_ms=1240),
    ]

    # Interleave tool calls — demonstrates parallel execution
    for i in range(4):
        yield _sse("tool_call", {"agent_id": "pharmacology_drug_analyst", "tool": pharma_tools[i].model_dump()})
        await asyncio.sleep(0.5)
        yield _sse("tool_call", {"agent_id": "neuro_genomics_analyst", "tool": neuro_tools[i].model_dump()})
        await asyncio.sleep(0.5)

    await asyncio.sleep(0.4)

    # Complete both agents
    pharma_done = AgentTrace(
        agent_id="pharmacology_drug_analyst", division="Dynamic SubLab · Group 1", status="complete",
        message="Semaglutide: validated GLP-1 agonist with established safety. 4 active PD trials. Phase II exenatide data showed motor improvement (n=62) but limited. Safety well-characterized (>10M patient-years).",
        tools_called=pharma_tools,
        confidence_score=0.82, confidence_level="HIGH", duration_ms=8420,
    )
    yield _sse("trace_complete", {"trace": pharma_done.model_dump()})
    all_traces.append(pharma_done)
    await asyncio.sleep(0.3)

    neuro_done = AgentTrace(
        agent_id="neuro_genomics_analyst", division="Dynamic SubLab · Group 1", status="complete",
        message="GLP1R expressed in SN dopaminergic neurons (TPM: 3.2), co-localized with TH. Validated cascade: GLP-1R → cAMP → PKA → CREB → BDNF. PI3K/Akt provides anti-apoptotic signaling. Epidemiological association with lower PD incidence.",
        tools_called=neuro_tools,
        confidence_score=0.88, confidence_level="HIGH", duration_ms=9270,
    )
    yield _sse("trace_complete", {"trace": neuro_done.model_dump()})
    all_traces.append(neuro_done)
    await asyncio.sleep(0.6)

    # ── Phase 5: Group 2 — Synthesis & Visualization ──

    yield _sse("trace_start", {"trace": AgentTrace(
        agent_id="pathway_visualization", division="Dynamic SubLab · Group 2", status="running",
        message="Generating pathway and MOA diagrams from Group 1 findings...",
    ).model_dump()})
    await asyncio.sleep(0.8)

    viz_tools = [
        ToolCall(
            tool_name="generate_pathway_diagram",
            tool_input={"title": "GLP-1R Neuroprotective Signaling in PD", "nodes": ["GLP-1R", "Gαs", "cAMP", "PKA", "CREB", "BDNF", "Neuronal Survival", "PI3K", "Akt", "Anti-apoptosis"]},
            result="Pathway diagram: 10 nodes, 9 edges. Linear cascade with PI3K/Akt branch.",
            duration_ms=2340,
        ),
        ToolCall(
            tool_name="generate_moa_diagram",
            tool_input={"drug": "semaglutide", "target": "GLP-1R", "indication": "Parkinson's disease"},
            result="MOA diagram: semaglutide → GLP-1R → dual neuroprotective mechanism in substantia nigra.",
            duration_ms=1890,
        ),
    ]
    for tool in viz_tools:
        yield _sse("tool_call", {"agent_id": "pathway_visualization", "tool": tool.model_dump()})
        await asyncio.sleep(0.8)

    await asyncio.sleep(0.4)
    viz_done = AgentTrace(
        agent_id="pathway_visualization", division="Dynamic SubLab · Group 2", status="complete",
        message="Generated pathway diagram (GLP-1R → BDNF cascade with PI3K/Akt branch) and MOA diagram for semaglutide in PD.",
        tools_called=viz_tools,
        confidence_score=0.94, confidence_level="HIGH", duration_ms=5840,
    )
    yield _sse("trace_complete", {"trace": viz_done.model_dump()})
    all_traces.append(viz_done)
    await asyncio.sleep(0.6)

    # ── Phase 6: Adversarial Review Panel ──

    yield _sse("trace_start", {"trace": AgentTrace(
        agent_id="review_panel", division="Orchestration", status="running",
        message="Running 3-pass adversarial review (methodology → evidence → synthesis)...",
    ).model_dump()})
    await asyncio.sleep(0.8)

    review_tool = ToolCall(
        tool_name="confidence_calibration",
        tool_input={"claims": 7, "method": "3-pass adversarial"},
        result="7 claims scored. Auto-pass (≥0.70): GLP1R expression, cAMP/CREB mechanism, semaglutide safety. Soft-flag: clinical efficacy (0.38). Mean: 0.76.",
        duration_ms=860,
    )
    yield _sse("tool_call", {"agent_id": "review_panel", "tool": review_tool.model_dump()})
    await asyncio.sleep(0.6)

    review_done = AgentTrace(
        agent_id="review_panel", division="Orchestration", status="complete",
        message="3-pass adversarial review complete. 6/7 findings APPROVED (≥0.70). 1 flagged SOFT (0.38) — clinical efficacy routed to HITL.",
        tools_called=[review_tool],
        confidence_score=0.92, confidence_level="HIGH", duration_ms=2180,
    )
    yield _sse("trace_complete", {"trace": review_done.model_dump()})
    all_traces.append(review_done)
    await asyncio.sleep(0.6)

    # ── Phase 7: HITL — Low-confidence clinical finding ──

    clinical_hitl = {
        "finding": "GLP-1 receptor agonists show disease-modifying potential in Parkinson's disease, with motor score improvement in the exenatide Phase II trial (Athauda et al., 2017, n=62).",
        "agent_id": "pharmacology_drug_analyst",
        "confidence_score": 0.38,
        "reason": "Below 0.50 threshold. Single Phase II RCT (n=62), open-label extension with mixed results. No Phase III data. Exenatide-PD3 (NCT04232969) pending.",
        "status": "pending",
    }
    yield _sse("hitl_flag", {"hitl": clinical_hitl})
    await asyncio.sleep(2.5)

    clinical_resolved = {
        **clinical_hitl,
        "status": "approved",
        "reason": "Domain expert: Include as promising signal with explicit uncertainty. Phase II is hypothesis-generating. Track Exenatide-PD3 Phase III for definitive evidence.",
    }
    yield _sse("hitl_resolved", {"hitl": clinical_resolved})
    all_hitl.append(HitlEvent(**clinical_resolved))
    await asyncio.sleep(0.8)

    # ── Phase 8: Integrations ──

    integrations = [
        IntegrationEvent(integration="Slack", action="Posted findings summary to #neuro-repurposing", status="complete", detail="7 findings, 1 HITL-reviewed. 3 agents across 5 domains. Confidence: 0.76."),
        IntegrationEvent(integration="BioRender", action="Generated GLP-1R neuroprotective signaling pathway diagram", status="complete", detail="10-node cascade: GLP-1R → BDNF with PI3K/Akt and anti-inflammatory branches."),
        IntegrationEvent(integration="Benchling", action="Created notebook entry EXP-2026-0417", status="complete", detail="Linked GLP-1R repurposing dossier to PD-Neuroprotection project."),
    ]
    for integ in integrations:
        all_integrations.append(integ)
        yield _sse("integration", {"call": integ.model_dump()})
        await asyncio.sleep(0.8)

    # ── Phase 9: Final synthesis ──

    text = _mock_response_text()
    chunks = [text[i:i + 80] for i in range(0, len(text), 80)]
    accumulated = ""
    for chunk in chunks:
        accumulated += chunk
        yield _sse("text_delta", {"delta": chunk})
        await asyncio.sleep(0.03)

    # Store message
    assistant_msg = Message(
        id=msg_id, role=Role.ASSISTANT, content=accumulated,
        agent_traces=all_traces, hitl_events=all_hitl, integration_events=all_integrations,
    )
    chat.messages.append(assistant_msg)
    chat.updated_at = datetime.now(timezone.utc)

    yield _sse("done", {})


# ===========================================================================
# Routes
# ===========================================================================


@router.get("")
async def list_chats() -> list[Chat]:
    return sorted(_chats.values(), key=lambda c: c.updated_at, reverse=True)


@router.post("")
async def create_chat(req: CreateChatRequest) -> Chat:
    log.info("create_chat sublab=%s msg=%s", req.sublab, req.message[:80])
    chat_id = str(uuid.uuid4())[:8]
    title = req.message[:60] + ("..." if len(req.message) > 60 else "")
    chat = Chat(id=chat_id, title=title, sublab=req.sublab)
    user_msg = Message(id=str(uuid.uuid4())[:8], role=Role.USER, content=req.message, sublab=req.sublab)
    chat.messages.append(user_msg)
    _chats[chat_id] = chat
    return chat


@router.get("/{chat_id}")
async def get_chat(chat_id: str) -> Chat:
    from fastapi import HTTPException
    if chat_id not in _chats:
        raise HTTPException(status_code=404, detail="Chat not found")
    return _chats[chat_id]


@router.post("/{chat_id}/messages")
async def send_message(chat_id: str, req: SendMessageRequest) -> StreamingResponse:
    log.info("send_message chat_id=%s content=%s", chat_id, req.content[:80])
    chat = _chats[chat_id]
    last = chat.messages[-1] if chat.messages else None
    if not last or last.role != Role.USER or last.content != req.content:
        user_msg = Message(id=str(uuid.uuid4())[:8], role=Role.USER, content=req.content)
        chat.messages.append(user_msg)
    msg_id = str(uuid.uuid4())[:8]
    return StreamingResponse(_stream_mock(chat, msg_id), media_type="text/event-stream")
