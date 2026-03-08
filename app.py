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
)

# ---------------------------------------------------------------------------
# Theme / Custom CSS
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --bg-primary: #faf9f5;
    --bg-card: #ffffff;
    --bg-input: #f5f4f0;
    --border: #e8e6e1;
    --border-hover: #d0cec9;
    --text-primary: #1a1a1a;
    --text-secondary: #6b6b6b;
    --text-muted: #9b9b9b;
    --accent: #0279ee;
    --accent-light: #e8f2fd;
    --green: #16a34a;
    --green-light: #dcfce7;
    --orange: #ea580c;
    --orange-light: #fff7ed;
    --red: #dc2626;
    --red-light: #fef2f2;
}

/* Global */
.stApp, .main .block-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: var(--bg-primary) !important;
}

.main .block-container {
    max-width: 1100px;
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}

/* Hide default Streamlit header/footer */
header[data-testid="stHeader"] { background: var(--bg-primary) !important; }
footer { display: none !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem !important;
}

/* Typography */
h1, h2, h3, h4 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.02em !important;
}
h1 { font-size: 1.5rem !important; }
h2 { font-size: 1.2rem !important; }
h3 { font-size: 1.05rem !important; }

p, li, span, div {
    font-family: 'Inter', sans-serif !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: transparent;
    border-bottom: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500;
    font-size: 0.85rem;
    color: var(--text-secondary);
    padding: 0.6rem 1.2rem;
    border-bottom: 2px solid transparent;
    background: transparent !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: var(--text-primary);
    border-bottom: 2px solid var(--text-primary);
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.5rem;
}

/* Cards / containers with border */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    box-shadow: none !important;
    padding: 0.2rem !important;
}

/* Buttons */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    border-radius: 8px !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    padding: 0.4rem 1rem !important;
    transition: all 0.15s ease !important;
    box-shadow: none !important;
}
.stButton > button:hover {
    border-color: var(--border-hover) !important;
    background: var(--bg-input) !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: var(--text-primary) !important;
    color: white !important;
    border-color: var(--text-primary) !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    background: #333 !important;
}

/* Text inputs / text areas */
.stTextArea textarea, .stTextInput input {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 0.8rem 1rem !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent) !important;
}

/* Selectbox */
div[data-baseweb="select"] > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
}

/* Metrics */
div[data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.8rem 1rem;
}
div[data-testid="stMetric"] label {
    font-size: 0.75rem !important;
    color: var(--text-muted) !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    font-size: 1.3rem !important;
    font-weight: 600 !important;
}

/* Expanders */
details {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    background: var(--bg-card) !important;
}
details summary {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
}

/* Progress bar */
div[data-testid="stProgress"] > div > div {
    background-color: var(--bg-input) !important;
    border-radius: 6px !important;
}
div[data-testid="stProgress"] > div > div > div {
    border-radius: 6px !important;
}

/* Dividers */
hr {
    border-color: var(--border) !important;
    margin: 1.2rem 0 !important;
}

/* Dataframe */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    overflow: hidden;
}

/* Info / success / warning boxes */
div[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 0.85rem !important;
}

/* Chip-style suggestion buttons */
.suggestion-chip {
    display: inline-block;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 0.45rem 1rem;
    font-size: 0.82rem;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.15s ease;
    line-height: 1.3;
}
.suggestion-chip:hover {
    border-color: var(--accent);
    color: var(--accent);
    background: var(--accent-light);
}

/* Agent badge */
.agent-tag {
    display: inline-block;
    background: var(--bg-input);
    border-radius: 6px;
    padding: 0.2rem 0.5rem;
    font-size: 0.75rem;
    font-family: 'SF Mono', 'Fira Code', monospace;
    color: var(--text-secondary);
    margin-right: 0.3rem;
    margin-bottom: 0.3rem;
}

/* Confidence pills */
.conf-high { background: var(--green-light); color: var(--green); }
.conf-medium { background: var(--orange-light); color: var(--orange); }
.conf-low { background: var(--red-light); color: var(--red); }
.conf-pill {
    display: inline-block;
    border-radius: 20px;
    padding: 0.2rem 0.7rem;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}

/* Debate position badges */
.pos-support { background: var(--green-light); color: var(--green); border: 1px solid #bbf7d0; }
.pos-challenge { background: var(--red-light); color: var(--red); border: 1px solid #fecaca; }
.pos-neutral { background: var(--orange-light); color: var(--orange); border: 1px solid #fed7aa; }
.pos-badge {
    display: inline-block;
    border-radius: 6px;
    padding: 0.15rem 0.5rem;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

/* Pipeline step */
.step-row { display: flex; align-items: center; gap: 0.6rem; padding: 0.4rem 0; font-size: 0.85rem; }
.step-icon { width: 20px; text-align: center; }
.step-complete { color: var(--green); }
.step-running { color: var(--orange); }
.step-pending { color: var(--text-muted); }

/* Job card status dot */
.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 0.4rem;
}
.dot-complete { background: var(--green); }
.dot-running { background: var(--orange); }
.dot-queued { background: var(--border-hover); }

/* Hide streamlit branding */
#MainMenu { visibility: hidden; }
</style>
"""

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUBLABS: dict[str, dict] = {
    "Target Validation": {
        "description": "Evidence dossiers with pathway diagrams and confidence scores",
        "icon": "🎯",
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
        "icon": "🔬",
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
        "icon": "📊",
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
        "icon": "📋",
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
        "icon": "⚗️",
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
        "icon": "🏥",
        "agents": ["clinical_trialist", "pharmacologist", "statistical_genetics", "fda_safety"],
        "divisions": ["Clinical Intelligence", "Target Safety", "Computational Biology"],
        "examples": [
            "Build go/no-go evidence package for anti-IL-17 antibody IND filing",
            "Assess clinical translatability of preclinical efficacy data for NASH target",
            "Evaluate first-in-human dose selection strategy for bispecific T-cell engager",
        ],
    },
}

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
    return [
        {"round": 1, "agent_id": "target_biologist", "position": "support", "argument": "BRCA1 loss-of-function is well-established as a synthetic lethality target. Multiple preclinical models confirm PARP sensitivity.", "evidence": ["PMID:38291045", "PMID:36842073"]},
        {"round": 1, "agent_id": "literature_synthesis", "position": "support", "argument": "247 publications consistently support BRCA1 as a validated target. Level 1 clinical evidence from OlympiAD and EMBRACA trials.", "evidence": ["PMID:28578601", "PMID:29863767"]},
        {"round": 2, "agent_id": "pharmacologist", "position": "challenge", "argument": "Resistance via reversion mutations is observed in 20-30% of patients. Long-term durability of response remains uncertain.", "evidence": ["PMID:37104562"]},
        {"round": 2, "agent_id": "fda_safety", "position": "neutral", "argument": "Safety profile is manageable but myelosuppression requires monitoring. Risk-benefit is favorable for BRCA-mutant patients specifically.", "evidence": ["PMID:35436722"]},
        {"round": 3, "agent_id": "target_biologist", "position": "support", "argument": "Acknowledging resistance concern — combination strategies with checkpoint inhibitors may address durability. Biomarker selection mitigates risk.", "evidence": ["PMID:39012345"]},
    ]


def _mock_execution_plan() -> ExecutionPlan:
    return ExecutionPlan(
        query_id="q_demo_001",
        user_query="Evaluate BRCA1 as a therapeutic target for triple-negative breast cancer",
        confirmed_scope="Full target validation dossier including genetic evidence, safety, and clinical translatability",
        phases=[
            Phase(phase_id=1, name="Genetic Evidence Collection", division="Target Identification", agents=["statistical_genetics", "functional_genomics", "single_cell_atlas"], dependencies=[], parallel_eligible=True, priority=Priority.HIGH, estimated_cost=1.50),
            Phase(phase_id=2, name="Safety Assessment", division="Target Safety", agents=["fda_safety", "toxicogenomics", "bio_pathways"], dependencies=[1], parallel_eligible=True, priority=Priority.HIGH, estimated_cost=1.20),
            Phase(phase_id=3, name="Literature Synthesis", division="Computational Biology", agents=["literature_synthesis"], dependencies=[], parallel_eligible=False, priority=Priority.MEDIUM, estimated_cost=0.80),
            Phase(phase_id=4, name="Clinical Translatability", division="Clinical Intelligence", agents=["clinical_trialist"], dependencies=[1, 2], parallel_eligible=False, priority=Priority.MEDIUM, estimated_cost=0.70),
            Phase(phase_id=5, name="Final Synthesis & Report", division=None, agents=[], dependencies=[1, 2, 3, 4], parallel_eligible=False, priority=Priority.HIGH, estimated_cost=0.50),
        ],
        estimated_total_cost=4.70,
    )


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def conf_pill(level: ConfidenceLevel) -> str:
    cls = {"HIGH": "conf-high", "MEDIUM": "conf-medium", "LOW": "conf-low", "INSUFFICIENT": "conf-low"}
    return f'<span class="conf-pill {cls.get(level.value, "conf-low")}">{level.value}</span>'


def agent_tag(name: str) -> str:
    return f'<span class="agent-tag">{name}</span>'


def pos_badge(position: str) -> str:
    return f'<span class="pos-badge pos-{position}">{position.upper()}</span>'


def render_confidence_bar(conf: ConfidenceAssessment) -> None:
    c1, c2 = st.columns([1, 3])
    with c1:
        st.markdown(conf_pill(conf.level), unsafe_allow_html=True)
    with c2:
        st.progress(conf.score, text=f"{conf.score:.0%}")


# ---------------------------------------------------------------------------
# Session state
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
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Lumi")
        st.caption("AI-powered drug discovery lab")
        st.markdown("---")

        # Sublab selector
        st.markdown('<p style="font-size:0.75rem;color:#9b9b9b;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.3rem;">Sublab</p>', unsafe_allow_html=True)
        selected = st.selectbox(
            "Sublab",
            list(SUBLABS.keys()),
            index=list(SUBLABS.keys()).index(st.session_state.selected_sublab),
            label_visibility="collapsed",
        )
        st.session_state.selected_sublab = selected
        sublab_info = SUBLABS[selected]
        st.caption(sublab_info["description"])

        st.markdown("---")

        # Active agents for current sublab
        st.markdown('<p style="font-size:0.75rem;color:#9b9b9b;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.3rem;">Active Agents</p>', unsafe_allow_html=True)
        sublab_agents = set(sublab_info["agents"])
        for agent in sublab_info["agents"]:
            st.markdown(f'<div style="display:flex;align-items:center;gap:0.4rem;padding:0.2rem 0;font-size:0.82rem;"><span style="color:#16a34a;">●</span> <code style="font-size:0.78rem;background:#f5f4f0;padding:0.1rem 0.4rem;border-radius:4px;">{agent}</code></div>', unsafe_allow_html=True)

        st.markdown("---")

        # All divisions (collapsed)
        st.markdown('<p style="font-size:0.75rem;color:#9b9b9b;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.3rem;">All Divisions</p>', unsafe_allow_html=True)
        for division, agents in AGENTS_BY_DIVISION.items():
            with st.expander(division, expanded=False):
                for agent in agents:
                    dot_color = "#16a34a" if agent in sublab_agents else "#d0cec9"
                    st.markdown(f'<div style="font-size:0.8rem;padding:0.15rem 0;"><span style="color:{dot_color};">●</span> <code style="font-size:0.75rem;">{agent}</code></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.caption("v0.1.0-dev")


# ---------------------------------------------------------------------------
# Tab: Query
# ---------------------------------------------------------------------------

def render_query_tab() -> None:
    sublab = st.session_state.selected_sublab
    sublab_info = SUBLABS[sublab]

    # Hero area
    st.markdown(f"## {sublab_info['icon']} {sublab}")
    st.markdown(f'<p style="color:#6b6b6b;font-size:0.9rem;margin-top:-0.5rem;">{sublab_info["description"]}</p>', unsafe_allow_html=True)

    # Suggestion chips
    st.markdown('<p style="font-size:0.78rem;color:#9b9b9b;margin-bottom:0.5rem;">Try an example</p>', unsafe_allow_html=True)
    chip_cols = st.columns(len(sublab_info["examples"]))
    for i, example in enumerate(sublab_info["examples"]):
        with chip_cols[i]:
            if st.button(example[:60] + ("..." if len(example) > 60 else ""), key=f"chip_{sublab}_{i}", use_container_width=True):
                st.session_state.query_text = example

    st.markdown("")

    # Query input
    query = st.text_area(
        "Query",
        value=st.session_state.query_text,
        height=100,
        placeholder="Ask a research question...",
        label_visibility="collapsed",
    )
    st.session_state.query_text = query

    # Agent tags + submit
    c1, c2 = st.columns([4, 1])
    with c1:
        tags_html = " ".join(agent_tag(a) for a in sublab_info["agents"])
        st.markdown(f'<div style="padding-top:0.4rem;">{tags_html}</div>', unsafe_allow_html=True)
    with c2:
        submitted = st.button("Run", type="primary", use_container_width=True, disabled=not query.strip())

    if submitted:
        st.session_state.submitted_query = {
            "query": query,
            "sublab": sublab,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents": sublab_info["agents"],
            "divisions": sublab_info["divisions"],
        }
        st.session_state.mock_report = _mock_final_report()
        st.session_state.mock_divisions = _mock_division_reports()
        st.session_state.mock_plan = _mock_execution_plan()
        st.session_state.mock_debate = _mock_debate_rounds()
        st.toast("Query submitted. View results below.")


# ---------------------------------------------------------------------------
# Tab: Results
# ---------------------------------------------------------------------------

def render_results_tab() -> None:
    report: FinalReport | None = st.session_state.mock_report
    divisions: list[DivisionReport] | None = st.session_state.mock_divisions

    if report is None:
        st.markdown('<div style="text-align:center;padding:3rem 0;color:#9b9b9b;font-size:0.9rem;">Submit a query to see results here.</div>', unsafe_allow_html=True)
        return

    # Executive summary card
    with st.container(border=True):
        st.markdown("#### Executive Summary")
        st.markdown(report.executive_summary)

    # Metrics row
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Cost", f"${report.total_cost:.2f}")
    with m2:
        st.metric("Duration", f"{report.total_duration_seconds:.0f}s")
    with m3:
        st.metric("Findings", str(len(report.key_findings)))

    # Visual context
    st.markdown("#### Figures")
    fig_cols = st.columns(3)
    placeholders = [
        ("Pathway Diagram", "Signaling pathway"),
        ("Expression Heatmap", "Tissue expression profile"),
        ("Mechanism of Action", "Drug-target interaction"),
    ]
    for col, (title, caption) in zip(fig_cols, placeholders):
        with col:
            with st.container(border=True):
                st.markdown(f'<div style="text-align:center;padding:1.5rem 0;"><p style="font-weight:500;font-size:0.85rem;margin:0;">{title}</p><p style="color:#9b9b9b;font-size:0.78rem;margin:0.3rem 0 0 0;">{caption}</p></div>', unsafe_allow_html=True)

    # Key findings
    st.markdown("#### Key Findings")
    for i, claim in enumerate(report.key_findings):
        with st.container(border=True):
            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.3rem;">'
                        f'<span style="font-weight:500;font-size:0.85rem;">Finding {i + 1}</span>'
                        f'{agent_tag(claim.agent_id)} {conf_pill(claim.confidence.level)}'
                        f'</div>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-size:0.88rem;line-height:1.5;margin:0;">{claim.claim_text}</p>', unsafe_allow_html=True)
            st.progress(claim.confidence.score, text=f"{claim.confidence.score:.0%}")

            with st.expander("Evidence & methodology"):
                if claim.supporting_evidence:
                    st.markdown("**Supporting**")
                    for ev in claim.supporting_evidence:
                        st.markdown(f"- `{ev.source_db}:{ev.source_id}`")
                if claim.contradicting_evidence:
                    st.markdown("**Contradicting**")
                    for ev in claim.contradicting_evidence:
                        st.markdown(f"- `{ev.source_db}:{ev.source_id}`")
                if claim.methodology:
                    st.caption(f"Methodology: {claim.methodology}")
                if claim.confidence.caveats:
                    st.caption(f"Caveats: {'; '.join(claim.confidence.caveats)}")

    # Agent debate
    st.markdown("#### Agent Debate")
    debate_rounds: list[dict] | None = st.session_state.mock_debate
    if debate_rounds:
        current_round = 0
        for entry in debate_rounds:
            if entry["round"] != current_round:
                current_round = entry["round"]
                st.markdown(f'<p style="font-size:0.78rem;color:#9b9b9b;text-transform:uppercase;letter-spacing:0.04em;margin:0.8rem 0 0.3rem 0;">Round {current_round}</p>', unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.3rem;">'
                            f'{pos_badge(entry["position"])} {agent_tag(entry["agent_id"])}'
                            f'</div>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size:0.85rem;line-height:1.5;margin:0;">{entry["argument"]}</p>', unsafe_allow_html=True)
                if entry.get("evidence"):
                    st.markdown(f'<p style="font-size:0.75rem;color:#9b9b9b;margin:0.3rem 0 0 0;">{", ".join(entry["evidence"])}</p>', unsafe_allow_html=True)

        # Consensus
        positions = [e["position"] for e in debate_rounds]
        with st.container(border=True):
            st.markdown("**Consensus**")
            cc1, cc2, cc3 = st.columns(3)
            with cc1:
                st.metric("Support", positions.count("support"))
            with cc2:
                st.metric("Challenge", positions.count("challenge"))
            with cc3:
                st.metric("Neutral", positions.count("neutral"))

    # Division reports
    st.markdown("#### Division Reports")
    if divisions:
        for div_report in divisions:
            with st.container(border=True):
                dc1, dc2 = st.columns([3, 1])
                with dc1:
                    st.markdown(f"**{div_report.division_name}**")
                    st.markdown(f'<p style="font-size:0.85rem;color:#6b6b6b;">{div_report.synthesis}</p>', unsafe_allow_html=True)
                with dc2:
                    render_confidence_bar(div_report.confidence)

                if div_report.specialist_results:
                    with st.expander(f"{len(div_report.specialist_results)} specialist(s)"):
                        for result in div_report.specialist_results:
                            st.markdown(f'{agent_tag(result.agent_id)} <span style="font-size:0.78rem;color:#9b9b9b;">${result.cost:.2f} · {result.duration_seconds:.0f}s · {", ".join(result.tools_used)}</span>', unsafe_allow_html=True)
                            for finding in result.findings:
                                st.markdown(f'<p style="font-size:0.82rem;margin:0.2rem 0 0.5rem 1rem;">• {finding.claim_text}</p>', unsafe_allow_html=True)

    # Risk assessment
    if report.risk_assessment:
        st.markdown("#### Risk Assessment")
        with st.container(border=True):
            for risk_type, description in report.risk_assessment.items():
                label = risk_type.replace("_", " ").title()
                st.markdown(f'<p style="font-size:0.85rem;margin:0.3rem 0;"><strong>{label}</strong> — {description}</p>', unsafe_allow_html=True)

    # Recommended experiments
    if report.recommended_experiments:
        st.markdown("#### Recommended Experiments")
        with st.container(border=True):
            for exp in report.recommended_experiments:
                priority = exp.get("priority", "MEDIUM")
                cls = {"HIGH": "conf-low", "MEDIUM": "conf-medium", "LOW": "conf-high"}.get(priority, "conf-medium")
                st.markdown(f'<div style="padding:0.3rem 0;font-size:0.85rem;"><span class="conf-pill {cls}">{priority}</span> {exp.get("experiment", "")}</div>', unsafe_allow_html=True)

    # Limitations
    if report.limitations:
        with st.expander("Limitations"):
            for lim in report.limitations:
                st.markdown(f"- {lim}")

    # Export
    st.markdown("#### Export")
    ec1, ec2, ec3 = st.columns(3)
    with ec1:
        st.button("PDF", disabled=True, use_container_width=True)
    with ec2:
        st.button("HTML", disabled=True, use_container_width=True)
    with ec3:
        st.button("JSON", disabled=True, use_container_width=True)


# ---------------------------------------------------------------------------
# Tab: Review
# ---------------------------------------------------------------------------

def render_review_tab() -> None:
    report: FinalReport | None = st.session_state.mock_report
    if report is None:
        st.markdown('<div style="text-align:center;padding:3rem 0;color:#9b9b9b;font-size:0.9rem;">No findings to review yet.</div>', unsafe_allow_html=True)
        return

    flagged = [(i, claim) for i, claim in enumerate(report.key_findings) if claim.confidence.score < 0.5]

    # Metrics
    reviewed = sum(1 for k in flagged if f"review_{k[0]}" in st.session_state.hitl_reviews)
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.metric("Flagged", len(flagged))
    with mc2:
        st.metric("Pending", len(flagged) - reviewed)
    with mc3:
        st.metric("Reviewed", reviewed)

    if not flagged:
        st.markdown('<div style="text-align:center;padding:2rem 0;color:#16a34a;font-size:0.9rem;">All findings meet the confidence threshold.</div>', unsafe_allow_html=True)
        return

    for idx, claim in flagged:
        review_key = f"review_{idx}"
        with st.container(border=True):
            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem;">'
                        f'<span style="font-weight:500;font-size:0.85rem;">Flagged Finding</span>'
                        f'{agent_tag(claim.agent_id)} {conf_pill(claim.confidence.level)}'
                        f'</div>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-size:0.88rem;line-height:1.5;">{claim.claim_text}</p>', unsafe_allow_html=True)
            st.progress(claim.confidence.score, text=f"{claim.confidence.score:.0%}")

            feedback = st.text_area(
                "Expert feedback",
                key=f"feedback_{idx}",
                placeholder="Your assessment...",
                height=80,
                label_visibility="collapsed",
            )

            bc1, bc2, bc3 = st.columns(3)
            with bc1:
                if st.button("Approve", key=f"approve_{idx}", type="primary", use_container_width=True):
                    st.session_state.hitl_reviews[review_key] = {"verdict": "approved", "feedback": feedback}
            with bc2:
                if st.button("Reject", key=f"reject_{idx}", use_container_width=True):
                    st.session_state.hitl_reviews[review_key] = {"verdict": "rejected", "feedback": feedback}
            with bc3:
                if st.button("Need More Evidence", key=f"more_{idx}", use_container_width=True):
                    st.session_state.hitl_reviews[review_key] = {"verdict": "needs_evidence", "feedback": feedback}

            if review_key in st.session_state.hitl_reviews:
                review = st.session_state.hitl_reviews[review_key]
                verdict_cls = {"approved": "conf-high", "rejected": "conf-low", "needs_evidence": "conf-medium"}
                st.markdown(f'<div style="margin-top:0.5rem;"><span class="conf-pill {verdict_cls.get(review["verdict"], "")}">{review["verdict"].replace("_", " ").upper()}</span></div>', unsafe_allow_html=True)
                if review["feedback"]:
                    st.caption(f"Feedback: {review['feedback']}")


# ---------------------------------------------------------------------------
# Tab: Monitor
# ---------------------------------------------------------------------------

def render_monitor_tab() -> None:
    # Agent roster
    st.markdown("#### Agent Roster")
    table_data = []
    for division, agents in AGENTS_BY_DIVISION.items():
        for agent in agents:
            sublab_membership = [name for name, info in SUBLABS.items() if agent in info["agents"]]
            table_data.append({
                "Agent": agent,
                "Division": division,
                "Sublabs": ", ".join(sublab_membership) if sublab_membership else "—",
                "Status": "Available",
            })
    st.dataframe(table_data, use_container_width=True, hide_index=True)

    # Execution plan
    st.markdown("#### Execution Plan")
    plan: ExecutionPlan | None = st.session_state.mock_plan

    if plan is None:
        st.caption("No execution plan yet.")
    else:
        with st.container(border=True):
            st.markdown(f'<p style="font-size:0.85rem;"><strong>Query:</strong> {plan.user_query}</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-size:0.82rem;color:#6b6b6b;">{plan.confirmed_scope}</p>', unsafe_allow_html=True)

        for phase in plan.phases:
            with st.container(border=True):
                pc1, pc2, pc3 = st.columns([4, 1, 1])
                with pc1:
                    st.markdown(f"**Phase {phase.phase_id}: {phase.name}**")
                    if phase.division:
                        st.caption(phase.division)
                    if phase.agents:
                        st.markdown(" ".join(agent_tag(a) for a in phase.agents), unsafe_allow_html=True)
                with pc2:
                    label = "Parallel" if phase.parallel_eligible else "Sequential"
                    cls = "conf-high" if phase.parallel_eligible else "conf-medium"
                    st.markdown(f'<span class="conf-pill {cls}">{label}</span>', unsafe_allow_html=True)
                with pc3:
                    st.markdown(f'<span style="font-size:0.85rem;font-weight:500;">${phase.estimated_cost:.2f}</span>', unsafe_allow_html=True)
                if phase.dependencies:
                    st.caption(f"Depends on: {', '.join(str(d) for d in phase.dependencies)}")

        st.metric("Estimated Total", f"${plan.estimated_total_cost:.2f}")

    # Pipeline progress
    st.markdown("#### Pipeline Progress")
    if plan:
        steps = [
            ("Query parsing & scope confirmation", "complete"),
            ("Agent dispatch & data collection", "complete"),
            ("Multi-agent debate", "running"),
            ("HITL review (if needed)", "pending"),
            ("Report generation", "pending"),
        ]
        completed = sum(1 for _, s in steps if s == "complete")
        st.progress(completed / len(steps), text=f"{completed}/{len(steps)} steps")

        icons = {"complete": "✓", "running": "↻", "pending": "○"}
        for name, status in steps:
            st.markdown(f'<div class="step-row"><span class="step-icon step-{status}">{icons[status]}</span><span>{name}</span></div>', unsafe_allow_html=True)

        tc1, tc2 = st.columns(2)
        with tc1:
            st.caption("Elapsed: 2m 14s")
        with tc2:
            st.caption("Est. remaining: 1m 30s")
    else:
        st.caption("No active pipeline.")

    # Cost tracker
    st.markdown("#### Cost Tracker")
    if st.session_state.mock_report:
        report: FinalReport = st.session_state.mock_report
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            st.metric("LLM Cost", f"${report.total_cost:.2f}")
        with cc2:
            st.metric("Duration", f"{report.total_duration_seconds:.0f}s")
        with cc3:
            avg = report.total_cost / max(len(report.key_findings), 1)
            st.metric("Per Finding", f"${avg:.2f}")

        if st.session_state.mock_divisions:
            div_costs = []
            for div in st.session_state.mock_divisions:
                div_cost = sum(r.cost for r in div.specialist_results)
                div_dur = sum(r.duration_seconds for r in div.specialist_results)
                div_costs.append({
                    "Division": div.division_name,
                    "Cost": f"${div_cost:.2f}",
                    "Duration": f"{div_dur:.0f}s",
                    "Agents": len(div.specialist_results),
                })
            st.dataframe(div_costs, use_container_width=True, hide_index=True)
    else:
        st.caption("No cost data yet.")

    # Computational biology jobs
    st.markdown("#### Compute Jobs")
    jobs = [
        {"job_id": "tb_001", "type": "protein_folding", "target": "BRCA1 BRCT domain", "status": "complete", "submitted": "2m ago"},
        {"job_id": "tb_002", "type": "docking", "target": "PARP1-olaparib", "status": "running", "submitted": "45s ago"},
        {"job_id": "tb_003", "type": "md_simulation", "target": "BRCA1-RAD51 complex", "status": "queued", "submitted": "10s ago"},
    ]
    for job in jobs:
        with st.container(border=True):
            jc1, jc2 = st.columns([4, 1])
            with jc1:
                dot_cls = f"dot-{job['status']}"
                st.markdown(f'<div style="font-size:0.85rem;"><span class="status-dot {dot_cls}"></span>'
                            f'<strong>{job["type"].replace("_", " ")}</strong>'
                            f'<span style="color:#9b9b9b;margin-left:0.5rem;">{job["target"]}</span></div>', unsafe_allow_html=True)
            with jc2:
                st.markdown(f'<span style="font-size:0.78rem;color:#9b9b9b;">{job["submitted"]}</span>', unsafe_allow_html=True)
            if job["status"] == "complete":
                with st.expander("Results"):
                    st.caption("pLDDT 87.3 — Placeholder for Tamarind Bio API")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="Lumi",
        page_icon="✦",
        layout="wide",
    )

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    init_session_state()
    render_sidebar()

    tab_query, tab_results, tab_review, tab_monitor = st.tabs([
        "Query", "Results", "Review", "Monitor",
    ])

    with tab_query:
        render_query_tab()
    with tab_results:
        render_results_tab()
    with tab_review:
        render_review_tab()
    with tab_monitor:
        render_monitor_tab()


if __name__ == "__main__":
    main()
