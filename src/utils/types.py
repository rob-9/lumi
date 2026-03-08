"""Core structured output types for Lumi Virtual Lab.

All Pydantic v2 models used across the agentic swarm for
structured data exchange, serialization, and validation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class Priority(str, Enum):
    """Task priority levels used by the CSO orchestrator."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TaskStatus(str, Enum):
    """Lifecycle status of an orchestrated task."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ConfidenceLevel(str, Enum):
    """Discrete confidence buckets for evidence-backed claims."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"


class ReviewVerdictType(str, Enum):
    """Verdict emitted by the Review Panel agent."""
    APPROVE = "APPROVE"
    REVISE = "REVISE"
    REJECT = "REJECT"


class BiosecurityCategory(str, Enum):
    """Biosecurity threat-level classification (traffic-light scheme)."""
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"


# ---------------------------------------------------------------------------
# Evidence & Confidence Models
# ---------------------------------------------------------------------------

class EvidenceSource(BaseModel):
    """Tracks the provenance of a single piece of evidence."""
    source_db: str = Field(..., description="Database or service the evidence came from (e.g. 'PubMed', 'UniProt').")
    source_id: str = Field(..., description="Identifier within the source database (e.g. PMID, accession).")
    access_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When the source was accessed.")
    data_version: Optional[str] = Field(default=None, description="Version or release tag of the source dataset.")
    query_params: Optional[dict] = Field(default=None, description="Parameters used to retrieve this evidence.")


class ConfidenceAssessment(BaseModel):
    """Calibrated confidence assessment attached to every claim."""
    level: ConfidenceLevel = Field(..., description="Discrete confidence bucket.")
    score: float = Field(..., ge=0.0, le=1.0, description="Continuous confidence score between 0 and 1.")
    evidence_convergence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Degree to which independent sources agree.")
    statistical_significance: Optional[float] = Field(default=None, description="p-value or equivalent measure (lower is more significant).")
    effect_size: Optional[float] = Field(default=None, description="Magnitude of the observed effect.")
    methodology_robustness: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Quality score of the methodology behind the evidence.")
    independent_replication: Optional[int] = Field(default=None, ge=0, description="Number of independent replications supporting the claim.")
    caveats: list[str] = Field(default_factory=list, description="Known limitations or caveats.")
    alternative_explanations: list[str] = Field(default_factory=list, description="Plausible alternative interpretations of the evidence.")


# ---------------------------------------------------------------------------
# Claims & Tasks
# ---------------------------------------------------------------------------

class Claim(BaseModel):
    """A single scientific claim produced by an agent, with full provenance."""
    claim_text: str = Field(..., description="Natural-language statement of the claim.")
    supporting_evidence: list[EvidenceSource] = Field(default_factory=list, description="Evidence sources that support this claim.")
    contradicting_evidence: list[EvidenceSource] = Field(default_factory=list, description="Evidence sources that contradict this claim.")
    confidence: ConfidenceAssessment = Field(..., description="Calibrated confidence assessment for this claim.")
    agent_id: str = Field(..., description="Identifier of the agent that produced this claim.")
    methodology: Optional[str] = Field(default=None, description="Description of the methodology used to arrive at this claim.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When this claim was produced.")


class Task(BaseModel):
    """A unit of work dispatched by the orchestrator."""
    task_id: str = Field(..., description="Unique task identifier.")
    description: str = Field(..., description="Human-readable description of what needs to be done.")
    division: Optional[str] = Field(default=None, description="Division responsible for this task.")
    agent: Optional[str] = Field(default=None, description="Specific agent assigned to this task.")
    priority: Priority = Field(default=Priority.MEDIUM, description="Task priority.")
    dependencies: list[str] = Field(default_factory=list, description="Task IDs that must complete before this task.")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status of the task.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Task creation timestamp.")


# ---------------------------------------------------------------------------
# Agent Results & Division Reports
# ---------------------------------------------------------------------------

class AgentResult(BaseModel):
    """Structured output from a single specialist agent execution."""
    agent_id: str = Field(..., description="Identifier of the agent that produced this result.")
    task_id: str = Field(..., description="Task this result corresponds to.")
    findings: list[Claim] = Field(default_factory=list, description="Scientific claims produced by the agent.")
    raw_data: dict = Field(default_factory=dict, description="Unstructured data collected during execution.")
    code_executed: list[str] = Field(default_factory=list, description="Code snippets that were executed.")
    tools_used: list[str] = Field(default_factory=list, description="Names of MCP tools invoked during execution.")
    cost: float = Field(default=0.0, ge=0.0, description="LLM API cost in USD for this agent run.")
    duration_seconds: float = Field(default=0.0, ge=0.0, description="Wall-clock duration of the agent run.")
    model_used: str = Field(default="claude-sonnet-4-6", description="Model used for this agent run.")


class DivisionReport(BaseModel):
    """Aggregated report from a division lead combining specialist results."""
    division_id: str = Field(..., description="Unique division identifier.")
    division_name: str = Field(..., description="Human-readable division name.")
    lead_agent: str = Field(..., description="ID of the division lead agent.")
    specialist_results: list[AgentResult] = Field(default_factory=list, description="Results from each specialist under this division.")
    synthesis: str = Field(default="", description="Division lead's synthesis of specialist findings.")
    confidence: ConfidenceAssessment = Field(..., description="Overall confidence assessment for this division's output.")
    lateral_flags: list[str] = Field(default_factory=list, description="Cross-division flags raised for other divisions to address.")


# ---------------------------------------------------------------------------
# Execution Planning
# ---------------------------------------------------------------------------

class Phase(BaseModel):
    """A single phase in an execution plan."""
    phase_id: int = Field(..., description="Sequential phase number.")
    name: str = Field(..., description="Human-readable phase name.")
    division: Optional[str] = Field(default=None, description="Primary division responsible.")
    agents: list[str] = Field(default_factory=list, description="Agent IDs involved in this phase.")
    dependencies: list[int] = Field(default_factory=list, description="Phase IDs that must complete first.")
    parallel_eligible: bool = Field(default=False, description="Whether agents in this phase can run in parallel.")
    priority: Priority = Field(default=Priority.MEDIUM, description="Phase priority.")
    estimated_cost: float = Field(default=0.0, ge=0.0, description="Estimated LLM cost in USD.")
    conditional_next: dict = Field(default_factory=dict, description="Mapping of outcome conditions to next phase IDs.")


class ExecutionPlan(BaseModel):
    """Full execution plan produced by the CSO orchestrator."""
    query_id: str = Field(..., description="Unique identifier for the user query.")
    user_query: str = Field(..., description="Original user query text.")
    confirmed_scope: str = Field(default="", description="Scope as confirmed/refined by the orchestrator.")
    phases: list[Phase] = Field(default_factory=list, description="Ordered list of execution phases.")
    lateral_channels: list[dict] = Field(default_factory=list, description="Cross-division communication channels.")
    estimated_total_cost: float = Field(default=0.0, ge=0.0, description="Estimated total cost in USD.")
    includes_design: bool = Field(default=False, description="Whether the plan includes molecular design.")
    includes_experimental: bool = Field(default=False, description="Whether the plan includes experimental validation protocols.")


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------

class ReviewVerdict(BaseModel):
    """Output of the Review Panel adversarial quality gate."""
    verdict: ReviewVerdictType = Field(..., description="Overall review verdict.")
    issues: list[dict] = Field(
        default_factory=list,
        description="List of issues found. Each dict has keys: priority (str), description (str), required_fix (str).",
    )
    missing_analyses: list[str] = Field(default_factory=list, description="Analyses that should have been performed but were not.")
    confidence_assessment: str = Field(default="", description="Reviewer's narrative assessment of confidence quality.")


# ---------------------------------------------------------------------------
# Biosecurity
# ---------------------------------------------------------------------------

class BiosecurityScreenResult(BaseModel):
    """Result from a single biosecurity screening agent."""
    screen_name: str = Field(..., description="Name of the screening method (e.g. 'BLAST select agent', 'toxin motif').")
    passed: bool = Field(..., description="Whether the sequence passed this screen (True = safe).")
    category: BiosecurityCategory = Field(default=BiosecurityCategory.GREEN, description="Threat-level classification.")
    details: str = Field(default="", description="Human-readable explanation of the screening outcome.")
    highest_identity: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Highest sequence identity percentage to a flagged organism.")
    flagged_domains: list[str] = Field(default_factory=list, description="Protein domains flagged as concerning.")


class BiosecurityAssessment(BaseModel):
    """Aggregated biosecurity assessment with veto authority."""
    category: BiosecurityCategory = Field(..., description="Overall biosecurity category.")
    agent_results: list[BiosecurityScreenResult] = Field(default_factory=list, description="Results from each screening agent.")
    veto: bool = Field(default=False, description="Whether biosecurity has vetoed proceeding.")
    veto_reasons: list[str] = Field(default_factory=list, description="Reasons for the veto, if applicable.")
    audit_id: str = Field(default="", description="Unique audit trail identifier for compliance.")


# ---------------------------------------------------------------------------
# Final Report
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Dynamic SubLab Planning
# ---------------------------------------------------------------------------

class AgentSpec(BaseModel):
    """Specification for a dynamically created agent in a SubLab."""
    name: str = Field(..., description="Human-readable agent name (e.g. 'Genomic Evidence Analyst').")
    role: str = Field(..., description="One-sentence role description.")
    tools: list[str] = Field(default_factory=list, description="Tool names from the catalog.")
    domains: list[str] = Field(default_factory=list, description="Domain keys for prompt composition.")
    model_tier: str = Field(default="SONNET", description="Model tier: 'OPUS', 'SONNET', or 'HAIKU'.")


class SubLabPlan(BaseModel):
    """LLM-generated plan for a dynamic multi-agent team."""
    agents: list[AgentSpec] = Field(default_factory=list, description="Agent specifications.")
    execution_groups: list[list[str]] = Field(
        default_factory=list,
        description="Sequential groups of agent names; agents within a group run in parallel.",
    )
    rationale: str = Field(default="", description="LLM rationale for the team composition.")


class FinalReport(BaseModel):
    """Complete output delivered to the user after all phases complete."""
    query_id: str = Field(..., description="Unique identifier for the user query.")
    user_query: str = Field(..., description="Original user query.")
    executive_summary: str = Field(default="", description="High-level summary of findings.")
    evidence_synthesis: dict = Field(default_factory=dict, description="Structured synthesis of evidence across divisions.")
    key_findings: list[Claim] = Field(default_factory=list, description="Most important claims with provenance.")
    risk_assessment: dict = Field(default_factory=dict, description="Risk analysis including safety and feasibility.")
    molecular_design_candidates: Optional[list[dict]] = Field(default=None, description="Designed molecules if the plan included molecular design.")
    biosecurity_clearance: Optional[BiosecurityAssessment] = Field(default=None, description="Biosecurity screening outcome.")
    recommended_experiments: list[dict] = Field(default_factory=list, description="Suggested wet-lab experiments to validate findings.")
    limitations: list[str] = Field(default_factory=list, description="Known limitations and caveats of this analysis.")
    total_cost: float = Field(default=0.0, ge=0.0, description="Total LLM API cost in USD.")
    total_duration_seconds: float = Field(default=0.0, ge=0.0, description="Total wall-clock duration.")
    provenance_chain: list[EvidenceSource] = Field(default_factory=list, description="Complete chain of evidence sources used.")
    living_document_markdown: str = Field(default="", description="Rendered living document narrative (Markdown).")
    hitl_summary: str = Field(default="", description="Human-in-the-loop routing summary.")
    figures: list[dict] = Field(default_factory=list, description="Visual context figures (title, caption, image_url, figure_type).")
