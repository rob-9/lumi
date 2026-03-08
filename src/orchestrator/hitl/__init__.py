"""
Human-in-the-Loop (HITL) Routing System.

Routes low-confidence findings to human domain experts before they
enter final reports. This is a core differentiator of Lumi — the system
knows what it doesn't know and escalates accordingly.

Key components:
- ConfidenceRouter: Evaluates findings against thresholds, flags for review
- ReviewQueue: Async queue of findings awaiting human expert input
- ExpertFeedbackIngester: Accepts expert feedback, re-injects into pipeline
- NotificationDispatcher: Alerts experts when findings need review

Workflow:
1. After Phase 7 (Review), findings below confidence threshold are flagged
2. ConfidenceRouter creates ReviewRequest objects with context
3. ReviewQueue holds requests; NotificationDispatcher alerts experts
4. Pipeline pauses on flagged findings (other work continues)
5. Expert submits feedback via UI or API
6. ExpertFeedbackIngester validates and injects feedback
7. Pipeline resumes with expert-augmented findings
8. Provenance chain records human contribution

Thresholds (configurable):
- HARD_THRESHOLD: 0.3 — always route to human, block report
- SOFT_THRESHOLD: 0.5 — route to human, include with caveat if no response
- AUTO_THRESHOLD: 0.7 — include automatically, flag for optional review
"""
