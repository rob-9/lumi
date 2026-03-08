"""
Phylogenetics MCP Server — Lumi Virtual Lab

Wraps CLI tools for phylogenetic analysis:
  MUSCLE (alignment), FastTree (approximate ML), IQ-TREE (ML tree + model selection).

Start with:  python -m src.mcp_servers.phylogenetics.server
"""

from __future__ import annotations

import asyncio
import shutil
from typing import Any

from fastmcp import FastMCP

try:
    from src.mcp_servers.base import handle_error, standard_response
except ImportError:
    from mcp_servers.base import handle_error, standard_response  # type: ignore[no-redef]

# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "Lumi Phylogenetics",
    instructions="CLI phylogenetics tools: MUSCLE alignment, FastTree, IQ-TREE tree building and model selection",
)


# ---------------------------------------------------------------------------
# Subprocess helper
# ---------------------------------------------------------------------------

async def _run_cmd(cmd: list[str], timeout: float = 120.0) -> tuple[str, str, int]:
    """Run a command and return (stdout, stderr, returncode)."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise TimeoutError(f"Command timed out after {timeout}s: {' '.join(cmd)}")
    return stdout.decode(), stderr.decode(), proc.returncode


def _find_fasttree() -> str | None:
    """Find FastTree or fasttree binary."""
    return shutil.which("FastTree") or shutil.which("fasttree")


def _find_iqtree() -> str | None:
    """Find iqtree2 or iqtree binary."""
    return shutil.which("iqtree2") or shutil.which("iqtree")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def muscle_align(
    input_fasta: str,
    output_file: str | None = None,
) -> dict[str, Any]:
    """
    Run MUSCLE multiple sequence alignment on a FASTA file.

    Args:
        input_fasta: Path to input FASTA file with unaligned sequences.
        output_file: Optional path for aligned output FASTA. Defaults to '<input>.aligned.fasta'.
    """
    try:
        if not shutil.which("muscle"):
            return handle_error("muscle_align", "muscle binary not found in PATH")

        if not output_file:
            output_file = f"{input_fasta}.aligned.fasta"

        cmd = ["muscle", "-in", input_fasta, "-out", output_file]
        stdout, stderr, rc = await _run_cmd(cmd, timeout=600.0)

        if rc != 0:
            return handle_error("muscle_align", f"MUSCLE exited with code {rc}: {stderr[:2000]}")

        # Count sequences in output
        seq_count = 0
        try:
            with open(output_file) as f:
                for line in f:
                    if line.startswith(">"):
                        seq_count += 1
        except FileNotFoundError:
            pass

        summary = f"MUSCLE alignment completed: {seq_count} sequences aligned. Output: {output_file}"

        return standard_response(
            summary=summary,
            raw_data={
                "output_file": output_file,
                "sequence_count": seq_count,
                "stderr": stderr[:2000],
            },
            source="MUSCLE",
            source_id=input_fasta,
            confidence=0.9,
        )
    except Exception as exc:
        return handle_error("muscle_align", exc)


@mcp.tool()
async def fasttree_build(
    alignment_file: str,
    output_file: str | None = None,
    model: str = "lg",
) -> dict[str, Any]:
    """
    Build an approximate maximum-likelihood phylogenetic tree with FastTree.

    Args:
        alignment_file: Path to aligned FASTA or PHYLIP file.
        output_file: Optional output Newick tree file. Defaults to '<input>.tree'.
        model: Substitution model — 'lg' (protein) or 'gtr' (nucleotide).
    """
    try:
        fasttree = _find_fasttree()
        if not fasttree:
            return handle_error("fasttree_build", "FastTree/fasttree binary not found in PATH")

        if not output_file:
            output_file = f"{alignment_file}.tree"

        cmd = [fasttree]
        if model.lower() == "gtr":
            cmd.extend(["-gtr", "-nt"])
        else:
            cmd.append("-lg")
        cmd.append(alignment_file)

        stdout, stderr, rc = await _run_cmd(cmd, timeout=600.0)

        if rc != 0:
            return handle_error("fasttree_build", f"FastTree exited with code {rc}: {stderr[:2000]}")

        # stdout is the Newick tree
        with open(output_file, "w") as f:
            f.write(stdout)

        # Extract log-likelihood from stderr if available
        log_likelihood = None
        for line in stderr.split("\n"):
            if "Gamma20" in line or "LogLk" in line or "lnLk" in line:
                log_likelihood = line.strip()
                break

        summary = f"FastTree built phylogeny from {alignment_file} (model: {model}). Output: {output_file}"
        if log_likelihood:
            summary += f". {log_likelihood}"

        return standard_response(
            summary=summary,
            raw_data={
                "output_file": output_file,
                "model": model,
                "newick_head": stdout[:500],
                "log_likelihood_line": log_likelihood,
                "stderr_tail": stderr[-2000:],
            },
            source="FastTree",
            source_id=alignment_file,
            confidence=0.85,
        )
    except Exception as exc:
        return handle_error("fasttree_build", exc)


@mcp.tool()
async def iqtree_build(
    alignment_file: str,
    model: str = "TEST",
    bootstrap: int = 1000,
    output_prefix: str | None = None,
) -> dict[str, Any]:
    """
    Build a maximum-likelihood phylogenetic tree with IQ-TREE.

    Args:
        alignment_file: Path to aligned FASTA or PHYLIP file.
        model: Substitution model or 'TEST' for automatic model selection.
        bootstrap: Number of ultrafast bootstrap replicates.
        output_prefix: Optional output file prefix.
    """
    try:
        iqtree = _find_iqtree()
        if not iqtree:
            return handle_error("iqtree_build", "iqtree2/iqtree binary not found in PATH")

        cmd = [
            iqtree, "-s", alignment_file,
            "-m", model,
            "-bb", str(bootstrap),
            "--redo",
        ]
        if output_prefix:
            cmd.extend(["--prefix", output_prefix])

        stdout, stderr, rc = await _run_cmd(cmd, timeout=1200.0)

        if rc != 0:
            return handle_error("iqtree_build", f"IQ-TREE exited with code {rc}: {stderr[:2000]}")

        # Parse key results from stdout
        best_model = None
        log_likelihood = None
        for line in stdout.split("\n"):
            if "Best-fit model:" in line:
                best_model = line.split(":")[-1].strip()
            if "Log-likelihood of the tree:" in line:
                log_likelihood = line.split(":")[-1].strip()

        prefix = output_prefix or alignment_file
        summary = f"IQ-TREE analysis completed on {alignment_file}"
        if best_model:
            summary += f". Best model: {best_model}"
        if log_likelihood:
            summary += f". Log-likelihood: {log_likelihood}"
        summary += f". Bootstrap: {bootstrap} UFBoot replicates"

        return standard_response(
            summary=summary,
            raw_data={
                "output_prefix": prefix,
                "best_model": best_model,
                "log_likelihood": log_likelihood,
                "bootstrap": bootstrap,
                "tree_file": f"{prefix}.treefile",
                "stdout_tail": stdout[-2000:],
                "stderr_tail": stderr[-2000:],
            },
            source="IQ-TREE",
            source_id=alignment_file,
            confidence=0.85,
        )
    except Exception as exc:
        return handle_error("iqtree_build", exc)


@mcp.tool()
async def iqtree_model_test(
    alignment_file: str,
    output_prefix: str | None = None,
) -> dict[str, Any]:
    """
    Run IQ-TREE model selection (ModelFinder) to find the best substitution model.

    Args:
        alignment_file: Path to aligned FASTA or PHYLIP file.
        output_prefix: Optional output file prefix.
    """
    try:
        iqtree = _find_iqtree()
        if not iqtree:
            return handle_error("iqtree_model_test", "iqtree2/iqtree binary not found in PATH")

        cmd = [
            iqtree, "-s", alignment_file,
            "-m", "TESTONLY",
            "--redo",
        ]
        if output_prefix:
            cmd.extend(["--prefix", output_prefix])

        stdout, stderr, rc = await _run_cmd(cmd, timeout=600.0)

        if rc != 0:
            return handle_error("iqtree_model_test", f"IQ-TREE model test exited with code {rc}: {stderr[:2000]}")

        # Parse best model
        best_model = None
        bic_score = None
        for line in stdout.split("\n"):
            if "Best-fit model:" in line:
                best_model = line.split(":")[-1].strip()
            if "Bayesian information criterion" in line.lower() or "BIC" in line:
                bic_score = line.strip()

        summary = f"IQ-TREE model selection completed on {alignment_file}"
        if best_model:
            summary += f". Best-fit model: {best_model}"

        return standard_response(
            summary=summary,
            raw_data={
                "best_model": best_model,
                "bic_info": bic_score,
                "stdout_tail": stdout[-2000:],
                "stderr_tail": stderr[-2000:],
            },
            source="IQ-TREE ModelFinder",
            source_id=alignment_file,
            confidence=0.85,
        )
    except Exception as exc:
        return handle_error("iqtree_model_test", exc)


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
