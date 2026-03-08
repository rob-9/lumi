"""Tests for the sublab framework."""

from __future__ import annotations

import pytest

from src.sublabs.base import Sublab
from src.sublabs.target_validation import TargetValidationSublab
from src.sublabs.assay_troubleshooting import AssayTroubleshootingSublab
from src.sublabs.biomarker_curation import BiomarkerCurationSublab
from src.sublabs.regulatory_submissions import RegulatorySubmissionsSublab
from src.sublabs.lead_optimization import LeadOptimizationSublab
from src.sublabs.clinical_translation import ClinicalTranslationSublab
from src.factory import (
    create_sublab,
    create_all_sublabs,
    create_system,
    SUBLAB_REGISTRY,
)
from src.utils.types import Phase


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def divisions():
    """Create the full system divisions once for all tests."""
    return create_system()


# ---------------------------------------------------------------------------
# Registry & Factory
# ---------------------------------------------------------------------------


class TestSubLabRegistry:
    def test_registry_has_all_six_sublabs(self):
        assert len(SUBLAB_REGISTRY) == 6
        expected = {
            "Target Validation",
            "Assay Troubleshooting",
            "Biomarker Curation",
            "Regulatory Submissions",
            "Lead Optimization",
            "Clinical Translation",
        }
        assert set(SUBLAB_REGISTRY.keys()) == expected

    def test_all_registry_values_are_sublab_subclasses(self):
        for name, cls in SUBLAB_REGISTRY.items():
            assert issubclass(cls, Sublab), f"{name} is not a Sublab subclass"


class TestCreateSublab:
    def test_create_known_sublab(self, divisions):
        sl = create_sublab("Target Validation", divisions=divisions)
        assert isinstance(sl, TargetValidationSublab)
        assert sl.name == "Target Validation"

    def test_create_unknown_sublab_raises(self, divisions):
        with pytest.raises(ValueError, match="Unknown sublab"):
            create_sublab("Nonexistent", divisions=divisions)

    def test_create_all_sublabs(self, divisions):
        all_sl = create_all_sublabs(divisions=divisions)
        assert len(all_sl) == 6
        for name, sl in all_sl.items():
            assert isinstance(sl, Sublab)
            assert sl.name == name


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------


class TestSublabBase:
    def test_normalise(self):
        assert Sublab._normalise("Statistical Genetics") == "statisticalgenetics"
        assert Sublab._normalise("statistical_genetics") == "statisticalgenetics"
        assert Sublab._normalise("FDA Safety") == "fdasafety"
        assert Sublab._normalise("fda_safety") == "fdasafety"
        assert Sublab._normalise("Dual-Use Screening") == "dualusescreening"

    def test_get_info_returns_expected_keys(self, divisions):
        sl = create_sublab("Target Validation", divisions=divisions)
        info = sl.get_info()
        expected_keys = {
            "name", "description", "agents", "divisions", "phases",
            "debate_protocol", "report_sections", "examples",
        }
        assert set(info.keys()) == expected_keys
        assert info["name"] == "Target Validation"

    def test_divisions_filtered_correctly(self, divisions):
        sl = create_sublab("Target Validation", divisions=divisions)
        assert set(sl.divisions.keys()) == {
            "Target Identification", "Target Safety", "Computational Biology",
        }

    def test_agents_matched_correctly(self, divisions):
        sl = create_sublab("Lead Optimization", divisions=divisions)
        agent_names_normalised = {Sublab._normalise(a.name) for a in sl.agents}
        expected = {
            Sublab._normalise(n) for n in sl.agent_names
            # Only agents from divisions the sublab actually includes
            if any(
                Sublab._normalise(a.name) == Sublab._normalise(n)
                for lead in sl.divisions.values()
                for a in lead.specialist_agents
            )
        }
        assert agent_names_normalised == expected


# ---------------------------------------------------------------------------
# Concrete sublabs — class-level config
# ---------------------------------------------------------------------------


ALL_SUBLAB_CLASSES = [
    TargetValidationSublab,
    AssayTroubleshootingSublab,
    BiomarkerCurationSublab,
    RegulatorySubmissionsSublab,
    LeadOptimizationSublab,
    ClinicalTranslationSublab,
]


class TestSublabConfigs:
    @pytest.mark.parametrize("cls", ALL_SUBLAB_CLASSES, ids=lambda c: c.name)
    def test_has_required_attributes(self, cls):
        assert cls.name, "name must be set"
        assert cls.description, "description must be set"
        assert len(cls.agent_names) > 0, "must have at least one agent"
        assert len(cls.division_names) > 0, "must have at least one division"
        assert len(cls.phases) > 0, "must have at least one phase"
        assert cls.debate_protocol, "debate_protocol must be set"
        assert len(cls.report_sections) > 0, "must have report sections"
        assert len(cls.examples) > 0, "must have example queries"

    @pytest.mark.parametrize("cls", ALL_SUBLAB_CLASSES, ids=lambda c: c.name)
    def test_examples_are_strings(self, cls):
        for ex in cls.examples:
            assert isinstance(ex, str) and len(ex) > 10

    @pytest.mark.parametrize("cls", ALL_SUBLAB_CLASSES, ids=lambda c: c.name)
    def test_build_phases_returns_phase_objects(self, cls, divisions):
        sl = cls(divisions=divisions)
        phases = sl._build_phases("test query")
        assert len(phases) > 0
        for p in phases:
            assert isinstance(p, Phase)
            assert p.phase_id > 0
            assert p.name
            assert p.division


# ---------------------------------------------------------------------------
# Execution plan
# ---------------------------------------------------------------------------


class TestExecutionPlan:
    def test_plan_has_correct_metadata(self, divisions):
        sl = create_sublab("Target Validation", divisions=divisions)
        plan = sl._build_execution_plan("Test query")
        assert plan.user_query == "Test query"
        assert "Target Validation" in plan.confirmed_scope
        assert plan.estimated_total_cost > 0

    def test_plan_phases_match_build_phases(self, divisions):
        sl = create_sublab("Assay Troubleshooting", divisions=divisions)
        plan = sl._build_execution_plan("Why is my ELISA failing?")
        phases = sl._build_phases("Why is my ELISA failing?")
        assert len(plan.phases) == len(phases)

    def test_dependencies_reference_existing_phases(self, divisions):
        sl = create_sublab("Target Validation", divisions=divisions)
        plan = sl._build_execution_plan("test")
        phase_ids = {p.phase_id for p in plan.phases}
        for p in plan.phases:
            for dep in p.dependencies:
                assert dep in phase_ids, f"Phase {p.phase_id} depends on non-existent phase {dep}"


# ---------------------------------------------------------------------------
# Integration: app.py SUBLABS dict
# ---------------------------------------------------------------------------


_has_streamlit = pytest.importorskip is not None  # just for marker

try:
    import streamlit  # noqa: F401
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False


@pytest.mark.skipif(not _HAS_STREAMLIT, reason="streamlit not installed")
class TestAppIntegration:
    def test_sublabs_dict_generated_from_registry(self):
        """The app.py SUBLABS dict should be auto-generated from SUBLAB_REGISTRY."""
        from app import SUBLABS
        assert len(SUBLABS) == 6
        for name, info in SUBLABS.items():
            assert name in SUBLAB_REGISTRY
            assert "description" in info
            assert "agents" in info
            assert "divisions" in info
            assert "examples" in info

    def test_sublabs_dict_matches_class_attrs(self):
        from app import SUBLABS
        for name, info in SUBLABS.items():
            cls = SUBLAB_REGISTRY[name]
            assert info["description"] == cls.description
            assert info["agents"] == cls.agent_names
            assert info["divisions"] == cls.division_names
            assert info["examples"] == cls.examples
