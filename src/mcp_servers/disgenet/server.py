"""
DisGeNET MCP Server — Lumi Virtual Lab

Exposes tools for querying DisGeNET gene-disease association data:
  gene-disease associations, variant-disease associations, disease search,
  and evidence scoring.

Uses the DisGeNET REST API (https://www.disgenet.org/api).
Optional: set DISGENET_API_KEY for higher rate limits.

Start with:  python -m src.mcp_servers.disgenet.server
"""

from __future__ import annotations

import os
from typing import Any

from fastmcp import FastMCP

try:
    from src.mcp_servers.base import async_http_get, handle_error, standard_response
except ImportError:
    from mcp_servers.base import async_http_get, handle_error, standard_response  # type: ignore[no-redef]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DISGENET_API = "https://www.disgenet.org/api"
DISGENET_KEY = os.environ.get("DISGENET_API_KEY", "")

mcp = FastMCP("lumi-disgenet")


def _headers() -> dict[str, str]:
    h: dict[str, str] = {"Accept": "application/json"}
    if DISGENET_KEY:
        h["Authorization"] = f"Bearer {DISGENET_KEY}"
    return h


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def disgenet_gene_diseases(
    gene_symbol: str,
    min_score: float = 0.3,
    max_results: int = 50,
) -> dict[str, Any]:
    """Get disease associations for a gene from DisGeNET.

    Args:
        gene_symbol: Official gene symbol (e.g. BRCA1, TP53).
        min_score: Minimum GDA score (0-1). Default 0.3.
        max_results: Maximum associations to return.
    """
    try:
        url = f"{DISGENET_API}/gda/gene/{gene_symbol}"
        params = {"min_score": str(min_score), "limit": str(max_results), "format": "json"}
        data = await async_http_get(url, params=params, headers=_headers())
        results = data if isinstance(data, list) else data.get("results", data.get("payload", []))
        count = len(results) if isinstance(results, list) else 0
        return standard_response(
            summary=f"Found {count} disease association(s) for {gene_symbol} (score >= {min_score})",
            raw_data={"associations": results},
            source="DisGeNET",
            source_id=f"gene:{gene_symbol}",
        )
    except Exception as exc:
        return handle_error("disgenet_gene_diseases", exc)


@mcp.tool()
async def disgenet_disease_genes(
    disease_id: str,
    min_score: float = 0.3,
    max_results: int = 100,
) -> dict[str, Any]:
    """Get gene associations for a disease from DisGeNET.

    Args:
        disease_id: UMLS CUI (e.g. C0006142 for breast cancer) or disease name.
        min_score: Minimum GDA score (0-1).
        max_results: Maximum genes to return.
    """
    try:
        url = f"{DISGENET_API}/gda/disease/{disease_id}"
        params = {"min_score": str(min_score), "limit": str(max_results), "format": "json"}
        data = await async_http_get(url, params=params, headers=_headers())
        results = data if isinstance(data, list) else data.get("results", data.get("payload", []))
        count = len(results) if isinstance(results, list) else 0
        return standard_response(
            summary=f"Found {count} gene association(s) for disease {disease_id} (score >= {min_score})",
            raw_data={"associations": results},
            source="DisGeNET",
            source_id=f"disease:{disease_id}",
        )
    except Exception as exc:
        return handle_error("disgenet_disease_genes", exc)


@mcp.tool()
async def disgenet_variant_diseases(
    variant_id: str,
    max_results: int = 50,
) -> dict[str, Any]:
    """Get disease associations for a variant (rsID or genomic position).

    Args:
        variant_id: dbSNP rsID (e.g. rs1234) or variant identifier.
        max_results: Maximum associations to return.
    """
    try:
        url = f"{DISGENET_API}/vda/variant/{variant_id}"
        params = {"limit": str(max_results), "format": "json"}
        data = await async_http_get(url, params=params, headers=_headers())
        results = data if isinstance(data, list) else data.get("results", data.get("payload", []))
        count = len(results) if isinstance(results, list) else 0
        return standard_response(
            summary=f"Found {count} disease association(s) for variant {variant_id}",
            raw_data={"associations": results},
            source="DisGeNET",
            source_id=f"variant:{variant_id}",
        )
    except Exception as exc:
        return handle_error("disgenet_variant_diseases", exc)


@mcp.tool()
async def disgenet_search_diseases(
    query: str,
    max_results: int = 25,
) -> dict[str, Any]:
    """Search DisGeNET for diseases by name or keyword."""
    try:
        url = f"{DISGENET_API}/disease/search/{query}"
        params = {"limit": str(max_results), "format": "json"}
        data = await async_http_get(url, params=params, headers=_headers())
        results = data if isinstance(data, list) else data.get("results", data.get("payload", []))
        count = len(results) if isinstance(results, list) else 0
        return standard_response(
            summary=f"Found {count} disease(s) matching '{query}'",
            raw_data={"diseases": results},
            source="DisGeNET",
            source_id=f"search:{query}",
        )
    except Exception as exc:
        return handle_error("disgenet_search_diseases", exc)


if __name__ == "__main__":
    mcp.run()
