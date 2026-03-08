"""
SV Calling MCP Server — Lumi Virtual Lab

Wraps CLI tools for structural variant detection:
  LUMPY (SV calling) and VCF-based SV filtering (pure Python).

Start with:  python -m src.mcp_servers.sv_calling.server
"""

from __future__ import annotations

import asyncio
import os
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
    "Lumi SV Calling",
    instructions="CLI structural variant tools: LUMPY SV calling and VCF-based SV filtering",
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


def _find_lumpy() -> str | None:
    """Find lumpyexpress or lumpy binary."""
    return shutil.which("lumpyexpress") or shutil.which("lumpy")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def lumpy_call_sv(
    bam_file: str,
    output_file: str | None = None,
    min_weight: int = 4,
) -> dict[str, Any]:
    """
    Call structural variants from a BAM file using LUMPY (via lumpyexpress).

    Args:
        bam_file: Path to the input BAM file (coordinate-sorted, indexed).
        output_file: Optional path for the output VCF file. Defaults to <input>.lumpy.vcf.
        min_weight: Minimum evidence weight to report an SV call.
    """
    try:
        lumpy = _find_lumpy()
        if not lumpy:
            return handle_error("lumpy_call_sv", "lumpyexpress or lumpy binary not found in PATH")

        if not output_file:
            base, _ = os.path.splitext(bam_file)
            output_file = f"{base}.lumpy.vcf"

        cmd = [lumpy, "-B", bam_file, "-o", output_file, "-m", str(min_weight)]

        stdout, stderr, rc = await _run_cmd(cmd, timeout=600.0)

        if rc != 0:
            return handle_error("lumpy_call_sv", f"LUMPY exited with code {rc}: {stderr[:2000]}")

        # Count SV calls and types from VCF
        sv_counts: dict[str, int] = {}
        total_svs = 0
        try:
            with open(output_file) as fh:
                for line in fh:
                    if line.startswith("#"):
                        continue
                    total_svs += 1
                    # Extract SVTYPE from INFO field
                    info_fields = line.split("\t")[7] if len(line.split("\t")) > 7 else ""
                    for field in info_fields.split(";"):
                        if field.startswith("SVTYPE="):
                            sv_type = field.split("=")[1]
                            sv_counts[sv_type] = sv_counts.get(sv_type, 0) + 1
                            break
        except FileNotFoundError:
            pass

        type_summary = ", ".join(f"{k}: {v}" for k, v in sorted(sv_counts.items(), key=lambda x: -x[1]))

        return standard_response(
            summary=f"LUMPY called {total_svs} structural variants from {bam_file}"
            + (f" ({type_summary})" if type_summary else ""),
            raw_data={
                "output_file": output_file,
                "total_svs": total_svs,
                "sv_type_counts": sv_counts,
                "min_weight": min_weight,
                "stderr": stderr[:2000],
            },
            source="LUMPY",
            source_id=bam_file,
            confidence=0.85,
        )
    except Exception as exc:
        return handle_error("lumpy_call_sv", exc)


@mcp.tool()
async def lumpy_filter_sv(
    vcf_file: str,
    min_qual: int = 100,
    sv_type: str | None = None,
) -> dict[str, Any]:
    """
    Filter structural variant calls from a LUMPY VCF output file (pure Python parsing).

    Args:
        vcf_file: Path to the LUMPY VCF output file.
        min_qual: Minimum QUAL score to retain an SV call.
        sv_type: Optional SV type to filter for (e.g. 'DEL', 'DUP', 'INV', 'BND').
    """
    try:
        all_records: list[dict[str, Any]] = []
        filtered_records: list[dict[str, Any]] = []

        with open(vcf_file) as fh:
            for line in fh:
                if line.startswith("#"):
                    continue
                parts = line.strip().split("\t")
                if len(parts) < 8:
                    continue

                chrom = parts[0]
                pos = parts[1]
                sv_id = parts[2]
                qual_str = parts[5]
                info = parts[7]

                # Parse QUAL
                try:
                    qual = float(qual_str) if qual_str != "." else 0.0
                except ValueError:
                    qual = 0.0

                # Parse SVTYPE from INFO
                record_svtype = "unknown"
                svlen = "N/A"
                for field in info.split(";"):
                    if field.startswith("SVTYPE="):
                        record_svtype = field.split("=")[1]
                    elif field.startswith("SVLEN="):
                        svlen = field.split("=")[1]

                record = {
                    "chrom": chrom,
                    "pos": pos,
                    "id": sv_id,
                    "qual": qual,
                    "svtype": record_svtype,
                    "svlen": svlen,
                }
                all_records.append(record)

                # Apply filters
                if qual < min_qual:
                    continue
                if sv_type and record_svtype != sv_type:
                    continue
                filtered_records.append(record)

        # Summarize filtered SV types
        filtered_types: dict[str, int] = {}
        for rec in filtered_records:
            t = rec["svtype"]
            filtered_types[t] = filtered_types.get(t, 0) + 1

        type_summary = ", ".join(f"{k}: {v}" for k, v in sorted(filtered_types.items(), key=lambda x: -x[1]))

        return standard_response(
            summary=f"Filtered {len(filtered_records)}/{len(all_records)} SVs from {vcf_file} "
            f"(min_qual={min_qual}"
            + (f", sv_type={sv_type}" if sv_type else "")
            + f"): {type_summary}",
            raw_data={
                "total_records": len(all_records),
                "filtered_records": len(filtered_records),
                "sv_type_counts": filtered_types,
                "variants": filtered_records[:100],
                "filters": {"min_qual": min_qual, "sv_type": sv_type},
            },
            source="LUMPY (filtered)",
            source_id=vcf_file,
            confidence=0.90,
        )
    except FileNotFoundError:
        return handle_error("lumpy_filter_sv", f"VCF file not found: {vcf_file}")
    except Exception as exc:
        return handle_error("lumpy_filter_sv", exc)


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
