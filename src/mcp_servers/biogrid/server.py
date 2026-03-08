"""
BioGRID MCP Server — Lumi Virtual Lab

Exposes tools for querying BioGRID protein-protein interaction data:
  interaction search by gene, organism filtering, evidence types,
  and interaction network retrieval.

Requires BIOGRID_API_KEY environment variable (free at https://webservice.thebiogrid.org/).

Start with:  python -m src.mcp_servers.biogrid.server
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

BIOGRID_API = "https://webservice.thebiogrid.org/interactions"
BIOGRID_KEY = os.environ.get("BIOGRID_API_KEY", "")

mcp = FastMCP("lumi-biogrid")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def biogrid_search_interactions(
    gene_symbol: str,
    organism: int = 9606,
    max_results: int = 100,
    evidence_type: str = "any",
) -> dict[str, Any]:
    """Search BioGRID for protein-protein interactions involving a gene.

    Args:
        gene_symbol: Official gene symbol (e.g. BRCA1, TP53).
        organism: NCBI Taxonomy ID (default 9606 = human).
        max_results: Max interactions to return.
        evidence_type: Filter by evidence: 'any', 'physical', 'genetic'.
    """
    try:
        params: dict[str, Any] = {
            "accesskey": BIOGRID_KEY,
            "format": "json",
            "searchNames": "true",
            "geneList": gene_symbol,
            "taxId": str(organism),
            "max": str(max_results),
            "includeInteractors": "true",
            "includeInteractorInteractions": "false",
        }
        if evidence_type != "any":
            params["evidenceList"] = evidence_type
        data = await async_http_get(BIOGRID_API, params=params)
        interactions = data if isinstance(data, dict) else {}
        count = len(interactions)
        return standard_response(
            summary=f"Found {count} BioGRID interaction(s) for {gene_symbol} (organism {organism})",
            raw_data=interactions,
            source="BioGRID",
            source_id=f"gene:{gene_symbol}",
        )
    except Exception as exc:
        return handle_error("biogrid_search_interactions", exc)


@mcp.tool()
async def biogrid_get_interaction_network(
    gene_list: str,
    organism: int = 9606,
    max_results: int = 500,
) -> dict[str, Any]:
    """Get the full interaction network for a set of genes.

    Args:
        gene_list: Pipe-separated gene symbols (e.g. 'BRCA1|TP53|EGFR').
        organism: NCBI Taxonomy ID (default 9606 = human).
        max_results: Max interactions to return.
    """
    try:
        params: dict[str, Any] = {
            "accesskey": BIOGRID_KEY,
            "format": "json",
            "searchNames": "true",
            "geneList": gene_list,
            "taxId": str(organism),
            "max": str(max_results),
            "includeInteractors": "true",
            "includeInteractorInteractions": "true",
        }
        data = await async_http_get(BIOGRID_API, params=params)
        interactions = data if isinstance(data, dict) else {}
        count = len(interactions)
        genes = gene_list.split("|")
        return standard_response(
            summary=f"BioGRID network for {len(genes)} gene(s): {count} interaction(s)",
            raw_data=interactions,
            source="BioGRID",
            source_id=f"network:{gene_list[:50]}",
        )
    except Exception as exc:
        return handle_error("biogrid_get_interaction_network", exc)


@mcp.tool()
async def biogrid_get_chemical_interactions(
    gene_symbol: str,
    organism: int = 9606,
    max_results: int = 100,
) -> dict[str, Any]:
    """Get BioGRID chemical-protein interactions for a gene."""
    try:
        url = "https://webservice.thebiogrid.org/interactions"
        params: dict[str, Any] = {
            "accesskey": BIOGRID_KEY,
            "format": "json",
            "searchNames": "true",
            "geneList": gene_symbol,
            "taxId": str(organism),
            "max": str(max_results),
            "includeInteractors": "true",
            "interSpeciesExcluded": "false",
            "evidenceList": "chemical",
        }
        data = await async_http_get(url, params=params)
        interactions = data if isinstance(data, dict) else {}
        count = len(interactions)
        return standard_response(
            summary=f"Found {count} chemical interaction(s) for {gene_symbol} in BioGRID",
            raw_data=interactions,
            source="BioGRID",
            source_id=f"chemical:{gene_symbol}",
        )
    except Exception as exc:
        return handle_error("biogrid_get_chemical_interactions", exc)


if __name__ == "__main__":
    mcp.run()
