"""Slack Notifier — sends alerts to domain experts when findings need review.

Uses the Slack MCP server (or direct Slack API via webhook/bot token) to
post structured messages to a configured channel when the HITL router
flags low-confidence findings.

Configuration:
    Set ``LUMI_SLACK_CHANNEL`` env var to the target channel ID.
    Set ``LUMI_SLACK_BOT_TOKEN`` env var for API auth (or rely on MCP).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger("lumi.hitl.slack")

# Try to import httpx for direct Slack API calls
try:
    import httpx

    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False


class SlackNotifier:
    """Sends Slack notifications when findings need human review.

    Supports two modes:
    1. Direct Slack API (if LUMI_SLACK_BOT_TOKEN is set)
    2. Slack MCP server (if available in the MCP bridge)

    Falls back to logging if neither is available.
    """

    SLACK_API_BASE = "https://slack.com/api"

    def __init__(
        self,
        channel: str = "",
        bot_token: str = "",
    ) -> None:
        self.channel = channel or os.environ.get("LUMI_SLACK_CHANNEL", "")
        self.bot_token = bot_token or os.environ.get("LUMI_SLACK_BOT_TOKEN", "")
        self._mcp_send: Any = None  # Will be set if MCP Slack server is wired

    def set_mcp_sender(self, send_fn: Any) -> None:
        """Wire an MCP Slack send function (from mcp_bridge)."""
        self._mcp_send = send_fn

    async def notify_review_needed(
        self,
        requests: list,  # list[ReviewRequest] — avoid circular import
        query_id: str = "",
    ) -> bool:
        """Send a Slack message listing findings that need expert review.

        Returns True if the message was sent successfully.
        """
        if not requests:
            return True

        # Build the message
        blocking = [r for r in requests if r.is_blocking]
        non_blocking = [r for r in requests if not r.is_blocking]

        blocks = self._build_review_blocks(
            blocking=blocking,
            non_blocking=non_blocking,
            query_id=query_id,
        )

        text_fallback = (
            f"🔬 Lumi HITL Alert: {len(requests)} finding(s) need expert review "
            f"({len(blocking)} blocking, {len(non_blocking)} advisory)"
        )

        return await self._send_message(text=text_fallback, blocks=blocks)

    async def notify_timeout(
        self,
        requests: list,
        query_id: str = "",
    ) -> bool:
        """Notify that soft-flagged reviews timed out and findings were
        included with caveats."""
        if not requests:
            return True

        text = (
            f"⏰ Lumi HITL: {len(requests)} finding(s) from query `{query_id}` "
            f"timed out waiting for review. They have been included in the "
            f"report with confidence caveats."
        )
        return await self._send_message(text=text)

    async def notify_pipeline_blocked(
        self,
        query_id: str,
        blocking_count: int,
    ) -> bool:
        """Notify that the pipeline is blocked waiting for mandatory reviews."""
        text = (
            f"🚨 Lumi Pipeline BLOCKED: Query `{query_id}` cannot proceed. "
            f"{blocking_count} finding(s) require mandatory expert review. "
            f"Please review and respond to unblock."
        )
        return await self._send_message(text=text)

    # ------------------------------------------------------------------
    # Message construction
    # ------------------------------------------------------------------

    def _build_review_blocks(
        self,
        blocking: list,
        non_blocking: list,
        query_id: str,
    ) -> list[dict[str, Any]]:
        """Build Slack Block Kit message for review requests."""
        blocks: list[dict[str, Any]] = []

        # Header
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🔬 Lumi: Findings Need Expert Review",
            },
        })

        # Context
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Query ID: `{query_id}` | {len(blocking)} blocking | {len(non_blocking)} advisory",
                }
            ],
        })

        blocks.append({"type": "divider"})

        # Blocking findings
        if blocking:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🚨 *BLOCKING — Pipeline paused until reviewed:*",
                },
            })
            for req in blocking[:10]:  # Cap at 10 to stay within Slack limits
                conf_score = req.claim.confidence.score
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*[{req.division_name}]* `{conf_score:.0%}` confidence\n"
                            f">{req.claim.claim_text[:300]}\n"
                            f"_Reason: {req.reason}_\n"
                            f"ID: `{req.request_id}`"
                        ),
                    },
                })

        # Non-blocking findings
        if non_blocking:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "⚠️ *ADVISORY — Will proceed with caveat if not reviewed:*",
                },
            })
            for req in non_blocking[:10]:
                conf_score = req.claim.confidence.score
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*[{req.division_name}]* `{conf_score:.0%}` confidence\n"
                            f">{req.claim.claim_text[:300]}\n"
                            f"ID: `{req.request_id}`"
                        ),
                    },
                })

        blocks.append({"type": "divider"})

        # Instructions
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "💡 *To respond:* Reply in thread with the request ID and your verdict:\n"
                    "• `APPROVE <request_id>` — finding is acceptable\n"
                    "• `REVISE <request_id> <your revision>` — provide corrected finding\n"
                    "• `REJECT <request_id>` — exclude from report"
                ),
            },
        })

        return blocks

    # ------------------------------------------------------------------
    # Transport layer
    # ------------------------------------------------------------------

    async def _send_message(
        self,
        text: str,
        blocks: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Send a message via the best available transport.

        Tries in order: MCP Slack server → direct Slack API → log fallback.
        """
        # 1. Try MCP sender
        if self._mcp_send is not None:
            try:
                await self._mcp_send(
                    channel=self.channel,
                    text=text,
                    blocks=json.dumps(blocks) if blocks else None,
                )
                logger.info("[Slack] Sent via MCP: %s", text[:100])
                return True
            except Exception as exc:
                logger.warning("[Slack] MCP send failed: %s", exc)

        # 2. Try direct Slack API
        if self.bot_token and self.channel and _HAS_HTTPX:
            try:
                return await self._send_via_api(text, blocks)
            except Exception as exc:
                logger.warning("[Slack] API send failed: %s", exc)

        # 3. Fallback to logging
        logger.info("[Slack] (no transport configured) Message: %s", text)
        if blocks:
            logger.info("[Slack] Blocks: %s", json.dumps(blocks, indent=2)[:500])
        return False

    async def _send_via_api(
        self,
        text: str,
        blocks: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Send message directly via Slack Web API."""
        if not _HAS_HTTPX:
            return False

        payload: dict[str, Any] = {
            "channel": self.channel,
            "text": text,
        }
        if blocks:
            payload["blocks"] = blocks

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.SLACK_API_BASE}/chat.postMessage",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            data = resp.json()
            if data.get("ok"):
                logger.info("[Slack] Message sent to %s", self.channel)
                return True
            else:
                logger.error("[Slack] API error: %s", data.get("error", "unknown"))
                return False
