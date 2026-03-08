"""Slack Listener — receives expert responses and resolves review requests.

This is the **return path** for the HITL system.  The SlackNotifier sends
messages *to* Slack; the SlackListener reads replies *from* Slack and
calls ``ReviewQueue.resolve_request()`` to unblock the pipeline.

It works by polling for new messages in threads where HITL notifications
were posted, parsing expert commands like::

    APPROVE review_abc123
    REVISE review_abc123 The actual mechanism is X not Y
    REJECT review_abc123

Two transport modes (matching SlackNotifier):
1. Direct Slack API (``conversations.replies``) — needs bot token
2. MCP Slack tools — if wired via ``set_mcp_reader()``

Runs as a background ``asyncio.Task`` alongside the pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Any, Callable

from .review_queue import ReviewQueue, ReviewStatus

logger = logging.getLogger("lumi.hitl.slack_listener")

# Try to import httpx for direct Slack API calls
try:
    import httpx

    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False

# ---------------------------------------------------------------------------
# Command parsing
# ---------------------------------------------------------------------------

# Matches: APPROVE review_abc123
# Matches: REVISE review_abc123 some revised text here
# Matches: REJECT review_abc123
_COMMAND_RE = re.compile(
    r"^\s*(APPROVE|REVISE|REJECT)\s+(review_[a-f0-9]+)(?:\s+(.+))?\s*$",
    re.IGNORECASE | re.DOTALL,
)

_STATUS_MAP = {
    "APPROVE": ReviewStatus.APPROVED,
    "REVISE": ReviewStatus.REVISED,
    "REJECT": ReviewStatus.REJECTED,
}


class SlackListener:
    """Polls Slack for expert responses to HITL review requests.

    Monitors threads where notifications were posted, parses expert
    commands, and resolves the corresponding ``ReviewRequest`` objects
    in the ``ReviewQueue``.

    Usage::

        listener = SlackListener(review_queue=queue)
        # Track the thread where we posted an HITL notification
        listener.track_thread(channel="C123", thread_ts="1234567890.123456")
        # Start listening (runs as background task)
        task = listener.start()
        # ... pipeline waits for reviews ...
        # Stop when done
        listener.stop()
    """

    SLACK_API_BASE = "https://slack.com/api"

    def __init__(
        self,
        review_queue: ReviewQueue,
        bot_token: str = "",
        poll_interval: float = 3.0,
    ) -> None:
        self.queue = review_queue
        self.bot_token = bot_token or os.environ.get("LUMI_SLACK_BOT_TOKEN", "")
        self.poll_interval = poll_interval

        # Threads we're monitoring: list of (channel, thread_ts)
        self._tracked_threads: list[tuple[str, str]] = []
        # Message timestamps we've already processed (avoid double-processing)
        self._seen_ts: set[str] = set()
        # Background task handle
        self._task: asyncio.Task | None = None
        self._running = False

        # Optional MCP reader function
        self._mcp_read: Callable | None = None

    def set_mcp_reader(self, read_fn: Callable) -> None:
        """Wire an MCP Slack read function (from mcp_bridge)."""
        self._mcp_read = read_fn

    def track_thread(self, channel: str, thread_ts: str) -> None:
        """Register a Slack thread to monitor for expert responses.

        Called by the SlackNotifier after posting an HITL notification,
        passing back the channel and thread_ts of the posted message.
        """
        if (channel, thread_ts) not in self._tracked_threads:
            self._tracked_threads.append((channel, thread_ts))
            logger.info(
                "[SlackListener] Tracking thread %s in channel %s",
                thread_ts,
                channel,
            )

    def start(self) -> asyncio.Task:
        """Start the background polling loop.

        Returns the ``asyncio.Task`` so the caller can await or cancel it.
        """
        if self._task is not None and not self._task.done():
            logger.warning("[SlackListener] Already running")
            return self._task

        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("[SlackListener] Started polling (interval=%.1fs)", self.poll_interval)
        return self._task

    def stop(self) -> None:
        """Signal the polling loop to stop."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("[SlackListener] Stopped")

    @property
    def is_running(self) -> bool:
        return self._running and self._task is not None and not self._task.done()

    # ------------------------------------------------------------------
    # Background polling loop
    # ------------------------------------------------------------------

    async def _poll_loop(self) -> None:
        """Continuously poll tracked Slack threads for new messages."""
        while self._running:
            try:
                # Stop if no pending reviews remain
                if self.queue.pending_count == 0:
                    logger.info("[SlackListener] No pending reviews — stopping")
                    self._running = False
                    return

                for channel, thread_ts in list(self._tracked_threads):
                    messages = await self._fetch_thread_replies(channel, thread_ts)
                    for msg in messages:
                        await self._process_message(msg)

            except asyncio.CancelledError:
                logger.info("[SlackListener] Poll loop cancelled")
                return
            except Exception as exc:
                logger.error("[SlackListener] Poll error: %s", exc)

            await asyncio.sleep(self.poll_interval)

    async def _process_message(self, msg: dict) -> None:
        """Parse a Slack message and resolve matching review requests."""
        ts = msg.get("ts", "")
        if ts in self._seen_ts:
            return

        text = msg.get("text", "").strip()
        user = msg.get("user", "")

        # Skip bot messages (our own notifications)
        if msg.get("bot_id") or msg.get("subtype") == "bot_message":
            self._seen_ts.add(ts)
            return

        match = _COMMAND_RE.match(text)
        if not match:
            # Not a command — ignore
            self._seen_ts.add(ts)
            return

        action = match.group(1).upper()
        request_id = match.group(2)
        feedback = (match.group(3) or "").strip()

        status = _STATUS_MAP.get(action)
        if status is None:
            self._seen_ts.add(ts)
            return

        # Look up the request
        req = self.queue.get_request(request_id)
        if req is None:
            logger.warning(
                "[SlackListener] Unknown request_id '%s' from user %s",
                request_id,
                user,
            )
            self._seen_ts.add(ts)
            return

        # Resolve the request
        resolved = await self.queue.resolve_request(
            request_id=request_id,
            status=status,
            feedback=feedback,
            reviewer=f"slack:{user}",
        )

        if resolved:
            logger.info(
                "[SlackListener] Resolved %s as %s by slack:%s",
                request_id,
                status.value,
                user,
            )
        else:
            logger.warning(
                "[SlackListener] Failed to resolve %s (already resolved?)",
                request_id,
            )

        self._seen_ts.add(ts)

    # ------------------------------------------------------------------
    # Slack API: fetch thread replies
    # ------------------------------------------------------------------

    async def _fetch_thread_replies(
        self, channel: str, thread_ts: str
    ) -> list[dict]:
        """Fetch replies in a Slack thread.

        Tries MCP reader first, then direct API, then returns empty.
        """
        # 1. Try MCP reader
        if self._mcp_read is not None:
            try:
                result = await self._mcp_read(
                    channel=channel,
                    thread_ts=thread_ts,
                )
                if isinstance(result, list):
                    return result
                if isinstance(result, dict):
                    return result.get("messages", [])
            except Exception as exc:
                logger.warning("[SlackListener] MCP read failed: %s", exc)

        # 2. Try direct Slack API
        if self.bot_token and _HAS_HTTPX:
            try:
                return await self._fetch_via_api(channel, thread_ts)
            except Exception as exc:
                logger.warning("[SlackListener] API fetch failed: %s", exc)

        return []

    async def _fetch_via_api(
        self, channel: str, thread_ts: str
    ) -> list[dict]:
        """Fetch thread replies via Slack Web API."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.SLACK_API_BASE}/conversations.replies",
                params={
                    "channel": channel,
                    "ts": thread_ts,
                    "limit": 50,
                },
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                },
                timeout=10.0,
            )
            data = resp.json()
            if data.get("ok"):
                # First message is the parent — skip it, return only replies
                messages = data.get("messages", [])
                return messages[1:] if len(messages) > 1 else []
            else:
                logger.error(
                    "[SlackListener] API error: %s",
                    data.get("error", "unknown"),
                )
                return []
