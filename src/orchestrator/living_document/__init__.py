"""
Living Document — Evolving research narrative layer.

Sits on top of the WorldModel (structured SQLite store) and maintains
a human-readable, continuously-updated research document that agents
can read from and write to as shared context.

Key components:
- LivingDocument: The evolving narrative object (sections, findings, open questions)
- DocumentManager: CRUD operations, versioning, conflict resolution
- NarrativeSynthesizer: Converts structured WorldModel data into prose sections
- ContextProvider: Gives agents relevant document sections as context

How it differs from WorldModel:
- WorldModel = structured knowledge graph (entities, claims, relationships)
- LivingDocument = narrative layer that tells the story of the research
- WorldModel is for machines; LivingDocument is for humans + agent context

Versioning:
- Every update creates a new version (append-only)
- Agents see the latest version as context
- Humans see the full history with diffs
- Contradictions between versions are flagged for review
"""
