"""Sublab framework -- focused agent teams for specific use cases.

A :class:`Sublab` sits between the CSO orchestrator and the divisions,
providing a lightweight, scoped pipeline that activates only the agents,
tools, and YOHAS phases relevant to a particular use case (e.g. target
validation, assay troubleshooting).
"""

from src.sublabs.base import Sublab
from src.sublabs.target_validation import TargetValidationSublab
from src.sublabs.assay_troubleshooting import AssayTroubleshootingSublab
from src.sublabs.biomarker_curation import BiomarkerCurationSublab
from src.sublabs.regulatory_submissions import RegulatorySubmissionsSublab
from src.sublabs.lead_optimization import LeadOptimizationSublab
from src.sublabs.clinical_translation import ClinicalTranslationSublab

__all__ = [
    "Sublab",
    "TargetValidationSublab",
    "AssayTroubleshootingSublab",
    "BiomarkerCurationSublab",
    "RegulatorySubmissionsSublab",
    "LeadOptimizationSublab",
    "ClinicalTranslationSublab",
]
