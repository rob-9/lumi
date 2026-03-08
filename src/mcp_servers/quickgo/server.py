"""
QuickGO MCP Server — Lumi Virtual Lab

Exposes tools for querying the EBI QuickGO API:
  GO annotation search, term info, term descendants, slim mapping.

Start with:  python -m src.mcp_servers.quickgo.server
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

# Relative import when running inside the package; fall back for direct exec.
try:
    from src.mcp_servers.base import async_http_get, async_http_post, handle_error, standard_response
except ImportError:
    from mcp_servers.base import async_http_get, async_http_post, handle_error, standard_response  # type: ignore[no-redef]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

QUICKGO_API = "https://www.ebi.ac.uk/QuickGO/services"

# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "Lumi QuickGO",
    instructions="Gene Ontology queries via EBI QuickGO: annotation search, term info, descendants, slim mapping",
)


# ---- 1. GO annotation search ------------------------------------------------


@mcp.tool()
async def quickgo_annotation_search(
    gene_id: str,
    taxon_id: int = 9606,
    aspect: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """
    Search GO annotations for a gene product.

    Args:
        gene_id: Gene product ID (e.g. UniProt accession like P04637).
        taxon_id: NCBI taxonomy ID (default 9606 for human).
        aspect: GO aspect filter — 'P' (biological process), 'F' (molecular function), or 'C' (cellular component). None for all.
        limit: Maximum number of annotations to return (default 50).
    """
    try:
        url = f"{QUICKGO_API}/annotation/search"
        params: dict[str, Any] = {
            "geneProductId": gene_id,
            "taxonId": taxon_id,
            "limit": limit,
        }
        if aspect:
            params["aspect"] = aspect

        headers = {"Accept": "application/json"}
        data = await async_http_get(url, params=params, headers=headers)

        results = data.get("results", [])
        total = data.get("numberOfHits", len(results))

        # Summarise top annotations
        go_terms: list[str] = []
        for ann in results[:10]:
            go_id = ann.get("goId", "")
            go_name = ann.get("goName", "")
            evidence = ann.get("goEvidence", "")
            go_terms.append(f"{go_id} ({go_name}, {evidence})")

        aspect_label = {"P": "Biological Process", "F": "Molecular Function", "C": "Cellular Component"}.get(
            aspect or "", "all aspects"
        )

        summary = (
            f"{total} GO annotations for {gene_id} (taxon {taxon_id}, {aspect_label}). "
            f"Top terms: {'; '.join(go_terms[:5])}"
            if results
            else f"No GO annotations found for {gene_id}."
        )

        return standard_response(
            summary=summary,
            raw_data={"total_hits": total, "annotations": results},
            source="EBI QuickGO",
            source_id=gene_id,
            confidence=0.85,
        )
    except Exception as exc:
        return handle_error("quickgo_annotation_search", exc)


# ---- 2. GO term info --------------------------------------------------------


@mcp.tool()
async def quickgo_term_info(go_id: str) -> dict[str, Any]:
    """
    Get information about a Gene Ontology term.

    Args:
        go_id: GO term identifier (e.g. GO:0008150).
    """
    try:
        url = f"{QUICKGO_API}/ontology/go/terms/{go_id}"
        headers = {"Accept": "application/json"}
        data = await async_http_get(url, headers=headers)

        results = data.get("results", [])
        if not results:
            return standard_response(
                summary=f"No GO term found for {go_id}.",
                raw_data={"go_id": go_id, "response": data},
                source="EBI QuickGO",
                source_id=go_id,
                confidence=0.5,
            )

        term = results[0]
        name = term.get("name", "unknown")
        aspect = term.get("aspect", "unknown")
        definition = term.get("definition", {}).get("text", "No definition available.")
        is_obsolete = term.get("isObsolete", False)
        synonyms = [s.get("name", "") for s in term.get("synonyms", [])]

        summary = (
            f"{go_id} — {name} (aspect: {aspect}). "
            f"{'OBSOLETE. ' if is_obsolete else ''}"
            f"Definition: {definition[:200]}{'...' if len(definition) > 200 else ''}. "
            f"{len(synonyms)} synonyms."
        )

        return standard_response(
            summary=summary,
            raw_data=term,
            source="EBI QuickGO",
            source_id=go_id,
            confidence=0.95,
        )
    except Exception as exc:
        return handle_error("quickgo_term_info", exc)


# ---- 3. GO term descendants -------------------------------------------------


@mcp.tool()
async def quickgo_term_descendants(go_id: str, relations: str = "is_a,part_of") -> dict[str, Any]:
    """
    Get descendants of a GO term.

    Args:
        go_id: GO term identifier (e.g. GO:0008150).
        relations: Comma-separated relation types to traverse (default 'is_a,part_of').
    """
    try:
        url = f"{QUICKGO_API}/ontology/go/terms/{go_id}/descendants"
        params: dict[str, Any] = {"relations": relations}
        headers = {"Accept": "application/json"}
        data = await async_http_get(url, params=params, headers=headers)

        results = data.get("results", [])
        descendants: list[dict[str, Any]] = []
        if results:
            descendants = results[0].get("descendants", [])

        descendant_names = []
        for desc in descendants[:10]:
            desc_id = desc if isinstance(desc, str) else desc.get("id", "")
            descendant_names.append(desc_id)

        summary = (
            f"{len(descendants)} descendants of {go_id} via [{relations}]. "
            f"Sample: {', '.join(descendant_names[:10])}"
            if descendants
            else f"No descendants found for {go_id} via [{relations}]."
        )

        return standard_response(
            summary=summary,
            raw_data={"go_id": go_id, "relations": relations, "descendants": descendants},
            source="EBI QuickGO",
            source_id=go_id,
            confidence=0.9,
        )
    except Exception as exc:
        return handle_error("quickgo_term_descendants", exc)


# ---- 4. GO slim mapping -----------------------------------------------------


@mcp.tool()
async def quickgo_slim_mapping(go_ids: str, slim_set: str = "goslim_generic") -> dict[str, Any]:
    """
    Map GO terms to a slim set.

    Args:
        go_ids: Comma-separated GO term IDs to map (e.g. 'GO:0008150,GO:0003674').
        slim_set: Name of the slim set to map to (default 'goslim_generic').
    """
    try:
        url = f"{QUICKGO_API}/ontology/go/slim"
        payload = {
            "goIds": [gid.strip() for gid in go_ids.split(",")],
            "slimsToMapTo": [slim_set],
        }
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        data = await async_http_post(url, data=payload, headers=headers)

        results = data.get("results", [])
        mappings: list[str] = []
        for entry in results[:20]:
            mapped_from = entry.get("slimsFromId", "")
            mapped_to = entry.get("slimsToIds", [])
            mappings.append(f"{mapped_from} -> {', '.join(mapped_to)}")

        summary = (
            f"Mapped {len(results)} GO terms to slim set '{slim_set}'. "
            f"Mappings: {'; '.join(mappings[:5])}"
            if results
            else f"No slim mappings found for provided GO IDs in '{slim_set}'."
        )

        return standard_response(
            summary=summary,
            raw_data={"slim_set": slim_set, "input_ids": go_ids, "mappings": results},
            source="EBI QuickGO",
            source_id=go_ids,
            confidence=0.85,
        )
    except Exception as exc:
        return handle_error("quickgo_slim_mapping", exc)


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
