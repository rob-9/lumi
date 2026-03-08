"""
miRTarBase MCP Server — Lumi Virtual Lab

Exposes tools for querying miRTarBase microRNA-target interaction data:
  miRNA target lookup, gene-miRNA search, and validated interaction
  retrieval with evidence types.

Uses the miRTarBase API at https://mirtarbase.cuhk.edu.cn/~miRTarBase/miRTarBase_2022/php/api.

Start with:  python -m src.mcp_servers.mirtarbase.server
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

try:
    from src.mcp_servers.base import async_http_get, handle_error, standard_response
except ImportError:
    from mcp_servers.base import async_http_get, handle_error, standard_response  # type: ignore[no-redef]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIRTARBASE_API = "https://mirtarbase.cuhk.edu.cn/~miRTarBase/miRTarBase_2022/php/api"

mcp = FastMCP("lumi-mirtarbase")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def mirtarbase_get_targets(
    mirna_id: str,
    species: str = "Homo sapiens",
    strong_evidence_only: bool = False,
) -> dict[str, Any]:
    """Get validated gene targets for a microRNA from miRTarBase.

    Args:
        mirna_id: miRNA ID (e.g. hsa-miR-21-5p, hsa-let-7a-5p).
        species: Species name (default 'Homo sapiens').
        strong_evidence_only: If True, only return strong evidence (Reporter Assay, Western Blot, qPCR).
    """
    try:
        url = f"{MIRTARBASE_API}/getTargetGene"
        params: dict[str, str] = {"mirna": mirna_id, "species": species}
        if strong_evidence_only:
            params["support_type"] = "Functional MTI"
        data = await async_http_get(url, params=params)
        targets = data if isinstance(data, list) else data.get("targets", data.get("results", []))
        count = len(targets) if isinstance(targets, list) else 0
        ev_str = " (strong evidence only)" if strong_evidence_only else ""
        return standard_response(
            summary=f"Found {count} validated target gene(s) for {mirna_id}{ev_str}",
            raw_data={"targets": targets},
            source="miRTarBase",
            source_id=f"mirna:{mirna_id}",
        )
    except Exception as exc:
        return handle_error("mirtarbase_get_targets", exc)


@mcp.tool()
async def mirtarbase_gene_mirnas(
    gene_symbol: str,
    species: str = "Homo sapiens",
) -> dict[str, Any]:
    """Get validated miRNAs that target a specific gene.

    Args:
        gene_symbol: Gene symbol (e.g. TP53, BRCA1).
        species: Species name (default 'Homo sapiens').
    """
    try:
        url = f"{MIRTARBASE_API}/getMiRNA"
        params = {"target": gene_symbol, "species": species}
        data = await async_http_get(url, params=params)
        mirnas = data if isinstance(data, list) else data.get("mirnas", data.get("results", []))
        count = len(mirnas) if isinstance(mirnas, list) else 0
        return standard_response(
            summary=f"Found {count} miRNA(s) targeting {gene_symbol}",
            raw_data={"mirnas": mirnas},
            source="miRTarBase",
            source_id=f"gene:{gene_symbol}",
        )
    except Exception as exc:
        return handle_error("mirtarbase_gene_mirnas", exc)


@mcp.tool()
async def mirtarbase_get_interaction(
    mirtarbase_id: str,
) -> dict[str, Any]:
    """Get detailed interaction record by miRTarBase ID.

    Args:
        mirtarbase_id: miRTarBase interaction ID (e.g. MIRT000002).
    """
    try:
        url = f"{MIRTARBASE_API}/getDetail"
        params = {"mirtarbase_id": mirtarbase_id}
        data = await async_http_get(url, params=params)
        return standard_response(
            summary=f"miRTarBase interaction {mirtarbase_id}",
            raw_data=data,
            source="miRTarBase",
            source_id=mirtarbase_id,
        )
    except Exception as exc:
        return handle_error("mirtarbase_get_interaction", exc)


if __name__ == "__main__":
    mcp.run()
