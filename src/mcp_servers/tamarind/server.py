"""
Tamarind Bio MCP Server -- Lumi Virtual Lab

Wraps the Tamarind Bio REST API so agents can submit and manage computational
biology jobs: protein folding (AlphaFold), docking (DiffDock), molecular
dynamics, protein design (RFdiffusion, ProteinMPNN), and multi-stage pipelines.

Jobs are asynchronous — submit returns immediately; agents poll for status
until completion, then retrieve presigned S3 URLs to download results.

API reference: https://app.tamarind.bio/api/
Auth: ``TAMARIND_API_KEY`` environment variable → ``x-api-key`` header.

Start with:  python -m src.mcp_servers.tamarind.server
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx
from fastmcp import FastMCP

try:
    from src.mcp_servers.base import handle_error, standard_response
except ImportError:
    from mcp_servers.base import handle_error, standard_response  # type: ignore[no-redef]

logger = logging.getLogger("lumi.mcp.tamarind")

mcp = FastMCP("tamarind")

# ---------------------------------------------------------------------------
# Constants & auth
# ---------------------------------------------------------------------------

_BASE_URL = "https://app.tamarind.bio/api"
_TIMEOUT = 60.0
_MAX_RETRIES = 2
_BACKOFF_BASE = 1.0


def _api_key() -> str:
    key = os.environ.get("TAMARIND_API_KEY", "")
    if not key:
        raise ValueError(
            "TAMARIND_API_KEY environment variable is not set. "
            "Get an API key at https://app.tamarind.bio"
        )
    return key


def _headers() -> dict[str, str]:
    return {
        "x-api-key": _api_key(),
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# HTTP helpers with retry + error mapping
# ---------------------------------------------------------------------------


async def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    data: bytes | None = None,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Make an authenticated request to the Tamarind API with retry logic.

    Handles:
    - 400 → surface API error message
    - 403 → budget exceeded
    - 429 → rate limit (retry with backoff)
    - 5xx → retry once then surface error
    """
    url = f"{_BASE_URL}/{path.lstrip('/')}"
    headers = _headers()
    if extra_headers:
        headers.update(extra_headers)

    last_exc: Exception | None = None

    for attempt in range(1, _MAX_RETRIES + 2):
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                if method == "GET":
                    resp = await client.get(url, params=params, headers=headers)
                elif method == "POST":
                    resp = await client.post(url, json=json_body, headers=headers)
                elif method == "PUT":
                    put_headers = {**headers}
                    if data is not None:
                        put_headers["Content-Type"] = "application/octet-stream"
                    resp = await client.put(url, content=data, headers=put_headers)
                elif method == "DELETE":
                    resp = await client.delete(url, params=params, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                if resp.status_code == 400:
                    detail = resp.text
                    try:
                        detail = resp.json().get("message", resp.text)
                    except Exception:
                        pass
                    raise httpx.HTTPStatusError(
                        f"Bad request: {detail}", request=resp.request, response=resp
                    )

                if resp.status_code == 403:
                    raise httpx.HTTPStatusError(
                        "Budget exceeded or access denied. Check your Tamarind Bio plan.",
                        request=resp.request,
                        response=resp,
                    )

                if resp.status_code == 429:
                    wait = _BACKOFF_BASE * (2 ** (attempt - 1))
                    logger.warning("Tamarind rate limited, retrying in %.1fs", wait)
                    await asyncio.sleep(wait)
                    continue

                resp.raise_for_status()

                if resp.headers.get("content-type", "").startswith("application/json"):
                    return resp.json()
                return {"text": resp.text}

        except httpx.HTTPStatusError:
            raise
        except (httpx.RequestError, httpx.TimeoutException) as exc:
            last_exc = exc
            if attempt <= _MAX_RETRIES:
                wait = _BACKOFF_BASE * (2 ** (attempt - 1))
                logger.warning(
                    "Tamarind %s %s attempt %d failed (%s), retrying in %.1fs",
                    method, path, attempt, exc, wait,
                )
                await asyncio.sleep(wait)

    raise last_exc  # type: ignore[misc]


# ===================================================================
# Tool discovery
# ===================================================================


@mcp.tool()
async def tamarind_list_tools() -> dict[str, Any]:
    """List all available Tamarind Bio computational tools and their configuration schemas.

    Returns tool names, descriptions, and the settings each tool accepts.
    Agents should call this first to discover available tools and valid
    parameter schemas before submitting jobs.
    """
    try:
        data = await _request("GET", "/tools")
        tools = data if isinstance(data, list) else data.get("tools", data)
        return standard_response(
            summary=f"Found {len(tools) if isinstance(tools, list) else '?'} Tamarind tools",
            raw_data={"tools": tools},
            source="tamarind_bio",
            source_id="list_tools",
        )
    except Exception as exc:
        return handle_error("tamarind_list_tools", exc)


# ===================================================================
# Job submission
# ===================================================================


@mcp.tool()
async def tamarind_submit_job(
    job_name: str,
    tool_type: str,
    settings: dict[str, Any],
    project_tag: str = "",
) -> dict[str, Any]:
    """Submit a single computational job to Tamarind Bio.

    Args:
        job_name: Unique name for the job (used for status polling and result retrieval).
        tool_type: Tool name (e.g. ``"alphafold"``, ``"rfdiffusion"``, ``"proteinmpnn"``,
                   ``"diffdock"``, ``"immunebuilder"``, ``"openmm"``).
        settings: Tool-specific configuration dict. Use ``tamarind_list_tools`` to
                  discover valid settings for each tool type.
        project_tag: Optional tag to group jobs by project.

    Returns confirmation and job name for subsequent polling.
    """
    try:
        body: dict[str, Any] = {
            "jobName": job_name,
            "type": tool_type,
            "settings": settings,
        }
        if project_tag:
            body["projectTag"] = project_tag

        data = await _request("POST", "/submit-job", json_body=body)
        return standard_response(
            summary=f"Job '{job_name}' ({tool_type}) submitted",
            raw_data={"job_name": job_name, "type": tool_type, "response": data},
            source="tamarind_bio",
            source_id=f"submit_job/{job_name}",
        )
    except Exception as exc:
        return handle_error("tamarind_submit_job", exc)


@mcp.tool()
async def tamarind_submit_batch(
    batch_name: str,
    tool_type: str,
    jobs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Submit a batch of jobs of the same tool type.

    Args:
        batch_name: Name for the batch (results aggregated under this name).
        tool_type: Tool name (same tool for all jobs in the batch).
        jobs: Array of settings dicts, one per job in the batch.
    """
    try:
        body = {
            "batchName": batch_name,
            "type": tool_type,
            "jobs": jobs,
        }
        data = await _request("POST", "/submit-batch", json_body=body)
        return standard_response(
            summary=f"Batch '{batch_name}' ({tool_type}, {len(jobs)} jobs) submitted",
            raw_data={"batch_name": batch_name, "type": tool_type, "job_count": len(jobs), "response": data},
            source="tamarind_bio",
            source_id=f"submit_batch/{batch_name}",
        )
    except Exception as exc:
        return handle_error("tamarind_submit_batch", exc)


# ===================================================================
# Job monitoring
# ===================================================================


@mcp.tool()
async def tamarind_get_jobs(
    job_name: str = "",
    batch: str = "",
    batch_only: bool = False,
    limit: int = 50,
    start_key: str = "",
    organization: bool = False,
) -> dict[str, Any]:
    """Get job status from Tamarind Bio.

    Call with a specific ``job_name`` to check one job, or leave empty to list
    recent jobs.  Each job includes: ``JobName``, ``JobStatus`` (one of
    ``"In Queue"``, ``"Running"``, ``"Complete"``, ``"Stopped"``), ``Type``,
    ``Settings``, ``Started``, ``Completed``, ``Created``, ``WeightedHours``.

    Also returns aggregate ``statuses`` counts across all jobs.
    """
    try:
        params: dict[str, Any] = {"limit": limit}
        if job_name:
            params["jobName"] = job_name
        if batch:
            params["batch"] = batch
        if batch_only:
            params["batchOnly"] = "true"
        if start_key:
            params["startKey"] = start_key
        if organization:
            params["organization"] = "true"

        data = await _request("GET", "/jobs", params=params)

        jobs = data.get("jobs", [])
        statuses = data.get("statuses", {})
        return standard_response(
            summary=f"{len(jobs)} jobs returned (Complete: {statuses.get('Complete', 0)}, Running: {statuses.get('Running', 0)}, Queued: {statuses.get('In Queue', 0)})",
            raw_data={"jobs": jobs, "statuses": statuses},
            source="tamarind_bio",
            source_id="get_jobs",
        )
    except Exception as exc:
        return handle_error("tamarind_get_jobs", exc)


@mcp.tool()
async def tamarind_poll_until_complete(
    job_name: str,
    poll_interval: float = 30.0,
    max_polls: int = 120,
) -> dict[str, Any]:
    """Poll a Tamarind job until it reaches ``Complete`` or ``Stopped`` status.

    This is a convenience wrapper that agents can call instead of manually
    looping on ``tamarind_get_jobs``.  Default: poll every 30s for up to 60
    minutes.

    Returns the final job record.
    """
    try:
        for i in range(1, max_polls + 1):
            data = await _request("GET", "/jobs", params={"jobName": job_name})
            jobs = data.get("jobs", [])
            if not jobs:
                return handle_error("tamarind_poll_until_complete", f"Job '{job_name}' not found")

            job = jobs[0]
            status = job.get("JobStatus", "")

            if status == "Complete":
                return standard_response(
                    summary=f"Job '{job_name}' complete (polled {i} times)",
                    raw_data={"job": job, "polls": i},
                    source="tamarind_bio",
                    source_id=f"poll/{job_name}",
                )

            if status == "Stopped":
                return standard_response(
                    summary=f"Job '{job_name}' stopped (polled {i} times)",
                    raw_data={"job": job, "polls": i},
                    source="tamarind_bio",
                    source_id=f"poll/{job_name}",
                    confidence=0.3,
                )

            logger.info("Job '%s' status: %s (poll %d/%d)", job_name, status, i, max_polls)
            await asyncio.sleep(poll_interval)

        return handle_error(
            "tamarind_poll_until_complete",
            f"Job '{job_name}' did not complete within {max_polls * poll_interval:.0f}s"
        )
    except Exception as exc:
        return handle_error("tamarind_poll_until_complete", exc)


# ===================================================================
# Results retrieval
# ===================================================================


@mcp.tool()
async def tamarind_get_result(
    job_name: str,
    file_name: str = "",
    pdbs_only: bool = False,
) -> dict[str, Any]:
    """Get a presigned S3 URL to download job results.

    Args:
        job_name: Name of the completed job.
        file_name: Optional path to a specific output file within the results.
        pdbs_only: For batch jobs, return only PDB files.

    Returns a presigned URL pointing to a zip file (or specific file) that can
    be downloaded or passed to downstream tools.
    """
    try:
        body: dict[str, Any] = {"jobName": job_name}
        if file_name:
            body["fileName"] = file_name
        if pdbs_only:
            body["pdbsOnly"] = True

        data = await _request("POST", "/result", json_body=body)

        # The API returns the presigned URL — extract it
        url = data.get("url", data.get("text", ""))
        return standard_response(
            summary=f"Results URL for '{job_name}' retrieved",
            raw_data={"job_name": job_name, "result_url": url, "file_name": file_name or "all"},
            source="tamarind_bio",
            source_id=f"result/{job_name}",
        )
    except Exception as exc:
        return handle_error("tamarind_get_result", exc)


# ===================================================================
# File management
# ===================================================================


@mcp.tool()
async def tamarind_upload_file(
    filename: str,
    file_content: str,
    folder: str = "",
) -> dict[str, Any]:
    """Upload a file (PDB, SDF, FASTA, etc.) to the Tamarind Bio account.

    After upload, reference the filename in job submissions as an input.
    For files under 4MB, pass the content directly as a string. For PDB files,
    pass the raw PDB text content.

    Args:
        filename: Target filename (e.g. ``"target.pdb"``).
        file_content: File content as text (PDB, FASTA, etc.) or base64 for binary.
        folder: Optional folder path.
    """
    try:
        path = f"/upload/{filename}"
        if folder:
            path = f"/upload/{folder}/{filename}"

        data = await _request(
            "PUT",
            path,
            data=file_content.encode("utf-8"),
        )

        return standard_response(
            summary=f"Uploaded '{filename}' ({len(file_content)} bytes)",
            raw_data={"filename": filename, "folder": folder, "response": data},
            source="tamarind_bio",
            source_id=f"upload/{filename}",
        )
    except Exception as exc:
        return handle_error("tamarind_upload_file", exc)


@mcp.tool()
async def tamarind_list_files(
    include_folders: bool = False,
    folder: str = "",
) -> dict[str, Any]:
    """List files in the Tamarind Bio account.

    Args:
        include_folders: Include folder entries in results.
        folder: Filter to a specific folder.
    """
    try:
        params: dict[str, Any] = {}
        if include_folders:
            params["includeFolders"] = True
        if folder:
            params["folder"] = folder

        data = await _request("GET", "/files", params=params)
        files = data if isinstance(data, list) else data.get("files", data)
        return standard_response(
            summary=f"Found {len(files) if isinstance(files, list) else '?'} files",
            raw_data={"files": files},
            source="tamarind_bio",
            source_id="list_files",
        )
    except Exception as exc:
        return handle_error("tamarind_list_files", exc)


# ===================================================================
# Pipelines
# ===================================================================


@mcp.tool()
async def tamarind_submit_pipeline(
    job_name: str,
    initial_inputs: list[str],
    stages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Submit a multi-stage computational pipeline to Tamarind Bio.

    Pipelines chain tools together automatically — use ``"pipe"`` as the value
    for any setting that should receive the output of the previous stage.

    Args:
        job_name: Unique pipeline job name.
        initial_inputs: List of input filenames or sequences for the first stage.
        stages: List of stage dicts, each with:
            - ``task``: one of ``"Structure Design"``, ``"Structure Prediction"``,
              ``"Inverse Folding"``, ``"Sequence Design"``, ``"Scoring"``
            - ``toolSettings``: dict mapping tool name to its settings dict.
              Use ``"pipe"`` for values that should receive previous stage output.

    Example pipeline (RFdiffusion -> ProteinMPNN -> AlphaFold)::

        stages = [
            {"task": "Structure Design", "toolSettings": {
                "rfdiffusion": {"pdbFile": "pipe", "contigs": "10-40/A163-181/10-40", "numDesigns": "2"}}},
            {"task": "Inverse Folding", "toolSettings": {
                "proteinmpnn": {"pdbFile": "pipe", "designedChains": ["A"], "numSequences": "2"}}},
            {"task": "Structure Prediction", "toolSettings": {
                "alphafold": {"sequence": "pipe"}}},
        ]
    """
    try:
        body = {
            "jobName": job_name,
            "initialInputs": initial_inputs,
            "stages": stages,
        }
        data = await _request("POST", "/submit-pipeline", json_body=body)
        return standard_response(
            summary=f"Pipeline '{job_name}' ({len(stages)} stages) submitted",
            raw_data={
                "job_name": job_name,
                "stage_count": len(stages),
                "stages": [s.get("task", "unknown") for s in stages],
                "response": data,
            },
            source="tamarind_bio",
            source_id=f"submit_pipeline/{job_name}",
        )
    except Exception as exc:
        return handle_error("tamarind_submit_pipeline", exc)


@mcp.tool()
async def tamarind_run_pipeline(
    job_name: str,
    pipeline_name: str,
    initial_inputs: list[str],
) -> dict[str, Any]:
    """Run a previously saved pipeline by name.

    Args:
        job_name: Unique name for this pipeline run.
        pipeline_name: Name of the saved pipeline template.
        initial_inputs: Input filenames or sequences.
    """
    try:
        body = {
            "jobName": job_name,
            "pipelineName": pipeline_name,
            "initialInputs": initial_inputs,
        }
        data = await _request("POST", "/run-pipeline", json_body=body)
        return standard_response(
            summary=f"Pipeline '{pipeline_name}' started as '{job_name}'",
            raw_data={"job_name": job_name, "pipeline_name": pipeline_name, "response": data},
            source="tamarind_bio",
            source_id=f"run_pipeline/{job_name}",
        )
    except Exception as exc:
        return handle_error("tamarind_run_pipeline", exc)


# ===================================================================
# Job management
# ===================================================================


@mcp.tool()
async def tamarind_delete_job(
    job_name: str,
) -> dict[str, Any]:
    """Delete a job and its results from Tamarind Bio.

    Args:
        job_name: Name of the job to delete.
    """
    try:
        data = await _request("DELETE", "/delete-job", params={"jobName": job_name})
        return standard_response(
            summary=f"Job '{job_name}' deleted",
            raw_data={"job_name": job_name, "response": data},
            source="tamarind_bio",
            source_id=f"delete_job/{job_name}",
        )
    except Exception as exc:
        return handle_error("tamarind_delete_job", exc)


@mcp.tool()
async def tamarind_get_finetuned_models(
    model_type: str = "",
    limit: int = 50,
) -> dict[str, Any]:
    """List personal and organization fine-tuned models.

    Args:
        model_type: Filter by finetune type (optional).
        limit: Max results to return.
    """
    try:
        params: dict[str, Any] = {"limit": limit}
        if model_type:
            params["type"] = model_type

        data = await _request("GET", "/finetuned-models", params=params)
        models = data if isinstance(data, list) else data.get("models", data)
        return standard_response(
            summary=f"Found {len(models) if isinstance(models, list) else '?'} finetuned models",
            raw_data={"models": models},
            source="tamarind_bio",
            source_id="finetuned_models",
        )
    except Exception as exc:
        return handle_error("tamarind_get_finetuned_models", exc)


# ---------------------------------------------------------------------------
# Standalone server entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
