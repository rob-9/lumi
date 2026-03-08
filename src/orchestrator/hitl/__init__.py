"""Human-in-the-Loop (HITL) Routing System.

Routes low-confidence findings to human domain experts before they
enter final reports.  Integrates with Slack for notifications and
feedback collection.

Components:
    - ConfidenceRouter: classifies claims and creates review requests
    - ReviewQueue: in-memory queue of pending/resolved review requests
    - SlackNotifier: sends Block Kit messages to Slack (outbound)
    - SlackListener: polls Slack threads for expert responses (inbound)
"""

from src.orchestrator.hitl.router import ConfidenceRouter, HITLConfig
from src.orchestrator.hitl.review_queue import ReviewQueue, ReviewRequest, ReviewStatus
from src.orchestrator.hitl.slack_listener import SlackListener
from src.orchestrator.hitl.slack_notifier import SlackNotifier

__all__ = [
    "ConfidenceRouter",
    "HITLConfig",
    "ReviewQueue",
    "ReviewRequest",
    "ReviewStatus",
    "SlackListener",
    "SlackNotifier",
]
