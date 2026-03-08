"""
BindingDB MCP Server — Lumi Virtual Lab

Exposes tools for querying BindingDB binding affinity data:
  compound-target binding affinities, target search, compound search,
  and Ki/Kd/IC50/EC50 measurements.

Start with:  python -m src.mcp_servers.bindingdb.server
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

BINDINGDB_API = "https://bindingdb.org/axis2/services/BDBService"
BINDINGDB_REST = "https://bindingdb.org/bind/index.jsp"

mcp = FastMCP("lumi-bindingdb")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def bindingdb_search_by_smiles(
    smiles: str,
    similarity: float = 0.85,
    max_results: int = 50,
) -> dict[str, Any]:
    """Search BindingDB for binding data by compound SMILES with similarity cutoff."""
    try:
        url = f"{BINDINGDB_API}/getLigandsBySmiles"
        params = {
            "smiles": smiles,
            "cutoff": str(similarity),
            "maxResults": str(max_results),
            "response": "json",
        }
        data = await async_http_get(url, params=params)
        affinities = data if isinstance(data, dict) else {"results": data}
        count = len(affinities.get("affinities", affinities.get("results", [])))
        return standard_response(
            summary=f"Found {count} binding record(s) for SMILES similarity >= {similarity}",
            raw_data=affinities,
            source="BindingDB",
            source_id=f"smiles:{smiles[:30]}",
        )
    except Exception as exc:
        return handle_error("bindingdb_search_by_smiles", exc)


@mcp.tool()
async def bindingdb_get_target_affinities(
    uniprot_id: str,
    max_results: int = 100,
) -> dict[str, Any]:
    """Get all binding affinities for a target protein by UniProt accession."""
    try:
        url = f"{BINDINGDB_API}/getLigandsByUniprots"
        params = {
            "uniprot": uniprot_id,
            "maxResults": str(max_results),
            "response": "json",
        }
        data = await async_http_get(url, params=params)
        affinities = data if isinstance(data, dict) else {"results": data}
        count = len(affinities.get("affinities", affinities.get("results", [])))
        return standard_response(
            summary=f"Found {count} binding record(s) for UniProt {uniprot_id}",
            raw_data=affinities,
            source="BindingDB",
            source_id=f"uniprot:{uniprot_id}",
        )
    except Exception as exc:
        return handle_error("bindingdb_get_target_affinities", exc)


@mcp.tool()
async def bindingdb_get_compound_affinities(
    monomer_id: str,
    max_results: int = 100,
) -> dict[str, Any]:
    """Get binding affinities for a specific BindingDB compound (monomer ID)."""
    try:
        url = f"{BINDINGDB_API}/getBindingsByMonomerID"
        params = {
            "monomerid": monomer_id,
            "maxResults": str(max_results),
            "response": "json",
        }
        data = await async_http_get(url, params=params)
        return standard_response(
            summary=f"Binding data for BindingDB monomer {monomer_id}",
            raw_data=data,
            source="BindingDB",
            source_id=f"monomer:{monomer_id}",
        )
    except Exception as exc:
        return handle_error("bindingdb_get_compound_affinities", exc)


@mcp.tool()
async def bindingdb_search_by_target_name(
    target_name: str,
    max_results: int = 50,
) -> dict[str, Any]:
    """Search BindingDB targets by name and return associated binding data."""
    try:
        url = f"{BINDINGDB_API}/getTargetByCompound"
        params = {
            "target": target_name,
            "maxResults": str(max_results),
            "response": "json",
        }
        data = await async_http_get(url, params=params)
        return standard_response(
            summary=f"BindingDB target search for '{target_name}'",
            raw_data=data,
            source="BindingDB",
            source_id=f"target:{target_name}",
        )
    except Exception as exc:
        return handle_error("bindingdb_search_by_target_name", exc)


if __name__ == "__main__":
    mcp.run()
