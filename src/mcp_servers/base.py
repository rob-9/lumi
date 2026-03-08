"""
Base helper module for all Lumi Virtual Lab MCP servers.

Provides:
- async_http_get / async_http_post with retry + timeout
- standard_response / handle_error for consistent output format
- Per-domain async semaphore rate limiting
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("lumi.mcp.base")

# ---------------------------------------------------------------------------
# Rate-limiting: one semaphore per domain, configurable concurrency
# ---------------------------------------------------------------------------

_domain_semaphores: dict[str, asyncio.Semaphore] = {}
_DEFAULT_CONCURRENCY = 2  # max concurrent requests per domain (lowered from 5)

# Per-domain concurrency overrides for APIs with known tight limits
_DOMAIN_CONCURRENCY: dict[str, int] = {
    "api.semanticscholar.org": 1,      # S2 free tier: 1 req/s
    "eutils.ncbi.nlm.nih.gov": 2,      # NCBI: 3/s without key, stay safe
    "api.opentargets.io": 2,
    "rest.ensembl.org": 2,
}


def _get_semaphore(url: str, max_concurrent: int | None = None) -> asyncio.Semaphore:
    """Return (or create) an asyncio.Semaphore for the domain in *url*."""
    domain = urlparse(url).netloc
    if domain not in _domain_semaphores:
        concurrency = max_concurrent or _DOMAIN_CONCURRENCY.get(domain, _DEFAULT_CONCURRENCY)
        _domain_semaphores[domain] = asyncio.Semaphore(concurrency)
    return _domain_semaphores[domain]


# ---------------------------------------------------------------------------
# Retry / timeout constants
# ---------------------------------------------------------------------------

MAX_RETRIES = 5           # increased from 3 to survive rate-limit bursts
BASE_BACKOFF = 2.0        # seconds; doubles each retry (was 1.0)
DEFAULT_TIMEOUT = 30.0    # seconds


# ---------------------------------------------------------------------------
# Core HTTP helpers
# ---------------------------------------------------------------------------

async def async_http_get(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
) -> dict[str, Any]:
    """
    Perform an async HTTP GET with retry (exponential back-off) and timeout.

    Returns the parsed JSON body on success, or raises after exhausting retries.
    Respects ``Retry-After`` headers on 429 responses and adds jitter to
    prevent thundering herd across concurrent agents.
    """
    sem = _get_semaphore(url)
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        async with sem:
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.get(url, params=params, headers=headers)
                    resp.raise_for_status()
                    try:
                        return resp.json()
                    except (json.JSONDecodeError, ValueError):
                        return {"text": resp.text}
            except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt < max_retries:
                    wait = _compute_backoff(attempt, exc)
                    logger.warning(
                        "GET %s attempt %d/%d failed (%s). Retrying in %.1fs ...",
                        url, attempt, max_retries, exc, wait,
                    )
                    await asyncio.sleep(wait)

    raise last_exc  # type: ignore[misc]


async def async_http_post(
    url: str,
    data: dict[str, Any] | str | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
) -> dict[str, Any]:
    """
    Perform an async HTTP POST with retry (exponential back-off) and timeout.

    If *data* is a dict it is sent as JSON; if it is a string it is sent as
    the raw body (useful for GraphQL query strings already serialised).
    """
    sem = _get_semaphore(url)
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        async with sem:
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    if isinstance(data, dict):
                        resp = await client.post(url, json=data, headers=headers)
                    else:
                        resp = await client.post(url, content=data, headers=headers)
                    resp.raise_for_status()
                    try:
                        return resp.json()
                    except (json.JSONDecodeError, ValueError):
                        return {"text": resp.text}
            except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt < max_retries:
                    wait = _compute_backoff(attempt, exc)
                    logger.warning(
                        "POST %s attempt %d/%d failed (%s). Retrying in %.1fs ...",
                        url, attempt, max_retries, exc, wait,
                    )
                    await asyncio.sleep(wait)

    raise last_exc  # type: ignore[misc]


def _compute_backoff(attempt: int, exc: Exception) -> float:
    """Compute backoff with jitter, respecting Retry-After on 429s."""
    base_wait = BASE_BACKOFF * (2 ** (attempt - 1))

    # Respect Retry-After header on 429 responses
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
        retry_after = exc.response.headers.get("retry-after")
        if retry_after:
            try:
                base_wait = max(base_wait, float(retry_after))
            except ValueError:
                pass

    # Add jitter (±25%) to desynchronize concurrent agents
    jitter = random.uniform(0.75, 1.25)
    return base_wait * jitter


# ---------------------------------------------------------------------------
# Standard response builders
# ---------------------------------------------------------------------------

def standard_response(
    summary: str,
    raw_data: dict[str, Any],
    source: str,
    source_id: str,
    version: str | None = None,
    confidence: float = 0.8,
) -> dict[str, Any]:
    """
    Build the canonical Lumi response envelope.

    Every tool across every MCP server should return this shape so that
    upstream agents can rely on a consistent schema.
    """
    return {
        "summary": summary,
        "raw_data": raw_data,
        "provenance": {
            "source": source,
            "source_id": source_id,
            "version": version or "latest",
            "access_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "confidence": confidence,
    }


def handle_error(tool_name: str, error: Exception | str) -> dict[str, Any]:
    """
    Return a structured error response that agents can inspect without crashing.
    """
    error_msg = str(error)
    logger.error("Tool %s error: %s", tool_name, error_msg)
    return {
        "error": True,
        "tool": tool_name,
        "message": error_msg,
        "provenance": {
            "source": tool_name,
            "source_id": "error",
            "version": None,
            "access_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "confidence": 0.0,
    }
