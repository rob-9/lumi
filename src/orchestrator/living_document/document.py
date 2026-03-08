"""Living Document data structures.

The document is an append-only versioned narrative.  Each version
captures the full state of all sections at a point in time.  Agents
write to sections; humans read the rendered narrative.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SectionType(str, Enum):
    """Standard section types for the research narrative."""

    EXECUTIVE_SUMMARY = "executive_summary"
    BACKGROUND = "background"
    HYPOTHESIS = "hypothesis"
    METHODS = "methods"
    FINDINGS = "findings"
    EVIDENCE = "evidence"
    CONTRADICTIONS = "contradictions"
    OPEN_QUESTIONS = "open_questions"
    RISK_ASSESSMENT = "risk_assessment"
    RECOMMENDATIONS = "recommendations"
    EXPERIMENTAL_PLAN = "experimental_plan"
    HUMAN_FEEDBACK = "human_feedback"
    APPENDIX = "appendix"


@dataclass
class DocumentSection:
    """A single section of the living document.

    Attributes:
        section_id: Unique identifier.
        section_type: Categorization of this section.
        title: Human-readable title.
        content: Markdown-formatted narrative text.
        author: Agent ID or human identifier who wrote this.
        confidence_score: Overall confidence of claims in this section.
        source_claims: Claim IDs that back statements in this section.
        source_divisions: Divisions that contributed to this section.
        created_at: When this section was first created.
        updated_at: When this section was last modified.
    """

    section_id: str = field(default_factory=lambda: f"sec_{uuid.uuid4().hex[:10]}")
    section_type: SectionType = SectionType.FINDINGS
    title: str = ""
    content: str = ""
    author: str = ""
    confidence_score: float = 0.0
    source_claims: list[str] = field(default_factory=list)
    source_divisions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update(self, content: str, author: str = "") -> None:
        """Update this section's content."""
        self.content = content
        self.updated_at = datetime.now(timezone.utc)
        if author:
            self.author = author


@dataclass
class DocumentVersion:
    """A snapshot of the entire document at a point in time.

    Append-only: each pipeline phase or human edit creates a new version.
    """

    version_id: str = field(default_factory=lambda: f"v_{uuid.uuid4().hex[:8]}")
    version_number: int = 1
    sections: list[DocumentSection] = field(default_factory=list)
    query_id: str = ""
    trigger: str = ""  # What caused this version (e.g. "phase_5_complete", "human_edit")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    summary_of_changes: str = ""

    def get_section(self, section_type: SectionType) -> DocumentSection | None:
        """Find a section by type."""
        for s in self.sections:
            if s.section_type == section_type:
                return s
        return None

    def get_sections_by_type(self, section_type: SectionType) -> list[DocumentSection]:
        """Get all sections of a given type (there can be multiple FINDINGS, etc.)."""
        return [s for s in self.sections if s.section_type == section_type]


class LivingDocument:
    """The evolving research narrative.

    Maintains an ordered history of ``DocumentVersion`` snapshots.
    Agents read the latest version as context; humans see the full
    history with diffs.
    """

    def __init__(self, query_id: str = "") -> None:
        self.query_id = query_id
        self._versions: list[DocumentVersion] = []

    @property
    def current(self) -> DocumentVersion | None:
        """The latest version, or None if empty."""
        return self._versions[-1] if self._versions else None

    @property
    def version_count(self) -> int:
        return len(self._versions)

    @property
    def versions(self) -> list[DocumentVersion]:
        return list(self._versions)

    def create_version(
        self,
        sections: list[DocumentSection],
        trigger: str = "",
        summary: str = "",
    ) -> DocumentVersion:
        """Create a new version with the given sections.

        Does NOT copy forward old sections — caller is responsible for
        including any sections they want to preserve.
        """
        version = DocumentVersion(
            version_number=len(self._versions) + 1,
            sections=sections,
            query_id=self.query_id,
            trigger=trigger,
            summary_of_changes=summary,
        )
        self._versions.append(version)
        return version

    def evolve(
        self,
        updates: dict[SectionType, str],
        author: str = "",
        trigger: str = "",
    ) -> DocumentVersion:
        """Create a new version by evolving the current one.

        Copies all sections from the current version, applies updates
        to matching section types, and creates the new version.

        Args:
            updates: Map of section_type -> new content.
            author: Who is making this update.
            trigger: What caused this evolution.

        Returns:
            The newly created ``DocumentVersion``.
        """
        current = self.current
        if current is None:
            # First version — create sections from scratch
            sections = []
            for stype, content in updates.items():
                sections.append(
                    DocumentSection(
                        section_type=stype,
                        title=stype.value.replace("_", " ").title(),
                        content=content,
                        author=author,
                    )
                )
            return self.create_version(
                sections=sections,
                trigger=trigger or "initial_creation",
                summary=f"Created {len(sections)} sections",
            )

        # Copy forward current sections
        new_sections: list[DocumentSection] = []
        updated_types: set[SectionType] = set()

        for old_sec in current.sections:
            if old_sec.section_type in updates:
                # Update existing section
                new_sec = DocumentSection(
                    section_id=old_sec.section_id,
                    section_type=old_sec.section_type,
                    title=old_sec.title,
                    content=updates[old_sec.section_type],
                    author=author or old_sec.author,
                    confidence_score=old_sec.confidence_score,
                    source_claims=list(old_sec.source_claims),
                    source_divisions=list(old_sec.source_divisions),
                    created_at=old_sec.created_at,
                )
                new_sections.append(new_sec)
                updated_types.add(old_sec.section_type)
            else:
                # Carry forward unchanged
                new_sections.append(old_sec)

        # Add new sections for types not already present
        for stype, content in updates.items():
            if stype not in updated_types:
                new_sections.append(
                    DocumentSection(
                        section_type=stype,
                        title=stype.value.replace("_", " ").title(),
                        content=content,
                        author=author,
                    )
                )

        change_summary = f"Updated: {', '.join(t.value for t in updates.keys())}"
        return self.create_version(
            sections=new_sections,
            trigger=trigger,
            summary=change_summary,
        )

    def render_markdown(self, version: DocumentVersion | None = None) -> str:
        """Render a version (default: latest) as a Markdown document."""
        ver = version or self.current
        if ver is None:
            return "# Living Document\n\n_No content yet._\n"

        lines: list[str] = [
            f"# Research Document (v{ver.version_number})",
            f"_Query: {ver.query_id}_  ",
            f"_Last updated: {ver.created_at.strftime('%Y-%m-%d %H:%M UTC')}_",
            "",
        ]

        # Order sections by their enum position
        type_order = list(SectionType)
        sorted_sections = sorted(
            ver.sections,
            key=lambda s: type_order.index(s.section_type) if s.section_type in type_order else 99,
        )

        for section in sorted_sections:
            lines.append(f"## {section.title}")
            if section.confidence_score > 0:
                lines.append(f"_Confidence: {section.confidence_score:.0%}_  ")
            if section.author:
                lines.append(f"_Author: {section.author}_  ")
            lines.append("")
            lines.append(section.content)
            lines.append("")

        return "\n".join(lines)

    def get_context_for_agent(
        self,
        relevant_types: list[SectionType] | None = None,
        max_chars: int = 8000,
    ) -> str:
        """Extract relevant sections as context for an agent prompt.

        Args:
            relevant_types: Section types to include.  If None, includes
                executive summary, findings, contradictions, and open questions.
            max_chars: Maximum character budget for the context string.

        Returns:
            Formatted string suitable for injection into an agent system prompt.
        """
        ver = self.current
        if ver is None:
            return ""

        if relevant_types is None:
            relevant_types = [
                SectionType.EXECUTIVE_SUMMARY,
                SectionType.FINDINGS,
                SectionType.CONTRADICTIONS,
                SectionType.OPEN_QUESTIONS,
            ]

        context_parts: list[str] = [
            f"[Living Document v{ver.version_number} — {ver.query_id}]"
        ]
        chars_used = len(context_parts[0])

        for stype in relevant_types:
            sections = ver.get_sections_by_type(stype)
            for section in sections:
                header = f"\n### {section.title}"
                if chars_used + len(header) + len(section.content) + 2 > max_chars:
                    # Truncate content to fit
                    remaining = max_chars - chars_used - len(header) - 20
                    if remaining > 100:
                        context_parts.append(header)
                        context_parts.append(section.content[:remaining] + "...[truncated]")
                    break
                context_parts.append(header)
                context_parts.append(section.content)
                chars_used += len(header) + len(section.content) + 2

        return "\n".join(context_parts)
