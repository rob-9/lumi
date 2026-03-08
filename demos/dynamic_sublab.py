"""
Demo: Dynamic SubLab Pipeline — Lumi Virtual Lab

Runs a target validation analysis using the dynamic SubLab mode, where
the orchestrator sees all tools and composes a query-specific agent team
instead of routing through the static 17-agent / 8-division roster.

Usage:
    python -m demos.dynamic_sublab
    python -m demos.dynamic_sublab --target BRCA1 --disease "breast cancer"
    python -m demos.dynamic_sublab --target PCSK9 --disease hypercholesterolemia

    # With a sublab hint to steer team composition:
    python -m demos.dynamic_sublab --target KRAS --disease "pancreatic cancer" \
        --hint "Focus on structural biology and small molecule druggability"

    # Dry-run: just show the tool catalog and planned team, no LLM execution:
    python -m demos.dynamic_sublab --dry-run

Requirements:
    - ANTHROPIC_API_KEY set in the environment (or in .env)
    - Project dependencies installed (see pyproject.toml)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_query(target: str, disease: str) -> str:
    return (
        f"Evaluate {target} as a therapeutic target for {disease}. "
        f"Assess genetic evidence, expression patterns, safety profile, "
        f"existing drugs, and clinical trial landscape."
    )


def _print_section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def _show_catalog() -> None:
    """Print the tool catalog summary (no LLM call needed)."""
    from src.mcp_bridge import build_tool_catalog

    catalog = build_tool_catalog()

    _print_section(f"Tool Catalog: {len(catalog)} tools")

    domains: dict[str, list[str]] = {}
    for td in catalog:
        domains.setdefault(td["domain"], []).append(td["name"])

    for domain in sorted(domains):
        tools = domains[domain]
        print(f"\n  [{domain}] ({len(tools)} tools)")
        for t in tools:
            print(f"    - {t}")

    print(f"\nTotal: {len(catalog)} tools across {len(domains)} domains")

    # Show the prompt text size
    from src.mcp_bridge import get_catalog_prompt_text
    text = get_catalog_prompt_text()
    print(f"Catalog prompt text: {len(text)} chars (~{len(text) // 4} tokens)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(
    target: str,
    disease: str,
    hint: str | None = None,
    cost_ceiling: float = 50.0,
    dry_run: bool = False,
) -> object | None:
    """Run a dynamic SubLab analysis.

    Parameters
    ----------
    target:
        Gene or protein target name.
    disease:
        Disease or indication.
    hint:
        Optional sublab hint to steer team composition.
    cost_ceiling:
        Maximum spend in USD.
    dry_run:
        If True, only show the tool catalog — no LLM calls.
    """
    # --- logging setup ---
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("demo.dynamic_sublab")

    if dry_run:
        logger.info("DRY RUN — showing tool catalog only")
        _show_catalog()
        return None

    query = _build_query(target, disease)

    logger.info("=" * 70)
    logger.info("LUMI VIRTUAL LAB — Dynamic SubLab Demo")
    logger.info("=" * 70)
    logger.info("Target:        %s", target)
    logger.info("Disease:       %s", disease)
    logger.info("Mode:          DYNAMIC (SubLab)")
    logger.info("SubLab hint:   %s", hint or "(none)")
    logger.info("Cost ceiling:  $%.2f", cost_ceiling)
    logger.info("Query:         %s", query)
    logger.info("=" * 70)

    # --- run the pipeline in dynamic mode ---
    from src.orchestrator.pipeline import run_yohas_pipeline

    t0 = time.time()
    report = await run_yohas_pipeline(
        user_query=query,
        dynamic=True,
        sublab_hint=hint,
        cost_ceiling=cost_ceiling,
        enable_world_model=True,
    )
    elapsed = time.time() - t0

    # --- print results ---
    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print("=" * 70)
    print(f"\nQuery ID:  {report.query_id}")
    print(f"Duration:  {elapsed:.1f}s")
    print(f"Cost:      ${report.total_cost:.4f}")

    _print_section("Executive Summary")
    print(report.executive_summary or "(no summary)")

    if report.key_findings:
        _print_section(f"Key Findings ({len(report.key_findings)})")
        for i, finding in enumerate(report.key_findings[:10], 1):
            conf = finding.confidence.level.value
            print(f"  {i}. [{conf}] {finding.claim_text[:120]}")

    if report.risk_assessment:
        _print_section("Risk Assessment")
        for key, val in report.risk_assessment.items():
            val_str = str(val)[:200]
            print(f"  {key}: {val_str}")

    if report.limitations:
        _print_section("Limitations")
        for lim in report.limitations[:5]:
            print(f"  - {lim}")

    # --- persist full report ---
    output_dir = os.path.join(_PROJECT_ROOT, "data", "reports")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{report.query_id}_dynamic.json")
    with open(output_path, "w") as fh:
        json.dump(report.model_dump(mode="json"), fh, indent=2, default=str)
    print(f"\nFull report saved to: {output_path}")

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Lumi Virtual Lab — Dynamic SubLab Demo",
    )
    parser.add_argument(
        "--target", default="BRCA1", help="Gene/protein target (default: BRCA1)",
    )
    parser.add_argument(
        "--disease", default="breast cancer",
        help='Disease or indication (default: "breast cancer")',
    )
    parser.add_argument(
        "--hint", default=None,
        help="Optional sublab hint to steer team composition",
    )
    parser.add_argument(
        "--cost-ceiling", type=float, default=50.0,
        help="Maximum spend in USD (default: 50.0)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Just show the tool catalog, no LLM calls",
    )
    args = parser.parse_args()

    asyncio.run(main(
        args.target,
        args.disease,
        hint=args.hint,
        cost_ceiling=args.cost_ceiling,
        dry_run=args.dry_run,
    ))
