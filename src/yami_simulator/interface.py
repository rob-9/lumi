"""
Yami Simulator Interface

Wraps calls to Protein Design MCP tools + LLM interpretation to simulate
a custom protein language model. For MVP, calls underlying tool functions
directly rather than via MCP protocol.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger("lumi.yami.interface")

# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ScoringResult:
    fitness_score: float
    stability_estimate: str
    fold_confidence: float
    expression_prediction: str
    solubility_class: str
    confidence: float


@dataclass
class MutantEffectResult:
    ddG_proxy: float  # negative = stabilizing
    effect_on_binding: str
    effect_on_expression: str
    effect_on_immunogenicity: str
    confidence: float
    rationale: str
    per_mutation_effects: list[dict] = field(default_factory=list)


@dataclass
class DesignCandidate:
    sequence: str
    predicted_fitness: float
    constraint_satisfaction: dict
    novelty_score: float
    closest_natural_sequence: str


@dataclass
class ParetoFront:
    candidates: list[DesignCandidate]
    objective_tradeoffs: str
    recommended_candidates: list[DesignCandidate]
    optimization_trajectory: list[dict]


# ---------------------------------------------------------------------------
# Yami Interface
# ---------------------------------------------------------------------------


class YamiInterface:
    """
    High-level protein intelligence interface.

    Aggregates results from ESM-2, AlphaFold DB, Biopython, and LLM
    interpretation to provide composite protein analysis capabilities.
    """

    def __init__(self):
        # Lazy import of MCP tool functions to avoid circular deps
        self._tools_imported = False

    def _ensure_tools(self):
        """Import tool functions on first use."""
        if self._tools_imported:
            return
        try:
            from src.mcp_servers.protein_design.server import (
                esm2_score_sequence,
                esm2_mutant_effect,
                esm2_embed,
                calculate_protein_properties,
                predict_solubility,
                predict_structure_alphafold,
                blast_sequence,
                calculate_cai,
                number_antibody,
                predict_developability,
            )
            self._esm2_score_sequence = esm2_score_sequence
            self._esm2_mutant_effect = esm2_mutant_effect
            self._esm2_embed = esm2_embed
            self._calculate_protein_properties = calculate_protein_properties
            self._predict_solubility = predict_solubility
            self._predict_structure_alphafold = predict_structure_alphafold
            self._blast_sequence = blast_sequence
            self._calculate_cai = calculate_cai
            self._number_antibody = number_antibody
            self._predict_developability = predict_developability
            self._tools_imported = True
        except ImportError as exc:
            logger.error("Failed to import protein design tools: %s", exc)
            self._tools_imported = False

    # ------------------------------------------------------------------
    # score
    # ------------------------------------------------------------------

    async def score(self, sequence: str) -> ScoringResult:
        """
        Composite protein fitness scoring.

        Aggregates ESM-2 pseudo-perplexity, physicochemical properties,
        solubility prediction, and developability assessment into a single
        ScoringResult with calibrated confidence.
        """
        self._ensure_tools()

        # Run tools concurrently
        esm_result, props_result, sol_result, dev_result = await asyncio.gather(
            asyncio.to_thread(self._safe_esm2_score, sequence),
            asyncio.to_thread(self._safe_protein_properties, sequence),
            asyncio.to_thread(self._safe_predict_solubility, sequence),
            asyncio.to_thread(self._safe_predict_developability, sequence),
        )

        # --- Fitness score (ESM-2 primary, with biophysical corrections) ---
        esm_fitness = esm_result.get("fitness_score", 0.5)
        esm_confidence = esm_result.get("overall_confidence", 0.1)
        sol_score = sol_result.get("score", 0.5)

        # Developability penalty: high-risk flags reduce effective fitness
        dev_risk = dev_result.get("overall_risk", "low")
        dev_penalty = {"low": 0.0, "medium": 0.05, "high": 0.12}.get(dev_risk, 0.0)

        # Composite fitness: ESM-2 weighted by biophysical quality
        fitness = esm_fitness * 0.65 + sol_score * 0.20 + 0.15 - dev_penalty
        fitness = max(0.0, min(1.0, fitness))

        # --- Stability estimate from multiple features ---
        instability_idx = props_result.get("instability_index", 40.0)
        gravy = props_result.get("gravy", 0.0)
        aa_comp = props_result.get("amino_acid_composition", {})

        # Aliphatic index (thermal stability indicator)
        aliphatic_idx = (
            aa_comp.get("A", 0) * 100
            + aa_comp.get("V", 0) * 2.9 * 100
            + aa_comp.get("I", 0) * 3.9 * 100
            + aa_comp.get("L", 0) * 3.9 * 100
        )

        if instability_idx < 25 and aliphatic_idx > 70:
            stability_estimate = "highly_stable"
        elif instability_idx < 40:
            stability_estimate = "stable"
        elif instability_idx < 50 and aliphatic_idx > 60:
            stability_estimate = "marginally_stable"
        else:
            stability_estimate = "unstable"

        # --- Fold confidence from ESM-2 perplexity ---
        perplexity = esm_result.get("pseudo_perplexity")
        if perplexity is not None:
            # Calibrated mapping: natural proteins typically 5-15 perplexity
            fold_confidence = max(0.0, min(1.0, 1.0 - (perplexity - 3.0) / 20.0))
        else:
            fold_confidence = 0.3

        # --- Expression prediction (multi-factor) ---
        sol_class = sol_result.get("solubility_class", "unknown")
        seq_len = len(sequence)

        expr_score = 0.5
        if sol_class == "soluble":
            expr_score += 0.15
        elif sol_class == "insoluble":
            expr_score -= 0.2
        if instability_idx < 40:
            expr_score += 0.1
        if -0.5 < gravy < 0.0:
            expr_score += 0.05  # mildly hydrophilic is ideal
        if seq_len > 800:
            expr_score -= 0.1  # large proteins harder to express
        if dev_risk == "high":
            expr_score -= 0.1

        if expr_score >= 0.7:
            expression_prediction = "likely_high"
        elif expr_score >= 0.5:
            expression_prediction = "moderate"
        elif expr_score >= 0.35:
            expression_prediction = "likely_low"
        else:
            expression_prediction = "poor"

        # --- Composite confidence ---
        confidence = esm_confidence * 0.5 + (0.3 if props_result.get("molecular_weight") else 0.0) + 0.2 * sol_score

        return ScoringResult(
            fitness_score=round(fitness, 4),
            stability_estimate=stability_estimate,
            fold_confidence=round(fold_confidence, 4),
            expression_prediction=expression_prediction,
            solubility_class=sol_class,
            confidence=round(confidence, 4),
        )

    # ------------------------------------------------------------------
    # mutant_effect
    # ------------------------------------------------------------------

    async def mutant_effect(self, wildtype: str, mutations: list[str]) -> MutantEffectResult:
        """
        Predict the effect of mutations on protein function.

        Uses ESM-2 masked marginal scoring to compute log-likelihood ratios
        and interprets results for binding, expression, and immunogenicity.
        Includes empirically-calibrated ddG estimates in kcal/mol.
        """
        self._ensure_tools()

        mutations_str = ",".join(mutations)
        esm_result = await asyncio.to_thread(
            self._safe_esm2_mutant_effect, wildtype, mutations_str
        )

        per_mut = esm_result.get("per_mutation_effects", [])
        overall_delta = esm_result.get("overall_delta_ll", 0.0)
        confidence = esm_result.get("confidence", 0.0)

        # ddG proxy: use calibrated estimate from MCP server (1.5 kcal/mol per unit delta_ll)
        ddG_proxy = esm_result.get("overall_ddg_estimate_kcal_mol", round(-overall_delta * 1.5, 2))

        # --- Binding effect interpretation (position-aware) ---
        # Mutations at conserved positions are more likely to affect binding
        conserved_mutations = sum(
            1 for m in per_mut if m.get("position_conservation") == "highly_conserved"
        )
        destabilizing = [m for m in per_mut if m.get("predicted_impact") in ("destabilizing", "highly_destabilizing")]

        if overall_delta > 0.3:
            effect_on_binding = "likely_improved"
        elif overall_delta < -0.5 and conserved_mutations > 0:
            effect_on_binding = "likely_reduced"
        elif overall_delta < -1.5:
            effect_on_binding = "likely_reduced"
        elif abs(overall_delta) <= 0.3:
            effect_on_binding = "likely_neutral"
        else:
            effect_on_binding = "uncertain"

        # --- Expression effect (stability-dependent) ---
        if ddG_proxy < -1.0:  # stabilizing
            effect_on_expression = "likely_improved"
        elif ddG_proxy > 2.0:  # significantly destabilizing
            effect_on_expression = "likely_reduced"
        elif ddG_proxy > 0.5 and len(destabilizing) > 1:
            effect_on_expression = "likely_reduced"
        else:
            effect_on_expression = "likely_neutral"

        # --- Immunogenicity assessment ---
        # Mutations at variable positions are tolerated; conserved positions diverge from germline
        destabilizing_count = len(destabilizing)
        conserved_destab = sum(
            1 for m in per_mut
            if m.get("predicted_impact") in ("destabilizing", "highly_destabilizing")
            and m.get("position_conservation") == "highly_conserved"
        )

        if conserved_destab > 0:
            effect_on_immunogenicity = "potentially_increased"
        elif destabilizing_count > len(mutations) * 0.6:
            effect_on_immunogenicity = "potentially_increased"
        else:
            effect_on_immunogenicity = "likely_unchanged"

        # --- Build rationale ---
        impacts = [m.get("predicted_impact", "unknown") for m in per_mut if "predicted_impact" in m]
        ddg_estimates = [m.get("ddg_estimate_kcal_mol", "?") for m in per_mut if "ddg_estimate_kcal_mol" in m]

        rationale = (
            f"Analysis of {len(mutations)} mutation(s) using ESM-2 masked marginal scoring. "
            f"Overall delta log-likelihood: {overall_delta:.3f} "
            f"(estimated ddG: {ddG_proxy:+.1f} kcal/mol). "
            f"Individual: {', '.join(f'{m}: {i} ({d:+.1f} kcal/mol)' for m, i, d in zip(mutations, impacts, ddg_estimates) if isinstance(d, (int, float)))}. "
            f"Note: ddG estimates are approximate (ESM-2 correlation r~0.4-0.5 with experimental values)."
        )

        return MutantEffectResult(
            ddG_proxy=round(ddG_proxy, 4),
            effect_on_binding=effect_on_binding,
            effect_on_expression=effect_on_expression,
            effect_on_immunogenicity=effect_on_immunogenicity,
            confidence=round(confidence, 4),
            rationale=rationale,
            per_mutation_effects=per_mut,
        )

    # ------------------------------------------------------------------
    # stability
    # ------------------------------------------------------------------

    async def stability(self, sequence: str) -> dict[str, Any]:
        """
        Assess protein stability using ESM-2 perplexity, physicochemical
        properties, and composition-based features.

        Combines: ESM-2 pseudo-perplexity, instability index, aliphatic index,
        GRAVY, disulfide bond potential, proline content, and charge balance.
        """
        self._ensure_tools()

        esm_result, props_result, dev_result = await asyncio.gather(
            asyncio.to_thread(self._safe_esm2_score, sequence),
            asyncio.to_thread(self._safe_protein_properties, sequence),
            asyncio.to_thread(self._safe_predict_developability, sequence),
        )

        perplexity = esm_result.get("pseudo_perplexity")
        instability_idx = props_result.get("instability_index", None)
        gravy = props_result.get("gravy", None)
        aa_comp = props_result.get("amino_acid_composition", {})
        seq_len = len(sequence)

        # --- Feature calculations ---
        # Aliphatic index: thermal stability indicator (Ikai, 1980)
        aliphatic_idx = (
            aa_comp.get("A", 0) * 100
            + aa_comp.get("V", 0) * 2.9 * 100
            + aa_comp.get("I", 0) * 3.9 * 100
            + aa_comp.get("L", 0) * 3.9 * 100
        )

        # Disulfide bond potential (paired cysteines stabilize)
        cys_count = round(aa_comp.get("C", 0) * seq_len)
        disulfide_pairs = cys_count // 2
        disulfide_contribution = min(disulfide_pairs * 0.03, 0.12)  # each bond ~3-5 kcal/mol

        # Proline content: rigidifies backbone, stabilizes against unfolding
        pro_frac = aa_comp.get("P", 0)
        pro_contribution = min(pro_frac * 0.5, 0.05)

        # Charge balance: extreme net charge destabilizes
        charge = props_result.get("charge_at_pH7", 0)
        charge_density = abs(charge) / max(seq_len, 1)
        charge_penalty = max(0, (charge_density - 0.05) * 2)  # penalty above 5% net charge

        # --- Composite stability score ---
        scores = []
        weights = []

        if perplexity is not None:
            # ESM-2 component: low perplexity = evolutionarily fit = likely stable
            esm_stability = max(0.0, min(1.0, 1.0 - (perplexity - 3.0) / 20.0))
            scores.append(esm_stability)
            weights.append(0.35)

        if instability_idx is not None:
            # Instability index component (Guruprasad et al., 1990)
            ii_score = max(0.0, min(1.0, 1.0 - instability_idx / 80.0))
            scores.append(ii_score)
            weights.append(0.25)

        # Aliphatic index component (higher = more thermostable, but diminishing returns)
        ai_score = max(0.0, min(1.0, aliphatic_idx / 120.0))
        scores.append(ai_score)
        weights.append(0.15)

        # GRAVY component: moderately hydrophobic cores stabilize folding
        if gravy is not None:
            # Optimal GRAVY for globular proteins: -0.4 to +0.2
            if -0.4 <= gravy <= 0.2:
                gravy_score = 0.8
            elif gravy < -0.4:
                gravy_score = max(0.3, 0.8 + (gravy + 0.4) * 0.5)
            else:
                gravy_score = max(0.2, 0.8 - (gravy - 0.2) * 1.5)
            scores.append(gravy_score)
            weights.append(0.10)

        # Structural stabilizers (disulfides + prolines)
        stabilizer_score = 0.5 + disulfide_contribution + pro_contribution - charge_penalty
        scores.append(max(0.0, min(1.0, stabilizer_score)))
        weights.append(0.15)

        # Weighted average
        total_weight = sum(weights)
        stability_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
        stability_score = max(0.0, min(1.0, stability_score))

        # Confidence depends on available data sources
        confidence = 0.3 + 0.35 * (perplexity is not None) + 0.15 * (instability_idx is not None) + 0.1 * (gravy is not None)

        # Developability flags that affect stability interpretation
        dev_flags = [f["type"] for f in dev_result.get("risk_flags", []) if f.get("severity") == "high"]

        return {
            "stability_score": round(stability_score, 4),
            "esm2_perplexity": perplexity,
            "instability_index": instability_idx,
            "aliphatic_index": round(aliphatic_idx, 2),
            "gravy": gravy,
            "disulfide_pairs": disulfide_pairs,
            "proline_fraction": round(pro_frac, 4),
            "charge_at_pH7": charge,
            "is_stable": instability_idx < 40 if instability_idx is not None else None,
            "predicted_relative_stability": (
                "high" if stability_score > 0.7 else
                "medium" if stability_score > 0.4 else
                "low"
            ),
            "high_risk_flags": dev_flags,
            "confidence": round(confidence, 4),
        }

    # ------------------------------------------------------------------
    # fold_confidence
    # ------------------------------------------------------------------

    async def fold_confidence(self, sequence: str, uniprot_id: Optional[str] = None) -> dict[str, Any]:
        """
        Assess folding confidence.

        If a UniProt ID is available, fetches AlphaFold pLDDT.
        Otherwise falls back to ESM-2 confidence proxy.
        """
        self._ensure_tools()

        if uniprot_id:
            try:
                af_result = await self._predict_structure_alphafold(uniprot_id)
                if "error" not in af_result:
                    plddt = af_result.get("pLDDT_mean", 0)
                    return {
                        "source": "alphafold_db",
                        "pLDDT_mean": plddt,
                        "fold_confidence": round(plddt / 100.0, 4) if plddt else 0.5,
                        "model_confidence": af_result.get("model_confidence", "unknown"),
                        "structure_url": af_result.get("structure_url", ""),
                        "per_residue_pLDDT": af_result.get("pLDDT_per_residue", []),
                        "confidence": 0.9,
                    }
            except Exception as exc:
                logger.warning("AlphaFold lookup failed for %s: %s", uniprot_id, exc)

        # Fallback: ESM-2 confidence proxy
        esm_result = await asyncio.to_thread(self._safe_esm2_score, sequence)
        perplexity = esm_result.get("pseudo_perplexity")

        if perplexity is not None:
            fold_conf = max(0.0, min(1.0, 1.0 - (perplexity - 3.0) / 20.0))
            confidence = 0.5  # lower confidence than AlphaFold
        else:
            fold_conf = 0.3
            confidence = 0.1

        return {
            "source": "esm2_proxy",
            "fold_confidence": round(fold_conf, 4),
            "esm2_perplexity": perplexity,
            "esm2_fitness": esm_result.get("fitness_score"),
            "note": "Fold confidence estimated from ESM-2 perplexity; use UniProt ID for AlphaFold pLDDT",
            "confidence": round(confidence, 4),
        }

    # ------------------------------------------------------------------
    # embed
    # ------------------------------------------------------------------

    async def embed(self, sequence: str) -> list[float]:
        """
        Extract ESM-2 mean-pooled embedding (1280-dim).
        """
        self._ensure_tools()

        result = await asyncio.to_thread(self._safe_esm2_embed, sequence)
        return result.get("embedding", [0.0] * 1280)

    # ------------------------------------------------------------------
    # explain
    # ------------------------------------------------------------------

    async def explain(self, sequence: str, property_name: str) -> str:
        """
        Generate a natural language explanation of a protein property.

        Gathers all available data, then uses an LLM to generate an
        interpretable explanation.
        """
        self._ensure_tools()

        # Gather data concurrently
        esm_result, props_result, sol_result, dev_result = await asyncio.gather(
            asyncio.to_thread(self._safe_esm2_score, sequence),
            asyncio.to_thread(self._safe_protein_properties, sequence),
            asyncio.to_thread(self._safe_predict_solubility, sequence),
            asyncio.to_thread(self._safe_predict_developability, sequence),
        )

        # Build context for LLM — include detailed feature data
        sol_features = sol_result.get("features_used", {})
        agg_patches = sol_result.get("aggregation_prone_patches", [])
        risk_flags = dev_result.get("risk_flags", [])
        risk_summary = "; ".join(
            f"{f['type']} ({f['severity']})" for f in risk_flags
        ) if risk_flags else "none"

        aa_comp = props_result.get("amino_acid_composition", {})
        aliphatic_idx = (
            aa_comp.get("A", 0) * 100
            + aa_comp.get("V", 0) * 2.9 * 100
            + aa_comp.get("I", 0) * 3.9 * 100
            + aa_comp.get("L", 0) * 3.9 * 100
        )

        context = (
            f"Protein sequence ({len(sequence)} residues):\n"
            f"First 50 residues: {sequence[:50]}...\n\n"
            f"ESM-2 Analysis:\n"
            f"  Fitness score: {esm_result.get('fitness_score', 'N/A')}\n"
            f"  Pseudo-perplexity: {esm_result.get('pseudo_perplexity', 'N/A')}\n"
            f"  Mean log-likelihood: {esm_result.get('mean_log_likelihood', 'N/A')}\n\n"
            f"Physicochemical Properties:\n"
            f"  MW: {props_result.get('molecular_weight', 'N/A')} Da\n"
            f"  pI: {props_result.get('isoelectric_point', 'N/A')}\n"
            f"  Instability index: {props_result.get('instability_index', 'N/A')} (stable < 40)\n"
            f"  GRAVY: {props_result.get('gravy', 'N/A')} (optimal for globular: -0.4 to +0.2)\n"
            f"  Aromaticity: {props_result.get('aromaticity', 'N/A')}\n"
            f"  Aliphatic index: {aliphatic_idx:.1f} (thermal stability indicator; typical: 60-120)\n"
            f"  Charge at pH 7: {props_result.get('charge_at_pH7', 'N/A')}\n\n"
            f"Solubility Prediction (CamSol-inspired):\n"
            f"  Class: {sol_result.get('solubility_class', 'N/A')}\n"
            f"  Score: {sol_result.get('score', 'N/A')}\n"
            f"  Mean CamSol intrinsic: {sol_features.get('mean_camsol_intrinsic', 'N/A')}\n"
            f"  Aggregation-prone patches: {len(agg_patches)}\n"
            f"  Turn-forming fraction: {sol_features.get('turn_forming_fraction', 'N/A')}\n\n"
            f"Developability Assessment:\n"
            f"  Overall risk: {dev_result.get('overall_risk', 'N/A')}\n"
            f"  Total flags: {dev_result.get('total_flags', 'N/A')}\n"
            f"  Details: {risk_summary}\n"
        )

        prompt = (
            f"You are a protein biochemist. Based on the following analysis data, "
            f"explain the '{property_name}' of this protein in 2-3 paragraphs. "
            f"Be specific about which features drive your assessment and what the "
            f"numbers mean in practical terms.\n\n{context}"
        )

        try:
            from src.utils.llm import call_llm
            explanation = await call_llm(
                prompt=prompt,
                system="You are an expert protein biochemist providing clear, accurate explanations.",
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
            )
            return explanation
        except Exception as exc:
            logger.error("LLM explain failed: %s", exc)
            # Fallback: structured summary without LLM
            return (
                f"Property: {property_name}\n"
                f"ESM-2 fitness: {esm_result.get('fitness_score', 'N/A')}\n"
                f"Stability: {'stable' if props_result.get('instability_index', 50) < 40 else 'unstable'}\n"
                f"Solubility: {sol_result.get('solubility_class', 'N/A')}\n"
                f"Developability risk: {dev_result.get('overall_risk', 'N/A')}\n"
                f"(LLM explanation unavailable: {exc})"
            )

    # ------------------------------------------------------------------
    # compare
    # ------------------------------------------------------------------

    async def compare(self, sequences: list[str], criteria: list[str]) -> dict[str, Any]:
        """
        Compare multiple sequences across specified criteria.

        Scores all sequences, builds a comparison matrix, performs Pareto
        front analysis for multi-objective ranking, and uses an LLM to
        generate an expert analysis.
        """
        self._ensure_tools()

        # Score and assess stability for all sequences concurrently
        scoring_tasks = [self.score(seq) for seq in sequences]
        stability_tasks = [self.stability(seq) for seq in sequences]
        all_results = await asyncio.gather(
            *scoring_tasks, *stability_tasks, return_exceptions=True,
        )

        n = len(sequences)
        scoring_results = all_results[:n]
        stability_results = all_results[n:]

        # Build comparison matrix with full data
        matrix: list[dict[str, Any]] = []
        for i, (seq, score_r, stab_r) in enumerate(zip(sequences, scoring_results, stability_results)):
            if isinstance(score_r, Exception):
                entry = {
                    "index": i,
                    "sequence_preview": seq[:30] + "..." if len(seq) > 30 else seq,
                    "error": str(score_r),
                }
            else:
                stab_score = stab_r.get("stability_score", 0.5) if isinstance(stab_r, dict) else 0.5
                entry = {
                    "index": i,
                    "sequence_preview": seq[:30] + "..." if len(seq) > 30 else seq,
                    "sequence_length": len(seq),
                    "fitness_score": score_r.fitness_score,
                    "stability_score": round(stab_score, 4),
                    "stability_estimate": score_r.stability_estimate,
                    "fold_confidence": score_r.fold_confidence,
                    "expression_prediction": score_r.expression_prediction,
                    "solubility_class": score_r.solubility_class,
                    "confidence": score_r.confidence,
                }
            matrix.append(entry)

        valid_entries = [e for e in matrix if "fitness_score" in e]

        # --- Pareto front analysis ---
        # Objectives: fitness (max), stability (max), fold_confidence (max)
        def _dominates(a: dict, b: dict) -> bool:
            """True if a dominates b (better or equal in all objectives, strictly better in at least one)."""
            objs = ["fitness_score", "stability_score", "fold_confidence"]
            at_least_one_better = False
            for obj in objs:
                va, vb = a.get(obj, 0), b.get(obj, 0)
                if va < vb:
                    return False
                if va > vb:
                    at_least_one_better = True
            return at_least_one_better

        pareto_front = []
        for entry in valid_entries:
            dominated = any(_dominates(other, entry) for other in valid_entries if other is not entry)
            if not dominated:
                pareto_front.append(entry)

        # Rank by composite score (weighted sum for total ordering)
        for e in valid_entries:
            e["composite_rank_score"] = round(
                e.get("fitness_score", 0) * 0.5
                + e.get("stability_score", 0) * 0.3
                + e.get("fold_confidence", 0) * 0.2,
                4,
            )
        ranked = sorted(valid_entries, key=lambda x: x["composite_rank_score"], reverse=True)

        # LLM-generated expert analysis
        analysis = ""
        try:
            from src.utils.llm import call_llm

            matrix_str = "\n".join(
                f"  Seq {e['index']}: fitness={e.get('fitness_score', '?')}, "
                f"stability={e.get('stability_score', '?')} ({e.get('stability_estimate', '?')}), "
                f"fold_conf={e.get('fold_confidence', '?')}, "
                f"solubility={e.get('solubility_class', '?')}, "
                f"expression={e.get('expression_prediction', '?')}"
                for e in matrix
            )
            pareto_str = ", ".join(f"Seq {e['index']}" for e in pareto_front)
            criteria_str = ", ".join(criteria) if criteria else "fitness, stability, fold confidence"

            prompt = (
                f"Compare these {len(sequences)} protein sequences for: {criteria_str}.\n\n"
                f"Scoring results:\n{matrix_str}\n\n"
                f"Pareto-optimal candidates (non-dominated): {pareto_str}\n"
                f"Best composite score: Seq {ranked[0]['index'] if ranked else '?'}\n\n"
                f"Provide:\n"
                f"1. A concise ranking with rationale (2-3 sentences per sequence)\n"
                f"2. Key trade-offs between the top candidates\n"
                f"3. Which candidate to prioritize and why"
            )

            analysis = await call_llm(
                prompt=prompt,
                system="You are a protein engineer comparing candidate sequences. Be quantitative and cite specific scores.",
                model="claude-haiku-4-5-20251001",
            )
        except Exception as exc:
            logger.error("LLM compare analysis failed: %s", exc)
            analysis = f"(LLM analysis unavailable: {exc})"

        return {
            "comparison_matrix": matrix,
            "ranking": [e["index"] for e in ranked],
            "pareto_front": [e["index"] for e in pareto_front],
            "best_candidate": ranked[0] if ranked else None,
            "criteria": criteria,
            "analysis": analysis,
        }

    # ------------------------------------------------------------------
    # Safe wrappers (handle missing tools gracefully)
    # ------------------------------------------------------------------

    def _safe_esm2_score(self, sequence: str) -> dict[str, Any]:
        try:
            self._ensure_tools()
            if self._tools_imported:
                return self._esm2_score_sequence(sequence)
        except Exception as exc:
            logger.warning("esm2_score_sequence failed: %s", exc)
        return {
            "fitness_score": 0.5,
            "pseudo_perplexity": None,
            "overall_confidence": 0.1,
            "warning": "ESM-2 unavailable",
        }

    def _safe_esm2_mutant_effect(self, wildtype: str, mutations: str) -> dict[str, Any]:
        try:
            self._ensure_tools()
            if self._tools_imported:
                return self._esm2_mutant_effect(wildtype, mutations)
        except Exception as exc:
            logger.warning("esm2_mutant_effect failed: %s", exc)
        return {
            "per_mutation_effects": [],
            "overall_delta_ll": 0.0,
            "overall_effect": "unknown",
            "confidence": 0.1,
            "warning": "ESM-2 unavailable",
        }

    def _safe_esm2_embed(self, sequence: str) -> dict[str, Any]:
        try:
            self._ensure_tools()
            if self._tools_imported:
                return self._esm2_embed(sequence)
        except Exception as exc:
            logger.warning("esm2_embed failed: %s", exc)
        return {
            "embedding": [0.0] * 1280,
            "dimensions": 1280,
            "warning": "ESM-2 unavailable; returning zero vector",
        }

    def _safe_protein_properties(self, sequence: str) -> dict[str, Any]:
        try:
            self._ensure_tools()
            if self._tools_imported:
                return self._calculate_protein_properties(sequence)
        except Exception as exc:
            logger.warning("calculate_protein_properties failed: %s", exc)
        return {"error": str(exc), "instability_index": 40.0, "gravy": 0.0}

    def _safe_predict_solubility(self, sequence: str) -> dict[str, Any]:
        try:
            self._ensure_tools()
            if self._tools_imported:
                return self._predict_solubility(sequence)
        except Exception as exc:
            logger.warning("predict_solubility failed: %s", exc)
        return {"solubility_class": "unknown", "score": 0.5}

    def _safe_predict_developability(self, sequence: str) -> dict[str, Any]:
        try:
            self._ensure_tools()
            if self._tools_imported:
                return self._predict_developability(sequence)
        except Exception as exc:
            logger.warning("predict_developability failed: %s", exc)
        return {"overall_risk": "unknown", "risk_flags": [], "total_flags": 0}
