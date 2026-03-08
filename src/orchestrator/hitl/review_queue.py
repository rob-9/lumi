"""Review Queue — tracks findings awaiting human expert input.

Thread-safe async queue that holds ``ReviewRequest`` objects.  External
systems (Slack bot, Streamlit UI, API endpoint) resolve requests by
calling ``resolve_request()`` with expert feedback.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from src.utils.types import Claim

logger = logging.getLogger("lumi.hitl.queue")


class ReviewStatus(str, Enum):
    """Lifecycle of a review request."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REVISED = "REVISED"
    REJECTED = "REJECTED"
    SKIPPED = "SKIPPED"


@dataclass
class ReviewRequest:
    """A single finding awaiting human expert review.

    Attributes:
        request_id: Unique identifier for this review request.
        claim: The scientific claim under review.
        division_name: Which division produced this claim.
        query_id: The pipeline query this belongs to.
        is_blocking: If True, the pipeline will not proceed to synthesis
            until this request is resolved.
        reason: Why this finding was flagged for review.
        status: Current review status.
        feedback: Expert's feedback text (populated on resolution).
        reviewer: Identifier of the expert who reviewed (e.g. Slack user ID).
        created_at: When the request was created.
        resolved_at: When the request was resolved.
    """

    request_id: str = field(default_factory=lambda: f"review_{uuid.uuid4().hex[:12]}")
    claim: Claim = field(default_factory=lambda: Claim(
        claim_text="", confidence=None, agent_id=""  # type: ignore[arg-type]
    ))
    division_name: str = ""
    query_id: str = ""
    is_blocking: bool = False
    reason: str = ""
    status: ReviewStatus = ReviewStatus.PENDING
    feedback: Optional[str] = None
    reviewer: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None


class ReviewQueue:
    """In-memory queue of findings awaiting human review.

    Provides thread-safe access for concurrent pipeline + UI/Slack
    interactions.  For production, this could be backed by Redis or
    a database table — the interface stays the same.
    """

    def __init__(self) -> None:
        self._requests: dict[str, ReviewRequest] = {}
        self._lock = asyncio.Lock()

    def add_request(
        self,
        claim: Claim,
        division_name: str = "",
        query_id: str = "",
        is_blocking: bool = False,
        reason: str = "",
    ) -> ReviewRequest:
        """Create and enqueue a new review request.

        Returns the created ``ReviewRequest`` (caller keeps a reference
        to poll its status).
        """
        req = ReviewRequest(
            claim=claim,
            division_name=division_name,
            query_id=query_id,
            is_blocking=is_blocking,
            reason=reason,
        )
        self._requests[req.request_id] = req
        logger.info(
            "[ReviewQueue] Added %s (blocking=%s): %s",
            req.request_id,
            req.is_blocking,
            claim.claim_text[:80],
        )
        return req

    async def resolve_request(
        self,
        request_id: str,
        status: ReviewStatus,
        feedback: str = "",
        reviewer: str = "",
    ) -> bool:
        """Resolve a pending review request with expert feedback.

        Args:
            request_id: The review request to resolve.
            status: Expert's verdict (APPROVED, REVISED, REJECTED, SKIPPED).
            feedback: Expert's feedback text or revised claim text.
            reviewer: Identifier of the reviewing expert.

        Returns:
            True if the request was found and resolved, False otherwise.
        """
        async with self._lock:
            req = self._requests.get(request_id)
            if req is None:
                logger.warning("[ReviewQueue] Request %s not found", request_id)
                return False

            if req.status != ReviewStatus.PENDING:
                logger.warning(
                    "[ReviewQueue] Request %s already resolved as %s",
                    request_id,
                    req.status.value,
                )
                return False

            req.status = status
            req.feedback = feedback
            req.reviewer = reviewer
            req.resolved_at = datetime.now(timezone.utc)

            logger.info(
                "[ReviewQueue] Resolved %s as %s by %s",
                request_id,
                status.value,
                reviewer or "unknown",
            )
            return True

    def get_pending(self, query_id: str = "") -> list[ReviewRequest]:
        """Get all pending review requests, optionally filtered by query."""
        results = []
        for req in self._requests.values():
            if req.status != ReviewStatus.PENDING:
                continue
            if query_id and req.query_id != query_id:
                continue
            results.append(req)
        return results

    def get_all(self, query_id: str = "") -> list[ReviewRequest]:
        """Get all review requests for a query."""
        if not query_id:
            return list(self._requests.values())
        return [r for r in self._requests.values() if r.query_id == query_id]

    def get_request(self, request_id: str) -> ReviewRequest | None:
        """Look up a specific request by ID."""
        return self._requests.get(request_id)

    @property
    def pending_count(self) -> int:
        return sum(1 for r in self._requests.values() if r.status == ReviewStatus.PENDING)

    @property
    def blocking_count(self) -> int:
        return sum(
            1
            for r in self._requests.values()
            if r.status == ReviewStatus.PENDING and r.is_blocking
        )
