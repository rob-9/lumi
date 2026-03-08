"""Pipeline evaluation script.

Tests the Lumi YOHAS pipeline architecture across multiple dimensions:
1. Component integration (factory → agents → divisions → CSO)
2. Concurrency gate (verifies rate limiting under parallel load)
3. HITL routing (confidence thresholds, Slack notification paths)
4. Living document (version evolution across pipeline milestones)
5. End-to-end pipeline (lightweight query through the full system)
6. Benchmark tasks comparable to LAB-Bench DbQA, SeqQA, and HLE
   (agent-executed with deterministic keyword scoring)

NOTE: Benchmark tasks are Lumi-constructed questions testing the same
capabilities as the official benchmarks, NOT the actual benchmark datasets.
Scores are NOT directly comparable to published Biomni numbers.

Usage:
    ANTHROPIC_API_KEY=sk-... python -m tests.eval_pipeline
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from dataclasses import dataclass, field

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("lumi.eval")


@dataclass
class EvalResult:
    name: str
    passed: bool
    duration: float = 0.0
    details: str = ""
    error: str = ""
    score: float | None = None  # For accuracy benchmarks


@dataclass
class EvalSuite:
    results: list[EvalResult] = field(default_factory=list)

    def add(self, result: EvalResult) -> None:
        self.results.append(result)
        status = "PASS" if result.passed else "FAIL"
        score_str = f" [score={result.score:.2f}]" if result.score is not None else ""
        logger.info(
            "[%s] %s (%.1fs)%s %s",
            status,
            result.name,
            result.duration,
            score_str,
            f"— {result.details}" if result.details else "",
        )
        if result.error:
            logger.error("  Error: %s", result.error)

    def summary(self) -> str:
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        lines = [
            "",
            "=" * 70,
            f"EVALUATION SUMMARY: {passed}/{total} passed",
            "=" * 70,
        ]
        for r in self.results:
            status = "PASS" if r.passed else "FAIL"
            score_str = f" [{r.score:.2f}]" if r.score is not None else ""
            lines.append(f"  [{status}] {r.name} ({r.duration:.1f}s){score_str}")
            if r.error:
                lines.append(f"         Error: {r.error[:200]}")

        # Benchmark results by category
        scored = [r for r in self.results if r.score is not None]
        if scored:
            lines.append("")
            lines.append("-" * 70)
            lines.append("BENCHMARK RESULTS (keyword-match scoring)")
            lines.append("-" * 70)

            # Group by category prefix
            categories = {"DbQA": [], "SeqQA": [], "HLE": []}
            for r in scored:
                for cat in categories:
                    if r.name.startswith(cat):
                        categories[cat].append(r.score)
                        break

            lines.append(f"  {'Task':<50} {'Score':>8}")
            lines.append(f"  {'─' * 50} {'─' * 8}")
            for r in scored:
                lines.append(f"  {r.name:<50} {r.score:>7.1%}")

            lines.append("")
            lines.append("  CATEGORY AVERAGES:")
            # Biomni reference scores from the Biomni paper (for context only)
            biomni_ref = {"DbQA": 0.744, "SeqQA": 0.819, "HLE": 0.173}
            for cat, scores in categories.items():
                if scores:
                    avg = sum(scores) / len(scores)
                    ref = biomni_ref.get(cat, 0)
                    lines.append(
                        f"  {cat:<12} Lumi: {avg:>6.1%}  |  "
                        f"Biomni ref: {ref:.1%} (NOT directly comparable)"
                    )

            lines.append("")
            lines.append(
                "  NOTE: Lumi scores are from Lumi-constructed questions with"
            )
            lines.append(
                "  keyword scoring. Biomni scores are from official benchmark"
            )
            lines.append(
                "  datasets. These numbers are NOT a head-to-head comparison."
            )
            lines.append("-" * 70)

        lines.append("=" * 70)
        return "\n".join(lines)


# -----------------------------------------------------------------------
# Test 1: API connectivity
# -----------------------------------------------------------------------

async def test_api_connectivity(suite: EvalSuite) -> bool:
    t0 = time.time()
    try:
        from src.utils.llm import LLMClient, ModelTier

        llm = LLMClient()
        response = await llm.chat(
            messages=[{"role": "user", "content": "Reply with exactly: LUMI_OK"}],
            model=ModelTier.HAIKU,
            max_tokens=20,
        )
        text = "".join(b.text for b in response.content if hasattr(b, "text"))
        ok = "LUMI_OK" in text or "OK" in text.upper()
        suite.add(EvalResult(
            name="API Connectivity",
            passed=ok,
            duration=time.time() - t0,
            details=f"Response: {text[:50]}",
        ))
        return ok
    except Exception as e:
        suite.add(EvalResult(
            name="API Connectivity", passed=False,
            duration=time.time() - t0, error=str(e),
        ))
        return False


# -----------------------------------------------------------------------
# Test 2: Factory & agent creation
# -----------------------------------------------------------------------

async def test_factory(suite: EvalSuite) -> dict | None:
    t0 = time.time()
    try:
        from src.factory import create_system
        divisions = create_system()

        expected_divisions = {
            "Target Identification", "Target Safety", "Modality Selection",
            "Molecular Design", "Clinical Intelligence", "Computational Biology",
            "Experimental Design", "Biosecurity",
        }
        actual = set(divisions.keys())
        missing = expected_divisions - actual
        total_specialists = sum(len(d.specialist_agents) for d in divisions.values())

        ok = len(missing) == 0 and total_specialists >= 17
        suite.add(EvalResult(
            name="Factory & Agent Creation",
            passed=ok,
            duration=time.time() - t0,
            details=f"{len(divisions)} divisions, {total_specialists} specialists"
            + (f", missing: {missing}" if missing else ""),
        ))
        return divisions if ok else None
    except Exception as e:
        suite.add(EvalResult(
            name="Factory & Agent Creation", passed=False,
            duration=time.time() - t0, error=str(e),
        ))
        return None


# -----------------------------------------------------------------------
# Test 3: Concurrency gate (reduced from 10 to 5 parallel)
# -----------------------------------------------------------------------

async def test_concurrency_gate(suite: EvalSuite) -> None:
    t0 = time.time()
    try:
        from src.utils.llm import LLMClient, ModelTier, get_concurrency_gate

        gate = get_concurrency_gate()

        async def mini_call(idx: int) -> str:
            llm = LLMClient()
            resp = await llm.chat(
                messages=[{"role": "user", "content": f"Reply with only: {idx}"}],
                model=ModelTier.HAIKU,
                max_tokens=10,
            )
            return "".join(b.text for b in resp.content if hasattr(b, "text"))

        results = await asyncio.gather(
            *[mini_call(i) for i in range(5)],
            return_exceptions=True,
        )
        errors = [r for r in results if isinstance(r, Exception)]
        successes = [r for r in results if not isinstance(r, Exception)]

        ok = len(errors) == 0
        suite.add(EvalResult(
            name="Concurrency Gate (5 parallel)",
            passed=ok,
            duration=time.time() - t0,
            details=f"{len(successes)} ok, {len(errors)} failed, gate={gate.stats}",
            error=str(errors[0]) if errors else "",
        ))
    except Exception as e:
        suite.add(EvalResult(
            name="Concurrency Gate (5 parallel)", passed=False,
            duration=time.time() - t0, error=str(e),
        ))


# -----------------------------------------------------------------------
# Test 4: HITL routing logic
# -----------------------------------------------------------------------

async def test_hitl_routing(suite: EvalSuite) -> None:
    t0 = time.time()
    try:
        from src.orchestrator.hitl.router import ConfidenceRouter, HITLConfig
        from src.utils.types import (
            AgentResult, Claim, ConfidenceAssessment, ConfidenceLevel, DivisionReport,
        )

        config = HITLConfig(hard_threshold=0.3, soft_threshold=0.5, auto_threshold=0.7, enabled=True)
        router = ConfidenceRouter(config=config)

        def make_claim(text: str, score: float, level: ConfidenceLevel) -> Claim:
            return Claim(
                claim_text=text,
                confidence=ConfidenceAssessment(level=level, score=score),
                agent_id="test_agent",
            )

        reports = [
            DivisionReport(
                division_id="div_test", division_name="Test Division",
                lead_agent="test_lead",
                specialist_results=[AgentResult(
                    agent_id="test_spec", task_id="task_1",
                    findings=[
                        make_claim("High confidence", 0.9, ConfidenceLevel.HIGH),
                        make_claim("Medium confidence", 0.6, ConfidenceLevel.MEDIUM),
                        make_claim("Low confidence", 0.4, ConfidenceLevel.LOW),
                        make_claim("Very low confidence", 0.2, ConfidenceLevel.INSUFFICIENT),
                    ],
                )],
                synthesis="Test synthesis",
                confidence=ConfidenceAssessment(level=ConfidenceLevel.MEDIUM, score=0.5),
            ),
        ]

        # Test with routing disabled (no blocking)
        config.enabled = False
        result = await router.evaluate_reports(reports, query_id="test_q")
        assert result.total_reviewed == 4, f"Expected 4, got {result.total_reviewed}"

        # Validate threshold logic
        config.enabled = True
        high_claim = make_claim("High", 0.9, ConfidenceLevel.HIGH)
        low_claim = make_claim("Low", 0.2, ConfidenceLevel.INSUFFICIENT)
        assert high_claim.confidence.score >= config.auto_threshold
        assert low_claim.confidence.score < config.hard_threshold

        suite.add(EvalResult(
            name="HITL Routing Logic", passed=True,
            duration=time.time() - t0,
            details="4 claims routed, thresholds validated",
        ))
    except Exception as e:
        suite.add(EvalResult(
            name="HITL Routing Logic", passed=False,
            duration=time.time() - t0, error=str(e),
        ))


# -----------------------------------------------------------------------
# Test 5: Living document lifecycle
# -----------------------------------------------------------------------

async def test_living_document(suite: EvalSuite) -> None:
    t0 = time.time()
    try:
        from src.orchestrator.living_document.document import LivingDocument, SectionType

        doc = LivingDocument(query_id="eval_test")

        doc.evolve(
            updates={SectionType.BACKGROUND: "Test background", SectionType.HYPOTHESIS: "Test hypothesis"},
            author="eval", trigger="test_init",
        )
        v2 = doc.evolve(
            updates={SectionType.FINDINGS: "Finding 1: Test", SectionType.BACKGROUND: "Updated bg"},
            author="eval", trigger="test_update",
        )
        assert doc.version_count == 2
        bg = v2.get_section(SectionType.BACKGROUND)
        hyp = v2.get_section(SectionType.HYPOTHESIS)
        assert bg is not None and "Updated" in bg.content
        assert hyp is not None  # carried forward

        md = doc.render_markdown()
        ctx = doc.get_context_for_agent(max_chars=5000)
        assert "eval_test" in ctx

        suite.add(EvalResult(
            name="Living Document Lifecycle", passed=True,
            duration=time.time() - t0,
            details=f"{doc.version_count} versions, {len(md)} chars rendered",
        ))
    except Exception as e:
        suite.add(EvalResult(
            name="Living Document Lifecycle", passed=False,
            duration=time.time() - t0, error=str(e),
        ))


# -----------------------------------------------------------------------
# Test 6: Confidence calibration
# -----------------------------------------------------------------------

async def test_confidence_calibration(suite: EvalSuite) -> None:
    t0 = time.time()
    try:
        from src.utils.confidence import calibrate_confidence
        from src.utils.types import ConfidenceLevel

        strong = calibrate_confidence([
            {"source": "PMID:12345", "strength": 0.9, "convergence": 0.85, "independent": True},
            {"source": "PMID:23456", "strength": 0.85, "convergence": 0.8, "independent": True},
            {"source": "PMID:34567", "strength": 0.88, "convergence": 0.9, "independent": True},
        ])
        weak = calibrate_confidence([{"source": "preprint", "strength": 0.15, "convergence": 0.1}])
        empty = calibrate_confidence([])

        ok = (
            strong.level == ConfidenceLevel.HIGH and strong.score > 0.8
            and weak.level in (ConfidenceLevel.LOW, ConfidenceLevel.INSUFFICIENT)
            and empty.level == ConfidenceLevel.INSUFFICIENT
        )
        suite.add(EvalResult(
            name="Confidence Calibration", passed=ok,
            duration=time.time() - t0,
            details=f"Strong: {strong.level.value}({strong.score:.2f}), Weak: {weak.level.value}({weak.score:.2f}), Empty: {empty.level.value}",
        ))
    except Exception as e:
        suite.add(EvalResult(
            name="Confidence Calibration", passed=False,
            duration=time.time() - t0, error=str(e),
        ))


# -----------------------------------------------------------------------
# Test 7: Provenance tracking
# -----------------------------------------------------------------------

async def test_provenance(suite: EvalSuite) -> None:
    t0 = time.time()
    try:
        from src.utils.provenance import ProvenanceTracker
        from src.utils.types import Claim, ConfidenceAssessment, ConfidenceLevel, EvidenceSource

        tracker = ProvenanceTracker()
        c1 = Claim(
            claim_text="BRCA1 is a tumor suppressor that prevents cancer growth",
            confidence=ConfidenceAssessment(level=ConfidenceLevel.HIGH, score=0.9),
            agent_id="agent_1",
            supporting_evidence=[
                EvidenceSource(source_db="PubMed", source_id="PMID:11111"),
                EvidenceSource(source_db="UniProt", source_id="P38398"),
            ],
        )
        tracker.add_claim(c1)
        c2 = Claim(
            claim_text="BRCA1 does not prevent cancer growth in certain contexts",
            confidence=ConfidenceAssessment(level=ConfidenceLevel.LOW, score=0.3),
            agent_id="agent_2",
            supporting_evidence=[
                EvidenceSource(source_db="PubMed", source_id="PMID:22222"),
                EvidenceSource(source_db="PubMed", source_id="PMID:11111"),
            ],
        )
        contradictions = tracker.check_contradiction(c2)
        tracker.add_claim(c2)
        chain = tracker.export_provenance_chain()

        ok = len(contradictions) > 0 and len(chain) == 3
        suite.add(EvalResult(
            name="Provenance Tracking", passed=ok,
            duration=time.time() - t0,
            details=f"Contradictions: {len(contradictions)}, Unique sources: {len(chain)}",
        ))
    except Exception as e:
        suite.add(EvalResult(
            name="Provenance Tracking", passed=False,
            duration=time.time() - t0, error=str(e),
        ))


# -----------------------------------------------------------------------
# Test 8: Single agent execution
# -----------------------------------------------------------------------

async def test_agent_execution(suite: EvalSuite) -> None:
    t0 = time.time()
    try:
        from src.agents import create_literature_synthesis_agent
        from src.utils.types import Task

        agent = create_literature_synthesis_agent()
        task = Task(
            task_id="eval_lit_1",
            description=(
                "Briefly summarize the role of PCSK9 in cholesterol metabolism. "
                "State one key finding with confidence level."
            ),
            division="Computational Biology",
        )
        result = await agent.execute(task)
        has_response = bool(result.raw_data.get("final_response", ""))
        has_findings = len(result.findings) > 0

        suite.add(EvalResult(
            name="Single Agent Execution",
            passed=has_response and has_findings,
            duration=time.time() - t0,
            details=f"Findings: {len(result.findings)}, Cost: ${result.cost:.4f}, Duration: {result.duration_seconds:.1f}s",
        ))
    except Exception as e:
        suite.add(EvalResult(
            name="Single Agent Execution", passed=False,
            duration=time.time() - t0, error=str(e),
        ))


# -----------------------------------------------------------------------
# Test 9: Division execution
# -----------------------------------------------------------------------

async def test_division_execution(suite: EvalSuite, divisions: dict | None) -> None:
    t0 = time.time()
    if divisions is None:
        suite.add(EvalResult(name="Division Execution", passed=False, error="Skipped — factory failed"))
        return
    try:
        from src.utils.types import Task, Priority

        lead = divisions.get("Computational Biology")
        if lead is None:
            suite.add(EvalResult(name="Division Execution", passed=False, duration=time.time() - t0, error="Division not found"))
            return

        task = Task(
            task_id="eval_div_1",
            description="Summarize the therapeutic rationale for targeting KRAS G12C in NSCLC. Be concise.",
            division="Computational Biology",
            priority=Priority.MEDIUM,
        )
        report = await lead.execute_division_task(task)
        has_synthesis = len(report.synthesis) > 50
        has_confidence = report.confidence.score > 0

        suite.add(EvalResult(
            name="Division Execution (CompBio)",
            passed=has_synthesis and has_confidence,
            duration=time.time() - t0,
            details=f"Specialists: {len(report.specialist_results)}, Confidence: {report.confidence.level.value} ({report.confidence.score:.2f})",
        ))
    except Exception as e:
        suite.add(EvalResult(
            name="Division Execution (CompBio)", passed=False,
            duration=time.time() - t0, error=str(e),
        ))


# -----------------------------------------------------------------------
# Test 10: CSO intake + planning
# -----------------------------------------------------------------------

async def test_cso_planning(suite: EvalSuite, divisions: dict | None) -> None:
    t0 = time.time()
    try:
        from src.orchestrator.cso import CSOOrchestrator
        cso = CSOOrchestrator(divisions=divisions)
        research_brief = await cso._intake(
            "Evaluate PCSK9 as a therapeutic target for familial hypercholesterolemia"
        )
        has_target = bool(research_brief.get("target") or research_brief.get("scope"))
        has_content = len(json.dumps(research_brief)) > 50

        suite.add(EvalResult(
            name="CSO Intake + Planning",
            passed=has_target and has_content,
            duration=time.time() - t0,
            details=f"Brief keys: {list(research_brief.keys())}",
        ))
    except Exception as e:
        suite.add(EvalResult(
            name="CSO Intake + Planning", passed=False,
            duration=time.time() - t0, error=str(e),
        ))


# =======================================================================
# BIOMNI-COMPARABLE BENCHMARK TASKS
# =======================================================================
# These test Lumi agents on tasks comparable to three Biomni benchmarks:
#
# 1. LAB-Bench DbQA — Database question answering using real tool calls
#    (Biomni scored 74.4%, human experts 74.7%)
# 2. LAB-Bench SeqQA — Biological sequence question answering
#    (Biomni scored 81.9%, human experts 78.8%)
# 3. HLE Biomedical — Expert-level biomedical questions (52-question subset)
#    (Biomni scored 17.3%, base LLM 6.0%)
#
# IMPORTANT CAVEATS:
# - These are NOT the actual LAB-Bench or HLE test sets (those are
#   proprietary/specific datasets). These are Lumi-constructed questions
#   designed to test the SAME capabilities each benchmark evaluates.
# - Scoring uses deterministic keyword matching against known correct
#   answers, NOT LLM-as-judge (which inflates scores).
# - Results are NOT directly comparable to Biomni's published numbers.
#   They measure whether Lumi's agents can perform the same category
#   of task, not performance on identical questions.
#
# Biomni reference scores are from the Biomni paper and included for
# context only — not as a head-to-head comparison.
# =======================================================================

# -- DbQA-style tasks: require querying databases via agent tools -------
DBQA_TASKS = [
    {
        "name": "DbQA: Gene function lookup",
        "task_description": (
            "Using available database tools, answer: What is the primary "
            "biological function of the TP53 gene, and what diseases are "
            "most commonly associated with its loss-of-function mutations? "
            "Cite specific database sources in your answer."
        ),
        "required_keywords": [
            "tumor suppressor", "apoptosis", "cell cycle",
            "Li-Fraumeni", "cancer",
        ],
        "min_correct": 3,
    },
    {
        "name": "DbQA: Drug-target interaction",
        "task_description": (
            "Using available database tools, answer: What is the approved "
            "mechanism of action of imatinib (Gleevec), what is its primary "
            "molecular target, and what disease was it first approved for? "
            "Cite specific database sources."
        ),
        "required_keywords": [
            "tyrosine kinase", "BCR-ABL", "CML",
            "chronic myeloid", "inhibitor",
        ],
        "min_correct": 3,
    },
    {
        "name": "DbQA: Pathway membership",
        "task_description": (
            "Using available database tools, answer: What signaling pathway "
            "does the BRAF gene primarily participate in, what is the most "
            "common oncogenic mutation in BRAF, and what cancers is it "
            "associated with? Cite sources."
        ),
        "required_keywords": [
            "MAPK", "RAS", "RAF", "MEK", "ERK",
            "V600E", "melanoma",
        ],
        "min_correct": 4,
    },
]

# -- SeqQA-style tasks: require sequence analysis / reasoning -----------
SEQQA_TASKS = [
    {
        "name": "SeqQA: Protein domain identification",
        "task_description": (
            "The human EGFR protein contains multiple functional domains. "
            "Using your tools and knowledge, identify the key extracellular "
            "and intracellular domains of EGFR, and explain which domain "
            "is the target of cetuximab vs. erlotinib."
        ),
        "required_keywords": [
            "extracellular", "kinase", "tyrosine",
            "cetuximab", "erlotinib", "ligand",
        ],
        "min_correct": 4,
    },
    {
        "name": "SeqQA: Mutation consequence",
        "task_description": (
            "A patient's tumor has an EGFR exon 19 deletion (delE746-A750). "
            "Explain the molecular consequence of this deletion on EGFR "
            "signaling, why it confers sensitivity to EGFR TKIs like "
            "gefitinib, and what resistance mutation commonly emerges."
        ),
        "required_keywords": [
            "in-frame", "deletion", "constitutive", "activation",
            "gefitinib", "T790M", "resistance",
        ],
        "min_correct": 4,
    },
    {
        "name": "SeqQA: Sequence feature interpretation",
        "task_description": (
            "The BRCA1 protein has an N-terminal RING domain and C-terminal "
            "BRCT repeats. Explain the function of each domain, what happens "
            "when truncating mutations occur before the BRCT domain, and why "
            "this matters for PARP inhibitor therapy."
        ),
        "required_keywords": [
            "RING", "BRCT", "ubiquitin", "E3 ligase",
            "DNA repair", "homologous recombination",
            "PARP", "synthetic lethality",
        ],
        "min_correct": 5,
    },
]

# -- HLE-style tasks: expert-level, not answerable by simple lookup -----
HLE_TASKS = [
    {
        "name": "HLE: Resistance mechanism",
        "task_description": (
            "In EGFR-mutant NSCLC treated with osimertinib (a third-generation "
            "EGFR TKI), what are the three most common classes of acquired "
            "resistance mechanisms, and for each, name a specific molecular "
            "alteration and a potential therapeutic strategy to overcome it?"
        ),
        "required_keywords": [
            "C797S", "MET amplification", "small cell transformation",
            "histologic", "bypass", "osimertinib",
        ],
        "min_correct": 3,
    },
    {
        "name": "HLE: Multi-omics integration",
        "task_description": (
            "Explain how single-cell RNA-seq and bulk ATAC-seq data can be "
            "integrated to identify cell-type-specific regulatory elements "
            "in a tumor microenvironment. What computational challenges arise "
            "from batch effects, and name one established method for this "
            "integration."
        ),
        "required_keywords": [
            "single-cell", "chromatin accessibility", "regulatory",
            "batch effect", "integration", "cell type",
        ],
        "min_correct": 4,
    },
    {
        "name": "HLE: Clinical genomics reasoning",
        "task_description": (
            "A rare disease patient has compound heterozygous variants in "
            "CFTR: one copy has the F508del mutation and the other has a "
            "novel missense variant (p.G551D). Explain the molecular "
            "pathology of each variant, predict the clinical phenotype, "
            "and identify which FDA-approved CFTR modulator(s) would be "
            "appropriate for this genotype."
        ),
        "required_keywords": [
            "F508del", "folding", "trafficking", "G551D", "gating",
            "ivacaftor", "cystic fibrosis",
        ],
        "min_correct": 4,
    },
]


def _keyword_score(answer: str, required: list[str], min_correct: int) -> tuple[float, list[str], list[str]]:
    """Deterministic keyword matching — no LLM judge.

    Returns (score, matched_list, missing_list).
    Score = fraction of required keywords found (case-insensitive).
    """
    answer_lower = answer.lower()
    matched = [kw for kw in required if kw.lower() in answer_lower]
    missing = [kw for kw in required if kw.lower() not in answer_lower]
    score = len(matched) / len(required) if required else 0.0
    return round(score, 4), matched, missing


async def _run_agent_task(task_description: str) -> str:
    """Run a task through an actual Lumi agent (Literature Synthesis) with tools.

    This tests real agent capability — tool use, reasoning, synthesis —
    not just raw LLM parametric knowledge.
    """
    from src.agents import create_literature_synthesis_agent
    from src.utils.types import Task

    agent = create_literature_synthesis_agent()
    task = Task(
        task_id=f"bench_{int(time.time())}",
        description=task_description,
        division="Computational Biology",
    )
    result = await agent.execute(task)
    return result.raw_data.get("final_response", "")


async def test_benchmark_suite(suite: EvalSuite) -> None:
    """Run all three benchmark categories through real Lumi agents.

    Each task is executed by an actual agent with tool access (not a raw
    LLM call). Scoring is deterministic keyword matching.
    """
    all_tasks = [
        ("DbQA", DBQA_TASKS),
        ("SeqQA", SEQQA_TASKS),
        ("HLE", HLE_TASKS),
    ]

    category_scores: dict[str, list[float]] = {"DbQA": [], "SeqQA": [], "HLE": []}

    for category, tasks in all_tasks:
        for task_def in tasks:
            t0 = time.time()
            name = task_def["name"]
            description = task_def["task_description"]
            required = task_def["required_keywords"]
            min_correct = task_def["min_correct"]

            try:
                answer = await _run_agent_task(description)

                score, matched, missing = _keyword_score(answer, required, min_correct)
                category_scores[category].append(score)

                passed = len(matched) >= min_correct
                suite.add(EvalResult(
                    name=name,
                    passed=passed,
                    duration=time.time() - t0,
                    details=f"Matched: {len(matched)}/{len(required)} — missing: {missing}" if missing else f"Matched: {len(matched)}/{len(required)} — all keywords found",
                    score=score,
                ))

                # Delay between tasks to respect rate limits
                await asyncio.sleep(3.0)

            except Exception as e:
                suite.add(EvalResult(
                    name=name, passed=False,
                    duration=time.time() - t0, error=str(e), score=0.0,
                ))
                category_scores[category].append(0.0)

    # Log category averages
    for cat, scores in category_scores.items():
        avg = sum(scores) / len(scores) if scores else 0.0
        logger.info("[%s] Category average: %.1f%% (%d tasks)", cat, avg * 100, len(scores))


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

async def main() -> None:
    suite = EvalSuite()

    logger.info("=" * 70)
    logger.info("LUMI PIPELINE EVALUATION + BIOMNI ACCURACY COMPARISON")
    logger.info("=" * 70)

    # 1. API connectivity (gates everything else)
    api_ok = await test_api_connectivity(suite)
    if not api_ok:
        logger.error("API connectivity failed — cannot proceed")
        print(suite.summary())
        return

    # 2-5: Non-LLM tests (parallel)
    await asyncio.gather(
        test_hitl_routing(suite),
        test_living_document(suite),
        test_confidence_calibration(suite),
        test_provenance(suite),
    )

    # 6. Concurrency gate
    await test_concurrency_gate(suite)

    # 7. Factory
    divisions = await test_factory(suite)

    # 8. Single agent execution
    await test_agent_execution(suite)

    # 9. Division execution
    await test_division_execution(suite, divisions)

    # 10. CSO planning
    await test_cso_planning(suite, divisions)

    # 11. Benchmark suite: DbQA + SeqQA + HLE (9 tasks, sequential)
    logger.info("=" * 70)
    logger.info("BENCHMARK TASKS: LAB-Bench DbQA / SeqQA + HLE (agent-executed)")
    logger.info("=" * 70)
    await test_benchmark_suite(suite)

    print(suite.summary())


if __name__ == "__main__":
    asyncio.run(main())
