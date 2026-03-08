"""Living Document — evolving research narrative layer.

Sits on top of the WorldModel and maintains a human-readable,
continuously-updated research document that agents can read/write.
"""

from src.orchestrator.living_document.document import (
    DocumentSection,
    DocumentVersion,
    LivingDocument,
)
from src.orchestrator.living_document.manager import DocumentManager

__all__ = [
    "DocumentSection",
    "DocumentVersion",
    "LivingDocument",
    "DocumentManager",
]
