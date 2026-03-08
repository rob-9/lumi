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


# ---------------------------------------------------------------------------
# Division → Slack channel/expert routing
# ---------------------------------------------------------------------------

# Default routing table: maps division names to Slack channels and expert
# user IDs.  Override via LUMI_SLACK_ROUTING env var (JSON) or by passing
# a custom routing_table to the SlackNotifier constructor.
#
# Format: { "division_name": { "channel": "#channel", "experts": ["@user"] } }
DEFAULT_ROUTING_TABLE: dict[str, dict[str, Any]] = {
    "Target ID": {"channel": "", "experts": []},
    "Target Safety": {"channel": "", "experts": []},
    "Modality": {"channel": "", "experts": []},
    "Molecular Design": {"channel": "", "experts": []},
    "Clinical": {"channel": "", "experts": []},
    "CompBio": {"channel": "", "experts": []},
    "Experimental": {"channel": "", "experts": []},
    "Biosecurity": {"channel": "", "experts": []},
}


class SlackNotifier:
    """Sends Slack notifications when findings need human review.

    Supports two modes:
    1. Direct Slack API (if LUMI_SLACK_BOT_TOKEN is set)
    2. Slack MCP server (if available in the MCP bridge)

    Falls back to logging if neither is available.

    Smart routing: When a routing_table is configured, notifications are
    sent to the channel/experts mapped to the division that produced the
    flagged finding, rather than a single catch-all channel.
    """

    SLACK_API_BASE = "https://slack.com/api"

    def __init__(
        self,
        channel: str = "",
        bot_token: str = "",
        routing_table: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.channel = channel or os.environ.get("LUMI_SLACK_CHANNEL", "")
        self.bot_token = bot_token or os.environ.get("LUMI_SLACK_BOT_TOKEN", "")
        self._mcp_send: Any = None  # Will be set if MCP Slack server is wired

        # Load routing table from env or constructor
        self.routing_table = routing_table or self._load_routing_table()

    def _load_routing_table(self) -> dict[str, dict[str, Any]]:
        """Load routing table from LUMI_SLACK_ROUTING env var or defaults."""
        env_routing = os.environ.get("LUMI_SLACK_ROUTING", "")
        if env_routing:
            try:
                return json.loads(env_routing)
            except json.JSONDecodeError:
                logger.warning("[Slack] Invalid LUMI_SLACK_ROUTING JSON, using defaults")
        return dict(DEFAULT_ROUTING_TABLE)

    def _get_channel_for_division(self, division_name: str) -> str:
        """Resolve the Slack channel for a division.

        Falls back to the default channel if no specific mapping exists.
        """
        route = self.routing_table.get(division_name, {})
        return route.get("channel", "") or self.channel

    def _get_experts_for_division(self, division_name: str) -> list[str]:
        """Get Slack user IDs/mentions for a division's domain experts."""
        route = self.routing_table.get(division_name, {})
        return route.get("experts", [])

    def set_mcp_sender(self, send_fn: Any) -> None:
        """Wire an MCP Slack send function (from mcp_bridge)."""
        self._mcp_send = send_fn

    async def notify_review_needed(
        self,
        requests: list,  # list[ReviewRequest] — avoid circular import
        query_id: str = "",
    ) -> bool:
        """Send Slack messages listing findings that need expert review.

        Uses smart routing: if division-specific channels are configured,
        sends targeted notifications to each division's channel with
        expert mentions.  Otherwise falls back to the default channel.

        Returns True if at least one message was sent successfully.
        """
        if not requests:
            return True

        # Group requests by division for smart routing
        by_division: dict[str, list] = {}
        for req in requests:
            div = getattr(req, "division_name", "") or "General"
            by_division.setdefault(div, []).append(req)

        any_sent = False

        for division_name, div_requests in by_division.items():
            target_channel = self._get_channel_for_division(division_name)
            experts = self._get_experts_for_division(division_name)

            blocking = [r for r in div_requests if r.is_blocking]
            non_blocking = [r for r in div_requests if not r.is_blocking]

            blocks = self._build_review_blocks(
                blocking=blocking,
                non_blocking=non_blocking,
                query_id=query_id,
                division_name=division_name,
                experts=experts,
            )

            text_fallback = (
                f"🔬 Lumi HITL Alert [{division_name}]: "
                f"{len(div_requests)} finding(s) need expert review "
                f"({len(blocking)} blocking, {len(non_blocking)} advisory)"
            )

            sent = await self._send_message(
                text=text_fallback, blocks=blocks, channel_override=target_channel
            )
            if sent:
                any_sent = True

        return any_sent

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
        division_name: str = "",
        experts: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Build Slack Block Kit message for review requests."""
        blocks: list[dict[str, Any]] = []

        # Header
        header_text = "🔬 Lumi: Findings Need Expert Review"
        if division_name:
            header_text = f"🔬 Lumi [{division_name}]: Expert Review Needed"

        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": header_text,
            },
        })

        # Expert mentions
        expert_text = ""
        if experts:
            mentions = " ".join(f"<@{uid}>" for uid in experts)
            expert_text = f" | cc: {mentions}"

        # Context
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        f"Query ID: `{query_id}` | {len(blocking)} blocking | "
                        f"{len(non_blocking)} advisory{expert_text}"
                    ),
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
        channel_override: str = "",
    ) -> bool:
        """Send a message via the best available transport.

        Args:
            text: Fallback text for the message.
            blocks: Slack Block Kit blocks.
            channel_override: Send to this channel instead of the default.

        Tries in order: MCP Slack server → direct Slack API → log fallback.
        """
        target_channel = channel_override or self.channel

        # 1. Try MCP sender
        if self._mcp_send is not None:
            try:
                await self._mcp_send(
                    channel=target_channel,
                    text=text,
                    blocks=json.dumps(blocks) if blocks else None,
                )
                logger.info("[Slack] Sent via MCP to %s: %s", target_channel, text[:100])
                return True
            except Exception as exc:
                logger.warning("[Slack] MCP send failed: %s", exc)

        # 2. Try direct Slack API
        if self.bot_token and target_channel and _HAS_HTTPX:
            try:
                return await self._send_via_api(text, blocks, channel_override=target_channel)
            except Exception as exc:
                logger.warning("[Slack] API send failed: %s", exc)

        # 3. Fallback to logging
        logger.info("[Slack] (no transport configured) [%s] Message: %s", target_channel, text)
        if blocks:
            logger.info("[Slack] Blocks: %s", json.dumps(blocks, indent=2)[:500])
        return False

    async def _send_via_api(
        self,
        text: str,
        blocks: list[dict[str, Any]] | None = None,
        channel_override: str = "",
    ) -> bool:
        """Send message directly via Slack Web API."""
        if not _HAS_HTTPX:
            return False

        payload: dict[str, Any] = {
            "channel": channel_override or self.channel,
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
