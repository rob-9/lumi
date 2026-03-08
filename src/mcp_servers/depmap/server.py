"""
DepMap (Cancer Dependency Map) MCP Server — Lumi Virtual Lab

Exposes tools for querying the Broad DepMap portal:
  gene dependency scores (CRISPR/RNAi), cell line info, gene expression,
  and mutation data across cancer cell lines.

Uses the DepMap portal API at https://depmap.org/portal/api.

Start with:  python -m src.mcp_servers.depmap.server
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

DEPMAP_API = "https://depmap.org/portal/api"

mcp = FastMCP("lumi-depmap")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def depmap_gene_dependency(
    gene_symbol: str,
    dataset: str = "Chronos_Combined",
) -> dict[str, Any]:
    """Get CRISPR dependency scores for a gene across cancer cell lines.

    Args:
        gene_symbol: Gene symbol (e.g. KRAS, EGFR).
        dataset: Dependency dataset to query. Default 'Chronos_Combined'.
    """
    try:
        url = f"{DEPMAP_API}/download/data_slicer"
        params = {
            "features": gene_symbol,
            "dataset_id": dataset,
            "format": "json",
        }
        data = await async_http_get(url, params=params)
        return standard_response(
            summary=f"DepMap dependency scores for {gene_symbol} ({dataset})",
            raw_data=data,
            source="DepMap",
            source_id=f"dependency:{gene_symbol}",
        )
    except Exception as exc:
        return handle_error("depmap_gene_dependency", exc)


@mcp.tool()
async def depmap_search_cell_lines(
    query: str,
    lineage: str | None = None,
) -> dict[str, Any]:
    """Search DepMap for cancer cell lines by name or lineage.

    Args:
        query: Cell line name or keyword (e.g. 'MCF7', 'lung').
        lineage: Optional lineage filter (e.g. 'lung', 'breast', 'blood').
    """
    try:
        url = f"{DEPMAP_API}/cell_line"
        params: dict[str, str] = {"q": query}
        if lineage:
            params["lineage"] = lineage
        data = await async_http_get(url, params=params)
        results = data if isinstance(data, list) else data.get("cell_lines", [])
        count = len(results) if isinstance(results, list) else 0
        return standard_response(
            summary=f"Found {count} DepMap cell line(s) matching '{query}'",
            raw_data={"cell_lines": results},
            source="DepMap",
            source_id=f"cell_line:{query}",
        )
    except Exception as exc:
        return handle_error("depmap_search_cell_lines", exc)


@mcp.tool()
async def depmap_gene_expression(
    gene_symbol: str,
    dataset: str = "Expression_Public",
) -> dict[str, Any]:
    """Get gene expression (TPM) across DepMap cell lines.

    Args:
        gene_symbol: Gene symbol (e.g. TP53).
        dataset: Expression dataset ID.
    """
    try:
        url = f"{DEPMAP_API}/download/data_slicer"
        params = {
            "features": gene_symbol,
            "dataset_id": dataset,
            "format": "json",
        }
        data = await async_http_get(url, params=params)
        return standard_response(
            summary=f"DepMap expression data for {gene_symbol}",
            raw_data=data,
            source="DepMap",
            source_id=f"expression:{gene_symbol}",
        )
    except Exception as exc:
        return handle_error("depmap_gene_expression", exc)


@mcp.tool()
async def depmap_gene_mutations(
    gene_symbol: str,
) -> dict[str, Any]:
    """Get mutation data for a gene across DepMap cell lines.

    Args:
        gene_symbol: Gene symbol (e.g. BRAF, PIK3CA).
    """
    try:
        url = f"{DEPMAP_API}/download/data_slicer"
        params = {
            "features": gene_symbol,
            "dataset_id": "Mutations_Public",
            "format": "json",
        }
        data = await async_http_get(url, params=params)
        return standard_response(
            summary=f"DepMap mutation data for {gene_symbol}",
            raw_data=data,
            source="DepMap",
            source_id=f"mutation:{gene_symbol}",
        )
    except Exception as exc:
        return handle_error("depmap_gene_mutations", exc)


if __name__ == "__main__":
    mcp.run()
