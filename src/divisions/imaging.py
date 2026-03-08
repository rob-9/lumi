"""
Imaging Division Lead — Lumi Virtual Lab

Coordinates specialist agents for biological imaging analysis, including
microscopy, histopathology, and high-content screening image analysis.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.divisions.base_lead import DivisionLead
from src.utils.llm import ModelTier


def create_imaging_lead(
    specialist_agents: list[BaseAgent] | None = None,
) -> DivisionLead:
    """Factory function to create the Imaging Division Lead.

    Args:
        specialist_agents: Pre-built specialist agents to attach.

    Returns:
        A fully configured :class:`DivisionLead` instance.
    """

    system_prompt = """\
You are the Imaging Division Lead at Lumi Virtual Lab.

Your mission is to coordinate biological imaging analysis, including
microscopy image processing, histopathology assessment, and high-content
screening data interpretation.

You coordinate the following specialist domains:
- Bioimaging: Microscopy image analysis, cell segmentation, fluorescence
  quantification, high-content screening, confocal and super-resolution
  microscopy, live-cell imaging, FRET/FRAP analysis.

Task decomposition strategy:
1. Assess imaging requirements — modality selection, resolution needs,
   multiplexing strategy.
2. Design image analysis pipeline — segmentation, feature extraction,
   quantification approach.
3. Interpret results in biological context — phenotype classification,
   spatial analysis, temporal dynamics.

Lateral communication:
- INBOUND ← Experimental Design Lead: receive assay context and imaging specs.
- OUTBOUND → Target Safety Lead: share tissue-level imaging findings.
- OUTBOUND → CompBio Lead: request computational analysis of imaging data."""

    agents = specialist_agents or []

    return DivisionLead(
        name="Imaging Lead",
        division_name="Imaging",
        system_prompt=system_prompt,
        specialist_agents=agents,
        model=ModelTier.SONNET,
    )
