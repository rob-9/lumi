"""Regulatory Submissions sublab -- tox reviews with MoA illustrations.

Prepares regulatory-grade toxicology literature reviews and mechanism-
of-action safety assessments. Uses query-aware phase routing to focus
on the relevant regulatory domain (toxicology, MoA, clinical safety,
or regulatory strategy) and a consensus debate to align safety ratings
across pharmacology, toxicology, and clinical perspectives.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.sublabs.base import Sublab
from src.utils.llm import ModelTier
from src.utils.types import (
    Claim,
    DivisionReport,
    FinalReport,
    Phase,
    Priority,
)

logger = logging.getLogger("lumi.sublabs.regulatory_submissions")

# ---------------------------------------------------------------------------
# Query classification keywords
# ---------------------------------------------------------------------------

_TOXICOLOGY_KEYWORDS = [
    "tox", "toxicity", "toxicology", "hepatotoxicity", "cardiotoxicity",
    "nephrotoxicity", "neurotoxicity", "genotoxicity", "carcinogenicity",
    "reproductive toxicity", "developmental toxicity", "organ toxicity",
    "ld50", "noael", "noel", "dose-limiting", "mtd", "maximum tolerated",
    "ames", "micronucleus",
]

_MOA_KEYWORDS = [
    "mechanism of action", "moa", "on-target", "off-target", "pathway",
    "pharmacodynamic", "target engagement", "selectivity", "specificity",
    "polypharmacology", "class effect", "adverse outcome pathway", "aop",
]

_CLINICAL_SAFETY_KEYWORDS = [
    "adverse event", "adverse reaction", "faers", "post-marketing",
    "pharmacovigilance", "rems", "boxed warning", "black box",
    "contraindication", "drug interaction", "ddi", "clinical safety",
    "safety signal", "side effect", "tolerability",
]

_REGULATORY_STRATEGY_KEYWORDS = [
    "ind", "nda", "bla", "anda", "breakthrough", "accelerated approval",
    "fast track", "priority review", "orphan drug", "pediatric",
    "fda guidance", "ema", "ich", "ctd", "module", "submission",
    "regulatory", "filing", "approval pathway", "pre-ind",
]


def _classify_regulatory_query(query: str) -> list[str]:
    """Classify a regulatory submission query into focus areas.

    Returns a list of matched categories ordered by relevance.
    Always includes ``"general"`` as a fallback.
    """
    q = query.lower()
    categories: list[str] = []

    score_map = {
        "toxicology": sum(1 for kw in _TOXICOLOGY_KEYWORDS if kw in q),
        "moa": sum(1 for kw in _MOA_KEYWORDS if kw in q),
        "clinical_safety": sum(1 for kw in _CLINICAL_SAFETY_KEYWORDS if kw in q),
        "regulatory_strategy": sum(1 for kw in _REGULATORY_STRATEGY_KEYWORDS if kw in q),
    }

    for cat, score in sorted(score_map.items(), key=lambda x: x[1], reverse=True):
        if score > 0:
            categories.append(cat)

    if not categories:
        categories.append("general")
    return categories


class RegulatorySubmissionsSublab(Sublab):
    """Focused pipeline for regulatory submission support.

    Enhancements over the base sublab:

    1. **Query-aware phase routing** -- analyses the query to determine
       which regulatory domain to emphasise (toxicology, MoA, clinical
       safety, or regulatory strategy).
    2. **Consensus debate** -- aligns safety risk ratings across
       toxicology, pharmacology, and clinical perspectives before
       finalising the regulatory risk assessment.
    3. **Structured synthesis** -- populates the six report sections
       with regulatory-grade content including gap analysis and
       recommended studies.
    """

    name = "Regulatory Submissions"
    description = "Tox literature reviews with MoA illustrations"

    agent_names = [
        "toxicogenomics",
        "pharmacologist",
        "fda_safety",
        "literature_synthesis",
        "clinical_trialist",
    ]

    tool_names = [
        "query_gene_chemical_interactions",
        "query_faers",
        "get_drug_safety",
        "search_papers",
        "search_trials",
        "get_pathways_for_gene",
    ]

    division_names = [
        "Target Safety",
        "Computational Biology",
        "Clinical Intelligence",
    ]

    phases = [
        "toxicology_review",
        "mechanism_of_action",
        "clinical_safety",
        "regulatory_compilation",
    ]

    debate_protocol = "consensus"
    report_sections = [
        "Nonclinical Toxicology Summary",
        "Mechanism of Action",
        "Clinical Safety Data",
        "Regulatory Risk Assessment",
        "Gap Analysis",
        "Recommended Studies",
    ]

    examples = [
        "Prepare a nonclinical toxicology summary for an anti-CD20 antibody",
        "Review hepatotoxicity signals for kinase inhibitor class",
        "Compile mechanism-of-action safety assessment for bispecific antibody",
    ]

    # ------------------------------------------------------------------
    # Query-aware phase routing
    # ------------------------------------------------------------------

    def _build_phases(self, query: str) -> list[Phase]:
        categories = _classify_regulatory_query(query)
        phases: list[Phase] = []
        phase_id = 0

        # Phase 1 (always): Toxicology literature review — the foundation
        # of any regulatory submission package.
        phase_id += 1
        phases.append(
            Phase(
                phase_id=phase_id,
                name="Toxicology Literature Review",
                division="Target Safety",
                agents=["toxicogenomics", "fda_safety"],
                dependencies=[],
                parallel_eligible=True,
                priority=Priority.HIGH,
                estimated_cost=1.50,
            ),
        )
        tox_review_id = phase_id

        # Phase 2 (always): Literature compilation runs in parallel with
        # tox review to gather published evidence.
        phase_id += 1
        phases.append(
            Phase(
                phase_id=phase_id,
                name="Literature Compilation",
                division="Computational Biology",
                agents=["literature_synthesis"],
                dependencies=[],
                parallel_eligible=True,
                priority=Priority.MEDIUM,
                estimated_cost=0.60,
            ),
        )
        lit_id = phase_id

        # Phase 3 (conditional): MoA & pharmacology deep-dive when
        # mechanism-related or general queries are submitted.
        if "moa" in categories or "general" in categories:
            phase_id += 1
            phases.append(
                Phase(
                    phase_id=phase_id,
                    name="Mechanism of Action & Pharmacology Assessment",
                    division="Target Safety",
                    agents=["pharmacologist"],
                    dependencies=[tox_review_id],
                    parallel_eligible=False,
                    priority=Priority.HIGH,
                    estimated_cost=1.00,
                ),
            )

        # Phase 4 (conditional): Clinical safety evidence when clinical
        # safety signals or post-marketing data are relevant.
        if "clinical_safety" in categories or "general" in categories:
            phase_id += 1
            phases.append(
                Phase(
                    phase_id=phase_id,
                    name="Clinical Safety Evidence Review",
                    division="Clinical Intelligence",
                    agents=["clinical_trialist"],
                    dependencies=[tox_review_id],
                    parallel_eligible=False,
                    priority=Priority.HIGH,
                    estimated_cost=0.90,
                ),
            )

        # Phase 5 (conditional): Regulatory strategy assessment when
        # submission pathway questions are raised.
        if "regulatory_strategy" in categories:
            phase_id += 1
            phases.append(
                Phase(
                    phase_id=phase_id,
                    name="Regulatory Strategy & Pathway Assessment",
                    division="Clinical Intelligence",
                    agents=["clinical_trialist"],
                    dependencies=[tox_review_id, lit_id],
                    parallel_eligible=False,
                    priority=Priority.MEDIUM,
                    estimated_cost=0.80,
                ),
            )

        # Final phase (always): Regulatory compilation depends on all
        # prior phases to produce the integrated risk assessment.
        prior_ids = [p.phase_id for p in phases]
        phase_id += 1
        phases.append(
            Phase(
                phase_id=phase_id,
                name="Regulatory Risk Compilation & Gap Analysis",
                division="Target Safety",
                agents=["fda_safety", "toxicogenomics"],
                dependencies=prior_ids,
                parallel_eligible=False,
                priority=Priority.HIGH,
                estimated_cost=1.00,
            ),
        )

        return phases

    # ------------------------------------------------------------------
    # Consensus debate
    # ------------------------------------------------------------------

    async def _run_debate(
        self,
        query: str,
        reports: list[DivisionReport],
    ) -> list[dict[str, Any]]:
        """Run consensus debate to align safety risk ratings.

        Unlike elimination (which removes hypotheses), consensus debate
        seeks agreement across disciplines on:
        1. Overall safety risk level (low / moderate / high / critical)
        2. Key safety liabilities and their severity
        3. Whether data gaps are acceptable for the submission stage
        """
        all_claims: list[Claim] = []
        for r in reports:
            for sr in r.specialist_results:
                all_claims.extend(sr.findings)

        if len(all_claims) < 2:
            return []

        claims_text = "\n".join(
            f"- [{c.agent_id}] {c.claim_text} "
            f"(confidence: {c.confidence.level.value}, score: {c.confidence.score:.2f})"
            for c in all_claims
        )

        debate_prompt = (
            "You are moderating a regulatory safety consensus debate.\n\n"
            f"Submission context: {query}\n\n"
            f"Agent findings:\n{claims_text}\n\n"
            "Run a consensus debate in 2 rounds:\n\n"
            "Round 1 — Each discipline states its safety risk assessment:\n"
            "  - Toxicology perspective: nonclinical safety signals and severity\n"
            "  - Pharmacology perspective: on-target vs off-target risk, therapeutic index\n"
            "  - Clinical perspective: clinical safety signals, class effects, post-marketing data\n"
            "  For each, provide an independent risk rating (low/moderate/high/critical)\n"
            "  with supporting evidence.\n\n"
            "Round 2 — Consensus building:\n"
            "  - Identify areas of agreement and disagreement\n"
            "  - Resolve disagreements by weighing evidence strength\n"
            "  - Arrive at a consensus risk rating with confidence level\n"
            "  - List unresolved data gaps that could change the assessment\n\n"
            "Return a JSON array of round objects:\n"
            "[\n"
            "  {\n"
            '    "round": 1,\n'
            '    "perspectives": [\n'
            "      {\n"
            '        "discipline": "toxicology|pharmacology|clinical",\n'
            '        "risk_rating": "low|moderate|high|critical",\n'
            '        "key_findings": ["finding1", "finding2"],\n'
            '        "evidence_strength": 0.8,\n'
            '        "caveats": ["caveat1"]\n'
            "      }\n"
            "    ]\n"
            "  },\n"
            "  {\n"
            '    "round": 2,\n'
            '    "consensus_rating": "low|moderate|high|critical",\n'
            '    "confidence": 0.75,\n'
            '    "agreements": ["agreed point 1"],\n'
            '    "disagreements": ["disagreement with resolution"],\n'
            '    "data_gaps": ["gap that could change assessment"],\n'
            '    "regulatory_implications": "summary of what this means for submission"\n'
            "  }\n"
            "]\n\n"
            "Return ONLY the JSON array."
        )

        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": debate_prompt}],
                model=ModelTier.SONNET,
                system=(
                    f"You are the consensus debate moderator for the {self.name} sublab. "
                    "Your job is to align safety risk assessments across toxicology, "
                    "pharmacology, and clinical perspectives into a unified regulatory "
                    "risk rating."
                ),
            )
            text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            cleaned = text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [ln for ln in lines if not ln.strip().startswith("```")]
                cleaned = "\n".join(lines)
            rounds = json.loads(cleaned)
            if isinstance(rounds, list):
                return rounds
        except Exception as exc:
            logger.warning("[%s] Consensus debate failed: %s", self.name, exc)

        return []

    # ------------------------------------------------------------------
    # Structured synthesis
    # ------------------------------------------------------------------

    async def _synthesize(
        self,
        query: str,
        reports: list[DivisionReport],
        debate_rounds: list[dict[str, Any]],
    ) -> FinalReport:
        """Synthesise findings into the six regulatory report sections.

        Produces regulatory-grade content with nonclinical tox summary,
        MoA assessment, clinical safety review, risk assessment, gap
        analysis, and recommended studies.
        """
        all_claims: list[Claim] = []
        all_evidence: list[Any] = []

        report_texts: list[str] = []
        for r in reports:
            report_texts.append(
                f"### {r.division_name}\n"
                f"Confidence: {r.confidence.level.value} ({r.confidence.score})\n"
                f"Synthesis: {r.synthesis[:1500]}\n"
            )
            for sr in r.specialist_results:
                all_claims.extend(sr.findings)
                for claim in sr.findings:
                    all_evidence.extend(claim.supporting_evidence)

        # Build debate context for synthesis.
        debate_context = ""
        if debate_rounds:
            consensus_round = next(
                (r for r in debate_rounds if r.get("round") == 2),
                debate_rounds[-1] if debate_rounds else {},
            )
            if "consensus_rating" in consensus_round:
                debate_context = (
                    f"\n\nConsensus debate outcome:\n"
                    f"  Risk rating: {consensus_round.get('consensus_rating', 'unknown')}\n"
                    f"  Confidence: {consensus_round.get('confidence', 'N/A')}\n"
                    f"  Agreements: {json.dumps(consensus_round.get('agreements', []))}\n"
                    f"  Data gaps: {json.dumps(consensus_round.get('data_gaps', []))}\n"
                    f"  Regulatory implications: {consensus_round.get('regulatory_implications', 'N/A')}\n"
                )
            else:
                debate_context = f"\n\nConsensus debate ran {len(debate_rounds)} round(s)."

        synthesis_prompt = (
            "You are synthesising a regulatory submission support report.\n\n"
            f"Submission context: {query}\n\n"
            f"Division reports:\n{''.join(report_texts)}\n"
            f"{debate_context}\n\n"
            "Produce a JSON object with exactly these six keys matching the "
            "report sections:\n\n"
            "{\n"
            '  "nonclinical_toxicology_summary": {\n'
            '    "overview": "summary of nonclinical tox findings",\n'
            '    "organ_toxicities": [\n'
            "      {\n"
            '        "organ": "liver|heart|kidney|CNS|other",\n'
            '        "finding": "description",\n'
            '        "severity": "minimal|mild|moderate|severe",\n'
            '        "species": "mouse|rat|dog|monkey|human",\n'
            '        "reversibility": "reversible|partially_reversible|irreversible|unknown"\n'
            "      }\n"
            "    ],\n"
            '    "genotoxicity": "summary of genotox findings or data gaps",\n'
            '    "carcinogenicity": "summary or data gap notation"\n'
            "  },\n"
            '  "mechanism_of_action": {\n'
            '    "primary_pharmacology": "description of intended MoA",\n'
            '    "on_target_risks": ["risk1"],\n'
            '    "off_target_risks": ["risk1"],\n'
            '    "class_effects": ["known class effect"]\n'
            "  },\n"
            '  "clinical_safety_data": {\n'
            '    "overview": "summary of clinical safety evidence",\n'
            '    "key_adverse_events": [\n'
            "      {\n"
            '        "event": "adverse event description",\n'
            '        "frequency": "common|uncommon|rare|very_rare|unknown",\n'
            '        "severity": "mild|moderate|severe|life_threatening",\n'
            '        "source": "FAERS|trial|label|literature"\n'
            "      }\n"
            "    ],\n"
            '    "risk_mitigation": ["mitigation strategy"]\n'
            "  },\n"
            '  "regulatory_risk_assessment": {\n'
            '    "overall_risk": "low|moderate|high|critical",\n'
            '    "confidence": 0.75,\n'
            '    "key_risks": [\n'
            "      {\n"
            '        "risk": "description",\n'
            '        "likelihood": "low|moderate|high",\n'
            '        "impact": "low|moderate|high|critical",\n'
            '        "mitigation": "proposed mitigation"\n'
            "      }\n"
            "    ],\n"
            '    "regulatory_implications": "what this means for the submission"\n'
            "  },\n"
            '  "gap_analysis": [\n'
            "    {\n"
            '      "gap": "description of missing data",\n'
            '      "regulatory_requirement": "which guideline requires it",\n'
            '      "criticality": "blocking|important|nice_to_have",\n'
            '      "resolution": "how to address the gap"\n'
            "    }\n"
            "  ],\n"
            '  "recommended_studies": [\n'
            "    {\n"
            '      "study": "study description",\n'
            '      "type": "in_vitro|in_vivo|clinical|computational",\n'
            '      "objective": "what it addresses",\n'
            '      "priority": "critical|high|medium|low",\n'
            '      "estimated_timeline": "timeline estimate"\n'
            "    }\n"
            "  ],\n"
            '  "executive_summary": "2-3 paragraph regulatory-grade summary of the '
            "overall safety profile, key risks, data gaps, and recommended path forward.\"\n"
            "}\n\n"
            "Return ONLY the JSON object."
        )

        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": synthesis_prompt}],
                model=ModelTier.SONNET,
                system=(
                    f"You are the synthesis engine for the {self.name} sublab. "
                    "Produce a regulatory-grade safety assessment with structured "
                    "toxicology summary, MoA analysis, clinical safety data, risk "
                    "assessment, gap analysis, and recommended studies."
                ),
            )
            text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            cleaned = text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [ln for ln in lines if not ln.strip().startswith("```")]
                cleaned = "\n".join(lines)
            synthesis = json.loads(cleaned)

            # Build evidence_synthesis from the structured sections.
            evidence_synthesis: dict[str, Any] = {
                "Nonclinical Toxicology Summary": synthesis.get("nonclinical_toxicology_summary", {}),
                "Mechanism of Action": synthesis.get("mechanism_of_action", {}),
                "Clinical Safety Data": synthesis.get("clinical_safety_data", {}),
                "Regulatory Risk Assessment": synthesis.get("regulatory_risk_assessment", {}),
                "Gap Analysis": synthesis.get("gap_analysis", []),
                "Recommended Studies": synthesis.get("recommended_studies", []),
            }

            # Derive recommended_experiments from recommended_studies.
            recommended_experiments: list[dict[str, str]] = []
            for study in synthesis.get("recommended_studies", []):
                recommended_experiments.append({
                    "experiment": study.get("study", ""),
                    "rationale": study.get("objective", ""),
                    "priority": study.get("priority", "medium"),
                    "type": study.get("type", ""),
                })

            # Extract risk assessment for the report.
            risk_data = synthesis.get("regulatory_risk_assessment", {})
            risk_assessment: dict[str, Any] = {
                "overall_risk": risk_data.get("overall_risk", "unknown"),
                "confidence": risk_data.get("confidence", 0.5),
                "key_risks": risk_data.get("key_risks", []),
                "regulatory_implications": risk_data.get("regulatory_implications", ""),
            }

            # Build limitations from gap analysis.
            limitations: list[str] = []
            gaps = synthesis.get("gap_analysis", [])
            blocking_gaps = [g for g in gaps if g.get("criticality") == "blocking"]
            if blocking_gaps:
                limitations.append(
                    f"{len(blocking_gaps)} blocking data gap(s) identified — "
                    "these must be addressed before regulatory submission."
                )
            if risk_data.get("confidence", 1.0) < 0.6:
                limitations.append(
                    "Regulatory risk confidence is below 0.6 — additional data "
                    "collection is recommended to strengthen the assessment."
                )

            return FinalReport(
                query_id=self._query_id,
                user_query=query,
                executive_summary=synthesis.get("executive_summary", ""),
                evidence_synthesis=evidence_synthesis,
                key_findings=all_claims[:20],
                risk_assessment=risk_assessment,
                recommended_experiments=recommended_experiments,
                limitations=limitations,
                provenance_chain=all_evidence[:50],
            )

        except Exception as exc:
            logger.error("[%s] Synthesis failed: %s", self.name, exc)
            return FinalReport(
                query_id=self._query_id,
                user_query=query,
                executive_summary=f"Synthesis failed: {exc}",
                key_findings=all_claims[:10],
                limitations=[f"Synthesis error: {exc}"],
                provenance_chain=all_evidence[:20],
            )
