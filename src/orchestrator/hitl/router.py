"""Confidence Router — evaluates findings and decides what needs human review.

The router sits between the Review Panel (Phase 7) and Synthesis (Phase 9).
It inspects every claim's confidence score and routes low-confidence findings
to the human review queue, optionally pausing the pipeline until feedback
arrives.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from src.utils.types import (
    Claim,
    DivisionReport,
)

from .review_queue import ReviewQueue, ReviewRequest, ReviewStatus
from .slack_notifier import SlackNotifier

logger = logging.getLogger("lumi.hitl.router")


@dataclass
class HITLConfig:
    """Configuration for human-in-the-loop routing thresholds.

    Attributes:
        hard_threshold: Findings below this MUST have human review before
            inclusion in the final report.  Pipeline blocks on these.
        soft_threshold: Findings below this are sent for review but the
            pipeline continues.  If no response arrives within
            ``soft_timeout_seconds``, findings are included with a caveat.
        auto_threshold: Findings above this are included automatically.
            Findings between soft and auto are flagged for optional review.
        soft_timeout_seconds: How long to wait for expert response on
            soft-flagged findings before proceeding with a caveat.
        slack_channel: Slack channel ID or name for notifications.
        enabled: Master switch for HITL routing.
    """

    hard_threshold: float = 0.3
    soft_threshold: float = 0.5
    auto_threshold: float = 0.7
    soft_timeout_seconds: float = 300.0  # 5 minutes
    slack_channel: str = ""
    enabled: bool = True


class ConfidenceRouter:
    """Evaluates claims from division reports and routes low-confidence
    findings to the human review queue.

    Integrates with :class:`SlackNotifier` to alert domain experts and
    with :class:`ReviewQueue` to track pending reviews.
    """

    def __init__(
        self,
        config: HITLConfig | None = None,
        review_queue: ReviewQueue | None = None,
        slack_notifier: SlackNotifier | None = None,
    ) -> None:
        self.config = config or HITLConfig()
        self.queue = review_queue or ReviewQueue()
        self.notifier = slack_notifier or SlackNotifier(
            channel=self.config.slack_channel,
        )

    async def evaluate_reports(
        self,
        reports: list[DivisionReport],
        query_id: str = "",
    ) -> HITLResult:
        """Scan all division reports for low-confidence findings.

        Returns an ``HITLResult`` containing:
        - claims that passed automatically
        - claims that are blocked pending human review
        - claims included with caveats (soft threshold, timed out)

        This method will **block** on hard-threshold findings until
        human feedback is received (or the review is explicitly skipped
        by an admin).
        """
        if not self.config.enabled:
            logger.info("[HITL] Routing disabled — all findings pass through")
            return HITLResult(
                auto_passed=self._extract_all_claims(reports),
                blocked=[],
                caveated=[],
                human_feedback={},
            )

        auto_passed: list[Claim] = []
        soft_flagged: list[tuple[Claim, str]] = []  # (claim, division_name)
        hard_flagged: list[tuple[Claim, str]] = []

        # Classify every claim
        for report in reports:
            for specialist_result in report.specialist_results:
                for claim in specialist_result.findings:
                    score = claim.confidence.score
                    if score >= self.config.auto_threshold:
                        auto_passed.append(claim)
                    elif score >= self.config.soft_threshold:
                        # Between soft and auto — optional review
                        auto_passed.append(claim)
                    elif score >= self.config.hard_threshold:
                        soft_flagged.append((claim, report.division_name))
                    else:
                        hard_flagged.append((claim, report.division_name))

        # Also check division-level confidence
        for report in reports:
            if report.confidence.score < self.config.hard_threshold:
                logger.warning(
                    "[HITL] Division '%s' overall confidence %.2f below hard threshold",
                    report.division_name,
                    report.confidence.score,
                )

        total_flagged = len(soft_flagged) + len(hard_flagged)
        logger.info(
            "[HITL] Routing: %d auto-passed, %d soft-flagged, %d hard-flagged",
            len(auto_passed),
            len(soft_flagged),
            len(hard_flagged),
        )

        if total_flagged == 0:
            return HITLResult(
                auto_passed=auto_passed,
                blocked=[],
                caveated=[],
                human_feedback={},
            )

        # Create review requests and notify
        human_feedback: dict[str, str] = {}

        # Handle hard-flagged: create requests, notify, BLOCK
        hard_requests: list[ReviewRequest] = []
        for claim, div_name in hard_flagged:
            req = self.queue.add_request(
                claim=claim,
                division_name=div_name,
                query_id=query_id,
                is_blocking=True,
                reason=f"Confidence {claim.confidence.score:.0%} below hard threshold ({self.config.hard_threshold:.0%})",
            )
            hard_requests.append(req)

        # Handle soft-flagged: create requests, notify, wait with timeout
        soft_requests: list[ReviewRequest] = []
        for claim, div_name in soft_flagged:
            req = self.queue.add_request(
                claim=claim,
                division_name=div_name,
                query_id=query_id,
                is_blocking=False,
                reason=f"Confidence {claim.confidence.score:.0%} below soft threshold ({self.config.soft_threshold:.0%})",
            )
            soft_requests.append(req)

        # Send Slack notifications for all flagged findings
        all_requests = hard_requests + soft_requests
        if all_requests:
            await self.notifier.notify_review_needed(
                requests=all_requests,
                query_id=query_id,
            )

        # Block on hard-flagged findings
        blocked_claims: list[Claim] = []
        if hard_requests:
            logger.info(
                "[HITL] BLOCKING pipeline — %d findings require human review",
                len(hard_requests),
            )
            await self._wait_for_reviews(
                hard_requests, timeout=None  # No timeout for hard blocks
            )
            for req in hard_requests:
                if req.status == ReviewStatus.APPROVED:
                    auto_passed.append(req.claim)
                    if req.feedback:
                        human_feedback[req.request_id] = req.feedback
                elif req.status == ReviewStatus.REVISED:
                    # Expert provided a revised claim — use their version
                    auto_passed.append(req.claim)
                    human_feedback[req.request_id] = req.feedback or ""
                else:
                    # Rejected or still pending — exclude from report
                    blocked_claims.append(req.claim)

        # Wait on soft-flagged with timeout
        caveated_claims: list[Claim] = []
        if soft_requests:
            logger.info(
                "[HITL] Waiting %.0fs for soft-flagged reviews...",
                self.config.soft_timeout_seconds,
            )
            await self._wait_for_reviews(
                soft_requests, timeout=self.config.soft_timeout_seconds
            )
            for req in soft_requests:
                if req.status == ReviewStatus.APPROVED:
                    auto_passed.append(req.claim)
                    if req.feedback:
                        human_feedback[req.request_id] = req.feedback
                elif req.status == ReviewStatus.REVISED:
                    auto_passed.append(req.claim)
                    human_feedback[req.request_id] = req.feedback or ""
                elif req.status == ReviewStatus.REJECTED:
                    blocked_claims.append(req.claim)
                else:
                    # Timed out — include with caveat
                    caveated_claims.append(req.claim)

        if caveated_claims:
            await self.notifier.notify_timeout(
                requests=[r for r in soft_requests if r.status == ReviewStatus.PENDING],
                query_id=query_id,
            )

        return HITLResult(
            auto_passed=auto_passed,
            blocked=blocked_claims,
            caveated=caveated_claims,
            human_feedback=human_feedback,
        )

    async def _wait_for_reviews(
        self,
        requests: list[ReviewRequest],
        timeout: float | None,
    ) -> None:
        """Poll the review queue until all requests are resolved or timeout."""
        if not requests:
            return

        poll_interval = 2.0  # seconds
        elapsed = 0.0

        while True:
            all_resolved = all(
                r.status != ReviewStatus.PENDING for r in requests
            )
            if all_resolved:
                return

            if timeout is not None and elapsed >= timeout:
                logger.info("[HITL] Timeout reached after %.0fs", elapsed)
                return

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            # Adaptive polling: slow down after initial burst
            if elapsed > 30:
                poll_interval = min(poll_interval * 1.5, 15.0)

    @staticmethod
    def _extract_all_claims(reports: list[DivisionReport]) -> list[Claim]:
        """Extract all claims from division reports."""
        claims: list[Claim] = []
        for report in reports:
            for sr in report.specialist_results:
                claims.extend(sr.findings)
        return claims


@dataclass
class HITLResult:
    """Result of HITL routing evaluation.

    Attributes:
        auto_passed: Claims that passed confidence thresholds automatically.
        blocked: Claims rejected or still awaiting mandatory human review.
        caveated: Claims included despite low confidence (timed out waiting
            for review).  These get a caveat in the final report.
        human_feedback: Map of request_id -> expert feedback text for
            findings that received human input.
    """

    auto_passed: list[Claim] = field(default_factory=list)
    blocked: list[Claim] = field(default_factory=list)
    caveated: list[Claim] = field(default_factory=list)
    human_feedback: dict[str, str] = field(default_factory=dict)

    @property
    def total_reviewed(self) -> int:
        return len(self.auto_passed) + len(self.blocked) + len(self.caveated)

    @property
    def has_blocked(self) -> bool:
        return len(self.blocked) > 0

    def summary(self) -> str:
        """Human-readable summary of routing decisions."""
        lines = [
            f"HITL Routing Summary: {self.total_reviewed} findings evaluated",
            f"  Auto-passed:  {len(self.auto_passed)}",
            f"  Blocked:      {len(self.blocked)}",
            f"  With caveats: {len(self.caveated)}",
            f"  Human input:  {len(self.human_feedback)} responses received",
        ]
        return "\n".join(lines)
