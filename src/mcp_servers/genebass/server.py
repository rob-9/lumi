"""
Genebass MCP Server — Lumi Virtual Lab

Exposes tools for querying Genebass exome-based gene-phenotype associations
from the UK Biobank exome sequencing analysis.

Uses the Genebass API at https://genebass.org/api.

Start with:  python -m src.mcp_servers.genebass.server
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

GENEBASS_API = "https://genebass.org/api/v1"

mcp = FastMCP("lumi-genebass")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def genebass_gene_associations(
    gene_symbol: str,
    p_threshold: float = 5e-8,
    max_results: int = 50,
) -> dict[str, Any]:
    """Get exome-based phenotype associations for a gene from Genebass.

    Args:
        gene_symbol: Gene symbol (e.g. PCSK9, APOB).
        p_threshold: P-value threshold for significance.
        max_results: Maximum associations to return.
    """
    try:
        url = f"{GENEBASS_API}/gene/{gene_symbol}/associations"
        params = {"p_threshold": str(p_threshold), "limit": str(max_results)}
        data = await async_http_get(url, params=params)
        results = data if isinstance(data, list) else data.get("associations", data.get("results", []))
        count = len(results) if isinstance(results, list) else 0
        return standard_response(
            summary=f"Found {count} Genebass association(s) for {gene_symbol} (p < {p_threshold})",
            raw_data={"associations": results},
            source="Genebass",
            source_id=f"gene:{gene_symbol}",
        )
    except Exception as exc:
        return handle_error("genebass_gene_associations", exc)


@mcp.tool()
async def genebass_phenotype_genes(
    phenotype_code: str,
    annotation: str = "pLoF",
    max_results: int = 50,
) -> dict[str, Any]:
    """Get gene-level association results for a phenotype from Genebass.

    Args:
        phenotype_code: Phenotype code (e.g. 'I25' for chronic ischaemic heart disease).
        annotation: Variant annotation type: 'pLoF', 'missense', 'synonymous'.
        max_results: Maximum genes to return.
    """
    try:
        url = f"{GENEBASS_API}/phenotype/{phenotype_code}/genes"
        params = {"annotation": annotation, "limit": str(max_results)}
        data = await async_http_get(url, params=params)
        results = data if isinstance(data, list) else data.get("genes", data.get("results", []))
        count = len(results) if isinstance(results, list) else 0
        return standard_response(
            summary=f"Found {count} gene(s) associated with phenotype {phenotype_code} ({annotation})",
            raw_data={"genes": results},
            source="Genebass",
            source_id=f"phenotype:{phenotype_code}",
        )
    except Exception as exc:
        return handle_error("genebass_phenotype_genes", exc)


@mcp.tool()
async def genebass_search_phenotypes(
    query: str,
    max_results: int = 25,
) -> dict[str, Any]:
    """Search Genebass for available phenotypes by keyword."""
    try:
        url = f"{GENEBASS_API}/phenotypes/search"
        params = {"q": query, "limit": str(max_results)}
        data = await async_http_get(url, params=params)
        results = data if isinstance(data, list) else data.get("phenotypes", data.get("results", []))
        count = len(results) if isinstance(results, list) else 0
        return standard_response(
            summary=f"Found {count} Genebass phenotype(s) matching '{query}'",
            raw_data={"phenotypes": results},
            source="Genebass",
            source_id=f"search:{query}",
        )
    except Exception as exc:
        return handle_error("genebass_search_phenotypes", exc)


if __name__ == "__main__":
    mcp.run()
