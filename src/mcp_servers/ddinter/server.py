"""
DDInter (Drug-Drug Interaction) MCP Server — Lumi Virtual Lab

Exposes tools for querying DDInter drug-drug interaction data:
  interaction lookup, severity classification, mechanism details,
  and drug search.

Uses the DDInter API at http://ddinter.scbdd.com/api.

Start with:  python -m src.mcp_servers.ddinter.server
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

DDINTER_API = "http://ddinter.scbdd.com/api/v1"

mcp = FastMCP("lumi-ddinter")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def ddinter_search_drug(
    drug_name: str,
    max_results: int = 20,
) -> dict[str, Any]:
    """Search DDInter for a drug by name.

    Args:
        drug_name: Drug name (e.g. 'warfarin', 'aspirin').
        max_results: Maximum results to return.
    """
    try:
        url = f"{DDINTER_API}/drugs/search"
        params = {"q": drug_name, "limit": str(max_results)}
        data = await async_http_get(url, params=params)
        results = data if isinstance(data, list) else data.get("drugs", data.get("results", []))
        count = len(results) if isinstance(results, list) else 0
        return standard_response(
            summary=f"Found {count} drug(s) matching '{drug_name}' in DDInter",
            raw_data={"drugs": results},
            source="DDInter",
            source_id=f"search:{drug_name}",
        )
    except Exception as exc:
        return handle_error("ddinter_search_drug", exc)


@mcp.tool()
async def ddinter_get_interactions(
    drug_id: str,
    severity: str | None = None,
    max_results: int = 50,
) -> dict[str, Any]:
    """Get drug-drug interactions for a specific drug.

    Args:
        drug_id: DDInter drug ID or drug name.
        severity: Optional filter: 'major', 'moderate', 'minor'.
        max_results: Maximum interactions to return.
    """
    try:
        url = f"{DDINTER_API}/interactions/{drug_id}"
        params: dict[str, str] = {"limit": str(max_results)}
        if severity:
            params["severity"] = severity
        data = await async_http_get(url, params=params)
        interactions = data if isinstance(data, list) else data.get("interactions", data.get("results", []))
        count = len(interactions) if isinstance(interactions, list) else 0
        sev_str = f" (severity={severity})" if severity else ""
        return standard_response(
            summary=f"Found {count} drug-drug interaction(s) for {drug_id}{sev_str}",
            raw_data={"interactions": interactions},
            source="DDInter",
            source_id=f"interactions:{drug_id}",
        )
    except Exception as exc:
        return handle_error("ddinter_get_interactions", exc)


@mcp.tool()
async def ddinter_check_pair(
    drug_a: str,
    drug_b: str,
) -> dict[str, Any]:
    """Check for interactions between two specific drugs.

    Args:
        drug_a: First drug name or DDInter ID.
        drug_b: Second drug name or DDInter ID.
    """
    try:
        url = f"{DDINTER_API}/interactions/pair"
        params = {"drug_a": drug_a, "drug_b": drug_b}
        data = await async_http_get(url, params=params)
        has_interaction = bool(data and not data.get("error"))
        return standard_response(
            summary=f"DDI check: {drug_a} + {drug_b} — {'interaction found' if has_interaction else 'no known interaction'}",
            raw_data=data,
            source="DDInter",
            source_id=f"pair:{drug_a}:{drug_b}",
        )
    except Exception as exc:
        return handle_error("ddinter_check_pair", exc)


if __name__ == "__main__":
    mcp.run()
