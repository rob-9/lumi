"""
GWAS CLI MCP Server — Lumi Virtual Lab

Wraps CLI tools for genome-wide association studies:
  PLINK (association, LD, PCA, clumping) and GCTA (GREML, COJO).

Start with:  python -m src.mcp_servers.gwas_cli.server
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
    "Lumi GWAS CLI",
    instructions="CLI GWAS tools: PLINK association/LD/PCA/clumping, GCTA GREML/COJO",
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


def _find_plink() -> str | None:
    """Find plink2 or plink binary."""
    return shutil.which("plink2") or shutil.which("plink")


def _find_gcta() -> str | None:
    """Find gcta64 or gcta binary."""
    return shutil.which("gcta64") or shutil.which("gcta")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def plink_assoc(
    bfile: str,
    pheno: str | None = None,
    covar: str | None = None,
    out: str = "plink_output",
) -> dict[str, Any]:
    """
    Run PLINK association analysis (logistic/linear).

    Args:
        bfile: Path prefix for PLINK binary fileset (.bed/.bim/.fam).
        pheno: Optional path to phenotype file.
        covar: Optional path to covariate file.
        out: Output file prefix.
    """
    try:
        plink = _find_plink()
        if not plink:
            return handle_error("plink_assoc", "plink2/plink binary not found in PATH")

        cmd = [plink, "--bfile", bfile, "--assoc", "--out", out]
        if pheno:
            cmd.extend(["--pheno", pheno])
        if covar:
            cmd.extend(["--covar", covar])

        stdout, stderr, rc = await _run_cmd(cmd, timeout=300.0)

        if rc != 0:
            return handle_error("plink_assoc", f"PLINK exited with code {rc}: {stderr[:2000]}")

        summary = f"PLINK association analysis completed on {bfile}. Output prefix: {out}"

        return standard_response(
            summary=summary,
            raw_data={"output_prefix": out, "stdout": stdout[:2000], "stderr": stderr[:2000]},
            source="PLINK",
            source_id=bfile,
            confidence=0.85,
        )
    except Exception as exc:
        return handle_error("plink_assoc", exc)


@mcp.tool()
async def plink_ld(
    bfile: str,
    snps: str,
    ld_window_kb: int = 1000,
) -> dict[str, Any]:
    """
    Calculate linkage disequilibrium between SNPs using PLINK.

    Args:
        bfile: Path prefix for PLINK binary fileset.
        snps: Comma-separated list of SNP IDs (e.g. 'rs123,rs456').
        ld_window_kb: LD window in kilobases.
    """
    try:
        plink = _find_plink()
        if not plink:
            return handle_error("plink_ld", "plink2/plink binary not found in PATH")

        cmd = [
            plink, "--bfile", bfile,
            "--ld-snp-list", snps,
            "--ld-window-kb", str(ld_window_kb),
            "--r2",
            "--out", "plink_ld_output",
        ]

        stdout, stderr, rc = await _run_cmd(cmd, timeout=300.0)

        if rc != 0:
            return handle_error("plink_ld", f"PLINK LD exited with code {rc}: {stderr[:2000]}")

        summary = f"PLINK LD calculation completed for SNPs: {snps} (window: {ld_window_kb}kb)"

        return standard_response(
            summary=summary,
            raw_data={"snps": snps, "ld_window_kb": ld_window_kb, "stdout": stdout[:2000], "stderr": stderr[:2000]},
            source="PLINK",
            source_id=bfile,
            confidence=0.85,
        )
    except Exception as exc:
        return handle_error("plink_ld", exc)


@mcp.tool()
async def plink_pca(
    bfile: str,
    n_pcs: int = 10,
    out: str = "plink_pca",
) -> dict[str, Any]:
    """
    Run principal component analysis using PLINK.

    Args:
        bfile: Path prefix for PLINK binary fileset.
        n_pcs: Number of principal components to compute.
        out: Output file prefix.
    """
    try:
        plink = _find_plink()
        if not plink:
            return handle_error("plink_pca", "plink2/plink binary not found in PATH")

        cmd = [plink, "--bfile", bfile, "--pca", str(n_pcs), "--out", out]

        stdout, stderr, rc = await _run_cmd(cmd, timeout=600.0)

        if rc != 0:
            return handle_error("plink_pca", f"PLINK PCA exited with code {rc}: {stderr[:2000]}")

        summary = f"PLINK PCA completed on {bfile}: {n_pcs} PCs computed. Output prefix: {out}"

        return standard_response(
            summary=summary,
            raw_data={"output_prefix": out, "n_pcs": n_pcs, "stdout": stdout[:2000], "stderr": stderr[:2000]},
            source="PLINK",
            source_id=bfile,
            confidence=0.85,
        )
    except Exception as exc:
        return handle_error("plink_pca", exc)


@mcp.tool()
async def plink_clump(
    bfile: str,
    assoc_file: str,
    p1: float = 5e-8,
    p2: float = 1e-5,
    r2: float = 0.1,
) -> dict[str, Any]:
    """
    Clump GWAS results to identify independent significant loci using PLINK.

    Args:
        bfile: Path prefix for PLINK binary fileset.
        assoc_file: Path to association results file.
        p1: Significance threshold for index SNPs.
        p2: Significance threshold for clumped SNPs.
        r2: LD threshold for clumping.
    """
    try:
        plink = _find_plink()
        if not plink:
            return handle_error("plink_clump", "plink2/plink binary not found in PATH")

        cmd = [
            plink, "--bfile", bfile,
            "--clump", assoc_file,
            "--clump-p1", str(p1),
            "--clump-p2", str(p2),
            "--clump-r2", str(r2),
            "--out", "plink_clump_output",
        ]

        stdout, stderr, rc = await _run_cmd(cmd, timeout=300.0)

        if rc != 0:
            return handle_error("plink_clump", f"PLINK clump exited with code {rc}: {stderr[:2000]}")

        summary = f"PLINK clumping completed on {assoc_file} (p1={p1}, p2={p2}, r2={r2})"

        return standard_response(
            summary=summary,
            raw_data={
                "assoc_file": assoc_file,
                "p1": p1,
                "p2": p2,
                "r2": r2,
                "stdout": stdout[:2000],
                "stderr": stderr[:2000],
            },
            source="PLINK",
            source_id=bfile,
            confidence=0.85,
        )
    except Exception as exc:
        return handle_error("plink_clump", exc)


@mcp.tool()
async def gcta_greml(
    grm: str,
    pheno: str,
    out: str = "gcta_greml",
) -> dict[str, Any]:
    """
    Estimate SNP heritability using GCTA GREML.

    Args:
        grm: Path prefix for genetic relationship matrix (GRM) files.
        pheno: Path to phenotype file.
        out: Output file prefix.
    """
    try:
        gcta = _find_gcta()
        if not gcta:
            return handle_error("gcta_greml", "gcta64/gcta binary not found in PATH")

        cmd = [
            gcta, "--grm", grm,
            "--pheno", pheno,
            "--reml",
            "--out", out,
        ]

        stdout, stderr, rc = await _run_cmd(cmd, timeout=600.0)

        if rc != 0:
            return handle_error("gcta_greml", f"GCTA GREML exited with code {rc}: {stderr[:2000]}")

        # Try to parse heritability from output
        h2_info: dict[str, Any] = {}
        for line in stdout.split("\n"):
            if "V(G)/Vp" in line:
                parts = line.strip().split()
                if len(parts) >= 2:
                    h2_info["h2"] = parts[-2] if len(parts) >= 3 else parts[-1]
                    if len(parts) >= 3:
                        h2_info["se"] = parts[-1]

        summary = f"GCTA GREML heritability estimation completed. Output prefix: {out}"
        if h2_info:
            summary += f". h2={h2_info.get('h2', 'N/A')} (SE={h2_info.get('se', 'N/A')})"

        return standard_response(
            summary=summary,
            raw_data={
                "output_prefix": out,
                "heritability": h2_info,
                "stdout": stdout[:2000],
                "stderr": stderr[:2000],
            },
            source="GCTA GREML",
            source_id=grm,
            confidence=0.85,
        )
    except Exception as exc:
        return handle_error("gcta_greml", exc)


@mcp.tool()
async def gcta_cojo(
    bfile: str,
    assoc_file: str,
    p: float = 5e-8,
    out: str = "gcta_cojo",
) -> dict[str, Any]:
    """
    Run GCTA COJO (conditional and joint) analysis for GWAS loci.

    Args:
        bfile: Path prefix for PLINK binary fileset (used as LD reference).
        assoc_file: Path to GWAS summary statistics file.
        p: P-value threshold for selecting SNPs.
        out: Output file prefix.
    """
    try:
        gcta = _find_gcta()
        if not gcta:
            return handle_error("gcta_cojo", "gcta64/gcta binary not found in PATH")

        cmd = [
            gcta, "--bfile", bfile,
            "--cojo-file", assoc_file,
            "--cojo-slct",
            "--cojo-p", str(p),
            "--out", out,
        ]

        stdout, stderr, rc = await _run_cmd(cmd, timeout=600.0)

        if rc != 0:
            return handle_error("gcta_cojo", f"GCTA COJO exited with code {rc}: {stderr[:2000]}")

        summary = f"GCTA COJO analysis completed on {assoc_file} (p threshold={p}). Output prefix: {out}"

        return standard_response(
            summary=summary,
            raw_data={
                "output_prefix": out,
                "p_threshold": p,
                "stdout": stdout[:2000],
                "stderr": stderr[:2000],
            },
            source="GCTA COJO",
            source_id=bfile,
            confidence=0.85,
        )
    except Exception as exc:
        return handle_error("gcta_cojo", exc)


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
