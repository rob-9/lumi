"""Chat endpoints with mock streaming responses.

Mocks a full multi-agent sublab pipeline:
  1. Biosecurity pre-screen
  2. Division agents execute in parallel (Target ID, Target Safety, CompBio)
  3. Adversarial review panel (3-pass)
  4. Low-confidence finding auto-flagged for HITL
  5. HITL auto-resolved by domain expert
  6. Integration calls (Slack alert, BioRender figure)
  7. Final synthesis streamed as markdown
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

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


def _pipeline_traces() -> list[dict]:
    """Return the full pipeline as a sequence of events (traces, hitl, integrations)."""
    return [
        # --- Phase 0: Biosecurity pre-screen ---
        {
            "kind": "trace",
            "trace": AgentTrace(
                agent_id="biosecurity_officer",
                division="Biosecurity",
                status="complete",
                message="Pre-screen PASSED. No dual-use risk detected. Category: GREEN.",
                tools_called=[
                    ToolCall(tool_name="screen_biosecurity", tool_input={"query": "BRCA1 TNBC target validation"}, result="5/5 screens passed — GREEN", duration_ms=820),
                ],
                confidence_score=1.0,
                confidence_level="HIGH",
                duration_ms=1040,
            ),
        },
        # --- Phase 1: Target Identification (parallel) ---
        {
            "kind": "trace",
            "trace": AgentTrace(
                agent_id="statistical_genetics",
                division="Target Identification",
                status="complete",
                message="BRCA1 rs80357906 strongly associated with TNBC risk (OR=11.2, p<1e-50). 3 independent GWAS replications.",
                tools_called=[
                    ToolCall(tool_name="query_gwas_catalog", tool_input={"gene": "BRCA1", "trait": "breast cancer"}, result="3 genome-wide significant loci", duration_ms=1230),
                    ToolCall(tool_name="execute_code", tool_input={"task": "meta-analysis forest plot"}, result="Forest plot generated, I²=12%", duration_ms=890),
                ],
                confidence_score=0.95,
                confidence_level="HIGH",
                duration_ms=4520,
            ),
        },
        {
            "kind": "trace",
            "trace": AgentTrace(
                agent_id="functional_genomics",
                division="Target Identification",
                status="complete",
                message="CRISPR knockout of BRCA1 sensitizes TNBC cell lines to DNA-damaging agents (log2FC=-3.2, FDR<0.001).",
                tools_called=[
                    ToolCall(tool_name="query_depmap", tool_input={"gene": "BRCA1", "lineage": "breast"}, result="Dependency score: -1.2 across 14 TNBC lines", duration_ms=980),
                    ToolCall(tool_name="execute_code", tool_input={"task": "differential dependency analysis"}, result="BRCA1 in top 2% dependencies for TNBC vs pan-cancer", duration_ms=1120),
                ],
                confidence_score=0.89,
                confidence_level="HIGH",
                duration_ms=3870,
            ),
        },
        {
            "kind": "trace",
            "trace": AgentTrace(
                agent_id="single_cell_atlas",
                division="Target Identification",
                status="complete",
                message="BRCA1 expression depleted in basal-like TNBC cluster (log2FC=-2.8). Highest expression in luminal progenitors.",
                tools_called=[
                    ToolCall(tool_name="simulate_expression", tool_input={"gene": "BRCA1", "dataset": "TCGA_BRCA_scRNA"}, result="5 cell clusters analyzed, basal cluster shows depletion", duration_ms=2340),
                ],
                confidence_score=0.78,
                confidence_level="MEDIUM",
                duration_ms=4100,
            ),
        },
        # --- Phase 2: Target Safety ---
        {
            "kind": "trace",
            "trace": AgentTrace(
                agent_id="fda_safety",
                division="Target Safety",
                status="complete",
                message="PARP inhibitors: manageable safety. Myelosuppression (Grade 3+: 24%), nausea (17%), fatigue (15%). No black box warnings.",
                tools_called=[
                    ToolCall(tool_name="query_faers", tool_input={"drug_class": "PARP inhibitors"}, result="1,247 AE reports analyzed across olaparib, rucaparib, niraparib", duration_ms=2100),
                    ToolCall(tool_name="query_clinical_trials", tool_input={"intervention": "PARP inhibitor", "condition": "TNBC"}, result="23 active trials, 8 Phase III", duration_ms=1340),
                ],
                confidence_score=0.85,
                confidence_level="HIGH",
                duration_ms=5210,
            ),
        },
        {
            "kind": "trace",
            "trace": AgentTrace(
                agent_id="toxicogenomics",
                division="Target Safety",
                status="complete",
                message="No off-target toxicity flags for BRCA1 pathway modulation. PARP1 selectivity confirmed by structural analysis.",
                tools_called=[
                    ToolCall(tool_name="query_pathways", tool_input={"gene": "BRCA1", "database": "Reactome"}, result="DNA Repair pathway — 47 downstream targets, no essential organ-specific genes", duration_ms=1560),
                ],
                confidence_score=0.82,
                confidence_level="HIGH",
                duration_ms=3200,
            ),
        },
        # --- Phase 3: Computational Biology ---
        {
            "kind": "trace",
            "trace": AgentTrace(
                agent_id="literature_synthesis",
                division="Computational Biology",
                status="complete",
                message="Systematic review: 247 publications confirm BRCA1 as validated oncology target. Level 1 evidence from OlympiAD (n=302) and EMBRACA (n=431).",
                tools_called=[
                    ToolCall(tool_name="search_pubmed", tool_input={"query": "BRCA1 PARP inhibitor triple-negative breast cancer", "max_results": 500}, result="247 relevant after dedup + filtering", duration_ms=1540),
                    ToolCall(tool_name="execute_code", tool_input={"task": "evidence grading"}, result="Level 1: 2 RCTs, Level 2: 14 cohort studies", duration_ms=670),
                ],
                confidence_score=0.88,
                confidence_level="HIGH",
                duration_ms=6130,
            ),
        },
        # --- Phase 4: Clinical Intelligence ---
        {
            "kind": "trace",
            "trace": AgentTrace(
                agent_id="clinical_trialist",
                division="Clinical Intelligence",
                status="complete",
                message="Olaparib monotherapy: 59.9% ORR in gBRCA+ HER2- MBC. PFS benefit 2.8 months (HR=0.58). Resistance via reversion mutations in 20-30%.",
                tools_called=[
                    ToolCall(tool_name="query_clinical_trials", tool_input={"nct": "NCT02000622"}, result="OlympiAD Phase III — primary endpoint met", duration_ms=890),
                ],
                confidence_score=0.91,
                confidence_level="HIGH",
                duration_ms=3400,
            ),
        },
        # --- Phase 5: Adversarial Review (low-confidence finding triggers HITL) ---
        {
            "kind": "trace",
            "trace": AgentTrace(
                agent_id="pharmacologist",
                division="Modality Selection",
                status="complete",
                message="Combination with anti-PD-L1 may overcome PARPi resistance, but clinical evidence is preliminary (Phase I/II only, n<50).",
                tools_called=[
                    ToolCall(tool_name="search_pubmed", tool_input={"query": "PARP inhibitor PD-L1 combination TNBC"}, result="12 publications, 3 clinical reports", duration_ms=1100),
                ],
                confidence_score=0.35,
                confidence_level="LOW",
                duration_ms=2800,
            ),
        },
        {
            "kind": "trace",
            "trace": AgentTrace(
                agent_id="review_panel",
                division="Orchestration",
                status="complete",
                message="3-pass adversarial review complete. 7/8 findings APPROVED. 1 finding flagged LOW confidence — routing to HITL.",
                tools_called=[
                    ToolCall(tool_name="execute_code", tool_input={"task": "confidence calibration across 8 claims"}, result="Mean confidence: 0.80. Outlier: pharmacologist claim at 0.35", duration_ms=440),
                ],
                confidence_score=0.91,
                confidence_level="HIGH",
                duration_ms=1800,
            ),
        },
        # --- HITL: auto-flag low-confidence finding ---
        {
            "kind": "hitl_flag",
            "hitl": {
                "finding": "Combination with anti-PD-L1 may overcome PARPi resistance, but clinical evidence is preliminary.",
                "agent_id": "pharmacologist",
                "confidence_score": 0.35,
                "reason": "Below 0.50 threshold. Phase I/II data only (n<50). No randomized evidence.",
                "status": "pending",
            },
        },
        # --- HITL: auto-resolved by domain expert ---
        {
            "kind": "hitl_resolved",
            "hitl": {
                "finding": "Combination with anti-PD-L1 may overcome PARPi resistance, but clinical evidence is preliminary.",
                "agent_id": "pharmacologist",
                "confidence_score": 0.35,
                "reason": "Domain expert: Include as hypothesis with explicit uncertainty. Recommend Phase II trial tracking.",
                "status": "approved",
            },
        },
        # --- Integration: Slack notification ---
        {
            "kind": "integration",
            "call": {
                "integration": "Slack",
                "action": "Posted findings summary to #target-validation",
                "status": "complete",
                "detail": "8 key findings, 1 HITL-reviewed. Overall confidence: HIGH (0.91).",
            },
        },
        # --- Integration: BioRender figure ---
        {
            "kind": "integration",
            "call": {
                "integration": "BioRender",
                "action": "Generated BRCA1-PARP synthetic lethality pathway diagram",
                "status": "complete",
                "detail": "DNA damage repair pathway with BRCA1 loss + PARP inhibition mechanism.",
            },
        },
        # --- Integration: Benchling notebook ---
        {
            "kind": "integration",
            "call": {
                "integration": "Benchling",
                "action": "Created notebook entry EXP-2026-0342",
                "status": "complete",
                "detail": "Linked target validation dossier to BRCA1-TNBC project.",
            },
        },
    ]


def _mock_response_text() -> str:
    return (
        "## BRCA1 Target Validation — TNBC\n\n"
        "### Executive Summary\n\n"
        "BRCA1 is a **validated synthetic lethality target** in triple-negative breast cancer. "
        "Convergent evidence across genetic association, functional genomics, and clinical trial data "
        "supports PARP inhibitor-based therapeutic strategies for BRCA1-mutant TNBC.\n\n"
        "---\n\n"
        "### Pipeline Execution\n\n"
        "- **Biosecurity**: Pre-screen PASSED (GREEN)\n"
        "- **Divisions activated**: Target Identification, Target Safety, Computational Biology, Clinical Intelligence, Modality Selection\n"
        "- **Agents dispatched**: 8 specialists across 5 divisions\n"
        "- **Review**: 3-pass adversarial review — 7/8 findings approved, 1 routed to HITL\n"
        "- **HITL**: Low-confidence finding reviewed and approved with caveats\n\n"
        "---\n\n"
        "### Key Findings\n\n"
        "| # | Finding | Agent | Confidence |\n"
        "|---|---------|-------|------------|\n"
        "| 1 | BRCA1 rs80357906 associated with TNBC (OR=11.2, p<1e-50) | statistical_genetics | **HIGH** 95% |\n"
        "| 2 | CRISPR KO sensitizes TNBC to DNA damage (log2FC=-3.2) | functional_genomics | **HIGH** 89% |\n"
        "| 3 | BRCA1 depleted in basal-like TNBC cluster | single_cell_atlas | **MED** 78% |\n"
        "| 4 | PARP inhibitors: manageable safety, myelosuppression primary AE | fda_safety | **HIGH** 85% |\n"
        "| 5 | No off-target toxicity flags for BRCA1 pathway | toxicogenomics | **HIGH** 82% |\n"
        "| 6 | 247 publications, Level 1 evidence (OlympiAD, EMBRACA) | literature_synthesis | **HIGH** 88% |\n"
        "| 7 | Olaparib 59.9% ORR in gBRCA+ HER2- MBC | clinical_trialist | **HIGH** 91% |\n"
        "| 8 | PD-L1 combination may address resistance *(HITL-reviewed)* | pharmacologist | **LOW** 35% |\n\n"
        "---\n\n"
        "### Risk Assessment\n\n"
        "- **Safety**: Moderate — myelosuppression is dose-limiting, but well-characterized from existing PARPi programs\n"
        "- **Feasibility**: Low risk — established clinical pathway, 23 active trials\n"
        "- **Resistance**: 20-30% reversion mutation rate; combination strategies under investigation\n\n"
        "### Recommended Experiments\n\n"
        "1. Validate BRCA1 promoter methylation as PARPi sensitivity biomarker in patient-derived organoids\n"
        "2. Assess olaparib + anti-PD-L1 synergy in syngeneic TNBC models\n"
        "3. Profile resistance mutations via longitudinal liquid biopsy in OlympiAD cohort\n\n"
        "### Integrations\n\n"
        "- Findings posted to **#target-validation** on Slack\n"
        "- Pathway diagram generated via **BioRender**\n"
        "- Notebook entry **EXP-2026-0342** created in **Benchling**\n\n"
        "---\n\n"
        "*Overall confidence: **HIGH** (0.91) · Cost: $4.72 · Duration: 4m 47s · 8 agents · 5 divisions*"
    )


@router.get("")
async def list_chats() -> list[Chat]:
    return sorted(_chats.values(), key=lambda c: c.updated_at, reverse=True)


@router.post("")
async def create_chat(req: CreateChatRequest) -> Chat:
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
    chat = _chats[chat_id]
    # Only add user message if it's not a duplicate of the last message
    last = chat.messages[-1] if chat.messages else None
    if not last or last.role != Role.USER or last.content != req.content:
        user_msg = Message(id=str(uuid.uuid4())[:8], role=Role.USER, content=req.content)
        chat.messages.append(user_msg)

    async def stream():
        msg_id = str(uuid.uuid4())[:8]
        pipeline = _pipeline_traces()
        all_traces: list[AgentTrace] = []
        all_hitl: list[HitlEvent] = []
        all_integrations: list[IntegrationEvent] = []

        for step in pipeline:
            kind = step["kind"]

            if kind == "trace":
                trace: AgentTrace = step["trace"]
                trace_running = trace.model_copy(update={"status": "running", "message": "", "tools_called": []})
                yield f"data: {json.dumps({'type': 'trace_start', 'message_id': msg_id, 'trace': trace_running.model_dump()})}\n\n"
                await asyncio.sleep(0.4)

                for tool in trace.tools_called:
                    yield f"data: {json.dumps({'type': 'tool_call', 'message_id': msg_id, 'agent_id': trace.agent_id, 'tool': tool.model_dump()})}\n\n"
                    await asyncio.sleep(0.25)

                yield f"data: {json.dumps({'type': 'trace_complete', 'message_id': msg_id, 'trace': trace.model_dump()})}\n\n"
                all_traces.append(trace)
                await asyncio.sleep(0.15)

            elif kind == "hitl_flag":
                yield f"data: {json.dumps({'type': 'hitl_flag', 'message_id': msg_id, 'hitl': step['hitl']})}\n\n"
                await asyncio.sleep(1.2)

            elif kind == "hitl_resolved":
                hitl_data = step["hitl"]
                all_hitl.append(HitlEvent(**hitl_data))
                yield f"data: {json.dumps({'type': 'hitl_resolved', 'message_id': msg_id, 'hitl': hitl_data})}\n\n"
                await asyncio.sleep(0.5)

            elif kind == "integration":
                int_data = step["call"]
                all_integrations.append(IntegrationEvent(**int_data))
                yield f"data: {json.dumps({'type': 'integration', 'message_id': msg_id, 'call': int_data})}\n\n"
                await asyncio.sleep(0.4)

        # Stream final synthesis
        text = _mock_response_text()
        chunks = [text[i:i + 100] for i in range(0, len(text), 100)]
        accumulated = ""
        for chunk in chunks:
            accumulated += chunk
            yield f"data: {json.dumps({'type': 'text_delta', 'message_id': msg_id, 'delta': chunk})}\n\n"
            await asyncio.sleep(0.03)

        assistant_msg = Message(
            id=msg_id,
            role=Role.ASSISTANT,
            content=accumulated,
            agent_traces=all_traces,
            hitl_events=all_hitl,
            integration_events=all_integrations,
        )
        chat.messages.append(assistant_msg)
        chat.updated_at = datetime.now(timezone.utc)

        yield f"data: {json.dumps({'type': 'done', 'message_id': msg_id})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
