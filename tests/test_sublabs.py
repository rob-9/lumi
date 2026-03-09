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
from src.sublabs.assay_troubleshooting import _classify_query
from src.sublabs.regulatory_submissions import _classify_regulatory_query
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
# Assay Troubleshooting — query classification & phase routing
# ---------------------------------------------------------------------------


class TestAssayTroubleshootingQueryClassification:
    def test_signal_noise_keywords(self):
        cats = _classify_query("Why is my ELISA showing high background in serum?")
        assert "signal_noise" in cats

    def test_variability_keywords(self):
        cats = _classify_query("Diagnose inconsistent IC50 values across plate replicates")
        assert "variability" in cats

    def test_expression_keywords(self):
        cats = _classify_query("Troubleshoot low transfection efficiency in HEK293 cells")
        assert "expression" in cats

    def test_protocol_keywords(self):
        cats = _classify_query("My western blot blocking step is not working with this antibody")
        assert "protocol" in cats

    def test_multiple_categories(self):
        cats = _classify_query(
            "High background noise and inconsistent replicates in my ELISA"
        )
        assert "signal_noise" in cats
        assert "variability" in cats

    def test_general_fallback(self):
        cats = _classify_query("Something is wrong with my experiment")
        assert "general" in cats

    def test_categories_ordered_by_relevance(self):
        cats = _classify_query(
            "High background signal noise artifact in my assay with some variability"
        )
        # signal_noise has more keyword hits than variability
        assert cats.index("signal_noise") < cats.index("variability")


class TestAssayTroubleshootingPhaseRouting:
    def test_signal_noise_query_gets_snr_phase(self, divisions):
        sl = create_sublab("Assay Troubleshooting", divisions=divisions)
        phases = sl._build_phases("Why is my ELISA showing high background?")
        phase_names = [p.name for p in phases]
        assert any("Signal-to-Noise" in n for n in phase_names)

    def test_variability_query_gets_qc_phase(self, divisions):
        sl = create_sublab("Assay Troubleshooting", divisions=divisions)
        phases = sl._build_phases("Inconsistent replicates across my plate")
        phase_names = [p.name for p in phases]
        assert any("Variability" in n or "QC" in n for n in phase_names)

    def test_expression_query_gets_expression_phase(self, divisions):
        sl = create_sublab("Assay Troubleshooting", divisions=divisions)
        phases = sl._build_phases("Low transfection efficiency in HEK293")
        phase_names = [p.name for p in phases]
        assert any("Expression" in n for n in phase_names)

    def test_general_query_gets_all_phases(self, divisions):
        sl = create_sublab("Assay Troubleshooting", divisions=divisions)
        phases = sl._build_phases("Something is wrong with my experiment")
        # general fallback should include performance analysis + expression + solution
        assert len(phases) >= 4

    def test_always_starts_with_characterization(self, divisions):
        sl = create_sublab("Assay Troubleshooting", divisions=divisions)
        for query in [
            "High background in ELISA",
            "Low transfection efficiency",
            "Inconsistent replicates",
            "Something is wrong",
        ]:
            phases = sl._build_phases(query)
            assert phases[0].name == "Problem Characterization & Data Review"

    def test_always_ends_with_solution_proposal(self, divisions):
        sl = create_sublab("Assay Troubleshooting", divisions=divisions)
        for query in [
            "High background in ELISA",
            "Low transfection efficiency",
            "Inconsistent replicates",
        ]:
            phases = sl._build_phases(query)
            assert "Solution" in phases[-1].name

    def test_solution_phase_depends_on_all_prior(self, divisions):
        sl = create_sublab("Assay Troubleshooting", divisions=divisions)
        phases = sl._build_phases("High background noise in ELISA")
        solution_phase = phases[-1]
        prior_ids = [p.phase_id for p in phases[:-1]]
        assert set(prior_ids).issubset(set(solution_phase.dependencies))

    def test_phase_ids_are_sequential(self, divisions):
        sl = create_sublab("Assay Troubleshooting", divisions=divisions)
        phases = sl._build_phases("test query")
        ids = [p.phase_id for p in phases]
        assert ids == list(range(1, len(phases) + 1))

    def test_dependencies_reference_valid_phases(self, divisions):
        sl = create_sublab("Assay Troubleshooting", divisions=divisions)
        for query in AssayTroubleshootingSublab.examples:
            phases = sl._build_phases(query)
            phase_ids = {p.phase_id for p in phases}
            for p in phases:
                for dep in p.dependencies:
                    assert dep in phase_ids, (
                        f"Phase {p.phase_id} depends on non-existent {dep} "
                        f"for query: {query}"
                    )


# ---------------------------------------------------------------------------
# Regulatory Submissions — query classification & phase routing
# ---------------------------------------------------------------------------


class TestRegulatoryQueryClassification:
    def test_toxicology_keywords(self):
        cats = _classify_regulatory_query("Review hepatotoxicity signals for kinase inhibitors")
        assert "toxicology" in cats

    def test_moa_keywords(self):
        cats = _classify_regulatory_query("Compile mechanism of action safety assessment")
        assert "moa" in cats

    def test_clinical_safety_keywords(self):
        cats = _classify_regulatory_query("Analyze FAERS adverse event reports for anti-PD1 class")
        assert "clinical_safety" in cats

    def test_regulatory_strategy_keywords(self):
        cats = _classify_regulatory_query("Assess breakthrough therapy designation eligibility for IND filing")
        assert "regulatory_strategy" in cats

    def test_multiple_categories(self):
        cats = _classify_regulatory_query(
            "Review hepatotoxicity and mechanism of action for IND submission"
        )
        assert "toxicology" in cats
        assert "moa" in cats

    def test_general_fallback(self):
        cats = _classify_regulatory_query("Prepare a safety review for this compound")
        assert "general" in cats

    def test_categories_ordered_by_relevance(self):
        cats = _classify_regulatory_query(
            "Evaluate hepatotoxicity cardiotoxicity nephrotoxicity and mechanism of action"
        )
        # toxicology has more keyword hits than moa
        assert cats.index("toxicology") < cats.index("moa")


class TestRegulatorySubmissionsPhaseRouting:
    def test_tox_query_starts_with_tox_review(self, divisions):
        sl = create_sublab("Regulatory Submissions", divisions=divisions)
        phases = sl._build_phases("Review hepatotoxicity signals")
        assert phases[0].name == "Toxicology Literature Review"

    def test_moa_query_gets_moa_phase(self, divisions):
        sl = create_sublab("Regulatory Submissions", divisions=divisions)
        phases = sl._build_phases("Compile mechanism of action safety assessment")
        phase_names = [p.name for p in phases]
        assert any("Mechanism of Action" in n for n in phase_names)

    def test_clinical_safety_query_gets_clinical_phase(self, divisions):
        sl = create_sublab("Regulatory Submissions", divisions=divisions)
        phases = sl._build_phases("Analyze FAERS adverse event reports")
        phase_names = [p.name for p in phases]
        assert any("Clinical Safety" in n for n in phase_names)

    def test_regulatory_strategy_query_gets_strategy_phase(self, divisions):
        sl = create_sublab("Regulatory Submissions", divisions=divisions)
        phases = sl._build_phases("Assess breakthrough therapy IND filing pathway")
        phase_names = [p.name for p in phases]
        assert any("Regulatory Strategy" in n for n in phase_names)

    def test_general_query_gets_moa_and_clinical(self, divisions):
        sl = create_sublab("Regulatory Submissions", divisions=divisions)
        phases = sl._build_phases("Prepare a safety review for this compound")
        phase_names = [p.name for p in phases]
        assert any("Mechanism of Action" in n for n in phase_names)
        assert any("Clinical Safety" in n for n in phase_names)

    def test_always_has_tox_review_first(self, divisions):
        sl = create_sublab("Regulatory Submissions", divisions=divisions)
        for query in RegulatorySubmissionsSublab.examples:
            phases = sl._build_phases(query)
            assert phases[0].name == "Toxicology Literature Review"

    def test_always_has_literature_compilation(self, divisions):
        sl = create_sublab("Regulatory Submissions", divisions=divisions)
        for query in RegulatorySubmissionsSublab.examples:
            phases = sl._build_phases(query)
            phase_names = [p.name for p in phases]
            assert any("Literature" in n for n in phase_names)

    def test_always_ends_with_compilation(self, divisions):
        sl = create_sublab("Regulatory Submissions", divisions=divisions)
        for query in [
            "Review hepatotoxicity signals",
            "Compile mechanism of action safety",
            "Analyze FAERS adverse events",
        ]:
            phases = sl._build_phases(query)
            assert "Compilation" in phases[-1].name or "Gap" in phases[-1].name

    def test_compilation_phase_depends_on_all_prior(self, divisions):
        sl = create_sublab("Regulatory Submissions", divisions=divisions)
        phases = sl._build_phases("Review hepatotoxicity for kinase inhibitor class")
        compilation_phase = phases[-1]
        prior_ids = [p.phase_id for p in phases[:-1]]
        assert set(prior_ids).issubset(set(compilation_phase.dependencies))

    def test_phase_ids_are_sequential(self, divisions):
        sl = create_sublab("Regulatory Submissions", divisions=divisions)
        phases = sl._build_phases("test query")
        ids = [p.phase_id for p in phases]
        assert ids == list(range(1, len(phases) + 1))

    def test_dependencies_reference_valid_phases(self, divisions):
        sl = create_sublab("Regulatory Submissions", divisions=divisions)
        for query in RegulatorySubmissionsSublab.examples:
            phases = sl._build_phases(query)
            phase_ids = {p.phase_id for p in phases}
            for p in phases:
                for dep in p.dependencies:
                    assert dep in phase_ids, (
                        f"Phase {p.phase_id} depends on non-existent {dep} "
                        f"for query: {query}"
                    )


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
