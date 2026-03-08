"""
HPO (Human Phenotype Ontology) MCP Server — Lumi Virtual Lab

Exposes tools for querying the HPO database:
  phenotype search, gene-phenotype associations, disease-phenotype
  associations, and ontology term navigation.

Uses the JAX HPO API at https://hpo.jax.org/api.

Start with:  python -m src.mcp_servers.hpo.server
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

HPO_API = "https://hpo.jax.org/api/hpo"

mcp = FastMCP("lumi-hpo")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def hpo_search_terms(
    query: str,
    max_results: int = 20,
) -> dict[str, Any]:
    """Search HPO for phenotype terms by keyword.

    Args:
        query: Search term (e.g. 'seizure', 'cardiomyopathy').
        max_results: Maximum terms to return.
    """
    try:
        url = f"{HPO_API}/search"
        params = {"q": query, "max": str(max_results), "category": "terms"}
        data = await async_http_get(url, params=params)
        terms = data.get("terms", data.get("results", []))
        count = len(terms) if isinstance(terms, list) else 0
        return standard_response(
            summary=f"Found {count} HPO term(s) matching '{query}'",
            raw_data={"terms": terms},
            source="HPO",
            source_id=f"search:{query}",
        )
    except Exception as exc:
        return handle_error("hpo_search_terms", exc)


@mcp.tool()
async def hpo_get_term(
    term_id: str,
) -> dict[str, Any]:
    """Get details for an HPO term including definition, synonyms, and hierarchy.

    Args:
        term_id: HPO term ID (e.g. HP:0001250 for seizures).
    """
    try:
        url = f"{HPO_API}/term/{term_id}"
        data = await async_http_get(url)
        name = data.get("name", data.get("details", {}).get("name", term_id))
        return standard_response(
            summary=f"HPO term {term_id}: {name}",
            raw_data=data,
            source="HPO",
            source_id=term_id,
        )
    except Exception as exc:
        return handle_error("hpo_get_term", exc)


@mcp.tool()
async def hpo_gene_phenotypes(
    gene_symbol: str,
) -> dict[str, Any]:
    """Get HPO phenotype terms associated with a gene.

    Args:
        gene_symbol: Gene symbol (e.g. BRCA1, SCN1A).
    """
    try:
        url = f"{HPO_API}/gene/{gene_symbol}"
        data = await async_http_get(url)
        phenotypes = data.get("associations", data.get("phenotypes", data.get("termAssoc", [])))
        count = len(phenotypes) if isinstance(phenotypes, list) else 0
        return standard_response(
            summary=f"Found {count} HPO phenotype(s) for gene {gene_symbol}",
            raw_data={"gene": gene_symbol, "phenotypes": phenotypes},
            source="HPO",
            source_id=f"gene:{gene_symbol}",
        )
    except Exception as exc:
        return handle_error("hpo_gene_phenotypes", exc)


@mcp.tool()
async def hpo_disease_phenotypes(
    disease_id: str,
) -> dict[str, Any]:
    """Get HPO phenotype terms associated with a disease.

    Args:
        disease_id: OMIM or ORPHA disease ID (e.g. OMIM:176000, ORPHA:558).
    """
    try:
        url = f"{HPO_API}/disease/{disease_id}"
        data = await async_http_get(url)
        phenotypes = data.get("associations", data.get("phenotypes", data.get("termAssoc", [])))
        count = len(phenotypes) if isinstance(phenotypes, list) else 0
        return standard_response(
            summary=f"Found {count} HPO phenotype(s) for disease {disease_id}",
            raw_data={"disease": disease_id, "phenotypes": phenotypes},
            source="HPO",
            source_id=f"disease:{disease_id}",
        )
    except Exception as exc:
        return handle_error("hpo_disease_phenotypes", exc)


if __name__ == "__main__":
    mcp.run()
