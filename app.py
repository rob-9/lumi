"""Lumi Virtual Lab -- Streamlit development UI.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from src.utils.types import (
    AgentResult,
    Claim,
    ConfidenceAssessment,
    ConfidenceLevel,
    DivisionReport,
    EvidenceSource,
    ExecutionPlan,
    FinalReport,
    Phase,
    Priority,
    Task,
    TaskStatus,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUBLABS: dict[str, dict] = {
    "Target Validation": {
        "description": "Evidence dossiers with pathway diagrams and confidence scores",
        "agents": ["target_biologist", "bio_pathways", "literature_synthesis", "fda_safety"],
        "divisions": ["Target Identification", "Target Safety", "Computational Biology"],
        "examples": [
            "Evaluate BRCA1 as a therapeutic target for triple-negative breast cancer",
            "Assess PCSK9 inhibition safety profile based on genetic evidence",
            "Validate KRAS G12C as a druggable target in non-small cell lung cancer",
        ],
    },
    "Assay Troubleshooting": {
        "description": "Root-cause analysis of unexpected experimental results",
        "agents": ["assay_design", "functional_genomics", "single_cell_atlas"],
        "divisions": ["Experimental Design", "Target Identification"],
        "examples": [
            "Why is my ELISA showing high background in serum samples?",
            "Troubleshoot low transfection efficiency in HEK293 cells",
            "Diagnose inconsistent IC50 values across plate replicates",
        ],
    },
    "Biomarker Curation": {
        "description": "Panel candidates with expression heatmaps",
        "agents": ["statistical_genetics", "single_cell_atlas", "clinical_trialist"],
        "divisions": ["Target Identification", "Clinical Intelligence"],
        "examples": [
            "Identify circulating biomarkers for early pancreatic cancer detection",
            "Curate a pharmacodynamic biomarker panel for JAK inhibitor response",
            "Find predictive biomarkers for immune checkpoint inhibitor response",
        ],
    },
    "Regulatory Submissions": {
        "description": "Tox literature reviews with MoA illustrations",
        "agents": ["toxicogenomics", "pharmacologist", "fda_safety", "literature_synthesis"],
        "divisions": ["Target Safety", "Computational Biology", "Clinical Intelligence"],
        "examples": [
            "Prepare a nonclinical toxicology summary for an anti-CD20 antibody",
            "Review hepatotoxicity signals for kinase inhibitor class",
            "Compile mechanism-of-action safety assessment for bispecific antibody",
        ],
    },
    "Lead Optimization": {
        "description": "Multi-parameter optimization of drug candidates",
        "agents": ["lead_optimization", "antibody_engineer", "developability", "structure_design"],
        "divisions": ["Molecular Design", "Modality Selection"],
        "examples": [
            "Optimize a lead compound for improved oral bioavailability and reduced hERG liability",
            "Improve thermostability of anti-HER2 antibody without losing affinity",
            "Design selective kinase inhibitor with improved metabolic stability",
        ],
    },
    "Clinical Translation": {
        "description": "Go/no-go evidence packages for IND-enabling studies",
        "agents": ["clinical_trialist", "pharmacologist", "statistical_genetics", "fda_safety"],
        "divisions": ["Clinical Intelligence", "Target Safety", "Computational Biology"],
        "examples": [
            "Build go/no-go evidence package for anti-IL-17 antibody IND filing",
            "Assess clinical translatability of preclinical efficacy data for NASH target",
            "Evaluate first-in-human dose selection strategy for bispecific T-cell engager",
        ],
    },
}

# All agents in the system, grouped by division
AGENTS_BY_DIVISION: dict[str, list[str]] = {
    "Target Identification": ["statistical_genetics", "functional_genomics", "single_cell_atlas"],
    "Target Safety": ["bio_pathways", "fda_safety", "toxicogenomics"],
    "Modality Selection": ["target_biologist", "pharmacologist"],
    "Molecular Design": ["protein_intelligence", "antibody_engineer", "structure_design", "lead_optimization", "developability"],
    "Clinical Intelligence": ["clinical_trialist"],
    "Computational Biology": ["literature_synthesis"],
    "Experimental Design": ["assay_design"],
    "Biosecurity": ["dual_use_screening"],
}


# ---------------------------------------------------------------------------
# Mock data generators
# ---------------------------------------------------------------------------

def _mock_confidence(level: ConfidenceLevel, score: float) -> ConfidenceAssessment:
    return ConfidenceAssessment(
        level=level,
        score=score,
        evidence_convergence=round(score * 0.9, 2),
        methodology_robustness=round(score * 0.85, 2),
        independent_replication=max(1, int(score * 5)),
        caveats=["Limited to publicly available data", "In-silico predictions only"],
        alternative_explanations=["Off-target effects not fully explored"],
    )


def _mock_claim(text: str, agent: str, level: ConfidenceLevel, score: float) -> Claim:
    return Claim(
        claim_text=text,
        supporting_evidence=[
            EvidenceSource(source_db="PubMed", source_id="PMID:38291045"),
            EvidenceSource(source_db="UniProt", source_id="P38398"),
        ],
        contradicting_evidence=[
            EvidenceSource(source_db="PubMed", source_id="PMID:37104562"),
        ],
        confidence=_mock_confidence(level, score),
        agent_id=agent,
        methodology="Systematic literature review and pathway analysis",
    )


def _mock_final_report() -> FinalReport:
    return FinalReport(
        query_id="q_demo_001",
        user_query="Evaluate BRCA1 as a therapeutic target for triple-negative breast cancer",
        executive_summary=(
            "BRCA1 shows strong evidence as a synthetic lethality target in TNBC. "
            "PARP inhibitor combinations demonstrate significant clinical benefit in "
            "BRCA1-mutant populations. Biomarker-guided patient selection is critical "
            "for therapeutic success. Safety profile is manageable with appropriate "
            "monitoring protocols."
        ),
        evidence_synthesis={
            "genetic_evidence": "Strong GWAS and functional genomics support",
            "pathway_analysis": "Central role in DNA damage repair confirmed",
            "clinical_correlation": "Response rates correlate with mutation status",
        },
        key_findings=[
            _mock_claim(
                "BRCA1 loss-of-function mutations confer synthetic lethality with PARP inhibition in TNBC cell lines and xenograft models.",
                "target_biologist",
                ConfidenceLevel.HIGH,
                0.92,
            ),
            _mock_claim(
                "Olaparib monotherapy achieves 59.9% objective response rate in germline BRCA-mutated HER2-negative metastatic breast cancer.",
                "clinical_trialist",
                ConfidenceLevel.HIGH,
                0.88,
            ),
            _mock_claim(
                "BRCA1 promoter methylation may serve as an additional biomarker for PARP inhibitor sensitivity beyond germline mutations.",
                "statistical_genetics",
                ConfidenceLevel.MEDIUM,
                0.65,
            ),
            _mock_claim(
                "Resistance mechanisms include BRCA1 reversion mutations and upregulation of drug efflux pumps, observed in 20-30% of patients.",
                "literature_synthesis",
                ConfidenceLevel.MEDIUM,
                0.71,
            ),
            _mock_claim(
                "Combination with immune checkpoint inhibitors may overcome resistance but requires further clinical validation.",
                "pharmacologist",
                ConfidenceLevel.LOW,
                0.35,
            ),
        ],
        risk_assessment={
            "safety_risk": "Moderate -- myelosuppression is the primary dose-limiting toxicity",
            "feasibility_risk": "Low -- established clinical pathway for PARP inhibitors",
            "commercial_risk": "Medium -- competitive landscape with multiple approved PARP inhibitors",
        },
        recommended_experiments=[
            {"experiment": "Validate BRCA1 methylation as PARPi sensitivity biomarker in patient-derived organoids", "priority": "HIGH"},
            {"experiment": "Assess combination synergy with anti-PD-L1 in syngeneic TNBC models", "priority": "MEDIUM"},
            {"experiment": "Profile resistance mutations in longitudinal liquid biopsy cohort", "priority": "HIGH"},
        ],
        limitations=[
            "Analysis limited to publicly available clinical trial data",
            "In-silico pathway analysis may not capture all tissue-specific effects",
            "Resistance mechanism frequencies based on limited patient cohorts",
        ],
        total_cost=4.72,
        total_duration_seconds=287.4,
    )


def _mock_division_reports() -> list[DivisionReport]:
    return [
        DivisionReport(
            division_id="div_target_identification",
            division_name="Target Identification",
            lead_agent="target_id_lead",
            specialist_results=[
                AgentResult(
                    agent_id="statistical_genetics",
                    task_id="task_gwas_review",
                    findings=[
                        _mock_claim(
                            "BRCA1 rs80357906 is strongly associated with TNBC risk (OR=11.2, p<1e-50).",
                            "statistical_genetics",
                            ConfidenceLevel.HIGH,
                            0.95,
                        ),
                    ],
                    tools_used=["query_gwas_catalog", "execute_code"],
                    cost=0.82,
                    duration_seconds=45.2,
                ),
                AgentResult(
                    agent_id="functional_genomics",
                    task_id="task_crispr_screens",
                    findings=[
                        _mock_claim(
                            "CRISPR knockout of BRCA1 sensitizes TNBC cells to DNA-damaging agents (log2FC=-3.2).",
                            "functional_genomics",
                            ConfidenceLevel.HIGH,
                            0.89,
                        ),
                    ],
                    tools_used=["query_depmap", "execute_code"],
                    cost=0.65,
                    duration_seconds=38.7,
                ),
            ],
            synthesis="Strong convergent evidence from GWAS and functional screens supports BRCA1 as a validated TNBC target.",
            confidence=_mock_confidence(ConfidenceLevel.HIGH, 0.91),
        ),
        DivisionReport(
            division_id="div_target_safety",
            division_name="Target Safety",
            lead_agent="target_safety_lead",
            specialist_results=[
                AgentResult(
                    agent_id="fda_safety",
                    task_id="task_fda_review",
                    findings=[
                        _mock_claim(
                            "PARP inhibitors targeting BRCA1 synthetic lethality have a manageable safety profile with myelosuppression as the primary AE.",
                            "fda_safety",
                            ConfidenceLevel.HIGH,
                            0.85,
                        ),
                    ],
                    tools_used=["query_faers", "execute_code"],
                    cost=0.71,
                    duration_seconds=42.1,
                ),
            ],
            synthesis="Safety profile is well-characterized from existing PARP inhibitor programs. No unexpected liabilities identified.",
            confidence=_mock_confidence(ConfidenceLevel.HIGH, 0.85),
        ),
        DivisionReport(
            division_id="div_computational_biology",
            division_name="Computational Biology",
            lead_agent="compbio_lead",
            specialist_results=[
                AgentResult(
                    agent_id="literature_synthesis",
                    task_id="task_lit_review",
                    findings=[
                        _mock_claim(
                            "Systematic review of 247 publications confirms BRCA1 as a well-validated oncology target with level 1 clinical evidence.",
                            "literature_synthesis",
                            ConfidenceLevel.HIGH,
                            0.88,
                        ),
                    ],
                    tools_used=["search_pubmed", "execute_code"],
                    cost=0.93,
                    duration_seconds=61.3,
                ),
            ],
            synthesis="Literature strongly supports BRCA1 targeting. No major contradictory evidence identified in recent publications.",
            confidence=_mock_confidence(ConfidenceLevel.HIGH, 0.88),
        ),
    ]


def _mock_debate_rounds() -> list[dict]:
    """Mock multi-agent debate data for confidence scoring visualization."""
    return [
        {
            "round": 1,
            "agent_id": "target_biologist",
            "position": "support",
            "argument": "BRCA1 loss-of-function is well-established as a synthetic lethality target. Multiple preclinical models confirm PARP sensitivity.",
            "evidence": ["PMID:38291045", "PMID:36842073"],
        },
        {
            "round": 1,
            "agent_id": "literature_synthesis",
            "position": "support",
            "argument": "247 publications consistently support BRCA1 as a validated target. Level 1 clinical evidence from OlympiAD and EMBRACA trials.",
            "evidence": ["PMID:28578601", "PMID:29863767"],
        },
        {
            "round": 2,
            "agent_id": "pharmacologist",
            "position": "challenge",
            "argument": "Resistance via reversion mutations is observed in 20-30% of patients. Long-term durability of response remains uncertain.",
            "evidence": ["PMID:37104562"],
        },
        {
            "round": 2,
            "agent_id": "fda_safety",
            "position": "neutral",
            "argument": "Safety profile is manageable but myelosuppression requires monitoring. Risk-benefit is favorable for BRCA-mutant patients specifically.",
            "evidence": ["PMID:35436722"],
        },
        {
            "round": 3,
            "agent_id": "target_biologist",
            "position": "support",
            "argument": "Acknowledging resistance concern — combination strategies with checkpoint inhibitors may address durability. Biomarker selection mitigates risk.",
            "evidence": ["PMID:39012345"],
        },
    ]


def _mock_execution_plan() -> ExecutionPlan:
    return ExecutionPlan(
        query_id="q_demo_001",
        user_query="Evaluate BRCA1 as a therapeutic target for triple-negative breast cancer",
        confirmed_scope="Full target validation dossier including genetic evidence, safety, and clinical translatability",
        phases=[
            Phase(
                phase_id=1,
                name="Genetic Evidence Collection",
                division="Target Identification",
                agents=["statistical_genetics", "functional_genomics", "single_cell_atlas"],
                dependencies=[],
                parallel_eligible=True,
                priority=Priority.HIGH,
                estimated_cost=1.50,
            ),
            Phase(
                phase_id=2,
                name="Safety Assessment",
                division="Target Safety",
                agents=["fda_safety", "toxicogenomics", "bio_pathways"],
                dependencies=[1],
                parallel_eligible=True,
                priority=Priority.HIGH,
                estimated_cost=1.20,
            ),
            Phase(
                phase_id=3,
                name="Literature Synthesis",
                division="Computational Biology",
                agents=["literature_synthesis"],
                dependencies=[],
                parallel_eligible=False,
                priority=Priority.MEDIUM,
                estimated_cost=0.80,
            ),
            Phase(
                phase_id=4,
                name="Clinical Translatability",
                division="Clinical Intelligence",
                agents=["clinical_trialist"],
                dependencies=[1, 2],
                parallel_eligible=False,
                priority=Priority.MEDIUM,
                estimated_cost=0.70,
            ),
            Phase(
                phase_id=5,
                name="Final Synthesis & Report",
                division=None,
                agents=[],
                dependencies=[1, 2, 3, 4],
                parallel_eligible=False,
                priority=Priority.HIGH,
                estimated_cost=0.50,
            ),
        ],
        estimated_total_cost=4.70,
    )


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def confidence_badge(level: ConfidenceLevel) -> str:
    """Return a colored label string for a confidence level."""
    color_map = {
        ConfidenceLevel.HIGH: "green",
        ConfidenceLevel.MEDIUM: "orange",
        ConfidenceLevel.LOW: "red",
        ConfidenceLevel.INSUFFICIENT: "gray",
    }
    color = color_map.get(level, "gray")
    return f":{color}[**{level.value}**]"


def render_confidence_score(conf: ConfidenceAssessment) -> None:
    """Render a confidence assessment with badge and progress bar."""
    cols = st.columns([1, 2])
    with cols[0]:
        st.markdown(confidence_badge(conf.level))
    with cols[1]:
        st.progress(conf.score, text=f"{conf.score:.0%}")

    if conf.caveats:
        with st.expander("Caveats"):
            for caveat in conf.caveats:
                st.markdown(f"- {caveat}")

    if conf.alternative_explanations:
        with st.expander("Alternative explanations"):
            for alt in conf.alternative_explanations:
                st.markdown(f"- {alt}")


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

def init_session_state() -> None:
    defaults = {
        "selected_sublab": "Target Validation",
        "query_text": "",
        "submitted_query": None,
        "mock_report": None,
        "mock_divisions": None,
        "mock_plan": None,
        "mock_debate": None,
        "hitl_reviews": {},
        "generated_figures": {},
        "tamarind_jobs": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar() -> None:
    with st.sidebar:
        st.title("Lumi Virtual Lab")
        st.caption("Agentic drug discovery platform")
        st.divider()

        # Sublab selector
        st.subheader("Sublab")
        selected = st.selectbox(
            "Choose a sublab",
            list(SUBLABS.keys()),
            index=list(SUBLABS.keys()).index(st.session_state.selected_sublab),
            label_visibility="collapsed",
        )
        st.session_state.selected_sublab = selected

        sublab_info = SUBLABS[selected]
        st.caption(sublab_info["description"])

        st.divider()

        # Agent status indicators
        st.subheader("Agent Status")
        sublab_agents = set(sublab_info["agents"])
        all_agents_flat = {a for agents in AGENTS_BY_DIVISION.values() for a in agents}

        for division, agents in AGENTS_BY_DIVISION.items():
            with st.expander(division, expanded=False):
                for agent in agents:
                    if agent in sublab_agents:
                        st.markdown(f":green_circle: `{agent}` -- active")
                    elif agent in all_agents_flat:
                        st.markdown(f":white_circle: `{agent}` -- available")

        st.divider()
        st.caption("v0.1.0-dev")


# ---------------------------------------------------------------------------
# Tab 1: Submit Query
# ---------------------------------------------------------------------------

def render_submit_tab() -> None:
    st.header("Submit Research Query")

    sublab = st.session_state.selected_sublab
    sublab_info = SUBLABS[sublab]

    st.info(f"Sublab: **{sublab}** -- {sublab_info['description']}")

    # Example queries as quick-fill buttons
    st.subheader("Example queries")
    example_cols = st.columns(len(sublab_info["examples"]))
    for i, example in enumerate(sublab_info["examples"]):
        with example_cols[i]:
            if st.button(
                f"Example {i + 1}",
                key=f"example_{sublab}_{i}",
                help=example,
                use_container_width=True,
            ):
                st.session_state.query_text = example

    # Query input
    query = st.text_area(
        "Research question",
        value=st.session_state.query_text,
        height=120,
        placeholder="Enter your research question here...",
    )
    st.session_state.query_text = query

    # Active agents for this sublab
    st.markdown("**Agents that will be activated:**")
    agent_cols = st.columns(4)
    for i, agent in enumerate(sublab_info["agents"]):
        with agent_cols[i % 4]:
            st.code(agent)

    # Submit button
    st.divider()
    if st.button("Submit Query", type="primary", disabled=not query.strip()):
        st.session_state.submitted_query = {
            "query": query,
            "sublab": sublab,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents": sublab_info["agents"],
            "divisions": sublab_info["divisions"],
        }
        # Populate mock data so the Results tab has something to show
        st.session_state.mock_report = _mock_final_report()
        st.session_state.mock_divisions = _mock_division_reports()
        st.session_state.mock_plan = _mock_execution_plan()
        st.session_state.mock_debate = _mock_debate_rounds()
        st.success("Query submitted! Switch to the **Results** tab to view output.")

    # Show last submitted query
    if st.session_state.submitted_query:
        with st.expander("Last submitted query"):
            st.json(st.session_state.submitted_query)


# ---------------------------------------------------------------------------
# Tab 2: Results
# ---------------------------------------------------------------------------

def render_results_tab() -> None:
    st.header("Results")

    report: FinalReport | None = st.session_state.mock_report
    divisions: list[DivisionReport] | None = st.session_state.mock_divisions

    if report is None:
        st.info("No results yet. Submit a query from the **Submit Query** tab.")
        return

    # Executive summary
    st.subheader("Executive Summary")
    st.markdown(report.executive_summary)

    # Metadata row
    meta_cols = st.columns(3)
    with meta_cols[0]:
        st.metric("Total Cost", f"${report.total_cost:.2f}")
    with meta_cols[1]:
        st.metric("Duration", f"{report.total_duration_seconds:.0f}s")
    with meta_cols[2]:
        st.metric("Key Findings", str(len(report.key_findings)))

    st.divider()

    # --- Visual Context (#3, #4) --------------------------------------------
    st.subheader("Visual Context")

    # Display generated figures if available in session state, otherwise show placeholders
    figures: dict[str, str] = st.session_state.get("generated_figures", {})

    fig_cols = st.columns(3)
    figure_slots = [
        ("Pathway Diagram", "pathway_diagram", "Signaling pathway for the target of interest"),
        ("Expression Heatmap", "expression_heatmap", "Tissue/cell-type expression profile"),
        ("Mechanism of Action", "moa_diagram", "Drug-target interaction illustration"),
    ]
    for col, (title, fig_key, caption) in zip(fig_cols, figure_slots):
        with col:
            st.markdown(f"**{title}**")
            url = figures.get(fig_key)
            if url:
                st.image(url, caption=caption, use_container_width=True)
            else:
                with st.container(border=True, height=200):
                    st.caption(caption)
                    st.caption(":gray[Submit a query to generate figures]")

    # Additional figures row (if generated)
    extra_keys = [k for k in figures if k not in {"pathway_diagram", "expression_heatmap", "moa_diagram"}]
    if extra_keys:
        extra_cols = st.columns(min(len(extra_keys), 3))
        for i, key in enumerate(extra_keys):
            with extra_cols[i % 3]:
                label = key.replace("_", " ").title()
                st.image(figures[key], caption=label, use_container_width=True)

    st.divider()

    # Key findings with confidence
    st.subheader("Key Findings")
    for i, claim in enumerate(report.key_findings):
        with st.container(border=True):
            st.markdown(f"**Finding {i + 1}** ({claim.agent_id})")
            st.markdown(claim.claim_text)
            render_confidence_score(claim.confidence)

            with st.expander("Evidence"):
                if claim.supporting_evidence:
                    st.markdown("**Supporting:**")
                    for ev in claim.supporting_evidence:
                        st.markdown(f"- {ev.source_db}: `{ev.source_id}`")
                if claim.contradicting_evidence:
                    st.markdown("**Contradicting:**")
                    for ev in claim.contradicting_evidence:
                        st.markdown(f"- {ev.source_db}: `{ev.source_id}`")
                if claim.methodology:
                    st.markdown(f"**Methodology:** {claim.methodology}")

    st.divider()

    # --- Agent Debate Viewer (#1) -------------------------------------------
    # TODO: Wire to real debate engine from confidence scoring (#1)
    st.subheader("Agent Debate")
    debate_rounds: list[dict] | None = st.session_state.mock_debate
    if debate_rounds:
        position_colors = {"support": "green", "challenge": "red", "neutral": "orange"}
        current_round = 0
        for entry in debate_rounds:
            if entry["round"] != current_round:
                current_round = entry["round"]
                st.markdown(f"**Round {current_round}**")
            with st.container(border=True):
                cols = st.columns([1, 4])
                with cols[0]:
                    color = position_colors.get(entry["position"], "gray")
                    st.markdown(f":`{color}`[**{entry['position'].upper()}**]")
                    st.caption(entry["agent_id"])
                with cols[1]:
                    st.markdown(entry["argument"])
                    if entry.get("evidence"):
                        st.caption(f"Evidence: {', '.join(entry['evidence'])}")

        # Consensus summary
        positions = [e["position"] for e in debate_rounds]
        support = positions.count("support")
        challenge = positions.count("challenge")
        neutral = positions.count("neutral")
        with st.container(border=True):
            st.markdown("**Consensus**")
            cons_cols = st.columns(3)
            with cons_cols[0]:
                st.metric("Support", support)
            with cons_cols[1]:
                st.metric("Challenge", challenge)
            with cons_cols[2]:
                st.metric("Neutral", neutral)
    else:
        st.info("No debate data. Submit a query to see agent deliberation.")

    st.divider()

    # Division report cards
    st.subheader("Division Reports")
    if divisions:
        for div_report in divisions:
            with st.container(border=True):
                div_cols = st.columns([3, 1])
                with div_cols[0]:
                    st.markdown(f"### {div_report.division_name}")
                    st.markdown(div_report.synthesis)
                with div_cols[1]:
                    st.markdown("**Confidence**")
                    render_confidence_score(div_report.confidence)

                # Specialist results
                if div_report.specialist_results:
                    with st.expander(f"Specialist details ({len(div_report.specialist_results)} agents)"):
                        for result in div_report.specialist_results:
                            st.markdown(f"**{result.agent_id}** (task: `{result.task_id}`)")
                            st.caption(
                                f"Cost: ${result.cost:.2f} | "
                                f"Duration: {result.duration_seconds:.1f}s | "
                                f"Tools: {', '.join(result.tools_used) if result.tools_used else 'none'}"
                            )
                            for finding in result.findings:
                                st.markdown(f"- {finding.claim_text}")
                            st.markdown("---")

    st.divider()

    # Risk assessment
    if report.risk_assessment:
        st.subheader("Risk Assessment")
        for risk_type, description in report.risk_assessment.items():
            label = risk_type.replace("_", " ").title()
            st.markdown(f"- **{label}:** {description}")

    # Recommended experiments
    if report.recommended_experiments:
        st.subheader("Recommended Experiments")
        for exp in report.recommended_experiments:
            priority = exp.get("priority", "MEDIUM")
            color = {"HIGH": "red", "MEDIUM": "orange", "LOW": "blue"}.get(priority, "gray")
            st.markdown(f"- :{color}[{priority}] {exp.get('experiment', '')}")

    # Limitations
    if report.limitations:
        st.subheader("Limitations")
        for lim in report.limitations:
            st.markdown(f"- {lim}")

    st.divider()

    # --- Export Report (#3) --------------------------------------------------
    # TODO: Wire to report generator (#3)
    st.subheader("Export Report")
    export_cols = st.columns(3)
    with export_cols[0]:
        st.button("Export PDF", disabled=True, help="Requires report generator (#3)")
    with export_cols[1]:
        st.button("Export HTML", disabled=True, help="Requires report generator (#3)")
    with export_cols[2]:
        st.button("Export JSON", disabled=True, help="Requires report generator (#3)")


# ---------------------------------------------------------------------------
# Tab 3: Agent Monitor
# ---------------------------------------------------------------------------

def render_monitor_tab() -> None:
    st.header("Agent Monitor")

    # Agent roster table
    st.subheader("Agent Roster")
    table_data = []
    for division, agents in AGENTS_BY_DIVISION.items():
        for agent in agents:
            sublab_membership = [
                name for name, info in SUBLABS.items() if agent in info["agents"]
            ]
            table_data.append({
                "Agent": agent,
                "Division": division,
                "Sublabs": ", ".join(sublab_membership) if sublab_membership else "--",
                "Status": "Available",
            })
    st.dataframe(table_data, use_container_width=True, hide_index=True)

    st.divider()

    # Execution plan viewer
    st.subheader("Execution Plan")
    plan: ExecutionPlan | None = st.session_state.mock_plan

    if plan is None:
        st.info("No execution plan yet. Submit a query first.")
    else:
        st.markdown(f"**Query:** {plan.user_query}")
        st.markdown(f"**Scope:** {plan.confirmed_scope}")
        st.metric("Estimated Total Cost", f"${plan.estimated_total_cost:.2f}")

        for phase in plan.phases:
            with st.container(border=True):
                phase_cols = st.columns([3, 1, 1])
                with phase_cols[0]:
                    st.markdown(f"**Phase {phase.phase_id}: {phase.name}**")
                    if phase.division:
                        st.caption(f"Division: {phase.division}")
                    if phase.agents:
                        st.caption(f"Agents: {', '.join(phase.agents)}")
                with phase_cols[1]:
                    parallel_label = "Parallel" if phase.parallel_eligible else "Sequential"
                    st.markdown(f":{'green' if phase.parallel_eligible else 'orange'}[{parallel_label}]")
                with phase_cols[2]:
                    st.markdown(f"${phase.estimated_cost:.2f}")

                if phase.dependencies:
                    st.caption(f"Depends on phases: {', '.join(str(d) for d in phase.dependencies)}")

    st.divider()

    # --- Pipeline Progress (#7-#10) -----------------------------------------
    # TODO: Wire to sublab pipeline runners (#7-#10)
    st.subheader("Pipeline Progress")
    if plan:
        mock_steps = [
            {"name": "Query parsing & scope confirmation", "status": "complete"},
            {"name": "Agent dispatch & data collection", "status": "complete"},
            {"name": "Multi-agent debate", "status": "running"},
            {"name": "HITL review (if needed)", "status": "pending"},
            {"name": "Report generation", "status": "pending"},
        ]
        completed = sum(1 for s in mock_steps if s["status"] == "complete")
        progress = completed / len(mock_steps)
        st.progress(progress, text=f"{progress:.0%} complete")

        status_icons = {"complete": "checkmark", "running": "arrows_counterclockwise", "pending": "white_circle"}
        for step in mock_steps:
            icon = status_icons.get(step["status"], "white_circle")
            st.markdown(f":{icon}: {step['name']}")

        time_cols = st.columns(2)
        with time_cols[0]:
            st.caption("Elapsed: 2m 14s")
        with time_cols[1]:
            st.caption("Est. remaining: 1m 30s")
    else:
        st.info("No active pipeline. Submit a query first.")

    st.divider()

    # Cost tracker placeholder
    st.subheader("Cost Tracker")
    if st.session_state.mock_report:
        report: FinalReport = st.session_state.mock_report
        cost_cols = st.columns(3)
        with cost_cols[0]:
            st.metric("Total LLM Cost", f"${report.total_cost:.2f}")
        with cost_cols[1]:
            st.metric("Total Duration", f"{report.total_duration_seconds:.0f}s")
        with cost_cols[2]:
            avg_cost_per_finding = report.total_cost / max(len(report.key_findings), 1)
            st.metric("Cost per Finding", f"${avg_cost_per_finding:.2f}")

        # Per-division cost breakdown (from mock division reports)
        if st.session_state.mock_divisions:
            st.markdown("**Per-division breakdown**")
            div_costs = []
            for div in st.session_state.mock_divisions:
                div_cost = sum(r.cost for r in div.specialist_results)
                div_duration = sum(r.duration_seconds for r in div.specialist_results)
                div_costs.append({
                    "Division": div.division_name,
                    "Cost (USD)": f"${div_cost:.2f}",
                    "Duration (s)": f"{div_duration:.1f}",
                    "Agents Used": len(div.specialist_results),
                })
            st.dataframe(div_costs, use_container_width=True, hide_index=True)
    else:
        st.info("No cost data yet. Submit a query first.")

    st.divider()

    # --- Computational Biology Jobs (#5) ------------------------------------
    st.subheader("Computational Biology Jobs")

    # Display Tamarind Bio jobs from session state (populated by pipeline or manual refresh)
    tamarind_jobs: list[dict] = st.session_state.get("tamarind_jobs", [])

    if not tamarind_jobs:
        st.info(
            "No computational biology jobs yet. Jobs are submitted by "
            "``protein_intelligence`` and ``structure_design`` agents during pipeline execution, "
            "or connect your Tamarind Bio API key (``TAMARIND_API_KEY``) and click Refresh."
        )
        if st.button("Refresh Jobs from Tamarind Bio"):
            try:
                from src.mcp_servers.tamarind.server import tamarind_get_jobs
                import asyncio

                result = asyncio.run(tamarind_get_jobs(limit=20))
                if not result.get("error"):
                    st.session_state.tamarind_jobs = result.get("raw_data", {}).get("jobs", [])
                    st.rerun()
                else:
                    st.error(f"Tamarind API error: {result.get('message', 'Unknown error')}")
            except Exception as e:
                st.error(f"Could not connect to Tamarind Bio: {e}")
    else:
        status_icons = {
            "Complete": ":green_circle:",
            "Running": ":orange_circle:",
            "In Queue": ":blue_circle:",
            "Stopped": ":red_circle:",
        }

        # Summary metrics
        status_counts: dict[str, int] = {}
        for job in tamarind_jobs:
            s = job.get("JobStatus", "Unknown")
            status_counts[s] = status_counts.get(s, 0) + 1

        job_metric_cols = st.columns(4)
        with job_metric_cols[0]:
            st.metric("Total", len(tamarind_jobs))
        with job_metric_cols[1]:
            st.metric("Complete", status_counts.get("Complete", 0))
        with job_metric_cols[2]:
            st.metric("Running", status_counts.get("Running", 0))
        with job_metric_cols[3]:
            st.metric("Queued", status_counts.get("In Queue", 0))

        for job in tamarind_jobs:
            job_status = job.get("JobStatus", "Unknown")
            job_name = job.get("JobName", "unnamed")
            job_type = job.get("Type", "unknown")
            created = job.get("Created", "")

            with st.container(border=True):
                cols = st.columns([1, 2, 1, 1])
                with cols[0]:
                    icon = status_icons.get(job_status, ":white_circle:")
                    st.markdown(f"{icon} **{job_status.upper()}**")
                with cols[1]:
                    st.markdown(f"`{job_name}` — {job_type}")
                    if job.get("WeightedHours"):
                        st.caption(f"Compute: {job['WeightedHours']:.2f} weighted hours")
                with cols[2]:
                    st.caption(f"Created: {created[:16] if created else 'N/A'}")
                with cols[3]:
                    if job_status == "Complete":
                        if st.button("Get Results", key=f"result_{job_name}"):
                            try:
                                from src.mcp_servers.tamarind.server import tamarind_get_result
                                import asyncio

                                result = asyncio.run(tamarind_get_result(job_name=job_name))
                                if not result.get("error"):
                                    url = result.get("raw_data", {}).get("result_url", "")
                                    st.markdown(f"[Download results]({url})")
                                else:
                                    st.error(result.get("message", "Failed"))
                            except Exception as e:
                                st.error(str(e))

        if st.button("Refresh Jobs"):
            try:
                from src.mcp_servers.tamarind.server import tamarind_get_jobs
                import asyncio

                result = asyncio.run(tamarind_get_jobs(limit=20))
                if not result.get("error"):
                    st.session_state.tamarind_jobs = result.get("raw_data", {}).get("jobs", [])
                    st.rerun()
                else:
                    st.error(f"Tamarind API error: {result.get('message', 'Unknown error')}")
            except Exception as e:
                st.error(f"Could not connect to Tamarind Bio: {e}")


# ---------------------------------------------------------------------------
# Tab 4: Expert Review (#2)
# ---------------------------------------------------------------------------

def render_expert_review_tab() -> None:
    """Human-in-the-loop review queue for low-confidence findings."""
    # TODO: Wire to HITL routing system (#2)
    st.header("Human-in-the-Loop Review Queue")

    report: FinalReport | None = st.session_state.mock_report
    if report is None:
        st.info("No findings to review. Submit a query first.")
        return

    # Collect flagged findings (confidence < 0.5)
    flagged = [
        (i, claim) for i, claim in enumerate(report.key_findings)
        if claim.confidence.score < 0.5
    ]

    # Summary metrics
    reviewed = sum(1 for k in flagged if f"review_{k[0]}" in st.session_state.hitl_reviews)
    metric_cols = st.columns(3)
    with metric_cols[0]:
        st.metric("Flagged", len(flagged))
    with metric_cols[1]:
        st.metric("Pending", len(flagged) - reviewed)
    with metric_cols[2]:
        st.metric("Reviewed", reviewed)

    if not flagged:
        st.success("All findings meet the confidence threshold. No expert review needed.")
        return

    st.divider()

    for idx, claim in flagged:
        review_key = f"review_{idx}"
        with st.container(border=True):
            st.markdown(f"**Flagged Finding** (from `{claim.agent_id}`)")
            st.markdown(claim.claim_text)

            flag_cols = st.columns([1, 2])
            with flag_cols[0]:
                st.markdown(confidence_badge(claim.confidence.level))
                st.caption(f"Score: {claim.confidence.score:.0%}")
            with flag_cols[1]:
                st.caption(f"Reason: Confidence below 50% threshold")

            # Expert feedback form
            feedback = st.text_area(
                "Expert feedback",
                key=f"feedback_{idx}",
                placeholder="Provide your assessment of this finding...",
                height=80,
            )

            btn_cols = st.columns(3)
            with btn_cols[0]:
                if st.button("Approve", key=f"approve_{idx}", type="primary"):
                    st.session_state.hitl_reviews[review_key] = {"verdict": "approved", "feedback": feedback}
            with btn_cols[1]:
                if st.button("Reject", key=f"reject_{idx}"):
                    st.session_state.hitl_reviews[review_key] = {"verdict": "rejected", "feedback": feedback}
            with btn_cols[2]:
                if st.button("Request More Evidence", key=f"more_{idx}"):
                    st.session_state.hitl_reviews[review_key] = {"verdict": "needs_evidence", "feedback": feedback}

            # Show existing review
            if review_key in st.session_state.hitl_reviews:
                review = st.session_state.hitl_reviews[review_key]
                verdict_colors = {"approved": "green", "rejected": "red", "needs_evidence": "orange"}
                color = verdict_colors.get(review["verdict"], "gray")
                st.markdown(f":{color}[Reviewed: **{review['verdict'].upper()}**]")
                if review["feedback"]:
                    st.caption(f"Feedback: {review['feedback']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="Lumi Virtual Lab",
        page_icon="lab",
        layout="wide",
    )

    init_session_state()
    render_sidebar()

    tab_submit, tab_results, tab_review, tab_monitor = st.tabs(
        ["Submit Query", "Results", "Expert Review", "Agent Monitor"]
    )

    with tab_submit:
        render_submit_tab()

    with tab_results:
        render_results_tab()

    with tab_review:
        render_expert_review_tab()

    with tab_monitor:
        render_monitor_tab()


if __name__ == "__main__":
    main()
